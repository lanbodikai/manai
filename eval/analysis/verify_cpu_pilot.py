"""Live v0.4 cost/delay, membership, partition and MCP verification."""
import copy
import json
import math
from pathlib import Path
import httpx
import pandas as pd
from service.analysis_routes import validate


def main():
    client = httpx.Client(base_url="http://127.0.0.1:8001", timeout=15)
    output = Path("private-eval/analysis")
    initial = json.loads((output / "audit.json").read_text())
    assert initial["contract_version"] == "0.4"
    refs, cursor = [], None
    while True:
        page = client.get(f"/api/audits/{initial['audit_id']}/evidence", params={"limit": 100, **({"cursor": cursor} if cursor else {})}).raise_for_status().json()
        refs += page["items"]
        cursor = page["next_cursor"]
        if not cursor: break
    job_refs = {r["source_id"]: r for r in refs if r["kind"] == "job"}
    jobs = pd.read_parquet("data/prepped/jobs.parquet")
    selected = jobs[jobs.id_job.astype(str).isin(job_refs)]
    partition = initial["eligibility"]["memory_partition"]
    masks = {"zero_memory": selected.max_gpu_mem_used.eq(0), "positive_memory": selected.max_gpu_mem_used.gt(0),
             "unknown_memory": selected.max_gpu_mem_used.isna() | selected.max_gpu_mem_used.lt(0)}
    for key, mask in masks.items():
        assert partition[key]["unique_jobs"] == int(mask.sum())
        assert math.isclose(partition[key]["recorded_gpu_hours"], float(selected.loc[mask, "gpu_hours"].sum()), abs_tol=1e-6)
    assert sum(partition[k]["unique_jobs"] for k in masks) == initial["eligibility"]["unique_jobs"]
    baseline_row = next(r for r in selected.to_dict("records") if r["walltime_sec"] > 0 and r["gpu_count"] > 0)
    eid = job_refs[str(baseline_row["id_job"])]["id"]
    t, h = baseline_row["walltime_sec"] / 3600, baseline_row["gpu_hours"]
    pilot = dict(mode="replacement_success", baseline_evidence_id=eid, cpu_vcpus=4, cpu_hours=t * 1.2,
                 cpu_vcpu_hour_usd=.1, extra_queue_hours=0, trial_cap_hours=None, baseline_host_costs_included=True,
                 assumption_note="Explicit hypothetical test: CPU duration/rate/allocation not measured; no workload execution.")
    cases = [({}, "success"), ({"mode": "replacement_failure"}, "failure"),
             ({"mode": "additional_validation"}, "validation"), ({"cpu_vcpu_hour_usd": 100}, "loss"),
             ({"cpu_vcpu_hour_usd": None}, "unknown_price"), ({"extra_queue_hours": None}, "unknown_queue"),
             ({"baseline_host_costs_included": False}, "pricing_boundary"), ({"cpu_hours": t / 2}, "earlier")]
    audits = []
    for changes, name in cases:
        p = {**pilot, **changes}
        request = dict(client_request_id="pilot-" + name, expected_data_fingerprint=initial["provenance"]["data_fingerprint"],
                       recommendation_id="cpu-placement-pilot", scenario={**initial["scenario"], "cpu_pilot": p})
        a = client.post("/api/audits", json=request).raise_for_status().json()
        validate("Audit", a)
        r = a["downside"]["cpu_pilot"]
        assert r["baseline"]["evidence_id"] == eid and r["baseline"]["recorded_gpu_hours"] == h
        assert r["baseline"]["elapsed_hours"] == t
        release = h if p["mode"] == "replacement_success" else 0
        cost = None if p["cpu_vcpu_hour_usd"] is None else 4 * p["cpu_hours"] * p["cpu_vcpu_hour_usd"]
        assert r["released_gpu_hours"] == release and r["scenario_gpu_hours"] == h - release
        assert r["added_cpu_reference_usd"] == cost
        expected_net = None if cost is None or not p["baseline_host_costs_included"] else release * initial["scenario"]["usd_per_gpu_hour"] - cost
        assert r["net_reference_value_usd"] == expected_net
        if name in {"failure", "loss"}: assert r["net_reference_value_usd"] < 0
        if name == "earlier": assert r["completion_change_hours_including_extra_queue"] < 0
        if name in {"validation", "unknown_queue"}: assert r["completion_change_hours_including_extra_queue"] is None
        assert a["recovery"] == initial["recovery"] and a["downside"]["money"] is None
        base = "/api/audits/" + a["audit_id"]
        detail = client.get(base + "/evidence/" + eid).raise_for_status().json()
        values = {o["name"]: o["value"] for o in detail["observations"]}
        assert values["gpu_hours"] == h and values["walltime_sec"] / 3600 == t
        claims = client.get(base + "/claims?team=manai").raise_for_status().json()
        assert claims["recoverable_gpu_hours"]["point"] == initial["recovery"]["gpu_hours"]["point"]
        if name in {"failure", "unknown_price", "validation"}:
            reply = client.post(base + "/chat", json={"client_request_id": "chat-" + name, "question": "What could go wrong?"}).raise_for_status().json()
            validate("Explanation", reply)
            assert reply["status"] == "ok" and eid in reply["supporting_evidence_ids"]
            assert "Single-job" in reply["answer"] and p["mode"] in reply["answer"]
            if name == "unknown_price": assert "added CPU reference cost unknown" in reply["answer"]
            if name == "failure": assert f"{r['net_reference_value_usd']:.6f}" in reply["answer"]
        audits.append(a)
    assert client.get("/api/audits/" + initial["audit_id"]).json() == initial
    bad = copy.deepcopy(request)
    bad["scenario"]["cpu_pilot"]["baseline_evidence_id"] = "not-in-audit"
    assert client.post("/api/audits", json=bad).status_code == 404
    bad["scenario"]["cpu_pilot"] = {**pilot, "trial_cap_hours": 0}
    assert client.post("/api/audits", json=bad).status_code == 422
    (output / "cpu-pilot-audits.json").write_text(json.dumps(audits, indent=2))
    print(json.dumps({"contract": "0.4", "live_cases": 8, "result": "PASS", "memory_partition": "independently reconciled",
                      "claims_unchanged": True, "baseline_resolves": True, "M02_M03_cpu_downside": "3 live MCP cases PASS",
                      "cpu_compatibility_verified": False, "realized_savings_verified": False}, indent=2))


if __name__ == "__main__": main()
