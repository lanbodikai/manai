# Common-base completion evidence

State: **READY TO SPLIT — BASE-01 through BASE-07 passed.** Verified implementation baseline: `7530865eeca4fe87daf91b5cc275af378bd42fb7`. Subsequent handoff/status commits change documentation only. Branch: `codex/integration`.

- Planning parent: 588ea666e5eb68fa58939efe05398b4fd1769dd6.
- Official source: 314cca0bba49e1bb137aa9094d1dac4cdf7e4490.
- Contract: API 0.3 (OpenAPI info 0.3.0); shared contract files unchanged.
- Linux Docker Engine 29.7.2 on amd64; official dependency lock retained. Team runtime resolves FastMCP 4.0.5 / MCP SDK 2.2.0, recorded in service/requirements.lock.txt; pip check passed.
- Time target: remaining bootstrap targeted at 15 minutes from 18:05:44 UTC, with final 3 minutes for publishing/handoff. This is a time target, not permission to waive a gate.

| Gate | Evidence | Status |
|---|---|---|
| BASE-01 | 35 imported files recorded; both supplied generator SHA256 values matched; notices preserved | PASS |
| BASE-02 | Official checker printed ok for all five canonical files | PASS |
| BASE-03 | All required cohort columns exist; unique job IDs; no missing/invalid required measurements; selected cohort exactly matches gpu-not-needed findings | PASS |
| BASE-04 | Five bootstrap tests passed, covering the six synthetic fixtures, overview mapping, structured errors and canonical-data mismatch/change handling; live overview matches official source endpoint; live official OpenAPI inspected | PASS |
| BASE-05 | Real stdio health/list_rules/list_findings calls; 13 tools enumerated; bounded finding retrieval; no provider credential | PASS |
| BASE-06 | Default stack started with api/analysis/dashboard only; live overview + labeled fixture + 404 path; C route 503 does not affect overview; Edge desktop/narrow viewport and keyboard refresh passed | PASS |
| BASE-07 | Independent clean clone of the baseline; fresh raw download and regenerated canonical data; complete setup script passed; exact docker compose up auto-built new project images and served :3000; live checks/tests/MCP/browser passed; baseline published | PASS |

Semantic fingerprint of canonical five-file dataset: `62fa722b0909528e0c78fa5300064593d0090c0c0dc44012d11effb4fcbf0e2b`.

## Commands actually run

- docker compose run --rm prep
- docker compose run --rm generate
- docker compose run --rm prep python scripts/checksum_data.py
- docker compose build analysis dashboard
- docker compose up -d (same default services as unattended docker compose up)
- docker compose run --rm --no-deps analysis python -m unittest discover -s tests/bootstrap -v
- docker compose run --rm --no-deps analysis python -m tools.bootstrap.cohort_check
- docker compose run --rm --no-deps analysis python -m tools.bootstrap.mcp_probe
- docker compose exec -T analysis python -m tools.bootstrap.verify_live
- Playwright with installed Edge: desktop 1280x1000, narrow viewport 390x844, keyboard refresh, no page exceptions. Screenshots inspected locally; not committed as source-data artifacts.

## Issues found and resolved

Docker was installed but stopped; started it automatically. Automatic address pools were exhausted by other projects: chose a separate configurable subnet, without pruning existing networks. MCP SDK 2 uses snake_case result fields; fixed probe accordingly and reran actual calls. Bundled Firefox failed to spawn; installed Edge passed browser checks. No Featherless key was read or provider request made.

## Limits and next ownership

This is not a finished submission: no audit/recovery calculation, final claims, full dashboard, required base-chat behavior or advanced reviewer is implemented. The bootstrap cohort check proves feasibility only; A's D-series research checks remain outstanding. Tests of live chatbot, C grounding, final usability and clean final submission are NOT RUN. A/B/C ownership and exact immutable boundaries: BOOTSTRAP_BOUNDARY.md. B's dashboard/ and contracts/ have no bootstrap changes.

## Clean-checkout verification details

Independent clone used the committed source, not uncommitted worktree files. Upstream Git-blob hashes matched in the fresh LF checkout; contracts/ and dashboard/ had zero diff from planning parent. Data was downloaded afresh. The first clean generator attempt exited nonzero while an image build was running; no cause was proven. An isolated generation succeeded, then the entire setup script was rerun sequentially and passed all steps. Do not parallelize memory-heavy build and generator work on a constrained host.

The exact `docker compose up` command ran under a new Compose project (`manai-verified`) with an unused subnet, automatically built its application images using available Docker layer cache, and started only api/analysis/dashboard. No model key or reviewer was configured. `verify_live`, all five unittest cases, MCP stdio probe and the Edge browser test passed again against this independent stack. Data fingerprint matched the original run. Original bootstrap stack was stopped during the test to free ports; the primary worktree is restored for the handoff.

Git checks: only data/README.md and data/checksums.txt tracked under data; representative secrets/data/cache paths ignored; tracked-file credential-pattern scan passed. Image inspection confirmed no /app/data or .env.featherless baked in and no FEATHERLESS_API_KEY environment value. Team diffs pass whitespace checks; original agreement's Markdown trailing spaces are retained verbatim rather than editing its notice.

Verified at approximately 18:15 UTC September 17, before the 18:20:44 UTC remaining-work target. No manual user action was required. Final submission deadline is still 15:00 PDT; this baseline is not a submitted entry.

## Immediate handoff commands

A (new branch):
```sh
git fetch origin
git switch -c codex/analysis-service 7530865eeca4fe87daf91b5cc275af378bd42fb7
```

B (existing B0 branch):
```sh
git fetch origin
git switch codex/product-integration
git merge origin/codex/integration
```

C (new branch):
```sh
git fetch origin
git switch -c codex/evidence-review-service 7530865eeca4fe87daf91b5cc275af378bd42fb7
```

Use separate clones/worktrees. Do not recreate or reset a branch that already contains work. All implementation PRs target codex/integration. Read CODEX_HANDOFF.md and the corresponding workstream contract. B should merge the integration branch to receive both verified code and the latest documentation; A/C should also read the published current handoffs when branching from the frozen implementation SHA.
