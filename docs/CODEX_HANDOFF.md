# Codex handoff — v0.3

## Planning continuation (use now)

Work in `C:\Users\05mus\manai`, origin `https://github.com/lanbodikai/manai.git`. Read AGENTS.md and README.md. The user approved Track 2, one verified recommendation, savings/evidence/downside thesis, completed zero-compute jobs, official Python API + React/TypeScript, dashboard-first MCP agent and two builder sessions with B coordinating merges. Continue the unanswered environment/provider and phase-activation questions in Round 3 from docs/QUESTIONS.md; edit decisions and contracts through new local commits. No implementation/import/publishing has been activated. Do not replace the approved research question. The official source snapshot and known doc/schema conflicts are in docs/DECISIONS.md. Record exact tests as NOT RUN until executed.

## Builder A prompt (only after activation and split gate)

You own Workstream A at the agreed baseline commit. Read AGENTS.md, docs/THESIS.md, docs/CONTRACT.md, docs/EVALUATION.md and docs/workstreams/A_ANALYSIS_AGENT.md. Implement the deterministic audit slice first, then the bounded MCP agent. Preserve Builder B's ownership. Use original synthetic fixtures for tests and real local organizer data for validation. Start by reporting baseline commit, contract version and the first failing/missing acceptance condition. Submit A1/A2 in the documented order; do not claim causal savings or treat a proposed recovery fraction as measured. Publish only if the active assignment authorizes it. End each handoff with commits, actual checks/results, open assumptions and required B integration.

## Builder B prompt (only after activation and split gate)

You own Workstream B at the agreed baseline commit. Read AGENTS.md, docs/THESIS.md, docs/CONTRACT.md, docs/EVALUATION.md and docs/workstreams/B_PRODUCT_INTEGRATION.md. Build the entire dashboard journey against shared synthetic fixtures, then integrate A's canonical endpoints. Preserve A's calculation ownership. Own compose/startup, interface states, report assembly and demo. Verify port 3000 and source-data mode; never use a mock to hide a failing integration. Submit B1/B2 as documented; publish only if the active assignment authorizes it. End each handoff with commits, run instructions, actual checks, blockers and readiness.

## Session coordination

- No need to reread the old speculative HTML as requirements; official snapshot plus current decision ledger governs the plan.
- Before parallel work, assign owner names, agree contract version and create separate worktrees from the same baseline.
- Messages should identify contract/data versions and exact paths rather than “latest.” Share changed assumptions immediately.
- The integration lead maintains docs/DECISIONS.md and CHANGELOG.md; builders propose changes rather than independently rewriting them.
- If the context is compacted, preserve current phase, approved decisions, branch/commit, data fingerprint, remaining checks and unresolved questions. Do not restart completed work.
- Recalculate time until the 15:00 PDT cutoff on every major handoff. Stop optional features before sacrificing submission checks.
