"""Additive cpu-hardware-1 feature; active v0.4 audit wire shapes stay unchanged."""
import asyncio
import hashlib
import json
from typing import Literal
import pandas as pd
from fastapi import APIRouter, Query, Request
from analysis.hardware_scenario import build_hardware_scenario
from api.models import PriceBook
from service.analysis_routes import require_data, ServiceError

router = APIRouter()
FILES = ["prepped/jobs.parquet", "prepped/gpus.parquet", "synthetic/findings.json", "synthetic/resources.parquet", "synthetic/edges.parquet"]


def load_hardware(state):
    checks = dict(line.split()[::-1] for line in (state.data_dir / "checksums.txt").read_text().splitlines()
                  if line.strip() and not line.startswith("#"))
    # The read-only Data browser uses ordered checksum concatenation; A uses a JSON hash.
    version = hashlib.sha256("".join(checks[name] for name in FILES).encode()).hexdigest()
    prices = PriceBook()
    rows = pd.read_parquet(state.data_dir / "prepped/jobs.parquet").to_dict("records")
    result, jobs = build_hardware_scenario(rows, prices.usd_per_gpu_hour, prices.version,
                                          state.source["fingerprint"], version)
    return json.dumps({"result": result, "jobs": jobs}, allow_nan=False)


async def snapshot(request, dataset_version):
    require_data(request)
    state = request.app.state
    async with state.hardware_lock:
        if state.hardware_snapshot is None:
            try:
                value = await asyncio.to_thread(load_hardware, state)
            except (ValueError, TypeError, KeyError, OSError, OverflowError):
                raise ServiceError(503, "DATA_NOT_READY", "Hardware scenario could not be calculated from the canonical source.")
            require_data(request, snapshot=True)
            state.hardware_snapshot = value
        payload = json.loads(state.hardware_snapshot)
    if payload["result"]["dataset_version"] != dataset_version:
        raise ServiceError(409, "DATA_VERSION_MISMATCH", "Hardware scenario and Data browser must use the same canonical source.")
    require_data(request, snapshot=True)
    return payload


@router.get("/api/cpu-hardware-scenario")
async def hardware_scenario(request: Request, dataset_version: str = Query(..., min_length=1, max_length=128)):
    return (await snapshot(request, dataset_version))["result"]


@router.get("/api/cpu-hardware-scenario/jobs")
async def hardware_jobs(request: Request, dataset_version: str = Query(..., min_length=1, max_length=128),
                        scenario_id: str = Query(..., min_length=1, max_length=128),
                        status: Literal["all", "fits", "non_fit", "unresolved"] = "all",
                        offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100)):
    payload = await snapshot(request, dataset_version)
    if payload["result"]["scenario_id"] != scenario_id:
        raise ServiceError(409, "SCENARIO_MISMATCH", "Refresh the hardware scenario before viewing its jobs.")
    jobs = [j for j in payload["jobs"] if status == "all" or j["status"] == status]
    return {"contract_version": "cpu-hardware-1", "scenario_id": scenario_id, "dataset_version": dataset_version,
            "synthetic": payload["result"]["synthetic"], "offset": offset, "limit": limit, "total": len(jobs), "items": jobs[offset:offset + limit]}
