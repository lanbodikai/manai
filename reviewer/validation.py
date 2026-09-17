"""Read-only, independent checks of an audit and its scoped evidence.

This module never imports A's calculator, retrieves data, or changes canonical
claims. A passing arithmetic check is not a CPU compatibility certification.
Evidence is the public EvidenceDetail shape. Complete pagination does not imply
complete cohort coverage unless every claimed job is represented exactly once.
"""

from __future__ import annotations

import copy
import hashlib
import math
import re
from typing import Any

_MISSING = object()
_BOUNDS = ("low", "point", "high")
_MEMORY_GROUPS = ("zero_memory", "positive_memory", "unknown_memory")
_UNITS = {
    "state_name": None,
    "sm_util_avg": "percent",
    "sm_util_max": "percent",
    "gpu_hours": "gpu_hours",
    "gpu_count": "gpus",
    "walltime_sec": "seconds",
    "max_gpu_mem_used": "bytes",
}
_CHECK_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z")


def _mapping(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _number(value: Any, *, minimum: float | None = None) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and (minimum is None or value >= minimum)
    except OverflowError:
        return False


def _integer(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, int) and _number(value, minimum=minimum)


def _sum(values) -> float:
    try:
        return math.fsum(values)
    except (OverflowError, ValueError):
        return float("nan")


def _same(actual: Any, expected: Any) -> bool:
    if expected is None:
        return actual is None
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return _number(expected) and _number(actual) and math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6)
    return type(actual) is type(expected) and actual == expected


def _safe(value: Any) -> Any:
    """Keep malformed observations reportable without emitting NaN/Infinity."""
    if value is _MISSING:
        return "missing"
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    return value


class _Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.limitations: list[str] = []

    def add(self, key: str, status: str, message: str, sources=(), **values) -> str:
        self.checks.append({
            "id": key, "status": status, "message": message,
            "source_ids": list(dict.fromkeys(str(s) for s in sources if s is not None)),
            **{k: _safe(v) for k, v in values.items()},
        })
        return status

    def compare(self, key: str, actual: Any, expected: Any, message: str, sources=()) -> str:
        status = "unknown" if actual is _MISSING else ("pass" if _same(actual, expected) else "fail")
        return self.add(key, status, message, sources, observed=actual, expected=expected)

    def limit(self, message: str) -> None:
        if message not in self.limitations:
            self.limitations.append(message)


def _interval(report: _Report, key: str, value: Any, *, fraction=False) -> bool:
    value = _mapping(value)
    vals = [value.get(k, _MISSING) for k in _BOUNDS]
    if any(v is _MISSING for v in vals):
        report.add(key, "unknown", "All low/point/high values are needed to check the interval.")
        return False
    valid = all(_number(v, minimum=0) for v in vals)
    valid = valid and vals[0] <= vals[1] <= vals[2]
    valid = valid and (not fraction or vals[2] <= 1)
    report.add(key, "pass" if valid else "fail", "Finite ordered bounds are required; recovery fractions must lie in [0, 1].", observed=value)
    return valid


