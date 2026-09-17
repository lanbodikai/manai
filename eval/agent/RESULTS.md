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
