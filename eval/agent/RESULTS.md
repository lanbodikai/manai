# Contract 0.4 deterministic C verification — 2026-09-17

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
