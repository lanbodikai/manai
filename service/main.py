"""Analysis API; deterministic base independent of the optional reviewer."""
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import json
import math
import os
import uuid
import httpx
import jsonschema
import pyarrow.parquet as pq
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from service.source import inspect_data, current_status
from service.analysis_routes import router, ServiceError
from service.audits import AuditStore
from service.base_chat.chat import router as chat_router

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UPSTREAM = "314cca0bba49e1bb137aa9094d1dac4cdf7e4490"
SPEC = json.loads((ROOT/"contracts/openapi.json").read_text())

@asynccontextmanager
async def lifespan(app):
    app.state.data_dir = DATA
    app.state.audits = AuditStore(capacity=128)
    app.state.analysis_context = None
    app.state.context_lock = asyncio.Lock()
    app.state.chat_slots = asyncio.Semaphore(2)
    app.state.source = await asyncio.to_thread(inspect_data, DATA)
    app.state.job_count = None
    if app.state.source["status"] == "ready":
        table = await asyncio.to_thread(pq.read_table, DATA/"prepped/jobs.parquet", columns=["state_name"])
        app.state.job_count = len(table) - table.column("state_name").null_count
    async with httpx.AsyncClient(base_url=os.getenv("MGAI_URL", "http://api:8000"), timeout=15) as client:
        app.state.upstream = client
        yield

app = FastAPI(title="manai analysis service", version="0.4.0", lifespan=lifespan)

def error(request, status, code, message, retryable=False):
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "retryable": retryable,
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4()))}})

@app.middleware("http")
async def identify(request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

@app.exception_handler(RequestValidationError)
async def invalid(request, exc):
    code = "INVALID_CURSOR" if request.url.path.endswith("/evidence") else "INVALID_REQUEST"
    return error(request, 422, code, "Request does not match the contract.")

@app.exception_handler(ServiceError)
async def service_error(request, exc):
    return error(request, exc.status, exc.code, exc.message, exc.retryable)

@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    return error(request, 500, "INTERNAL_ERROR", "The analysis service could not complete this request.")

@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return error(request, exc.status_code, "ROUTE_NOT_AVAILABLE", "This route is not available in the bootstrap service.")

@app.get("/api/health")
def health(request: Request):
    snapshot = request.app.state.source
    status = current_status(DATA, snapshot)
    return {"service": "ok", "contract_version": "0.4", "data_status": status,
            "data_fingerprint": snapshot["fingerprint"] if status == "ready" else None,
            "agent_status": "unconfigured", "mode": "real"}

def map_overview(summary, waste, prices, job_count, fingerprint):
    if summary["kind"] != "fact" or waste["kind"] != "fact":
        raise ValueError("Expected factual overview endpoints")
    rate = prices["usd_per_gpu_hour"]
    if not isinstance(rate, (float,int)) or not math.isfinite(rate) or rate <= 0:
        raise ValueError("Invalid source price")
    caveats = [summary["provenance"]["caveat"], waste["provenance"]["caveat"],
        "Source outcome totals are rounded to 0.1 GPU-hour; reference dollars are not verified cash savings.",
        "Recovery scenarios are hypothetical; CPU compatibility and realized savings are unproven."]
    result = {"provenance": {"data_fingerprint": fingerprint,
        "sample_label": "MIT SuperCloud four-month job sample; not whole-fleet utilization",
        "window_label": summary["window"]["start"] + " to " + summary["window"]["end"],
        "synthetic": False, "source_version": UPSTREAM, "caveats": caveats},
        "price_book_version": prices["version"], "usd_per_gpu_hour": rate,
        "allocated_gpu_hours": summary["value"], "job_count": job_count,
        "outcomes": [{"outcome": row["state"], "gpu_hours": row["gpu_hours"],
                      "reference_usd": round(row["gpu_hours"]*rate,2)} for row in waste["rows"]],
        "warnings": caveats}
    jsonschema.Draft202012Validator({"$ref":"#/components/schemas/Overview", **SPEC}).validate(result)
    # JSON itself rejects non-finite values even if a permissive numeric validator accepted them.
    json.dumps(result, allow_nan=False)
    return result

@app.get("/api/overview")
async def overview(request: Request):
    snapshot = request.app.state.source
    if current_status(DATA, snapshot) != "ready":
        return error(request,503,"DATA_NOT_READY","Canonical source data is missing, invalid or changed. Recheck it and restart.",True)
    try:
        client = request.app.state.upstream
        responses = await asyncio.gather(*(client.get(path) for path in
            ["/v1/efficiency/summary", "/v1/waste/breakdown", "/v1/price-book"]))
        for response in responses:
            response.raise_for_status()
        result = map_overview(*(r.json() for r in responses), request.app.state.job_count, snapshot["fingerprint"])
        if current_status(DATA, snapshot) != "ready":
            return error(request,409,"DATA_VERSION_MISMATCH","Source changed during this request. Recheck and restart.")
        return result
    except httpx.HTTPError:
        return error(request,503,"UPSTREAM_UNAVAILABLE","Official API is unavailable.",True)
    except (KeyError, TypeError, ValueError, jsonschema.ValidationError):
        return error(request,502,"UPSTREAM_RESPONSE_INVALID","Official response did not match the expected overview contract.")

app.include_router(router)
app.include_router(chat_router)

@app.post("/api/audits/{audit_id}/explanations")
def reviewer_unavailable(audit_id: str, request: Request):
    return error(request,503,"AGENT_UNAVAILABLE","Optional reviewer is not enabled.")

@app.api_route("/api/{remaining:path}", methods=["GET","POST"])
def not_implemented(remaining: str, request: Request):
    return error(request,503,"BOOTSTRAP_NOT_IMPLEMENTED","This capability belongs to the next workstream slice.")
