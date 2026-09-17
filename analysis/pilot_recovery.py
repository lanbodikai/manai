"""Independent, hypothetical CPU pilot alternatives; never runs or restores work."""
from copy import deepcopy
import math

from analysis.cpu_pilot import assess_cpu_pilot


OUTCOMES = {"success", "failure_recovered", "failure_unavailable"}
LIMITATIONS = [
    "Simulation only: no workload was started, stopped, validated or recovered.",
    "Each result is one independent alternative, not an accumulated retry history.",
    "Historical telemetry does not include executable configuration, inputs, reference outputs or verified checkpoints.",
    "Correctness and recovery completion are assumed outcomes, not results established by this calculator.",
    "Runtime and spending limits operate inside this simulation only; no live enforcement has been tested.",
    "Dollars are reference estimates, not verified cash savings. Migration, storage, contention and business-delay costs are excluded.",
    "The trial spending limit includes setup and CPU execution, but excludes recovery spending.",
    "The response is a standalone snapshot; the server does not persist simulation history.",
]


def finite(value, positive=False, integer=False):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and (value > 0 if positive else value >= 0)
            and (not integer or int(value) == value))


def nullable_measure(value, positive=False, integer=False):
    return value if finite(value, positive=positive, integer=integer) else None


def checked(value):
    if value is not None and not math.isfinite(value):
        raise ValueError("Pilot arithmetic overflow")
    return value


def add_known(*values):
    return None if any(v is None for v in values) else checked(math.fsum(values))


def baseline_from_evidence(detail, gpu_price):
    """Copy nullable measurements from an already scoped frozen job detail."""
    observations = {o["name"]: o for o in detail["observations"]}
    def measured(name, unit, **kwargs):
        observation = observations.get(name, {})
        return nullable_measure(observation.get("value"), **kwargs) if observation.get("unit") == unit else None
    hours = measured("gpu_hours", "GPU-hours", positive=True)
    duration = measured("walltime_sec", "seconds", positive=True)
    elapsed = None if duration is None else nullable_measure(duration / 3600, positive=True)
    price = nullable_measure(gpu_price, positive=True)
    cost = checked(hours * price) if hours is not None and price is not None else None
    result = {
        "evidence_id": detail["evidence"]["id"],
        "source_job_id": detail["evidence"]["source_id"],
        "synthetic": detail["provenance"]["synthetic"],
        "state_name": observations.get("state_name", {}).get("value"),
        "sm_util_avg": measured("sm_util_avg", "percent"),
        "sm_util_max": measured("sm_util_max", "percent"),
        "max_gpu_mem_used": measured("max_gpu_mem_used", "bytes"),
        "gpu_count": measured("gpu_count", "GPUs", positive=True, integer=True),
        "elapsed_hours": elapsed,
        "recorded_gpu_hours": hours,
        "usd_per_gpu_hour": price,
        "original_reference_cost_usd": cost,
    }
    result["missing_fields"] = [k for k in ("gpu_count", "elapsed_hours", "recorded_gpu_hours",
                                               "usd_per_gpu_hour", "original_reference_cost_usd") if result[k] is None]
    return result


def validate_inputs(inputs):
    """Defense in depth for direct calculator use; HTTP also applies closed JSON Schema."""
    if inputs.get("outcome") not in OUTCOMES:
        raise ValueError("Unknown pilot outcome")
    for key in ("client_request_id", "baseline_evidence_id", "proposal", "correctness_check"):
        if not isinstance(inputs.get(key), str) or not inputs[key].strip():
            raise ValueError(key + " must be nonblank")
    if not finite(inputs.get("cpu_vcpus"), positive=True, integer=True):
        raise ValueError("CPU vCPUs must be a positive integer")
    for key in ("cpu_hours", "max_trial_spend_usd"):
        if not finite(inputs.get(key)):
            raise ValueError(key + " must be finite and nonnegative")
    if not finite(inputs.get("max_runtime_hours"), positive=True):
        raise ValueError("Maximum runtime must be positive")
    if inputs["outcome"] == "success" and inputs["cpu_hours"] <= 0:
        raise ValueError("A successful CPU trial needs positive duration")
    for key in ("cpu_vcpu_hour_usd", "setup_cost_usd", "extra_queue_hours"):
        if inputs.get(key) is not None and not finite(inputs[key]):
            raise ValueError(key + " must be nonnegative or unknown")
    if type(inputs.get("baseline_host_costs_included")) is not bool:
        raise ValueError("Pricing boundary must be explicit")
    for key in ("failure_reason", "recovery_note"):
        if not isinstance(inputs.get(key), str):
            raise ValueError(key + " must be text")
    if inputs["outcome"] != "success" and not inputs["failure_reason"].strip():
        raise ValueError("A failed trial needs an explicit assumed failure reason")


