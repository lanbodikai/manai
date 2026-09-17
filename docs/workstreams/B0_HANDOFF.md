# B0 handoff — fixture UI, bootstrap pending

## Latest update — CFO CPU pilot decision planner

User explicitly authorized implementing the decision-planner proposal on baseline **bde7e7b**. The Decisions page retains the allocation bar and source evidence, prioritizes the CPU pilot first and idle-session investigation second (testability, not a savings ranking), and shows a 20% comparison against the same historical sample reference-cost baseline. It explicitly shows that the entire CPU cohort cannot supply a 20% cut on its own. Six other investigations and the full table remain expandable.

Selecting the CPU task opens a local planner. Inputs: pilot size as a fraction of eligible GPU-hours, independent CPU core-hour low/base/high estimates and price, implementation cost, extra retry/rollback reserve, worst slowdown, spend/slowdown limits, recovery assumptions and their source. Unknown costs/performance stay blank and prevent calculation. Initial 0/50/100 recovery levels are labeled illustrative stress scenarios, not measured recovery or confidence intervals. GPU-hours never become CPU core-hours by conversion. The pilot is an hours budget; concrete jobs are not selected automatically.

Results compare unchanged allocation cost with modeled alternative cost, signed low/base/high net reference benefit, base contribution and remaining gap to the sample 20% target, break-even CPU usage, full GPU fallback extra cost, and unpriced business harm. Guardrail breaches flag Revise before approval; a favorable scenario remains only a candidate for owner review. Proposed stop conditions cover output correctness, slowdown and spend, with GPU rollback; no infrastructure mutation, automatic approval, enforcement or cash-savings claim. Idle sessions remain a second investigation with no fabricated financial estimator.

The model is B-owned local planning arithmetic, not A's canonical v0.3/v0.4 audit. The existing backend action still submits only fix IDs and clearly states that local assumptions are not forwarded. Immutable calculated snapshots preserve old results when controls change; downloads export the last calculated snapshot as cpu-pilot-plan.example.json, with source identity and caveats, never claims.json. Dataset changes remount the planner. A must agree canonical fields and implement/validate the financial model before live integration or claims acceptance.

Verification: npm test **51/51 PASS** covers independent arithmetic, signed losses, costs, zero rates, malformed/overflowing inputs, invalid source scope, target units, breached limits and stale form results. npm run build **PASS** including typecheck/live fixture exclusion; existing ~820 kB chunk warning remains. npm run test:local **7/7 PASS (13.1s)** includes desktop/mobile CPU flows, errors, source-based independent arithmetic, snapshot download identity, downside flags, evidence navigation and existing findings checks. npm run test:browser **8/8 PASS (19.4s)** covers prior mock journey, exports, reviewer resilience and HTTP failure. Desktop/mobile result screenshots inspected; no horizontal overflow. Tests initially exposed help text becoming part of field names; accessible labels/descriptions were corrected. After improving the comparison to show cost-versus-cost, final npm test **51/51 PASS**, npm run build **PASS**, and the focused desktop/mobile pilot browser rerun **2/2 PASS (3.4s)**. Input and result screenshots were inspected. Builder self-review only; source screenshots remain ignored. Live CPU benchmarks, cash savings, automatic guardrail enforcement, canonical backend financial model and MCP acceptance remain **NOT RUN**. Only dashboard and this handoff changed.

## Latest update — reference cost beside tasks; unverified savings removed

User asked whether the amounts were legitimate and requested placement only beside tasks. B clarified that the recovery range was illustrative, not measured savings. Verified the running supplied API GET /v1/price-book returns version 2026-Q3, usd_per_gpu_hour 2.5. The task header now shows source eligible hours × that pinned reference rate, labeled **Reference cost · not savings**. This is not actual billing. Removed recovery controls, invented ranges, outcome-dollar displays, combined-dollar summary and duplicate table-dollar displays; deleted the unused what-if helper/tests. Backend net savings remain unmodeled. Historical change records below are superseded.

Actual checks: npm test **47/47 PASS**, npm run build **PASS** including typecheck/mock exclusion, focused local optimization browser tests **2/2 PASS** at desktop/mobile. Existing build chunk warning remains. No backend/shared contract changes. Verified cash savings require equivalent-work pilot measurements, actual marginal/billing rates, incremental costs and subsequent billing evidence; freed capacity on fixed-cost hardware is not automatically cash saved. Live financial modeling and operational effect remain **NOT RUN**.

