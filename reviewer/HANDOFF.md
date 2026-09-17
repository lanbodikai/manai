# C handoff to A/B and the next executor

## Version and ownership

- Starting main: `ce6a44e2a2eb2e66c42cf7372ff2628164f930c5` (includes the verified bootstrap and the A/C downside proposal).
- New head branch: `codex/evidence-review-service` in a separate worktree.
- Core checks/adapters commit: `b52bab7`.
- Service/model/evaluation commit: `417902c`.
- This handoff is a following documentation commit; use `git rev-parse HEAD` for its exact current SHA.
- Active public contract: 0.3. Proposed 0.4 is read only behind `REVIEWER_ENABLE_PROPOSED_V04=true`; not promoted.
- All C-authored changes are under `reviewer/`, `tests/reviewer/`, `eval/agent/`. A/B, root Compose, shared contracts, claims and official API/MCP files were not edited.
- Requested draft PR target: `codex/integration`. At inspection it was `ee529ee`, behind main by existing commits `b42997d` and `ce6a44e`. The PR comparison may therefore show those inherited main documentation changes. They are not C-authored. B should align the integration baseline before merge, or explicitly agree on another target. C does not move shared branches or merge.
- Publication is currently blocked: HTTPS Git has no configured login, the SSH agent has no identities, and the connected GitHub integration rejects repository writes with HTTP 403. These commits are local only; no PR exists yet. The prepared PR description is [PR_DESCRIPTION.md](PR_DESCRIPTION.md). Authenticate Git or grant connector write access, then push only this new branch and create the draft. Do not claim that publishing succeeded.

## What works

`POST /api/audits/{audit_id}/explanations` reads A only through bounded GETs.
It validates schemas and scoped identity, independently checks evidence/units,
deduplication, arithmetic, coverage and proposed CPU downside, and returns the
existing Explanation/Error shape. Detailed internal reports contain assumptions,
pass/fail/unknown checks, expected versus observed values and next tests.

The deterministic mode has no provider requirement. Optional model mode makes one
bounded provider call to choose existing fact/check IDs and verification topics.
It cannot set outcomes, invent numeric prose, change canonical money or execute
actions. Failed/unknown checks and synthetic labels cannot be hidden by selection.
Keys stay server-side and are excluded from the MCP child environment and image.

Official MCP uses the unchanged stdio implementation. `price_only` provides a
working reference-metadata probe. `rules` uses fixed CPU-placement rule/finding
retrieval and conditional causal lookup, capped at six operations. No tool context
is silently joined to an A snapshot when lineage is unknown. There are no writes
to A, to the telemetry, or to infrastructure.

## Readiness and evidence

See [evaluation results](../eval/agent/RESULTS.md) for full PASS/FAIL/NOT RUN scope.

- **C1 code is implemented; full C1 acceptance remains incomplete.** 89 C tests,
  5 existing contract tests, 24 repeated deterministic cases and the final actual
  socket/real-MCP smoke test passed. The first cold MCP run timed out under the
  earlier 8s sub-budget; its receipt was retained, and the final 15s budget test
  passed within the 30s outer deadline. A real lookup against main correctly gives
  404. No positive real A audit exists in this baseline, so that gate is pending.
- **C2 adapter is implemented; live C2 evaluation is incomplete.** Mock-provider
  transport/guard tests pass, including the same eight cases repeated three times.
  The live comparison explicitly records 24 NOT RUN attempts. No provider key,
  model or spending authorization was available; no paid requests were made.
- **Data evidence is limited.** Two official prepared-table semantic hashes and
  twelve offline regression checks passed. They reproduce the previous cohort
  and memory partition; they do not prove a full five-file source gate, CPU
  compatibility, live causal corroboration or operational savings.
- **Docker, A-summary comparison and B's R01–R05 are NOT RUN.** This host has no
  Docker, and the starting A implementation is a bootstrap. The isolated Python
  install passed dependency checks. B must test its own proxy/profile behavior.

Public evaluation fixtures are invented. Actual source receipts and each failed
or successful local attempt stay in ignored `reviewer/.private/`; no source rows,
provider responses or secret values were committed.

## Run and configuration

Install `reviewer/requirements.lock.txt` into a separate Python 3.12 environment.
Run from the repo root:

```sh
ANALYSIS_URL=http://127.0.0.1:8001 python -m uvicorn reviewer.main:app --port 8002
python -m unittest discover -s tests/reviewer -p 'test_*.py' -v
python -m eval.agent.run --mode both --output reviewer/.private/new-comparison.json
```

Environment variable names only:
`ANALYSIS_URL`, `REVIEWER_MODE`, `REVIEWER_MCP_CONTEXT`,
`FEATHERLESS_BASE_URL`, `FEATHERLESS_API_KEY`, `REVIEWER_MODEL`,
`REVIEWER_INPUT_USD_PER_MILLION`, `REVIEWER_OUTPUT_USD_PER_MILLION`,
`REVIEWER_TIMEOUT_SECONDS`, `REVIEWER_MAX_EVIDENCE`, `REVIEWER_MAX_PAGES`,
`REVIEWER_ENABLE_PROPOSED_V04`.

Defaults, Docker commands and the proposed integration behavior are in
[reviewer README](README.md). A model key alone is not permission to spend: obtain
the selected model and an approved evaluation cap before the live comparison.
Absent configuration is an explicit error/NOT RUN, never a substituted answer.

## How A/B can benefit independently

[AB_IMPROVEMENT_PROPOSALS.md](AB_IMPROVEMENT_PROPOSALS.md) records reproducible
triggers, expectations, limits, owner changes and regressions. In particular:

1. A should supply the actual predicate observations and stable evidence scope.
2. A can reuse the independently hand-worked downside tests, especially H≠gT,
   additional testing versus replacement, null prices and negative net value.
3. A/B can prioritize pilots by memory evidence without changing broad eligibility.
4. B should keep unknowns, coverage and reference-versus-cash labels visible, and
   make C failure affect only the optional panel.

Adopted improvements belong in A/B and must remain available with C disabled.
C's findings do not block the base release or replace A/B's own tests.

## Next executor instructions

Continue this branch; verify the exact HEAD and clean tree before changes. Read
root AGENTS and C's workstream contract. Stay inside the same C-owned folders.
Request permission before shared-contract, A/B or root Compose edits.

First connect to A's completed immutable audit service and run a real positive
review with matching scoped evidence. Mount and verify all five organizer files
before enabling `rules`; preserve unknown source identity until a verifiable
mapping exists. Coordinate an A summary baseline and B's resilience tests.
Then, with approved provider setup/spend, run all eight cases identically for
deterministic and live-model modes, three repetitions, retaining every attempt.
Measure useful discrepancy detection, false alarms and human next-step clarity;
mechanical safety gates alone do not show model value.

Keep the PR draft until the affected acceptance gates actually pass. B owns merge.
Do not submit the event form, force-push shared history, alter the default branch,
or claim workload execution/savings. AI disclosure: this C implementation and
documentation were generated and reviewed using OpenAI Codex; human review is
required before integration.
