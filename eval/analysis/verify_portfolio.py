"""Exhaustive independent source/Decimal witness. All results stay private."""
import argparse
from datetime import datetime, timezone
from decimal import ROUND_CEILING
import hashlib
import json
import math
from pathlib import Path
import traceback
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import pandas as pd
from eval.analysis.verify_hardware_product import fingerprint, code_hash
from eval.analysis.portfolio_reference import D, reference, close

ACTIONS=['cpu-placement','idle-sessions','timeouts','startup-failures','failed-arrays','low-utilization','gpu-imbalance','memory-sizing']
RULES=['gpu-not-needed','idle-interactive-session','wallclock-kill','gpu-never-computed','array-task-failure','gpu-low-utilization','gpu-imbalance','gpu-memory-oversized']


def valid(x):return isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x)


def usable(row,action):
    if action in ACTIONS[3:]:return True
    if not valid(row['walltime_sec']) or row['walltime_sec']<=0 or not valid(row['gpu_count']) or row['gpu_count']<=0 or int(row['gpu_count'])!=row['gpu_count']:return False
    if action=='cpu-placement':
        return (row['nodes_alloc']==row['n_nodes_listed']==1 and valid(row['cpus_req']) and row['cpus_req']>0 and int(row['cpus_req'])==row['cpus_req'] and row['cpus_req']<=48 and valid(row['mem_req_total_mb']) and 0<row['mem_req_total_mb']<=192000)
    nominal=D(row['gpu_count'])*D(row['walltime_sec'])/3600
    return abs(D(row['gpu_hours'])-nominal)<=nominal/10


