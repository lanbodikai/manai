# Pilot & Recovery verification — 2026-09-17

Feature code: `2619b31` (A), `8176249` (B). Integration `5b0395b` preserves A's `db6f418` and B's latest reviewed `788b5ad`. Python 3.12 and Node 22.14.0; locked project dependencies. No provider key, C process or workload execution was used.

## Actual checks

| Check | Result | What it establishes |
| --- | --- | --- |
| Analysis tests | **44 passed**: 29 feature + 15 existing | Arithmetic, three outcomes, signed losses, caps, missing values, immutable inputs, schema, scoped source identity and routes. |
| Bootstrap tests | **5 passed** | Existing contract/readiness behavior under test fixtures. |
| Base-chat tests | **4 passed** | Existing unit behavior; tool calls are mocked here, not a new live MCP acceptance run. |
| Full dashboard suite after latest B merge | **87 passed**, 8 files, no skips | Existing B behavior plus adapter and component regressions. Includes the five actual HTTP cases below. Component tests use jsdom, not a graphical browser. |
| A routes → B adapter over local HTTP | **5 passed** | All three outcomes, cap override, unknown price/queue, audit/claims unchanged, no C calls. Repeated successfully after final fixture revision. |
| Production build | **Passed** | TypeScript, Vite and live-bundle exclusion of mock/fixture markers. Nonblocking warning: main JS chunk ~861 KB (~250 KB gzip). |
| Prepared-data sensitivity check | **1,389 outcome cases passed** over **463 historical baselines** | Two organizer-prepared tables match the pinned content hashes. Each baseline is checked against three invented trial outcomes; 926 cases reuse A's existing CPU calculator. This is not 1,389 workload runs. |
| Publication scope | **Passed scoped inspection** | No feature credential-pattern hits, source-data/archive additions or changes under `data/`; only README/checksum manifest remain tracked there. `git diff --check` passed. A scan does not prove universal absence of secrets. |

PR01–PR08 have deterministic coverage. PR09 has synthetic HTTP + mocked component coverage. PR10 has build coverage; Docker and visual/usability portions remain unverified.

The HTTP harness uses A's actual audit, evidence and pilot routers with an explicitly original synthetic context. Its invented job is included in the locally hashed jobs table. Other table placeholders and the prebuilt analysis context make this an integration harness, not verification of production source loading, upstream API/MCP, canonical five-file readiness or recovery execution. Every returned source is labelled synthetic. The harness refuses to stand in for production startup.

The prepared-data check independently selects completed jobs with both zero average and maximum GPU utilization and more than one recorded GPU-hour. It checks original cost against raw `gpu_hours × 2.5` and elapsed time against raw `walltime_sec / 3600`; it does not replace recorded GPU-hours with GPU count times duration. The two prepared tables are hashed, but the calculator check uses jobs only. GPU time-series behavior and the three generated files are not validated by this check. No source rows or derived per-job results are committed.

## Transparent illustrative outcome

The HTTP fixture is invented: original job 2 GPUs, 20 recorded GPU-hours, 10 elapsed hours, $50 reference cost. Assumed CPU trial: 4 vCPUs at $0.10/vCPU-hour; 12 hours on success or 3 hours before failure; zero setup/queue; comparable pricing boundary explicitly assumed.

| Outcome | Total cost to finish | Net benefit | Completion delay |
| --- | --- | --- | --- |
| Success | $4.80 | $45.20 | +2 hours |
| Failure + full original GPU rerun | $51.20 | −$1.20 | +3 hours |
| Failure + unavailable recovery | Unknown; $1.20 known cost so far | Unknown | Unknown; paused for owner action |

These are checked arithmetic examples, not actual bills, realized savings or evidence that a historical job is CPU-compatible.

## Reproduce

From the repository root in the documented Python environment:

```sh
python -m unittest discover -s tests/analysis -v
python -m unittest discover -s tests/bootstrap -v
python -m unittest discover -s tests/base_chat -v
python -m eval.pilot_recovery.verify_prepared --data-dir /path/to/organizer/track-2/data
```

The offline check needs only the two canonical prepared tables. It must not be used to mark A's five-file readiness gate ready.

Start the original synthetic HTTP harness in a separate terminal:

```sh
python -m eval.pilot_recovery.fixture_server
```

Then, with Node 22.14 available:

```sh
cd dashboard
npm ci
MANAI_PILOT_HTTP_URL=http://127.0.0.1:8121 npm test
npm run build
```

PowerShell: set `$env:MANAI_PILOT_HTTP_URL='http://127.0.0.1:8121'` before `npm test`. Without this environment variable, the five socket tests are explicitly skipped; do not report them as passed. The harness binds only to loopback and is excluded from the production service image.

## Issues found and resolved

- Unknown setup cost initially prevented a known CPU overspend stop. The simulator now applies the known CPU-cost ceiling while keeping total-budget status unverified; a regression covers it.
- Draft-only export initially lacked source scope. It now retains audit/source identity, including the synthetic flag, even before a simulation.
- B's prior adapter allowed nonfinite numbers and carried v0.3 assumptions against A v0.4. Strict number validation, regenerated types and the affected fixture tests now pass.
- Independent review caught an expected timing value taken from the calculator output. The prepared-data oracle now uses the raw source duration and rejects an empty checked cohort.
- Initial local HTTP rerun could not reach the loopback server under the tool sandbox. Rerunning with approved local network access passed. This was a test-environment access failure, not a hidden successful check.

## Not established; next owner

- **Docker clean startup / nginx proxy (P01): NOT RUN.** Docker/nginx runtime is unavailable on this host. B should provision canonical data, run the root Compose startup, verify :3000, simulate all outcomes and exercise unavailable A. Other service definitions were preserved; only the dashboard image wiring changed.
- **Graphical browser / narrow layout / keyboard / timed human task (U04/U05): NOT RUN.** Browser access was blocked because the administrative security-policy check was unavailable; it was not bypassed. B should complete desktop/mobile and keyboard review and a timed CFO explanation task.
- **Full real-source A integration / five canonical files (D01): NOT RUN here.** The local offline dataset contains the two prepared tables only. Keep the existing readiness gate; do not substitute the synthetic harness or weaken hashes.
- **Official final submission validation: not a feature release claim.** Canonical claims are unchanged; final claims, REPORT, demo and the public default branch remain the team's release responsibility.
- **Live MCP/C evaluations:** not rerun by this feature. Existing chat unit tests do not establish M01; stochastic G01–G05 are for the optional model reviewer, not this deterministic simulator.
- **Automatic recovery / real savings: NOT IMPLEMENTED OR VERIFIED.** Needs authorized scheduler controls, saved runnable configuration and inputs, reference-output checks, actual stop/budget enforcement, available original GPUs, durable/idempotent execution records, measured queue/billing, and failure-injection trials. Checkpoint use requires a separately demonstrated restoration test. Until then assume a full rerun or pause for the owner.

A+B review the feature; B coordinates root Compose verification and merges. C can later consume the evidence as an optional reviewer, but cannot alter the calculations or block this panel. Keep the PR draft until the outstanding integration checks and cross-review are complete.