## Latest update — per-task what-if dollar ranges

User explicitly requested dollar savings under each task immediately. On baseline cfddfa9, B added a local, user-editable what-if preview: recorded eligible GPU-hours × reference USD/GPU-hour × assumed recovery. Defaults are explicitly illustrative ($2.50 and 0–25%), not calibrated recovery estimates. Every task and detailed table row shows its gross reference-dollar range; the selected total uses deduplicated hours. Outcome tabs show allocation reference cost, never savings inferred solely from status. All amounts apply to the sample window, not a month. Actual net savings may be zero or negative; CPU, implementation and performance costs are unmeasured. These local preview assumptions are not submitted to the pending canonical backend model. Backend net savings remains Not modeled; no claims export was changed.

Actual verification: npm test **49/49 PASS**, npm run build **PASS** including typecheck/live mock exclusion (existing chunk warning); focused npm run test:local -- tests/local/optimization.spec.ts **2/2 PASS**. Mobile screenshot inspected; arithmetic, invalid inputs, price editing and deduplicated selected dollars covered. A fixture expectation initially used a different synthetic job cohort and was corrected to the actual 30-hour fixture. Full browser suite not rerun for this focused change. Live financial modeling, MCP and operational savings remain **NOT RUN**. Changes are confined to dashboard and this handoff; frontend preview is not production financial validation.

## Latest update — CFO decisions and cost-optimization tasks

User requested findings-based cost optimization with percentage data, proposed fixes, checkboxes and a backend Optimize action. B implemented `#optimization` using verified local data. Eight rule families have distinct suggested fixes and owner roles; each exposes its share of full-sample recorded GPU-hours, source evidence and downside. Cancellation and synthetic findings are excluded from row numerators; the denominator remains the full sample. The selected union counts each physical job's recorded hours once. No recoverability, dollar saving or intervention effect is inferred from exposure. Historical (`RESOLVED`) and Needs review (`ACTION_REQUIRED`) labels explain lifecycle without implying remediation.

The new `OptimizationApi` capability fits the existing `DashboardApi` and has separate HTTP/mock adapters. Local GET `/api/datasets/decisions` supplies read-only exposure aggregates; POST `/api/optimizations` goes to the actual backend proxy and is intentionally not implemented by the preview. A's inspected branch `05c7fa0` has no multi-fix endpoint. Errors retain selection/evidence; same-selection retries reuse request identity. Strict response checks reject wrong version/selection/request or synthetic live receipts. The UI models intent only and does not execute workload changes. This route is a **B-owned proposal**, not an adopted shared v0.3/v0.4 API extension. See [optimization handoff](../../dashboard/OPTIMIZATION_API.md) for the exact request/receipt and A's remaining work.

Independent source-column selection in Pandas reproduced CPU exposure **2.01785%**, non-cancelled idle-session exposure **5.39872%**, and union exposure **6.82145%**. Mock/schema tests and browser checks do not establish savings. Real screenshots are private/ignored. Changes remain under `dashboard/` and this handoff; A/backend/shared contracts/Compose are untouched. Live multi-fix modeling, v0.4 financial results, MCP and operational effects remain **NOT RUN**.

At the user's follow-up request, the CFO-facing **Decisions** tab now starts with a storage-style segmented bar: Finished, Cancelled, Timed out, Failed and Other. These are mutually exclusive shares of recorded allocation, not productive capacity or recoverable savings. Outcome totals must reconcile before rendering. Keyboard-accessible legend buttons explain each category. Three investigation cards appear initially, with five additional opportunities on demand; each exposes a checkbox, owner, source percentage, risk/safeguards and findings link. The detailed decision table stays collapsed below the **Model selected changes** action. Selected exposure and potential savings remain separate. No recovery target is falsely shown as achieved.

Verification on baseline **fc55840** plus this change: `npm test` **47/47 PASS**; `npm run build` **PASS**, including TypeScript and exclusion of mock fixtures and local aggregation from the live bundle (nonfatal 806 kB chunk warning). `npm run test:local` **5/5 PASS (11.5s)**, including real-source selection, outcome interaction, show-more/less, keyboard Enter/Space, deduplication, filtered evidence, actual unavailable POST and a separately stubbed receipt. `npm run test:browser` **8/8 PASS (19.2s)** covers the existing synthetic journey, exports, reviewer failure states and HTTP failure without fallback. The initial test typing error was corrected; final checks above passed. Desktop 1440px and mobile 390px screenshots were visually inspected; no mobile page overflow. Builder self-review only. No independent CFO usability acceptance is claimed.

