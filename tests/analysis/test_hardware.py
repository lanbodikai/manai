"""Invented records; hardware results must not modify canonical audits/claims."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import jsonschema
import numpy as np
import test_analysis as fixtures
from analysis.hardware_scenario import build_hardware_scenario, resource_fit
from service.main import app

SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'contracts/cpu-hardware.schema.json').read_text())


def rows():
    base = dict(state_name='COMPLETED', sm_util_avg=0, sm_util_max=0, gpu_hours=8, gpu_count=2,
                walltime_sec=7200, nodes_alloc=1, n_nodes_listed=1, cpus_req=2, mem_req_total_mb=9000, max_gpu_mem_used=0)
    return [{**base, 'id_job': 'invented-fit'}, {**base, 'id_job': 'invented-big', 'mem_req_total_mb': 200000},
            {**base, 'id_job': 'invented-multi', 'nodes_alloc': 2, 'n_nodes_listed': 2},
            {**base, 'id_job': 'invented-excluded', 'state_name': 'CANCELLED'}]


def built():
    return build_hardware_scenario(rows(), 2.5, 'invented-pricebook', 'synthetic-unit-v1', 'invented-browser', True)


class HardwareMath(unittest.TestCase):
    def test_resource_boundaries_and_unknowns(self):
        row=rows()[0]
        self.assertEqual(resource_fit(row)['memory_adjusted_cores'],3)
        for memory,status in [(192000,'fits'),(192001,'non_fit'),(None,'unresolved')]:
            self.assertEqual(resource_fit({**row,'mem_req_total_mb':memory})['status'],status)
        self.assertEqual(resource_fit({**row,'cpus_req':49})['status'],'non_fit')
        self.assertEqual(resource_fit({**row,'cpus_req':True})['status'],'unresolved')
        self.assertEqual(resource_fit({**row,'walltime_sec':0})['status'],'unresolved')

    def test_independent_prices_accounting_and_target(self):
        result,jobs=built()
        jsonschema.validate(result,{**SCHEMA,'$ref':'#/$defs/summary'})
        self.assertEqual(result['baseline_reference_usd'],80)  # Cancelled allocation stays in spending baseline.
        self.assertEqual(result['coverage']['eligible_jobs'],3)
        self.assertEqual(result['coverage']['fitting_jobs'],1)
        self.assertEqual(result['target_reference_usd'],16)
        a=result['allocations'][0]
        self.assertAlmostEqual(a['success_net_reference_usd']['low'],20-6*.05)
        self.assertAlmostEqual(a['success_net_reference_usd']['high'],20-6*.0125)
        self.assertAlmostEqual(a['failure_extra_reference_usd']['high'],6*.05)
        self.assertEqual(a['cases'][0]['cpu_core_hours'],6)
        self.assertEqual(a['cases'][0]['validation_completion_change_hours'],None)
        fitting=next(j for j in jobs if j['status']=='fits')
        self.assertAlmostEqual(fitting['cost_break_even_cpu_hours']['memory_adjusted']['high_cpu_price'],8/(3*.02))

    def test_preserves_losses_and_changes_identity_with_source(self):
        r=rows()[0];r.update(gpu_hours=2,walltime_sec=360000,cpus_req=48)
        first,_=build_hardware_scenario([r],2.5,'v','one','browser')
        second,_=build_hardware_scenario([r],2.5,'v','two','browser')
        self.assertLess(first['allocations'][0]['success_net_reference_usd']['high'],0)
        self.assertGreater(first['allocations'][0]['remaining_target_reference_usd']['low'],first['target_reference_usd'])
        self.assertNotEqual(first['scenario_id'],second['scenario_id'])
        with self.assertRaises(ValueError):build_hardware_scenario([r,r],2.5,'v','one','browser')

    def test_prepared_array_metadata_does_not_change_model(self):
        original=rows()
        with_metadata=[{**r,'unrelated_array':np.array(['invented-a','invented-b'])} for r in original]
        self.assertEqual(build_hardware_scenario(original,2.5,'v','one','browser'),
                         build_hardware_scenario(with_metadata,2.5,'v','one','browser'))


class HardwareRoutes(unittest.TestCase):
    def setUp(self):
        fixtures.Routes.setUp(self)
        self.summary,self.jobs=built()
        self.patcher=patch('service.hardware_routes.load_hardware',return_value=json.dumps({'result':self.summary,'jobs':self.jobs}))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop();fixtures.Routes.tearDown(self)

    def test_identity_pagination_and_immutable_claims(self):
        audit=fixtures.Routes.create(self)
        path='/api/audits/'+audit['audit_id']+'/claims?team=Synthetic'
        claims=self.client.get(path).json()
        summary=self.client.get('/api/cpu-hardware-scenario?dataset_version=invented-browser')
        self.assertEqual(summary.status_code,200)
        base='/api/cpu-hardware-scenario/jobs'
        args={'dataset_version':'invented-browser','scenario_id':self.summary['scenario_id'],'limit':1}
        p=self.client.get(base,params=args).json()
        jsonschema.validate(p,{**SCHEMA,'$ref':'#/$defs/page'})
        self.assertEqual(len(p['items']),1)
        self.assertNotEqual(p['items'][0]['job_id'],self.client.get(base,params={**args,'offset':1}).json()['items'][0]['job_id'])
        p['items'][0]['job_id']='mutated-client-copy'
        self.assertNotEqual(self.client.get(base,params=args).json()['items'][0]['job_id'],'mutated-client-copy')
        self.assertEqual(self.client.get(base,params={**args,'scenario_id':'stale'}).status_code,409)
        self.assertEqual(self.client.get(base,params={**args,'limit':101}).status_code,422)
        self.assertEqual(self.client.get('/api/cpu-hardware-scenario?dataset_version=stale').status_code,409)
        self.assertEqual(self.client.get(path).json(),claims)
        self.assertEqual(self.client.get('/api/audits/'+audit['audit_id']).json(),audit)

    def test_source_change_and_missing_data_are_explicit(self):
        with patch('service.analysis_routes.current_status',return_value='invalid'):
            self.assertEqual(self.client.get('/api/cpu-hardware-scenario?dataset_version=invented-browser').status_code,503)
        with patch('service.hardware_routes.load_hardware',side_effect=ValueError('source invalid')):
            self.assertEqual(self.client.get('/api/cpu-hardware-scenario?dataset_version=invented-browser').status_code,503)


if __name__=='__main__':unittest.main()
