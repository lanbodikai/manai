"""Bounded real official MCP retrieval; templates never invent numeric evidence."""
import asyncio
import json
from pathlib import Path
import re
import time
import uuid

from fastapi import APIRouter, Request

from analysis.core import RULE, evidence_id
from service.analysis_routes import ServiceError, get_snapshot, read_body, require_data, validate
from service.mcp_client import connect_official

router = APIRouter()
TOOL_LIMIT = 3
TIME_LIMIT = 10
# Pinned SDK shutdown allows 0.5s writer flush + 2s exit + 2s kill/reap.
# Reserve five seconds so cancellation cleanup fits inside the public budget.
CLEANUP_RESERVE = 5
QUESTIONS = {
    "why this pilot": "support", "what supports this recommendation": "support",
    "what evidence supports this recommendation": "support", "explain this recommendation": "support",
    "which jobs are eligible": "eligibility", "explain eligibility": "eligibility",
    "why are these jobs included": "eligibility", "what is the eligibility rule": "eligibility",
    "what are the recovery assumptions": "assumptions", "explain recovery assumptions": "assumptions",
    "are these cash savings": "assumptions", "how are recovery hours calculated": "assumptions",
    "what could go wrong": "downside", "what is the downside": "downside",
    "what if these workloads actually need gpus": "downside", "what are the risks": "downside",
}


def service_failure(exc):
    """MCP transport task groups may wrap domain errors during cleanup."""
    if isinstance(exc, ServiceError):
        return exc
    if isinstance(exc, BaseExceptionGroup):
        for child in exc.exceptions:
            result = service_failure(child)
            if result is not None:
                return result
    return None


def classify_supported_question(question):
    normalized = re.sub(r"\s+", " ", question.strip().lower()).rstrip("?.!")
    return QUESTIONS.get(normalized)


def tool_body(result):
    if getattr(result, "is_error", False):
        raise ServiceError(503, "UPSTREAM_UNAVAILABLE", "Official MCP tool reported failure.", True)
    value = getattr(result, "structured_content", None)
    if value is None:
        try:
            value = json.loads(next(item.text for item in result.content if item.type == "text"))
        except (StopIteration, ValueError, AttributeError):
            raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP response is not a valid evidence object.")
    if not isinstance(value, dict):
        raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP response is not an evidence object.")
    return value


async def call_mcp_evidence(snapshot, check_source, trace_dir, connector=connect_official):
    """Fresh subprocess reads the same verified source; no provider environment passed."""
    audit = snapshot.audit
    fingerprint = audit["provenance"]["data_fingerprint"]
    calls, traces = [], []
    async with connector() as client:
        async def call(name, arguments):
            if len(calls) >= TOOL_LIMIT:
                raise ServiceError(429, "REQUEST_BUDGET_EXCEEDED", "MCP tool budget exhausted.")
            check_source()
            calls.append(name)
            value = tool_body(await client.call_tool(name, arguments))
            check_source()
            trace_id = uuid.uuid4().hex
            # Private trace provides reproducibility without publishing source rows.
            trace = {"trace_id": trace_id, "audit_id": audit["audit_id"], "fingerprint": fingerprint,
                     "transport": "official stdio MCP", "tool": name, "arguments": arguments, "result": value}
            trace_dir.mkdir(parents=True, exist_ok=True)
            (trace_dir / (trace_id + ".json")).write_text(json.dumps(trace, allow_nan=False))
            traces.append(trace_id)
            return value

        rules = await call("list_rules", {})
        rule = next((r for r in rules.get("rules", []) if isinstance(r, dict) and r.get("rule_id") == RULE), None)
        rid = evidence_id(fingerprint, "rule", RULE)
        if rule is None or rid not in snapshot.evidence:
            raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "Required official rule evidence is missing.")
        expected_rule = json.loads(snapshot.evidence[rid])
        summary = next(o["value"] for o in expected_rule["observations"] if o["name"] == "summary")
        if rule.get("summary") != summary:
            raise ServiceError(409, "DATA_VERSION_MISMATCH", "MCP rule differs from the audit snapshot.")
        refs = [rid, evidence_id(fingerprint, "aggregate", "accounting")]
        if any(ref not in snapshot.evidence for ref in refs):
            raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "Canonical accounting evidence is missing.")
        findings = await call("list_findings", {"detector_id": RULE, "limit": 1, "offset": 0})
        rows = findings.get("findings")
        if not isinstance(rows, list) or len(rows) > 1 or type(findings.get("total")) is not int:
            raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP returned malformed bounded findings.")
        if not rows and audit["eligibility"]["unique_jobs"]:
            raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP finding evidence is missing for this cohort.")
        for row in rows:
            if not isinstance(row, dict) or row.get("detectorId") != RULE or not isinstance(row.get("metadata"), dict):
                raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP finding does not match the requested rule.")
            fid = evidence_id(fingerprint, "finding", row.get("id"))
            jid = evidence_id(fingerprint, "job", row["metadata"].get("job_id"))
            if fid not in snapshot.evidence or jid not in snapshot.evidence:
                raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP evidence does not belong to this audit.")
            expected = json.loads(snapshot.evidence[fid])
            for observation in expected["observations"]:
                if observation["column"].startswith("metadata."):
                    key = observation["column"].split(".", 1)[1]
                    if observation["value"] != row["metadata"].get(key):
                        raise ServiceError(409, "DATA_VERSION_MISMATCH", "MCP observation differs from the audit.")
            if bool(row["metadata"].get("synthetic")) != expected["evidence"]["synthetic"] and not audit["provenance"]["synthetic"]:
                raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "MCP synthetic provenance does not match the audit.")
            refs.extend([fid, jid])
    check_source()
    return refs, traces, len(calls)


