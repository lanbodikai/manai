# Optional Contract 0.4 evidence reviewer

C reads A's immutable audit and scoped evidence over HTTP, checks accounting and
CPU downside independently, and explains what remains uncertain. It never changes
A's audits/claims or executes workloads. A+B remain usable without C.

**Current state:** active Contract 0.4 is supported by default. The old proposed
v0.4 opt-in is removed; 0.3/unknown versions are rejected. The public Explanation
and Error formats and existing explanations route are unchanged. Deterministic
review is the default; live model evaluation is deferred by the user.

## Run

From this repository root, with Python 3.12:

```sh
python3.12 -m venv reviewer/.venv
reviewer/.venv/bin/python -m pip install -r reviewer/requirements.lock.txt
ANALYSIS_URL=http://127.0.0.1:8001 reviewer/.venv/bin/python -m uvicorn reviewer.main:app --host 127.0.0.1 --port 8002
```

On Windows use `reviewer\.venv\Scripts\python.exe` and set `ANALYSIS_URL` in
PowerShell. Point it at the actual A service or the same-origin A+B API; old
bootstrap/development ports may no longer serve A.

```sh
curl http://127.0.0.1:8002/health
curl -X POST http://127.0.0.1:8002/api/audits/AUDIT_ID/explanations \
  -H 'Content-Type: application/json' \
  -d '{"client_request_id":"review-1","question":"Review the evidence, CPU downside and recovery assumptions."}'
python -m reviewer.run_validation --audit-id AUDIT_ID --output reviewer/.private/review.json
```

`/health` reports process state, Contract 0.4, mode and last tool/source status; an
alive process is not proof of a successful review. Detailed JSON reports stay
private. Public answers group repeated checks without hiding any failed/unknown
category. A failed/unknown check returns `insufficient_evidence`, not a fabricated
approval. A valid arithmetic review can still have unknown coverage or lineage.

The selected CPU baseline is fetched first. The same detail is not fetched again
when pagination reaches it. Up to 100 distinct details / four pages are reviewed;
a targeted baseline outside those pages is counted separately. Whole-cohort
checks remain unknown if pagination is incomplete. Aggregates are diagnostics,
not extra jobs. Recorded GPU-hours and scheduler duration remain separate.

## Configuration

| Variable | Default / meaning |
|---|---|
| `ANALYSIS_URL` | `http://analysis:8001`; server configuration only |
| `REVIEWER_MODE` | `deterministic`; model support remains opt-in and unevaluated live |
| `REVIEWER_TIMEOUT_SECONDS` | 30 maximum for the whole request |
| `REVIEWER_MAX_EVIDENCE` | 100 maximum, including a directly fetched CPU baseline |
| `REVIEWER_MAX_PAGES` | 4 maximum; reaching the cap leaves partial coverage |
| `REVIEWER_MCP_CONTEXT` | `price_only`; `rules` remains optional and uncorroborated |
| `FEATHERLESS_BASE_URL` | Provider URL, used only in explicit model mode |
| `FEATHERLESS_API_KEY`, `REVIEWER_MODEL` | Unset; never required for deterministic review |
| `REVIEWER_INPUT_USD_PER_MILLION`, `REVIEWER_OUTPUT_USD_PER_MILLION` | Optional price assumptions, not actual invoices |

The obsolete `REVIEWER_ENABLE_PROPOSED_V04` variable has no effect; remove it from
old deployment recipes. There is no silent downgrade or automatic provider call.
Existing bounds remain: two concurrent reviews, at most six MCP operations,
15-second MCP startup/inspection inside the 30-second outer deadline. A retrieval
has its existing five-second budget. Failures return explicit 404/409/429/502/503/504
responses and do not replace canonical results.

Real `price_book` access proves MCP connectivity and reference metadata only. It
does not establish matching data lineage, audit-specific findings or CPU safety.
The optional `rules` mode requires the five-file bundle at `/app/data`, mounted
read-only; unknown identity stays unknown. A returned official finding is not
silently promoted to an audit citation.

## Independent validation

```sh
python -m unittest discover -s tests/reviewer -p 'test_*.py' -v
python -m unittest discover -s tests/bootstrap -p 'test_contract.py' -v
python -m eval.agent.run --mode deterministic --output reviewer/.private/deterministic.json
python -m eval.agent.http_smoke --output reviewer/.private/socket.json
# After building dashboard/dist, include the actual production proxy:
python -m eval.agent.http_smoke --dashboard-node /path/to/node22 --output reviewer/.private/proxy.json
python -m eval.agent.live_review --analysis-url http://127.0.0.1:3000 \
  --reviewer-url http://127.0.0.1:8002 --explanations-url http://127.0.0.1:3000 \
  --audit-id AUDIT_ID \
  --output reviewer/.private/real-a-review.json
```

The socket test starts actual A and C processes and uses real official MCP, but
its A data/context is explicitly synthetic. It exercises no-pilot and all eight
CPU scenarios; it does not pass canonical-data acceptance. `live_review` instead
reads a supplied audit from the team's actual A endpoint, checks every returned
citation and compares audit/claims before and after. It refuses model-mode C.
The optional `--explanations-url` is the public proxy origin; deterministic-mode
health is still checked directly on `--reviewer-url`. Without that option,
explanations also use the direct reviewer service.
Its exit code validates transport/schema/identity/non-mutation; inspect the
reported FAIL/UNKNOWN counts before making an evidence-quality claim.

Private outputs use exclusive creation: choose a new filename on a rerun. No
paid model evaluation is part of this phase. Existing provider adapter tests use
explicit test doubles only. See `eval/agent/RESULTS.md` for actual receipts.

## Container and B integration

```sh
docker build -f reviewer/Dockerfile -t manai-reviewer .
docker run --rm --network YOUR_BASE_NETWORK \
  -e ANALYSIS_URL=http://analysis:8001 -e REVIEWER_MODE=deterministic \
  -p 8002:8002 manai-reviewer
```

These are reproduction commands; this C update's image was not built on the Mac
because Docker is absent. C's image contains its runtime, active contracts and
unchanged official API/MCP files; it excludes evaluation test peers/private data.

B owns root Compose and proxy changes. Add C only under optional profile
`reviewer`; configure the existing production proxy with
`REVIEWER_URL=http://reviewer:8002`. PR #7 already includes this optional routing
and the 31-second proxy/35-second browser deadlines. Keep base startup
and readiness independent of C. Use a browser timeout above 30 seconds (35 seconds)
and lazy/optional routing so absent C cannot prevent startup. Run R01–R05 against
the actual merged product before enabling it. No new root Compose file is needed.

AI disclosure: C implementation/tests/docs were generated and reviewed with
OpenAI Codex. Human integration review remains required. No workload, rollback,
CPU compatibility or realized savings has been demonstrated.
