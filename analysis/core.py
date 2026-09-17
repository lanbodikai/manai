"""Pure cohort, overlap, scenario and evidence calculations."""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

import pandas as pd
from analysis.cpu_pilot import assess_cpu_pilot, memory_partition

RULE = "rules::gpu-not-needed"
DEFINITION = "COMPLETED; sm_util_avg == 0; sm_util_max == 0; gpu_hours > 1; required values present and valid"
UPSTREAM = "314cca0bba49e1bb137aa9094d1dac4cdf7e4490"
LIMITATIONS = [
    "Historical zero SM activity does not prove CPU compatibility or absence of useful work.",
    "Recovery fractions are assumptions, not calibrated probabilities or measured savings.",
    "Reference dollars are not cash savings; CPU, migration and business-delay costs are not included.",
    "This four-month job sample is not the whole fleet. Cancelled jobs are excluded.",
    "The organizer rec_lowutil recommendation has a different cohort and action; this is not its corrected estimate.",
]


def finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def native(value):
    if hasattr(value, "item"):
        value = value.item()
    return None if value is None or (isinstance(value, float) and not math.isfinite(value)) else value


@dataclass
class Cohort:
    jobs: list
    excluded: dict
    total_jobs: int

    @property
    def hours(self):
        return math.fsum(float(j["gpu_hours"]) for j in self.jobs)


def load_tables(data_dir):
    data = Path(data_dir)
    jobs = pd.read_parquet(data / "prepped/jobs.parquet")
    required = {"id_job", "state_name", "sm_util_avg", "sm_util_max", "gpu_hours"}
    if not required <= set(jobs.columns):
        raise ValueError("Required cohort columns missing")
    findings = json.loads((data / "synthetic/findings.json").read_text())
    if not isinstance(findings, list) or any(not isinstance(f, dict) for f in findings):
        raise ValueError("Invalid findings source")
    ids = [f["id"] for f in findings]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate finding identity")
    return jobs, findings


def select_cohort(jobs):
    rows = jobs.to_dict("records") if isinstance(jobs, pd.DataFrame) else jobs
    unique = {}
    for raw in rows:
        row = {k: native(v) for k, v in raw.items() if k in {
            "id_job", "state_name", "sm_util_avg", "sm_util_max", "gpu_hours",
            "gpu_count", "walltime_sec", "max_gpu_mem_used"}}
        key = row.get("id_job")
        if key is None:
            raise ValueError("Missing job identity")
        if key in unique and unique[key] != row:
            raise ValueError("Inconsistent duplicate job identity")
        unique[key] = row
    selected, excluded = [], Counter()
    for row in sorted(unique.values(), key=lambda x: str(x["id_job"])):
        avg, peak, hours = (row.get(k) for k in ("sm_util_avg", "sm_util_max", "gpu_hours"))
        if row.get("state_name") is None or any(v is None for v in (avg, peak, hours)):
            reason = "missing required measurement"
        elif not all(finite(v) for v in (avg, peak, hours)) or not 0 <= avg <= peak <= 100 or hours < 0:
            reason = "invalid required measurement"
        elif row.get("walltime_sec") is not None and (not finite(row["walltime_sec"]) or row["walltime_sec"] < 0):
            reason = "invalid scheduler duration"
        elif row["state_name"] != "COMPLETED":
            reason = "not completed (including cancelled)"
        elif avg != 0 or peak != 0:
            reason = "nonzero SM activity"
        elif hours <= 1:
            reason = "recorded GPU-hours not greater than one"
        else:
            selected.append(row)
            continue
        excluded[reason] += 1
    return Cohort(selected, dict(sorted(excluded.items())), len(unique))


def audit_impacts(cohort, findings):
    eligible = {str(j["id_job"]): j for j in cohort.jobs}
    refs, excluded, included = [], Counter(), []
    for finding in findings:
        md = finding.get("metadata", {})
        job = str(md.get("job_id"))
        if job not in eligible:
            continue
        if md.get("impact_scope") != "job":
            excluded["non-job scope"] += 1
        elif md.get("impact_kind") != "unused_capacity":
            excluded["different impact kind"] += 1
        else:
            refs.append(job)
            included.append(finding)
    # Repeat each source-linked physical allocation only to expose overlap.
    naive = math.fsum(eligible[k]["gpu_hours"] for k in refs)
    deduplicated = math.fsum(eligible[k]["gpu_hours"] for k in sorted(set(refs)))
    return {"overlapping_finding_references": len(refs) - len(set(refs)),
            "naive_linked_allocation_gpu_hours": naive,
            "deduplicated_linked_allocation_gpu_hours": deduplicated,
            "excluded_impacts": dict(sorted(excluded.items())), "findings": included}