Changed areas: `dashboard/src/components/CostOptimization.tsx`, API capability/adapters, synthetic optimization fixtures, dev-only source exposure aggregation, related styles, navigation, findings lifecycle labels, local/browser/unit tests, synthetic evidence screenshots, frontend documentation, and this handoff. All source records/screenshots remain ignored. Current implementation SHA is the commit containing this section (`git log -1 --format=%H -- dashboard/src/components/CostOptimization.tsx`). A must agree the proposed identity/idempotency semantics and supply modeling/results; B then connects canonical financial ranges and downside. No backend, Compose or shared contract edits; no merge into main.

## Latest update — official findings generated and loaded

User authorized starting Docker and obtaining findings. Following a failed initial Desktop startup and the user's manual opening of Desktop, engine **29.6.2** became available. No Docker factory reset, socket deletion or runtime-directory move was performed by B. In `C:/Users/lanbo/mantisgrid`, B ran `docker compose run --rm prep`, `docker compose run --rm generate`, `docker compose run --rm prep python scripts/checksum_data.py`, and `docker compose up -d api`. All commands succeeded; **all five canonical data files printed `ok`**. The supplied Linux generator hash matched `bin/SHA256SUMS`. Source code was not modified; generated data remain local.

Output: **11,979 findings**, including **121 explicitly synthetic findings**, plus 77,399 resources and 198,601 edges. Official API health at :8000 reports the matching findings/resource counts. B rebuilt the ignored local preview using `tools/prepare_preview.py --official-root C:/Users/lanbo/mantisgrid` with bundled Python and the existing isolated numeric dependencies. The importer now verifies all three generated files, enriches job/machine joins using the official resource mapping, and keeps source judgments distinct from synthetic findings. No financial totals or savings estimator were added.

Dashboard findings at **http://127.0.0.1:3002/#data/findings** support search, lifecycle/machine filters, pagination, impact kind/scope, complete fields and connected-record drilldown. The drawer clears stale content when changing records and exposes reported impact instead of an empty metric panel. The preview is a local snapshot; A's production dataset/audit adapter remains pending.

Actual checks: `npm test` **33/33 PASS**; `npm run build` **PASS** including typecheck and mock exclusion (existing nonfatal chunk-size warning). Read-only SQLite inspection resolved **all 32,414 source links**. Final `npm run test:local` **3/3 PASS (8.4s)** covered browser navigation, independent official-API comparison of nine findings across three rule families, counts, synthetic flags, and source links, plus existing read-only/version/pagination checks. Desktop and narrow screenshots were visually inspected; the mobile finding drawer occupies the full 390 x 844 viewport, contains keyboard focus and has no horizontal overflow. A browser test's search debounce race was corrected by waiting for the selected rule before opening a record. Real source screenshots remain ignored under `.local-data/evidence/`. This is B self-review; real savings, v0.4 CPU service/UI adoption, live MCP and complete Compose dashboard integration remain **NOT RUN**. Follow [local preview guide](../../dashboard/LOCAL_DATA_PREVIEW.md) to reproduce.

## Latest update — main merged and API alignment acknowledged

The dashboard branch was merged into `main` at **`5a8d995a624dcd188101de802f75263a512bcc48`** at the user's request; PR #1 is merged. Immediately before publication, `npm test` passed **33/33** and `npm run build` passed typecheck, production build and mock-exclusion checks. The nonfatal chunk-size warning remains. Earlier draft-PR/bootstrap-pending statements below are historical.

At the user's subsequent request, B reviewed both contracts and acknowledges **v0.3 as the official current team contract and v0.4 as the accepted official CPU-extension specification for implementation**. These are manai team contracts, not MantisGrid product APIs. This supplies B's acceptance; A agreement and coordinated runtime adoption remain pending. Active schemas, backend and current v0.3 client were preserved.

See [API alignment review](../../dashboard/API_ALIGNMENT.md) for compatibility, UI implications, actual verification and next-owner actions. The v0.4 validator passed six complete fixtures and eight synthetic pilot cases. Ajv fixture and cross-version probes confirm realistic alignment but a required client upgrade: the closed v0.3 validator rejects v0.4 audits. Positive infinity is accepted under the current non-strict Ajv number configuration; explicit finite-number validation is required during adoption. CPU hours versus trial-cap comparison also needs semantic validation in A. Live v0.4, MCP, Docker and operational-effect checks are **NOT RUN** in this review. No calculator/UI implementation or shared-contract promotion is claimed.

