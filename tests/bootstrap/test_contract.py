import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import jsonschema
from fastapi.testclient import TestClient
from service.main import app, map_overview, SPEC
from service.source import inspect_data, current_status

ROOT=Path(__file__).resolve().parents[2]
def validate(name, value):
    jsonschema.Draft202012Validator({**SPEC,"$ref":"#/components/schemas/"+name}).validate(value)

class Contracts(unittest.TestCase):
    def test_original_examples(self):
        folder=ROOT/'contracts/examples'
        for filename,name in json.loads((folder/'manifest.json').read_text()).items():
            with self.subTest(filename=filename): validate(name,json.loads((folder/filename).read_text()))

    def test_overview_mapping_and_labels(self):
        summary={"kind":"fact","value":30,"window":{"start":"synthetic-start","end":"synthetic-end"},"provenance":{"caveat":"sample only"}}
        waste={"kind":"fact","rows":[{"state":"COMPLETED","gpu_hours":30}],"provenance":{"caveat":"not cash"}}
        prices={"usd_per_gpu_hour":2.5,"version":"synthetic-test"}
        result=map_overview(summary,waste,prices,2,"synthetic-fingerprint")
        validate('Overview',result)
        self.assertEqual(result['outcomes'][0]['reference_usd'],75)
        self.assertEqual(result['allocated_gpu_hours'],30)
        self.assertIn('not verified cash savings',' '.join(result['warnings']))
        summary['kind']='judgment'
        with self.assertRaises(ValueError): map_overview(summary,waste,prices,2,'test')

    def test_missing_source_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            source=inspect_data(Path(folder))
            self.assertEqual(source['status'],'missing')
            self.assertIsNone(source['fingerprint'])
            self.assertEqual(current_status(Path(folder),source),'missing')

    def test_canonical_mismatch_and_changed_source(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from scripts.checksum_data import FILES, digest
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            for name in FILES:
                path=data/name
                path.parent.mkdir(parents=True,exist_ok=True)
                if path.suffix=='.json': path.write_text('[]')
                else: pq.write_table(pa.table({'original_synthetic_column':[1]}),path)
            (data/'checksums.txt').write_text(''.join(digest(data/name)+'  '+name+'\n' for name in FILES))
            source=inspect_data(data)
            self.assertEqual(source['status'],'ready')
            self.assertEqual(current_status(data,source),'ready')
            (data/'synthetic/findings.json').write_text('[{}]')
            self.assertEqual(current_status(data,source),'invalid')
            self.assertEqual(inspect_data(data)['status'],'invalid')

    def test_structured_errors_and_no_provider(self):
        state={"status":"missing","fingerprint":None,"signature":None}
        with patch('service.main.inspect_data',return_value=state),patch('service.main.current_status',return_value='missing'):
            with TestClient(app) as client:
                health=client.get('/api/health')
                validate('Health',health.json())
                self.assertEqual(health.json()['agent_status'],'unconfigured')
                for method,path,status,code in [
                    ('get','/api/overview',503,'DATA_NOT_READY'),
                    ('get','/api/audits/missing',404,'AUDIT_NOT_FOUND'),
                    ('post','/api/audits/missing/explanations',503,'AGENT_UNAVAILABLE'),
                    ('post','/api/audits',503,'BOOTSTRAP_NOT_IMPLEMENTED')]:
                    with self.subTest(path=path):
                        response=getattr(client,method)(path)
                        self.assertEqual(response.status_code,status)
                        validate('Error',response.json())
                        self.assertEqual(response.json()['error']['code'],code)

if __name__=='__main__': unittest.main()
