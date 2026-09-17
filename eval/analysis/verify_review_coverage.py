"""Check full frozen-snapshot review with local data and actual MCP, without a key."""
import asyncio
import json
import os
from pathlib import Path

import httpx
from service.main import app, lifespan
from service.portfolio_routes import load_source


async def run():
    os.environ.pop('FEATHERLESS_API_KEY', None)
    async with lifespan(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            config = json.loads(Path('contracts/portfolio-presets.json').read_text())
            config['dataset_version'] = load_source(app.state)[0]
            response = await client.post('/api/portfolio-simulations', json=config)
            assert response.status_code == 201, response.status_code
            snapshot = response.json()
            path = '/api/portfolio-simulations/' + snapshot['simulation_id']
            response = await client.post(path + '/review', json={
                'dataset_version': config['dataset_version'], 'action': 'all',
                'question': 'Reconcile every assigned contribution with the frozen evidence.',
                'client_request_id': 'full-snapshot-coverage-check'})
            assert response.status_code == 200, response.status_code
            report = response.json()
            assert report['coverage']['complete'] and report['coverage']['retrieved'] > 100
            assert not [c for c in report['checks'] if c['status'] == 'fail']
            assert len([c for c in report['checks'] if c['id'].endswith('.evidence_totals') and c['status'] == 'pass']) == len(snapshot['actions'])
            assert report['status'] == 'insufficient_evidence'
            assert next(c for c in report['checks'] if c['id'] == 'source_proof')['status'] == 'unknown'
            assert len(report['source_examples']) <= 3 and report['usage']['model'] is None
            frozen = await client.get(path, params={'dataset_version': config['dataset_version']})
            assert frozen.json() == snapshot
            print(json.dumps({'result': 'PASS', 'coverage': report['coverage'],
                              'checks': len(report['checks']), 'displayed_examples': len(report['source_examples']),
                              'snapshot_unchanged': True, 'model': None}))


if __name__ == '__main__':
    asyncio.run(run())
