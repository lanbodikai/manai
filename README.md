# manai — planning draft v0.7

Status: DISCUSSION DRAFT. Track, thesis, first cohort, stack and agent role approved; implementation has not started.

Build a complete GPU-efficiency decision dashboard around one verified recommendation: audit proposed savings, expose supporting evidence, and show the downside of acting on uncertain assumptions.

## Start here

1. [Decisions and confirmed requirements](docs/DECISIONS.md)
2. [Short thesis](docs/THESIS.md)
3. [Questions for the next discussion](docs/QUESTIONS.md)
4. [Engineering roadmap and split gate](docs/ROADMAP.md)
5. [Official starter import plan](docs/UPSTREAM.md)
6. [Shared function/data contract](docs/CONTRACT.md), [frontend/backend API](docs/API_SPEC.md), and [OpenAPI schema](contracts/openapi.json)
7. [Tests and evaluations](docs/EVALUATION.md)
8. [Workstream A — analysis and audit service](docs/workstreams/A_ANALYSIS_SERVICE.md)
9. [Workstream B — dashboard and integration](docs/workstreams/B_PRODUCT_INTEGRATION.md)
10. [Workstream C — MCP evidence-review service](docs/workstreams/C_EVIDENCE_REVIEW_SERVICE.md)
11. [Codex handoff](docs/CODEX_HANDOFF.md)

Read [AGENTS.md](AGENTS.md) before editing. Every builder starts from the same approved plan version and contract version. Plans, interfaces, fixtures and thresholds below are proposals unless marked CONFIRMED or DECIDED.

## Present state

- Existing empty local clone: `C:\Users\05mus\manai`; origin `https://github.com/lanbodikai/manai.git`.
- Planning documents only. No starter imported, dependencies installed, dataset downloaded, implementation tested, or measured savings established in this repository.
- No application run command exists yet. Proposed final command: `docker compose up`; dashboard on port 3000.
- Three builder sessions are intended: A analysis, B product/integration, C evidence-review service. Do not start them until the split gate is satisfied.
- Public source snapshot reviewed: official commit `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`.

## Versioning

v0.1 records Round 1; v0.2 records Round 2 and the explicit starter/notice checklist; v0.3 records B as merge coordinator and environment readiness limits; v0.4 defines the reviewable frontend/backend API and synthetic examples; v0.6 adds the third participant and separates the explanation service. Each discussion revision updates [CHANGELOG.md](CHANGELOG.md), decision IDs and the handoff version. Commit each coherent revision locally. Publishing or opening PRs is a separate step from this initial planning draft.

The 3 PM PDT September 17 deadline is fixed. Recalculate time remaining before execution; do not reuse a stale clock-based schedule from the briefing.

## Base guarantee

The A+B product must work without C. The reviewer is an optional, profile-isolated enhancement. Default startup needs no LLM key and must not build C. Dashboard, audit, downside, deterministic evidence summary, drill-down claims export and a minimal live MCP chatbot remain available when C is disabled or fails.

## Slide alignment

See [requirement-to-deliverable matrix](docs/REQUIREMENTS.md). Plan v0.6 makes the minimum MCP chatbot part of A+B; C adds richer review. A static summary alone does not meet our slide-aligned completion gate. Contract v0.3 adds the independent `/api/audits/{audit_id}/chat` endpoint. No implementation has started.

## Official Track 2 cross-check

[Review and corrections](docs/TRACK2_REVIEW.md): exact cohort confirmed; split gate includes live API/MCP verification; final range basis is a required check; base chat versus optional reviewer wording reconciled. Plan v0.7; API contract stays v0.3. Documentation only, runtime checks remain NOT RUN.