def _recovery(report: _Report, audit: dict) -> None:
    scenario = _mapping(audit.get("scenario"))
    recovery = _mapping(audit.get("recovery"))
    eligibility = _mapping(audit.get("eligibility"))
    fractions = _mapping(scenario.get("recovery_fraction"))
    hours = _mapping(recovery.get("gpu_hours"))
    money = _mapping(recovery.get("reference_usd"))
    values = _mapping(money.get("values"))
    inputs_ok = _interval(report, "recovery.fractions", fractions, fraction=True)
    _interval(report, "recovery.hours_interval", hours)
    _interval(report, "recovery.money_interval", values)
    h, price = eligibility.get("eligible_gpu_hours", _MISSING), scenario.get("usd_per_gpu_hour", _MISSING)
    for key, value, valid in [
        ("eligible_hours", h, _number(h, minimum=0)),
        ("price", price, _number(price) and price > 0),
    ]:
        report.add("recovery." + key, "unknown" if value is _MISSING else ("pass" if valid else "fail"), "Recovery requires finite eligible hours and a positive GPU reference rate.", observed=value)
    if inputs_ok and _number(h, minimum=0) and _number(price) and price > 0:
        for bound in _BOUNDS:
            expected = h * fractions[bound]
            report.compare(f"recovery.gpu_hours.{bound}", hours.get(bound, _MISSING), expected, "Cohort hours use only the stated eligible allocation and recovery fraction.")
            report.compare(f"recovery.reference_usd.{bound}", values.get(bound, _MISSING), expected * price, "Reference dollars use the same cohort hours and GPU rate; no pilot subtraction.")
    else:
        report.add("recovery.arithmetic", "unknown", "Invalid or absent arithmetic inputs prevent recomputation.")
    for key, value, expected in [
        ("scenario_label", scenario.get("interval_kind", _MISSING), "scenario"),
        ("result_label", recovery.get("interval_kind", _MISSING), "scenario"),
        ("cancelled_policy", scenario.get("cancelled_policy", _MISSING), "exclude"),
        ("money_unit", money.get("unit", _MISSING), "reference_usd"),
        ("currency", money.get("currency", _MISSING), "USD"),
        ("cash_verified", money.get("cash_savings_verified", _MISSING), False),
        ("compatibility_verified", _mapping(audit.get("action")).get("compatibility_verified", _MISSING), False),
    ]:
        report.compare("recovery." + key, value, expected, "Scenario labels must not imply measured savings or verified CPU compatibility.")