## Latest update — real local dataset explorer and baseline merged

The original B0 record below is historical. Following the user's request for real front-page visualizations and per-GPU data browsing, implementation commit **`e28179e`** adds an explicit read-only local preview. Merge commit **`25fbe6d6204e4ecfbc8864b144cbb540ac01380d`** incorporates `origin/codex/integration` at `ee529ee9f1839131c4ef1b72656030ce4780b9d4`, including the verified implementation baseline **`7530865eeca4fe87daf91b5cc275af378bd42fb7`**. Bootstrap's published status now records BASE-01–BASE-07 PASS. The merge had no conflicts and changed no dashboard or shared-contract files relative to our tested implementation. These are bootstrap owner's recorded results, not a rerun by B.

The same draft PR now targets integration. B has not merged the PR or changed root Compose, backend implementation or shared contracts. Development `/api` proxy targets A at :8001 (configurable `MANAI_ANALYSIS_URL`); completed overview can render even when the bootstrap recommendations endpoint is unfinished. Actual A audit/chat integration, Docker replacement of the temporary page and B1/B2 are still pending.

### Added user journey

`npm run dev:local` opens **http://127.0.0.1:3002** with a persistent real-source/local-preview label. The front page plots recorded → estimated active → completed active GPU-hours and the separate outcome breakdown. Click an outcome or collection to enter Jobs, GPUs, Machines or Findings. Search/filter/sort/page the full local dataset; open full job fields and per-GPU measurements; follow connected resources or browse every job on a selected physical card. A GPU is keyed by machine + GPU ID, with activity keyed additionally by job. First-machine placement is never used as the sole physical-machine filter. Nulls remain unknown; finding rows preserve synthetic labels.

This is a **temporary browsing API/cache owned inside dashboard**, not A's audit service. The frozen v0.3 DTOs/routes are unchanged. A frontend-owned `preview-1` optional capability and endpoint proposal are documented in [LOCAL_DATA_PREVIEW.md](../../dashboard/LOCAL_DATA_PREVIEW.md). Production dataset opt-in remains disabled until the backend agrees and exposes it. Mock mode and normal HTTP mode remain separate. Local records never supply synthetic savings, claims or MCP answers.

### Actual data and checks

- Used the existing downloaded CSVs in the original workspace, read-only. Ran the unmodified supplied preparation functions with NumPy 2.5.2, pandas 3.0.5 and pyarrow 25.0.1 installed into ignored `dashboard/.local-python/`.
- Actual command: bundled Python with `PYTHONPATH=dashboard/.local-python` ran `tools/prepare_preview.py --official-root C:/Users/lanbo/mantisgrid` from dashboard. The portable venv equivalent is in the preview guide.
- Produced **74,849 jobs, 96,893 GPU-job records, 450 cards and 225 machines**. Both prepared-table semantic digests printed `ok` against the official expectations. Internal job/card identity, hour reconciliation and bounded-duration checks passed.
- Generated findings were absent. Findings are explicitly **not loaded**, not zero findings. Full five-file D01, generator checks, real claims and MCP are **NOT RUN by B**.
- Data/parquet/SQLite cache and real screenshots are confined to ignored `.local-data/`; no raw or source-derived rows/screenshots were staged. The temporary imports' bytecode cache was removed from the supplied checkout and future cache writes there are disabled.
- `npm test`: **33/33 PASS**, including immutable demo reconciliation, paging, physical-card identity, schema/identity guards, no fallback and unavailable recommendations preserving overview.
- `npm run build`: **PASS**, including typecheck and live mock-exclusion checks. Nonfatal chunk warning now approximately 784 kB / 230 kB gzip; production optimization remains open.
- `npm run test:browser`: **8/8 PASS**, synthetic desktop/mobile explorer and prior CFO/resilience journey. `npm run test:local`: **2/2 PASS**, real source chart-to-record walkthrough plus read-only/versioned/paginated API behavior, literal SQL-safe search, and physical-card filtering checked against returned activity.
- Real screenshots visually inspected at desktop and narrow widths; saved only under `.local-data/evidence/`. Builder self-review, no independent human acceptance. Synthetic explorer screenshots are under `dashboard/evidence/`.
- Initial failures resolved: reserved Vite mode name, async config typing, parallel development cache/test-output collisions, select labels, and mobile overflow from absolutely positioned accessible table text. No failing checks were waived.

