"""v0.3 endpoints: no C service or provider dependency."""
import asyncio
import json
import uuid
from pathlib import Path

import httpx
import jsonschema
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from analysis.core import (RULE, UPSTREAM, audit_impacts, load_tables, select_cohort,
                           make_evidence, export_claims)
from api.models import RecommendationsResponse, RuleTemplatesResponse
from service.audits import AuditStore, freeze_evidence, resolve_evidence, list_evidence
from service.source import current_status

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "contracts/openapi.json").read_text())
CLAIMS = json.loads((ROOT / "starter/claims.schema.json").read_text())
router = APIRouter()


class ServiceError(Exception):
    def __init__(self, status, code, message, retryable=False):
        self.status, self.code, self.message, self.retryable = status, code, message, retryable


def validate(name, value):
    json.dumps(value, allow_nan=False)
    jsonschema.Draft202012Validator({**SPEC, "$ref": "#/components/schemas/" + name}).validate(value)


async def read_body(request, name, code):
    try:
        body = await request.json()
        validate(name, body)
        return body
    except (ValueError, TypeError, jsonschema.ValidationError):
        raise ServiceError(422, code, "Request must match the frozen API schema, including finite numeric inputs.")


def require_data(request, snapshot=False):
    state = request.app.state
    if current_status(state.data_dir, state.source) != "ready":
        raise ServiceError(409 if snapshot else 503, "DATA_VERSION_MISMATCH" if snapshot else "DATA_NOT_READY",
                           "Canonical data is missing, invalid or changed; recheck and restart.")


async def fetch_source_context(client):
    try:
        replies = await asyncio.gather(*(client.get(path) for path in
            ("/v1/policies/rules", "/v1/recommendations", "/v1/efficiency/summary")))
        for reply in replies:
            reply.raise_for_status()
        rules, recommendations, summary = [r.json() for r in replies]
        RuleTemplatesResponse.model_validate(rules)
        RecommendationsResponse.model_validate(recommendations)
        rule = next(r for r in rules["rules"] if r["rule_id"] == RULE)
        if summary["kind"] != "fact":
            raise ValueError("Invalid summary kind")
        return {"rule": rule, "recommendations": recommendations["recommendations"], "summary": summary}
    except httpx.HTTPError:
        raise ServiceError(503, "UPSTREAM_UNAVAILABLE", "Official API is unavailable.", True)
    except (ValueError, TypeError, KeyError, StopIteration):
        raise ServiceError(502, "UPSTREAM_RESPONSE_INVALID", "Official source context is malformed.")


def prepare_context(data_dir, source, upstream):
    jobs, findings = load_tables(data_dir)
    cohort = select_cohort(jobs)
    impacts = audit_impacts(cohort, findings)
    summary = upstream["summary"]
    provenance = {"data_fingerprint": source["fingerprint"], "source_version": UPSTREAM, "synthetic": False,
        "sample_label": "MIT SuperCloud four-month job sample; not whole-fleet utilization",
        "window_label": summary["window"]["start"] + " to " + summary["window"]["end"],
        "caveats": ["Measured eligibility is distinct from hypothetical recovery and organizer judgments."]}
    evidence = make_evidence(cohort, impacts, findings, upstream["rule"], provenance)
    return freeze_evidence({"cohort": cohort, "impacts": impacts, "findings": findings,
        "provenance": provenance, "evidence": evidence, "upstream": upstream})


async def get_context(request):
    require_data(request)
    state = request.app.state
    async with state.context_lock:
        if state.analysis_context is None:
            upstream = await fetch_source_context(state.upstream)
            try:
                context = await asyncio.to_thread(prepare_context, state.data_dir, state.source, upstream)
            except (ValueError, KeyError, TypeError, OSError):
                raise ServiceError(503, "DATA_NOT_READY", "Source tables or join identities are invalid.")
            require_data(request, snapshot=True)
            state.analysis_context = context
    return state.analysis_context


def get_snapshot(request, audit_id):
    snapshot = request.app.state.audits.get(audit_id)
    if snapshot is None:
        raise ServiceError(404, "AUDIT_NOT_FOUND", "Unknown or expired audit; recompute the scenario.")
    require_data(request, snapshot=True)
    if snapshot.audit["provenance"]["data_fingerprint"] != request.app.state.source["fingerprint"]:
        raise ServiceError(409, "DATA_VERSION_MISMATCH", "Audit does not match the available source.")
    return snapshot


@router.get("/api/recommendations")
async def recommendations(request: Request):
    context = await get_context(request)
    items = [{"id": "cpu-placement-pilot", "source_recommendation_id": None,
        "title": "Audit completed zero-compute jobs for a CPU-placement pilot", "origin": "team", "kind": "judgment",
        "audit_available": True, "finding_ids": [f["id"] for f in context["findings"] if f["detectorId"] == RULE][:20],
        "caveats": ["CPU placement is already suggested upstream. Compatibility and realized savings remain unproven."]}]
    for r in context["upstream"]["recommendations"]:
        items.append({"id": r["id"], "source_recommendation_id": r["id"], "title": r["title"],
            "origin": "organizer", "kind": "judgment", "audit_available": False,
            "finding_ids": r["finding_ids"], "caveats": ["Organizer judgment; not audited by this CPU-placement analysis."]})
    result = {"provenance": context["provenance"], "items": items}
    validate("Recommendations", result)
    return result


@router.post("/api/audits", status_code=201)
async def create_audit(request: Request):
    body = await read_body(request, "AuditRequest", "INVALID_SCENARIO")
    require_data(request)
    if body["expected_data_fingerprint"] != request.app.state.source["fingerprint"]:
        raise ServiceError(409, "DATA_VERSION_MISMATCH", "Refresh readiness and calculate with the current fingerprint.")
    context = await get_context(request)
    try:
        snapshot = request.app.state.audits.create(body, context)
    except (ValueError, OverflowError):
        raise ServiceError(422, "INVALID_SCENARIO", "Fractions must be ordered within [0,1]; price and results must be finite.")
    require_data(request, snapshot=True)
    validate("Audit", snapshot.audit)
    return snapshot.audit


@router.get("/api/audits/{audit_id}")
def audit(audit_id: str, request: Request):
    return get_snapshot(request, audit_id).audit


@router.get("/api/audits/{audit_id}/evidence")
def evidence_page(audit_id: str, request: Request, limit: int = Query(25, ge=1, le=100), cursor: str | None = Query(None, max_length=512)):
    snapshot = get_snapshot(request, audit_id)
    try:
        return list_evidence(snapshot, audit_id, limit, cursor)
    except ValueError:
        raise ServiceError(422, "INVALID_CURSOR", "Cursor must belong to this audit and identify a valid page.")


@router.get("/api/audits/{audit_id}/evidence/{evidence_id}")
def evidence_detail(audit_id: str, evidence_id: str, request: Request):
    try:
        return resolve_evidence(get_snapshot(request, audit_id), audit_id, evidence_id)
    except KeyError:
        raise ServiceError(404, "EVIDENCE_NOT_FOUND", "Evidence does not belong to this audit.")


@router.get("/api/audits/{audit_id}/claims")
def claims(audit_id: str, request: Request, team: str = Query(..., min_length=1, max_length=120)):
    if not team.strip():
        raise ServiceError(422, "INVALID_REQUEST", "Team name must not be blank.")
    result = export_claims(get_snapshot(request, audit_id).audit, team)
    validate("Claims", result)
    jsonschema.validate(result, CLAIMS)
    return JSONResponse(result, headers={"Content-Disposition": 'attachment; filename="claims.json"'})