def _evidence(report: _Report, audit: dict, details: list, coverage: dict) -> tuple[dict, bool, list[str]]:
    audit_id = audit.get("audit_id")
    provenance = _mapping(audit.get("provenance"))
    fingerprint = provenance.get("data_fingerprint")
    records, verified = {}, []
    seen_ids, physical_jobs = set(), set()
    duplicate_ids = set()
    synthetic_refs = []
    duplicate_jobs = []
    malformed = False
    preview = {r["id"]: r for r in audit.get("evidence_preview", [])
               if isinstance(r, dict) and isinstance(r.get("id"), str)}
    preview_complete = _integer(audit.get("evidence_count")) and len(preview) == audit["evidence_count"]
    for index, detail in enumerate(details):
        detail = _mapping(detail)
        ref = _mapping(detail.get("evidence"))
        eid = ref.get("id")
        key = str(eid) if isinstance(eid, str) and eid else f"missing-{index}"
        if not _CHECK_TOKEN.fullmatch(key):
            # Public evidence IDs are opaque; model selector check IDs are bounded
            # ASCII tokens. Keep the actual reference unchanged in source_ids.
            key = "ref-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        sources = [eid] if isinstance(eid, str) else []
        prov = _mapping(detail.get("provenance"))
        identity_ok = bool(eid and isinstance(eid, str) and audit_id and fingerprint)
        identity_ok = identity_ok and detail.get("audit_id") == audit_id and prov.get("data_fingerprint") == fingerprint
        identity_ok = identity_ok and eid not in seen_ids
        identity_ok = identity_ok and isinstance(ref.get("synthetic"), bool) and ref.get("synthetic") is prov.get("synthetic")
        kind = ref.get("kind")
        if ref.get("synthetic") is True and isinstance(eid, str):
            synthetic_refs.append(eid)
        identity_ok = identity_ok and kind in ("job", "gpu", "finding", "rule")
        if isinstance(eid, str) and eid in seen_ids:
            duplicate_ids.add(eid)
        if preview_complete:
            identity_ok = identity_ok and eid in preview
        if isinstance(eid, str) and eid in preview:
            expected_ref = preview[eid]
            identity_ok = identity_ok and all(ref.get(k) == expected_ref.get(k) for k in ("kind", "source_id", "synthetic"))
        if kind == "job":
            source = ref.get("source_id")
            joined = _mapping(detail.get("join_keys")).get("id_job")
            identity_ok = identity_ok and source is not None and bool(str(source)) and joined is not None and str(source) == str(joined)
            # A synthetic job must not become real accounting via an audit label.
            identity_ok = identity_ok and not (ref.get("synthetic") is True and provenance.get("synthetic") is not True)
            job_key = str(source)
            if job_key in physical_jobs:
                duplicate_jobs.append(job_key)
            physical_jobs.add(job_key)
        else:
            job_key = None
        if isinstance(eid, str):
            seen_ids.add(eid)
        report.add(f"evidence.identity:{key}", "pass" if identity_ok else "fail", "Evidence must retain scoped audit identity, fingerprint, unique reference ID, join key and synthetic provenance.", sources)
        observations, units_ok = {}, True
        raw_observations = detail.get("observations")
        if not isinstance(raw_observations, list):
            units_ok = False
            raw_observations = []
        for observation in raw_observations:
            observation = _mapping(observation)
            column = observation.get("column")
            if not isinstance(column, str) or not column or column in observations:
                units_ok = False
                continue
            value = observation.get("value", _MISSING)
            observations[column] = value
            if column in _UNITS:
                units_ok = units_ok and observation.get("unit", _MISSING) == _UNITS[column]
                if column != "state_name" and value is not None:
                    units_ok = units_ok and _number(value, minimum=0)
        report.add(f"evidence.units:{key}", "pass" if units_ok else "fail", "Known source columns must use their documented units and finite nonnegative measurements; duplicate columns are ambiguous.", sources)
        eligibility_status = "unknown"
        if kind == "job":
            required = ("state_name", "sm_util_avg", "sm_util_max", "gpu_hours")
            present = all(k in observations and observations[k] is not None for k in required)
            if present:
                qualifies = observations["state_name"] == "COMPLETED" and observations["sm_util_avg"] == 0 and observations["sm_util_max"] == 0
                qualifies = qualifies and _number(observations["gpu_hours"]) and observations["gpu_hours"] > 1
                eligibility_status = "pass" if qualifies and units_ok else "fail"
            report.add(f"evidence.eligibility:{key}", eligibility_status, "The broad CPU-review rule requires COMPLETED, average and peak SM zero, and recorded GPU-hours greater than one; memory use does not certify compatibility.", sources)
        record = {"detail": detail, "ref": ref, "values": observations, "identity_ok": identity_ok, "units_ok": units_ok, "eligibility": eligibility_status, "job_key": job_key}
        if isinstance(eid, str) and eid not in records:
            records[eid] = record
        if identity_ok and units_ok and eligibility_status != "fail":
            verified.append(eid)
        malformed = malformed or not identity_ok or not units_ok
    report.add("evidence.physical_job_uniqueness", "fail" if duplicate_jobs else "pass", "Multiple evidence IDs for one physical job must never inflate cohort hours.", observed=duplicate_jobs)
    if duplicate_jobs:
        verified = [eid for eid in verified if records[eid]["job_key"] not in duplicate_jobs]
    verified = [eid for eid in verified if eid not in duplicate_ids]
    for eid, record in records.items():
        if eid in duplicate_ids or record["job_key"] in duplicate_jobs:
            record["identity_ok"] = False
    if synthetic_refs:
        report.limit(f"{len(synthetic_refs)} fetched evidence records are explicitly synthetic; they do not establish real production incidents or measured operational outcomes. Examples: {', '.join(synthetic_refs[:5])}.")

    counts = [coverage.get(k, _MISSING) for k in ("listed_count", "fetched_count", "total")]
    consistent = all(_integer(v) for v in counts)
    consistent = consistent and counts[1] == len(details) and counts[1] <= counts[0] <= counts[2]
    report.add("evidence.coverage_counts", "pass" if consistent else "fail", "Coverage counts must describe the supplied details and pagination, not inferred cohort size.", observed=coverage)
    manifest_status = report.compare("evidence.manifest_count", coverage.get("total", _MISSING), audit.get("evidence_count", _MISSING), "Pagination totals must match the immutable audit's evidence manifest.")
    complete = consistent and coverage.get("complete") is True and coverage.get("truncated") is False
    complete = complete and manifest_status == "pass" and not coverage.get("reasons") and counts[0] == counts[1] == counts[2]
    report.add("evidence.coverage", "pass" if complete else "unknown", "Full-source verification requires complete, untruncated, internally consistent pagination.")
    if not complete:
        report.limit("Evidence coverage is incomplete; sampled records cannot verify exact cohort totals or memory partitions.")
    jobs = [r for r in records.values() if r["ref"].get("kind") == "job"]
    total_ready = complete and not malformed and not duplicate_jobs and all(r["eligibility"] == "pass" for r in jobs)
    eligibility = _mapping(audit.get("eligibility"))
    if total_ready:
        report.compare("cohort.unique_jobs", eligibility.get("unique_jobs", _MISSING), len(jobs), "Only distinct scoped job records are counted; findings and cards are not extra jobs.", [r["ref"]["id"] for r in jobs])
        report.compare("cohort.recorded_gpu_hours", eligibility.get("eligible_gpu_hours", _MISSING), _sum(r["values"]["gpu_hours"] for r in jobs), "Complete eligible job evidence independently reproduces recorded cohort hours.", [r["ref"]["id"] for r in jobs])
        total_ready = _same(eligibility.get("unique_jobs"), len(jobs))
    else:
        report.add("cohort.unique_jobs", "unknown", "Exact job count cannot be certified from missing, invalid, duplicate, or partially qualified evidence.")
        report.add("cohort.recorded_gpu_hours", "unknown", "Exact cohort hours are not checked against a sample or mixed physical grains.")
    report.limit("Verified evidence IDs mean scoped references and supplied observations were checked; they do not prove the underlying telemetry is accurate or CPU execution works.")
    return records, total_ready, sorted(set(verified))


