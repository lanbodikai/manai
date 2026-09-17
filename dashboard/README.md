> Current integration update (2026-09-17): production Compose now serves the v0.4 audit flow and the existing read-only explorer/decision routes on :3000. `dataset-prep` builds the verified private snapshot automatically; `tools/dataset-handler.ts` is shared with the local preview. These browsing routes remain B-owned and are not additions to A's v0.4 contract. Multi-fix modeling is disabled in production. The historical local/B0 instructions below remain useful for development; their production-unavailable statements are superseded by [current root instructions](../README.md) and [integration results](../eval/integration/RESULTS.md).

# MANAI dashboard — B0 synthetic MVP

React + TypeScript + Vite, Recharts, Lucide and plain CSS. This frontend is runnable before the shared bootstrap. All demo records are invented. No real data, savings, MCP execution or submission readiness is established here.

**Real dataset browser added:** use the separate [local preview instructions](LOCAL_DATA_PREVIEW.md) to browse prepared source records and real front-page charts on :3002. This explicitly selected development mode does not mix real records with mock savings. The original B0 instructions/results below describe synthetic mode.

## Start the demo

Use Node **22.12 or newer within Node 22** and npm. Verified with Node 22.16.0 / npm 11.5.2 on Windows. From the repository checkout:

```sh
cd dashboard
npm ci
npm run dev:mock
```

Open http://127.0.0.1:3000. No backend, Docker, organizer data or credentials are needed. The persistent banner reads **Synthetic demo — no live data or MCP**. The mock API holds immutable audits in memory; refreshing resets them. The UI uses system font fallbacks when Google Fonts cannot load.

## A 30-second journey

1. Read the three cards: the sample's reference value, a CPU-placement pilot owned by Platform/SRE with the workload owner, and the unmeasured risk of slower or failed work.
2. Click **$15–$45** to inspect the calculation, then select J1 or J2 to see fields, joins, method and caveats. Escape closes the drawer and restores focus.
3. Adjust recovery low/point/high, reference price and assumption note. **Model scenario** creates another snapshot; pending inputs do not change the displayed audit or its export.
4. Ask a supported question in the required base-chat panel. The optional reviewer has its own error/loading state. Both return labeled examples in mock mode.
5. Download **synthetic-claims.example.json** for the displayed audit. This is not a submission file.

For a second scenario use 0% / 50% / 100% at $4/GPU-hour: the invented 30-hour eligibility ceiling yields 0 / 15 / 30 hours and $0 / $60 / $120. This arithmetic lives only in the mock adapter. Cancelled jobs remain excluded. Recovery percentages are scenario assumptions, not confidence intervals. Reference dollars are not verified cash savings. The 20% contribution/gap uses the same invented sample window and scenario price; it is not a quarterly forecast.

## Live integration boundary

```sh
npm run dev
npm run build
```

Both default to the **HTTP** entry point. Calls use same-origin `/api/*`. No proxy or backend is supplied in B0, so an unconfigured launch visibly fails instead of substituting fixtures. Bootstrap/B1 must route `/api` to A and serve the dashboard. The live form has no invented recovery defaults. A owns production calculations; the target contribution/gap is unavailable until agreed canonical fields exist.

`src/api/types.ts` defines one `DashboardApi`. `src/api/http.ts` validates v0.3 payloads and request/audit/evidence identities. Base chat times out after 12 seconds, optional review after 35 seconds, other requests after 15 seconds. All errors are explicit. Vite chooses `src/mock/runtime.ts` only with `--mode mock`; a normal production build rejects mock/fixture modules and scans emitted assets for fixture markers.

Generate types from the existing, unchanged contract:

```sh
npm run types:generate
```

Types are committed under `src/api/generated.ts`. Runtime Ajv validators read the same shared OpenAPI document. Shared original examples are read-only seeds; additional invented overview/recommendation/pagination/health states and simulation code are confined to `src/mock/`. No organizer records are imported.

## Inspect failure states

Append a query to the mock URL; these have no effect in live mode.

| Query | State |
| --- | --- |
| `?demo=empty` | Zero eligible jobs, zero recovery, no source records |
| `?demo=source-unavailable` | Evidence detail returns 503; audit remains usable |
| `?demo=not-found` | Evidence detail returns 404 |
| `?demo=conflict` | Audit creation returns 409 data-version mismatch |
| `?demo=invalid` | Audit creation returns 422 validation error |
| `?demo=reviewer-unavailable` | Optional reviewer returns 503 |
| `?demo=reviewer-timeout` | Optional reviewer returns a simulated 504 after the demo delay |
| `?demo=reviewer-malformed` | Optional reviewer reports invalid response, 502 |

The default mock delay makes loading states visible. The reviewer timeout fixture does not wait 35 seconds; the HTTP adapter's actual deadline mechanism is tested separately using a shortened test deadline. None of these are live resilience/MCP checks.

## Verify

```sh
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:browser
```

Browser tests launch mock :3000 and HTTP :3001. Keep both ports free, or only reuse servers running the correct modes. They exercise real Chromium, download and inspect claims, check keyboard/focus behavior, test mobile overflow, and capture screenshots in `evidence/`. Vitest covers schema validation, scenario races, snapshot identity, errors and reviewer isolation. Browser installation requires network access once; this is not required to run the dashboard.

See [B0 handoff](../docs/workstreams/B0_HANDOFF.md) for actual results and integration requirements. B1/B2, live data, Docker, actual MCP, independent human usability and official submission checks are **NOT RUN**.
