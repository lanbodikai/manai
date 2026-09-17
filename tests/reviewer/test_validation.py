"""Invented, hand-worked oracles for C's independent read-only validator."""

import copy
import json
from pathlib import Path
import re
import unittest

from reviewer.validation import validate_audit


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "contracts/examples"


def fixture(name):
    return json.loads((EXAMPLES / name).read_text())


def coverage(count=2, *, complete=True, total=None):
    return {"listed_count": count, "fetched_count": count,
            "total": count if total is None else total,
            "complete": complete, "truncated": not complete,
            "reasons": [] if complete else ["request budget"]}


def job(audit_id, jid, hours, memory, gpu_count=1, seconds=None):
    # Original test data, not organizer rows. Units are literal test oracles.
    fields = [("state_name", "COMPLETED", None), ("sm_util_avg", 0, "percent"),
              ("sm_util_max", 0, "percent"), ("gpu_hours", hours, "gpu_hours"),
              ("gpu_count", gpu_count, "gpus"),
              ("walltime_sec", hours * 3600 / gpu_count if seconds is None else seconds, "seconds"),
              ("max_gpu_mem_used", memory, "bytes")]
    return {"audit_id": audit_id,
            "evidence": {"id": "job:" + jid, "kind": "job", "source_id": jid,
                         "label": "Invented test job " + jid, "synthetic": True},
            "source_table": "synthetic_jobs", "source_columns": [x[0] for x in fields],
            "join_keys": {"id_job": jid},
            "observations": [{"name": name, "column": name, "value": value, "unit": unit}
                             for name, value, unit in fields],
            "method": "Hand-worked invented fixture", "caveats": ["Synthetic"],
            "provenance": {"data_fingerprint": "synthetic-fixture-v1", "synthetic": True}}


def example():
    audit = fixture("audit-response.json")
    return audit, [job(audit["audit_id"], "J1", 10, 100), fixture("baseline-evidence.json")]


def observation(detail, column):
    return next(o for o in detail["observations"] if o["column"] == column)


def checks(report):
    return {row["id"]: row for row in report["checks"]}


