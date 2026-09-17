# Workstream A handoff

Branch: `codex/analysis-service`. PR: https://github.com/lanbodikai/manai/pull/2 targeting `codex/integration`. A1: `05c7fa0`. Resolve the final A2 revision from PR head; no merge or main push is authorized. Implementation baseline `7530865`, documentation/proposal handoff `ce6a44e`. Active contract **0.3**, official source `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`.

## Implemented and verified

Real health/overview/recommendations, immutable audit creation/read, scoped evidence pagination/detail, qualitative downside, claims export and template-based official MCP chat. Accounting, evidence, API and MCP checks are recorded with exact commands in `eval/analysis/RESULTS.md`. Methodology and limitations are in `docs/methodology.md`. A does not execute workloads or prove compatibility/savings.

Every audit includes source fingerprint, full scenario and immutable identity. The required chat uses two actual MCP calls, no model/provider, and the existing Explanation shape. Questions match B's four buttons. C remains optional. Root Compose and dashboard files were not modified.

## B integration

1. Review PR #2 at its current head, including source/contract tests. Merge only under lead authorization. Replace the temporary bootstrap page with the existing dashboard and route base `/api/*` to A. A's Dockerfile now includes analysis, chat and tests; no new dependencies are required.
2. For the current local witness, use `MANAI_ANALYSIS_URL=http://127.0.0.1:18001` with B's normal live frontend. The isolated A container reads canonical bootstrap data without modifying it. Actual audit IDs, source records and exported claims live in ignored `private-eval/analysis/`; audit IDs expire on container restart. Recreate via health fingerprint and POST /api/audits.
3. Use final recovery fractions low=0, point=0, high=1 and the official reference rate, explaining zero empirical CPU-recoverability evidence and the physical upper ceiling. Positive settings are exploratory. Do not silently use synthetic fixture fractions as a final claim.
4. Development browser witness passed matching display/export and real MCP, plus optional C unavailable/malformed/wrong-audit/hang injection. Reproduce in final Compose; finish U/P/R gates and REPORT matching the selected immutable audit. Correct the team recommendation's “Organizer judgment” label and explicitly label the headline high bound as eligibility ceiling.
5. Confirm the exact v0.4 proposal at ce6a44e in the coordination thread before A/B promote schemas and regenerate the strict client. Until then qualitative downside stays active; no CPU-pilot fields leak into v0.3. B's extra dataset/target-gap capabilities are separate proposals, not silently implemented by A.

## C integration

Read A's audit and audit-scoped evidence over HTTP. Cite resolvable references, preserve scenario/source identity and keep calculated values unchanged. Explain risks/assumptions/unknowns and proposed stop conditions; do not infer CPU compatibility, empirical probabilities or cash savings. The optional reviewer can fail without affecting base chat, downside, claims or evidence. G01–G05 remain C's responsibility.

## Publication limits

Source data, generated claims, private MCP traces and real screenshots remain local. Public fixtures are invented; official source notices are preserved. The final required root claims/report publication decision remains with the integration lead under organizer terms. Pending B agreement is a contract gate, not permission to claim v0.4 complete.
