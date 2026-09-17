"""Read an existing real A audit through C; never creates or changes A's state.

python -m eval.agent.live_review --analysis-url URL --reviewer-url URL \
  --audit-id ID --output reviewer/.private/live.json
Uses actual HTTP, verifies scoped citations, and compares audit/claims before and
after. Synthetic provenance stays explicit. No provider call is authorized here:
C must report deterministic mode in its health response.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

import httpx
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


async def review(analysis_url, reviewer_url, audit_id, *, explanations_url=None):
    base = analysis_url.rstrip('/') + '/api/audits/' + quote(audit_id, safe='')
    async with httpx.AsyncClient(timeout=35, trust_env=False, follow_redirects=False) as client:
        health = await client.get(reviewer_url.rstrip('/') + '/health')
        health.raise_for_status()
        if health.json().get('mode') != 'deterministic':
            raise ValueError('This evaluation requires deterministic C; no model calls are allowed')
        before_a = await client.get(base)
        before_a.raise_for_status()
        audit = before_a.json()
        before_c = await client.get(base + '/claims', params={'team': 'C validation'})
        before_c.raise_for_status()
        response = await client.post((explanations_url or reviewer_url).rstrip('/') + '/api/audits/' + quote(audit_id, safe='') + '/explanations',
                                     json={'client_request_id': 'c-v04-live-review', 'question': 'Review evidence, CPU cost, downside risk and recovery assumptions.'})
        response.raise_for_status()
        body = response.json()
        spec = json.loads((ROOT / 'contracts/openapi.json').read_text())
        Draft202012Validator({'$ref': '#/components/schemas/Explanation', **spec}).validate(body)
        cited = body['supporting_evidence_ids']
        citations_resolve = len(cited) == len(set(cited))
        for eid in cited:
            result = await client.get(base + '/evidence/' + quote(eid, safe=''))
            if result.status_code != 200:
                citations_resolve = False
                continue
            detail = result.json()
            citations_resolve &= detail['audit_id'] == audit_id and detail['evidence']['id'] == eid
            citations_resolve &= detail['provenance']['data_fingerprint'] == audit['provenance']['data_fingerprint']
        after_a = await client.get(base)
        after_a.raise_for_status()
        after_c = await client.get(base + '/claims', params={'team': 'C validation'})
        after_c.raise_for_status()
        count = re.search(r'Independent checks: (\d+) PASS, (\d+) FAIL, (\d+) UNKNOWN', body['answer'])
        checks = {
            'active_v04': audit['contract_version'] == '0.4' and health.json().get('contract_version') == '0.4',
            'identity': body['audit_id'] == audit_id and body['client_request_id'] == 'c-v04-live-review',
            'scoped_citations': citations_resolve,
            'audit_unchanged': audit == after_a.json(),
            'claims_unchanged': before_c.json() == after_c.json(),
            'live_mcp': body['usage']['tool_calls'] >= 2 and len(body['tool_trace_ids']) >= 2,
            'no_provider': body['usage']['model'] is None and body['usage']['provider'] is None,
            'check_counts_present': count is not None,
        }
        return {'scope': 'Actual A and C HTTP services with ' + ('synthetic test inputs' if audit['provenance']['synthetic'] else 'A-reported non-synthetic audit'),
                'data_fingerprint': audit['provenance']['data_fingerprint'], 'audit_id': audit_id,
                'source_provenance': audit['provenance'], 'checks': checks,
                'check_counts': dict(zip(('pass', 'fail', 'unknown'), map(int, count.groups()))) if count else None,
                'response': body,
                'limits': 'A reported source identity is checked, not independently certified by MCP price-book metadata. No workload or model evaluation.'}


def write_private(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-url', required=True)
    parser.add_argument('--reviewer-url', required=True)
    parser.add_argument('--explanations-url', help='Optional dashboard proxy origin; health still uses the direct reviewer URL')
    parser.add_argument('--audit-id', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = asyncio.run(review(args.analysis_url, args.reviewer_url, args.audit_id, explanations_url=args.explanations_url))
    write_private(args.output, result)
    print(json.dumps({'scope': result['scope'], 'checks': result['checks'], 'check_counts': result['check_counts']}))
    raise SystemExit(0 if all(result['checks'].values()) else 1)


if __name__ == '__main__':
    main()
