# A+B integration execution — 2026-09-17

Publication update: Winston explicitly approved merging this baseline while deferring independent cross-review and U05. PR #6 merged the frozen snapshot into integration (`982b407`); PR #7 merged it to main (`610f89d`). Main at that merge has exactly the tested snapshot tree. Subsequent B revisions and C compatibility remain separate; see [current handoff](../../docs/MAIN_BASELINE_HANDOFF.md). The historical test record below retains its original scope.

Candidate implementation: `2dbc7fc` on `codex/product-integration`, PR #4 into `codex/integration`. Shared baseline: `db6f418`, including reviewed A `adfcd88` and existing main/B history. `5166afd` adds v0.4 UI; `4a260ae` adds production read-only data/decisions; `2dbc7fc` preserves B's concurrent UI through `788b5ad` with multi-fix action disabled. This candidate was subsequently published by the baseline merges recorded above.

## Outcomes actually observed

| Gate / scope | Result and boundary |
|---|---|
| A regression / T and API gates | PASS: packaged 15 analysis/API + 4 base-chat + 5 bootstrap tests (24 total); proposed/active v0.4 contract and synthetic fixtures validate. A implementation unchanged in B integration. |
| D01–D05 | PASS in the reviewed A environment: all five canonical files; independent cohort comparison; mismatched source recommendation explained; private 5 eligible + 3 boundary inspections; 6 recovery/price sensitivities. No source records published. |
| D06 | Default/report/export agree on 0/0/1 recovery fractions: no empirical positive lower/central estimate; upper eligibility ceiling is not a forecast. Final local claims exported from A and compared exactly. This is scenario accounting, not measured savings. |
| CPU / T05–T07 / C04,C06 / U02,U03 | PASS: eight real production UI cases (success, failure/full rerun, extra validation, negative value, unknown CPU price, unknown queue, unknown pricing boundary, earlier completion), unchanged cohort recovery, signed/null results, evidence and claims identity. |
| B unit/type/build | PASS: 54/54 tests and TypeScript on final merged `2dbc7fc`; production Node 22 build and mock-module exclusion scan pass. Bundle size warning remains (~833 kB JS, ~243 kB gzip). |
| U01–U04 | PASS automated scope: 8 synthetic/HTTP browser cases; 7 local-source browser cases (repeated after the latest B merge); real production desktop/narrow CPU, evidence, keyboard/citations, claims and dataset/decision navigation. Human usability is separate below. |
| Read-only production pages | PASS on :3000 at `2dbc7fc`: all 4 collections, detail links, GPU paging, 8 decision rows, deduplicated union, linked finding→job, stale-version409, page-limit422, write405, multi-fix501 and visibly disabled action. No synthetic substitution. |
| M01–M03 | PASS: actual official MCP calls for 4 supported classes, audit-scoped citations; A timeout/malformed/stale/scope regression and process-cleanup checks reproduced. No model key. |
| P01 / R01 | PASS with explicit configuration scope: clean committed checkout `4a260ae` starts by one Compose command with existing canonical data, fresh private dataset volume and C disabled; isolated test changes only ports/subnet. Production :3000/:8000 startup and full browser flow also pass. No claim of downloading all source data in a network-isolated clean VM. Later B dialog-only merge passes build/browser regression. |
| R02–R04 / M04 | PASS on both original and final Node production proxies: actual stopped reviewer, real HTTP503, malformed JSON, wrong audit and 40-second upstream hang. The final proxy returns within its 31-second deadline. Chat, current claims and canonical results remain usable. Final repeats used clean `4a260ae`; the subsequent B dialog-only merge does not change the proxy. |
| R05 | PASS: test reviewer build deliberately exits1; afterward clean `4a260ae` base starts without reviewer and full live browser suite passes. No failed reviewer fix or build required. |
| P02 | PASS: official validator parses local root claims, validates official schema, accepts 3/10 answered categories and gets HTTP200 at the real dashboard. It warns that no confidence is stated. Disposition: retained; no empirically calibrated confidence exists and none is invented. |
| P03 | Staged source/credential-pattern checks PASS; source data, browsing cache, generated root claims and real screenshots/receipts are excluded from Git and image contexts. Official notices preserved and AI disclosure updated for this session. Final team-wide disclosure and derived-claims publication disposition remain lead tasks; this is not license clearance. |
| U05 / independent cross-review | NOT RUN / PENDING. User navigation feedback found the missing production routes and was addressed; this is not a recorded timed independent usability pass. PR #4 remains draft. No GitHub Actions checks or independent reviews were present when inspected. |
| C enhancement | NOT READY: isolated `d4fa017` image build + 89 tests PASS. Real no-pilot + 3 CPU-mode calls return200/insufficient_evidence using MCP, missing audit404, immutable A claims. Aggregate kinds/columns, live units and CPU-baseline evidence coverage need fixes. No live-model G01–G05 run; no C merge/enablement. |