Additional owned paths since B0: `dashboard/LOCAL_DATA_PREVIEW.md`, `dashboard/playwright.local.config.ts`, `dashboard/src/api/dataset.ts`, `dashboard/src/api/local-runtime.ts`, `dashboard/src/components/DataExplorer.tsx`, `dashboard/src/dataset-fields.ts`, `dashboard/src/dataset.css`, `dashboard/src/mock/datasets.ts`, `dashboard/tests/datasets.test.ts`, `dashboard/tests/browser/dataset.spec.ts`, `dashboard/tests/local/preview.spec.ts`, `dashboard/tools/local-dataset-plugin.ts`, `dashboard/tools/prepare_preview.py`, `dashboard/tools/preview-requirements.txt`, `dashboard/evidence/dataset-empty.png`, `dashboard/evidence/dataset-mobile.png`. Existing dashboard config/components/tests/docs/screenshots were updated; all B-authored changes still lie under dashboard and this handoff.

Featherless/model credentials are not needed for these visualizations or browsing. No credential was requested or used. Next: A agrees production dataset routes and delivers audited endpoints; B continues Compose, live same-audit journey and required MCP integration. C remains optional.

---

## Original B0 completion record

Recorded 17 September 2026. B0-01 through B0-06 **PASS within synthetic frontend scope**. B1/B2, submission readiness and live-data/MCP correctness are **NOT RUN**. This is builder self-review, not independent UX or cross-review approval.

## Branch and ownership

- Isolated clone: `C:\Users\lanbo\manai-b`; original `C:\Users\lanbo\mantisgrid` preserved.
- Branch: `codex/product-integration`.
- Start: `origin/codex/planning` at `588ea666e5eb68fa58939efe05398b4fd1769dd6`.
- Current tested implementation: `eb9ac98f77e7769327f68f739c4430b5fd041551`.
- This handoff is a subsequent documentation-only commit. Resolve its exact current branch SHA with `git rev-parse HEAD`; the tested code remains the implementation commit above.
- API: existing OpenAPI **v0.3**, unchanged.
- `git ls-remote --heads origin` showed only `codex/planning` at publication preparation. Draft PR therefore targets `codex/planning`, marked **B0 fixture UI — bootstrap pending**. Do not merge. Retarget the same PR when integration is available and inspect the resulting diff.
- No verified bootstrap SHA has been delivered. No bootstrap, source preparation, Docker, A/C service or shared-contract changes were attempted.

## Implemented

Three connected cards; outcome chart and accessible values table; mock-only matching-window 20% target/contribution/gap; owned CPU-placement pilot; explicit unknown financial downside; scenario assumptions and pending-input state; immutable audit snapshots; calculation-to-source dialog with eligibility, safeguards, source fields, joins and caveats; separate base and optional chat panels; current-audit synthetic claims download. Responsive desktop/mobile layout and modal keyboard behavior follow the supplied visual reference.

One `DashboardApi` covers every v0.3 operation. Generated TypeScript and Ajv validation use the existing contract. Separate mock and HTTP entry points prevent fixture imports in normal live builds. Live HTTP errors remain explicit. Latest-request tracking protects scenario results; audit/request/evidence identities protect drilldown and answers. Chat state resets when the audit changes. Export captures the displayed audit and rejects a response after the display changes.

The user also requested a production/human-usability review. [PRODUCTION_REVIEW.md](../../dashboard/PRODUCTION_REVIEW.md) records findings, data-grounded limitations and proposed next work; those proposals are not silently implemented or reported as complete.

## Setup and actual commands

Environment: Windows, Node **22.16.0**, npm **11.5.2**. Package supports Node >=22.12 and <23. One committed npm lockfile. Run commands from `dashboard/` unless stated otherwise.

