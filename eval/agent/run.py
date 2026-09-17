"""Repeat identical eight-case fixtures for baseline and optional live model.

python -m eval.agent.run --mode deterministic --output reviewer/.private/eval.json
--mode both additionally attempts the configured provider; no fallback or retries.
"""
import argparse
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import time
import httpx

from eval.agent.cases import CASES, fixture, fixture_transport, FixtureMCP, grade
from reviewer.clients import AnalysisClient
from reviewer.main import create_app
from reviewer.settings import Settings


async def evaluate(mode, repeats):
    settings = Settings.from_env()
    rows = []
    for current in (["deterministic", "model"] if mode == "both" else [mode]):
        configured = current != "model" or bool(settings.provider_key and settings.model)
        for repeat in range(repeats):
            for name, question in CASES:
                audit, evidence = fixture(name)
                source = {"contract_version": audit["contract_version"], "data_fingerprint": audit["provenance"]["data_fingerprint"], "source_version": audit["provenance"]["source_version"]}
                if not configured:
                    rows.append(dict(mode=current, case=name, repeat=repeat, source=source, outcome="not_run_missing_provider_configuration", gates=None, usage=None))
                    continue
                before = json.dumps([audit, evidence], sort_keys=True)
                analysis = AnalysisClient("http://fixture-a", transport=fixture_transport(audit, evidence))
                app = create_app(replace(settings, mode=current), analysis=analysis, mcp=FixtureMCP(name == "tool_failure"))
                started = time.monotonic()
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://reviewer") as client:
                    response = await client.post(f"/api/audits/{audit['audit_id']}/explanations", json={"client_request_id": f"{current}-{name}-{repeat}", "question": question})
                body = response.json()
                gates = grade(name, response.status_code, body, audit, evidence, before)
                rows.append(dict(mode=current, case=name, repeat=repeat, source=source, outcome="pass" if all(v is not False for v in gates.values()) else "fail",
                                 gates=gates, http_status=response.status_code, response=body,
                                 usage=body.get("usage"), elapsed_ms=(time.monotonic()-started)*1000))
    return {"source": "original synthetic contract fixtures", "mcp": "explicit test double; see separate live probe",
            "limits": "Gates check mechanical safety; they do not certify semantic quality, real A integration, or workload outcomes.", "attempts": rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["deterministic", "model", "both"], default="deterministic")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not 1 <= args.repeats <= 3:
        p.error("repeats must be 1–3; changing the spend bound requires explicit review")
    result = asyncio.run(evaluate(args.mode, args.repeats))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    counts = {name: sum(a["outcome"] == name for a in result["attempts"]) for name in {a["outcome"] for a in result["attempts"]}}
    print(json.dumps(counts, sort_keys=True))
    raise SystemExit(1 if counts.get("fail") else 0)


if __name__ == "__main__":
    main()
