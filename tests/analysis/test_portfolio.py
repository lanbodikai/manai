"""Original invented jobs; substantive boundary, assignment and API regressions."""
import copy
import json
import unittest
from unittest.mock import patch
import jsonschema
import test_analysis as fixtures
from analysis.portfolio import PRESETS, ACTIONS, RULES, calculate, job_case, evaluability
from eval.analysis.portfolio_reference import reference, close
from service.portfolio_routes import validate_request, SCHEMA


def rows():
    base = dict(state_name='COMPLETED', sm_util_avg=0, sm_util_max=0, gpu_hours=16, gpu_count=2,
                walltime_sec=28800, nodes_alloc=1, n_nodes_listed=1, cpus_req=4, mem_req_total_mb=16000,
                max_gpu_mem_used=0, job_type='BATCH')
    return [{**base,'id_job':'invented-cpu-idle','job_type':'LLSUB:INTERACTIVE'},
            {**base,'id_job':'invented-idle-timeout','job_type':'LLSUB:INTERACTIVE','state_name':'TIMEOUT'},
            {**base,'id_job':'invented-timeout','state_name':'TIMEOUT','sm_util_avg':70,'sm_util_max':90},
            {**base,'id_job':'invented-bad-accounting','state_name':'TIMEOUT','gpu_hours':50},
            {**base,'id_job':'invented-cancelled','state_name':'CANCELLED'}]


def config():
    return {**copy.deepcopy(PRESETS),'dataset_version':'invented-version'}


def built(request=None):
    return calculate(rows(),None,request or config(),'invented-fingerprint',2.5,'invented-pricebook',True)


class PortfolioMath(unittest.TestCase):
    def test_reference_and_exact_checkpoint_boundaries(self):
        for seconds in (1,3599,3600,3601,7200,28800):
            row={**rows()[0],'walltime_sec':seconds,'gpu_hours':seconds/1800}
            for action in ACTIONS:
                for case in config()['cases']:
                    for allocation in ('memory_adjusted','whole_node'):
                        actual=job_case(row,action,case,allocation,2.5)
                        for key,value in reference(row,action,case,allocation,2.5).items():close(actual[key],value)
        exact=job_case({**rows()[0],'walltime_sec':3600},'timeouts',config()['cases'][0],'memory_adjusted',2.5)
        self.assertEqual(exact['checkpoints'],0)
        self.assertLess(exact['net_reference_usd'],0)

    def test_exclusions_cancellation_and_assignment(self):
        result,jobs=built()
        assignments={j['job_id']:j['assigned_action'] for j in jobs}
        self.assertEqual(assignments,{'invented-cpu-idle':'cpu-placement','invented-idle-timeout':'idle-sessions',
                                     'invented-timeout':'timeouts','invented-bad-accounting':None})
        self.assertEqual(result['coverage']['overlapping_references_removed'],2)
        request=config();request['selected_actions']=['timeouts']
        self.assertEqual(next(j for j in built(request)[1] if j['job_id']=='invented-idle-timeout')['assigned_action'],'timeouts')
        r=rows()[0]
        self.assertIsNone(evaluability({**r,'gpu_hours':17.6},'timeouts'))
        self.assertEqual(evaluability({**r,'gpu_hours':17.6001},'timeouts'),'accounting_discrepancy_over_10_percent')
        for key,value in [('walltime_sec',None),('gpu_count',0),('gpu_count',1.5)]:self.assertIsNotNone(evaluability({**r,key:value},'timeouts'))

    def test_no_replay_no_release_and_failure(self):
        row=rows()[0];c=config()['cases'][1]
        x=job_case(row,'timeouts',{**c,'replay_fraction':0},'memory_adjusted',2.5)
        self.assertEqual(x['net_reference_usd'],x['failure_net_reference_usd'])
        self.assertLess(x['net_reference_usd'],0)
        x=job_case(row,'idle-sessions',{**c,'release_hours':8},'memory_adjusted',2.5)
        self.assertEqual(x['net_reference_usd'],0);self.assertEqual(x['failure_net_reference_usd'],0)
        x=job_case(row,'idle-sessions',{**c,'mistake_fraction':1},'memory_adjusted',2.5)
        self.assertEqual(x['net_reference_usd'],x['failure_net_reference_usd']);self.assertLess(x['net_reference_usd'],0)

    def test_monotonicity_and_signed_portfolio(self):
        row=rows()[0];c=config()['cases'][1]
        for action,key,value in [('timeouts','checkpoint_minutes',20),('timeouts','replay_fraction',0),
                                 ('idle-sessions','mistake_fraction',1),('cpu-placement','cpu_price_ratio',1)]:
            self.assertLessEqual(job_case(row,action,{**c,key:value},'memory_adjusted',2.5)['net_reference_usd'],
                                 job_case(row,action,c,'memory_adjusted',2.5)['net_reference_usd'])
        request=config();request['overheads']['timeouts']['setup_usd']=10000
        result,_=built(request)
        self.assertLess(result['bounds']['net_reference_usd']['high'],0)
        for c in result['cases']:
            self.assertAlmostEqual(c['net_reference_usd'],sum(next(v for v in a['cases'] if v['id']==c['id'])['net_reference_usd'] for a in result['actions']))
            self.assertGreater(c['remaining_target_reference_usd'],result['target_reference_usd'])
        request['selected_actions']=[]
        self.assertEqual(built(request)[0]['bounds']['net_reference_usd'],{'low':0,'high':0})

    def test_schema_invalid_and_nulls(self):
        jsonschema.validate(built()[0],{**SCHEMA,'$ref':'#/$defs/summary'})
        validate_request(config())
        for key,value in [('interval_minutes',0),('release_hours',.1),('mistake_fraction',2),('cpu_price_ratio',float('nan'))]:
            request=config();request['cases'][0][key]=value
            with self.assertRaises((ValueError,jsonschema.ValidationError)):validate_request(request)
        result,_=built()
        self.assertIsNone(next(a for a in result['actions'] if a['id']=='idle-sessions')['cases'][0]['modeled_elapsed_change_hours'])

    def test_screening_findings_and_priority(self):
        r={**rows()[0],'id_job':'invented-screening','state_name':'FAILED','sm_util_avg':20}
        findings=[{'id':'invented-'+a,'detectorId':RULES[a],'metadata':{'job_id':r['id_job'],'impact_scope':'job','impact_kind':'consumed'}} for a in ACTIONS[3:]]
        result,jobs=calculate([r],findings,config(),'invented',2.5,'v',True)
        self.assertEqual(jobs[0]['assigned_action'],'startup-failures')
        self.assertEqual(result['coverage']['overlapping_references_removed'],4)
        for a in result['actions'][3:]:
            self.assertEqual(a['model_kind'],'assumption_only_screening')
            self.assertEqual(a['diagnosed_jobs'],1)
            self.assertGreater(a['standalone_cases'][2]['net_reference_usd'],0)


