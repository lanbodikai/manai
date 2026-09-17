# Real local dataset preview

This temporary frontend development mode supplies the requested real-data charts and database browser before A exposes general dataset endpoints. It is explicit and read-only. It does not replace the analysis service, calculate savings, generate claims, or call a model/MCP. Featherless is not required.

## Open it

The prepared local preview is at **http://127.0.0.1:3002** while `npm run dev:local` runs. The original B0 synthetic dashboard remains available with `npm run dev:mock` on :3000. Normal `npm run dev`/build remain HTTP mode with no data fallback.

To reproduce from this dashboard directory on Windows with Python 3.12 and Node 22:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r tools/preview-requirements.txt
.venv\Scripts\python tools/prepare_preview.py --official-root C:\Users\lanbo\mantisgrid
npm ci
npm run dev:local
```

`--official-root` is an existing Track 2 checkout containing `scripts/prep_data.py`, `scripts/checksum_data.py`, `data/checksums.txt` and the two downloaded CSVs under `data/raw/`. It may be a different path on a teammate's machine. On Linux/macOS use `.venv/bin/python`. Stop the local preview before rebuilding its cache, then restart it.

The preparation tool calls the **unmodified official prep functions** using the supplied numeric dependency versions. Output goes only to ignored `dashboard/.local-data/`. It checks both prepared tables with the official semantic digest function and refuses to publish a cache if either differs. It creates a private SQLite browsing cache. It does not modify the official checkout or run the organizer's generator. Optional findings are imported only if `data/synthetic/findings.json` exists and passes its official digest; otherwise their count is unknown and the page explicitly reports unavailable.

The Vite development middleware opens SQLite read-only, binds to loopback and serves bounded JSON pages. No raw data is placed in `public/`, embedded in a production bundle, or committed. Node 22 currently prints an experimental SQLite warning for this explicit local mode. The database is a disposable browsing cache, not a production persistence decision.

## What is browsable

- Front page: recorded GPU-hours → estimated active GPU-hours → active GPU-hours in completed jobs; separate outcome chart whose bars open matching jobs.
- Jobs: final state, first machine, GPU count, recorded hours and average activity. Search all fields, filter by outcome or physical machine/card, sort and page. Detail exposes all 65 prepared job fields, its physical cards and their complete source fields.
- GPUs: one physical card identified by **Node + gpu_id**, never gpu_id alone. Detail lists up to 100 per-card job records, all their available fields, and a link to browse **all** jobs on that specific card.
- Machines: per-card placement attribution and workload exposure. Job filters use the GPU table's actual `Node`, not just `primary_node`, so wide/requeued workloads remain discoverable.
- Findings: available only when the generated file is supplied; per-record synthetic labeling remains explicit. Unavailable findings do not block jobs/cards/machines.

Search and sorting run against the entire matching dataset in SQLite. The browser receives 20 records per page, maximum API limit 100. Nulls display as **Not recorded**. Snapshot versions are attached to every request; mismatch returns 409. POST/write requests return 405. SQL search uses bound parameters, treats wildcard characters literally, and allows sorting only by displayed fields.

## Important data definitions

The overview uses the supplied API's arithmetic for its telemetry activity proxy. Stages are nested, not additive; they are not savings. `gpu_hours` retains the official reported telemetry hours, including its documented measurement quirks, so it reconciles with the prepared tables. Per-card averages use duration bounded by the final job walltime; `bounded_gpu_hours`, anomalous-duration flags and attempt counts are separately exposed. Requeue histories can mix placements; neither failure counts nor exposure diagnose faulty hardware.

Time remains labeled as an approximately four-month sample with **relative offsets**. The preview does not invent calendar dates, prices, budgets, CPU compatibility or cash savings. It contains no researcher waste ranking. Unknown terminal states and cancellations stay distinct.

## Frontend-owned endpoint proposal

These routes are implemented only by this explicit development bridge. They are **not additions to the frozen shared API v0.3** and have not been accepted by A. `DashboardApi.datasets` is an optional capability; existing v0.3 methods are unchanged. Shapes and runtime validators live in `src/api/dataset.ts`, version `preview-1`.

| Method | Proposed route | Result |
| --- | --- | --- |
| GET | `/api/datasets/catalog` | Version, source scope, collection counts/availability, node filter choices, optional overview summary |
| GET | `/api/datasets/{jobs,gpus,machines,findings}` | Version-bound filtered/sorted page |
| GET | `/api/datasets/{collection}/{encoded-id}` | Full record, related links, bounded per-card activity and caveats |

List query: `version`, `query`, `node`, optional `gpu=0|1` together with `node` on Jobs, `outcome`, `sort`, `direction=asc|desc`, `offset`, `limit`. Detail query requires `version`. IDs are opaque and encoded; a card ID includes its machine. Counts may be null with `available:false`; absent data must never be zero-filled.

After A agrees the routes, `VITE_DATASET_API_ENABLED=true` explicitly enables the HTTP dataset adapter. Same-origin routing must be configured by integration. The default remains disabled and visibly unavailable. Remove the development middleware from deployment; components and adapter shapes can be reused after agreement. Do not silently present this browsing cache as A's audited results.

For development, `/api/*` proxies to `http://127.0.0.1:8001` or the process environment's `MANAI_ANALYSIS_URL`. The local dataset middleware handles its own read-only routes first. Unreachable A produces a structured 503, never sample data. Its unfinished recommendations route does not hide a successful source overview. Docker deployment routing and live audit/chat acceptance remain separate integration work.

## Actual verification

The local run produced 74,849 jobs, 96,893 GPU-job records, 450 physical cards and 225 machines. Both jobs/GPU semantic checksums passed. No generated findings file was available. This is **two-file browsing verification**, not the five-file bootstrap/D01 gate.

Run `npm test`, `npm run build`, `npm run test:browser`, and—with a prepared local cache—`npm run test:local`. The last command exercises real-data HTTP and browser behavior: charts, outcome drilldown, full fields, physical GPU history, paging, narrow layout, missing findings, read-only routes, snapshot rejection and literal search. It saves real-data screenshots only under ignored `.local-data/evidence/`. Synthetic screenshots remain under `evidence/`.

Real audit/recovery claims, live MCP, production dataset routes, Docker integration and final submission checks remain separate work.
