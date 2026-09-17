"""Local-only fault peer for full-flow simulation; never a reviewer runtime."""
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()


@app.get('/health')
async def health():
    return {'fault_peer': True}


@app.post('/api/audits/{audit_id}/explanations')
async def fault(audit_id: str, request: Request):
    body = await request.json()
    if body['question'] == 'hang':
        await asyncio.sleep(40)
    if body['question'] == 'malformed':
        return Response('{broken', media_type='application/json')
    if body['question'] == 'wrong-audit':
        result = json.loads((Path(__file__).resolve().parents[2] / 'contracts/examples/explanation-response.json').read_text())
        result.update(audit_id='wrong-audit', client_request_id=body['client_request_id'])
        return result
    return JSONResponse(status_code=503, content={'error': dict(code='AGENT_UNAVAILABLE',
        message='Injected simulation outage', retryable=True, request_id=body['client_request_id'])})