def estimate_recovery(cohort, scenario):
    fractions = scenario["recovery_fraction"]
    values = [fractions[k] for k in ("low", "point", "high")]
    price = scenario["usd_per_gpu_hour"]
    if not all(finite(v) for v in values) or not 0 <= values[0] <= values[1] <= values[2] <= 1:
        raise ValueError("Recovery fractions must be finite, ordered and within [0,1]")
    if not finite(price) or price <= 0 or scenario["cancelled_policy"] != "exclude":
        raise ValueError("Invalid price or cancellation policy")
    hours = {k: cohort.hours * fractions[k] for k in ("low", "point", "high")}
    money = {k: hours[k] * price for k in hours}
    if not all(math.isfinite(v) for v in [*hours.values(), *money.values()]):
        raise ValueError("Scenario arithmetic overflow")
    basis = (f"{cohort.hours:.17g} recorded eligible GPU-hours multiplied by explicit fractions "
             f"{values[0]:.17g}/{values[1]:.17g}/{values[2]:.17g}. " + scenario["assumption_note"])
    return {"gpu_hours": hours, "reference_usd": {"currency": "USD", "unit": "reference_usd",
            "values": money, "cash_savings_verified": False}, "interval_kind": "scenario", "basis": basis}


def assess_downside(cohort, scenario):
    result = {"status": "unmeasured", "money": None, "money_unit": None, "cpu_pilot": None,
        "mechanisms": ["CPU execution could fail or run more slowly.",
                       "CPU queue pressure, retries and rollback could delay useful work."],
        "assumptions": ["Zero historical SM activity establishes rule eligibility only.",
                        "CPU compatibility, runtime and available CPU capacity remain unknown.",
                        "Recovery assumption: " + scenario["assumption_note"]],
        "guardrails": ["Obtain workload-owner opt-in for a small pilot; retain original GPU placement.",
                       "Compare output validity, task success and runtime to the original placement.",
                       "Stop and roll back on task failure or owner-agreed runtime/queue limits; set limits before the pilot.",
                       "Rollback and automatic stop enforcement have not been tested."],
        "pilot_success_metrics": ["Task completion and output validity", "Runtime relative to original placement",
                                  "Queue delay", "Actual GPU allocation avoided"]}
    return result


def evidence_id(fingerprint, kind, source_id):
    return hashlib.sha256(f"{fingerprint}|{kind}|{source_id}".encode()).hexdigest()[:32]


def make_evidence(cohort, impacts, findings, rule, provenance):
    details = {}
    def add(kind, source_id, label, table, observations, joins, method, synthetic=False, caveats=()):
        eid = evidence_id(provenance["data_fingerprint"], kind, str(source_id))
        ref = {"id": eid, "kind": kind, "source_id": str(source_id), "label": label, "synthetic": synthetic}
        p = {**provenance, "synthetic": synthetic, "caveats": [*provenance["caveats"], *caveats]}
        details[eid] = {"evidence": ref, "source_table": table,
            "source_columns": [o["column"] for o in observations if o["column"] is not None],
            "join_keys": joins, "observations": observations, "method": method,
            "caveats": list(caveats), "provenance": p}
    def obs(name, value, unit=None, column=None):
        return {"name": name, "value": native(value), "unit": unit, "column": column}
    units = {"gpu_hours": "GPU-hours", "sm_util_avg": "percent", "sm_util_max": "percent",
             "gpu_count": "GPUs", "walltime_sec": "seconds", "max_gpu_mem_used": "bytes"}
    for job in cohort.jobs:
        add("job", job["id_job"], "Eligible completed job " + str(job["id_job"]), "prepped/jobs.parquet",
            [obs(k, job.get(k), units.get(k), k) for k in
             ("state_name", "sm_util_avg", "sm_util_max", "gpu_hours", "gpu_count", "walltime_sec", "max_gpu_mem_used")],
            {"id_job": job["id_job"]}, DEFINITION, provenance["synthetic"],
            ["Recorded allocation and scheduler duration are distinct; missing observations remain null.",
             "CPU compatibility is unproven."])
    eligible = {str(j["id_job"]) for j in cohort.jobs}
    for f in sorted(findings, key=lambda x: x["id"]):
        md = f.get("metadata", {})
        if str(md.get("job_id")) not in eligible:
            continue
        simulated = provenance["synthetic"] or bool(md.get("synthetic")) or "filesystem-latency" in f["detectorId"]
        add("finding", f["id"], "Organizer rule finding: " + f["detectorId"], "synthetic/findings.json",
            [obs("detector", f["detectorId"], column="detectorId"),
             *[obs(k, md.get(k), "GPU-hours" if k == "impact_gpu_hours" else None, "metadata." + k)
               for k in ("impact_scope", "impact_kind", "impact_gpu_hours")]],
            {"job_id": md.get("job_id")}, "Join by metadata.job_id, never prose; organizer rule output, not intervention proof.",
            simulated, ["Generated rule findings are distinct from raw telemetry; synthetic incidents remain labeled."])
    add("rule", RULE, "Completed zero-compute eligibility rule", "official /v1/policies/rules",
        [obs("rule_id", RULE, column="rule_id"), obs("summary", rule["summary"], column="summary")],
        {"rule_id": RULE}, "Pinned organizer rule catalogue; CPU-placement remedy already exists upstream.", provenance["synthetic"])
    add("aggregate", "accounting", "Deterministic evidence summary and overlap accounting", "prepped/jobs.parquet + findings.json",
        [obs("eligible_gpu_hours", cohort.hours, "GPU-hours"), obs("eligible_jobs", len(cohort.jobs), "jobs"),
         *[obs(k, impacts[k], "GPU-hours" if "hours" in k else "references") for k in
           ("naive_linked_allocation_gpu_hours", "deduplicated_linked_allocation_gpu_hours", "overlapping_finding_references")],
         obs("selection_exclusions", json.dumps(cohort.excluded, sort_keys=True)),
         obs("impact_exclusions", json.dumps(impacts["excluded_impacts"], sort_keys=True))], {},
        "Sum recorded GPU-hours once per unique eligible job. Linked-allocation overlap totals are diagnostics, not additional recovery.",
        provenance["synthetic"], LIMITATIONS)
    return details


