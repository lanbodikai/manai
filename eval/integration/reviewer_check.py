"""Reproduce real A -> C compatibility; keep returned evidence/reviews local."""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def call(base, path, body=None):
    request = Request(base + path, data=None if body is None else json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=40) as reply: return reply.status, json.load(reply)
    except HTTPError as error:
        return error.code, json.load(error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", default="http://127.0.0.1:18001")
    parser.add_argument("--reviewer", default="http://127.0.0.1:18002")
    args = parser.parse_args()
    _, health = call(args.analysis, "/api/health")
    _, overview = call(args.analysis, "/api/overview")
    body = {"client_request_id": "c-compat", "expected_data_fingerprint": health["data_fingerprint"],
            "recommendation_id": "cpu-placement-pilot", "scenario": {
                "recovery_fraction": {"low": 0, "point": 0, "high": 1}, "usd_per_gpu_hour": overview["usd_per_gpu_hour"],
                "cancelled_policy": "exclude", "interval_kind": "scenario",
                "assumption_note": "Zero empirical recoverability; upper bound is eligibility ceiling."}}
    code, audit = call(args.analysis, "/api/audits", body)
    assert code == 201
    cursor, baseline = "", None
    while baseline is None:
        _, page = call(args.analysis, f"/api/audits/{audit['audit_id']}/evidence?limit=100" + ("&cursor=" + cursor if cursor else ""))
        for ref in page["items"]:
            if ref["kind"] == "job":
                _, detail = call(args.analysis, f"/api/audits/{audit['audit_id']}/evidence/{ref['id']}")
                values = {o["name"]: o["value"] for o in detail["observations"]}
                if values.get("walltime_sec", 0) > 0 and values.get("gpu_count", 0) > 0:
                    baseline = ref["id"]
                    break
        cursor = page["next_cursor"]
        if not cursor: break
    assert baseline
    receipts, summary = [], []
    for mode in [None, "replacement_success", "replacement_failure", "additional_validation"]:
        request = json.loads(json.dumps(body))
        if mode:
            request["scenario"]["cpu_pilot"] = {"mode": mode, "baseline_evidence_id": baseline,
                "cpu_vcpus": 4, "cpu_hours": 1, "cpu_vcpu_hour_usd": None, "extra_queue_hours": None,
                "trial_cap_hours": None, "baseline_host_costs_included": False,
                "assumption_note": "Hypothetical compatibility probe; no workload or model execution."}
        code, current = call(args.analysis, "/api/audits", request)
        assert code == 201
        root = "/api/audits/" + current["audit_id"]
        _, claims = call(args.analysis, root + "/claims?team=MANAI")
        code, review = call(args.reviewer, root + "/explanations", {"client_request_id": "c-check", "question": "Review CPU downside and evidence"})
        assert code == 200, (code, review)
        assert review["audit_id"] == current["audit_id"] and review["usage"]["tool_calls"] > 0
        assert call(args.analysis, root)[1] == current
        assert call(args.analysis, root + "/claims?team=MANAI")[1] == claims
        failures = [line for line in review["answer"].splitlines() if ": FAIL" in line]
        summary.append({"mode": mode or "no_pilot", "http": code, "status": review["status"],
                        "reported_failures": len(failures), "real_mcp_calls": review["usage"]["tool_calls"], "claims_unchanged": True})
        receipts.append({"mode": mode, "audit": current, "review": review})
    missing_code, _ = call(args.reviewer, "/api/audits/does-not-exist/explanations", {"client_request_id":"missing", "question":"Review evidence"})
    assert missing_code == 404
    out = Path("private-eval/integration")
    out.mkdir(parents=True, exist_ok=True)
    (out / "reviewer-private.json").write_text(json.dumps(receipts, indent=2))
    (out / "reviewer-summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"transport": "PASS", "missing_audit": missing_code, "cases": summary,
                      "enhancement_ready": False, "live_model": "NOT RUN"}, indent=2))


if __name__ == "__main__": main()
