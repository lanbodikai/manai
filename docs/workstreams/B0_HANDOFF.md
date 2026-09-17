# B0 handoff — fixture UI, bootstrap pending

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
