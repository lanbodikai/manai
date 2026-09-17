# Shared contract v0.2 — PROPOSED, freeze before split

Purpose: both sessions can work against one original synthetic fixture and interface without sharing unfinished code. This is our contract, not MantisGrid's API schema.

## Types

- `EvidenceRef`: stable `id`, source kind (`job`, `gpu`, `finding`, `rule`), source ID, table/columns, join keys, sample/window, synthetic flag. References resolve locally; raw data are not sent to Git or silently to an external LLM.
- `Scenario`: selected cohort ID, recovery fractions `low <= point <= high` within [0,1], positive reference USD/GPU-hour, cancellation policy, explicit downside assumptions and units. Default recovery fractions remain unchosen until discussed/inspected.
- `AuditResult`: contract_version, recommendation_id, source recommendation ID if applicable, data fingerprint, sample/window, fact/judgment/synthetic labels; eligible unique jobs and hours; low/point/high recovery and USD values; assumptions; evidence IDs; excluded/overlapping counts; proposed owner role/action; downside; limitations. Distinguish source confidence from our confidence.
- `Explanation`: answer, supporting evidence IDs, counterevidence/limitations, tool trace IDs, model/provider, latency and token/cost fields if available, status (`ok`, `insufficient_evidence`, `unavailable`). Never invent missing cost or confidence.

`interval_kind=scenario` means sensitivity to assumptions, not a statistical confidence interval. Do not populate confidence probabilities without a defensible basis; schema permits omission. Counts may have exact zero; missing values are null/unknown, never silently zero.

## Functions — Builder A owns implementations

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

Authoritative draft route/payload definitions are in [API_SPEC.md](API_SPEC.md) and [OpenAPI](../contracts/openapi.json). The v0.1 singular `/api/audit`, global evidence and global claims sketches are superseded by immutable audit-scoped routes in v0.2. Original synthetic fixtures now exist under `contracts/examples/`.

The first completed-job cohort fixes `cancelled_policy=exclude`; changing that requires a cohort/contract decision. Explanation success is `ok` or `insufficient_evidence`; provider unavailability and timeout use structured error responses rather than a fabricated successful explanation.

## Builder B components

`OverviewView`, `RecommendationList`, `AuditDetail`, `ScenarioControls`, `DownsidePanel`, `EvidenceDrawer`, `ExplainPanel`, `SubmissionStatus` (development-only if useful). UI formats numbers but does not independently recompute financial totals. Controls show loading/error/empty states; citations work without the agent.

## Freeze gate

Stack and cohort are approved. Before branching: verify precise column mappings against actual data, review the v0.2 OpenAPI schema and synthetic fixtures, agree rounding/display rules and have both sessions acknowledge the same commit. The schema/examples exist and can be validated; the API server and generated TypeScript client do not yet exist.
