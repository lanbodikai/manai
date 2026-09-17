"""Render source quotations and separately labelled independent checks.

Model text never enters the answer: a model may select existing fact/check IDs
and a bounded vocabulary of proposed verification steps only.
"""
import json

CONCERNS = {
    "gpu_dependency": "Before changing allocation, check CUDA/device dependencies and whether the workload requires multiple GPUs.",
    "correctness": "Run the original and proposed configuration on the same inputs; compare outputs against an owner-approved tolerance.",
    "memory": "Measure peak memory and out-of-memory failures during the pilot; low compute does not establish low memory demand.",
    "runtime": "Measure completion time and throughput against an agreed deadline; telemetry does not establish CPU performance.",
    "recovery": "Before a pilot, save a checkpoint, test restoration, set stop limits and retain the original GPU configuration for rollback.",
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
        add("pilot_downside", "A's single-job CPU pilot scenario (not a cohort total or measured workload test)", pilot, "as labelled in source", "scenario_estimate")
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
    lines.append("Independent checks (PASS verifies only the named check; UNKNOWN means insufficient evidence):")
    # Failures and unknowns cannot be hidden by the model's selection.
    selected_checks = set(selection["selected_check_ids"]) if selection is not None else {c["id"] for c in report["checks"]}
    for check in report["checks"]:
        if check["id"] in selected_checks or check["status"] != "pass":
            lines.append(f"- {check['id']}: {check['status'].upper()} — {check['message']}")
            if check["status"] == "fail":
                for key in ("observed", "expected"):
                    if key in check:
                        label = "A/source reported" if key == "observed" else "C independently expected"
                        lines.append(f"  {label}: {json.dumps(check[key], sort_keys=True, allow_nan=False)}")
    lines.append("Evidence coverage: " + json.dumps(report["coverage"], sort_keys=True) + ".")
    lines.extend("Limitation: " + item for item in report["limitations"])
    concerns = selection["concern_codes"] if selection is not None else ["gpu_dependency", "correctness", "memory", "runtime", "recovery"]
    lines.append("Proposed verification, not completed tests:")
    lines.extend("- " + CONCERNS[c] for c in dict.fromkeys(concerns))
    lines.append("No workload was moved. No compatibility, rollback success, cash saving or causal blame has been verified. A's audit and claims remain unchanged.")
    return "\n".join(lines)