def _memory(report: _Report, audit: dict, records: dict, complete: bool) -> None:
    eligibility = _mapping(audit.get("eligibility"))
    partition = eligibility.get("memory_partition")
    if not isinstance(partition, dict):
        report.add("memory.partition", "unknown", "This audit does not supply a memory partition.")
        return
    valid = all(
        isinstance(partition.get(group), dict)
        and _integer(partition[group].get("unique_jobs"))
        and _number(partition[group].get("recorded_gpu_hours"), minimum=0)
        for group in _MEMORY_GROUPS
    )
    report.add("memory.partition_shape", "pass" if valid else "fail", "Each disjoint memory group requires a nonnegative integer count and finite recorded hours.")
    if not valid:
        return
    report.compare("memory.partition_count", sum(partition[g]["unique_jobs"] for g in _MEMORY_GROUPS), eligibility.get("unique_jobs"), "Memory counts must reconcile to the broad cohort; this alone is internal consistency.")
    report.compare("memory.partition_hours", _sum(partition[g]["recorded_gpu_hours"] for g in _MEMORY_GROUPS), eligibility.get("eligible_gpu_hours"), "Memory hours must reconcile without folding unknown memory into zero.")
    if not complete:
        report.add("memory.partition_evidence", "unknown", "Partition membership requires complete, valid job evidence; a sample cannot verify the totals.")
        return
    groups = {name: [] for name in _MEMORY_GROUPS}
    for record in records.values():
        if record["ref"].get("kind") != "job":
            continue
        memory = record["values"].get("max_gpu_mem_used")
        group = "unknown_memory" if memory is None else ("zero_memory" if memory == 0 else "positive_memory")
        groups[group].append(record)
    for group, members in groups.items():
        refs = [r["ref"]["id"] for r in members]
        report.compare(f"memory.{group}.unique_jobs", partition[group]["unique_jobs"], len(members), "Memory membership is recomputed from scoped job observations, retaining unknowns.", refs)
        report.compare(f"memory.{group}.recorded_gpu_hours", partition[group]["recorded_gpu_hours"], _sum(r["values"]["gpu_hours"] for r in members), "Memory group hours use recorded job allocation once.", refs)


