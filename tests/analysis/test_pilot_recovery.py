"""Original synthetic examples and hand-worked oracles; no organizer source rows."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import jsonschema

from analysis.core import audit_impacts, evidence_id, make_evidence, select_cohort
from analysis.pilot_recovery import baseline_from_evidence, simulate_pilot
from service.audits import freeze_evidence
from service.main import app
from service.pilot_recovery_routes import SPEC, validate


ROOT = Path(__file__).resolve().parents[2]


def baseline():
    return dict(evidence_id="invented-baseline", source_job_id="INVENTED-JOB", synthetic=True,
                state_name="COMPLETED", sm_util_avg=0, sm_util_max=0, max_gpu_mem_used=0,
                gpu_count=2, elapsed_hours=10, recorded_gpu_hours=20, usd_per_gpu_hour=2.5,
                original_reference_cost_usd=50, missing_fields=[])


def inputs(**changes):
    request = dict(client_request_id="invented-request", baseline_evidence_id="invented-baseline",
                   proposal="Test an isolated CPU replacement using original invented fixtures.",
                   correctness_check="Assume the fixture output matches its known reference exactly.",
                   cpu_vcpus=4, cpu_hours=12, cpu_vcpu_hour_usd=.1, max_runtime_hours=15,
                   max_trial_spend_usd=20, setup_cost_usd=2, extra_queue_hours=2,
                   baseline_host_costs_included=True, outcome="success", failure_reason="",
                   recovery_note="Assume the full original configuration is available; no checkpoint is reused.")
    request.update(changes)
    return request


def envelope(result):
    return dict(feature_version="0.1", simulation_id="invented-simulation", audit_id="invented-audit",
                audit_client_request_id="invented-audit-request", client_request_id=result["inputs"]["client_request_id"],
                data_fingerprint="invented-data-v1", source_version="invented-fixture-v1", synthetic=True, **result)


class Arithmetic(unittest.TestCase):
    def calculate(self, base=None, **changes):
        result = simulate_pilot(base or baseline(), inputs(**changes))
        validate("PilotSimulation", envelope(result))
        return result

    def test_success_original_minus_cpu_and_setup(self):
        result = self.calculate()
        self.assertEqual(result["status"], "success")
        self.assertAlmostEqual(result["costs"]["cpu_trial_cost_usd"], 4.8)
        self.assertAlmostEqual(result["costs"]["total_cost_to_complete_usd"], 6.8)
        self.assertAlmostEqual(result["costs"]["net_benefit_usd"], 43.2)
        self.assertEqual(result["capacity"]["released_gpu_hours"], 20)
        self.assertEqual(result["timing"]["completion_change_hours"], 4)
        self.assertTrue(result["canonical_calculator_reused"])

    def test_failed_trial_full_rerun_counted_once(self):
        result = self.calculate(outcome="failure_recovered", cpu_hours=3, failure_reason="Assumed incorrect output")
        self.assertEqual(result["status"], "recovered")
        self.assertAlmostEqual(result["costs"]["trial_cost_usd"], 3.2)
        self.assertEqual(result["costs"]["recovery_cost_usd"], 50)
        self.assertAlmostEqual(result["costs"]["total_cost_to_complete_usd"], 53.2)
        self.assertAlmostEqual(result["costs"]["net_benefit_usd"], -3.2)
        self.assertEqual(result["timing"]["completion_change_hours"], 5)
        self.assertEqual(result["timing"]["total_elapsed_hours_including_queue"], 15)
        self.assertEqual(result["capacity"]["released_gpu_hours"], 0)
        self.assertEqual(result["recovery"]["strategy"], "full_original_gpu_rerun")
        self.assertFalse(result["recovery"]["checkpoint_verified"])

    def test_unavailable_recovery_never_claims_unfinished_work_as_savings(self):
        result = self.calculate(outcome="failure_unavailable", cpu_hours=3, failure_reason="Assumed GPU recovery unavailable")
        self.assertEqual(result["status"], "paused")
        self.assertAlmostEqual(result["costs"]["cost_so_far_usd"], 3.2)
        for name in ("net_benefit_usd", "total_cost_to_complete_usd", "recovery_cost_usd"):
            self.assertIsNone(result["costs"][name])
        self.assertIsNone(result["capacity"]["released_gpu_hours"])
        self.assertIsNone(result["timing"]["completion_change_hours"])
        self.assertIsNone(result["timing"]["total_elapsed_hours_including_queue"])
        self.assertFalse(result["canonical_calculator_reused"])

    def test_recorded_allocation_not_gpu_count_times_runtime(self):
        base = {**baseline(), "recorded_gpu_hours": 25, "original_reference_cost_usd": 62.5}
        result = self.calculate(base)
        self.assertEqual(result["capacity"]["released_gpu_hours"], 25)
        self.assertAlmostEqual(result["costs"]["net_benefit_usd"], 55.7)

    def test_runtime_cap_changes_success_to_assumed_full_recovery(self):
        result = self.calculate(max_runtime_hours=5)
        self.assertEqual(result["stop_reason"], "runtime_limit")
        self.assertEqual(result["effective_outcome"], "failure_recovered")
        self.assertEqual(result["timing"]["effective_cpu_hours"], 5)
        self.assertEqual(result["costs"]["total_cost_to_complete_usd"], 54)
        self.assertEqual(result["costs"]["net_benefit_usd"], -4)
        self.assertEqual(result["timing"]["completion_change_hours"], 7)
        self.assertTrue(result["failure_details"]["selected_outcome_changed"])

    def test_spend_cap_includes_setup_and_excludes_full_rerun(self):
        result = self.calculate(max_trial_spend_usd=3)
        self.assertEqual(result["stop_reason"], "spend_limit")
        self.assertEqual(result["timing"]["effective_cpu_hours"], 2.5)
        self.assertEqual(result["costs"]["trial_cost_usd"], 3)
        self.assertEqual(result["costs"]["total_cost_to_complete_usd"], 53)
        self.assertEqual(result["costs"]["net_benefit_usd"], -3)
        self.assertTrue(result["limits"]["spend_limit_excludes_recovery"])

    def test_earliest_cap_and_tied_caps(self):
        cases = [({"max_runtime_hours": 5, "max_trial_spend_usd": 3}, "spend_limit", 2.5),
                 ({"max_runtime_hours": 2, "max_trial_spend_usd": 3}, "runtime_limit", 2),
                 ({"max_runtime_hours": 5, "max_trial_spend_usd": 4}, "runtime_and_spend_limit", 5)]
        for assumptions, reason, duration in cases:
            with self.subTest(assumptions=assumptions):
                result = self.calculate(**assumptions)
                self.assertEqual(result["stop_reason"], reason)
                self.assertEqual(result["timing"]["effective_cpu_hours"], duration)

    def test_setup_over_budget_blocks_before_starting_or_spending(self):
        result = self.calculate(setup_cost_usd=21)
        self.assertEqual(result["stop_reason"], "setup_exceeds_spend_limit")
        self.assertEqual(result["limits"]["spend_limit_status"], "blocked_before_start")
        self.assertFalse(result["limits"]["trial_started"])
        self.assertEqual(result["timing"]["effective_cpu_hours"], 0)
        self.assertEqual(result["costs"]["trial_cost_usd"], 0)
        self.assertEqual(result["costs"]["setup_cost_usd"], 0)
        self.assertEqual(result["costs"]["total_cost_to_complete_usd"], 50)
        self.assertEqual(result["costs"]["net_benefit_usd"], 0)

    def test_free_cpu_with_setup_equal_to_cap_and_zero_budget(self):
        for setup in (0, 2):
            with self.subTest(setup=setup):
                result = self.calculate(cpu_vcpu_hour_usd=0, setup_cost_usd=setup, max_trial_spend_usd=setup)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["costs"]["trial_cost_usd"], setup)
                self.assertEqual(result["timing"]["effective_cpu_hours"], 12)

    def test_unknown_price_or_setup_never_verifies_spend_or_net(self):
        for changes in ({"cpu_vcpu_hour_usd": None}, {"setup_cost_usd": None}):
            with self.subTest(changes=changes):
                result = self.calculate(**changes)
                self.assertEqual(result["limits"]["spend_limit_status"], "unverified")
                self.assertIsNone(result["costs"]["trial_cost_usd"])
                self.assertIsNone(result["costs"]["net_benefit_usd"])
                self.assertEqual(result["timing"]["completion_change_hours"], 4)

    def test_unknown_queue_and_incomplete_pricing_boundary(self):
        no_queue = self.calculate(extra_queue_hours=None)
        self.assertIsNone(no_queue["timing"]["completion_change_hours"])
        self.assertEqual(no_queue["timing"]["run_time_change_hours_excluding_queue"], 2)
        no_boundary = self.calculate(baseline_host_costs_included=False)
        self.assertIsNone(no_boundary["costs"]["net_benefit_usd"])
        self.assertAlmostEqual(no_boundary["costs"]["total_cost_to_complete_usd"], 6.8)

    def test_unknown_setup_still_bounds_known_cpu_spending(self):
        result = self.calculate(cpu_vcpus=1, cpu_vcpu_hour_usd=1, cpu_hours=2,
                                max_runtime_hours=2, max_trial_spend_usd=1, setup_cost_usd=None)
        self.assertEqual(result["timing"]["effective_cpu_hours"], 1)
        self.assertEqual(result["costs"]["cpu_trial_cost_usd"], 1)
        self.assertEqual(result["stop_reason"], "spend_limit")
        self.assertEqual(result["effective_outcome"], "failure_recovered")
        self.assertEqual(result["limits"]["spend_limit_status"], "unverified")
        self.assertIsNone(result["costs"]["trial_cost_usd"])
        self.assertIsNone(result["costs"]["net_benefit_usd"])

    def test_negative_net_and_earlier_completion_are_preserved(self):
        expensive = self.calculate(cpu_vcpu_hour_usd=10, max_trial_spend_usd=1000)
        self.assertEqual(expensive["costs"]["net_benefit_usd"], -432)
        earlier = self.calculate(cpu_hours=4, extra_queue_hours=0)
        self.assertEqual(earlier["timing"]["completion_change_hours"], -6)

    def test_failure_reason_survives_a_cap(self):
        result = self.calculate(outcome="failure_unavailable", failure_reason="Owner-defined output mismatch", max_runtime_hours=1)
        self.assertEqual(result["failure_details"]["requested_failure_reason"], "Owner-defined output mismatch")
        self.assertIn("Owner-defined output mismatch", result["failure_details"]["effective_failure_reason"])
        self.assertEqual(result["status"], "paused")

    def test_missing_baseline_is_not_fabricated(self):
        for missing in ("gpu_count", "elapsed_hours", "recorded_gpu_hours"):
            base = {**baseline(), missing: None, "missing_fields": [missing]}
            if missing == "recorded_gpu_hours": base["original_reference_cost_usd"] = None
            with self.subTest(missing=missing):
                result = self.calculate(base)
                self.assertIsNone(result["baseline"][missing])
                self.assertFalse(result["canonical_calculator_reused"])
                if missing == "elapsed_hours": self.assertIsNone(result["timing"]["completion_change_hours"])
                if missing == "recorded_gpu_hours": self.assertIsNone(result["costs"]["net_benefit_usd"])

    def test_baseline_and_request_are_copied_not_mutated(self):
        base, request = baseline(), inputs()
        expected_base, expected_request = copy.deepcopy(base), copy.deepcopy(request)
        result = simulate_pilot(base, request)
        self.assertEqual(base, expected_base)
        self.assertEqual(request, expected_request)
        base["recorded_gpu_hours"] = 999
        request["cpu_hours"] = 999
        self.assertEqual(result["baseline"]["recorded_gpu_hours"], 20)
        self.assertEqual(result["inputs"]["cpu_hours"], 12)

    def test_invalid_values_and_overflow_fail(self):
        invalid = [{"cpu_hours": float("nan")}, {"max_runtime_hours": 0}, {"cpu_vcpus": True},
                   {"cpu_vcpus": 1.5}, {"cpu_vcpu_hour_usd": -1}, {"max_trial_spend_usd": -1},
                   {"setup_cost_usd": float("inf")}, {"extra_queue_hours": -1},
                   {"baseline_host_costs_included": None}, {"correctness_check": " "},
                   {"outcome": "failure_recovered", "failure_reason": ""}, {"cpu_hours": 0},
                   {"cpu_vcpus": 10, "cpu_vcpu_hour_usd": 1e308}]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises((ValueError, OverflowError)):
                simulate_pilot(baseline(), inputs(**change))

    def test_schema_and_original_examples(self):
        jsonschema.Draft202012Validator.check_schema(SPEC)
        directory = ROOT / "contracts/examples/pilot-recovery"
        for path in directory.glob("*.json"):
            schema = "PilotBaselines" if path.name == "baselines.json" else "PilotSimulationRequest" if path.name.startswith("request-") else "PilotSimulation"
            with self.subTest(path=path.name): validate(schema, json.loads(path.read_text()))


class Routes(unittest.TestCase):
    def setUp(self):
        self.patches = [patch("service.main.inspect_data", return_value={"status": "missing", "fingerprint": None, "signature": None}),
                        patch("service.main.current_status", return_value="ready"),
                        patch("service.analysis_routes.current_status", return_value="ready")]
        for item in self.patches: item.start()
        self.client = TestClient(app).__enter__()
        provenance = dict(data_fingerprint="invented-pilot-source", source_version="invented-fixture-v1", synthetic=True,
                          sample_label="Original synthetic jobs", window_label="Invented window", caveats=["Original synthetic only"])
        jobs = [dict(id_job="PILOT-A", state_name="COMPLETED", sm_util_avg=0, sm_util_max=0, gpu_hours=20,
                     gpu_count=2, walltime_sec=36000, max_gpu_mem_used=0),
                dict(id_job="PILOT-UNKNOWN", state_name="COMPLETED", sm_util_avg=0, sm_util_max=0, gpu_hours=5,
                     gpu_count=None, walltime_sec=None, max_gpu_mem_used=None)]
        cohort = select_cohort(jobs)
        impacts = audit_impacts(cohort, [])
        evidence = make_evidence(cohort, impacts, [], {"summary": "Invented test eligibility rule"}, provenance)
        self.context = freeze_evidence(dict(cohort=cohort, impacts=impacts, findings=[], evidence=evidence, provenance=provenance))
        self.audit_request = dict(client_request_id="invented-parent-request", expected_data_fingerprint=provenance["data_fingerprint"],
                                 recommendation_id="cpu-placement-pilot", scenario=dict(recovery_fraction=dict(low=0, point=0, high=0),
                                 usd_per_gpu_hour=2.5, cancelled_policy="exclude", interval_kind="scenario", assumption_note="Invented baseline-only audit"))
        app.state.source = {"status": "ready", "fingerprint": provenance["data_fingerprint"], "signature": None}
        app.state.analysis_context = self.context
        self.snapshot = app.state.audits.create(self.audit_request, self.context)
        self.audit = self.snapshot.audit
        self.base = "/api/audits/" + self.audit["audit_id"]
        self.eid = evidence_id(provenance["data_fingerprint"], "job", "PILOT-A")
        self.body = inputs(baseline_evidence_id=self.eid)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches): item.stop()

    def post(self, body=None):
        return self.client.post(self.base + "/pilot-simulations", json=self.body if body is None else body)

    def test_list_frozen_baselines_and_unknowns(self):
        response = self.client.get(self.base + "/pilot-baselines")
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        validate("PilotBaselines", result)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["items"][0]["evidence_id"], self.eid)
        self.assertEqual(result["items"][0]["original_reference_cost_usd"], 50)
        unknown = result["items"][1]
        self.assertIsNone(unknown["gpu_count"])
        self.assertIsNone(unknown["elapsed_hours"])
        self.assertEqual(unknown["recorded_gpu_hours"], 5)
        response = self.post({**self.body, "baseline_evidence_id": unknown["evidence_id"]})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsNone(response.json()["timing"]["completion_change_hours"])

    def test_three_outcomes_have_scoped_identity_and_no_audit_mutation(self):
        before = self.client.get(self.base).json()
        claims = self.client.get(self.base + "/claims?team=OriginalSyntheticTeam").json()
        for outcome, status in [("success", "success"), ("failure_recovered", "recovered"), ("failure_unavailable", "paused")]:
            body = {**self.body, "outcome": outcome, "failure_reason": "Assumed incorrect output" if outcome != "success" else ""}
            response = self.post(body)
            self.assertEqual(response.status_code, 201, response.text)
            result = response.json()
            validate("PilotSimulation", result)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["audit_id"], self.audit["audit_id"])
            self.assertEqual(result["audit_client_request_id"], self.audit["client_request_id"])
            self.assertEqual(result["client_request_id"], body["client_request_id"])
            self.assertEqual(result["inputs"], body)
            self.assertTrue(result["synthetic"])
            self.assertFalse(result["execution_performed"])
        self.assertEqual(self.client.get(self.base).json(), before)
        self.assertEqual(self.client.get(self.base + "/claims?team=OriginalSyntheticTeam").json(), claims)

    def test_frozen_evidence_not_current_mutable_context(self):
        detail = self.context["evidence"][self.eid]
        next(o for o in detail["observations"] if o["name"] == "gpu_hours")["value"] = 999
        response = self.post()
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["baseline"]["recorded_gpu_hours"], 20)

    def test_forged_checkpoint_and_baseline_overrides_rejected(self):
        for key, value in (("checkpoint_verified", True), ("gpu_count", 1), ("baseline", baseline()),
                           ("original_reference_cost_usd", 99999)):
            with self.subTest(key=key):
                response = self.post({**self.body, key: value})
                self.assertEqual(response.status_code, 422, response.text)
                validate("PilotError", response.json())

    def test_unknown_and_nonjob_baseline_membership(self):
        for eid in ("foreign-evidence", evidence_id("invented-pilot-source", "aggregate", "accounting")):
            with self.subTest(eid=eid):
                response = self.post({**self.body, "baseline_evidence_id": eid})
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()["error"]["code"], "EVIDENCE_NOT_FOUND")

    def test_source_mismatch_blocks_both_routes(self):
        with patch("service.analysis_routes.current_status", return_value="invalid"):
            self.assertEqual(self.client.get(self.base + "/pilot-baselines").status_code, 409)
            self.assertEqual(self.post().status_code, 409)
        app.state.source["fingerprint"] = "changed-source"
        self.assertEqual(self.client.get(self.base + "/pilot-baselines").status_code, 409)
        self.assertEqual(self.post().status_code, 409)

    def test_mismatched_frozen_detail_fails_closed(self):
        # Deliberately build a corrupted frozen snapshot; never mutate real source files.
        self.context["evidence"][self.eid]["provenance"]["source_version"] = "foreign-version"
        freeze_evidence(self.context)
        corrupt = app.state.audits.create(self.audit_request, self.context)
        response = self.client.post("/api/audits/" + corrupt.audit["audit_id"] + "/pilot-simulations", json=self.body)
        self.assertEqual(response.status_code, 409)

    def test_nonfinite_missing_inputs_and_empty_reason_rejected(self):
        for body in ({}, {**self.body, "outcome": "failure_recovered"}, {**self.body, "correctness_check": " "}):
            self.assertEqual(self.post(body).status_code, 422)
        response = self.client.post(self.base + "/pilot-simulations", content=json.dumps({**self.body, "cpu_hours": float("nan")}), headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 422)

    def test_repeated_client_id_is_independent_no_execution(self):
        first, second = self.post().json(), self.post().json()
        self.assertNotEqual(first["simulation_id"], second["simulation_id"])
        self.assertEqual(first["costs"], second["costs"])
        self.assertEqual(first["client_request_id"], second["client_request_id"])
        self.assertTrue(second["independent_alternative"])
        self.assertFalse(second["history_persisted"])

    def test_missing_audit(self):
        response = self.client.post("/api/audits/missing/pilot-simulations", json=self.body)
        self.assertEqual(response.status_code, 404)

    def test_invalid_baseline_metrics_remain_null(self):
        detail = copy.deepcopy(self.context["evidence"][self.eid])
        for observation in detail["observations"]:
            if observation["name"] == "gpu_count": observation["value"] = 0
            if observation["name"] == "walltime_sec": observation["value"] = -1
            if observation["name"] == "gpu_hours": observation["unit"] = "seconds"
        result = baseline_from_evidence(detail, 2.5)
        for key in ("gpu_count", "elapsed_hours", "recorded_gpu_hours", "original_reference_cost_usd"):
            self.assertIsNone(result[key])


if __name__ == "__main__":
    unittest.main()
