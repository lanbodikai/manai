"""Export the documented conservative scenario locally; never publish source data."""
import argparse
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:3000')
    parser.add_argument('--team', default='MANAI')
    args = parser.parse_args()

    def call(route, body=None):
        request = Request(args.url.rstrip('/') + route,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    health, overview = call('/api/health'), call('/api/overview')
    assert health['data_status'] == 'ready' and health['contract_version'] == '0.4'
    assert not overview['provenance']['synthetic']
    audit = call('/api/audits', {
        'client_request_id': str(uuid.uuid4()), 'expected_data_fingerprint': health['data_fingerprint'],
        'recommendation_id': 'cpu-placement-pilot', 'scenario': {
            'recovery_fraction': {'low': 0, 'point': 0, 'high': 1},
            'usd_per_gpu_hour': overview['usd_per_gpu_hour'], 'cancelled_policy': 'exclude',
            'interval_kind': 'scenario',
            'assumption_note': 'No empirical CPU recoverability: zero low/point; high is the physical eligibility ceiling, not a forecast.',
        },
    })
    claims = call(f"/api/audits/{quote(audit['audit_id'], safe='')}/claims?team={quote(args.team, safe='')}")
    for bound in ('low', 'point', 'high'):
        assert claims['recoverable_gpu_hours'][bound] == audit['recovery']['gpu_hours'][bound]
        assert claims['recoverable_usd'][bound] == audit['recovery']['reference_usd']['values'][bound]
    private = Path('private-eval/integration')
    private.mkdir(parents=True, exist_ok=True)
    (private / 'final-default-audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    Path('claims.json').write_text(json.dumps(claims, indent=2), encoding='utf-8')
    print('PASS: local root claims.json matches the documented 0/0/1 scenario; no publication performed.')


if __name__ == '__main__':
    main()
