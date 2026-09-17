"""D01-D06/API checks. Run locally; private rows and claims never enter Git."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

import httpx
import pandas as pd

from service.analysis_routes import validate, CLAIMS
import jsonschema


def run(base, data, output):
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "scripts/checksum_data.py", "--data", str(data)], check=True)
    client = httpx.Client(base_url=base, timeout=120)
    health = client.get("/api/health").raise_for_status().json()
    assert health["data_status"] == "ready"
    overview = client.get("/api/overview").raise_for_status().json()
    request = {"client_request_id": "a-real-verification", "expected_data_fingerprint": health["data_fingerprint"],
        "recommendation_id": "cpu-placement-pilot", "scenario": {"recovery_fraction": {"low": 0, "point": 0, "high": 1},
        "usd_per_gpu_hour": overview["usd_per_gpu_hour"], "cancelled_policy": "exclude", "interval_kind": "scenario",
        "assumption_note": "No empirical CPU-recoverability evidence: zero low/point; high is the eligibility ceiling, not a forecast. Positive scenarios are exploratory."}}
    response = client.post("/api/audits", json=request).raise_for_status()
    assert response.status_code == 201
    audit = response.json()
    validate("Audit", audit)
    aid = audit["audit_id"]
    # Independent row-loop, not the service's select_cohort or aggregation.
    jobs = pd.read_parquet(data / "prepped/jobs.parquet")
    eligible, excluded = [], []
    columns = ["id_job", "state_name", "sm_util_avg", "sm_util_max", "gpu_hours", "walltime_sec", "gpu_count", "max_gpu_mem_used"]
    assert jobs.id_job.is_unique
    for row in jobs[columns].to_dict("records"):
        measurements = [row[k] for k in ("sm_util_avg", "sm_util_max", "gpu_hours")]
        good = (all(pd.notna(v) and math.isfinite(v) for v in measurements)
                and row["state_name"] == "COMPLETED" and row["sm_util_avg"] == row["sm_util_max"] == 0
                and row["gpu_hours"] > 1 and (pd.isna(row["walltime_sec"]) or row["walltime_sec"] >= 0))
        (eligible if good else excluded).append(row)
    independent_hours = math.fsum(r["gpu_hours"] for r in eligible)
    assert len(eligible) == audit["eligibility"]["unique_jobs"]
    assert math.isclose(independent_hours, audit["eligibility"]["eligible_gpu_hours"], rel_tol=1e-6)
    gpus = pd.read_parquet(data / "prepped/gpus.parquet", columns=["id_job", "gpu_hours"])
    card_hours = math.fsum(gpus.loc[gpus.id_job.isin([r["id_job"] for r in eligible]), "gpu_hours"])
    assert math.isclose(card_hours, independent_hours, rel_tol=1e-6)
    refs, cursor = [], None
    while True:
        page = client.get(f"/api/audits/{aid}/evidence", params={"limit": 100, **({"cursor": cursor} if cursor else {})}).raise_for_status().json()
        validate("EvidencePage", page)
        refs.extend(page["items"])
        cursor = page["next_cursor"]
        if not cursor: break
    assert len(refs) == len({r["id"] for r in refs}) == audit["evidence_count"]
    assert {r["source_id"] for r in refs if r["kind"] == "job"} == {str(r["id_job"]) for r in eligible}
    for ref in refs[:5]:
        validate("EvidenceDetail", client.get(f"/api/audits/{aid}/evidence/{ref['id']}").raise_for_status().json())
    findings = json.loads((data / "synthetic/findings.json").read_text())
    rule_ids = {str(f["metadata"]["job_id"]) for f in findings if f["detectorId"] == "rules::gpu-not-needed"}
    assert rule_ids == {str(r["id_job"]) for r in eligible}
    recommendations = client.get("/api/recommendations").raise_for_status().json()
    validate("Recommendations", recommendations)
    assert not audit["source_recommendation_ids"]
    # D04 captures five eligible and distinct exclusion/boundary categories for inspection.
    boundary = []
    for predicate in (lambda r: r["state_name"] == "CANCELLED",
                      lambda r: r["state_name"] == "COMPLETED" and r["sm_util_avg"] > 0,
                      lambda r: r["state_name"] == "COMPLETED" and r["sm_util_avg"] == r["sm_util_max"] == 0 and r["gpu_hours"] <= 1):
        match = next((r for r in excluded if predicate(r)), None)
        if match is not None: boundary.append(match)
    assert len(boundary) == min(3, len(excluded))
    review = {"eligible": eligible[:5], "excluded_boundary": boundary}
    (output / "record-review.json").write_text(json.dumps(review, indent=2, default=str))
    scenarios = []
    for fraction in (0, .5, 1):
        for price in (overview["usd_per_gpu_hour"], overview["usd_per_gpu_hour"] * 2):
            req = json.loads(json.dumps(request))
            req["scenario"].update(recovery_fraction=dict(low=0, point=fraction, high=1), usd_per_gpu_hour=price)
            a = client.post("/api/audits", json=req).raise_for_status().json()
            assert a["eligibility"]["eligible_gpu_hours"] == independent_hours
            assert a["recovery"]["gpu_hours"]["point"] == independent_hours * fraction
            assert a["recovery"]["reference_usd"]["values"]["point"] == independent_hours * fraction * price
            assert 0 <= a["recovery"]["gpu_hours"]["point"] <= independent_hours
            scenarios.append({"fraction": fraction, "price": price, "recovery": a["recovery"]})
    claims = client.get(f"/api/audits/{aid}/claims", params={"team": "manai"}).raise_for_status().json()
    validate("Claims", claims)
    jsonschema.validate(claims, CLAIMS)
    assert claims["recoverable_gpu_hours"]["point"] == claims["recoverable_gpu_hours"]["low"] == 0
    assert claims["recoverable_gpu_hours"]["high"] == independent_hours
    assert client.get(f"/api/audits/{aid}").json() == audit
    bad = {**request, "expected_data_fingerprint": "stale"}
    assert client.post("/api/audits", json=bad).status_code == 409
    assert client.get(f"/api/audits/{aid}/evidence/not-a-member").status_code == 404
    for name, payload in (("audit", audit), ("claims", claims), ("sensitivity", scenarios)):
        (output / (name + ".json")).write_text(json.dumps(payload, indent=2))
    result = {"D01": "PASS", "D02": "PASS: independent row loop, exact IDs and card reconciliation",
        "D03": "PASS: gpu-not-needed rule aligned; rec_lowutil cohort/action differs, no correction claimed",
        "D04": "ROWS_CAPTURED: inspect private record-review.json before claiming PASS",
        "D05": "PASS: 3 recovery settings x 2 prices", "D06": "PASS A-side basis/export; B display/report agreement pending",
        "API": "PASS live Audit/Recommendations/EvidencePage/EvidenceDetail/Claims; stale request and unknown evidence rejected",
        "audit_id": aid, "fingerprint": health["data_fingerprint"], "contract_version": audit["contract_version"],
        "eligible_jobs": len(eligible), "eligible_gpu_hours": independent_hours, "evidence_count": len(refs),
        "cpu_compatibility_verified": False, "realized_savings_verified": False}
    (output / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8001")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("private-eval/analysis"))
    args = parser.parse_args()
    run(args.base, args.data, args.output)