## Commands run

A checks used `manai-analysis-a04` / `manai-a-analysis` before the port switch. Equivalent commands on the current base:

```sh
docker compose exec -T analysis python -m unittest discover -s tests/analysis -v
docker compose exec -T analysis python -m unittest discover -s tests/base_chat -v
docker compose exec -T analysis python -m unittest discover -s tests/bootstrap -v
docker compose exec -T analysis python contracts/proposals/v0.4/validate.py
docker compose exec -T analysis python -m eval.analysis.verify_live
docker compose exec -T analysis python -m eval.analysis.verify_cpu_pilot
docker compose exec -T analysis python -m eval.analysis.verify_chat
docker compose exec -T analysis python -m eval.analysis.verify_mcp_cleanup
```

Frontend commands used the supplied local Node 22 executable directly (host npm initially selected Node 24); the production container uses Node 22. From dashboard, with locked dependencies installed:

```sh
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vitest/vitest.mjs run
node node_modules/@playwright/test/cli.js test
node node_modules/@playwright/test/cli.js test --config playwright.local.config.ts
```

Browser runs set `PLAYWRIGHT_CHANNEL=msedge`; synthetic/HTTP regression ports were 13020/13021 to avoid the live app. Real local preview remains :3002. From repository root:

```sh
docker compose -p manai-release up -d --build --wait
node eval/integration/browser.cjs http://127.0.0.1:3000 base
node eval/integration/datasets.cjs http://127.0.0.1:3000
python eval/integration/export_final.py --url http://127.0.0.1:3000
python eval/integration/reviewer_check.py --analysis http://127.0.0.1:18001 --reviewer http://127.0.0.1:18002
```

The reviewer command ran before the port switch, against isolated exact A/C containers. See handoff before trying to reuse those old endpoints. The official validator ran in the pinned analysis image with the checkout mounted read-only and `--claims claims.json --url http://dashboard:3000` on the production stack's own network.

Fault tests used `-p manai-fault-check`, existing read-only source data through `MANAI_DATA_DIR`, and these files/commands:

```sh
docker compose -f docker-compose.yml -f eval/integration/compose.isolated.yml -f eval/integration/compose.faults.yml --profile reviewer up -d --build --wait
node eval/integration/browser.cjs http://127.0.0.1:13011 faults
docker compose -f docker-compose.yml -f eval/integration/compose.isolated.yml -f eval/integration/compose.faults.yml --profile reviewer stop reviewer
node eval/integration/browser.cjs http://127.0.0.1:13011 crash
# Expected failure (exit1):
docker compose -f docker-compose.yml -f eval/integration/compose.isolated.yml -f eval/integration/compose.faults.yml -f eval/integration/compose.fail-build.yml --profile reviewer build reviewer
# Default base independently recovers without the reviewer override:
docker compose -f docker-compose.yml -f eval/integration/compose.isolated.yml up -d --build --wait
node eval/integration/browser.cjs http://127.0.0.1:13011 base
```

Private artifacts are under ignored `private-eval/integration/` and `dashboard/.local-data/`. Only executable witnesses and aggregate summaries are public. Unit/browser passes do not establish CPU compatibility, measured recovery or user approval. During early local regression, GPU Next-page navigation failed (4/5 at that time); the initial-search debounce race was fixed, and the later expanded 7/7 suite passed. No failing check was waived.

## Remaining owners

A/B: cross-review PR #4; B/teammate: U05. Lead: final integration/main release, generated root-claims publication decision, completed model/framework disclosure and default branch change from `codex/planning` to approved main (current account WRITE, not ADMIN). C: compatibility and G checks separately. See [copyable author handoff and branch tree](../../docs/AB_INTEGRATION_HANDOFF.md).
