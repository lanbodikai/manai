"""Original, tiny on-disk simulation bundle. Never source-data acceptance."""
import json
from pathlib import Path
import shutil

import pandas as pd

from scripts.checksum_data import FILES, digest

ROOT = Path(__file__).resolve().parents[2]


def prepare(runtime):
    runtime.mkdir(parents=True, exist_ok=False)
    for name in ('api', 'analysis', 'service', 'mcp_layer', 'contracts', 'scripts', 'reviewer'):
        shutil.copytree(ROOT / name, runtime / name,
                        ignore=shutil.ignore_patterns('__pycache__', '.private', '.venv', '*.log', '.env'))
    (runtime / 'starter').mkdir()
    shutil.copy2(ROOT / 'starter/claims.schema.json', runtime / 'starter/claims.schema.json')
    (runtime / 'eval/agent').mkdir(parents=True)
    shutil.copy2(ROOT / 'eval/agent/simulation_service.py', runtime / 'eval/agent/simulation_service.py')
    data = runtime / 'data'
    (data / 'prepped').mkdir(parents=True)
    (data / 'synthetic').mkdir()
    (data / 'SIMULATION_ONLY').write_text('Invented test records. Never canonical organizer data.\n')
    jobs = [dict(id_job='J1', state_name='COMPLETED', is_success=True,
                 sm_util_avg=0., sm_util_max=0., gpu_hours=10., gpu_count=1,
                 walltime_sec=36000., max_gpu_mem_used=100., time_submit=0., time_end=36000., wait_sec=0.),
            dict(id_job='J2', state_name='COMPLETED', is_success=True,
                 sm_util_avg=0., sm_util_max=0., gpu_hours=20., gpu_count=2,
                 walltime_sec=36000., max_gpu_mem_used=0., time_submit=0., time_end=36000., wait_sec=0.)]
    pd.DataFrame(jobs).to_parquet(data / 'prepped/jobs.parquet', index=False)
    pd.DataFrame([dict(id_job=j['id_job'], Node='invented-node', gpu_id=i,
                       gpu_hours=10., totalexecutiontime_sec=36000., sm_util_avg=0.)
                  for j in jobs for i in range(j['gpu_count'])]).to_parquet(data / 'prepped/gpus.parquet', index=False)
    pd.DataFrame([dict(id='invented-pod-'+j['id_job'], type='k8s:pod', resourceId=j['id_job'], name='Invented '+j['id_job'])
                  for j in jobs]).to_parquet(data / 'synthetic/resources.parquet', index=False)
    pd.DataFrame({'source': pd.Series(dtype=str), 'target': pd.Series(dtype=str)}).to_parquet(data / 'synthetic/edges.parquet', index=False)
    findings = [dict(id='invented-finding-'+j['id_job'], integrationId='simulation', enterpriseId='simulation',
        detectorId='rules::gpu-not-needed', shortDescription='Invented CPU candidate',
        longDescription='Original synthetic fixture; not actual telemetry.', impactDescription='Scenario only',
        resourceIds=['invented-pod-'+j['id_job']], rootCauses=[], status='ACTIVE', severity='LOW', confidence='LOW',
        category='COST', priority='LOW', detectionTime='2026-01-01T00:00:00Z', isActive=True,
        metadata=dict(job_id=j['id_job'], synthetic=True, impact_scope='job', impact_kind='unused_capacity', impact_gpu_hours=j['gpu_hours']))
        for j in jobs]
    (data / 'synthetic/findings.json').write_text(json.dumps(findings))
    (data / 'checksums.txt').write_text('# ORIGINAL SIMULATION CHECKSUMS, not organizer checksums\n' +
        ''.join(f'{digest(data / name)}  {name}\n' for name in FILES))
    return runtime
