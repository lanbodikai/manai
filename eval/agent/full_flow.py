"""Run isolated full-flow simulation; actual services/MCP and invented disk data.

Requires built dashboard/dist and Node 22. Outputs/logs/screenshots are private.
No deployment, provider call, canonical-data acceptance or workload execution.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx

from eval.agent.http_smoke import free_port, wait_ready
from eval.agent.live_review import write_private
from eval.agent.simulation_data import prepare

ROOT = Path(__file__).resolve().parents[2]


async def run(node, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    runtime = prepare(output / 'runtime')
    env = {k: os.environ[k] for k in ('PATH','HOME','SYSTEMROOT','WINDIR','TEMP','TMP') if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE='1', REVIEWER_MODE='deterministic', REVIEWER_MCP_CONTEXT='price_only', PLAYWRIGHT_CHANNEL='chrome')
    processes, logs, reports = [], [], []

    def start(command, cwd, extra, name):
        log = (output / (name+'.log')).open('w')
        logs.append(log)
        p = subprocess.Popen(command,cwd=cwd,env={**env,**extra},stdout=log,stderr=subprocess.STDOUT)
        processes.append(p)
        return p

    async def service(module, cwd, extra, health, name):
        port=free_port()
        url=f'http://127.0.0.1:{port}'
        p=start([sys.executable,'-m','uvicorn',module,'--host','127.0.0.1','--port',str(port)],cwd,extra,name)
        await wait_ready(client,url+health)
        return p,url

    async def dashboard(a_url,c_url,name):
        port=free_port()
        url=f'http://127.0.0.1:{port}'
        extra=dict(HOST='127.0.0.1',PORT=str(port),ANALYSIS_URL=a_url,
                   DASHBOARD_DIST=str(ROOT/'dashboard/dist'),DATASET_DB=str(output/'not-prepared.sqlite'))
        if c_url: extra['REVIEWER_URL']=c_url
        start([node,'--experimental-strip-types','server.mjs'],ROOT/'dashboard',extra,name)
        await wait_ready(client,url+'/api/health')
        return url

    async def browser(url,mode):
        print('Running production-browser phase: '+mode,flush=True)
        command=[node,str(ROOT/'eval/agent/full_flow_browser.cjs'),url,mode,str(output)]
        proc=await asyncio.create_subprocess_exec(*command,cwd=ROOT,env=env,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:
            stdout,stderr=await asyncio.wait_for(proc.communicate(),timeout=180)
        except BaseException:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
            raise
        (output/(mode+'-browser.log')).write_bytes(stdout+stderr)
        if proc.returncode:
            raise RuntimeError(f'{mode} browser failed; see {output / (mode+"-browser.log")}')
        report=json.loads(stdout.decode().strip().splitlines()[-1])
        reports.append(report)
        print(json.dumps(report),flush=True)

    try:
        async with httpx.AsyncClient(timeout=35,trust_env=False) as client:
            _,api_url=await service('api.main:app',runtime,{},'/health','official-api')
            _,a_url=await service('eval.agent.simulation_service:app',runtime,{'MGAI_URL':api_url},'/api/health','analysis')
            # No C process exists during the default-base phase.
            base_url=await dashboard(a_url,None,'dashboard-base')
            await browser(base_url,'unconfigured')
            c,c_url=await service('reviewer.main:app',runtime,{'ANALYSIS_URL':a_url},'/health','reviewer')
            full_url=await dashboard(a_url,c_url,'dashboard-reviewer')
            await browser(full_url,'full')
            c.terminate()
            c.wait(timeout=5)
            await browser(full_url,'crashed')
            _,fault_url=await service('eval.agent.fault_service:app',ROOT,{},'/health','fault-peer')
            faults_url=await dashboard(a_url,fault_url,'dashboard-faults')
            await browser(faults_url,'faults')
            validation=await asyncio.create_subprocess_exec(sys.executable,'scripts/validate_submission.py',
                '--claims',str(output/'full-claims.json'),'--url',full_url,cwd=ROOT,env=env,
                stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
            stdout,_=await asyncio.wait_for(validation.communicate(),timeout=30)
            (output/'submission-check.log').write_bytes(stdout)
            if validation.returncode: raise RuntimeError('Synthetic claims/schema/URL check failed')
            result={'result':'PASS','phases':reports,'submission_schema_url':'PASS for synthetic output only',
                    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    'limits':['Simulation data only; organizer dataset and Docker unavailable.',
                              'A wrapper adjusts provenance only. Readiness, checksums and source HTTP are real.',
                              'No dataset-browser cache was prepared; Data explorer is outside this simulated flow.',
                              'Compose build-failure isolation and actual workload execution not tested.']}
            write_private(output/'receipt.json',result)
            return result
    finally:
        for p in processes:
            if p.poll() is None: p.terminate()
        for p in processes:
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill(); p.wait(timeout=5)
        for log in logs: log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',required=True)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    result=asyncio.run(run(args.node,args.output_dir))
    print(json.dumps({'result':result['result'],'phases':[r['mode'] for r in result['phases']]}))


if __name__=='__main__': main()
