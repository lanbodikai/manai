# Workstream A — analysis and audit service

Plan v0.6 / Contract v0.3. Owner: Builder A/session TBD. NOT STARTED; wait for activation and shared split gate.

## Mission and ownership

Deliver one deterministic, reproducible audit from source data to cohort, recovery scenarios, downside and claims. Own `analysis/`, `service/`, `tests/analysis/`, `eval/analysis/`, and `docs/methodology.md`. Produce final root claims.json from the investigated audit. A also owns `service/base_chat/` and `tests/base_chat/`; C owns enhanced agent/reviewer; B owns dashboard/root Compose/report/integration. Shared contracts require review by affected owners.

## Functions and order

For the minimum downside analysis and its handoff to C/B, follow [A downside and A–C bridge](A_C_DOWNSIDE_BRIDGE.md). A owns the canonical risk, assumptions and pilot stop conditions; C is not required to produce them. Existing v0.3 fields support the qualitative fallback. The [v0.4 proposal](../../contracts/proposals/v0.4/README.md) adds structured CPU cost/delay and memory partitions for the next slice; agree it with B before implementation.

Read CONTRACT.md and API_SPEC.md. Implement `load_tables`, `fetch_source_context`, `select_cohort`, `audit_impacts`, `estimate_recovery`, `assess_downside`, `build_audit`, `resolve_evidence` and `export_claims`. Serve all public data/audit/evidence/claims routes on internal `analysis:8001`. Immutable audit IDs let B display and C explain the same result. Implement minimal `answer_base_chat`, `classify_supported_question`, `call_mcp_evidence`, and `render_supported_answer`; do not implement C's richer explanation logic or independently change the OpenAPI payloads.

First inspect actual columns/coverage; then determine exact eligibility, reconcile source overlaps, compute scenario bounds and preserve evidence. Use official tooling; do not rebuild ingestion. Unknown CPU compatibility stays unknown. A value is never measured merely because our service calculated it.

## Comparison and completion

Compare source recommendation and our audit using aligned cohort/price; decompose selection, overlap and recovery assumptions. If source cohort cannot be aligned, report that instead of claiming a correction.

**A1:** T01–T09 pass; real audit returned; D01–D04 recorded; evidence resolves; claims validate; data fingerprint and runtime logged. May merge without an agent if no agent success is advertised.

**A2:** D05 complete; C02/C03 and relevant C05/C06 API tests pass; B's displayed/exported numbers agree; C can retrieve immutable audit/evidence; methodology and limitations delivered; required live MCP chatbot passes M01–M04 without C or a model key. This replaces the earlier A2 agent responsibility, now C2.

Handoff: exact commit, endpoints, actual checks/results, source/contract versions, unresolved assumptions and required B/C integration. Real data and private review records stay local.

## PR/merge

Branch `codex/analysis-service` from the common baseline, separate worktree. Publish only if authorized. Draft A1 after a coherent computed endpoint and fixture work; mark ready after A1 gates. B reviews UI/claims consistency; C reviews evidence interface. B coordinates merge after relevant checks. A2 follows with integration evidence. Do not touch others' uncommitted files or push to main directly.

## Failure conditions

Missing eligibility measurements, canonical-data mismatch, unreproducible totals, mixed units, recovery bounds outside eligible allocation, unresolved licensing/publication constraint. Report precise blockers and continue synthetic tests; no fabricated data or unsupported savings.

## Official-doc review amendment — v0.7

Read ../TRACK2_REVIEW.md. A2 also requires D06 (defensible final range basis). CPU placement is already the official gpu-not-needed remedy; our added contribution is the audit and decision evidence. Confirm exact column/tool types against the running official /docs and MCP schemas. Use metadata join keys. No required interface change beyond API v0.3.