def _pilot(report: _Report, audit: dict, records: dict) -> None:
    scenario = _mapping(audit.get("scenario"))
    downside = _mapping(audit.get("downside"))
    request, result = scenario.get("cpu_pilot"), downside.get("cpu_pilot")
    if request is None and result is None:
        report.add("downside.availability", "unknown", "No quantified CPU pilot is supplied; qualitative v0.3 downside is not a failed calculation.")
        report.limit("CPU pilot cost and completion effects are unquantified in this audit.")
        return
    if not isinstance(request, dict) or not isinstance(result, dict):
        report.add("downside.availability", "fail", "A quantified pilot must have both its explicit inputs and result.")
        return
    report.compare("downside.contract_version", audit.get("contract_version", _MISSING), "0.4", "CPU pilot fields belong to proposed v0.4, not the closed active v0.3 payload.")
    report.compare("downside.status", downside.get("status", _MISSING), "scenario", "Quantified pilot outcomes are hypothetical scenarios.")
    for field in ("money", "money_unit"):
        report.compare("downside.legacy_" + field, downside.get(field, _MISSING), None, "Legacy downside money stays null; single-job signed metrics have separate meanings.")
    for field, expected in {
        "scope": "single_job", "evidence_kind": "scenario_estimate",
        "compatibility_verified": False, "cash_savings_verified": False,
        "trial_stop_enforcement_tested": False,
    }.items():
        report.compare("downside." + field, result.get(field, _MISSING), expected, "Pilot arithmetic cannot become cohort savings, an observed outcome, or verified enforcement.")
    mode = request.get("mode")
    report.compare("downside.mode", result.get("mode", _MISSING), mode, "Result mode must match the frozen request.")
    required = ("mode", "baseline_evidence_id", "cpu_vcpus", "cpu_hours", "cpu_vcpu_hour_usd", "extra_queue_hours", "trial_cap_hours", "baseline_host_costs_included", "assumption_note")
    v, c = request.get("cpu_vcpus"), request.get("cpu_hours")
    pc, q, cap = (request.get(k) for k in ("cpu_vcpu_hour_usd", "extra_queue_hours", "trial_cap_hours"))
    pg = scenario.get("usd_per_gpu_hour")
    valid = all(k in request for k in required)
    valid = valid and mode in ("replacement_success", "replacement_failure", "additional_validation")
    valid = valid and _integer(v, 1) and _number(c, minimum=0) and (mode != "replacement_success" or c > 0)
    valid = valid and all(x is None or _number(x, minimum=0) for x in (pc, q, cap))
    valid = valid and (cap is None or c <= cap) and _number(pg) and pg > 0
    valid = valid and isinstance(request.get("baseline_host_costs_included"), bool)
    valid = valid and isinstance(request.get("assumption_note"), str) and bool(request["assumption_note"].strip())
    report.add("downside.inputs", "pass" if valid else "fail", "Validate finite explicit CPU assumptions, nonnegative extra wait, positive vCPUs, successful runtime and any trial cap; a cap is not watchdog enforcement.")
    eid = request.get("baseline_evidence_id")
    record = records.get(eid) if isinstance(eid, str) else None
    baseline = _mapping(result.get("baseline"))
    report.compare("downside.baseline_evidence_id", baseline.get("evidence_id", _MISSING), eid, "The scenario baseline must be the requested scoped evidence reference.", [eid] if eid else [])
    if not record:
        report.add("downside.baseline_source", "unknown", "Baseline source was not fetched; output measurements cannot corroborate themselves.", [eid] if eid else [])
        return
    ready = record["identity_ok"] and record["units_ok"] and record["eligibility"] == "pass" and record["ref"].get("kind") == "job"
    obs = record["values"]
    memory = obs.get("max_gpu_mem_used", _MISSING)
    report.add("downside.baseline_memory", "unknown" if memory is _MISSING or memory is None else ("pass" if _number(memory, minimum=0) else "fail"), "Baseline maximum GPU memory and missingness must remain visible; zero compute or memory does not establish CPU compatibility.", [eid])
    g, seconds, h = (obs.get(k) for k in ("gpu_count", "walltime_sec", "gpu_hours"))
    ready = ready and _number(g) and g > 0 and float(g).is_integer() and _number(seconds) and seconds > 0 and _number(h) and h > 0
    if not ready:
        report.add("downside.baseline_source", "unknown", "Complete eligible source measurements with correct units and identity are required for independent pilot recomputation.", [eid])
        return
    t = seconds / 3600
    report.add("downside.baseline_source", "pass", "One scoped eligible job supplies recorded GPU-hours and scheduler elapsed time separately.", [eid])
    for field, expected in (("gpu_count", g), ("elapsed_hours", t), ("recorded_gpu_hours", h)):
        report.compare("downside.baseline." + field, baseline.get(field, _MISSING), expected, "The output baseline must match source observations, not edited client inputs.", [eid])
    note = baseline.get("accounting_note")
    report.add("downside.accounting_note", "pass" if isinstance(note, str) and bool(note.strip()) else "fail", "State the recorded-allocation versus scheduler-duration accounting, including any discrepancy.", [eid], observed={"recorded_gpu_hours": h, "gpu_count_times_elapsed": g * t})
    if not _same(h, g * t):
        report.add("downside.allocation_discrepancy", "pass", f"Recorded allocation is {h} GPU-hours; GPU count times elapsed time is {g * t} GPU-hours. The scenario must use the recorded allocation.", [eid])
    if not valid:
        report.add("downside.arithmetic", "unknown", "Invalid scenario inputs prevent independent arithmetic verification.", [eid])
        return
    released = h if mode == "replacement_success" else 0
    cpu = v * c
    cpu_cost = None if pc is None else cpu * pc
    runtime = c - t if mode == "replacement_success" else c if mode == "replacement_failure" else None
    expected = {
        "scenario_gpu_hours": h - released,
        "released_gpu_hours": released,
        "added_cpu_vcpu_hours": cpu,
        "released_gpu_reference_usd": released * pg,
        "added_cpu_reference_usd": cpu_cost,
        "net_reference_value_usd": None if cpu_cost is None or request["baseline_host_costs_included"] is not True else released * pg - cpu_cost,
        "run_time_change_hours_excluding_queue": runtime,
        "completion_change_hours_including_extra_queue": None if runtime is None or q is None else runtime + q,
    }
    for field, value in expected.items():
        report.compare("downside." + field, result.get(field, _MISSING), value, "Independent single-job scenario arithmetic preserves recorded H, incremental failure cost, unknowns, and signed results.", [eid])
    report.limit("CPU runtime, pricing boundary and extra wait are assumptions; passing arithmetic does not validate CPU compatibility, cash savings, or rollback enforcement.")
    report.limit("The single-job CPU pilot is separate from cohort recovery and must not be added to or subtracted from exported cohort claims.")


