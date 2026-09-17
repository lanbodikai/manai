"""Render source quotations and separately labelled independent checks.

Model text never enters the answer: a model may select existing fact/check IDs
and a bounded vocabulary of proposed verification steps only.
"""
import json
from collections import defaultdict

CONCERNS = {
    "gpu_dependency": "Before changing allocation, check CUDA/device dependencies and whether the workload requires multiple GPUs.",
    "correctness": "Run the original and proposed configuration on the same inputs; compare outputs against an owner-approved tolerance.",
    "memory": "Measure peak memory and out-of-memory failures during the pilot; low compute does not establish low memory demand.",
    "runtime": "Measure completion time and throughput against an agreed deadline; telemetry does not establish CPU performance.",
    "recovery": "Proposed response: stop on incorrect output, crash, or owner-set runtime/spend limits. Retain the original GPU settings; assume a full rerun unless checkpoint restoration is tested. If GPU capacity or recovery is unavailable, pause for owner action. Preserve logs and diagnose before retrying.",
    "unsupported_causality": "This review cannot establish hardware blame, workload compatibility or operational safety from utilization alone.",
    "insufficient_coverage": "Request the missing cohort evidence before treating a sampled review as validation of the whole total.",
    "synthetic_context": "Synthetic detector/context records demonstrate the method; they do not establish a real production incident.",
}


def build_facts(audit, report):
    refs = report.get("verified_evidence_ids", [])
    facts = []
    def add(fid, label, value, unit, kind):
        facts.append(dict(id=fid, label=label, value=value, unit=unit,
                          kind=kind, source="A immutable audit", source_ids=refs))
    add("eligible_hours", "A's eligible cohort", audit["eligibility"]["eligible_gpu_hours"], "GPU-hours", "reported_observation")
    add("eligible_jobs", "A's unique jobs", audit["eligibility"]["unique_jobs"], "jobs", "reported_observation")
    add("recovery_fraction", "Assumed recovery fraction", audit["scenario"]["recovery_fraction"], "fraction", "scenario_assumption")
    add("gpu_price", "Assumed GPU reference price", audit["scenario"]["usd_per_gpu_hour"], "USD/GPU-hour", "scenario_assumption")
    add("recovery_hours", "A's scenario recovery range", audit["recovery"]["gpu_hours"], "GPU-hours", "scenario_estimate")
    add("recovery_value", "A's reference value (not cash savings)", audit["recovery"]["reference_usd"], "USD", "scenario_estimate")
    pilot = audit.get("downside", {}).get("cpu_pilot")
    if pilot is not None:
        for fid, label, field, unit in (
            ("pilot_mode", "Single-job pilot outcome", "mode", "outcome"),
            ("pilot_cpu_cost", "Added CPU reference cost", "added_cpu_reference_usd", "USD"),
            ("pilot_net_value", "Net reference benefit or loss", "net_reference_value_usd", "USD"),
            ("pilot_delay", "Completion change including extra queue", "completion_change_hours_including_extra_queue", "hours"),
        ):
            add(fid, label, pilot[field], unit, "scenario_estimate")
    return facts


def render_answer(audit, report, facts, selection=None):
    lines = ["Optional evidence validation — " + ("model-selected review; fixed source-grounded rendering." if selection is not None else "deterministic checks; no model was used.")]
    lines.append("Source audit: " + audit["audit_id"] + "; fingerprint: " + audit["provenance"]["data_fingerprint"] + ".")
    lines.append("Source provenance: " + ("SYNTHETIC TEST AUDIT; not real telemetry." if audit["provenance"]["synthetic"] else "Audit marked non-synthetic; individual evidence may be synthetic.") + " Sample: " + audit["provenance"]["sample_label"])
    lines.append("Validation covers only the fetched evidence and the named checks. It is not a full-source or workload-execution certification.")
    selected = set(selection["selected_fact_ids"]) if selection is not None else {f["id"] for f in facts}
    lines.append("Reported by A (quoted values, not independently certified totals):")
    for fact in facts:
        if fact["id"] in selected:
            lines.append(f"- {fact['label']}: {json.dumps(fact['value'], sort_keys=True, allow_nan=False)} {fact['unit']} [{fact['kind']}].")
    counts = {status: sum(c["status"] == status for c in report["checks"]) for status in ("pass", "fail", "unknown")}
    lines.append(f"Independent checks: {counts['pass']} PASS, {counts['fail']} FAIL, {counts['unknown']} UNKNOWN. PASS verifies only its named check.")
    selected_checks = set(selection["selected_check_ids"]) if selection is not None else set()
    groups = defaultdict(list)
    for check in report["checks"]:
        if check["status"] != "pass" or check["id"] in selected_checks:
            # Per-record checks share a category; no failed/unknown category is
            # dropped. Individual checks remain in the private validation report.
            groups[(check["id"].split(":", 1)[0], check["status"])].append(check)
    for (category, status), items in sorted(groups.items(), key=lambda item: ({"fail": 0, "unknown": 1, "pass": 2}[item[0][1]], item[0][0])):
        first = items[0]
        suffix = f" ({len(items)} checks; representative details below)" if len(items) > 1 else ""
        lines.append(f"- {category}: {status.upper()} — {first['message']}{suffix}")
        if status == "fail":
            for key in ("observed", "expected"):
                if key in first:
                    label = "A/source reported" if key == "observed" else "C independently expected"
                    lines.append(f"  {label}: {json.dumps(first[key], sort_keys=True, allow_nan=False)}")
        sources = list(dict.fromkeys(eid for check in items for eid in check.get("source_ids", [])))
        if sources:
            lines.append("  Evidence examples: " + ", ".join(sources[:3]) + (" (additional records grouped)" if len(sources) > 3 else ""))
    cover = report["coverage"]
    lines.append(f"Evidence coverage: {cover['fetched_count']} fetched of {cover['total']} audit references; {cover['listed_count']} listed through pagination; {cover.get('targeted_count', 0)} selected baseline outside those pages. " + ("Complete pagination." if cover.get("complete") else "Partial review; whole-cohort totals are not certified."))
    if audit.get("downside", {}).get("cpu_pilot") is not None:
        lines.append("Single-job pilot estimates are separate from cohort recovery. Null cost or delay means unknown, not zero. A failed trial retains the original GPU run and adds trial cost; additional validation releases no GPU allocation.")
        for limit in audit["downside"]["cpu_pilot"].get("limitations", []):
            lines.append("Pilot limitation: " + limit)
    lines.extend("Limitation: " + item for item in report["limitations"])
    concerns = selection["concern_codes"] if selection is not None else ["gpu_dependency", "correctness", "memory", "runtime", "recovery"]
    lines.append("Proposed verification, not completed tests:")
    lines.extend("- " + CONCERNS[c] for c in dict.fromkeys(concerns))
    lines.append("No workload was moved. No compatibility, rollback success, cash saving or causal blame has been verified. A's audit and claims remain unchanged.")
    return "\n".join(lines)
