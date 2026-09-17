# Shared contract v0.4 — adopted A/B CPU-pilot extension

Adoption: Winston confirmed B acceptance of the exact ce6a44e proposal; A accepted and recorded this in PR #2 before promotion. `contracts/openapi.json` now matches that proposal. Existing routes, Claims and Explanation shapes remain unchanged. Scenario optionally adds `cpu_pilot`; Downside requires nullable `cpu_pilot`; eligibility may include memory partitions. See contracts/proposals/v0.4/README.md for formulas and units. Historical v0.3 discussion below describes the base; v0.4 adoption supersedes its pending-version statements. B must regenerate its strict client before deploying this branch.

Purpose: all three sessions can work against one original synthetic fixture and interface without sharing unfinished code. This is our contract, not MantisGrid's API schema.

## Types

- `EvidenceRef`: stable `id`, source kind (`job`, `gpu`, `finding`, `rule`), source ID, table/columns, join keys, sample/window, synthetic flag. References resolve locally; raw data are not sent to Git or silently to an external LLM.
- `Scenario`: selected cohort ID, recovery fractions `low <= point <= high` within [0,1], positive reference USD/GPU-hour, cancellation policy, explicit downside assumptions and units. Default recovery fractions remain unchosen until discussed/inspected.
- `AuditResult`: contract_version, recommendation_id, source recommendation ID if applicable, data fingerprint, sample/window, fact/judgment/synthetic labels; eligible unique jobs and hours; low/point/high recovery and USD values; assumptions; evidence IDs; excluded/overlapping counts; proposed owner role/action; downside; limitations. Distinguish source confidence from our confidence.
- `Explanation`: answer, supporting evidence IDs, counterevidence/limitations, tool trace IDs, model/provider, latency and token/cost fields if available, status (`ok`, `insufficient_evidence`, `unavailable`). Never invent missing cost or confidence.

`interval_kind=scenario` means sensitivity to assumptions, not a statistical confidence interval. Do not populate confidence probabilities without a defensible basis; schema permits omission. Counts may have exact zero; missing values are null/unknown, never silently zero.

## Functions — Builder A owns analysis/service/base chat; C owns enhanced explain_audit

| Signature (language-neutral) | Responsibility / failure behavior |
|---|---|
| `load_tables(data_dir) -> Tables` | Read required columns; validate keys/units; reject missing required files. |
| `fetch_source_context(client, recommendation_id) -> SourceContext` | Retrieve recommendation, referenced findings, rule and optional causal/neighbor evidence; paginate/cache; preserve provenance. |
| `select_cohort(tables, policy) -> Cohort` | Return unique eligible job IDs, raw measurement coverage, exclusions and eligibility evidence; no invented savings. |
| `audit_impacts(cohort, findings) -> ImpactAudit` | Map overlapping findings to physical jobs/cards; expose naive and deduplicated quantities only when same scope/unit. |
| `estimate_recovery(cohort, scenario) -> RecoveryEstimate` | Compute bounded scenario quantities, not probabilities or asserted actual savings. |
| `assess_downside(cohort, scenario) -> Downside` | Return assumed harm mechanisms/quantities with units; say unknown where no estimate is justified. |
| `build_audit(context, cohort, scenario) -> AuditResult` | One canonical result used by UI, agent and claims. |
| `resolve_evidence(ref_ids, bounds) -> EvidenceBundle` | Deterministic bounded retrieval; unknown ID fails explicitly. |
| `explain_audit(question, audit_id, tool_client, budget) -> Explanation` | Bounded MCP-backed evidence use; fixed call/time budget, explicit errors; never changes claims. |
| `export_claims(audit, team) -> Claims` | Map only investigated values to official schema; enforce low <= point <= high and unit consistency. |

Recovery model for the first version: `eligible_unique_gpu_hours * explicitly_assumed_recovery_fraction`. All recovery bounds must be between zero and eligible hours. Reference dollar values use the same price and bounds. This is a sensitivity model; a richer estimator requires a versioned contract change.

## Team service and UI boundary

Authoritative draft route/payload definitions are in [API_SPEC.md](API_SPEC.md) and [OpenAPI](../contracts/openapi.json). The v0.1 singular `/api/audit`, global evidence and global claims sketches are superseded by immutable audit-scoped routes in v0.3. Original synthetic fixtures now exist under `contracts/examples/`.

The first completed-job cohort fixes `cancelled_policy=exclude`; changing that requires a cohort/contract decision. Explanation success is `ok` or `insufficient_evidence`; provider unavailability and timeout use structured error responses rather than a fabricated successful explanation.

## Builder B components

`OverviewView`, `RecommendationList`, `AuditDetail`, `ScenarioControls`, `DownsidePanel`, `EvidenceDrawer`, `ExplainPanel`, `SubmissionStatus` (development-only if useful). UI formats numbers but does not independently recompute financial totals. Controls show loading/error/empty states; citations work without the agent.

## Freeze gate

Stack and cohort are approved. Before branching: verify precise column mappings against actual data, review the v0.3 OpenAPI schema and synthetic fixtures, agree rounding/display rules and have all three sessions acknowledge the same commit. The schema/examples exist and can be validated; the bootstrap health/overview service exists; full audit/chat APIs and generated TypeScript client remain workstream work.

## Base versus enhancement

The [A downside and A–C bridge](workstreams/A_C_DOWNSIDE_BRIDGE.md) defines the minimum content of existing `Audit.downside` fields and C's read-only use of them. Active API v0.3 is unchanged; qualitative downside with null money remains valid. The [proposed v0.4 extension](../contracts/proposals/v0.4/README.md) adds quantified single-job CPU scenarios for A/B agreement; no implementation or promotion is implied.

D11 makes C optional. Core routes, including the required minimal MCP chat, are implemented by A and served through B independently. Explanation request/response schemas remain the same when C is enabled; otherwise the route returns 503 with a clear unavailable state. See API_SPEC.md for profile and timeout behavior.

## Base chatbot — contract v0.3

`answer_base_chat(audit_id, request) -> Explanation` belongs to A. Use a bounded intent allowlist (support for this recommendation, rule eligibility, recovery assumptions, what could go wrong), call actual official MCP tools, verify audit/data identity, and render supported templates. Unsupported questions return `insufficient_evidence`; tool failures return structured errors. No provider key or C code is required. `POST /api/audits/{audit_id}/chat` uses existing ExplanationRequest/Explanation/Error shapes. B labels it "MCP evidence chatbot — template-based". Its source numbers remain A's canonical audit; source tool outputs are labeled fact/judgment/simulated. The separate `/explanations` endpoint is C's optional richer review.
