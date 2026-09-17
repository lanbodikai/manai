"""Actual A routes/calculator with original synthetic input, for socket tests only.

This replaces data readiness/context in a standalone test process. It is not a
canonical-data test and is never imported by reviewer runtime.
"""
from contextlib import asynccontextmanager
from unittest.mock import patch

from analysis.core import RULE, audit_impacts, make_evidence, select_cohort
from service.audits import freeze_evidence
from service.main import app, lifespan as a_lifespan


def context():
    jobs = [dict(id_job='J1', state_name='COMPLETED', sm_util_avg=0, sm_util_max=0,
                 gpu_hours=10, gpu_count=1, walltime_sec=36000, max_gpu_mem_used=100),
            dict(id_job='J2', state_name='COMPLETED', sm_util_avg=0, sm_util_max=0,
                 gpu_hours=20, gpu_count=2, walltime_sec=36000, max_gpu_mem_used=0)]
    findings = [dict(id='invented-finding-1', detectorId=RULE,
                    metadata=dict(job_id='J1', impact_scope='job', impact_kind='unused_capacity', impact_gpu_hours=10))]
    cohort = select_cohort(jobs)
    impacts = audit_impacts(cohort, findings)
    provenance = dict(data_fingerprint='synthetic-socket-v04', source_version='original-c-test-v1',
                      synthetic=True, sample_label='Original invented socket test jobs',
                      window_label='Invented window; not production telemetry', caveats=['Synthetic test only'])
    evidence = make_evidence(cohort, impacts, findings, {'summary': 'Invented CPU rule'}, provenance)
    return freeze_evidence(dict(cohort=cohort, impacts=impacts, evidence=evidence,
                               provenance=provenance, findings=findings, upstream={'recommendations': []}))


@asynccontextmanager
async def lifespan(application):
    with patch('service.main.inspect_data', return_value={'status': 'missing', 'fingerprint': None, 'signature': None}), \
         patch('service.main.current_status', return_value='ready'), \
         patch('service.analysis_routes.current_status', return_value='ready'):
        async with a_lifespan(application):
            application.state.source = {'status': 'ready', 'fingerprint': 'synthetic-socket-v04', 'signature': None}
            application.state.analysis_context = context()
            yield


app.router.lifespan_context = lifespan
