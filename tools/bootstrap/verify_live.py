"""Run inside analysis image against same-origin bootstrap page."""
import json
import os
from pathlib import Path
import httpx
import jsonschema

root=Path(__file__).resolve().parents[2]
spec=json.loads((root/'contracts/openapi.json').read_text())
def validate(name,payload):
    jsonschema.Draft202012Validator({**spec,"$ref":"#/components/schemas/"+name}).validate(payload)

with httpx.Client(base_url=os.getenv('BOOTSTRAP_URL','http://dashboard:3000'),timeout=30) as client:
    page=client.get('/')
    assert page.status_code==200 and 'Not the finished dashboard' in page.text
    health=client.get('/api/health'); assert health.status_code==200
    validate('Health',health.json()); assert health.json()['data_status']=='ready'
    overview=client.get('/api/overview'); assert overview.status_code==200
    validate('Overview',overview.json())
    assert overview.json()['provenance']['data_fingerprint']==health.json()['data_fingerprint']
    assert overview.json()['provenance']['synthetic'] is False
    assert overview.json()['job_count']>0
    fixture=client.get('/bootstrap/fixture.json'); validate('Audit',fixture.json())
    assert fixture.json()['provenance']['synthetic'] is True
    missing=client.get('/api/audits/bootstrap-missing')
    assert missing.status_code==404 and missing.json()['error']['code']=='AUDIT_NOT_FOUND'
    validate('Error',missing.json())
    optional=client.post('/api/audits/bootstrap-missing/explanations',json={'client_request_id':'probe','question':'why?'})
    assert optional.status_code==503 and optional.json()['error']['code']=='AGENT_UNAVAILABLE'
    assert client.get('/api/overview').status_code==200
    with httpx.Client(base_url=os.getenv('MGAI_URL','http://api:8000'),timeout=30) as upstream:
        live_spec=upstream.get('/openapi.json').json()
        assert '/v1/efficiency/summary' in live_spec['paths']
        summary=upstream.get('/v1/efficiency/summary').json()
        assert overview.json()['allocated_gpu_hours']==summary['value']
    example=json.loads((root/'contracts/examples/claims-response.json').read_text())
    official=json.loads((root/'starter/claims.schema.json').read_text()) if (root/'starter/claims.schema.json').exists() else None
    if official is None: raise RuntimeError('Official schema must be available')
    jsonschema.validate(example,official)
    print(json.dumps({'result':'PASS','contract':'0.3','real_overview':True,
        'synthetic_fixture_labeled':True,'error_404':True,'reviewer_disabled_503':True,
        'official_api_shape_inspected':True,'official_claims_fixture_valid':True,
        'data_fingerprint':health.json()['data_fingerprint']}))
