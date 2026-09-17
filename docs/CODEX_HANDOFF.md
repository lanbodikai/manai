# Codex handoff — v0.6

## Planning continuation (use now)

Work in `C:\Users\05mus\manai`, origin `https://github.com/lanbodikai/manai.git`. Read AGENTS.md and README.md. The user approved Track 2, one verified recommendation, savings/evidence/downside thesis, completed zero-compute jobs, official Python API + React/TypeScript, dashboard-first MCP agent and three builder sessions with B coordinating merges and C owning the MCP reviewer service. Continue the unanswered environment/provider and phase-activation questions in Round 3 from docs/QUESTIONS.md; edit decisions and contracts through new local commits. No implementation/import/publishing has been activated. Do not replace the approved research question. The official source snapshot and known doc/schema conflicts are in docs/DECISIONS.md. Record exact tests as NOT RUN until executed.

## Builder A prompt (only after activation and split gate)

You own Workstream A at the agreed baseline commit. Read AGENTS.md, docs/THESIS.md, docs/CONTRACT.md, docs/API_SPEC.md, contracts/openapi.json, docs/EVALUATION.md and docs/workstreams/A_ANALYSIS_SERVICE.md. Implement deterministic analysis/audit/evidence/claims endpoints; C owns the bounded MCP agent. Preserve B and C ownership. Use original synthetic fixtures for tests and real local organizer data for validation. Start by reporting baseline commit, contract version and the first failing/missing acceptance condition. Submit A1/A2 in the documented order; do not claim causal savings or treat a proposed recovery fraction as measured. Publish only if the active assignment authorizes it. End each handoff with commits, actual checks/results, open assumptions and required B integration.

## Builder B prompt (only after activation and split gate)

You own Workstream B at the agreed baseline commit. Read AGENTS.md, docs/THESIS.md, docs/CONTRACT.md, docs/API_SPEC.md, contracts/openapi.json, docs/EVALUATION.md and docs/workstreams/B_PRODUCT_INTEGRATION.md. Build the entire dashboard journey against shared synthetic fixtures, then integrate A's canonical endpoints and C's explanation route. Preserve A's calculation ownership. Own compose/startup, interface states, report assembly and demo. Verify port 3000 and source-data mode; never use a mock to hide a failing integration. Submit B1/B2 as documented; publish only if the active assignment authorizes it. End each handoff with commits, run instructions, actual checks, blockers and readiness.

## Builder C prompt (only after activation and split gate)

You own the MCP evidence-review service. Read AGENTS.md, docs/CONTRACT.md, docs/API_SPEC.md, contracts/openapi.json, docs/EVALUATION.md and docs/workstreams/C_EVIDENCE_REVIEW_SERVICE.md. Implement only the reviewer component and its Dockerfile/tests. Read immutable audit/evidence over A's API; call the official MCP tools; never rewrite savings or claims. Validate grounding, budgets, source identity and unavailable states. B owns root Compose/proxy/integration. Start from the same approved baseline, use codex/evidence-review-service, and publish only if authorized. Handoff C1/C2 with actual tool-call and eval evidence.

## Session coordination

- No need to reread the old speculative HTML as requirements; official snapshot plus current decision ledger governs the plan.
- Before parallel work, assign owner names, agree contract version and create separate worktrees from the same baseline.
- Messages should identify contract/data versions and exact paths rather than “latest.” Share changed assumptions immediately.
- The integration lead maintains docs/DECISIONS.md and CHANGELOG.md; builders propose changes rather than independently rewriting them.
- If the context is compacted, preserve current phase, approved decisions, branch/commit, data fingerprint, remaining checks and unresolved questions. Do not restart completed work.
- Recalculate time until the 15:00 PDT cutoff on every major handoff. Stop optional features before sacrificing submission checks.

## Critical latest constraint

User explicitly requires base functionality even if the third split is unstable. C is optional and profile-isolated. A/B must deliver the complete deterministic flow without C or model keys; B verifies R01–R05. Do not let C's build, process, provider or response failure block the base. See D11 and API_SPEC.md.

## v0.6 slide-alignment override

Read REQUIREMENTS.md first. A implements minimal template-based chatbot using real official MCP calls at `/api/audits/{audit_id}/chat`; B supplies chat UI, base container/process wiring and M/R integration checks. C remains optional richer review at `/explanations`. A static summary alone is not complete. Contract is now v0.3. Show the 20% target and the audited contribution/unmet gap without inventing extra savings or extrapolating the sample. No code implementation/import is activated by this planning update.
