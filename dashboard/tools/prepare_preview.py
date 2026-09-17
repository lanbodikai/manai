"""Build an ignored, local-only read-only browsing cache using the official prep.

No source or derived rows are written into tracked paths. This is not A's audit
service and never calculates recoverability, money, claims or hardware causality.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
CACHE = HERE / '.local-data'


def module(path, name):
    sys.dont_write_bytecode = True  # Never leave import caches in the supplied checkout.
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def normalized(value):
    if isinstance(value, (list, np.ndarray)):
        return json.dumps([normalized(v) for v in value])
    if value is None or pd.isna(value):
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def dump(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def build(official):
    official = official.resolve()
    CACHE.mkdir(exist_ok=True)
    old_cwd = Path.cwd()
    try:
        # The unmodified supplied module creates data/prepped relative to cwd.
        os.chdir(CACHE)
        prep = module(official / 'scripts/prep_data.py', 'official_preview_prep')
        prep.RAW = official / 'data/raw'
        prep.OUT = CACHE / 'data/prepped'
        jobs, cards = prep.build()
    finally:
        os.chdir(old_cwd)
    checks = module(official / 'scripts/checksum_data.py', 'official_preview_checks')
    expected = {}
    for line in (official / 'data/checksums.txt').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            digest, name = line.split()
            expected[name] = digest
    fingerprints = []
    for name in ['prepped/jobs.parquet', 'prepped/gpus.parquet']:
        digest = checks.digest(CACHE / 'data' / name)
        if digest != expected[name]:
            raise RuntimeError(f'Canonical checksum mismatch for {name}; preview was not published.')
        fingerprints.append(digest)
        print(f'ok {name}')
    version = hashlib.sha256(''.join(fingerprints).encode()).hexdigest()
    cards = cards.merge(jobs[['id_job', 'walltime_sec', 'attempts']], on='id_job', validate='many_to_one')
    cards['duration_exceeds_final_walltime'] = cards.totalexecutiontime_sec > cards.walltime_sec
    cards['bounded_gpu_hours'] = cards[['totalexecutiontime_sec', 'walltime_sec']].min(axis=1).clip(lower=0) / 3600
    nodes = sorted(cards.Node.dropna().unique().tolist())
    output = CACHE / 'preview.build.sqlite'
    if output.exists():
        output.unlink()  # Fixed known cache file, never source data.
    db = sqlite3.connect(output)
    db.executescript('''
      CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
      CREATE TABLE records(collection TEXT,id TEXT,title TEXT,summary TEXT,synthetic INTEGER,values_json TEXT,related_json TEXT,search_text TEXT,node TEXT,outcome TEXT,PRIMARY KEY(collection,id));
      CREATE INDEX records_filter ON records(collection,node,outcome);
      CREATE TABLE activity(id_job TEXT,node TEXT,gpu_id INTEGER,values_json TEXT);
      CREATE INDEX activity_job ON activity(id_job);
      CREATE INDEX activity_card ON activity(node,gpu_id);
    ''')
    def add(collection, key, title, summary, values, related, synthetic=False):
        values = {k: normalized(v) for k, v in values.items()}
        db.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (collection, key, title, summary, int(synthetic), dump(values), dump(related),
                    ' '.join(str(v) for v in values.values() if v is not None).lower(),
                    values.get('Node', values.get('primary_node')), values.get('state_name', values.get('status'))))
    def link(collection, key, label):
        return {'collection': collection, 'id': str(key), 'label': label}
    card_groups = {str(int(key)): frame for key, frame in cards.groupby('id_job', sort=False)}
    for raw in jobs.to_dict('records'):
        key = str(int(raw['id_job']))
        raw['id_job'] = key
        group = card_groups[key]
        related = [link('gpus', f'{node}/gpu-{gpu}', f'{node} · GPU {gpu}') for node, gpu in group[['Node', 'gpu_id']].itertuples(index=False, name=None)]
        completed_zero = raw['state_name'] == 'COMPLETED' and raw['sm_util_avg'] == 0 and raw['sm_util_max'] == 0
        summary = ('This job completed with no recorded GPU compute. CPU-only compatibility remains untested.' if completed_zero
                   else f"Final recorded outcome: {raw['state_name']}. Outcome alone does not establish waste or hardware causality.")
        add('jobs', key, f'Job {key}', summary, raw, related)
    for raw in cards.to_dict('records'):
        raw = {k: normalized(v) for k, v in raw.items()}
        raw['id_job'] = str(int(raw['id_job']))
        db.execute('INSERT INTO activity VALUES (?,?,?,?)', (raw['id_job'], raw['Node'], raw['gpu_id'], dump(raw)))
    def weighted(group, field):
        valid = group[field].notna() & group.bounded_gpu_hours.notna()
        weight = group.loc[valid, 'bounded_gpu_hours']
        return (float((group.loc[valid, field] * weight).sum() / weight.sum()) if weight.sum() else None)
    gpu_count = 0
    for (node, gpu), group in cards.groupby(['Node', 'gpu_id']):
        gpu_count += 1
        key = f'{node}/gpu-{gpu}'
        values = {'Node': node, 'gpu_id': int(gpu), 'job_count': int(group.id_job.nunique()),
                  'gpu_hours': float(group.gpu_hours.sum()), 'bounded_gpu_hours': float(group.bounded_gpu_hours.sum()),
                  'sm_util_weighted': weighted(group, 'smutilization_pct_avg'), 'watts_avg_weighted': weighted(group, 'powerusage_watts_avg'),
                  'duration_anomaly_rows': int(group.duration_exceeds_final_walltime.sum()), 'requeued_job_count': int(group.loc[group.attempts > 1, 'id_job'].nunique())}
        add('gpus', key, f'{node} · GPU {gpu}', 'Historical telemetry while jobs held this card. Unallocated time is absent. GPU ID is local to this machine.', values,
            [link('machines', node, node)])
    for node, group in cards.groupby('Node'):
        values = {'Node': node, 'observed_gpu_count': int(group.gpu_id.nunique()), 'job_count': int(group.id_job.nunique()),
                  'gpu_hours': float(group.gpu_hours.sum()), 'sm_util_weighted': weighted(group, 'smutilization_pct_avg'),
                  'unsuccessful_jobs': int(group.loc[group.state_name.notna() & (group.state_name != 'COMPLETED'), 'id_job'].nunique()),
                  'duration_anomaly_rows': int(group.duration_exceeds_final_walltime.sum())}
        add('machines', node, node, 'Recorded job exposure, attributed through per-card Node values. This is not a diagnosis of faulty hardware.', values,
            [link('gpus', f'{node}/gpu-{gpu}', f'GPU {gpu}') for gpu in sorted(group.gpu_id.unique())])
    findings_path = official / 'data/synthetic/findings.json'
    finding_count = None
    if findings_path.exists():
        if checks.digest(findings_path) != expected['synthetic/findings.json']:
            raise RuntimeError('Findings checksum mismatch; preview was not published.')
        findings = json.loads(findings_path.read_text())
        for finding in findings:
            meta = finding.get('metadata', {})
            values = {'rule': finding.get('detectorId'), 'status': finding.get('status'), 'Node': meta.get('node'), 'id_job': str(meta['job_id']) if meta.get('job_id') is not None else None,
                      'impact_gpu_hours': meta.get('impact_gpu_hours'), 'impact_kind': meta.get('impact_kind'), 'impact_scope': meta.get('impact_scope')}
            values.update({k: dump(v) if isinstance(v, (dict, list)) else v for k, v in finding.items()})
            related = [link('jobs', meta['job_id'], f"Job {meta['job_id']}")] if meta.get('job_id') is not None else []
            add('findings', str(finding['id']), finding.get('shortDescription', 'Finding'), finding.get('longDescription', ''), values, related, meta.get('synthetic', False))
        finding_count = len(findings)
        version = hashlib.sha256((version + expected['synthetic/findings.json']).encode()).hexdigest()
    util = jobs.sm_util_avg.clip(0, 100) / 100
    summary = {'gpu_hours': float(jobs.gpu_hours.sum()), 'estimated_active_gpu_hours': float((jobs.gpu_hours * util).sum()),
               'estimated_completed_active_gpu_hours': float((jobs.loc[jobs.is_success, 'gpu_hours'] * util[jobs.is_success]).sum()),
               'outcomes': [{'outcome': str(state), 'gpu_hours': float(value)} for state, value in jobs.groupby('state_name', dropna=False).gpu_hours.sum().sort_values(ascending=False).items()]}
    catalog = {'dataset_contract_version': 'preview-1', 'version': version, 'source_label': 'MIT SuperCloud workload sample · local read-only preview',
               'window_label': 'Approximately four months; source timestamps are relative offsets', 'synthetic': False, 'nodes': nodes,
               'collections': [{'key': key, 'count': count, 'available': count is not None} for key, count in [('jobs', len(jobs)), ('gpus', gpu_count), ('machines', len(nodes)), ('findings', finding_count)]],
               'summary': summary, 'caveats': [
                 'Jobs and GPU tables match the official semantic checksums. This does not validate the full five-file dataset or savings claims.',
                 'This workload sample cannot establish whole-cluster utilization or next-quarter savings.',
                 'GPU time is reported telemetry, not purchased capacity. Activity is an SM-weighted proxy, not measured research output.',
                 'Per-card activity averages use runtime clipped to the final job walltime; source reported hours remain visible for reconciliation. Requeues can mix attempts.',
                 'Findings are not loaded unless the official generated file is present and checksum-matched.'
               ]}
    db.execute('INSERT INTO metadata VALUES (?,?)', ('catalog', dump(catalog)))
    db.commit()
    # Internal consistency checks: row uniqueness, attribution and bounded runtime.
    assert jobs.id_job.is_unique
    assert not cards.duplicated(['Node', 'gpu_id', 'id_job']).any()
    assert np.isclose(cards.gpu_hours.sum(), jobs.gpu_hours.sum())
    assert ((cards.bounded_gpu_hours >= 0) & (cards.bounded_gpu_hours <= cards.gpu_hours + 1e-9)).all()
    db.close()
    output.replace(CACHE / 'preview.sqlite')
    print(f'Local preview ready: {len(jobs)} jobs, {gpu_count} cards, {len(nodes)} machines. Findings: {finding_count if finding_count is not None else "not loaded"}.')
    print('No savings, billing or MCP claims computed. Cache is ignored by Git.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--official-root', type=Path, required=True, help='Existing official Track 2 directory containing scripts/ and data/raw/.')
    build(parser.parse_args().official_root)