def render_supported_answer(intent, audit):
    e, r = audit["eligibility"], audit["recovery"]
    prefix = "MCP evidence chatbot — template-based. "
    if audit["provenance"]["synthetic"]:
        prefix += "This audit uses synthetic records, not measured telemetry. "
    if intent == "support":
        return prefix + (f"The canonical audit contains {e['unique_jobs']} completed zero-SM jobs and "
            f"{e['eligible_gpu_hours']:.6f} recorded eligible GPU-hours. Official rule evidence supports investigating "
            "a CPU-placement pilot; the proposed action is a judgment, not proof of compatibility. "
            "The retrieved finding is one supporting example, not a new cohort total. Recovery remains an assumed scenario.")
    if intent == "eligibility":
        return prefix + e["definition"] + ". " + e["coverage_note"] + ". Missing values are not zero; cancelled jobs are excluded. Zero SM activity does not prove CPU compatibility."
    if intent == "assumptions":
        return prefix + (r["basis"] + f" Recoverable low/point/high: {r['gpu_hours']['low']:.6f}/"
            f"{r['gpu_hours']['point']:.6f}/{r['gpu_hours']['high']:.6f} GPU-hours. "
            f"Reference USD/GPU-hour: {audit['scenario']['usd_per_gpu_hour']:.6f}. "
            "These are assumed scenario bounds, not calibrated probabilities or verified cash savings. "
            "MCP verifies supporting rule/finding evidence; it does not establish the conversion fractions.")
    d = audit["downside"]
    pilot = d.get("cpu_pilot")
    if pilot is not None:
        metric = lambda value: "unknown" if value is None else format(value, ".6f")
        pilot_text = (f" Single-job {pilot['mode']} scenario: released {metric(pilot['released_gpu_hours'])} GPU-hours; "
            f"added CPU reference cost {metric(pilot['added_cpu_reference_usd'])} USD; signed net reference value "
            f"{metric(pilot['net_reference_value_usd'])} USD; completion change "
            f"{metric(pilot['completion_change_hours_including_extra_queue'])} hours. "
            "Failure assumes a full GPU rerun; additional validation retains GPU allocation with unknown completion impact. "
            "These metrics are separate from cohort recovery; unknown cost/delay remains unknown. ")
    else:
        pilot_text = " Downside money is not quantified. "
    return prefix + " ".join(d["mechanisms"] + d["assumptions"] + d["guardrails"]) + pilot_text + "These are proposed risks and checks, not observed intervention outcomes."


async def answer_base_chat(snapshot, body, check_source, trace_dir, connector=connect_official, time_limit=TIME_LIMIT):
    start = time.monotonic()
    intent = classify_supported_question(body["question"])
    audit = snapshot.audit
    refs, traces, calls = [], [], 0
    if intent is None:
        status = "insufficient_evidence"
        answer = "This template-based chatbot supports recommendation evidence, eligibility, recovery assumptions and downside. It cannot establish CPU compatibility, causal certainty, realized savings or individual blame."
    else:
        try:
            async with asyncio.timeout(max(.001, time_limit - CLEANUP_RESERVE)):
                refs, traces, calls = await call_mcp_evidence(snapshot, check_source, trace_dir, connector)
        except TimeoutError:
            raise ServiceError(504, "EXPLANATION_TIMEOUT", "Official MCP evidence retrieval exceeded the ten-second budget.", True)
        except ServiceError:
            raise
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "Official MCP evidence response was malformed.")
        except Exception as exc:
            domain_error = service_failure(exc)
            if domain_error is not None:
                raise domain_error
            raise ServiceError(503, "UPSTREAM_UNAVAILABLE", "Official MCP runtime is unavailable.", True)
        status, answer = "ok", render_supported_answer(intent, audit)
        pilot = audit["downside"].get("cpu_pilot")
        if pilot is not None and intent == "downside":
            baseline = pilot["baseline"]["evidence_id"]
            if baseline not in snapshot.evidence:
                raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "CPU baseline evidence is missing from the audit.")
            if baseline not in refs:
                refs.append(baseline)
    result = {"audit_id": audit["audit_id"], "client_request_id": body["client_request_id"], "status": status,
        "answer": answer, "supporting_evidence_ids": refs, "tool_trace_ids": traces,
        "limitations": ["Template-based; no model/provider is used.", "Tool evidence does not prove CPU compatibility or realized savings."],
        "usage": {"tool_calls": calls, "input_tokens": None, "output_tokens": None, "estimated_usd": None,
                  "latency_ms": (time.monotonic() - start) * 1000, "model": None, "provider": None}}
    validate("Explanation", result)
    return result


@router.post("/api/audits/{audit_id}/chat")
async def chat(audit_id: str, request: Request):
    body = await read_body(request, "ExplanationRequest", "INVALID_QUESTION")
    if not body["question"].strip():
        raise ServiceError(422, "INVALID_QUESTION", "Question must not be blank.")
    snapshot = get_snapshot(request, audit_id)
    semaphore = request.app.state.chat_slots
    if semaphore.locked():
        raise ServiceError(429, "REQUEST_BUDGET_EXCEEDED", "Two MCP requests are already active; retry shortly.", True)
    async with semaphore:
        return await answer_base_chat(snapshot, body, lambda: require_data(request, snapshot=True),
                                      Path("private-eval/base-chat"))
