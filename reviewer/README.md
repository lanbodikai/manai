# Optional evidence validation (Workstream C)

C reads A's immutable audit and evidence over HTTP, independently checks selected
claims, and returns a review at the existing explanations endpoint. It cannot
create audits, change claims, move workloads, or run arbitrary tools. A/B never
import this package and their required `/chat` remains their responsibility.

**Current boundary:** the starting `main` commit `ce6a44e` has placeholder A
audit/evidence routes. A successful real A→C audit test is therefore pending.
Synthetic fixture tests are clearly labelled; they are not production evidence.
The real official MCP subprocess can retrieve `price_book`. That reference
metadata does not verify a cohort or establish matching data fingerprints.

## Local run

Use Python 3.12 from the repository root, in a separate environment:

```sh
python3.12 -m venv reviewer/.venv
reviewer/.venv/bin/python -m pip install -r reviewer/requirements.lock.txt
ANALYSIS_URL=http://127.0.0.1:8001 reviewer/.venv/bin/python -m uvicorn reviewer.main:app --port 8002
```

Windows: use `reviewer\.venv\Scripts\python.exe` and set environment variables in
PowerShell before running. The base needs no reviewer installation.

```sh
curl http://127.0.0.1:8002/health
curl -X POST http://127.0.0.1:8002/api/audits/AUDIT_ID/explanations \
  -H 'Content-Type: application/json' \
  -d '{"client_request_id":"review-1","question":"Validate the evidence and explain the downside risk."}'
python -m reviewer.run_validation --audit-id AUDIT_ID --output reviewer/.private/review.json
```

The private JSON report has individual pass/fail/unknown checks, source IDs and
coverage. It is not a new public contract. Unknown data stays unknown; v0.3's
unquantified downside is a limitation rather than a false arithmetic failure.
An answer with failed/unknown checks is `insufficient_evidence`, even when some
checks pass. A reported arithmetic inconsistency does not rewrite A's result.

## Configuration

| Variable | Default / meaning |
|---|---|
| `ANALYSIS_URL` | `http://analysis:8001`; trusted server configuration only |
| `REVIEWER_MODE` | `deterministic`; opt into `model` explicitly |
| `FEATHERLESS_BASE_URL` | `https://api.featherless.ai/v1` |
| `FEATHERLESS_API_KEY` | unset; server-side only, never passed to MCP |
| `REVIEWER_MODEL` | unset; explicit allowed provider model required in model mode |
| `REVIEWER_INPUT_USD_PER_MILLION` | unset; explicit current price assumption |
| `REVIEWER_OUTPUT_USD_PER_MILLION` | unset; explicit current price assumption |
| `REVIEWER_TIMEOUT_SECONDS` | 30 maximum for the entire request |
| `REVIEWER_MAX_EVIDENCE` | 100 maximum; truncation remains visible |
| `REVIEWER_MAX_PAGES` | 4 maximum |
| `REVIEWER_MCP_CONTEXT` | `price_only`; `rules` also retrieves CPU-placement rules/findings and available causal context |
| `REVIEWER_ENABLE_PROPOSED_V04` | `false`; read-only proposal validation, not contract promotion |

No credential is needed in deterministic mode. In model mode, missing setup is
503, an outage is 503, invalid model output is 502 and timeout is 504. There is no
silent fallback or paid retry. Unknown token counts/cost remain null; supplied
prices produce estimates, not provider invoices. Model mode makes at most one
provider request per review, bounded by the adapter's token and payload limits.

The model selects existing fact/check IDs and verification topics. It cannot
write free-form factual prose or new numeric values. The renderer quotes A's
values, labels independently expected values, always displays failed/unknown
checks, and proposes correctness/memory/runtime/rollback tests. This deliberately
limits flexibility. Relevance and usefulness still need live-model evaluation.

## Optional container (B owns integration)

```sh
docker build -f reviewer/Dockerfile -t manai-reviewer .
docker run --rm --network YOUR_BASE_NETWORK \
  -e ANALYSIS_URL=http://analysis:8001 -p 8002:8002 manai-reviewer
```

This is a separate image, not a second root Compose file. B may add it under
profile `reviewer`, proxy only the explanations POST, and leave every base service
independent of C. Never add `depends_on: reviewer` or provider variables required
at default startup. Use a browser timeout above 30 seconds (proposed 35), check
audit/request identity, and retain A's last result after errors. Official MCP is
copied unchanged into C's image. The currently used `price_book` needs no dataset;
The optional `rules` mode requires the verified five-file bundle mounted
read-only at `/app/data`; missing data returns an error. It uses a fixed read-only
tool plan, at most six operations. Context without matching source identity stays
uncorroborated, and cannot become an A evidence citation. Default `price_only`
mode proves tool connectivity and retrieves reference metadata only; it does not
complete the finding/causal integration gate.

## Tests and evaluations

```sh
python -m unittest discover -s tests/reviewer -p 'test_*.py' -v
python -m eval.agent.run --mode deterministic --output reviewer/.private/baseline.json
# Only after provider setup and spend approval:
python -m eval.agent.run --mode both --output reviewer/.private/comparison.json
```

The comparison uses the same eight synthetic cases three times per mode. Missing
provider setup records NOT RUN instead of a fabricated model score. Every actual
attempt is retained privately, including errors, latency and usage. G01–G05 are
mechanical numeric/citation/provenance/unknown/failure gates; not an unrestricted
semantic accuracy benchmark. Test-double MCP results are labelled separately from
the real stdio probe. See `eval/agent/RESULTS.md` and `reviewer/HANDOFF.md` for the
checks actually run and the uncompleted gates.

AI disclosure: this optional service, tests, evaluation runner and handoff docs
were generated and reviewed using OpenAI Codex. A human owner must review the PR.
No source rows, credentials or private provider traces are included in Git.
