# Workstream A — analysis, evidence and agent

Plan v0.1 / Contract v0.1. Owner: Builder A, person/session TBD. Status: NOT STARTED; activate only after ROADMAP split gate.

## Mission

Deliver one reproducible audit from source data to scenario estimate, with an evidence-grounded MCP explanation. The result is a decision input; it does not prove intervention savings.

## Owned paths

`analysis/`, `agent/`, `service/`, `tests/analysis/`, `tests/agent/`, `eval/`, `docs/methodology.md`. Produce canonical root `claims.json` only from the final investigated audit. B owns compose/dashboard/root report; send methodology and result references to B. Shared `contracts/` changes require joint agreement.

## Functions and order

1. `load_tables`, `fetch_source_context`: inspect actual columns/units, validate source fingerprint, use provided API/MCP/client rather than rebuilding collectors.
2. `select_cohort`: exact eligibility and missing-data policy; return evidence and exclusions.
3. `audit_impacts`: reconcile overlapping source findings at the proper grain.
4. `estimate_recovery`, `assess_downside`, `build_audit`: deterministic scenario model with explicit unmeasured fractions and risk assumptions.
5. `resolve_evidence`, `export_claims`: stable citations and one numeric source of truth.
6. Serve agreed `/api/*` routes using the frozen contract; keep original API untouched unless an evidenced compatibility fix is needed.
7. `explain_audit`: bounded agent actually calls supplied MCP tools, then uses audited results to explain support/counterevidence. LLM does not decide numeric totals or mutate claims.

Function signatures, response/error semantics and scenario boundaries are in CONTRACT.md; do not create a parallel schema.

## Required comparison

Compare source recommendation and audited estimate with aligned cohort/price. Decompose differences into selection, overlap and recovery assumptions. If source cohort is unrecoverable, state that comparison is not like-for-like; do not claim a measured correction. Compare agent answers to a deterministic evidence summary for grounding and usefulness.

## Completion contract

**A1 deterministic slice:** T01–T09 pass; one real audit available; D01–D04 recorded; evidence endpoints resolve; claims validate; runtime and data fingerprint logged. It can merge before the agent exists if no agent success is advertised.

**A2 agent slice:** G01–G05 and repeated cases pass; bounded tool/time behavior; real MCP use evidenced by logs; explicit unavailable state; D05 complete; methodological report supplied; no unsupported probabilities/causal/cash claims.

**Final handoff:** exact commit, endpoint examples, paths, actual checks and results, unresolved assumptions, setup instructions, known failures and what B must integrate. All real-data checks remain local unless permitted to publish.

## PR and merge

Branch `codex/analysis-agent` from common baseline, preferably its own worktree. When publishing is authorized, open draft A1 once a valid fixture and computed endpoint work. Mark ready only after A1 contract; B cross-reviews contract, duplicate accounting and claims/UI consistency. Integration lead merges after shared checks. A2 follows the same flow with agent evaluation evidence. Do not touch B's uncommitted files or push to main directly.

## Stop / escalate

No source evidence, no reliable eligibility fields, unexplained canonical-data mismatch, impossible bounds, or source-data redistribution ambiguity. Report the exact blocker and continue independent tests using original synthetic fixtures. Do not “fix” a blocker by fabricating rows or labeling a mock as a real result.
