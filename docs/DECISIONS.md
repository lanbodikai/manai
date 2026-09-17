# Decision and evidence ledger — v0.1

Statuses: CONFIRMED = official source; DECIDED = explicit user choice; PROPOSED = editable design; OPEN = unresolved; DEFERRED = outside current scope.

## Explicit user choices

| ID | Status | Decision |
|---|---|---|
| D01 | DECIDED | Track 2; complete GPU-efficiency dashboard with one deeply verified recommendation. |
| D02 | DECIDED | Thesis: audit proposed savings and show evidence plus downside. |
| D03 | DECIDED | Two builders/Codex sessions, one per workstream. |
| D04 | DECIDED | Several discussion rounds before implementation; create versioned planning documents now. |
| D05 | PROPOSED | Completed zero-compute jobs as first cohort. |
| D06 | PROPOSED | Official Python API plus React/TypeScript dashboard. |
| D07 | PROPOSED | Dashboard first; bounded MCP agent explains/challenges decisions. |
| D08 | PROPOSED | Builder A: analysis + agent; Builder B: product + packaging/integration. |

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