class PortfolioRoutes(unittest.TestCase):
    def setUp(self):
        fixtures.Routes.setUp(self)
        self.patcher=patch('service.portfolio_routes.load_source',return_value=('invented-version',rows(),None));self.patcher.start()
    def tearDown(self):self.patcher.stop();fixtures.Routes.tearDown(self)
    def test_snapshot_identity_evidence_eviction_and_claims(self):
        audit=fixtures.Routes.create(self);claims_path='/api/audits/'+audit['audit_id']+'/claims?team=Synthetic'
        claims=self.client.get(claims_path).json();response=self.client.post('/api/portfolio-simulations',json=config())
        self.assertEqual(response.status_code,201,response.text);result=response.json();sid=result['simulation_id']
        path='/api/portfolio-simulations/'+sid;args={'dataset_version':'invented-version'}
        page=self.client.get(path+'/evidence',params={**args,'limit':1}).json()
        self.assertEqual(len(page['items']),1)
        self.assertEqual(self.client.get(path,params=args).json(),result)
        self.assertEqual(self.client.get(path,params={'dataset_version':'stale'}).status_code,409)
        self.assertEqual(self.client.get(path+'/evidence',params={**args,'limit':101}).status_code,422)
        self.assertEqual(self.client.post('/api/portfolio-simulations',json={**config(),'dataset_version':'stale'}).status_code,409)
        for n in range(17):
            request=config();request['overheads']['timeouts']['setup_usd']=n+1
            self.assertEqual(self.client.post('/api/portfolio-simulations',json=request).status_code,201)
        self.assertEqual(self.client.get(path,params=args).status_code,404)
        self.assertEqual(self.client.get(claims_path).json(),claims)
        self.assertEqual(self.client.get('/api/audits/'+audit['audit_id']).json(),audit)
    def test_source_failures_are_explicit(self):
        with patch('service.portfolio_routes.load_source',side_effect=ValueError('bad')):
            self.assertEqual(self.client.post('/api/portfolio-simulations',json=config()).status_code,503)