def simulate_pilot(baseline, inputs):
    """Return a deterministic alternative, preserving unfinished work and unknown costs."""
    validate_inputs(inputs)
    if inputs["baseline_evidence_id"] != baseline["evidence_id"]:
        raise ValueError("Baseline identity mismatch")
    requested = inputs["cpu_hours"]
    runtime_cap = inputs["max_runtime_hours"]
    spend_cap = inputs["max_trial_spend_usd"]
    setup = inputs["setup_cost_usd"]
    price = inputs["cpu_vcpu_hour_usd"]
    vcpus = inputs["cpu_vcpus"]
    hourly_cost = None if price is None else checked(vcpus * price)
    preflight_blocked = setup is not None and setup > spend_cap
    budget_known = setup is not None and hourly_cost is not None
    budget_duration = None
    if hourly_cost is not None and not preflight_blocked and hourly_cost > 0:
        # Unknown nonnegative setup still leaves CPU spending bounded above by the entire cap.
        # This optimistic ceiling does not verify the combined budget. An infinite quotient
        # means the finite requested duration cannot reach this particular bound.
        budget_duration = (spend_cap - (setup if setup is not None else 0)) / hourly_cost
    duration = min(requested, runtime_cap)
    if preflight_blocked:
        duration, incurred_setup = 0, 0
        stop = "setup_exceeds_spend_limit"
    else:
        incurred_setup = setup
        if budget_duration is not None:
            duration = min(duration, budget_duration)
        runtime_stop = requested > runtime_cap and duration == runtime_cap
        spend_stop = budget_duration is not None and requested > budget_duration and duration == budget_duration
        stop = ("runtime_and_spend_limit" if runtime_stop and spend_stop else
                "runtime_limit" if runtime_stop else "spend_limit" if spend_stop else None)
    effective = inputs["outcome"]
    if stop is not None and effective == "success":
        effective = "failure_recovered"
    recovered = effective == "failure_recovered"
    paused = effective == "failure_unavailable"
    success = effective == "success"
    cpu_vcpu_hours = checked(vcpus * duration)
    cpu_cost = 0 if preflight_blocked else None if price is None else checked(cpu_vcpu_hours * price)
    trial_cost = add_known(cpu_cost, incurred_setup)
    original_cost = baseline["original_reference_cost_usd"]
    recovery_cost = None if paused else original_cost if recovered else 0
    total_cost = None if paused else add_known(trial_cost, recovery_cost)
    net = (checked(original_cost - total_cost)
           if original_cost is not None and total_cost is not None and inputs["baseline_host_costs_included"] else None)
    elapsed = baseline["elapsed_hours"]
    queue = inputs["extra_queue_hours"]
    runtime_change = None if paused else duration if recovered else None if elapsed is None else checked(duration - elapsed)
    completion_change = add_known(runtime_change, queue)
    total_elapsed = None if paused else add_known(duration, elapsed if recovered else 0, queue)
    recorded = baseline["recorded_gpu_hours"]
    released = None if paused else recorded if success else 0
    remaining = None if paused else recorded if recovered else 0

    # Reuse the reviewed canonical arithmetic wherever its required baseline exists.
    canonical = None
    reusable = all(baseline[k] is not None for k in ("gpu_count", "elapsed_hours", "recorded_gpu_hours", "usd_per_gpu_hour"))
    if reusable and not paused:
        canonical = assess_cpu_pilot({"gpu_count": baseline["gpu_count"],
            "walltime_sec": checked(baseline["elapsed_hours"] * 3600), "gpu_hours": recorded}, {
            "mode": "replacement_success" if success else "replacement_failure",
            "baseline_evidence_id": baseline["evidence_id"], "cpu_vcpus": vcpus,
            "cpu_hours": duration, "cpu_vcpu_hour_usd": price, "extra_queue_hours": queue,
            "trial_cap_hours": runtime_cap, "baseline_host_costs_included": inputs["baseline_host_costs_included"],
            "assumption_note": inputs["proposal"]}, baseline["usd_per_gpu_hour"])
        # Check the wrapper's cost and completion basis against the unchanged reviewed calculator.
        if not preflight_blocked and canonical["added_cpu_reference_usd"] != cpu_cost:
            raise ValueError("Canonical CPU cost mismatch")
        if canonical["completion_change_hours_including_extra_queue"] != completion_change:
            raise ValueError("Canonical completion comparison mismatch")
        released, remaining = canonical["released_gpu_hours"], canonical["scenario_gpu_hours"]

    failure = None if success else (inputs["failure_reason"].strip() or "The simulated trial was stopped by its configured limit.")
    if stop is not None and inputs["failure_reason"].strip():
        failure += " The simulated limit also stopped the trial: " + stop + "."
    spend_status = ("blocked_before_start" if preflight_blocked else "unverified" if not budget_known else
                    "reached" if stop in {"spend_limit", "runtime_and_spend_limit"} else "within_limit")
    limitations = list(LIMITATIONS)
    if not budget_known and not preflight_blocked:
        limitations.append("Unknown CPU price or setup cost prevents verifying the combined spending cap. Known CPU spending is still bounded by the remaining known budget; unknown setup may exhaust it earlier.")
    if not inputs["baseline_host_costs_included"]:
        limitations.append("The baseline host/CPU pricing boundary is incomplete; net benefit is unknown.")
    if baseline["missing_fields"]:
        limitations.append("Missing or invalid baseline measurements stay unknown: " + ", ".join(baseline["missing_fields"]) + ".")
    if paused:
        limitations.append("Recovery is unavailable and work remains unfinished. No net benefit or completed-work savings is claimed.")
    if baseline["synthetic"]:
        limitations.insert(0, "SYNTHETIC BASELINE: this example is not real workload telemetry.")
    causes = [] if success else [
        {"hypothesis": "The workload may require a GPU runtime or device even with zero recorded SM activity.",
         "next_check": "Inspect launch configuration and dependencies, then run an isolated startup check.", "evidence_status": "unverified_hypothesis"},
        {"hypothesis": "CPU runtime, memory demand or output quality may differ from the original run.",
         "next_check": "Compare representative peak phases and final outputs against the workload owner's correctness criterion.", "evidence_status": "unverified_hypothesis"},
    ]
    proof = [
        {"quantity": "Original reference cost", "formula": "recorded baseline GPU-hours × audit GPU-hour reference rate", "value": original_cost, "unit": "reference USD"},
        {"quantity": "CPU trial cost", "formula": "effective simulated CPU hours × vCPUs × CPU-hour reference rate; zero if blocked before startup", "value": cpu_cost, "unit": "reference USD"},
        {"quantity": "Trial cost", "formula": "CPU trial cost + incurred setup cost", "value": trial_cost, "unit": "reference USD"},
        {"quantity": "Total cost to complete", "formula": "trial cost + full original GPU rerun cost when recovered; unknown when recovery is unavailable", "value": total_cost, "unit": "reference USD"},
        {"quantity": "Net benefit", "formula": "original reference cost − total cost to complete; unknown if pricing boundary is incomplete", "value": net, "unit": "reference USD"},
    ]
    result = {
        "simulation_only": True, "execution_performed": False, "independent_alternative": True,
        "history_persisted": False, "compatibility_verified": False, "cash_savings_verified": False,
        "live_stop_enforcement_verified": False,
        "inputs": deepcopy(inputs), "baseline": deepcopy(baseline),
        "status": "paused" if paused else "recovered" if recovered else "success",
        "effective_outcome": effective, "stop_reason": stop,
        "failure_details": {"requested_failure_reason": inputs["failure_reason"], "effective_failure_reason": failure,
                            "selected_outcome_changed": effective != inputs["outcome"]},
        "costs": {"currency": "USD", "kind": "reference_estimate", "original_cost_usd": original_cost,
                  "cpu_trial_cost_usd": cpu_cost, "setup_cost_usd": incurred_setup, "trial_cost_usd": trial_cost,
                  "recovery_cost_usd": recovery_cost, "cost_so_far_usd": trial_cost if paused else total_cost,
                  "total_cost_to_complete_usd": total_cost, "net_benefit_usd": net},
        "timing": {"requested_cpu_hours": requested, "effective_cpu_hours": duration,
                   "baseline_elapsed_hours": elapsed, "extra_queue_hours": queue,
                   "run_time_change_hours_excluding_queue": runtime_change,
                   "completion_change_hours": completion_change, "total_elapsed_hours_including_queue": total_elapsed},
        "capacity": {"released_gpu_hours": released, "remaining_gpu_hours": remaining,
                     "added_cpu_vcpu_hours": cpu_vcpu_hours},
        "limits": {"max_runtime_hours": runtime_cap, "max_trial_spend_usd": spend_cap,
                   "requested_setup_cost_usd": setup, "runtime_limit_reached": stop in {"runtime_limit", "runtime_and_spend_limit"},
                   "spend_limit_status": spend_status, "cap_enforcement": "simulation_only",
                   "trial_started": not preflight_blocked and duration > 0, "spend_limit_excludes_recovery": True},
        "recovery": {"status": "unavailable_paused" if paused else "assumed_completed" if recovered else "not_required",
                     "strategy": "full_original_gpu_rerun" if recovered else "none", "checkpoint_verified": False,
                     "available_assumed": inputs["outcome"] != "failure_unavailable", "note": inputs["recovery_note"],
                     "recovery_gpu_hours": recorded if recovered else None if paused else 0},
        "timeline": [
            {"step": "baseline", "status": "incomplete" if baseline["missing_fields"] else "captured", "detail": "Frozen historical job evidence; no runnable configuration or verified checkpoint is supplied."},
            {"step": "trial", "status": "blocked" if preflight_blocked else "stopped" if stop else "assumed_success" if success else "assumed_failure", "detail": "Simulated CPU duration: " + str(duration) + " hours. Correctness criterion: " + inputs["correctness_check"]},
            {"step": "recovery", "status": "paused" if paused else "assumed_completed" if recovered else "not_required", "detail": "Recovery unavailable; work remains paused." if paused else "Assume a full original GPU rerun; no checkpoint progress is reused." if recovered else "No rerun needed under the assumed successful replacement."},
            {"step": "result", "status": "paused" if paused else "estimated", "detail": "No completed-work savings can be claimed while paused." if paused else "Reference costs compare two independent ways of completing the same work; this is not a measured intervention."},
        ],
        "canonical_calculator_reused": canonical is not None,
        "calculator_proof": proof, "possible_causes": causes, "limitations": limitations,
    }
    return result
