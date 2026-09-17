"""Original synthetic fixtures. No organizer-derived records."""
import copy
import json
import unittest
from unittest.mock import patch

import jsonschema
from fastapi.testclient import TestClient

from analysis.core import *
from service.audits import AuditStore, freeze_evidence, list_evidence, resolve_evidence
from service.analysis_routes import validate, CLAIMS
from service.main import app


def fixture():
    jobs = [dict(id_job="J1", state_name="COMPLETED", sm_util_avg=0, sm_util_max=0, gpu_hours=10, walltime_sec=3600),
            dict(id_job="J2", state_name="COMPLETED", sm_util_avg=0, sm_util_max=0, gpu_hours=20, walltime_sec=7200),
            dict(id_job="J3", state_name="CANCELLED", sm_util_avg=0, sm_util_max=0, gpu_hours=40)]
    findings = [dict(id=f"F{i}", detectorId=RULE, metadata=dict(job_id=job, impact_scope=scope, impact_kind=kind, impact_gpu_hours=10))
                for i, (job, scope, kind) in enumerate([
                    ("J1", "job", "unused_capacity"), ("J1", "job", "unused_capacity"),
                    ("J2", "job", "unused_capacity"), ("J1", "user", "unused_capacity"), ("J2", "job", "queue_wait")])]
    cohort = select_cohort(jobs)
    impacts = audit_impacts(cohort, findings)
    provenance = dict(data_fingerprint="synthetic-unit-v1", source_version="original-fixture-v1", synthetic=True,
                      sample_label="Original synthetic jobs", window_label="Invented window", caveats=["Synthetic only"])
    evidence = make_evidence(cohort, impacts, findings, {"summary": "Invented rule context"}, provenance)
    context = freeze_evidence(dict(cohort=cohort, impacts=impacts, evidence=evidence, provenance=provenance,
                                  findings=findings, upstream={"recommendations": []}))
    request = dict(client_request_id="test-request", expected_data_fingerprint=provenance["data_fingerprint"],
                   recommendation_id="cpu-placement-pilot", scenario=dict(recovery_fraction=dict(low=.2, point=.4, high=.6),
                   usd_per_gpu_hour=2.5, cancelled_policy="exclude", interval_kind="scenario", assumption_note="Synthetic assumed fractions"))
    return jobs, context, request


class Arithmetic(unittest.TestCase):
    def setUp(self):
        self.jobs, self.context, self.request = fixture()

    def test_T01_T02_T03_overlap_and_scope(self):
        c, i = self.context["cohort"], self.context["impacts"]
        self.assertEqual(c.hours, 30)
        self.assertEqual(len(c.jobs), 2)
        self.assertEqual(i["naive_linked_allocation_gpu_hours"], 40)
        self.assertEqual(i["deduplicated_linked_allocation_gpu_hours"], 30)
        self.assertEqual(i["overlapping_finding_references"], 1)
        self.assertEqual(i["excluded_impacts"], {"non-job scope": 1, "different impact kind": 1})

    def test_T04_invalid_missing_duplicates(self):
        for updates in ({"sm_util_avg": 1}, {"sm_util_max": None}, {"walltime_sec": -1}, {"gpu_hours": float("nan")}, {"sm_util_avg": True}):
            with self.subTest(updates=updates):
                self.assertEqual(len(select_cohort([{**self.jobs[0], **updates}]).jobs), 0)
        self.assertEqual(select_cohort([self.jobs[0], self.jobs[0]]).hours, 10)
        with self.assertRaises(ValueError):
            select_cohort([self.jobs[0], {**self.jobs[0], "gpu_hours": 20}])

    def test_T05_T06_scenario_math_and_rejection(self):
        r = estimate_recovery(self.context["cohort"], self.request["scenario"])
        self.assertEqual(r["gpu_hours"], dict(low=6, point=12, high=18))
        self.assertEqual(r["reference_usd"]["values"], dict(low=15, point=30, high=45))
        for values in [(-1, .4, .6), (.5, .4, .6), (.2, .7, .6), (0, .5, 2), (0, float("nan"), 1)]:
            s = {**self.request["scenario"], "recovery_fraction": dict(zip(("low", "point", "high"), values))}
            with self.assertRaises(ValueError): estimate_recovery(self.context["cohort"], s)
        for price in (0, -1, True, float("inf"), 1e308):
            with self.assertRaises(ValueError): estimate_recovery(self.context["cohort"], {**self.request["scenario"], "usd_per_gpu_hour": price})

    def test_T07_T08_T09_immutable_claims_and_evidence(self):
        store = AuditStore(2)
        a, b = [store.create(self.request, self.context) for _ in range(2)]
        self.assertEqual(a.audit["recovery"], b.audit["recovery"])
        self.assertEqual(a.refs, b.refs)
        claims = export_claims(a.audit, "Synthetic team")
        validate("Claims", claims)
        jsonschema.validate(claims, CLAIMS)
        self.assertEqual(claims["recoverable_gpu_hours"]["point"], a.audit["recovery"]["gpu_hours"]["point"])
        self.request["scenario"]["recovery_fraction"]["point"] = .5
        self.assertEqual(a.audit["scenario"]["recovery_fraction"]["point"], .4)
        eid = next(iter(a.evidence))
        self.assertTrue(resolve_evidence(a, a.audit["audit_id"], eid)["evidence"]["synthetic"])
        with self.assertRaises(KeyError): resolve_evidence(a, a.audit["audit_id"], "outside")
        store.create(self.request, self.context)
        self.assertIsNone(store.get(a.audit["audit_id"]))


