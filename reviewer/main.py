"""Optional reviewer entrypoint, isolated from all required A/B services."""
from __future__ import annotations

import asyncio
import json
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator
from starlette.exceptions import HTTPException

from reviewer.clients import AnalysisClient, OfficialMCP, ReviewError
from reviewer.model import ModelReviewer, ModelError
from reviewer.render import build_facts, render_answer
from reviewer.settings import Settings
from reviewer.validation import validate_audit


def create_app(settings=None, *, analysis=None, mcp=None, model=None):
    settings = settings or Settings.from_env()
    spec = json.loads((settings.repo_root / "contracts/openapi.json").read_text())
    def validator(name):
        return Draft202012Validator({"$ref": "#/components/schemas/" + name, **spec})
    request_validator = validator("ExplanationRequest")
    response_validator = validator("Explanation")
    app = FastAPI(title="Optional evidence validation", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.active = 0
    app.state.last_mcp = "not_checked"
    app.state.last_analysis = "not_checked"
    analysis = analysis or AnalysisClient(settings.analysis_url, max_pages=settings.max_pages,
                                         max_evidence=settings.max_evidence)
    mcp = mcp or OfficialMCP(settings.repo_root, context_mode=settings.mcp_context)

    def error_response(status, code, message, request_id, retryable=False):
        return JSONResponse(status_code=status, content={"error": dict(
            code=code, message=message, retryable=retryable, request_id=request_id)})

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error_response(exc.status_code, "INVALID_ROUTE", "Unknown route or method.", str(uuid.uuid4()))

    @app.get("/health")
    async def health():
        return {"status": "alive", "mode": settings.mode,
                "analysis": app.state.last_analysis, "tools": app.state.last_mcp,
                "mcp_scope": settings.mcp_context,
                "provider": ("not_required" if settings.mode == "deterministic" else
                             "configured_not_probed" if settings.provider_key and settings.model else "unconfigured"),
                "contract_version": "0.4"}

    @app.post("/api/audits/{audit_id}/explanations")
    async def explain(audit_id: str, request: Request):
        request_id = str(uuid.uuid4())
        if app.state.active >= 2:
            return error_response(429, "REQUEST_BUDGET_EXCEEDED", "Reviewer concurrency limit reached.", request_id, True)
        app.state.active += 1
        started = time.monotonic()
        try:
            async with asyncio.timeout(settings.timeout_seconds):
                body = bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > 12000:
                        raise ReviewError(422, "INVALID_QUESTION", "Request exceeds the reviewer body limit.")
                try:
                    payload = json.loads(body)
                    request_validator.validate(payload)
                    if not payload["question"].strip() or not audit_id or len(audit_id) > 200:
                        raise ValueError("invalid question or identity")
                except Exception:
                    raise ReviewError(422, "INVALID_QUESTION", "Provide a question and client_request_id matching the contract.") from None
                request_id = payload["client_request_id"]
                audit, evidence, coverage = await analysis.load(audit_id)
                app.state.last_analysis = "last_request_succeeded"
                try:
                    context = await mcp.inspect()
                except Exception:
                    app.state.last_mcp = "unavailable"
                    raise
                app.state.last_mcp = "last_probe_succeeded"
                report = validate_audit(audit, evidence, coverage, context)
                report["limitations"].extend(context.get("limitations", []))
                facts = build_facts(audit, report)
                selection = None
                usage = dict(tool_calls=context["tool_calls"], input_tokens=None, output_tokens=None,
                             estimated_usd=None, model=None, provider=None, latency_ms=0)
                if settings.mode == "model":
                    reviewer = model or ModelReviewer(
                        base_url=settings.provider_url, api_key=settings.provider_key, model=settings.model,
                        input_usd_per_million=settings.input_rate, output_usd_per_million=settings.output_rate)
                    # Model selection sees a bounded view. Final rendering still includes
                    # every failed/unknown check from the full independent report.
                    ranked = sorted(report["checks"], key=lambda c: {"fail": 0, "unknown": 1, "pass": 2}[c["status"]])
                    compact = {"audit_id": report["audit_id"], "data_fingerprint": report["data_fingerprint"],
                               "coverage": report["coverage"], "limitations": report["limitations"][:12],
                               "checks": [{k: c[k] for k in ("id", "status", "message")} for c in ranked[:60]],
                               "selection_scope": "At most sixty checks, failures and unknowns first. Full checks remain in the rendered review."}
                    selection = await reviewer.review(payload["question"], compact, facts)
                    usage.update(selection["usage"])
                question = payload["question"].lower()
                unsupported = not any(word in question for word in (
                    "review", "valid", "risk", "evidence", "hours", "cost", "saving", "recover", "cohort", "overlap", "synthetic", "blame", "caus", "downside", "gpu", "cpu"))
                limitations = list(dict.fromkeys(report["limitations"] + context.get("limitations", []) + [
                    "Telemetry does not prove workload compatibility, output correctness, cash savings or tested recovery.",
                    "MCP context is not treated as matching audit evidence without independently established source identity and scoped references."]))
                if unsupported:
                    limitations.append("The question is outside this bounded audit review; the response only reports available validation checks.")
                unsupported = unsupported or any(word in question for word in ("blame", "cause", "guarantee", "safe", "prove"))
                result = {
                    "audit_id": audit_id, "client_request_id": request_id,
                    "status": "insufficient_evidence" if unsupported or any(c["status"] != "pass" for c in report["checks"]) else "ok",
                    "answer": render_answer(audit, report, facts, selection),
                    "supporting_evidence_ids": report["verified_evidence_ids"],
                    "limitations": limitations, "tool_trace_ids": context["tool_trace_ids"],
                    "usage": {**usage, "latency_ms": round((time.monotonic() - started) * 1000, 3)},
                }
                response_validator.validate(result)
                return result
        except (ReviewError, ModelError) as exc:
            return error_response(exc.status, exc.code, exc.message, request_id, exc.retryable)
        except (TimeoutError, asyncio.TimeoutError):
            return error_response(504, "EXPLANATION_TIMEOUT", "Review exceeded the configured time budget.", request_id, True)
        except Exception:
            return error_response(502, "UPSTREAM_RESPONSE_INVALID", "Review could not validate the source response.", request_id)
        finally:
            app.state.active -= 1

    return app


app = create_app()
