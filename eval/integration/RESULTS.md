# A+B integration execution — 2026-09-17

Shared baseline: `db6f418` (main/B history plus reviewed A `adfcd88`, PR #2 merged). Product work continues on PR #4, now targeting `codex/integration`. This is an execution record, not a claim of final submission readiness.

- A packaged regression: 15 analysis/API, 4 base-chat, 5 bootstrap tests PASS; v0.4 proposal equality/fixtures PASS.
- Reproduced D01–D05, A-side D06, eight CPU API cases, four supported live MCP classes, timeout/scope cleanup. D04 inspected privately; no source rows published.
- B integration: 50 unit tests, TypeScript, production build and eight synthetic/HTTP browser tests PASS. Live production browser on :13010 passed eight CPU scenarios, canonical claims agreement, actual MCP/citations and desktop/narrow inspection. Updated Compose startup on :3000 has healthy api/analysis/dashboard only; default services exclude C.
- Local-source regression initially 4/5 PASS, GPU pagination navigation failure under investigation. No failing check waived.
- C `d4fa017`: isolated Docker build and 89 tests PASS. Real A→C requests for no-pilot and all three CPU modes returned 200/insufficient_evidence, two actual MCP operations each, correct 404 for missing audit and unchanged A audit/claims. C reports false failures for aggregate evidence and has live-unit/baseline-coverage compatibility gaps. It is not enabled or merged. Live model evaluation NOT RUN.
- Pending: final Compose browser/fault/build-failure tests, P02, independent U05/cross-review, publication disposition for generated root claims, release approval and owner default-branch change.

Executable witnesses: `eval/integration/browser.cjs`, `reviewer_check.py`, `reviewer_stub.py`. Private receipts and real screenshots stay in ignored `private-eval/integration/`.
