# PR #8 merge review — 2026-09-17

Scope: paused B branch `codex/cfo-decision-review` at `ff122f5`, merged with main `7197d03` in an isolated review checkout. The user requested review and merge of this B revision. This record covers the resolved result, not just the author's original branch. Resolve its exact commit through PR #8; this file is included in that commit.

## Review and conflict resolution

- Preserved B's CFO tiles, Investigate/Model/Authorize guidance, action prioritization, review dialog/export, CPU result summary, chat retry and configurable development API origin.
- Preserved main's working CPU input form, read-only dataset/decision deployment, explicit disabled multi-fix action, positive-successful-duration/time-cap validation and strict finite-number checks.
- Kept generated types, runtime validation and fixtures on the **adopted active** v0.4 schema, not the historical proposal path. Generated types and package lock remain identical to main.
- Kept the synthetic demo from returning a fixed CPU result for arbitrary trial inputs. The CPU summary rendering test uses an explicit fixture response instead; live arithmetic is checked against A.
- Initial unit attempt was 55/56 because the new render test assumed that arbitrary CPU mock behavior. Corrected the explicit test fixture; final 56/56 passed.
- Initial local browser run was 4/7 because three selectors still expected the renamed "Review pilot risks" button. Changed them to the actual "Review guardrails" label, retaining behavior assertions; final 7/7 passed.
- Verified no changes relative to main in analysis, service, MCP runtime, shared contracts, Compose, dashboard image/server or dataset preparation/serving code. No C or Pilot & Recovery feature is included.

## Checks run and outcomes

All frontend checks use Node 22; the host npm installer reported its Node 24 launcher, while tests and production build explicitly ran Node 22. Locked install completed; no dependency/lock changes.

| Command / scope | Outcome |
|---|---|
| `node node_modules/typescript/bin/tsc --noEmit` | PASS |
| `node node_modules/vitest/vitest.mjs run` | PASS, 56/56 |
| `node node_modules/@playwright/test/cli.js test` | PASS, 8/8 synthetic/HTTP browser cases |
| `node node_modules/@playwright/test/cli.js test --config playwright.local.config.ts` | PASS, 7/7 real-source local browser cases, including review/export, planner updates, keyboard/modal focus, narrow layout and source navigation |
| `docker compose -p manai-pr8-check -f docker-compose.yml -f eval/integration/compose.isolated.yml up -d --build --wait` | PASS, healthy production base on isolated :13011/:18080, fresh checksum-verified private dataset snapshot, C absent |
| `node eval/integration/browser.cjs http://127.0.0.1:13011 base` | PASS, eight real CPU cases; signed/unknown values, immutable cohort recovery, actual MCP, evidence, claim identity, optional-reviewer unavailable isolation and desktop/narrow flow |
| `node eval/integration/datasets.cjs http://127.0.0.1:13011` | PASS, all four collections, read-only/version/page guards, deduplicated decisions, new decision-review export with null verified savings, disabled unimplemented action, source links and desktop/mobile |
| Official `scripts/validate_submission.py` in pinned analysis image, private live claims and real dashboard URL | PASS schema / 3 of 10 answered categories / HTTP200; expected no-calibrated-confidence warning retained |
| `git diff --check`, runtime-boundary comparison and staged artifact/credential-pattern scan | PASS |

Browser runs use Edge (`PLAYWRIGHT_CHANNEL=msedge`); synthetic/HTTP ports are 13020/13021. `MANAI_DATA_DIR` points at the existing canonical data read-only. Screenshots, browsing cache and detailed real receipts remain ignored/private. Production desktop/mobile screenshot inspection found no clipped mandatory content; automated usability is not independent U05.

The previous full R01–R05 evidence remains scoped to the baseline; this change repeats real base/C-unavailable and synthetic reviewer-failure regressions without claiming another complete real fault-matrix run. No model-provider calls or actual workloads were executed. Human U05 remains outstanding; no measured savings or final submission acceptance is claimed. Next owners: B for further UI work based on merged main, C for compatibility against the new main head.
