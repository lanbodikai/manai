"""v0.4 scenarios use only agreed original synthetic fixtures."""
import copy
import json
import math
from pathlib import Path
import unittest

import test_analysis as fixtures
from analysis.cpu_pilot import assess_cpu_pilot, memory_partition
from analysis.core import make_evidence, select_cohort, audit_impacts, evidence_id
from service.audits import freeze_evidence
from service.analysis_routes import validate
from service.main import app

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "contracts/examples/pilot-cases.json").read_text())


class Calculator(unittest.TestCase):
    def test_T05_all_eight_agreed_cases(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                baseline = case["result"]["baseline"]
                job = dict(gpu_count=baseline["gpu_count"], walltime_sec=baseline["elapsed_hours"] * 3600,
                           gpu_hours=baseline["recorded_gpu_hours"])
                result = assess_cpu_pilot(job, case["input"], case["gpu_hour_usd"])
                validate("CpuPilotResult", result)
                for key, value in case["result"].items():
                    if key in {"baseline", "limitations"}: continue
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        self.assertAlmostEqual(result[key], value)
                    else: self.assertEqual(result[key], value)

    def test_T05_recorded_allocation_not_scheduler_product(self):
        pilot = CASES[0]["input"]
        result = assess_cpu_pilot(dict(gpu_count=2, walltime_sec=36000, gpu_hours=25), pilot, 2.5)
        self.assertEqual(result["released_gpu_hours"], 25)
        self.assertEqual(result["baseline"]["elapsed_hours"], 10)
        self.assertIn("differs", result["baseline"]["accounting_note"])

    def test_T06_invalid_finite_baseline_and_cap(self):
        job = dict(gpu_count=2, walltime_sec=36000, gpu_hours=20)
        pilot = CASES[0]["input"]
        for change in ({"cpu_hours": 0}, {"cpu_hours": float("nan")}, {"cpu_hours": float("inf")},
                       {"cpu_hours": 1e308, "cpu_vcpus": 8}, {"trial_cap_hours": 1},
                       {"cpu_vcpus": True}, {"cpu_vcpus": 1.5}, {"extra_queue_hours": -1},
                       {"cpu_vcpu_hour_usd": -1}, {"baseline_host_costs_included": None}):
            with self.subTest(change=change), self.assertRaises((ValueError, OverflowError)):
                assess_cpu_pilot(job, {**pilot, **change}, 2.5)
        for change in ({"gpu_count": None}, {"walltime_sec": 0}, {"gpu_hours": -1}, {"gpu_count": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                assess_cpu_pilot({**job, **change}, pilot, 2.5)

    def test_T05_memory_unknown_is_not_zero(self):
        jobs, _, _ = fixtures.fixture()
        jobs[0]["max_gpu_mem_used"] = 0
        jobs[1]["max_gpu_mem_used"] = None
        cohort = select_cohort(jobs)
        partition = memory_partition(cohort)
        self.assertEqual(partition["zero_memory"], {"unique_jobs": 1, "recorded_gpu_hours": 10})
        self.assertEqual(partition["unknown_memory"], {"unique_jobs": 1, "recorded_gpu_hours": 20})
        self.assertEqual(sum(partition[k]["recorded_gpu_hours"] for k in ("zero_memory", "positive_memory", "unknown_memory")), cohort.hours)


class PilotRoutes(unittest.TestCase):
    def setUp(self):
        fixtures.Routes.setUp(self)
        jobs, _, _ = fixtures.fixture()
        jobs[0].update(gpu_count=1, walltime_sec=36000, max_gpu_mem_used=8)
        jobs[1].update(gpu_count=2, walltime_sec=36000, max_gpu_mem_used=0)
        self.context["cohort"] = select_cohort(jobs)
        self.context["impacts"] = audit_impacts(self.context["cohort"], self.context["findings"])
        self.context["evidence"] = make_evidence(self.context["cohort"], self.context["impacts"], self.context["findings"],
                                                {"summary": "Invented rule context"}, self.context["provenance"])
        freeze_evidence(self.context)
        app.state.analysis_context = self.context
        self.pilot = {**CASES[0]["input"], "baseline_evidence_id": evidence_id("synthetic-unit-v1", "job", "J2")}

    def tearDown(self): fixtures.Routes.tearDown(self)

    def create(self): return fixtures.Routes.create(self)

    def test_T07_C06_optional_pilot_preserves_recovery_claims_identity(self):
        a = self.create()
        self.assertEqual(a["contract_version"], "0.4")
        self.assertIsNone(a["downside"]["cpu_pilot"])
        self.request["scenario"]["cpu_pilot"] = self.pilot
        b = self.create()
        self.assertNotEqual(a["audit_id"], b["audit_id"])
        self.assertEqual(a["recovery"], b["recovery"])
        self.assertEqual(b["downside"]["cpu_pilot"]["baseline"]["recorded_gpu_hours"], 20)
        self.assertEqual(b["downside"]["cpu_pilot"]["net_reference_value_usd"], 45.2)
        self.assertIsNone(b["downside"]["money"])
        ca, cb = [self.client.get(f"/api/audits/{x['audit_id']}/claims?team=X").json() for x in (a, b)]
        for key in ("recoverable_gpu_hours", "recoverable_usd"):
            self.assertEqual(ca[key], cb[key])
        self.pilot["mode"] = "replacement_failure"
        c = self.create()
        self.assertLess(c["downside"]["cpu_pilot"]["net_reference_value_usd"], 0)
        self.assertEqual(c["downside"]["cpu_pilot"]["released_gpu_hours"], 0)
        self.assertEqual(self.client.get("/api/audits/" + b["audit_id"]).json(), b)

    def test_C02_T06_baseline_membership_version_and_validation(self):
        original = self.create()
        self.request["scenario"]["cpu_pilot"] = {**self.pilot, "baseline_evidence_id": "outside"}
        self.assertEqual(self.client.post("/api/audits", json=self.request).status_code, 404)
        self.request["scenario"]["cpu_pilot"] = {**self.pilot, "trial_cap_hours": 1}
        self.assertEqual(self.client.post("/api/audits", json=self.request).status_code, 422)
        self.request["scenario"]["cpu_pilot"] = {**self.pilot, "cpu_hours": 0}
        self.assertEqual(self.client.post("/api/audits", json=self.request).status_code, 422)
        self.request["scenario"]["cpu_pilot"] = self.pilot
        eid = self.pilot["baseline_evidence_id"]
        self.context["evidence"][eid]["provenance"]["data_fingerprint"] = "foreign"
        self.assertEqual(self.client.post("/api/audits", json=self.request).status_code, 409)
        self.assertEqual(self.client.get("/api/audits/" + original["audit_id"]).json(), original)


if __name__ == "__main__": unittest.main()
