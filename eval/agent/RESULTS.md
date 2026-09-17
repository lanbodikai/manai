# Real-data execution preflight — 2026-09-17 20:35 UTC

**BLOCKED: integration-host access is unavailable from this Mac task.**
Network fetch confirms candidate `003ad777bb5ac275368bfc9e4a491b5fed29e11c`
and main `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9`; the main-version gate
passes. No Docker CLI/app/socket, configured Docker host or SSH alias is present.
The organizer-data host connection and dataset path are needed to continue.

The private 13012/18081/10.254.194.0/24 overlay passes static YAML assertions;
remote collision checks, Docker build/start, real audit/browser/MCP/citation/
claims checks and C restart are **NOT RUN**. No audit IDs or screenshots exist.
No deployment, provider call or change to main/production/PR #3 was made.
Full blocked handoff: `reviewer/REAL_HOST_HANDOFF.md`. Previous synthetic results
below remain synthetic; they were not rerun as a substitute for this host pass.

---

# Fresh-main isolated full-flow integration — 2026-09-17

Branch `codex/c-main-integration` starts from PR #8 main `a7087eb` and imports
C `846ee97` through merge `5325858`. Main and PR #3 were left untouched.
Tested files were committed as CSS fix `ff82dbf` and simulation/overlay
`91edaa74e7b1f44e41d01f6c900cc78240939dd9`. A/contract/runtime unchanged.

**PASS:** 123 Python tests (15 A + 4 base chat + 5 contract + 99 C), 56 dashboard
tests, production build/typecheck/mock exclusion, 24 deterministic evaluations,
and 4 existing browser regressions. Full simulation passed all four phases:
unconfigured C, full nine-review CPU journey, stopped C, and fault peer with
503/malformed/wrong-audit/actual proxy deadline. Real MCP calls serve both base
chat and C; no model/provider calls. Evidence resolves and claims/audits remain
unchanged after reviews and C faults. Synthetic claims/schema/live-URL checker
passes with 3/10 categories and the expected no-confidence warning.

The full flow uses invented on-disk source and actual source checksum/readiness,
API, A, C, MCP, proxy and React implementations. A test-only wrapper changes
provenance labels; it does not bypass readiness or replace calculations. The
Data explorer snapshot was not prepared or claimed tested. Docker, official
organizer-data and complete Compose R01–R05 remain pending. Optional-profile
configuration was checked statically only.

Initial runs 1–3 stopped on the same actual mobile overflow (483px content in
390px viewport); logs/diagnostic screenshots retained. Four CSS lines let long
answer identifiers wrap and preserve paragraphs. Full run 4 passes at 390px.
Private receipt: `reviewer/.private/full-flow-4/receipt.json`; its pre-commit head
is `5325858`, with the tested additions subsequently committed unchanged above.
The desktop/mobile result was also visually inspected.

Additional commands beyond PR #8 commands below:

```sh
python -m unittest discover -s tests/analysis -p 'test_*.py'
python -m unittest discover -s tests/base_chat -p 'test_*.py'
python -m eval.agent.run --mode deterministic --output reviewer/.private/integration-deterministic.json
# In dashboard, with Node 22 on PATH:
PLAYWRIGHT_CHANNEL=chrome MANAI_TEST_MOCK_PORT=19300 MANAI_TEST_HTTP_PORT=19301 CI=1 npm run test:browser -- --grep 'reviewer|live entry'
# From repository root after production build:
python -m eval.agent.full_flow --node /path/to/node22 --output-dir reviewer/.private/full-flow-4
python -m compileall -q eval/agent reviewer
python -m pip check
git diff --check
```

The supplied runner cleans up only processes it started and retains private
receipts. No other checkout was changed. See `reviewer/INTEGRATION_STOP.md` for
exact revisions, reproducible startup and the requested 15-minute stopping point.

---

# PR #8 merged-main compatibility — 2026-09-17

