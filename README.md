# manai — planning draft v0.3

Status: DISCUSSION DRAFT. Track, thesis, first cohort, stack and agent role approved; implementation has not started.

Build a complete GPU-efficiency decision dashboard around one verified recommendation: audit proposed savings, expose supporting evidence, and show the downside of acting on uncertain assumptions.

## Start here

1. [Decisions and confirmed requirements](docs/DECISIONS.md)
2. [Short thesis](docs/THESIS.md)
3. [Questions for the next discussion](docs/QUESTIONS.md)
4. [Engineering roadmap and split gate](docs/ROADMAP.md)
5. [Official starter import plan](docs/UPSTREAM.md)
6. [Shared function/data contract](docs/CONTRACT.md)
7. [Tests and evaluations](docs/EVALUATION.md)
8. [Workstream A — analysis and agent](docs/workstreams/A_ANALYSIS_AGENT.md)
9. [Workstream B — dashboard and integration](docs/workstreams/B_PRODUCT_INTEGRATION.md)
10. [Codex handoff](docs/CODEX_HANDOFF.md)

Read [AGENTS.md](AGENTS.md) before editing. Every builder starts from the same approved plan version and contract version. Plans, interfaces, fixtures and thresholds below are proposals unless marked CONFIRMED or DECIDED.

## Present state

- Existing empty local clone: `C:\Users\05mus\manai`; origin `https://github.com/lanbodikai/manai.git`.
- Planning documents only. No starter imported, dependencies installed, dataset downloaded, implementation tested, or measured savings established in this repository.
- No application run command exists yet. Proposed final command: `docker compose up`; dashboard on port 3000.
- Two builder sessions are intended. Do not start them until the split gate is satisfied.
- Public source snapshot reviewed: official commit `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`.

## Versioning

v0.1 records Round 1; v0.2 records Round 2 and the explicit starter/notice checklist; v0.3 records B as merge coordinator and environment readiness limits. Each discussion revision updates [CHANGELOG.md](CHANGELOG.md), decision IDs and the handoff version. Commit each coherent revision locally. Publishing or opening PRs is a separate step from this initial planning draft.

The 3 PM PDT September 17 deadline is fixed. Recalculate time remaining before execution; do not reuse a stale clock-based schedule from the briefing.
