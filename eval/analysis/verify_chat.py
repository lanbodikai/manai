"""Live MCP route checks; UI and B-owned C-failure acceptance remain separate."""
import json
from pathlib import Path
import httpx
from service.analysis_routes import validate


def main():
    client = httpx.Client(base_url="http://127.0.0.1:8001", timeout=15)
    output = Path("private-eval/analysis")
    audit = json.loads((output / "audit.json").read_text())
    base = "/api/audits/" + audit["audit_id"]
    claims_before = client.get(base + "/claims?team=manai").raise_for_status().json()
    results = []
    for q in ("Why this pilot?", "Which jobs are eligible?", "What are the recovery assumptions?", "What could go wrong?"):
        reply = client.post(base + "/chat", json={"client_request_id": "live-" + str(len(results)), "question": q}).raise_for_status().json()
        validate("Explanation", reply)
        assert reply["status"] == "ok" and reply["audit_id"] == audit["audit_id"]
        assert 0 < reply["usage"]["tool_calls"] <= 3 and reply["usage"]["latency_ms"] < 10000
        assert reply["usage"]["model"] is None and reply["usage"]["provider"] is None
        assert len(reply["tool_trace_ids"]) == reply["usage"]["tool_calls"]
        for tid in reply["tool_trace_ids"]:
            trace = json.loads((Path("private-eval/base-chat") / (tid + ".json")).read_text())
            assert trace["audit_id"] == audit["audit_id"] and trace["transport"] == "official stdio MCP"
        for eid in reply["supporting_evidence_ids"]:
            detail = client.get(base + "/evidence/" + eid).raise_for_status().json()
            validate("EvidenceDetail", detail)
        results.append(reply)
    unsupported = client.post(base + "/chat", json={"client_request_id": "unsupported", "question": "Guarantee CPU compatibility and cash savings"}).raise_for_status().json()
    assert unsupported["status"] == "insufficient_evidence" and not unsupported["supporting_evidence_ids"]
    assert client.post(base + "/chat", json={"client_request_id": "blank", "question": "   "}).status_code == 422
    assert client.post(base + "/explanations", json={"client_request_id": "optional", "question": "Why this pilot?"}).status_code == 503
    after = client.post(base + "/chat", json={"client_request_id": "after-c", "question": "Why this pilot?"}).raise_for_status().json()
    assert after["status"] == "ok"
    assert client.get(base + "/claims?team=manai").json() == claims_before
    (output / "chat-results.json").write_text(json.dumps(results + [unsupported, after], indent=2))
    print(json.dumps({"live_supported_questions": len(results), "actual_mcp_calls": sum(r["usage"]["tool_calls"] for r in results) + after["usage"]["tool_calls"],
                      "latency_ms": [round(r["usage"]["latency_ms"]) for r in results],
                      "citations_resolve": True, "claims_unchanged": True, "C_absent": True,
                      "M01": "service PASS; UI pending B", "M02": "PASS live supported classes and uncertainty",
                      "M03": "synthetic failure tests separate", "M04": "absent-C service PASS; B crash/hang/malformed integration pending"}, indent=2))


if __name__ == "__main__": main()
