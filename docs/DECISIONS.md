# Decision and evidence ledger — v0.6

Statuses: SUPERSEDED = retained historical decision; CONFIRMED = official source; DECIDED = explicit user choice; PROPOSED = editable design; OPEN = unresolved; DEFERRED = outside current scope.

## Explicit user choices

| ID | Status | Decision |
|---|---|---|
| D01 | DECIDED | Track 2; complete GPU-efficiency dashboard with one deeply verified recommendation. |
| D02 | DECIDED | Thesis: audit proposed savings and show evidence plus downside. |
| D03 | SUPERSEDED | Initially two builders; D10 adds a third participant. |
| D04 | DECIDED | Several discussion rounds before implementation; create versioned planning documents now. |
| D05 | DECIDED | Completed zero-compute jobs as first cohort; CPU-placement pilot is the proposed action, compatibility remains unverified. |
| D06 | DECIDED | Official Python API plus React/TypeScript dashboard. |
| D07 | DECIDED | Dashboard first; bounded MCP agent explains/challenges evidence. |
| D08 | DECIDED | Builder A: analysis/audit service; Builder B: React dashboard/packaging/integration; B coordinates merges. Enhanced MCP explanation moves to C under D10; the mandatory minimal MCP chatbot remains in A/B under D12. Individual identities remain unassigned. |
| D09 | DECIDED | Include a specific checklist for importing official Track 2 code plus agreement/license/attribution. Import execution is not yet activated. |
| D10 | DECIDED | Third participant owns the enhanced MCP evidence-review/explanation service; separate workstream C. |
| D11 | DECIDED | A+B must remain fully functional if C is disabled, unavailable or unstable. C is an optional enhancement, never a base startup dependency. |

## Official requirements

Reference snapshot: MantisGridAI/hackathon-2026-official at `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`, inspected September 17. These are source descriptions, not evidence that the provided code runs locally.

| ID | Status | Requirement / implication | Source |
|---|---|---|---|
| F01 | CONFIRMED | One project, one nominated track; deadline September 17, 15:00 PDT. | [Agreement](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/PARTICIPANT_AGREEMENT.md) |
| F02 | CONFIRMED | Three tiles: spending, specific owned recommendation, cost of being wrong. | [Track 2 brief](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/README.md) |
| F03 | CONFIRMED | Root compose file, claims.json and REPORT.md; one-command startup; dashboard :3000. | [Submission](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/submission.md) |
| F04 | CONFIRMED | Public repository; AI-use disclosure; around four-minute working presentation. | Submission + agreement |
| F05 | CONFIRMED | Keep data local; organizers regenerate the expected five files before judging. | [Data setup](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/data/README.md) |
| F06 | CONFIRMED | API/MCP use, evidence, actionability and calibration matter; Layer B is proposed and open to challenge. | [API guide](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/api.md) |
| F07 | CONFIRMED | Findings overlap; impact scopes/kinds differ; cancellation treatment changes interpretation; sample is not the whole fleet. | [Traps](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/traps.md) |
| F08 | CONFIRMED | The shared-volume incident is synthetic; preserve that label. | Traps |
| F09 | CONFIRMED | New judged work is created during the event; licensed public starters are allowed; disclose our added functionality. | Agreement |

## Conflicts and careful conclusions

- **Claims requiredness:** prose says all but team are optional. Actual schema requires `recoverable_gpu_hours`; validator uses that schema. Plan to include team plus a defensible recoverable estimate with low/point/high, basis and interval_kind. Other uninvestigated claims stay omitted. Ask organizer about conflict; do not invent data to satisfy it.
- **Scoring weights:** agreement publishes overall 40/30/20/10 criteria. Other files contain differing statements about accuracy/calibration shares. Do not claim a verified Track 2 numeric weighting from those fragments.
- **Commit selection:** root README mentions selecting a commit; detailed track submission says default branch at clone time with no commit field. Prepare the desired final default branch before deadline and verify the actual form.
- **MCP prominence:** deck explicitly asks for a chatbot/agent; README describes chat as an example. A small real tool-backed explanation flow covers the stronger expectation without making it the whole application.
- **Validator confidence warning:** it checks top-level `_confidence` fields and can warn despite a nested recoverable estimate confidence. Inspect warnings; do not add unrelated unsupported claims solely to silence them.
- **Validation limits:** official claims validator checks schema and HTTP availability; it does not establish arithmetic correctness or UI semantics. Add our own contract tests.

## Deferred

Track 1; live remediation; training a router; optimizing all 24 rules; identifying people; forecasting annual cash savings; multiple frontends; reproduction of external papers. A later explicit decision may change these, but do not drift silently.

## Local environment observation

Docker CLI is present. A read-only check from the restricted session could not access Docker configuration and found no docker_engine pipe. This does not establish readiness on the actual demo machine; engine access remains UNVERIFIED. No application/data/evaluation checks were run. Clarify the active machine/provider and execution phase before setup.

## D12 — slide alignment (user requirement; implementation design proposed)

User requires alignment with the quoted Track 2 slide, including its explicit MCP chatbot/agent deliverable. A+B therefore include a minimal template-based chatbot making real MCP calls; C adds richer review. This reconciles D07/D10/D11 without dropping a required feature. Static summaries do not satisfy chatbot acceptance. The 20% cut is a business target, not a result we may assert; show audited contribution and unmet gap with a matching denominator. See REQUIREMENTS.md.

## Official documentation review — v0.7

See [TRACK2_REVIEW.md](TRACK2_REVIEW.md). The actual claims schema explicitly permits scenario intervals and says recoverable_gpu_hours is assessed on reasoning and interval honesty, not one correct numeric answer. Keep scenario modeling, justify its assumptions (D06), and avoid implying that our chosen recovery estimate has a hidden numeric ground truth. The selected CPU-placement remedy already appears in the official rules. The repo calls chat an example; the stronger slide wording motivates our required base chatbot, whose template-based design remains our interpretation.

## Team handoff update — v0.8

User authorized publishing the plan/setup branch. See [TEAM_START_HERE.md](../TEAM_START_HERE.md) for bootstrap execution assignments, current phase, exact branch strategy and A/B/C ownership. No runtime bootstrap has yet been performed. Historical activation questions must not override an explicit subsequent session assignment.

## D13 — B0 early frontend work (DECIDED, v0.9)

User authorized B to start before bootstrap and fit back in afterward. Scope: isolated dashboard with original fixtures and typed mock/HTTP adapters; no shared import/backend/root Compose edits during B0. Separate bootstrap session establishes integration baseline, which B merges into its existing branch. B0 has its own completion checks and cannot substitute for real-data/MCP/packaging checks. See [B_PREBOOTSTRAP.md](workstreams/B_PREBOOTSTRAP.md).

## D14 — Common-base execution (DECIDED)

Winston authorized executing the common bootstrap in goal mode through the split completion contract, with frozen code boundaries and minimal manual work. Work happens in an isolated codex/integration worktree; B0 remains independent, C begins after the shared base. Provider configuration does not gate bootstrap. Ignore rules and Docker-context exclusions cover local credentials and datasets. User requested a hackathon time budget; a 15-minute remaining-work target was announced at 18:05:44 UTC. Actual gate evidence is in BOOTSTRAP_STATUS.md.
