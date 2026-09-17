"""Original synthetic HTTP integration server; never part of production startup.

Runs A's real audit/evidence/pilot routers over invented test records. The local
checksums describe these invented fixtures, NOT the organizer's canonical data.
Every baseline/overview is labelled synthetic. Bind to loopback only.
"""
import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import tempfile

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pyarrow as pa
import pyarrow.parquet as pq
import uvicorn

from analysis.core import RULE, audit_impacts, make_evidence, select_cohort
from scripts.checksum_data import FILES, digest
from service.analysis_routes import ServiceError, router as analysis_router
from service.audits import AuditStore, freeze_evidence
from service.pilot_recovery_routes import router as pilot_router
from service.source import inspect_data


@asynccontextmanager
async def lifespan(app):
    with tempfile.TemporaryDirectory(prefix="manai-original-http-fixtures-") as folder:
        data = Path(folder)
        jobs = [dict(id_job="ORIGINAL-HTTP-J1", state_name="COMPLETED", sm_util_avg=0,
                     sm_util_max=0, gpu_hours=20, walltime_sec=36000, gpu_count=2, max_gpu_mem_used=0)]
        for name in FILES:
            path = data / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                path.write_text("[]")
            elif name == "prepped/jobs.parquet":
                pq.write_table(pa.Table.from_pylist(jobs), path)
            else:
                pq.write_table(pa.table({"original_synthetic_test_value": [1]}), path)
        (data / "checksums.txt").write_text("".join(f"{digest(data / name)}  {name}\n" for name in FILES))
        app.state.data_dir = data
        app.state.source = inspect_data(data)
        cohort = select_cohort(jobs)
        impacts = audit_impacts(cohort, [])
        provenance = dict(data_fingerprint=app.state.source["fingerprint"],
                          source_version="original-pilot-http-fixture-v1", synthetic=True,
                          sample_label="ORIGINAL SYNTHETIC HTTP TEST — not real telemetry",
                          window_label="Invented test window", caveats=["All workload values are invented for integration testing."])
        evidence = make_evidence(cohort, impacts, [], {"summary": "Original synthetic eligible job"}, provenance)
        app.state.analysis_context = freeze_evidence(dict(cohort=cohort, impacts=impacts, findings=[],
            provenance=provenance, evidence=evidence, upstream={"recommendations": []}))
        app.state.context_lock = asyncio.Lock()
        app.state.audits = AuditStore(capacity=16)
        yield


app = FastAPI(title="ORIGINAL SYNTHETIC Pilot & Recovery HTTP test", lifespan=lifespan)


@app.exception_handler(ServiceError)
async def service_error(request, exc):
    return JSONResponse(status_code=exc.status, content={"error": {
        "code": exc.code, "message": exc.message, "retryable": exc.retryable,
        "request_id": "original-synthetic-http-test"}})


@app.get("/api/health")
def health(request: Request):
    return {"service": "ok", "contract_version": "0.4", "data_status": "ready",
            "data_fingerprint": request.app.state.source["fingerprint"],
            "agent_status": "unconfigured", "mode": "synthetic_fixture"}


@app.get("/api/overview")
def overview(request: Request):
    return {"provenance": request.app.state.analysis_context["provenance"],
            "price_book_version": "original-synthetic-http-fixture", "usd_per_gpu_hour": 2.5,
            "allocated_gpu_hours": 20, "job_count": 1,
            "outcomes": [{"outcome": "COMPLETED", "gpu_hours": 20, "reference_usd": 50}],
            "warnings": ["Original invented fixture; not organizer telemetry or a savings claim."]}


app.include_router(analysis_router)
app.include_router(pilot_router)


if __name__ == "__main__":
    print("ORIGINAL SYNTHETIC HTTP TEST ONLY; no real workloads, canonical data or C service.")
    uvicorn.run(app, host="127.0.0.1", port=8121)
