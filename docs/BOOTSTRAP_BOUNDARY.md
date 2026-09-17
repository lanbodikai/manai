# Frozen bootstrap boundary — API v0.3

## What the common base implements

- Official API unchanged at api:8000, verified local data, and pinned tools/runtime.
- Team analysis service at analysis:8001: real GET /api/health and GET /api/overview; canonical semantic data fingerprint; missing/changed-data handling.
- GET /api/audits/{audit_id} returns structured 404 because no audit snapshots exist yet. Other unfinished team paths return explicit non-success. Optional /explanations returns 503 AGENT_UNAVAILABLE.
- A real stdio MCP connection utility and probe; no live user-facing chatbot yet.
- Temporary integration-check page at :3000 in tools/bootstrap/page/, outside B's dashboard/. It is not the final three-tile product.

## Ownership transfer at the verified baseline

| Owner | Files and duties |
|---|---|
| A | analysis/, service/ including inherited skeleton and MCP utility, base chat, analysis/base-chat tests, methodology and canonical final claims |
| B | dashboard/, root Compose and public proxy, UI/integration tests, final report/demo; replace the temporary page after equivalent checks pass |
| C | agent/, reviewer/, its Dockerfile/tests/evals; richer explanations only, optional profile |
| Shared review | contracts/, imported api/mcp_layer semantics, upstream dependency pins and data tooling |

API wire shapes, existing synthetic fixtures, same-origin /api routes, immutable audit IDs and error envelopes remain v0.3. No bootstrap changes to B's dashboard/ or the shared contract. Preserve the imported official requirements lock; the team service has its own resolved lock. A owns required /chat, C owns optional /explanations. C failures cannot make the final base depend on a model key.

Root Compose uses a configurable default subnet (`MANAI_SUBNET`, default 10.254.197.0/24) because the integration host's automatic Docker pools were exhausted. Use another unused subnet for a second concurrent checkout; do not prune other projects' networks. Do not change a running project's subnet without coordinating its restart.

## What is intentionally not done

Recovery estimation, deduplication audit, final claims/report, production dashboard, required base-chat behavior, optional model reviewer and their full T/D/U/P/M/R/G acceptance suites. Real source-cohort agreement establishes feasibility only, not CPU compatibility or saved money. Source causal tools describe the organizer's model, not an experimental proof of intervention effect.

## Branching and integration

Baseline is verified implementation commit `7530865eeca4fe87daf91b5cc275af378bd42fb7` (all BASE gates passed); subsequent status-only commits do not change its code. A/C branch from it on codex/analysis-service and codex/evidence-review-service. B retains codex/product-integration and merges that baseline, preserving B0 work. PR target: codex/integration. No force push or default-branch change. B coordinates reviewed slice merges after acceptance conditions pass.