def validate_audit(audit: dict, evidence: list[dict], coverage: dict, mcp_context: dict | None = None) -> dict:
    """Return explicit pass/fail/unknown checks without changing any input.

    ``coverage`` describes all supplied EvidenceDetail objects, including non-job
    references. ``mcp_context`` may supply a top-level ``data_fingerprint`` or a
    ``provenance.data_fingerprint``. Without it, tool-source alignment is unknown.
    Schema validation and live source trust are separate caller responsibilities.
    """
    report = _Report()
    audit = _mapping(audit)
    details = evidence if isinstance(evidence, list) else []
    coverage = _mapping(coverage)
    provenance = _mapping(audit.get("provenance"))
    audit_id, fingerprint = audit.get("audit_id"), provenance.get("data_fingerprint")
    report.add("audit.identity", "pass" if isinstance(audit_id, str) and bool(audit_id) and isinstance(fingerprint, str) and bool(fingerprint) else "fail", "Audit and data identities are required before checking scoped evidence.")
    _recovery(report, audit)
    records, complete, verified = _evidence(report, audit, details, coverage)
    _memory(report, audit, records, complete)
    _pilot(report, audit, records)
    mcp = _mapping(mcp_context)
    mcp_fingerprint = mcp.get("data_fingerprint", _mapping(mcp.get("provenance")).get("data_fingerprint", _MISSING))
    if mcp_fingerprint is _MISSING:
        report.add("mcp.source_identity", "unknown", "No MCP source fingerprint was supplied; tool corroboration is not assumed.")
    else:
        report.compare("mcp.source_identity", mcp_fingerprint, fingerprint, "MCP evidence must refer to the same source snapshot before corroborating the audit.")
    report.limit("Checks validate supplied accounting and evidence consistency, not hidden source truth, a failure probability, or operational outcomes.")
    return {
        "audit_id": audit_id,
        "data_fingerprint": fingerprint,
        "checks": report.checks,
        "coverage": _safe(copy.deepcopy(coverage)),
        "assumptions": _safe(copy.deepcopy(_mapping(audit.get("scenario")))),
        "suggested_next_steps": [
            "Resolve failed or unknown checks with the audit owner; keep canonical claims unchanged.",
            "Before a CPU pilot, verify GPU dependencies, output correctness, peak memory and completion time on matching inputs.",
            "Agree on stop limits and test checkpoint restoration and return to the original GPU configuration.",
        ],
        "limitations": report.limitations,
        "verified_evidence_ids": verified,
    }
