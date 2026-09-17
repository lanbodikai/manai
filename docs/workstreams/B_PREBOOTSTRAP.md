# B0 — start the dashboard before bootstrap

**Authorized by Winston:** B can begin now against API v0.3 and original synthetic fixtures. This is a narrow exception to the shared split gate. A's real-data acceptance and C's live-tool evaluation remain unchanged. Do not wait for Docker/data/MCP/provider setup to build this slice. Do not dispatch extra agents.

## Start and scope

Use your own clone/worktree. Start from the published `origin/codex/planning` commit containing this file and record its SHA; this is a planning baseline, not a passed bootstrap gate.

```sh
git clone --branch codex/planning https://github.com/lanbodikai/manai.git manai-b
cd manai-b
git switch -c codex/product-integration
git log -1 --oneline
```

If your clone/branch already exists, inspect status and preserve its work; do not recreate or reset it. B keeps this branch when integrating later. Shared bootstrap runs separately on `codex/integration`, owned by the lead or assigned bootstrap session while B works here. B resumes overall merge coordination after bootstrap; B0 does not require one person to run two sessions.

Read [requirements](../REQUIREMENTS.md), [API spec](../API_SPEC.md), [OpenAPI](../../contracts/openapi.json), [synthetic fixtures](../../contracts/examples/manifest.json), [evaluation](../EVALUATION.md), and [full B workstream](B_PRODUCT_INTEGRATION.md). This file takes precedence over statements that B must wait for the split gate, within B0 only.

**Own now:** `dashboard/` including package/lockfile, local readme, components, client adapters, mock support and frontend tests; `docs/workstreams/B0_HANDOFF.md` for results and integration needs. Keep frontend tests under dashboard for this slice. You may add `dashboard/Dockerfile`, but container work is not a B0 gate.

**Leave to bootstrap/A:** root Compose, official import/API/MCP/data paths, analysis/service code, root dependency files, shared contract and fixtures, root claims.json/REPORT.md. Do not edit root AGENTS/README or the integration branch to make your app appear fully integrated. Propose missing contract fields in B0_HANDOFF.md, and isolate temporary display assumptions in the mock adapter.

## Deliver one useful CFO-to-evidence journey

1. Three connected tiles: spending; a specific owned CPU-placement pilot; downside of being wrong. Clear action, reference-dollar range, assumptions, and risk in the first screen.
2. Show the 20% target and a clearly synthetic illustration of the audited contribution/gap with matching units/window. If the current overview contract lacks a required field, document the gap for A rather than silently adding production fields or computing new financial claims in React.
3. Drill down from a dollar range into the audit calculation, evidence list and source detail, with fact/judgment/synthetic labels.
4. Scenario form with explicit low/point/high and price inputs; show pending changes separately from the last calculated immutable audit. Provide at least two matching preset fixture scenarios or a mock-only simulator. Do not display a fixed response as if it reflected arbitrary submitted inputs. Production financial arithmetic belongs to A.
5. Required base MCP chat UI and optional advanced reviewer UI, separately labeled. In fixture mode, every answer is a mock and tool traces do not represent real MCP calls. The base question panel must not require the advanced reviewer to be present.
6. Claims download from the currently displayed audit via the client adapter. In fixture mode use a clearly synthetic filename such as synthetic-claims.example.json; never generate root submission claims.json from mocks.

Favor an immediately understandable dashboard over animation or additional cohorts. Keyboard-accessible controls and a narrow viewport must work.

## Adapter boundary — so this fits back in

Define a typed `DashboardApi` interface matching API v0.3:

```text
getHealth()
getOverview()
listRecommendations()
createAudit(request)
getAudit(auditId)
listEvidence(auditId, page)
getEvidence(auditId, evidenceId)
askBaseChat(auditId, request)       -> /chat, A, required
explainAudit(auditId, request)      -> /explanations, C, optional
exportClaims(auditId, team)
```

- `createHttpApi(...)` sends same-origin `/api/*` requests and normalizes the documented error envelope; no provider keys in the browser. Keep HTTP handling outside components.
- `createMockApi(...)` implements the same interface from original synthetic examples. Extend missing overview/recommendation/page/error fixtures only inside dashboard's test/mock directories and validate them against existing schemas. Do not copy actual organizer records into fixtures.
- Select mode explicitly with separate documented scripts/config. Example: `npm run dev:mock` for B0 and `npm run dev` for live integration. A live request failure must NEVER automatically switch to mock data.
- Keep mock modules out of the live production entry/bundle, and make the explicit mock startup display a persistent “Synthetic demo — no live data or MCP” banner. A normal production build defaults to live HTTP and shows honest unconfigured errors until services exist.
- Use schema-derived or schema-checked types; do not invent a second incompatible DTO layer. Validate outbound requests and representative response/error fixtures. Document any generator/build command.
- Track request identity. Reject or ignore stale scenario responses and mismatched audit IDs in evidence/chat. All drilldowns, questions and exports use the displayed immutable audit, never an unrelated latest response.
- Give each chat path independent timeout/error state. A C error cannot clear the audit, disable export or prevent A's chat UI from being used.