Latest tested main: `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9` (PR #8).
Conflict-free C merge/tested tree: `f16f7b370c4813a8cb431e26fd5d540b19406cb1`.
A source remains `adfcd883edebfd8b7100179ab545cc4000fca479`; contract 0.4.
This section supersedes the PR #7 current-baseline statements below.

PR #8 changes B's CFO views, client contract guard, configurable API origin and
chat retry. No changes to A, C runtime, shared contracts, official API/MCP,
production server/Compose or package lock. C sync required no runtime fixes.
A/B-owned files remain identical to main in C's checkout.

| Repeated check on PR #8 | Result and boundary |
|---|---|
| Reviewer / active contract | **99/99 + 5/5 PASS** |
| Deterministic eval | **24/24 PASS**, eight cases × three, `pr8-deterministic.json` |
| Dashboard unit / production build | **56/56 PASS**, TypeScript and mock-exclusion PASS; existing bundle-size warning only |
| Actual production proxy → A/C | **9/9 PASS**, 18 actual MCP operations; immutable audit/claims, resolving citations, CPU oracles and zero false FAILs. Original synthetic A inputs/readiness; `pr8-proxy.json`. |
| Missing audit / stopped C | Six checks PASS: missing-audit 404, C-unavailable 503, unchanged base audit/claims, healthy A and available dashboard page |
| Browser reviewer failure regressions | **3/3 PASS** in Chrome; explicit demo unavailable/timeout/malformed doubles. Not canonical-data UI or full real-timeout acceptance. |
| Scope/diff | PASS; no A/B file edits beyond imported main, zero provider calls |

Commands: same Python 3.12.14 and Node 22.14.0 environments as PR #7 below.

```sh
python -m unittest discover -s tests/reviewer -p 'test_*.py'
python -m unittest discover -s tests/bootstrap -p 'test_contract.py'
python -m eval.agent.run --mode deterministic --output reviewer/.private/pr8-deterministic.json
cd dashboard
npm test
VITE_DATASET_API_ENABLED=true npm run build
PLAYWRIGHT_CHANNEL=chrome MANAI_TEST_MOCK_PORT=19300 MANAI_TEST_HTTP_PORT=19301 CI=1 npm run test:browser -- --grep reviewer
cd ..
python -m eval.agent.http_smoke --dashboard-node /path/to/node22 --output reviewer/.private/pr8-proxy.json
git diff --check
git diff origin/main --exit-code -- analysis service contracts dashboard docker-compose.yml
```

No reinstall was needed: the dependency lock did not change. Direct-only sockets
were not repeated separately; the updated run passes through the actual production
proxy. Real-data Docker/image and full combined UI/Compose R01–R05 remain pending
on the integration host. Previous receipts below retain their original scope;
PR #8's separate B-host receipt does not certify this C image. C stays draft and
disabled. Review baseline is now PR #8, not PR #7.

---

# PR #7 merged-main compatibility — 2026-09-17

Main `610f89d8d2b4b9c1aa07b7e2c12087ec4849adeb` merged into the existing C
branch without conflicts at `c5a9f5d98da0c53d9c6f5d0b7709d202726f1926`.
Tested C/harness: `a32af3e671a0ccd0a3f2c55c58e495f20b3a016b`; A runtime still
`adfcd883edebfd8b7100179ab545cc4000fca479`. Active contract: 0.4.
No C runtime compatibility fixes or A/B-owned edits were necessary. Subsequent
handoff edits are documentation-only. This section supersedes earlier next-base
and unrun-proxy statements; historical receipts below remain scoped to their runs.

| Check on merged tree | Result and scope |
|---|---|
| Reviewer regression / active contract | **99/99 + 5/5 PASS** |
| Deterministic eval | **24/24 PASS**, eight cases × three; `pr7-deterministic.json` |
| Direct A→C sockets | **9/9 PASS**, 18 actual MCP operations; `pr7-socket.json` |
| Actual production B proxy → A/C | **9/9 PASS**, 18 additional actual MCP operations; `pr7-proxy.json`. Audit identity, resolving citations, unchanged audits/claims, CPU oracles and zero false FAILs verified. Original synthetic A source context; not canonical-data acceptance. |
| C process stopped | Production proxy returns `503 AGENT_UNAVAILABLE`; A audit, claims, health and static dashboard remain available and unchanged. Six negative/base checks including missing-audit 404 passed. |
| Dashboard tests/build | **54/54 PASS**; TypeScript, production build and no-mock live-bundle check PASS. Existing >500 kB bundle warning only. |
| Browser reviewer-failure regressions | **3/3 PASS**, Chrome; unavailable/timeout/malformed explicit demo doubles. Base chat/evidence work and download stays enabled. No claim of actual full-timeout or canonical-data browser acceptance. |
| Python dependency/compile and diff scope | PASS; zero A/B runtime differences against merged main; no paid provider calls. |
| Still pending | Standalone Docker build/run, canonical five-file data review and combined real-data browser/Compose R01–R05 on the integration host. No C profile enabled. |

Commands from repository root, Python 3.12.14 environment and Node 22.14.0:

```sh
python -m unittest discover -s tests/reviewer -p 'test_*.py'
python -m unittest discover -s tests/bootstrap -p 'test_contract.py'
python -m eval.agent.run --mode deterministic --output reviewer/.private/pr7-deterministic.json
python -m eval.agent.http_smoke --output reviewer/.private/pr7-socket.json
cd dashboard
npm ci --ignore-scripts
npm test
VITE_DATASET_API_ENABLED=true npm run build
PLAYWRIGHT_CHANNEL=chrome MANAI_TEST_MOCK_PORT=19300 MANAI_TEST_HTTP_PORT=19301 CI=1 npm run test:browser -- --grep reviewer
cd ..
python -m eval.agent.http_smoke --dashboard-node /path/to/node22 --output reviewer/.private/pr7-proxy.json
python -m compileall -q reviewer eval/agent tests/reviewer
python -m pip check
git diff --check
```

Actual executables: `/private/tmp/manai-c-isolated/bin/python` and
`/private/tmp/node-v22.14.0-darwin-arm64/bin/node` (Node's bin on PATH for npm).
Receipts are private/ignored. Both socket runs preserve `insufficient_evidence`
for unknown MCP-to-audit lineage; passing transport/calculation checks does not
prove whole-source coverage or measured savings. PR #3 remains draft, targeting
`codex/integration` (same runtime tree as main).

Final fetch found documentation-only main `7197d03cd4b98813583e8eac86cd723417acfbb8`.
It merged cleanly at `cae5647efa36d6452543868e97fc91fa56fa0ec3`; the six imported
publication/handoff files change no tested runtime or contract. Tests were not
repeated for documentation alone. Independent human review and U05 remain
deferred as stated in the newly published main handoff.

Fresh environment check (`pr7-environment.json`): no Docker executable or Docker
app, no listener on local ports 3000/8000/8001/8002/18001, and generated resources,
edges and findings absent from the available source directory. These prevent
claiming canonical-data/container acceptance here.

---

# Earlier Contract 0.4 deterministic C verification — 2026-09-17

This record supersedes the earlier bootstrap-based current-state statements below.
Baseline integration: `db6f418f2cf4fb761eb560870814331b323eefd0`.
Tested A runtime source: `adfcd883edebfd8b7100179ab545cc4000fca479`.
C runtime: `ebdc00a` after `7fb356b`; test harness:
`e48e57edecd3fd6745387bbef2f9d894a6e95674`. Later handoff edits are documentation-only.
Runtime: isolated Python 3.12.14, unchanged reviewer dependency lock.

| Check | Actual result and limit |
|---|---|
| Reviewer regression | **99/99 PASS**; includes ten new v0.4 unit/aggregate, targeted baseline, deduplication, cap, missing/wrong evidence and grouped-output cases. Existing mocked model tests remain mock-only. |
| Active contract tests | **5/5 PASS**, using inherited bootstrap contract tests. |
| Deterministic evaluation | **24/24 PASS**, eight cases repeated three times. Synthetic HTTP/MCP doubles are explicit; private final receipt `v04-deterministic-final.json`. |
| Actual A→C HTTP sockets | **9/9 PASS**, no-pilot plus eight CPU scenarios. Both services run as real processes; A's source context/readiness is explicitly replaced with original synthetic data by the C-owned test peer. This does not verify organizer telemetry. |
| MCP in socket run | **18 actual operations** (two per review); no provider calls, resolving A citations, unchanged audit/claims, zero false FAIL results. Unknown source lineage remains visible. Receipt `v04-socket-1.json`. |
| Negative/failure cases | Actual socket missing audit gives 404. Regression suite covers normalized 409, A/MCP unavailable, malformed responses, identity conflicts, bounded timeouts, slot cleanup and unsupported versions. |
| Arithmetic | All eight hand-worked CPU cases plus H≠gT, failure double-charge mutation, negative values and unknown prices/delays pass. A and C compare independently; C does not import A's calculators. Only the isolated evaluation peer invokes actual A code. |
| Packaging/dependency inspection | Python compile and `pip check` PASS; C diff restricted to reviewer/tests/evaluation. Image definition unchanged; excludes test peer/private data. **Image build/run NOT RUN: Docker absent on this Mac.** |
| Canonical real-data A→C review | **NOT RUN** at this C revision. No local A endpoint is reachable; three generated canonical files are absent. The new read-only `live_review` runner is supplied for B's host. |
| Final merged-A+B proxy/React/R01–R05 | **NOT RUN in this C pass**. B owns integration. Do not substitute old C or fixture-only checks. |
| Live model/G semantic evaluation | **DEFERRED by user**. Zero paid provider calls. Deterministic fixture checks do not establish live model quality. |
| Workload replay/rollback/savings | **NOT RUN**; no workload execution exists in C. |

Commands actually run from repository root (the isolated interpreter was
`/private/tmp/manai-c-isolated/bin/python`):

```sh
python -m unittest discover -s tests/reviewer -p 'test_*.py'
python -m unittest discover -s tests/bootstrap -p 'test_contract.py'
python -m eval.agent.run --mode deterministic --output reviewer/.private/v04-deterministic-final.json
python -m eval.agent.http_smoke --output reviewer/.private/v04-socket-1.json
python -m compileall -q reviewer eval/agent tests/reviewer
python -m pip check
git diff --check
```

Actual socket replies were 3,357–4,555 characters. With complete synthetic
pagination, no-pilot had 46 PASS / 0 FAIL / 2 UNKNOWN; each CPU case had
72 PASS / 0 FAIL / 1 UNKNOWN. HTTP 200 plus `insufficient_evidence` is expected
because `price_only` does not corroborate an audit fingerprint. It must not be
changed to an all-clear solely to satisfy a test.

The first adoption run found eight fixture errors and one assertion failure:
active evidence examples have a different audit ID from the no-pilot fixture.
C-owned fixture builders were corrected to use matching audit identity, preserving
strict validation; 89/89 then passed. The later compatibility suite passed 99/99.
Initial failed logs and all evaluation receipts remain private; none were erased.
A default-sandbox Git fetch failed DNS, then the authorized network fetch succeeded;
the baseline was confirmed unchanged. No failed checks were silently waived.

`reviewer/.private/v04-environment.json` records Docker absence, local endpoint
connection failures and exact missing generated files. Only the two prepared
parquet files are available here. The pre-existing 12-check offline data receipt
below was not rerun or promoted into a five-file/current C acceptance result.

Current next base candidate observed: `codex/ab-validated` at
`5c4fd8376380b95ff09560ab7a688a5306ed5072`; shared integration is still `db6f418`.
C stays draft. Complete the merged-base checks from `reviewer/HANDOFF.md` on the
integration host before declaring deterministic enhancement integration complete.

---

## Historical receipt — pre-0.4 C baseline

# Part C evaluation receipt — 2026-09-17

Starting source: `ce6a44e2a2eb2e66c42cf7372ff2628164f930c5` on main.
Runtime: isolated Python 3.12 virtual environment, installed solely from
`reviewer/requirements.lock.txt`. No root/base dependency files were changed.

| Gate | Result | What was actually checked |
|---|---|---|
| Unit / integration-contract tests | PASS, 89 tests | Includes validator, HTTP/MCP adapters, model adapter and service. The two eight-case route sets run three repetitions each as subtests, not additional independent unit-test counts. |
| Existing bootstrap contract tests | PASS, 5 tests | Original tests run unchanged. This is not a Docker or base resilience test. |
| Eight-case deterministic evaluation | PASS, 24/24 attempts | Identical synthetic inputs, explicit HTTP/MCP test doubles. G01 checks source quotes plus hand-worked discrepancy values; G02 scoped citations; G03 mandatory synthetic labels; G04 unknowns; G05 bounded failures and no mutation. |
| Model adapter through service | PASS with mock provider | Eight cases × three repetitions; checks transport and rendering. Not model reasoning quality or a live provider result. |
| Live model comparison | NOT RUN, 24 attempts recorded as missing configuration | No provider key/model or spending approval supplied. No live model spend occurred. Unknown usage/cost is null. |
| Eight CPU downside cases | PASS | Original pre-existing synthetic 0.4 oracles; independent C arithmetic and mutations. Includes recorded H≠gT, signed values, unknowns and unchanged GPU baseline. |
| Real official MCP | PASS, limited scope | SDK stdio initialization, 13 advertised tools, `price_book`, 2 counted operations including list_tools. Reference GPU rate is metadata, not measured savings or audit corroboration. |
| Real rules/findings/causal integration | NOT RUN | Three generated source files absent locally. Fixed rules plan and malformed/down tools tested with explicit doubles only. |
| Socket HTTP → C → synthetic A peer + real MCP | PASS after a startup-timeout failure | First cold test returned bounded 504 under an 8s MCP deadline; separate live probe and second socket test passed. All receipts retained. Final socket test also passed after increasing MCP startup budget to 15s, still inside the overall 30s request limit. |
| Real HTTP lookup against main's A bootstrap | PASS for expected 404 | Confirms actual HTTP access and normalized AUDIT_NOT_FOUND; positive real audit validation is NOT RUN. |
| Previous real-data trial reproduction | PASS, 12/12 checks | Both prepared-table semantic hashes match pinned organizer hashes; historical cohort and memory partition reproduced. Independent offline check only; no source rows committed. |
| Full five-file source gate | NOT RUN | Prepared files verified; generated findings/resources/edges unavailable. |
| Comparison with A's completed deterministic summary | NOT RUN | Not implemented in this baseline. C's deterministic mode must not be presented as A's summary. |
| Docker build, root Compose, React R01–R05 | NOT RUN | Docker unavailable on this host; B owns integration. Standalone Python installation and actual local sockets tested. |
| CPU/GPU workload replay, rollback, realized savings | NOT RUN | Telemetry and scenario arithmetic cannot establish these outcomes. |

Reproduce from repo root after installing C's isolated dependencies:

```sh
python -m unittest discover -s tests/reviewer -p 'test_*.py' -v
python -m eval.agent.run --mode both --output reviewer/.private/comparison.json
python -m eval.agent.http_smoke --output reviewer/.private/http-smoke.json
python -m eval.agent.real_data_check --data /PRIVATE/PATH/TO/data --output reviewer/.private/offline-data.json
```

Private receipts include each attempt, source contract/fingerprint/version,
status, answer, calls, latency and nullable observed token/cost fields. Original
fixture identity is `synthetic-fixture-v1` / `fixture-v1`; it is never the real
five-file fingerprint. Output creation is exclusive: choose a new filename for
each rerun so failures cannot be silently overwritten. Model-mode reruns require
configuration and an approved spending limit; no retries or fallback hide failures.

No unsupported causal/CPU-compatibility claims or unresolved citations passed the
executed mechanical fixture gates. This statement is limited to those fixtures;
live-model usefulness, human next-step clarity and end-to-end real-data behavior
remain unmeasured. C1 and C2 are **not declared complete**.
