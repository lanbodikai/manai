"""Original synthetic oracles matching A's v0.4 serialization, not source rows."""
import copy
import json
from pathlib import Path
import unittest
from urllib.parse import unquote

import httpx

from reviewer.clients import AnalysisClient, ReviewError
from reviewer.render import build_facts, render_answer
from reviewer.validation import validate_audit

ROOT = Path(__file__).resolve().parents[2]


def fixture(name):
    return json.loads((ROOT / 'contracts/examples' / name).read_text())


def sample(count=2, baseline_last=False):
    audit = fixture('audit-response.json')
    ids = [f'J{i + 1}' for i in range(count)]
    if baseline_last:
        ids.remove('J2')
        ids.append('J2')
    details = []
    for jid in ids:
        d = fixture('baseline-evidence.json')
        d['audit_id'] = audit['audit_id']
        d['evidence'] = {'id': 'job:' + jid, 'kind': 'job', 'source_id': jid,
                         'label': 'Invented ' + jid, 'synthetic': True}
        d['join_keys'] = {'id_job': jid}
        for o in d['observations']:
            if o['column'] == 'gpu_hours':
                o['unit'] = 'GPU-hours'
            elif o['column'] == 'gpu_count':
                o['unit'] = 'GPUs'
        details.append(d)
    audit['evidence_preview'] = [copy.deepcopy(d['evidence']) for d in details[:2]]
    audit['evidence_count'] = count
    audit['eligibility'].update(unique_jobs=count, eligible_gpu_hours=count * 20)
    audit['eligibility']['memory_partition'] = {
        'zero_memory': {'unique_jobs': count, 'recorded_gpu_hours': count * 20},
        'positive_memory': {'unique_jobs': 0, 'recorded_gpu_hours': 0},
        'unknown_memory': {'unique_jobs': 0, 'recorded_gpu_hours': 0}, 'basis': 'Invented zero-memory jobs'}
    for bound, fraction in audit['scenario']['recovery_fraction'].items():
        audit['recovery']['gpu_hours'][bound] = count * 20 * fraction
        audit['recovery']['reference_usd']['values'][bound] = count * 20 * fraction * 2.5
    return audit, details


def peer(audit, details, requests, *, page_size=None, missing=None, mutate=None):
    by_id = {d['evidence']['id']: d for d in details}
    def respond(request):
        requests.append(request)
        assert request.method == 'GET'
        path = request.url.path
        if path.endswith('/evidence'):
            offset = int(request.url.params.get('cursor', '0'))
            limit = int(request.url.params['limit'])
            stop = min(len(details), offset + min(limit, page_size or limit))
            body = {'audit_id': audit['audit_id'], 'total': audit['evidence_count'],
                    'items': [d['evidence'] for d in details[offset:stop]],
                    'next_cursor': str(stop) if stop < len(details) else None}
        elif '/evidence/' in path:
            eid = unquote(path.rsplit('/', 1)[-1])
            if eid == missing or eid not in by_id:
                return httpx.Response(404, json={'error': 'invented missing baseline'})
            body = copy.deepcopy(by_id[eid])
            if mutate:
                mutate(body)
        else:
            body = audit
        return httpx.Response(200, json=body)
    return httpx.MockTransport(respond)


def check_map(report):
    return {c['id']: c for c in report['checks']}