| Command/check | Actual result |
| --- | --- |
| `npm ci` | PASS after stopping the prior preview; 206 packages installed, 207 audited, zero reported vulnerabilities. No backend or keys. |
| `npm run dev:mock` | PASS on `127.0.0.1:3000`, initially launched directly and subsequently launched by Playwright from the clean install. |
| `npm run types:generate` | PASS, OpenAPI TypeScript output committed inside dashboard. |
| `npm test` | PASS: **28/28** tests in two files on final run; 20.50s with build/browser jobs running concurrently. |
| `npm run build` | PASS: includes `tsc --noEmit`, Vite production HTTP build, module-graph exclusion and emitted-asset marker scan. |
| `npx playwright install chromium` | PASS: Chromium installed for browser verification. |
| `npm run test:browser` | PASS: **6/6** real Chromium browser tests, final run 17.7s, desktop 1440×1000 and narrow 390×844. Starts separate mock :3000 and HTTP :3001 servers. |
| `git diff --cached --check` | PASS before implementation commit; no whitespace errors. |
| Changed-path inspection | PASS: only dashboard files and this handoff. No raw/prepared/generated organizer records, provider credentials, root dependencies or shared schema modifications added. |

Build emits a nonfatal JavaScript chunk-size warning: about 758 kB minified / 223 kB gzip. Chart/schema dependency splitting is a future performance improvement, not a claim of production performance readiness. Initial implementation failures were corrected before final checks: TypeScript dependency compatibility, nullable mock latency violating the schema, reused consumed Response test stubs, and display-format assertions. None remain failing. No tests were skipped to obtain the final pass.

See [dashboard README](../../dashboard/README.md) for live/mock startup, fault URLs, generation command and reproduction instructions. `npm run dev` and normal `npm run build` select HTTP; B0 intentionally has no `/api` backend/proxy, and live startup honestly reports unavailable data.

## B0 gates and evidence

| Gate | Result | Evidence |
| --- | --- | --- |
| B0-01 | PASS | Clean `npm ci`; mock startup and browser page at :3000 without Docker, backend, source data or credentials. |
| B0-02 | PASS | Browser follows three cards → $15–$45 → J1 source detail. Second scenario's downloaded file is `synthetic-claims.example.json`, bound to `demo-audit-2`, with 0/15/30 hours and $0/$60/$120. Adapter test also exports an older snapshot correctly after a newer snapshot exists. |
| B0-03 | PASS | Seed 20/40/60% at $2.50 produces 6/12/18 hours, $15/$30/$45. Second scenario 0/50/100% at $4 matches 0/15/30 hours, $0/$60/$120. Delayed older request cannot replace the newer display. Missing, unordered, nonfinite, out-of-range and nonpositive inputs fail explicitly. |
| B0-04 | PASS | Loading, empty cohort, source 503, source 404, creation 409/422, reviewer absence/504/malformed response covered. All three reviewer failures leave base chat and export available; browser also follows base-chat citations. These are injected fixture/HTTP-stub faults, not real service resilience proof. |
| B0-05 | PASS | Shared examples and additional representative payloads validate with v0.3. Typecheck/build pass. HTTP statuses 404/409/422/429/502/503/504, network/HTML/malformed replies and cross-audit/request/evidence IDs reject. Timeout mechanism tested using a shortened deadline; configured defaults are 12s base, 35s optional, 15s other. Live browser displays connection failure and loads no mock modules. Production bundler rejects mock/fixture module IDs and scans fixture markers. |
| B0-06 | PASS, self-review | Real Chromium screenshots inspected at desktop and mobile; no horizontal overflow at narrow width. Enter opens the focused dollar control, Tab stays inside native modal, Escape closes and restores focus. Mobile source drawer is full-screen with scrolling. Explicit mobile navigation names added. Independent 30-second participant test NOT RUN. |

Screenshots, all synthetic:

- [Desktop overview](../../dashboard/evidence/desktop-overview.png)
- [Desktop source detail](../../dashboard/evidence/evidence-detail.png)
- [Mobile overview](../../dashboard/evidence/mobile-overview.png)
- [Mobile source detail](../../dashboard/evidence/mobile-evidence.png)

## Fixture coverage and limits

Shared original seeds: audit request/response, evidence, explanation, claims and error examples in `contracts/examples/`, read without modifying them. Dashboard adds an invented 600-GPU-hour/20-job overview, five outcome rows, one recommendation, health/page states, J2 detail, immutable simulations and fault injection. Eligible invented jobs are J1=10 and J2=20 GPU-hours. These are not extracted from organizer data. Fraction/price calculations are in `src/mock/`; live components format A's canonical numbers.

