# A1 verification record

2026-09-17. Active API 0.3; official source 314cca0bba49e1bb137aa9094d1dac4cdf7e4490; baseline 7530865 plus handoff ce6a44e. Source fingerprint: 62fa722b0909528e0c78fa5300064593d0090c0c0dc44012d11effb4fcbf0e2b.

| Checks | Actual outcome |
|---|---|
| T01–T09 | PASS in 8 synthetic analysis/API unittest methods. Invented data only. |
| C01–C03, A-owned C05/C06 | PASS: inherited fixtures; real and synthetic route shapes; immutable audit/claims, stale version, membership, pagination, request validation, eviction. Full B proxy/UI coverage remains pending. |
| D01 | PASS, all five canonical semantic hashes matched in isolated A container. |
| D02 | PASS, independent record loop IDs/counts/hours match service; independent GPU-row hours reconcile within 1e-6 relative tolerance. |
| D03 | PASS, gpu-not-needed exact cohort agreement; rec_lowutil has a different cohort/action, recorded as non-aligned rather than a correction. |
| D04 | PASS, Codex inspected five eligible rows and three excluded/boundary rows privately. Completed zero-SM examples include positive GPU memory; excluded examples cover cancelled, positive SM and <=1 GPU-hour. This is agent inspection, not independent human review. |
| D05 | PASS A-side: 3 recovery settings (0/.5/1) x 2 reference prices; bounded and monotone; price leaves eligibility unchanged. |
| D06 | A-side basis and export PASS under user-selected 0/0/1 policy. Final B display/report agreement PENDING. |
| Bootstrap regression | PASS 5/5 tests; unfinished audit expectation updated to implemented validation error. |
| M01–M04 / U/P/R / G | NOT RUN for A1. No chatbot success or final base readiness claimed. |

## Commands actually run

- `docker run --rm --network manai-bootstrap_default --mount type=bind,source=C:/Users/05mus/manai/work/analysis-service,target=/app,readonly --mount type=bind,source=C:/Users/05mus/manai-bootstrap/data,target=/app/data,readonly manai-bootstrap-analysis python -m unittest discover -s tests/analysis -v`
- `docker exec manai-a-analysis python -m eval.analysis.verify_live`
- `docker exec manai-a-analysis python -m unittest discover -s tests/bootstrap -v`
- Read private `private-eval/analysis/record-review.json` and verified each inclusion/exclusion against the predicate.

Runtime reused the pinned bootstrap image in a separate A container on localhost:18001; shared services were not restarted. Source and code mounts read-only; only ignored private evaluation output writable. Generated audit/claims/review artifacts stay local. No model key or C service was used. CPU compatibility and realized savings remain unproven. A2 and B integration follow; no merge is authorized.

## A2 verification update

A1 published commit: `05c7fa0`. A2 adds real official MCP chat and additional upstream/error consistency checks. Active v0.3; B contract acceptance and final integration review remain pending.

- Analysis/API suite: **9/9 PASS**. Base-chat suite: **4/4 PASS**, covering four supported intents, unsupported certainty/injection, missing/malformed/error tools, wrong-audit evidence, stale observations, timeout cleanup and nested transport errors. Bootstrap: **5/5 PASS**.
- `docker exec manai-a-analysis python -m eval.analysis.verify_live`: repeated D01/D02/D03/D05 and A-side D06 PASS after source consistency checks. Private D04 examples remain the same inspected records. No source rows entered Git.
- `docker exec manai-a-analysis python -m eval.analysis.verify_chat`: **4/4 supported live questions PASS**, ten actual MCP calls including a repeat after C-unavailable response. Citations resolve, claims unchanged, no provider/model. Observed answer latencies about 2.7–3.4 seconds. Both API and MCP use the canonical fingerprint above.
- `docker exec manai-a-analysis python -m eval.analysis.verify_mcp_cleanup`: **PASS** real stdio cancellation (504) and absent audit membership (502), with no orphan MCP processes. The forced short timeout includes SDK cleanup latency; normal public budget reserves five seconds for shutdown.
- `node eval/analysis/ui_smoke.cjs artifacts/b-review/dashboard/node_modules`: **PASS** in Edge with Node 22.16.0 against unchanged B `5a8d995`, development HTTP preview on :13000 and A on :18001. M01 live UI→A→official MCP with citation; M04 reviewer unavailable/malformed/wrong-audit/hang injection preserves actual base chat and identical claims. C04 displayed audit/export agreement and D06 0/0/1 display/export verified. Desktop/narrow screenshots inspected privately; no page exceptions or mock imports. No B source files changed.
- The first frontend dependency install used host Node 24 and warned about B's engine range; verification subsequently used isolated Node 22.16.0. No frontend dependencies or lockfiles changed in A's tracked tree.

M02 and M03 are verified within the template-based scope. M01/M04 now have live development-browser witnesses, not final Compose acceptance. Final D06 REPORT agreement, B cross-review, U05/P/R01/R05 packaging checks and optional G checks remain **PENDING/NOT RUN**. These witnesses do not declare the overall base or C enhancement complete.

Observed B-owned follow-ups: the team recommendation is rendered as “Organizer judgment”; the main upper range should explicitly say eligibility ceiling. The v0.3 target/gap panel remains honestly unavailable. Full real-data browser artifacts remain under ignored `private-eval/ui/`.