class V04IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def load(self, audit, details, **kwargs):
        self.requests = []
        transport = peer(audit, details, self.requests, **kwargs.pop('peer_options', {}))
        return await AnalysisClient('http://analysis', transport=transport, **kwargs).load(audit['audit_id'])

    async def test_selected_baseline_beyond_first_page_is_reviewed_within_budget(self):
        audit, details = sample(120, baseline_last=True)
        actual, fetched, coverage = await self.load(audit, details)
        self.assertTrue(self.requests[1].url.path.endswith('/evidence/job:J2'))
        self.assertEqual(len(fetched), 100)
        self.assertEqual(coverage['listed_count'], 99)
        self.assertEqual(coverage['targeted_evidence_ids'], ['job:J2'])
        self.assertFalse(coverage['complete'])
        report = validate_audit(actual, fetched, coverage)
        checks = check_map(report)
        self.assertEqual(checks['downside.net_reference_value_usd']['status'], 'pass')
        self.assertEqual(checks['cohort.recorded_gpu_hours']['status'], 'unknown')
        self.assertEqual(checks['evidence.coverage_counts']['status'], 'pass')
        self.assertFalse(any(c['status'] == 'fail' for c in report['checks']))

    async def test_target_deduplicated_when_later_listed(self):
        audit, details = sample(3, baseline_last=True)
        _, fetched, coverage = await self.load(audit, details, peer_options={'page_size': 1})
        target_requests = [r for r in self.requests if r.url.path.endswith('/evidence/job:J2')]
        self.assertEqual(len(target_requests), 1)
        self.assertEqual(len(fetched), 3)
        self.assertEqual(coverage['targeted_count'], 0)
        self.assertTrue(coverage['complete'])

    async def test_page_cap_does_not_hide_selected_baseline(self):
        audit, details = sample(12, baseline_last=True)
        _, fetched, coverage = await self.load(audit, details, peer_options={'page_size': 1})
        self.assertEqual(coverage['pages_fetched'], 4)
        self.assertEqual(len(fetched), 5)
        self.assertEqual(coverage['reasons'], ['max_pages'])
        self.assertFalse(coverage['complete'])

    async def test_one_record_budget_reserved_for_baseline_is_not_complete(self):
        audit, details = sample()
        _, fetched, coverage = await self.load(audit, details, max_evidence=1)
        self.assertEqual(fetched[0]['evidence']['id'], 'job:J2')
        self.assertEqual(coverage['listed_count'], 0)
        self.assertEqual(coverage['pages_fetched'], 0)
        self.assertFalse(coverage['complete'])

    async def test_missing_selected_baseline_is_normalized(self):
        audit, details = sample()
        with self.assertRaises(ReviewError) as caught:
            await self.load(audit, details, peer_options={'missing': 'job:J2'})
        self.assertEqual((caught.exception.status, caught.exception.code), (404, 'EVIDENCE_NOT_FOUND'))

    async def test_wrong_target_identity_kind_and_provenance_are_rejected(self):
        def identity(d): d['evidence']['id'] = 'job:wrong'
        def kind(d): d['evidence']['kind'] = 'finding'
        def lineage(d): d['provenance']['data_fingerprint'] = 'wrong'
        for mutate in (identity, kind, lineage):
            with self.subTest(mutation=mutate.__name__):
                audit, details = sample()
                with self.assertRaises(ReviewError) as caught:
                    await self.load(audit, details, peer_options={'mutate': mutate})
                self.assertEqual(caught.exception.status, 409)

    async def test_actual_unit_spellings_and_named_aggregate_do_not_false_fail(self):
        audit, details = sample()
        aggregate = copy.deepcopy(details[0])
        aggregate.update(source_columns=[], join_keys={}, source_table='synthetic derived summary',
                         observations=[{'name': 'eligible_gpu_hours', 'column': None, 'value': 40, 'unit': 'GPU-hours'},
                                       {'name': 'eligible_jobs', 'column': None, 'value': 2, 'unit': 'jobs'}])
        aggregate['evidence'].update(id='aggregate:accounting', kind='aggregate', source_id='accounting')
        details.insert(0, aggregate)
        audit['evidence_count'] = 3
        actual, fetched, coverage = await self.load(audit, details)
        report = validate_audit(actual, fetched, coverage)
        self.assertEqual([c for c in report['checks'] if c['status'] == 'fail'], [])
        self.assertEqual(check_map(report)['cohort.unique_jobs']['expected'], 2)
        self.assertEqual(check_map(report)['cohort.recorded_gpu_hours']['expected'], 40)
        self.assertNotIn('evidence.eligibility:aggregate:accounting', check_map(report))
        aggregate['observations'].append(copy.deepcopy(aggregate['observations'][0]))
        actual, fetched, coverage = await self.load(audit, details)
        self.assertEqual(check_map(validate_audit(actual, fetched, coverage))['evidence.units:aggregate:accounting']['status'], 'fail')

    async def test_bad_units_still_fail_and_missing_observations_stay_unknown(self):
        audit, details = sample()
        target = details[1]
        next(o for o in target['observations'] if o['column'] == 'gpu_hours')['unit'] = 'CPU-hours'
        actual, fetched, coverage = await self.load(audit, details)
        self.assertEqual(check_map(validate_audit(actual, fetched, coverage))['evidence.units:job:J2']['status'], 'fail')
        next(o for o in target['observations'] if o['column'] == 'gpu_hours')['unit'] = 'GPU-hours'
        target['observations'] = [o for o in target['observations'] if o['column'] != 'sm_util_max']
        actual, fetched, coverage = await self.load(audit, details)
        self.assertEqual(check_map(validate_audit(actual, fetched, coverage))['evidence.eligibility:job:J2']['status'], 'unknown')

    async def test_grouped_answer_retains_failure_and_unknown_categories(self):
        audit, details = sample(120, baseline_last=True)
        actual, fetched, coverage = await self.load(audit, details)
        for d in fetched:
            next(o for o in d['observations'] if o['column'] == 'gpu_hours')['unit'] = 'wrong'
        report = validate_audit(actual, fetched, coverage)
        answer = render_answer(actual, report, build_facts(actual, report))
        self.assertIn('100 checks; representative details below', answer)
        for check in report['checks']:
            if check['status'] != 'pass':
                self.assertIn(check['id'].split(':', 1)[0] + ': ' + check['status'].upper(), answer)
        self.assertNotIn('"accounting_note"', answer)
        self.assertIn('Net reference benefit or loss', answer)
        self.assertIn('Partial review', answer)
        self.assertLess(len(answer), 12000)
        self.assertIn('pause for owner action', answer)

    def test_limits_cannot_be_expanded_by_client(self):
        for kwargs in ({'max_pages': 5}, {'max_evidence': 101}):
            with self.assertRaises(ValueError):
                AnalysisClient('http://analysis', **kwargs)


if __name__ == '__main__':
    unittest.main()
