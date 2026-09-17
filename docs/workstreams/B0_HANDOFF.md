# B0 handoff — fixture UI, bootstrap pending

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
