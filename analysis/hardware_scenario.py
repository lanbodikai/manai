"""Documented hardware scenario, independent of canonical recovery/claims.

Ported from private evaluator ea6e732; contains no source-derived constants.
One modeled calculator vCPU represents one physical core, with no SMT speedup.
"""
import hashlib
import json
import math
from collections import Counter
from decimal import Decimal, ROUND_CEILING
from analysis.core import finite, native, select_cohort
from analysis.cpu_pilot import assess_cpu_pilot

VERSION = "cpu-hardware-1"
HARDWARE = {"name": "MIT Xeon Platinum 8260 CPU partition", "partition": "xeon-p8",
            "physical_cores": 48, "memory_mb": 192000, "memory_mb_per_core": 4000,
            "sources": ["https://mit-supercloud.github.io/supercloud-docs/systems-and-software/",
                        "https://mit-supercloud.github.io/supercloud-docs/submitting-jobs/"]}
ASSUMPTIONS = {"runtime_ratio": 1, "extra_queue_hours": 0, "cpu_price_ratios": [0.005, 0.02],
               "baseline_host_costs_included": True, "allocation_unit": "physical_core",
               "scope": "all_resource_fitting_jobs_not_a_small_pilot",
               "range_kind": "cpu_price_sensitivity_not_confidence_interval"}
LIMITATIONS = [
    "Successful CPU execution, unchanged runtime and zero added queue are assumptions, not observations.",
    "CPU reference rates are sensitivity assumptions, not verified MIT prices; values are not cash savings.",
    "Requested memory is not measured peak use. Decimal 192000 MB/node and 4000 MB/core are conservative sizing conventions.",
    "CPU slots model physical cores; additional cores provide memory capacity, not an assumed speedup.",
    "Spare CPU capacity, compatibility and output correctness are unverified. Multi-node placement is unresolved.",
    "Setup, migration, storage, contention and business-delay costs are omitted; further retries may cost more.",
    "The range covers only successful replacement under two CPU prices; failure is modeled separately.",
    "Whole historical sample window, not a next-quarter forecast. Official recovery/claims remain unchanged.",
]


def positive(value, integer=False):
    return finite(value) and value > 0 and (not integer or value == int(value))


def resource_fit(row):
    nodes, listed = row.get("nodes_alloc"), row.get("n_nodes_listed")
    if not positive(nodes, True) or not positive(listed, True) or nodes != listed:
        return {"status": "unresolved", "reason": "invalid_node_count"}
    if nodes != 1:
        return {"status": "unresolved", "reason": "multi_node_placement"}
    if not positive(row.get("cpus_req"), True) or not positive(row.get("mem_req_total_mb")):
        return {"status": "unresolved", "reason": "invalid_resource_request"}
    if not positive(row.get("walltime_sec")) or not positive(row.get("gpu_count"), True):
        return {"status": "unresolved", "reason": "invalid_scenario_baseline"}
    required = max(int(row["cpus_req"]), int((Decimal(str(row["mem_req_total_mb"])) / 4000).to_integral_value(rounding=ROUND_CEILING)))
    detail = {"requested_cores": int(row["cpus_req"]), "requested_memory_mb": row["mem_req_total_mb"],
              "memory_adjusted_cores": required, "extra_cores_for_memory": required - int(row["cpus_req"])}
    if row["mem_req_total_mb"] > 192000:
        return {**detail, "status": "non_fit", "reason": "requested_memory_exceeds_node"}
    if required > 48:
        return {**detail, "status": "non_fit", "reason": "required_cores_exceed_node"}
    return {**detail, "status": "fits", "reason": "requested_resources_fit"}