def build_audit(audit_id, request, cohort, impacts, evidence, provenance):
    refs = sorted((d["evidence"] for d in evidence.values()), key=lambda r: (r["kind"], r["source_id"]))
    downside = assess_downside(cohort, request["scenario"])
    pilot = request["scenario"].get("cpu_pilot")
    if pilot is not None:
        eid = pilot["baseline_evidence_id"]
        detail = evidence.get(eid)
        if detail is None or detail["evidence"]["kind"] != "job":
            raise KeyError("CPU baseline is not an eligible job in this audit")
        if detail["provenance"]["data_fingerprint"] != provenance["data_fingerprint"]:
            raise RuntimeError("CPU baseline fingerprint differs")
        job = next((j for j in cohort.jobs if str(j["id_job"]) == detail["evidence"]["source_id"]), None)
        if job is None:
            raise KeyError("CPU baseline is not eligible")
        downside["cpu_pilot"] = assess_cpu_pilot(job, pilot, request["scenario"]["usd_per_gpu_hour"])
        downside["status"] = "scenario"
        downside["assumptions"].append("Single-job cost/delay is a hypothetical scenario, separate from cohort recovery. " + pilot["assumption_note"])
    return {"contract_version": "0.4", "audit_id": audit_id, "client_request_id": request["client_request_id"],
        "recommendation_id": "cpu-placement-pilot", "source_recommendation_ids": [], "provenance": provenance,
        "scenario": request["scenario"], "eligibility": {"definition": DEFINITION, "unique_jobs": len(cohort.jobs),
        "eligible_gpu_hours": cohort.hours, "excluded_jobs": sum(cohort.excluded.values()),
        "overlapping_finding_references": impacts["overlapping_finding_references"],
        "coverage_note": f"{cohort.total_jobs} unique source jobs; exclusions: {json.dumps(cohort.excluded, sort_keys=True)}",
        "memory_partition": memory_partition(cohort)},
        "recovery": estimate_recovery(cohort, request["scenario"]),
        "action": {"title": "Pilot CPU placement for eligible workloads", "owner_role": "Platform/SRE with workload owner",
                   "state": "proposed_pilot", "compatibility_verified": False},
        "downside": downside, "evidence_preview": refs[:5],
        "evidence_count": len(refs), "limitations": LIMITATIONS + ([] if cohort.jobs else ["No eligible jobs."])}


def export_claims(audit, team):
    r = audit["recovery"]
    return {"team": team, "recoverable_gpu_hours": {**r["gpu_hours"], "basis": r["basis"], "interval_kind": "scenario"},
        "recoverable_usd": {**r["reference_usd"]["values"], "interval_kind": "scenario",
            "basis": f"Same recovery bounds at {audit['scenario']['usd_per_gpu_hour']:.17g} reference USD/GPU-hour; not cash savings."},
        "cancelled_is_waste": False, "cancelled_rationale": "Cancelled jobs are outside the completed-job cohort.",
        "notes": f"Audit {audit['audit_id']}; data {audit['provenance']['data_fingerprint']}; "
                 + ("SYNTHETIC TEST ONLY. " if audit["provenance"]["synthetic"] else "") + " ".join(audit["limitations"])}
