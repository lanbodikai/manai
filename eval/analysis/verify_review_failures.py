"""Real local source and MCP; only model transport is replaced with explicit faults."""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import patch

import httpx
from service.main import app, lifespan
from service.portfolio_routes import load_source


async def run():
    original = httpx.AsyncClient
    # Never use the configured credential in this deterministic failure run.
    os.environ.pop('FEATHERLESS_API_KEY', None)
    async with lifespan(app):
        async with original(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            config = json.loads(Path('contracts/portfolio-presets.json').read_text())
            config['dataset_version'] = load_source(app.state)[0]
            created = await client.post('/api/portfolio-simulations', json=config)
            assert created.status_code == 201, created.text
            snapshot = created.json()
            sid = snapshot['simulation_id']
            path = '/api/portfolio-simulations/' + sid
            body = {'dataset_version':config['dataset_version'], 'action':'all',
                    'question':'Which assumptions are untested?', 'client_request_id':'release-fault-check'}
            health = await client.get('/api/health')
            assert health.status_code == 200
            cases = []
            for mode, status in [('no_key',200), ('unavailable',503), ('malformed',502), ('invented_id',502), ('timeout',504)]:
                class FaultClient:
                    def __init__(self,*args,**kwargs): pass
                    async def __aenter__(self): return self
                    async def __aexit__(self,*args): pass
                    @asynccontextmanager
                    async def stream(self,*args,**kwargs):
                        if mode == 'timeout': raise httpx.ReadTimeout('injected test timeout')
                        data = {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'selected_fact_ids':['invented-fact']})}}]}
                        content = b'not JSON' if mode == 'malformed' else json.dumps(data).encode()
                        yield httpx.Response(503 if mode == 'unavailable' else 200, content=content)
                if mode == 'no_key':
                    response = await client.post(path+'/review',json=body)
                    assert response.json()['usage']['model'] is None
                else:
                    os.environ['FEATHERLESS_API_KEY']='synthetic-test-key-not-a-credential'
                    with patch('service.simulation_review.httpx.AsyncClient',FaultClient):
                        response = await client.post(path+'/review',json=body)
                assert response.status_code == status, (mode,response.text)
                frozen = await client.get(path,params={'dataset_version':config['dataset_version']})
                assert frozen.status_code == 200 and frozen.json() == snapshot
                assert (await client.get('/api/overview')).status_code == 200
                assert app.state.chat_slots._value == 2
                cases.append({'mode':mode,'status':status,'snapshot_unchanged':True,'overview_available':True,'chat_capacity_restored':True})
            print(json.dumps({'result':'PASS','cases':cases}))


if __name__ == '__main__': asyncio.run(run())