def build_hardware_scenario(rows, rate, price_version, fingerprint, dataset_version, synthetic=False):
    # Prepared jobs also contain array-valued metadata. Normalize only the scalar
    # fields used by this model; unrelated columns must not break resource sizing.
    fields = {'id_job', 'state_name', 'sm_util_avg', 'sm_util_max', 'gpu_hours',
              'gpu_count', 'walltime_sec', 'max_gpu_mem_used', 'nodes_alloc',
              'n_nodes_listed', 'cpus_req', 'mem_req_total_mb'}
    rows = [{k: native(v) for k, v in row.items() if k in fields} for row in rows]
    if not positive(rate) or not rows or len({str(r.get("id_job")) for r in rows}) != len(rows):
        raise ValueError("Invalid price or source identities")
    if any(r.get("id_job") is None or not finite(r.get("gpu_hours")) or r["gpu_hours"] < 0 for r in rows):
        raise ValueError("Invalid baseline allocation")
    by_id = {str(r["id_job"]): r for r in rows}
    cohort = select_cohort(rows)
    jobs, fitting = [], []
    for baseline in cohort.jobs:
        row = by_id[str(baseline["id_job"])]
        fit = resource_fit(row)
        memory = row.get("max_gpu_mem_used")
        record = {"job_id": str(row["id_job"]), "recorded_gpu_hours": row["gpu_hours"],
                  "scheduler_hours": row.get("walltime_sec", 0) / 3600 if row.get("walltime_sec") is not None else None,
                  "gpu_memory_category": "unknown" if not finite(memory) or memory < 0 else "zero" if memory == 0 else "positive",
                  **fit}
        if fit["status"] == "fits":
            fitting.append((row, fit))
            record["cost_break_even_cpu_hours"] = {
                name: {"low_cpu_price": row["gpu_hours"] / (cores * .005), "high_cpu_price": row["gpu_hours"] / (cores * .02)}
                for name, cores in (("memory_adjusted", fit["memory_adjusted_cores"]), ("whole_node", 48))}
        jobs.append(record)
    baseline = math.fsum(r["gpu_hours"] for r in rows) * rate
    target = baseline * .2
    allocations = []
    for name in ("memory_adjusted", "whole_node"):
        cases = []
        for ratio in ASSUMPTIONS["cpu_price_ratios"]:
            outputs = {mode: [] for mode in ("replacement_success", "replacement_failure", "additional_validation")}
            for row, fit in fitting:
                for mode in outputs:
                    p = {"mode": mode, "baseline_evidence_id": "hardware-job:" + str(row["id_job"]),
                         "cpu_vcpus": fit["memory_adjusted_cores"] if name == "memory_adjusted" else 48,
                         "cpu_hours": row["walltime_sec"] / 3600, "cpu_vcpu_hour_usd": rate * ratio,
                         "extra_queue_hours": 0, "trial_cap_hours": None, "baseline_host_costs_included": True,
                         "assumption_note": "Documented hardware; physical-core units; successful runtime is assumed unchanged."}
                    outputs[mode].append(assess_cpu_pilot(row, p, rate))
            net = math.fsum(x["net_reference_value_usd"] for x in outputs["replacement_success"])
            failure_net = math.fsum(x["net_reference_value_usd"] for x in outputs["replacement_failure"])
            cases.append({"cpu_price_ratio": ratio, "cpu_reference_usd_per_core_hour": rate * ratio,
                          "cpu_core_hours": math.fsum(x["added_cpu_vcpu_hours"] for x in outputs["replacement_success"]),
                          "cpu_cost_reference_usd": math.fsum(x["added_cpu_reference_usd"] for x in outputs["replacement_success"]),
                          "released_gpu_hours_if_success": math.fsum(x["released_gpu_hours"] for x in outputs["replacement_success"]),
                          "success_net_reference_usd": net, "failure_net_reference_usd": failure_net,
                          "failure_extra_reference_usd": -failure_net,
                          "validation_net_reference_usd": math.fsum(x["net_reference_value_usd"] for x in outputs["additional_validation"]),
                          "success_completion_change_hours": 0, "failure_runtime_ratio": 2,
                          "validation_completion_change_hours": None,
                          "positive_no_slower_jobs": sum(x["net_reference_value_usd"] > 1e-8 for x in outputs["replacement_success"]),
                          "baseline_reduction_pct": 100 * net / baseline if baseline else 0,
                          "target_contribution_pct": 100 * net / target if target else 0,
                          "remaining_target_reference_usd": max(0, target - net)})
        def bounds(field):
            return {"low": min(c[field] for c in cases), "high": max(c[field] for c in cases)}
        allocations.append({"id": name, "cases": cases, **{field: bounds(field) for field in (
            "success_net_reference_usd", "failure_extra_reference_usd", "baseline_reduction_pct",
            "target_contribution_pct", "remaining_target_reference_usd")}})
    counts = Counter(j["status"] for j in jobs)
    result = {"contract_version": VERSION, "dataset_version": dataset_version, "data_fingerprint": fingerprint,
              "synthetic": synthetic, "kind": "scenario_estimate", "hardware": HARDWARE, "assumptions": ASSUMPTIONS,
              "gpu_reference_usd_per_hour": rate, "price_book_version": price_version,
              "baseline_reference_usd": baseline, "target_reference_usd": target,
              "coverage": {"eligible_jobs": len(jobs), "eligible_gpu_hours": cohort.hours,
                           "fitting_jobs": counts["fits"], "non_fitting_jobs": counts["non_fit"], "unresolved_jobs": counts["unresolved"],
                           "fitting_gpu_hours": math.fsum(r["gpu_hours"] for r, _ in fitting),
                           "memory_resized_jobs": sum(f["extra_cores_for_memory"] > 0 for _, f in fitting)},
              "allocations": allocations, "limitations": LIMITATIONS, "compatibility_verified": False, "cash_savings_verified": False}
    identity = json.dumps({"result": result, "jobs": jobs}, sort_keys=True, allow_nan=False)
    result["scenario_id"] = hashlib.sha256(identity.encode()).hexdigest()
    return result, jobs
