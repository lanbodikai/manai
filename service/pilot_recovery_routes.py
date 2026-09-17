"""Additive audit-scoped pilot simulations, independent of optional C and live execution."""
import json
from pathlib import Path
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import jsonschema

from analysis.pilot_recovery import baseline_from_evidence, simulate_pilot
from service.analysis_routes import ServiceError, get_snapshot
from service.audits import resolve_evidence


router = APIRouter()
SPEC = json.loads((Path(__file__).resolve().parents[1] / "contracts/pilot-recovery.openapi.json").read_text())


def validate(name, payload):
    json.dumps(payload, allow_nan=False)
    jsonschema.Draft202012Validator({**SPEC, "$ref": "#/components/schemas/" + name}).validate(payload)


def identity(audit):
    return {"feature_version": "0.1", "audit_id": audit["audit_id"],
            "audit_client_request_id": audit["client_request_id"],
            **{k: audit["provenance"][k] for k in ("data_fingerprint", "source_version", "synthetic")}}


def resolve_baseline(snapshot, audit, evidence_id):
    try:
        detail = resolve_evidence(snapshot, audit["audit_id"], evidence_id)
    except KeyError:
        raise ServiceError(404, "EVIDENCE_NOT_FOUND", "The pilot baseline must belong to this audit.")
    if detail["evidence"]["kind"] != "job":
        raise ServiceError(404, "EVIDENCE_NOT_FOUND", "The pilot baseline must be an eligible job in this audit.")
    provenance = detail["provenance"]
    if (detail["evidence"]["id"] != evidence_id
            or any(provenance[k] != audit["provenance"][k] for k in ("data_fingerprint", "source_version", "synthetic"))
            or detail["evidence"]["synthetic"] != provenance["synthetic"]):
        raise ServiceError(409, "DATA_VERSION_MISMATCH", "The frozen baseline identity differs from its audit.")
    return baseline_from_evidence(detail, audit["scenario"]["usd_per_gpu_hour"])


@router.get("/api/audits/{audit_id}/pilot-baselines")
def pilot_baselines(audit_id: str, request: Request):
    snapshot = get_snapshot(request, audit_id)
    audit = snapshot.audit
    try:
        refs = [json.loads(ref) for ref in snapshot.refs]
        items = [resolve_baseline(snapshot, audit, ref["id"]) for ref in refs if ref["kind"] == "job"]
        items.sort(key=lambda item: (-(item["recorded_gpu_hours"] or 0), item["source_job_id"]))
        result = {**identity(audit), "simulation_only": True, "items": items, "total": len(items),
                  "limitations": ["These are eligible historical jobs, not proof of CPU compatibility.",
                                  "Nullable baseline fields remain unknown and cannot be overridden by the browser.",
                                  "Baseline evidence is frozen within a memory-only audit; simulation history is not persisted."]}
        if audit["provenance"]["synthetic"]:
            result["limitations"].insert(0, "SYNTHETIC TEST BASELINES: not real workload telemetry.")
        validate("PilotBaselines", result)
    except (ValueError, OverflowError, jsonschema.ValidationError):
        raise ServiceError(422, "INVALID_BASELINE", "Baseline measurements cannot be represented by the pilot contract.")
    get_snapshot(request, audit_id)
    return result


@router.post("/api/audits/{audit_id}/pilot-simulations")
async def pilot_simulation(audit_id: str, request: Request):
    snapshot = get_snapshot(request, audit_id)
    audit = snapshot.audit
    try:
        body = await request.json()
        validate("PilotSimulationRequest", body)
    except (ValueError, TypeError, jsonschema.ValidationError):
        raise ServiceError(422, "INVALID_PILOT_SIMULATION", "The request does not match the pilot simulation contract.")
    try:
        baseline = resolve_baseline(snapshot, audit, body["baseline_evidence_id"])
        result = {**identity(audit), "simulation_id": uuid.uuid4().hex,
                  "client_request_id": body["client_request_id"], **simulate_pilot(baseline, body)}
        validate("PilotSimulation", result)
    except (ValueError, OverflowError, jsonschema.ValidationError):
        raise ServiceError(422, "INVALID_PILOT_SIMULATION", "The pilot assumptions or arithmetic are invalid.")
    get_snapshot(request, audit_id)
    return JSONResponse(result, status_code=201)
