# Workstream B — dashboard, packaging and integration

Plan v0.6 / Contract v0.3. Owner: Builder B, person/session TBD. Status: NOT STARTED; activate only after ROADMAP split gate.

## Mission

Ship the complete decision journey and required package while Builder A supplies canonical analysis and C supplies the reviewer service. Make the evidence chain and consequences understandable in a short demo.

## Owned paths

`dashboard/`, `tests/ui/`, `tests/integration/`, root `docker-compose.yml`, team Dockerfiles, README.md implementation sections, REPORT.md, demo assets and CI configuration if needed. Confirmed merge coordinator and proposed bootstrap integrator for upstream import; preserve A/shared contracts. Do not alter official source semantics for a nicer chart.

## Components and functions

- `loadOverview()` / `OverviewView`: sample/window, price book, spending breakdown, supplied caveats.
- `loadRecommendations()` / `RecommendationList`: identify supplied judgments and the one audited recommendation; no invented rank labels.
- `submitScenario(input)` / `ScenarioControls`: validate obvious form bounds, send server request, retain request identity, suppress stale responses.
- `renderAudit(result)` / `AuditDetail`: action, owner role, eligible versus recoverable quantities, range and interval kind.
- `renderDownside(result)` / `DownsidePanel`: assumptions and unmeasured consequences; do not manufacture dollars for unknown harm.
- `openEvidence(id)` / `EvidenceDrawer`: source ID, calculation grain, relevant fields, provenance, synthetic label and error state.
- `askExplanation(question,auditId)` / `ExplainPanel`: use A's required `/chat` route by default and offer C's `/explanations` route only when available, show tool-backed citations and status; never substitute canned text for a failed live call.
- `downloadClaims(auditId)`: get server export; compare displayed scenario to exported audit ID.

Dashboard functions do formatting and interaction; A owns financial arithmetic. Favor one clean view with drill-downs over many disconnected pages.

## Build order

1. Import/bootstrap with shared gate; add port-3000 service and preserve official API/data mounts.
2. Render complete three-view journey from original synthetic fixtures, labeled as development mode.
3. Wire deterministic real API responses, source recommendation labels and evidence links.
4. Integrate MCP explanation, failure states and scenario updates.
5. Assemble report from A's recorded results; describe which features are ours versus starter; complete AI disclosure and run instructions.
6. Perform fresh-start test and four-minute rehearsal. First 30 seconds must communicate action/range/risk.

## Completion contract

**B1 product slice:** U01 fixture path, U02–U04 pass; three views present; errors/empty states tested; :3000 container responds. Mock mode cannot satisfy real-data acceptance.

**B2 integrated slice:** U01 on real data, U05 recorded, P01–P03 and M01–M04 pass; claims and UI agree; A's analysis results linked; C status reported separately; one complete reproducible flow; REPORT.md and disclosure finished; no unsupported extra claims.

## PR and merge

Branch `codex/product-integration` from common baseline, own worktree. If publishing is authorized, open draft B1 after the complete synthetic journey works. Mark ready after B1 contract; A cross-reviews units, labels, scenario/export consistency. Lead merges compatible A1/B1; B integrates A2 and prepares B2 independently of C. Integrate C1/C2 only after its checks pass; base must not wait for C. Final merge only after full actual test results and lead authorization. Publishing the repository does not submit the event form.

## Final report to lead

Commit, running URL, startup command, checks actually run, current data mode, agent provider/config needs, presentation outline, outstanding limitations, submission-ready yes/no with reason. Do not say ready if a missing API key is hidden by mock responses.

## Optional-service acceptance

B owns R01–R05 resilience tests. Default Compose excludes reviewer build/startup via profile. Minimal live MCP chatbot, deterministic summary, all evidence paths, scenario calculations and export work with C stopped and no model key. C can be integrated later without changing these base guarantees. Mark base complete independently of C; explicitly report agent status and its optional profile command.
