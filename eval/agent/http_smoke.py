"""Actual A v0.4 + C sockets and official MCP, with explicit synthetic inputs.

Canonical data readiness is replaced only inside the standalone A test process.
Use live_review against the team's real A audit for source-data acceptance.
"""
import argparse
import asyncio
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import httpx

from eval.agent.live_review import review, write_private

ROOT = Path(__file__).resolve().parents[2]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def launch(module, port, env):
    return subprocess.Popen([sys.executable, '-m', 'uvicorn', module, '--host', '127.0.0.1', '--port', str(port)],
                            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def wait_ready(client, url):
    for _ in range(100):
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
        await asyncio.sleep(.1)
    raise RuntimeError('Local socket-test service failed to start')


async def run():
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if key in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE='1', REVIEWER_MODE='deterministic', REVIEWER_MCP_CONTEXT='price_only')
    processes, attempts = [], []
    a_port, c_port = free_port(), free_port()
    a_url, c_url = f'http://127.0.0.1:{a_port}', f'http://127.0.0.1:{c_port}'
    try:
        async with httpx.AsyncClient(timeout=35, trust_env=False) as client:
            processes.append(launch('eval.agent.a_fixture_server:app', a_port, env))
            health = await wait_ready(client, a_url + '/api/health')
            processes.append(launch('reviewer.main:app', c_port, {**env, 'ANALYSIS_URL': a_url}))
            await wait_ready(client, c_url + '/health')
            request = json.loads((ROOT / 'contracts/examples/audit-request.json').read_text())
            request['expected_data_fingerprint'] = health['data_fingerprint']
            request['scenario'].pop('cpu_pilot', None)
            response = await client.post(a_url + '/api/audits', json=request)
            response.raise_for_status()
            baseline_audit = response.json()
            attempts.append({'case': 'no_pilot', **await review(a_url, c_url, baseline_audit['audit_id'])})
            page = await client.get(a_url + '/api/audits/' + baseline_audit['audit_id'] + '/evidence', params={'limit': 100})
            page.raise_for_status()
            ref = next(r for r in page.json()['items'] if r['kind'] == 'job' and r['source_id'] == 'J2')
            cases = json.loads((ROOT / 'contracts/examples/pilot-cases.json').read_text())
            fields = ('released_gpu_hours', 'scenario_gpu_hours', 'added_cpu_vcpu_hours',
                      'added_cpu_reference_usd', 'net_reference_value_usd',
                      'run_time_change_hours_excluding_queue', 'completion_change_hours_including_extra_queue')
            for case in cases:
                payload = copy.deepcopy(request)
                payload['scenario']['cpu_pilot'] = {**case['input'], 'baseline_evidence_id': ref['id']}
                response = await client.post(a_url + '/api/audits', json=payload)
                response.raise_for_status()
                audit = response.json()
                result = await review(a_url, c_url, audit['audit_id'])
                # Oracles predate this harness; don't import C's calculator to grade C.
                expected = case['result']
                result['checks']['hand_worked_cpu_fields'] = all(audit['downside']['cpu_pilot'][k] == expected[k] if expected[k] is None
                    else abs(audit['downside']['cpu_pilot'][k] - expected[k]) < 1e-8 for k in fields)
                attempts.append({'case': case['name'], **result})
            missing = await client.post(c_url + '/api/audits/nonexistent-audit/explanations',
                                        json={'client_request_id': 'missing', 'question': 'Review evidence'})
            negatives = {'missing_audit_404': missing.status_code == 404 and missing.json()['error']['code'] == 'AUDIT_NOT_FOUND'}
            for attempt in attempts:
                attempt['checks']['no_false_failures'] = attempt['check_counts']['fail'] == 0
                attempt['checks']['unknown_lineage_preserved'] = 'mcp.source_identity: UNKNOWN' in attempt['response']['answer']
            return {'scope': 'Actual A/C processes and MCP; original synthetic input, data readiness explicitly replaced in test peer',
                    'a_source_commit': subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', 'analysis', 'service'], cwd=ROOT, text=True).strip(),
                    'attempts': attempts, 'negative_checks': negatives,
                    'canonical_data_acceptance': 'NOT RUN: this test does not use the organizer five-file bundle'}
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(run())
    write_private(args.output, result)
    print(json.dumps({'cases': {a['case']: {'checks': a['checks'], 'counts': a['check_counts']} for a in result['attempts']},
                      'negative_checks': result['negative_checks'], 'scope': result['scope']}))
    raise SystemExit(0 if all(all(a['checks'].values()) for a in result['attempts']) and all(result['negative_checks'].values()) else 1)


if __name__ == '__main__':
    main()
