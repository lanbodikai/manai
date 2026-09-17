"""Actual loopback HTTP + official MCP; fixture and bootstrap outcomes separated."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

import httpx

ROOT = Path(__file__).resolve().parents[2]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def launch(module, port, env):
    child = subprocess.Popen([sys.executable, "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(port)],
                             cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return child


async def wait_ready(client, port, path):
    for _ in range(80):
        try:
            response = await client.get(f"http://127.0.0.1:{port}{path}")
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
        await asyncio.sleep(.1)
    raise RuntimeError("Local smoke-test server failed to start")


async def run():
    env = {key: os.environ[key] for key in ("PATH", "HOME", "SYSTEMROOT", "WINDIR", "TEMP", "TMP") if key in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", REVIEWER_MODE="deterministic", REVIEWER_MCP_CONTEXT="price_only")
    processes, result = [], {}
    try:
        async with httpx.AsyncClient(timeout=35, trust_env=False) as client:
            for label, module in [("synthetic_socket_peer", "eval.agent.fixture_server:app"), ("actual_main_bootstrap", "service.main:app")]:
                a_port, c_port = free_port(), free_port()
                processes.append(launch(module, a_port, env))
                await wait_ready(client, a_port, "/api/health")
                processes.append(launch("reviewer.main:app", c_port, {**env, "ANALYSIS_URL": f"http://127.0.0.1:{a_port}"}))
                await wait_ready(client, c_port, "/health")
                started = time.monotonic()
                response = await client.post(f"http://127.0.0.1:{c_port}/api/audits/synthetic-audit-001/explanations", json={"client_request_id": "socket-smoke", "question": "Validate the evidence and downside risk."})
                body = response.json()
                expected = 200 if label == "synthetic_socket_peer" else 404
                result[label] = {"http_status": response.status_code, "expected_status": expected,
                                 "pass": response.status_code == expected,
                                 "latency_ms": (time.monotonic()-started)*1000, "response": body}
            return result
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = asyncio.run(run())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    print(json.dumps({k: {field: v[field] for field in ("http_status", "expected_status", "pass")} for k, v in result.items()}))
    raise SystemExit(0 if all(v["pass"] for v in result.values()) else 1)


if __name__ == "__main__":
    main()
