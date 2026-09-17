"""Single-job hypothetical cost/delay, adapted from the reviewed verifier model.

Preserve recorded allocation H independently of scheduler duration T. This does
not execute a workload, forecast cohort recovery or prove CPU compatibility.
"""
import math


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(name + " must be finite")
    if value < 0 or (positive and value == 0):
        raise ValueError(name + " outside permitted range")
    return value


def integer(value, name):
    number(value, name, positive=True)
    if int(value) != value:
        raise ValueError(name + " must be an integer")
    return int(value)


def assess_cpu_pilot(job, pilot, gpu_price):
    mode = pilot["mode"]
    if mode not in {"replacement_success", "replacement_failure", "additional_validation"}:
        raise ValueError("Unknown CPU pilot mode")
    h = number(job.get("gpu_hours"), "Recorded GPU-hours", positive=True)
    t = number(job.get("walltime_sec"), "Scheduler duration", positive=True) / 3600
    if t <= 0:
        raise ValueError("Scheduler duration underflows hours")
    g = integer(job.get("gpu_count"), "Baseline GPU count")
    v = integer(pilot["cpu_vcpus"], "CPU vCPUs")
    c = number(pilot["cpu_hours"], "CPU duration", positive=mode == "replacement_success")
    pg = number(gpu_price, "GPU reference price", positive=True)
    for key in ("cpu_vcpu_hour_usd", "extra_queue_hours", "trial_cap_hours"):
        if pilot[key] is not None:
            number(pilot[key], key)
    if pilot["trial_cap_hours"] is not None and c > pilot["trial_cap_hours"]:
        raise ValueError("CPU duration exceeds assumed trial cap")
    if type(pilot["baseline_host_costs_included"]) is not bool:
        raise ValueError("Pricing boundary must be explicit")
    released = h if mode == "replacement_success" else 0
    cpu_hours = v * c
    cost = None if pilot["cpu_vcpu_hour_usd"] is None else cpu_hours * pilot["cpu_vcpu_hour_usd"]
    net = None if cost is None or not pilot["baseline_host_costs_included"] else released * pg - cost
    runtime = c - t if mode == "replacement_success" else c if mode == "replacement_failure" else None
    completion = None if runtime is None or pilot["extra_queue_hours"] is None else runtime + pilot["extra_queue_hours"]
    scheduler_allocation = g * t
    note = (f"Use recorded allocation H={h:.17g} GPU-hours and scheduler T={t:.17g} hours separately. "
            f"GPU count times scheduler duration is {scheduler_allocation:.17g} GPU-hours; "
            + ("it agrees within numerical tolerance." if math.isclose(h, scheduler_allocation, rel_tol=1e-9)
               else "it differs from recorded allocation; recorded H is preserved."))
    result = {"scope": "single_job", "mode": mode, "evidence_kind": "scenario_estimate",
        "baseline": {"evidence_id": pilot["baseline_evidence_id"], "gpu_count": g, "elapsed_hours": t,
                     "recorded_gpu_hours": h, "accounting_note": note},
        "scenario_gpu_hours": h - released, "released_gpu_hours": released,
        "added_cpu_vcpu_hours": cpu_hours, "released_gpu_reference_usd": released * pg,
        "added_cpu_reference_usd": cost, "net_reference_value_usd": net,
        "run_time_change_hours_excluding_queue": runtime, "completion_change_hours_including_extra_queue": completion,
        "compatibility_verified": False, "cash_savings_verified": False, "trial_stop_enforcement_tested": False,
        "limitations": ["Single-job assumed scenario; not cohort recovery or realized savings.",
                        "Migration, storage, setup, contention and business-delay costs excluded.",
                        "Failure assumes a full GPU rerun with no reused CPU progress; additional-validation completion impact is unknown.",
                        "Trial cap validates input only; no workload stop or rollback has been tested.",
                        "Assumed CPU inputs: " + pilot["assumption_note"]]}
    if not all(math.isfinite(value) for value in result.values() if isinstance(value, (int, float))):
        raise ValueError("CPU scenario arithmetic overflow")
    if not math.isfinite(scheduler_allocation):
        raise ValueError("Baseline arithmetic overflow")
    return result


def memory_partition(cohort):
    groups = {key: [] for key in ("zero_memory", "positive_memory", "unknown_memory")}
    for job in cohort.jobs:
        memory = job.get("max_gpu_mem_used")
        known = isinstance(memory, (int, float)) and not isinstance(memory, bool) and math.isfinite(memory) and memory >= 0
        key = "unknown_memory" if not known else "zero_memory" if memory == 0 else "positive_memory"
        groups[key].append(job["gpu_hours"])
    return {**{key: {"unique_jobs": len(values), "recorded_gpu_hours": math.fsum(values)} for key, values in groups.items()},
        "basis": "Maximum observed GPU-memory bytes partition the unchanged broad cohort. Missing/invalid memory stays unknown; zero memory is an investigation priority, not proof of CPU compatibility."}
