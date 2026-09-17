"""Offline real-baseline check. Never bypasses A's five-file readiness gate.

Reads organizer data locally, prints aggregate checks only, and writes no rows.
All trial outcomes and prices below are explicit invented sensitivity inputs.
"""
import argparse
import json
import math
from pathlib import Path

import pandas as pd

from analysis.pilot_recovery import baseline_from_evidence, simulate_pilot
from scripts.checksum_data import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = Path(__file__).resolve().parents[2] / "data/checksums.txt"
    expected = {name: sha for line in manifest.read_text().splitlines()
                if line.strip() and not line.startswith("#") for sha, name in [line.split()]}
    for name in ("prepped/jobs.parquet", "prepped/gpus.parquet"):
        assert digest(args.data_dir / name) == expected[name], "Prepared value hash mismatch"
    jobs = pd.read_parquet(args.data_dir / "prepped/jobs.parquet")
    # Independent direct predicate, not A's cohort selector.
    eligible = jobs.loc[(jobs.state_name == "COMPLETED") & (jobs.sm_util_avg == 0)
                        & (jobs.sm_util_max == 0) & (jobs.gpu_hours > 1)]
    assert len(eligible) > 0, "No eligible historical baselines were checked"
    fields = {"gpu_hours": "GPU-hours", "gpu_count": "GPUs", "walltime_sec": "seconds",
              "state_name": None, "sm_util_avg": "percent", "sm_util_max": "percent",
              "max_gpu_mem_used": "bytes"}
    checked = 0
    reuse = 0
    for index, (_, row) in enumerate(eligible.iterrows()):
        observations = []
        for column, unit in fields.items():
            value = row.get(column)
            if value is not None and pd.isna(value):
                value = None
            if hasattr(value, "item"):
                value = value.item()
            observations.append({"name": column, "unit": unit, "value": value})
        # Local identity is only for pure-calculator input; it is never an A audit/evidence receipt.
        detail = {"evidence": {"id": f"offline-baseline-{index}", "source_id": str(row.id_job)},
                  "observations": observations, "provenance": {"synthetic": False}}
        baseline = baseline_from_evidence(detail, 2.5)
        original = float(row.gpu_hours) * 2.5
        elapsed = float(row.walltime_sec) / 3600  # Independent raw-row unit conversion.
        assert math.isclose(baseline["original_reference_cost_usd"], original)
        assert math.isfinite(elapsed) and elapsed > 0, "Selected baseline runtime is invalid"
        assert baseline["elapsed_hours"] is not None, "Selected baseline runtime is missing"
        assert math.isclose(baseline["elapsed_hours"], elapsed, rel_tol=1e-12)
        for mode in ("success", "failure_recovered", "failure_unavailable"):
            cpu_duration = 12 if mode == "success" else 3
            request = {"client_request_id": "offline-check", "baseline_evidence_id": baseline["evidence_id"],
                       "proposal": "Invented CPU placement sensitivity; not a workload run",
                       "correctness_check": "Future owner-provided output comparison",
                       "cpu_vcpus": 4, "cpu_hours": cpu_duration, "cpu_vcpu_hour_usd": .1,
                       "max_runtime_hours": 20, "max_trial_spend_usd": 100,
                       "setup_cost_usd": 0, "extra_queue_hours": 0,
                       "baseline_host_costs_included": True, "outcome": mode,
                       "failure_reason": "" if mode == "success" else "Invented output mismatch",
                       "recovery_note": "Assumed original resources available" if mode != "failure_unavailable" else "Assumed original resources unavailable"}
            result = simulate_pilot(baseline, request)
            cost = result["costs"]
            trial = 4.8 if mode == "success" else 1.2  # Hand-calculated independent oracle.
            assert math.isclose(cost["cpu_trial_cost_usd"], trial, rel_tol=1e-12)
            assert cost["original_cost_usd"] == original
            if mode == "failure_unavailable":
                assert result["status"] == "paused"
                assert cost["total_cost_to_complete_usd"] is None
                assert cost["net_benefit_usd"] is None
                assert result["timing"]["completion_change_hours"] is None
                assert math.isclose(cost["cost_so_far_usd"], trial)
            else:
                total = trial + (original if mode == "failure_recovered" else 0)
                assert math.isclose(cost["total_cost_to_complete_usd"], total, rel_tol=1e-12)
                assert math.isclose(cost["net_benefit_usd"], original - total, abs_tol=1e-8)
                delay = 3 if mode == "failure_recovered" else 12 - elapsed
                assert math.isclose(result["timing"]["completion_change_hours"], delay, abs_tol=1e-9)
            assert result["execution_performed"] is False
            assert result["recovery"]["checkpoint_verified"] is False
            checked += 1
            reuse += int(result["canonical_calculator_reused"])
    print(json.dumps({"status": "passed", "prepared_tables_verified": 2,
                      "eligible_historical_baselines": len(eligible), "three_outcome_checks": checked,
                      "canonical_calculator_reuse_cases": reuse,
                      "trial_inputs": "Invented: 4 vCPUs at $0.10/vCPU-hour, 12h success/3h failure, zero setup/queue, $2.50 reference GPU-hour",
                      "source_rows_written": False, "live_A_readiness_verified": False,
                      "five_file_gate_verified": False, "workloads_executed": 0}, indent=2))


if __name__ == "__main__":
    main()