Mock queries: `empty`, `source-unavailable`, `not-found`, `conflict`, `invalid`, `reviewer-unavailable`, `reviewer-timeout`, `reviewer-malformed` via `?demo=...`. The timeout fixture returns a simulated error after normal demo latency; HTTP deadline logic is independently tested, not claimed to have waited 35s in that browser case. Mock chat has zero tool calls and no trace IDs; it is explicitly an example. Preset fractions are not recommendations or measured recovery bounds.

Only two source records exist, so pagination is adapter-tested with page size one; large real cohorts and real service paging performance are NOT RUN. Screenshots were reviewed by the builder; no independent person has passed U05.

## Contract gaps and next owners

1. **A + B:** overview lacks canonical same-window baseline reference dollars, target amount, contribution interval, remaining gap and normalization basis. Only mock runtime supplies the illustration; live target panel says unavailable. Do not add financial arithmetic to production React to hide the gap.
2. **A + B:** the official starter distinguishes recorded GPU-hours, estimated active GPU-hours and active hours in completed jobs. Current v0.3 outcome rows do not contain that activity progression. Agree fields before making the 83% narrative a live chart; outcome completion and GPU activity are different.
3. **A:** confirm source window/price version, completed-zero-compute eligibility, measurement coverage, overlap accounting and scenario-bound evidence on real data. Positive lower bounds in synthetic defaults provide no evidence; D06 includes zero sensitivity.
4. **Bootstrap, then B:** deliver exact verified bootstrap SHA; fetch and merge it into this same branch, retaining both histories. Resolve owned conflicts only, retarget the same draft PR to integration if needed, then wire :3000 and same-origin `/api` routing to A. No shared branch force-push or merge authorization inferred.
5. **A + B:** exercise actual health/overview/audits/evidence/claims and real MCP-backed `/chat`; confirm errors and identity with actual payloads. A must normalize FastAPI validation errors to v0.3. C is optional and cannot enter the base dependency chain.
6. **B:** improve human labels, progressive evidence disclosure, assumption guidance and pilot-plan prominence as proposed in the review. New persisted decisions, comparisons or pilot fields require agreement with A; B0 creates calculation snapshots only, no workload actions.
7. **A + finance/workload owners:** CPU-only compatibility, CPU cost, cash-releasability, rerun cost and research-delay value are not measured by this dataset. Keep downside money unknown until supported. Do not present reference-dollar opportunities as verified budget cuts.

## Explicitly NOT RUN

- T01–T09 analytical service acceptance; similar mock arithmetic is not A's implementation proof.
- D01–D06 source verification, independent recomputation and claim calibration.
- M01–M04 real official MCP execution and chatbot grounding.
- G01–G05 enhanced reviewer grounding/model evaluation.
- P01–P03 Docker packaging, official claims/live-URL submission validation and full submission audit.
- Real-data U01–U04, independent U05, real integration C02–C06 and R01–R05 service/process resilience.
- Actual pilot, measured slowdown, realized cash savings, external accessibility audit, production load/security readiness.

B0 schema tests establish shape only; they do not claim the official source-data/claims validator or live service gates passed. The separate bootstrap/A session is the next dependency; C remains optional.

## Exact changed paths

```text
dashboard/.gitignore
dashboard/PRODUCTION_REVIEW.md
dashboard/README.md
dashboard/evidence/desktop-overview.png
dashboard/evidence/evidence-detail.png
dashboard/evidence/mobile-evidence.png
dashboard/evidence/mobile-overview.png
dashboard/index.html
dashboard/package-lock.json
dashboard/package.json
dashboard/playwright.config.ts
dashboard/scripts/check-live-bundle.mjs
dashboard/src/App.tsx
dashboard/src/api/generated.ts
dashboard/src/api/http.ts
dashboard/src/api/runtime.ts
dashboard/src/api/types.ts
dashboard/src/api/validation.ts
dashboard/src/components/ChatPanel.tsx
dashboard/src/components/EvidenceDrawer.tsx
dashboard/src/components/ScenarioForm.tsx
dashboard/src/format.ts
dashboard/src/main.tsx
dashboard/src/mock/api.ts
dashboard/src/mock/runtime.ts
dashboard/src/runtime.d.ts
dashboard/src/styles.css
dashboard/tests/App.test.tsx
dashboard/tests/adapters.test.ts
dashboard/tests/browser/journey.spec.ts
dashboard/tests/setup.ts
dashboard/tsconfig.json
dashboard/vite.config.ts
docs/workstreams/B0_HANDOFF.md
```