## B0 completion contract

Record commands and results in B0_HANDOFF.md; these are fixture-stage checks, not full submission acceptance:

| ID | Required condition |
|---|---|
| B0-01 | From a clean dependency install, documented local mock command starts the dashboard with no backend, Docker, source dataset or model key. Record Node/package-manager requirements and commit one lockfile. |
| B0-02 | Three tiles → dollar → evidence detail → synthetic claims download works; downloaded values match the displayed fixture audit. |
| B0-03 | At least two scenario results work consistently; an intentionally delayed older response cannot overwrite the current result. Unsupported mock inputs produce explicit error, not misleading fixed numbers. |
| B0-04 | Loading, empty cohort, source unavailable, 404/409/422 errors, C absent/timeout/malformed reply are visible and preserve usable unrelated features. Test base-chat UI while C fails. |
| B0-05 | Representative payloads pass shared schemas; typecheck and production build pass; live mode never falls back to synthetic data and excludes mock modules. |
| B0-06 | Keyboard walkthrough and desktop/narrow-viewport visual check recorded. At least one real browser inspection; if unavailable, mark NOT RUN rather than claim visual acceptance. |

Use focused tests for identity, adapter errors, download consistency and optional-reviewer isolation. Do not add a large framework for future hypothetical features. A short teammate 30-second walkthrough is useful; label self-review honestly if nobody is available.

T/D/M/G/P and real-data parts of U/C/R remain NOT RUN unless actually executed later. Passing mock chat tests is not passing M01. B0 is not B1/B2 completion or submission readiness.

## Commit, review and fit back in

1. Commit a coherent runnable B0 slice and push `codex/product-integration`. Open a draft PR to `codex/planning` if `codex/integration` does not exist; label it **B0 fixture UI — bootstrap pending** and do not merge it into planning. Once integration exists, retarget that same PR to `codex/integration` (inspect the resulting diff).
2. Bootstrap session announces its exact verified commit. Fetch and merge it into B's branch; preserve B0 work and both histories. No shared-branch force push. Resolve only owned conflicts; coordinate shared schema/Compose conflicts with the bootstrap owner.
3. Check API version and actual payloads. Prefer fixing the adapter if implementation differs only in wiring. Breaking schema changes require affected-owner agreement and updated tests/fixtures; do not conceal drift with unsafe casts.
4. Enable the HTTP adapter, add the agreed dashboard service/proxy to root Compose now that bootstrap ownership hands over, and run the same journey with A's real audit and required MCP /chat. Keep C behind its optional profile.
5. Complete B1/B2 and real U/P/M/R gates. Fresh data-provisioned checkout must start on :3000 with `docker compose up`. Root claims/report use a real final A audit. Merge the reviewed B PR into integration only after the relevant slice checks pass; do not wait for C to finish the base.

Handoff file must list: start/current commits, exact changed paths, setup/run commands, API version, fixture coverage, B0 pass/fail/NOT RUN results, screenshots or browser-check evidence if available, contract questions, integration needs and remaining real-data checks. No source data or secrets in the handoff.

## Copy-paste prompt

```text
Start Workstream B0 now for https://github.com/lanbodikai/manai.
Use your own clone/worktree, branch codex/product-integration, from the latest
origin/codex/planning containing docs/workstreams/B_PREBOOTSTRAP.md.
Read AGENTS.md and B_PREBOOTSTRAP.md first, then the linked API v0.3,
requirements and evaluation docs. This assignment explicitly authorizes
frontend implementation before the shared bootstrap/split gate.

Build the complete three-tile CFO-to-evidence dashboard against original
synthetic fixtures, with scenario states, drilldown, base-chat UI, optional
reviewer states and synthetic claims download. Own dashboard/ and
docs/workstreams/B0_HANDOFF.md only for this slice. Do not wait for Docker,
real data, A, C or model keys. Leave root Compose/import/backend/shared
contracts to the bootstrap session.

Use one typed DashboardApi with separate HTTP and mock adapters. Mock mode
must be explicit and visibly synthetic; live failures never trigger mocks.
Production components use A's canonical numbers. Check stale-response and
audit-ID consistency, and keep base UI usable when C fails.

Complete B0-01 through B0-06 as specified, reporting actual results and
NOT RUN checks. Commit/push codex/product-integration and open a draft PR
using the documented temporary-base rule; do not merge before integration
review. Record setup, test results and contract gaps in B0_HANDOFF.md.

When the bootstrap commit arrives, merge it into your branch, retain your
UI work, switch to HTTP, and finish B1/B2 against real A endpoints and the
required MCP chatbot. C stays optional. Do not claim mock work passes live
MCP, real-data or submission checks. Do not dispatch additional agents.
```