class Routes(unittest.TestCase):
    def setUp(self):
        _, self.context, self.request = fixture()
        self.patches = [patch("service.main.inspect_data", return_value={"status": "missing", "fingerprint": None, "signature": None}),
                        patch("service.main.current_status", return_value="ready"),
                        patch("service.analysis_routes.current_status", return_value="ready")]
        for p in self.patches: p.start()
        self.client = TestClient(app).__enter__()
        app.state.source = {"status": "ready", "fingerprint": "synthetic-unit-v1", "signature": None}
        app.state.analysis_context = self.context

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for p in reversed(self.patches): p.stop()

    def create(self):
        response = self.client.post("/api/audits", json=self.request)
        self.assertEqual(response.status_code, 201, response.text)
        validate("Audit", response.json())
        return response.json()

    def test_C01_C06_full_routes(self):
        a = self.create()
        base = "/api/audits/" + a["audit_id"]
        self.assertEqual(self.client.get(base).json(), a)
        validate("Recommendations", self.client.get("/api/recommendations").json())
        response = self.client.get(base + "/claims?team=Synthetic")
        self.assertIn("attachment", response.headers["content-disposition"])
        validate("Claims", response.json())
        jsonschema.validate(response.json(), CLAIMS)
        self.assertEqual(response.json()["recoverable_gpu_hours"]["point"], 12)
        self.assertIsNone(a["downside"]["money"])

    def test_C02_stale_and_membership(self):
        a = self.create()
        self.request["expected_data_fingerprint"] = "different"
        self.assertEqual(self.client.post("/api/audits", json=self.request).status_code, 409)
        base = "/api/audits/" + a["audit_id"]
        self.assertEqual(self.client.get(base).json(), a)
        self.assertEqual(self.client.get(base + "/evidence/outside").status_code, 404)
        with patch("service.analysis_routes.current_status", return_value="invalid"):
            for path in (base, base + "/evidence", base + "/claims?team=X"):
                self.assertEqual(self.client.get(path).status_code, 409)
        self.assertEqual(self.client.get(base).json(), a)

    def test_C03_pagination_and_cross_audit_cursor(self):
        a, b = self.create(), self.create()
        base = "/api/audits/" + a["audit_id"]
        cursor, ids = None, []
        while True:
            page = self.client.get(base + "/evidence", params={"limit": 2, **({"cursor": cursor} if cursor else {})}).json()
            validate("EvidencePage", page)
            for ref in page["items"]:
                ids.append(ref["id"])
                validate("EvidenceDetail", self.client.get(base + "/evidence/" + ref["id"]).json())
            cursor = page["next_cursor"]
            if not cursor: break
            self.assertEqual(self.client.get("/api/audits/" + b["audit_id"] + "/evidence", params={"cursor": cursor}).status_code, 422)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), a["evidence_count"])
        for params in ({"limit": 101}, {"limit": 0}, {"cursor": "bad"}):
            r = self.client.get(base + "/evidence", params=params)
            self.assertEqual(r.status_code, 422)
            validate("Error", r.json())

    def test_C05_invalid_input_and_missing_audit(self):
        for body in ({}, {**self.request, "extra": True}, {**self.request, "scenario": {}}):
            response = self.client.post("/api/audits", json=body)
            self.assertEqual(response.status_code, 422)
            validate("Error", response.json())
        response = self.client.post("/api/audits", content='{"scenario":NaN}', headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/api/audits/missing").status_code, 404)


if __name__ == "__main__": unittest.main()
