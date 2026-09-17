"""Private live product witness; independent Decimal oracle, no calculator imports.

Run with pinned Python dependencies, read-only source/data and a fresh output path.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, getcontext
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import traceback
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

import pandas as pd
from scripts.checksum_data import FILES, digest

getcontext().prec = 40
D = lambda x: Decimal(str(x))


def close(actual, expected):
    assert actual is not None and math.isfinite(actual)
    assert abs(D(actual) - D(expected)) <= max(D('1e-8'), D('1e-9') * abs(D(expected))), (actual, str(expected))


def fingerprint(data):
    actual = {name: digest(data / name) for name in FILES}
    expected = dict(line.split()[::-1] for line in (data / 'checksums.txt').read_text().splitlines()
                    if line.strip() and not line.startswith('#'))
    assert actual == expected, 'Canonical semantic checksum mismatch'
    return actual


def code_hash(root):
    result = {}
    for directory in ['analysis', 'service', 'api', 'contracts', 'dashboard/src', 'dashboard/tools', 'dashboard/scripts', 'scripts', 'tests', 'eval/analysis', 'eval/integration']:
        for path in sorted((root / directory).rglob('*')):
            if path.is_file() and path.suffix in {'.py', '.ts', '.tsx', '.css', '.json', '.cjs', '.yml'}:
                result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ['requirements.lock.txt', 'service/requirements.lock.txt', 'service/Dockerfile',
                 'api/Dockerfile.local', 'dashboard/Dockerfile', 'dashboard/package.json',
                 'dashboard/package-lock.json', 'dashboard/server.mjs', 'docker-compose.yml', '.dockerignore']:
        result[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(), result


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def positive(x, integer=False):
    return finite(x) and x > 0 and (not integer or int(x) == x)


def expected_fit(r):
    if not positive(r['nodes_alloc'], True) or not positive(r['n_nodes_listed'], True) or r['nodes_alloc'] != r['n_nodes_listed']:
        return 'unresolved', 'invalid_node_count', None
    if r['nodes_alloc'] != 1:
        return 'unresolved', 'multi_node_placement', None
    if not positive(r['cpus_req'], True) or not positive(r['mem_req_total_mb']):
        return 'unresolved', 'invalid_resource_request', None
    if not positive(r['walltime_sec']) or not positive(r['gpu_count'], True):
        return 'unresolved', 'invalid_scenario_baseline', None
    cores = max(int(r['cpus_req']), int((D(r['mem_req_total_mb']) / 4000).to_integral_value(rounding=ROUND_CEILING)))
    if r['mem_req_total_mb'] > 192000:
        return 'non_fit', 'requested_memory_exceeds_node', cores
    if cores > 48:
        return 'non_fit', 'required_cores_exceed_node', cores
    return 'fits', 'requested_resources_fit', cores


def run(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)  # Failed attempts are never overwritten.
    manifest = {'started': datetime.now(timezone.utc).isoformat(), 'revision': args.revision,
                'url': args.url, 'python': platform.python_version(),
                'dependencies': {n: importlib.metadata.version(n) for n in ['pandas', 'pyarrow', 'numpy']},
                'checks': []}
    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    def request(path):
        with urlopen(args.url.rstrip('/') + path, timeout=120) as response:
            return json.load(response)
    def status(path, expected):
        try:
            request(path)
        except HTTPError as e:
            assert e.code == expected, (e.code, expected)
        else:
            raise AssertionError('Expected explicit rejection')
    def passed(name):
        manifest['checks'].append({'id': name, 'status': 'PASS'})
        print(name, 'PASS', flush=True)
    try:
        manifest['code_hash'], manifest['code_files'] = code_hash(Path(args.source))
        manifest['before'] = fingerprint(Path(args.data))
        passed('HP01 canonical source before')
        catalog = request('/api/datasets/catalog')
        version = catalog['version']
        summary = request('/api/cpu-hardware-scenario?' + urlencode({'dataset_version': version}))
        save('summary.json', summary)
        assert summary['dataset_version'] == version
        assert summary['data_fingerprint'] == hashlib.sha256(json.dumps(manifest['before'], sort_keys=True).encode()).hexdigest()
        assert summary['kind'] == 'scenario_estimate' and not summary['synthetic']
        assert not summary['cash_savings_verified'] and not summary['compatibility_verified']
        rows = pd.read_parquet(Path(args.data) / 'prepped/jobs.parquet').to_dict('records')
        assert len({str(r['id_job']) for r in rows}) == len(rows)
        cohort = {}
        for r in rows:
            avg, peak, hours, duration = (r[k] for k in ['sm_util_avg', 'sm_util_max', 'gpu_hours', 'walltime_sec'])
            valid_duration = duration is None or (isinstance(duration, float) and math.isnan(duration)) or (finite(duration) and duration >= 0)
            if r['state_name'] == 'COMPLETED' and finite(avg) and finite(peak) and avg == peak == 0 and finite(hours) and hours > 1 and valid_duration:
                cohort[str(r['id_job'])] = r
        params = {'dataset_version': version, 'scenario_id': summary['scenario_id'], 'limit': 100}
        jobs = []
        for group in ['all', 'fits', 'non_fit', 'unresolved']:
            group_jobs = []
            offset = 0
            while True:
                page = request('/api/cpu-hardware-scenario/jobs?' + urlencode({**params, 'status': group, 'offset': offset}))
                assert page['offset'] == offset and page['scenario_id'] == summary['scenario_id']
                group_jobs.extend(page['items'])
                offset += len(page['items'])
                if offset >= page['total']:
                    break
                assert page['items'], 'Pagination stopped progressing'
            assert len({j['job_id'] for j in group_jobs}) == len(group_jobs)
            if group == 'all':
                jobs = group_jobs
            else:
                assert [j for j in jobs if j['status'] == group] == group_jobs
        assert set(cohort) == {j['job_id'] for j in jobs}
        fits = []
        for j in jobs:
            r = cohort[j['job_id']]
            group, reason, cores = expected_fit(r)
            assert (j['status'], j['reason']) == (group, reason)
            if cores is not None:
                assert j['memory_adjusted_cores'] == cores
            close(j['recorded_gpu_hours'], r['gpu_hours'])
            if group == 'fits':
                fits.append((r, cores))
                for allocation, n in [('memory_adjusted', cores), ('whole_node', 48)]:
                    for name, ratio in [('low_cpu_price', '.005'), ('high_cpu_price', '.02')]:
                        close(j['cost_break_even_cpu_hours'][allocation][name], D(r['gpu_hours']) / (n * D(ratio)))
        coverage = summary['coverage']
        counts = Counter(j['status'] for j in jobs)
        for field, value in [('eligible_jobs', len(cohort)), ('fitting_jobs', counts['fits']), ('non_fitting_jobs', counts['non_fit']), ('unresolved_jobs', counts['unresolved'])]:
            assert coverage[field] == value
        close(coverage['eligible_gpu_hours'], sum(D(r['gpu_hours']) for r in cohort.values()))
        close(coverage['fitting_gpu_hours'], sum(D(r['gpu_hours']) for r, _ in fits))
        assert coverage['memory_resized_jobs'] == sum(cores > r['cpus_req'] for r, cores in fits)
        save('jobs.json', jobs)
        passed('HP02 exhaustive resource fit and evidence pagination')
        price = D(summary['gpu_reference_usd_per_hour'])
        assert price == D('2.5'), 'Pinned official reference price changed; review assumptions'
        baseline = sum(D(r['gpu_hours']) for r in rows) * price
        target = baseline / 5
        close(summary['baseline_reference_usd'], baseline)
        close(summary['target_reference_usd'], target)
        for allocation in summary['allocations']:
            for case in allocation['cases']:
                cost = core_hours = released = D(0)
                positive_jobs = 0
                for r, n in fits:
                    cores = n if allocation['id'] == 'memory_adjusted' else 48
                    ch = D(r['walltime_sec']) / 3600 * cores
                    cpu_cost = ch * price * D(case['cpu_price_ratio'])
                    cost += cpu_cost
                    core_hours += ch
                    released += D(r['gpu_hours'])
                    positive_jobs += D(r['gpu_hours']) * price - cpu_cost > D('1e-8')
                net = released * price - cost
                expected = {'cpu_core_hours': core_hours, 'cpu_cost_reference_usd': cost,
                            'released_gpu_hours_if_success': released, 'success_net_reference_usd': net,
                            'failure_net_reference_usd': -cost, 'failure_extra_reference_usd': cost,
                            'validation_net_reference_usd': -cost, 'baseline_reduction_pct': net / baseline * 100,
                            'target_contribution_pct': net / target * 100, 'remaining_target_reference_usd': max(D(0), target - net)}
                for key, value in expected.items():
                    close(case[key], value)
                assert case['positive_no_slower_jobs'] == positive_jobs
                assert case['failure_runtime_ratio'] == 2 and case['success_completion_change_hours'] == 0
                assert case['validation_completion_change_hours'] is None
            for key in ['success_net_reference_usd', 'failure_extra_reference_usd', 'baseline_reduction_pct', 'target_contribution_pct', 'remaining_target_reference_usd']:
                assert allocation[key] == {'low': min(c[key] for c in allocation['cases']), 'high': max(c[key] for c in allocation['cases'])}
        passed('HP03 independent Decimal arithmetic and same-window target')
        status('/api/cpu-hardware-scenario?dataset_version=stale', 409)
        status('/api/cpu-hardware-scenario/jobs?' + urlencode({**params, 'scenario_id': 'stale'}), 409)
        status('/api/cpu-hardware-scenario/jobs?' + urlencode({**params, 'limit': 101}), 422)
        assert request('/api/cpu-hardware-scenario?' + urlencode({'dataset_version': version})) == summary
        passed('HP04 stale identities and immutable responses')
        manifest['after'] = fingerprint(Path(args.data))
        assert manifest['after'] == manifest['before']
        assert code_hash(Path(args.source))[0] == manifest['code_hash']
        passed('HP05 unchanged source and code')
        manifest['status'] = 'PASS'
    except Exception:
        manifest['status'] = 'FAIL'
        (out / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
    finally:
        manifest['finished'] = datetime.now(timezone.utc).isoformat()
        save('manifest.json', manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['data', 'output', 'revision']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--source', default='/app')
    parser.add_argument('--url', default='http://dashboard:3000')
    run(parser.parse_args())