class AuditValidationTests(unittest.TestCase):
    def run_check(self, audit, evidence, cover=None, mcp=None):
        return validate_audit(audit, evidence, coverage(len(evidence)) if cover is None else cover, mcp)

    def assert_status(self, report, key, status):
        self.assertEqual(checks(report)[key]["status"], status, checks(report)[key])

    def test_existing_eight_hand_worked_pilot_cases(self):
        # Expected fixture results were authored before this checker, not produced
        # by it or A's calculator. Every mode/unknown/sign must independently pass.
        for case in fixture("pilot-cases.json"):
            with self.subTest(case=case["name"]):
                audit, evidence = example()
                audit["scenario"]["cpu_pilot"] = case["input"]
                audit["downside"]["cpu_pilot"] = case["result"]
                report = self.run_check(audit, evidence)
                self.assertEqual([c for c in report["checks"] if c["status"] == "fail"], [])
                for metric in ("released_gpu_hours", "scenario_gpu_hours", "added_cpu_vcpu_hours", "added_cpu_reference_usd", "net_reference_value_usd", "run_time_change_hours_excluding_queue", "completion_change_hours_including_extra_queue"):
                    self.assert_status(report, "downside." + metric, "pass")
                self.assertEqual(report["verified_evidence_ids"], ["job:J1", "job:J2"])

    def test_missing_predicate_observations_are_unknown_not_failure(self):
        audit = fixture("audit-without-pilot.json")
        evidence = [fixture("evidence-response.json")]
        evidence[0]["audit_id"] = audit["audit_id"]
        evidence[0]["observations"] = [o for o in evidence[0]["observations"] if o["column"] != "sm_util_max"]
        report = self.run_check(audit, evidence, coverage(1, complete=False, total=2))
        self.assert_status(report, "downside.availability", "unknown")
        self.assert_status(report, "cohort.recorded_gpu_hours", "unknown")
        self.assert_status(report, "evidence.eligibility:" + evidence[0]["evidence"]["id"], "unknown")
        self.assertEqual([c for c in report["checks"] if c["status"] == "fail"], [])

    def test_v04_without_pilot_is_unknown_not_failure(self):
        audit = fixture("audit-without-pilot.json")
        report = self.run_check(audit, [], coverage(0, complete=False, total=2))
        self.assert_status(report, "downside.availability", "unknown")

    def test_no_input_mutation(self):
        audit, evidence = example()
        inputs = [audit, evidence, coverage(), {"data_fingerprint": "synthetic-fixture-v1"}]
        before = copy.deepcopy(inputs)
        self.run_check(*inputs)
        self.assertEqual(inputs, before)

    def test_recovery_uses_cohort_not_single_job_pilot(self):
        audit, evidence = example()
        audit["recovery"]["gpu_hours"]["point"] = 20
        report = self.run_check(audit, evidence)
        self.assert_status(report, "recovery.gpu_hours.point", "fail")
        self.assertEqual(checks(report)["recovery.gpu_hours.point"]["expected"], 12)

    def test_interval_and_price_errors(self):
        audit, evidence = example()
        audit["scenario"]["recovery_fraction"] = {"low": .5, "point": .4, "high": 1.1}
        audit["scenario"]["usd_per_gpu_hour"] = float("nan")
        report = self.run_check(audit, evidence)
        self.assert_status(report, "recovery.fractions", "fail")
        self.assert_status(report, "recovery.price", "fail")
        json.dumps(report, allow_nan=False)

    def test_memory_reconciliation_and_membership(self):
        audit, evidence = example()
        audit["eligibility"]["memory_partition"]["zero_memory"]["recorded_gpu_hours"] = 10
        audit["eligibility"]["memory_partition"]["positive_memory"]["recorded_gpu_hours"] = 20
        report = self.run_check(audit, evidence)
        self.assert_status(report, "memory.partition_hours", "pass")
        self.assert_status(report, "memory.zero_memory.recorded_gpu_hours", "fail")
        self.assert_status(report, "memory.positive_memory.recorded_gpu_hours", "fail")

    def test_unknown_memory_never_becomes_zero(self):
        audit, evidence = example()
        observation(evidence[0], "max_gpu_mem_used")["value"] = None
        report = self.run_check(audit, evidence)
        self.assert_status(report, "memory.unknown_memory.unique_jobs", "fail")
        self.assertEqual(checks(report)["memory.unknown_memory.recorded_gpu_hours"]["expected"], 10)
        self.assert_status(report, "memory.zero_memory.unique_jobs", "pass")

    def test_partial_coverage_cannot_certify_cohort_or_partition(self):
        audit, evidence = example()
        report = self.run_check(audit, evidence[:1], coverage(1, complete=False, total=2))
        self.assert_status(report, "cohort.recorded_gpu_hours", "unknown")
        self.assert_status(report, "cohort.unique_jobs", "unknown")
        self.assert_status(report, "memory.partition_evidence", "unknown")
        self.assert_status(report, "downside.baseline_source", "unknown")

    def test_false_complete_coverage_counts_do_not_pass(self):
        audit, evidence = example()
        report = self.run_check(audit, evidence[:1], coverage(2))
        self.assert_status(report, "evidence.coverage_counts", "fail")
        self.assert_status(report, "cohort.recorded_gpu_hours", "unknown")

    def test_complete_evidence_checks_actual_totals(self):
        audit, evidence = example()
        audit["eligibility"]["eligible_gpu_hours"] = 31
        report = self.run_check(audit, evidence)
        self.assert_status(report, "cohort.recorded_gpu_hours", "fail")
        self.assertEqual(checks(report)["cohort.recorded_gpu_hours"]["expected"], 30)

    def test_scope_fingerprint_and_synthetic_failures(self):
        for path, value in [("audit_id", "another-audit"), ("data_fingerprint", "stale"), ("synthetic", False), ("join", "J-other")]:
            with self.subTest(path=path):
                audit, evidence = example()
                if path == "audit_id":
                    evidence[1][path] = value
                elif path == "join":
                    evidence[1]["join_keys"]["id_job"] = value
                else:
                    evidence[1]["provenance"][path] = value
                report = self.run_check(audit, evidence)
                self.assert_status(report, "evidence.identity:job:J2", "fail")
                self.assertNotIn("job:J2", report["verified_evidence_ids"])

    def test_synthetic_jobs_cannot_be_presented_as_real(self):
        audit, evidence = example()
        audit["provenance"]["synthetic"] = False
        report = self.run_check(audit, evidence)
        self.assert_status(report, "evidence.identity:job:J2", "fail")

    def test_duplicate_physical_job_cannot_inflate_hours(self):
        audit, evidence = example()
        alias = copy.deepcopy(evidence[1])
        alias["evidence"]["id"] = "job:J2-alias"
        evidence.append(alias)
        report = self.run_check(audit, evidence)
        self.assert_status(report, "evidence.physical_job_uniqueness", "fail")
        self.assert_status(report, "cohort.recorded_gpu_hours", "unknown")
        self.assert_status(report, "downside.baseline_source", "unknown")
        self.assertNotIn("job:J2", report["verified_evidence_ids"])

    def test_findings_are_not_extra_physical_job_hours(self):
        audit, evidence = example()
        finding = copy.deepcopy(evidence[0])
        finding["evidence"].update(id="finding:F1", kind="finding", source_id="F1")
        observation(finding, "gpu_hours")["value"] = 9000
        evidence.append(finding)
        audit["evidence_count"] = 3
        report = self.run_check(audit, evidence)
        self.assert_status(report, "cohort.recorded_gpu_hours", "pass")
        self.assertEqual(checks(report)["cohort.recorded_gpu_hours"]["expected"], 30)

    def test_wrong_units_and_eligibility_are_not_approved(self):
        for column, value in [("gpu_hours", "engineer_hours"), ("sm_util_avg", "fraction"), ("max_gpu_mem_used", "gigabytes")]:
            with self.subTest(column=column):
                audit, evidence = example()
                observation(evidence[1], column)["unit"] = value
                report = self.run_check(audit, evidence)
                self.assert_status(report, "evidence.units:job:J2", "fail")
                self.assert_status(report, "downside.baseline_source", "unknown")
        audit, evidence = example()
        observation(evidence[1], "sm_util_max")["value"] = 1
        self.assert_status(self.run_check(audit, evidence), "evidence.eligibility:job:J2", "fail")

    def test_recorded_h_is_not_replaced_with_gpu_count_times_time(self):
        audit, evidence = example()
        # Source H=18, g*T=20. Hand-worked success: 18*$2.5-$4.8=$40.2.
        observation(evidence[1], "gpu_hours")["value"] = 18
        result = audit["downside"]["cpu_pilot"]
        result["baseline"]["recorded_gpu_hours"] = 18
        result["baseline"]["accounting_note"] = "Recorded H=18 differs from scheduler g*T=20."
        result.update(released_gpu_hours=18, released_gpu_reference_usd=45, net_reference_value_usd=40.2)
        report = self.run_check(audit, evidence)
        self.assert_status(report, "downside.released_gpu_hours", "pass")
        self.assert_status(report, "downside.net_reference_value_usd", "pass")
        self.assert_status(report, "downside.baseline.recorded_gpu_hours", "pass")
        result["released_gpu_hours"] = 20
        self.assert_status(self.run_check(audit, evidence), "downside.released_gpu_hours", "fail")

    def test_failure_does_not_charge_baseline_gpu_twice(self):
        audit, evidence = example()
        case = fixture("pilot-cases.json")[1]
        audit["scenario"]["cpu_pilot"] = case["input"]
        audit["downside"]["cpu_pilot"] = case["result"]
        audit["downside"]["cpu_pilot"]["net_reference_value_usd"] = -51.2
        report = self.run_check(audit, evidence)
        self.assert_status(report, "downside.net_reference_value_usd", "fail")
        self.assertAlmostEqual(checks(report)["downside.net_reference_value_usd"]["expected"], -1.2)

    def test_unknowns_cannot_turn_into_zero(self):
        for name, field in [("unknown-cpu-price", "added_cpu_reference_usd"), ("unknown-queue", "completion_change_hours_including_extra_queue"), ("incomplete-price-boundary", "net_reference_value_usd")]:
            with self.subTest(case=name):
                case = next(c for c in fixture("pilot-cases.json") if c["name"] == name)
                audit, evidence = example()
                audit["scenario"]["cpu_pilot"] = case["input"]
                audit["downside"]["cpu_pilot"] = case["result"]
                audit["downside"]["cpu_pilot"][field] = 0
                self.assert_status(self.run_check(audit, evidence), "downside." + field, "fail")

    def test_no_compatibility_or_cohort_approval_from_scenario(self):
        audit, evidence = example()
        pilot = audit["downside"]["cpu_pilot"]
        pilot.update(compatibility_verified=True, cash_savings_verified=True,
                     trial_stop_enforcement_tested=True, scope="cohort", evidence_kind="fact")
        report = self.run_check(audit, evidence)
        for field in ("compatibility_verified", "cash_savings_verified", "trial_stop_enforcement_tested", "scope", "evidence_kind"):
            self.assert_status(report, "downside." + field, "fail")

    def test_invalid_cap_nonfinite_and_negative_pilot_inputs(self):
        for field, value in [("trial_cap_hours", 11), ("cpu_vcpus", True), ("cpu_hours", float("inf")), ("extra_queue_hours", -1), ("cpu_vcpu_hour_usd", -1)]:
            with self.subTest(field=field):
                audit, evidence = example()
                audit["scenario"]["cpu_pilot"][field] = value
                self.assert_status(self.run_check(audit, evidence), "downside.inputs", "fail")

    def test_zero_cpu_price_is_known_and_negative_values_are_preserved(self):
        audit, evidence = example()
        audit["scenario"]["cpu_pilot"]["cpu_vcpu_hour_usd"] = 0
        audit["downside"]["cpu_pilot"].update(added_cpu_reference_usd=0, net_reference_value_usd=50)
        report = self.run_check(audit, evidence)
        self.assert_status(report, "downside.inputs", "pass")
        self.assert_status(report, "downside.net_reference_value_usd", "pass")

    def test_mcp_identity_does_not_invent_live_corroboration(self):
        audit, evidence = example()
        self.assert_status(self.run_check(audit, evidence), "mcp.source_identity", "unknown")
        self.assert_status(self.run_check(audit, evidence, mcp={"data_fingerprint": "wrong"}), "mcp.source_identity", "fail")
        self.assert_status(self.run_check(audit, evidence, mcp={"provenance": {"data_fingerprint": "synthetic-fixture-v1"}}), "mcp.source_identity", "pass")

    def test_v04_pilot_cannot_silently_enter_v03_contract(self):
        audit, evidence = example()
        audit["contract_version"] = "0.3"
        self.assert_status(self.run_check(audit, evidence), "downside.contract_version", "fail")

    def test_complete_claim_cannot_override_audit_manifest(self):
        audit, evidence = example()
        report = self.run_check(audit, evidence[:1], coverage(1))
        self.assert_status(report, "evidence.manifest_count", "fail")
        self.assert_status(report, "cohort.recorded_gpu_hours", "unknown")

    def test_conflicting_duplicate_reference_is_not_verified(self):
        audit, evidence = example()
        duplicate = copy.deepcopy(evidence[0])
        observation(duplicate, "gpu_hours")["value"] = 11
        evidence.append(duplicate)
        report = self.run_check(audit, evidence)
        self.assertNotIn("job:J1", report["verified_evidence_ids"])

    def test_preview_scope_cannot_be_relabelled(self):
        audit, evidence = example()
        evidence[1]["evidence"]["source_id"] = "unlisted"
        evidence[1]["join_keys"]["id_job"] = "unlisted"
        report = self.run_check(audit, evidence)
        self.assert_status(report, "evidence.identity:job:J2", "fail")

    def test_overflow_cannot_validate_nonfinite_outputs(self):
        audit, evidence = example()
        audit["scenario"]["cpu_pilot"]["cpu_hours"] = 1e308
        audit["downside"]["cpu_pilot"]["added_cpu_vcpu_hours"] = float("inf")
        report = self.run_check(audit, evidence)
        self.assert_status(report, "downside.added_cpu_vcpu_hours", "fail")
        json.dumps(report, allow_nan=False)
        audit["scenario"]["cpu_pilot"]["cpu_vcpus"] = 10 ** 1000
        self.assert_status(self.run_check(audit, evidence), "downside.inputs", "fail")

    def test_missing_baseline_memory_remains_unknown(self):
        audit, evidence = example()
        evidence[1]["observations"] = [o for o in evidence[1]["observations"] if o["column"] != "max_gpu_mem_used"]
        report = self.run_check(audit, evidence)
        self.assert_status(report, "downside.baseline_memory", "unknown")
        self.assert_status(report, "downside.compatibility_verified", "pass")
        self.assertIs(checks(report)["downside.compatibility_verified"]["expected"], False)

    def test_synthetic_finding_can_be_labeled_context_in_real_audit(self):
        audit, evidence = example()
        audit["provenance"]["synthetic"] = False
        for ref in audit["evidence_preview"]:
            ref["synthetic"] = False
        for detail in evidence:
            detail["evidence"]["synthetic"] = False
            detail["provenance"]["synthetic"] = False
        finding = copy.deepcopy(evidence[0])
        finding["evidence"].update(id="finding:S1", kind="finding", source_id="S1", synthetic=True)
        finding["provenance"]["synthetic"] = True
        evidence.append(finding)
        audit["evidence_count"] = 3
        report = self.run_check(audit, evidence)
        self.assert_status(report, "evidence.identity:finding:S1", "pass")
        self.assert_status(report, "cohort.recorded_gpu_hours", "pass")
        self.assertTrue(any("finding:S1" in item and "synthetic" in item for item in report["limitations"]))

    def test_opaque_evidence_ids_do_not_break_model_check_ids(self):
        audit, evidence = example()
        opaque = "job/工作/" + "x" * 140
        evidence[1]["evidence"]["id"] = opaque
        audit["evidence_preview"][1]["id"] = opaque
        audit["scenario"]["cpu_pilot"]["baseline_evidence_id"] = opaque
        audit["downside"]["cpu_pilot"]["baseline"]["evidence_id"] = opaque
        report = self.run_check(audit, evidence)
        self.assertIn(opaque, report["verified_evidence_ids"])
        self.assertTrue(all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", c["id"]) for c in report["checks"]))
        self.assert_status(report, "downside.baseline_source", "pass")


if __name__ == "__main__":
    unittest.main()
