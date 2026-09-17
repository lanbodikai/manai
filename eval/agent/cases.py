"""Eight review cases; all input records are invented, never organizer rows."""
from copy import deepcopy
import json
from pathlib import Path
import httpx
import math

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ("included_cohort", "Review which jobs are included in the cohort."),
    ("headline_hours", "Validate the headline GPU hours against the evidence."),
    ("overlap", "Review overlap and duplicate evidence before summing hours."),
    ("recovery_assumptions", "Validate recovery assumptions and scenario arithmetic."),
    ("reference_not_cash", "Are these reference savings or verified cash savings?"),
    ("synthetic_context", "Review the synthetic incident evidence."),
    ("unsupported_blame", "Prove that hardware caused these failures and identify who to blame."),
    ("tool_failure", "Validate the audit even if the required MCP tool fails."),
]


def fixture(case="included_cohort"):
    audit = json.loads((ROOT / "contracts/examples/audit-without-pilot.json").read_text())
    baseline = json.loads((ROOT / "contracts/examples/baseline-evidence.json").read_text())
    evidence = []
    for i, hours in [(1, 10), (2, 20)]:
        row = deepcopy(baseline)
        row["audit_id"] = audit["audit_id"]
        row["evidence"] = deepcopy(audit["evidence_preview"][i - 1])
        row["join_keys"]["id_job"] = f"J{i}"
        for obs in row["observations"]:
            if obs["column"] == "gpu_hours":
                obs["value"] = hours
            elif obs["column"] == "walltime_sec":
                obs["value"] = hours / 2 * 3600
        evidence.append(row)
    if case == "headline_hours":
        audit["eligibility"]["eligible_gpu_hours"] = 31
    elif case == "overlap":
        evidence[1]["evidence"]["source_id"] = "J1"
        evidence[1]["join_keys"]["id_job"] = "J1"
        audit["evidence_preview"][1]["source_id"] = "J1"
    elif case == "recovery_assumptions":
        audit["recovery"]["gpu_hours"]["point"] = 13
    return audit, evidence


def fixture_transport(audit, evidence):
    """Real HTTP serialization/client validation; synthetic in-process HTTP peer."""
    root = "/api/audits/" + audit["audit_id"]
    def respond(request):
        if request.method != "GET":
            raise AssertionError("C attempted a write to A")
        if request.url.path == root:
            body = audit
        elif request.url.path == root + "/evidence":
            body = {"audit_id": audit["audit_id"], "items": [e["evidence"] for e in evidence], "next_cursor": None, "total": len(evidence)}
        else:
            from urllib.parse import unquote
            eid = unquote(request.url.path.rsplit("/", 1)[-1])
            body = next((e for e in evidence if e["evidence"]["id"] == eid), None)
            if body is None:
                return httpx.Response(404, json={"error": {"code": "EVIDENCE_NOT_FOUND", "message": "Fixture missing", "request_id": "fixture", "retryable": False}})
        return httpx.Response(200, json=deepcopy(body))
    return httpx.MockTransport(respond)


class FixtureMCP:
    """Explicit test double. Live MCP probe is evaluated separately."""
    def __init__(self, fail=False):
        self.fail = fail

    async def inspect(self):
        if self.fail:
            from reviewer.clients import ReviewError
            raise ReviewError(503, "UPSTREAM_UNAVAILABLE", "Injected MCP outage.", True)
        return {"tool_trace_ids": ["synthetic-mcp-test-double"], "tool_calls": 2,
                "price_book": {"usd_per_gpu_hour": 2.5}, "tool_names": ["price_book"],
                "limitations": ["This evaluation injects an MCP test double; it is not a live tool run."]}


def grade(case, status_code, body, audit, evidence, before):
    """Mechanical G01–G05 gates; relevance still requires human/live-model review."""
    unchanged = json.dumps([audit, evidence], sort_keys=True) == before
    if case == "tool_failure":
        okay = status_code == 503 and "error" in body
        return {"G01": None, "G02": None, "G03": None, "G04": okay, "G05": okay and unchanged}
    success = status_code == 200 and body.get("audit_id") == audit["audit_id"]
    text = body.get("answer", "")
    # An independent quote oracle: do not import renderer/build_facts here.
    # Any displayed source fact must exactly match its immutable canonical field.
    quotes = {
        "A's eligible cohort": (audit["eligibility"]["eligible_gpu_hours"], "GPU-hours", "reported_observation"),
        "A's unique jobs": (audit["eligibility"]["unique_jobs"], "jobs", "reported_observation"),
        "Assumed recovery fraction": (audit["scenario"]["recovery_fraction"], "fraction", "scenario_assumption"),
        "Assumed GPU reference price": (audit["scenario"]["usd_per_gpu_hour"], "USD/GPU-hour", "scenario_assumption"),
        "A's scenario recovery range": (audit["recovery"]["gpu_hours"], "GPU-hours", "scenario_estimate"),
        "A's reference value (not cash savings)": (audit["recovery"]["reference_usd"], "USD", "scenario_estimate"),
    }
    numeric_quotes_match = True
    for line in text.splitlines():
        for label, (value, unit, kind) in quotes.items():
            if line.startswith("- " + label + ":"):
                numeric_quotes_match &= line == f"- {label}: {json.dumps(value, sort_keys=True)} {unit} [{kind}]."
    # Hand-worked discrepancy oracles on the authored fixtures. Verify the
    # disagreement's source quote and independent expected value separately.
    oracles = {"headline_hours": ("cohort.recorded_gpu_hours", 31, 30),
               "recovery_assumptions": ("recovery.gpu_hours.point", 13, 12)}
    if case in oracles:
        key, observed, expected_value = oracles[case]
        lines = text.splitlines()
        position = next((i for i, line in enumerate(lines) if line.startswith("- " + key + ": FAIL")), None)
        try:
            actual = json.loads(lines[position+1].split("A/source reported: ", 1)[1])
            independent = json.loads(lines[position+2].split("C independently expected: ", 1)[1])
            numeric_quotes_match &= math.isclose(actual, observed) and math.isclose(independent, expected_value)
        except (TypeError, IndexError, ValueError):
            numeric_quotes_match = False
    ids = {e["evidence"]["id"] for e in evidence}
    expected = {"headline_hours": "cohort.recorded_gpu_hours: FAIL", "overlap": "evidence.physical_job_uniqueness: FAIL", "recovery_assumptions": "recovery.gpu_hours.point: FAIL"}.get(case)
    return {
        "G01": success and "Reported by A" in text and numeric_quotes_match and (expected is None or expected in text),
        "G02": success and set(body.get("supporting_evidence_ids", [])) <= ids,
        "G03": success and "synthetic" in text.lower(),
        "G04": success and body.get("status") == "insufficient_evidence" and "UNKNOWN" in text and "not completed tests" in text,
        "G05": success and unchanged and "remain unchanged" in text,
    }
