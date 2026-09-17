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
