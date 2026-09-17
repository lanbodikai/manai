"""Invented HTTP peer for the socket smoke test; never a replacement A service."""
from copy import deepcopy
from fastapi import FastAPI, HTTPException
from eval.agent.cases import fixture

app = FastAPI()
audit, evidence = fixture()


@app.get("/api/health")
def health():
    return {"status": "synthetic_test_peer"}


@app.get("/api/audits/{audit_id}")
def get_audit(audit_id: str):
    if audit_id != audit["audit_id"]:
        raise HTTPException(404)
    return deepcopy(audit)


@app.get("/api/audits/{audit_id}/evidence")
def list_evidence(audit_id: str):
    get_audit(audit_id)
    return {"audit_id": audit_id, "items": [deepcopy(e["evidence"]) for e in evidence], "next_cursor": None, "total": len(evidence)}


@app.get("/api/audits/{audit_id}/evidence/{evidence_id}")
def get_evidence(audit_id: str, evidence_id: str):
    get_audit(audit_id)
    row = next((e for e in evidence if e["evidence"]["id"] == evidence_id), None)
    if row is None:
        raise HTTPException(404)
    return deepcopy(row)
