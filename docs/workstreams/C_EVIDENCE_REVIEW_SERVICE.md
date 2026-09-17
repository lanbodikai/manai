# Workstream C — MCP evidence-review service

Plan v0.6 / API contract v0.3. Owner: third participant/session TBD. Status: NOT STARTED; activate only after the shared split gate.

## Mission and boundary

Deliver one independently runnable explanation service. It retrieves an immutable audit from A, calls the official MCP evidence tools, and explains support, uncertainty and counterevidence. It cannot change the cohort, compute the official financial totals, write claims or execute infrastructure actions.

## Owned paths

`agent/`, `reviewer/`, `reviewer/Dockerfile`, `tests/agent/`, `tests/reviewer/`, `eval/agent/`. A owns analysis/service/evidence/claims; B owns dashboard/root Compose/report and merge coordination. Shared contracts and imported `mcp_layer/` require review before edits.

## API and integration

Follow [A downside and A–C bridge](A_C_DOWNSIDE_BRIDGE.md): read A's complete downside and scenario, distinguish evidence from hypothetical harm, and return read-only explanation/challenge using the existing schemas. Do not replace A's downside or gate its availability on your review. After proposed v0.4 adoption, explain its single-job cost/delay fields, distinguishing failure from extra validation and retaining signed results/unknowns; Explanation wire shape is unchanged.

C serves `POST /api/audits/{audit_id}/explanations` on internal service `reviewer:8002`. B's same-origin proxy sends this route to C; other public `/api/*` routes go to A's `analysis:8001`. C calls A's read-only audit/evidence routes via `ANALYSIS_URL`; it never reads A's in-memory objects directly. An internal `GET /health` reports process, provider configuration and tool readiness without exposing secrets. Public health reports unconfigured or unavailable until C readiness is known, consistent with the schema.

Use the existing OpenAPI ExplanationRequest/Explanation/Error schemas and original fixtures. A restart may invalidate an audit; propagate the documented 404 and let the UI offer recomputation. If source data changed since the audit, return 409; never combine current evidence with a stale calculation silently.

## Function-level implementation plan

| Function | Responsibility |
|---|---|
| `fetch_audit(audit_id) -> Audit` | Retrieve A's frozen scenario/result and verify contract version. |
| `build_review_context(audit, question) -> ReviewContext` | Distinguish accounting facts, assumptions, pilot proposal and unmeasured effects. Bound context size. |
| `create_tool_client(config) -> MCPClient` | Launch/connect supplied MCP server by documented transport; preserve module name and read-only data mount. |
| `retrieve_support(context, client, budget) -> ToolEvidence` | Fetch relevant findings/rules and causal/neighbor results only when relevant; record tool trace and provenance. |
| `verify_source_compatibility(audit, evidence) -> Validation` | Match data version/synthetic labels; absent lineage is disclosed or rejected, not assumed aligned. |
| `review_question(question, context, evidence) -> DraftExplanation` | Produce a short supported answer plus counterevidence and limitations. |
| `validate_explanation(draft, audit, evidence) -> Explanation` | Check reference membership, numeric support and output shape; unsupported answer must be downgraded or regenerated within budget. |
| `explain_audit(audit_id, request) -> Explanation` | Orchestrate time/tool budget, error normalization, usage and immutable result identity. |

Use A/B's base chatbot and deterministic summary as the baseline; add richer live tool-using review. A canned summary can be a clearly labeled fallback but is not evidence of live MCP/LLM success. Provider is unresolved; accept server-side configuration and report unconfigured state honestly.

## Required eval

Own G01–G05 and the eight-case suite in EVALUATION.md. Repeat numeric, unsupported-claim and failure cases three times. Compare against deterministic summaries on identical inputs. Log all attempts, calls, model, tokens, latency and estimated cost when observable. Do not tune away failures by dropping difficult questions from the evaluation set.

Critical failure conditions: unsupported numeric claim, unresolved citation, synthetic-as-real statement, confident CPU compatibility claim without a pilot, missing-evidence fabrication, or altering A's result. No critical violation may remain in the final evaluated set. A deterministic validator reduces risk but is not proof of general semantic grounding.

## Completion contract

**C1 service slice:** real MCP connection works on an allowed environment; fetches one relevant tool result; A's audit lookup and 404/409 behavior work; Explanation/Error schema checks pass; explicit missing-provider/tool-down state; Dockerfile supplied to B. Original fixtures can unblock development but cannot satisfy the real tool-call condition.

**C2 agent slice:** G01–G05 pass including repetitions; proposed 6-call/30-second bound enforced; no claims mutation; data identity and citations preserved; B successfully exercises route from React; usage/limitations report supplied for final report.

## PR/merge

Branch `codex/evidence-review-service` from shared baseline, separate worktree. Publish only if active assignment authorizes it. Open draft C1 after the service boundary and failure states are testable. A reviews grounding/numeric integrity; B reviews API and container integration. B coordinates merge after relevant checks and review. C2 follows with the evaluation report; do not merge a tool-less mock as completed agent functionality.

Handoff: commit, internal port/routes, env variable names only, data mounts, actual tool calls, test/eval outcomes, failures and integration requirements. No credentials or raw source data in public artifacts.

## Independence requirement

C is optional. Supply a reviewer-profile service proposal to B, not a mandatory root startup dependency. Your failures must be bounded to the explanation request. Base release may proceed while C is unfinished; do not block A/B or replace their required minimal MCP chatbot or deterministic evidence summary. Coordinate R02–R05 injection tests with B.
