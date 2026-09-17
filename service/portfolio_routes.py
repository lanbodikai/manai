"""Source-bound, immutable and bounded portfolio simulation snapshots."""
import asyncio
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
from typing import Literal
import jsonschema
import pandas as pd
from fastapi import APIRouter, Request, Query
from api.models import PriceBook
from analysis.portfolio import calculate
from service.analysis_routes import require_data, ServiceError
from service.hardware_routes import FILES

router = APIRouter()
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / 'contracts/portfolio-simulation.schema.json').read_text())


def validate_request(body):
    json.dumps(body, allow_nan=False)
    jsonschema.validate(body, {**SCHEMA, '$ref': '#/$defs/request'})
    if [c['id'] for c in body['cases']] != ['lower', 'illustrative', 'upper']:
        raise ValueError('Cases must retain their identities and order')


def load_source(state):
    checks = dict(line.split()[::-1] for line in (state.data_dir / 'checksums.txt').read_text().splitlines() if line.strip() and not line.startswith('#'))
    version = hashlib.sha256(''.join(checks[n] for n in FILES).encode()).hexdigest()
    return version, pd.read_parquet(state.data_dir / 'prepped/jobs.parquet').to_dict('records'), json.loads((state.data_dir / 'synthetic/findings.json').read_text())


@router.post('/api/portfolio-simulations', status_code=201)
async def create(request: Request):
    require_data(request)
    try:
        body = await request.json()
        validate_request(body)
    except (ValueError, TypeError, jsonschema.ValidationError):
        raise ServiceError(422, 'INVALID_SIMULATION', 'Use finite assumptions within the portfolio-simulation-1 contract.')
    state = request.app.state
    async with state.portfolio_lock:
        try:
            if state.portfolio_source is None:
                state.portfolio_source = await asyncio.to_thread(load_source, state)
            version, rows, findings = state.portfolio_source
            if body['dataset_version'] != version:
                raise ServiceError(409, 'DATA_VERSION_MISMATCH', 'Reload the canonical dataset before modeling.')
            cache_key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
            if cache_key in state.portfolio_requests:
                sid = state.portfolio_requests[cache_key]
                if sid in state.portfolio_snapshots:
                    require_data(request, snapshot=True)
                    return json.loads(state.portfolio_snapshots[sid])['result']
            prices = PriceBook()
            result, evidence = await asyncio.to_thread(calculate, rows, findings, body, state.source['fingerprint'], prices.usd_per_gpu_hour, prices.version)
            require_data(request, snapshot=True)
            encoded = json.dumps({'result': result, 'evidence': evidence}, allow_nan=False)
        except (ValueError, TypeError, KeyError, OSError, OverflowError):
            raise ServiceError(503, 'SIMULATION_SOURCE_INVALID', 'The source cannot support a reconciled portfolio simulation.')
        sid = result['simulation_id']
        state.portfolio_snapshots[sid] = encoded
        state.portfolio_requests[cache_key] = sid
        while len(state.portfolio_snapshots) > 16:
            old, _ = state.portfolio_snapshots.popitem(last=False)
            state.portfolio_requests = {k: v for k, v in state.portfolio_requests.items() if v != old}
        return result


def get_snapshot(request, sid, version):
    require_data(request, snapshot=True)
    value = request.app.state.portfolio_snapshots.get(sid)
    if value is None:
        raise ServiceError(404, 'SIMULATION_NOT_FOUND', 'This simulation expired or does not exist. Recalculate it.')
    payload = json.loads(value)
    if payload['result']['dataset_version'] != version:
        raise ServiceError(409, 'DATA_VERSION_MISMATCH', 'Simulation belongs to another dataset.')
    return payload


@router.get('/api/portfolio-simulations/{sid}')
async def read(sid: str, request: Request, dataset_version: str):
    return get_snapshot(request, sid, dataset_version)['result']


@router.get('/api/portfolio-simulations/{sid}/evidence')
async def evidence(sid: str, request: Request, dataset_version: str,
                   action: Literal['all', 'cpu-placement', 'idle-sessions', 'timeouts', 'startup-failures', 'failed-arrays', 'low-utilization', 'gpu-imbalance', 'memory-sizing', 'excluded'] = 'all',
                   offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100)):
    snapshot = get_snapshot(request, sid, dataset_version)
    items = [j for j in snapshot['evidence'] if action == 'all' or
             (action == 'excluded' and j['assigned_action'] is None) or j['assigned_action'] == action]
    return {'contract_version': 'portfolio-simulation-1', 'simulation_id': sid, 'dataset_version': dataset_version,
            'offset': offset, 'limit': limit, 'total': len(items), 'items': items[offset:offset+limit]}
