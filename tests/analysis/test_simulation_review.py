"""Review must detect broken arithmetic and preserve unmeasured assumptions."""
import copy
import unittest
from test_portfolio import built
from service.simulation_review import build_review

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