def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(args.source);data=Path(args.data)
    manifest={'started':datetime.now(timezone.utc).isoformat(),'revision':args.revision,'checks':[]}
    def save(name,value):(out/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
    def request(path,body=None):
        req=Request(args.url+path,data=json.dumps(body).encode() if body else None,headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=120) as r:return json.load(r)
    def passed(name):manifest['checks'].append(name);print('PASS',name,flush=True)
    try:
        manifest['before']=fingerprint(data);manifest['code_hash'],manifest['code_files']=code_hash(root)
        catalog=request('/api/datasets/catalog');config=json.loads((root/'contracts/portfolio-presets.json').read_text());config['dataset_version']=catalog['version']
        summary=request('/api/portfolio-simulations',config);save('summary.json',summary);save('configuration.json',config)
        rows=pd.read_parquet(data/'prepped/jobs.parquet').to_dict('records');by_id={str(r['id_job']):r for r in rows}
        assert len(rows)==len(by_id)
        findings=json.loads((data/'synthetic/findings.json').read_text())
        sets={a:{str(f['metadata']['job_id']) for f in findings if f.get('detectorId')=='rules::'+rule and f['metadata'].get('impact_scope')=='job' and not f['metadata'].get('synthetic',False) and by_id[str(f['metadata']['job_id'])]['state_name']!='CANCELLED'} for a,rule in zip(ACTIONS,RULES)}
        independent_cpu={k for k,r in by_id.items() if r['state_name']=='COMPLETED' and r['sm_util_avg']==r['sm_util_max']==0 and r['gpu_hours']>1 and (not valid(r['walltime_sec']) or r['walltime_sec']>=0)}
        assert sets['cpu-placement']==independent_cpu
        assert sets['timeouts']=={k for k,r in by_id.items() if r['state_name']=='TIMEOUT'}
        assert sets['idle-sessions']=={k for k,r in by_id.items() if r['state_name']!='CANCELLED' and r['job_type']=='LLSUB:INTERACTIVE' and r['walltime_sec']>14400 and 0<=r['sm_util_avg']<5}
        union=set().union(*sets.values());assigned={k:next((a for a in ACTIONS if k in sets[a] and usable(by_id[k],a)),None) for k in union}
        path='/api/portfolio-simulations/'+summary['simulation_id'];jobs=[]
        while len(jobs)<len(union):
            p=request(path+'/evidence?'+urlencode({'dataset_version':catalog['version'],'offset':len(jobs),'limit':100}))
            assert p['items'];jobs.extend(p['items'])
        assert len(jobs)==len(union) and {j['job_id'] for j in jobs}==union
        assert {j['job_id']:j['assigned_action'] for j in jobs}==assigned
        save('evidence.json',jobs)
        coverage=summary['coverage'];assert coverage['unique_jobs']==len(union)
        assert coverage['assigned_jobs']==sum(a is not None for a in assigned.values())
        assert coverage['overlapping_references_removed']==sum(len(v) for v in sets.values())-len(union)
        close(coverage['unique_gpu_hours'],sum(D(by_id[k]['gpu_hours']) for k in union))
        passed('PS01 source cohorts, coverage and exclusive assignment')
        price=D(summary['gpu_reference_usd_per_hour']);baseline=sum(D(r['gpu_hours']) for r in rows)*price
        close(summary['baseline_reference_usd'],baseline);close(summary['target_reference_usd'],baseline/5)
        fields=['gross_reference_usd','intervention_reference_usd','net_reference_usd','failure_net_reference_usd','enrolled_gpu_hours','released_gpu_hours','avoided_replay_gpu_hours','overhead_gpu_hours','cpu_core_hours']
        for c in config['cases']:
            totals={a:{field:D(0) for field in fields} for a in ACTIONS}
            for j in jobs:
                a=assigned[j['job_id']]
                if a is None:continue
                expected=reference(by_id[j['job_id']],a,c,config['cpu_allocation'],price)
                for field in fields:
                    close(j['cases'][c['id']][field],expected[field]);totals[a][field]+=expected[field]
            for a in ACTIONS:
                fixed=sum(D(x) for x in config['overheads'][a].values())
                totals[a]['intervention_reference_usd']+=fixed;totals[a]['net_reference_usd']-=fixed;totals[a]['failure_net_reference_usd']-=fixed
                action=next(x for x in summary['actions'] if x['id']==a)
                actual=next(x for x in action['cases'] if x['id']==c['id'])
                assert action['diagnosed_jobs']==len(sets[a]);assert action['assigned_jobs']==sum(x==a for x in assigned.values())
                assert action['excluded_jobs']==sum(not usable(by_id[k],a) for k in sets[a])
                for field in fields:close(actual[field],totals[a][field])
                standalone=sum(reference(by_id[k],a,c,config['cpu_allocation'],price)['net_reference_usd'] for k in sets[a] if usable(by_id[k],a))-fixed
                close(next(v for v in action['standalone_cases'] if v['id']==c['id'])['net_reference_usd'],standalone)
            actual=next(x for x in summary['cases'] if x['id']==c['id'])
            for field in fields:close(actual[field],sum(v[field] for v in totals.values()))
            net=sum(v['net_reference_usd'] for v in totals.values())
            close(actual['baseline_reduction_pct'],100*net/baseline);close(actual['target_contribution_pct'],500*net/baseline)
            close(actual['remaining_target_reference_usd'],max(D(0),baseline/5-net))
        passed('PS02 all per-job, standalone and portfolio Decimal cost comparisons')
        for key,b in summary['bounds'].items():
            close(b['low'],min(c[key] for c in summary['cases']));close(b['high'],max(c[key] for c in summary['cases']))
        assert request(path+'?'+urlencode({'dataset_version':catalog['version']}))==summary
        assert summary['cash_savings_verified'] is False and summary['performance_verified'] is False
        passed('PS03 complete-case ranges, target denominator and immutable result')
        manifest['after']=fingerprint(data);assert manifest['after']==manifest['before'];assert code_hash(root)[0]==manifest['code_hash']
        passed('PS04 unchanged canonical fingerprints and code')
        b=summary['bounds'];lines=['# Private portfolio simulation',f"Code: {args.revision}",f"Simulation: {summary['simulation_id']}",
          f"Simulated net reference cost reduction: ${b['net_reference_usd']['low']:,.2f}–${b['net_reference_usd']['high']:,.2f}.",
          f"Baseline reduction: {b['baseline_reduction_pct']['low']:.2f}%–{b['baseline_reduction_pct']['high']:.2f}%.",
          f"Failure stress: ${b['failure_extra_reference_usd']['low']:,.2f}–${b['failure_extra_reference_usd']['high']:,.2f} extra.",
          'Three detailed mechanisms plus five assumption-only screens. No preset tuning. No verified cash savings or research-performance benefit.',
          '| Action | Assigned jobs | Lower net | Illustrative net | Upper net |','|---|---:|---:|---:|---:|']
        for a in summary['actions']:lines.append('| '+a['id']+' | '+str(a['assigned_jobs'])+' | '+' | '.join(f"${c['net_reference_usd']:,.2f}" for c in a['cases'])+' |')
        (out/'REPORT.md').write_text('\n\n'.join(lines[:7])+'\n\n'+'\n'.join(lines[7:]),encoding='utf-8')
        manifest['status']='PASS'
    except Exception:
        manifest['status']='FAIL';(out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        manifest['finished']=datetime.now(timezone.utc).isoformat();save('manifest.json',manifest)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['data','output','revision']:p.add_argument('--'+n,required=True)
    p.add_argument('--source',default='/app');p.add_argument('--url',default='http://dashboard:3000');run(p.parse_args())
