"""Review must detect broken arithmetic and preserve unmeasured assumptions."""
import copy
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
import unittest
from test_portfolio import built, rows, config
from analysis.portfolio import calculate
from service.simulation_review import build_review, review, validate_selection

class ModelSelectionTests(unittest.TestCase):
    def test_long_grounded_selection_is_bounded_after_validation(self):
        ids = [f'fact-{i}' for i in range(30)]
        self.assertEqual(validate_selection(ids, set(ids)), ids[:16])
        self.assertEqual(validate_selection(ids[:2], set(ids)), ids[:2])

    def test_bad_ids_beyond_display_limit_are_still_rejected(self):
        ids = [f'fact-{i}' for i in range(30)]
        for invalid in ([], ids + ['invented'], ids + [ids[0]], ids + [None]):
            with self.assertRaises(ValueError):
                validate_selection(invalid, set(ids))

class SimulationReviewTests(unittest.TestCase):
    def test_reports_uncertainty_and_detects_changed_total(self):
        summary, rows = built()
        context = {'price_book': {'version': summary['price_book_version'], 'usd_per_gpu_hour': summary['gpu_reference_usd_per_hour']}}
        facts, report = build_review(summary, {'total':len(rows),'items':rows}, 'all', context)
        self.assertTrue(facts)
        self.assertFalse([c for c in report['checks'] if c['status']=='fail'])
        self.assertTrue([c for c in report['checks'] if c['status']=='unknown'])
        changed = copy.deepcopy(summary)
        changed['cases'][0]['net_reference_usd'] += 123
        _, bad = build_review(changed, {'total':len(rows)+1,'items':rows}, 'all', context)
        self.assertEqual(next(c for c in bad['checks'] if c['id']=='total.lower')['status'],'fail')
        self.assertEqual(next(c for c in bad['checks'] if c['id']=='coverage')['status'],'unknown')

    def test_fixed_costs_scoped_totals_and_corrupt_evidence(self):
        request = config()
        request['overheads']['cpu-placement']['setup_usd'] = 123
        summary, evidence = built(request)
        context = {'price_book': {'version': summary['price_book_version'], 'usd_per_gpu_hour': summary['gpu_reference_usd_per_hour']}}
        for action in ['all', 'cpu-placement']:
            scoped = [r for r in evidence if action == 'all' or r['assigned_action'] == action]
            _, report = build_review(summary, {'total': len(scoped), 'items': scoped}, action, context)
            self.assertFalse([c for c in report['checks'] if c['status'] == 'fail'])
        changed = copy.deepcopy(evidence)
        # Preserve per-job arithmetic while breaking reconciliation with the summary.
        changed_cpu = next(r for r in changed if r['assigned_action'] == 'cpu-placement')
        changed_cpu['cases']['lower']['gross_reference_usd'] += 7
        changed_cpu['cases']['lower']['net_reference_usd'] += 7
        _, report = build_review(summary, {'total': len(changed), 'items': changed}, 'all', context)
        self.assertEqual(next(c for c in report['checks'] if c['id'] == 'cpu-placement.evidence_totals')['status'], 'fail')
        duplicate = evidence + [evidence[0]]
        _, report = build_review(summary, {'total': len(duplicate), 'items': duplicate}, 'all', context)
        self.assertEqual(next(c for c in report['checks'] if c['id'] == 'unique_jobs')['status'], 'fail')


class FullSnapshotRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_route_checks_records_beyond_display_limit(self):
        invented = [{**rows()[0], 'id_job': f'invented-{i:03}'} for i in range(105)]
        summary, evidence = calculate(invented, None, config(), 'invented-fingerprint', 2.5, 'invented-pricebook', True)
        body = {'client_request_id': 'test', 'question': 'Trace evidence', 'dataset_version': 'a'*64, 'action': 'all'}
        async def stream():
            yield json.dumps(body).encode()
        request = SimpleNamespace(stream=stream, app=SimpleNamespace(state=SimpleNamespace(chat_slots=asyncio.Semaphore(1))))
        @asynccontextmanager
        async def official():
            yield SimpleNamespace(call_tool=AsyncMock(return_value={'version': 'invented-pricebook', 'usd_per_gpu_hour': 2.5}))
        saved = {'result': summary, 'evidence': evidence}
        with patch('service.simulation_review.get_snapshot', return_value=saved), patch('service.simulation_review.require_data'), patch('service.simulation_review.connect_official', official), patch('service.simulation_review.tool_body', side_effect=lambda x: x), patch.dict('os.environ', {'FEATHERLESS_API_KEY': ''}):
            result = await review('b'*64, request)
            self.assertEqual(result['coverage'], {'retrieved': 105, 'total': 105, 'complete': True})
            self.assertEqual(len(result['source_examples']), 3)
            self.assertFalse([c for c in result['checks'] if c['status'] == 'fail'])
            self.assertEqual(result['status'], 'insufficient_evidence')
            evidence[104]['cases']['lower']['net_reference_usd'] += 1
            result = await review('b'*64, request)
            self.assertEqual(next(c for c in result['checks'] if c['id'] == 'sample_arithmetic')['status'], 'fail')
            self.assertEqual(next(c for c in result['checks'] if c['id'] == 'cpu-placement.evidence_totals')['status'], 'fail')
