# Track 2: slide and repository alignment — v0.6

Sources: the Track 2 slide quoted by Winston; [official brief](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/README.md); [submission format](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/submission.md); [official MCP tools](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/mcp_layer/README.md). All deliverables below are planned, not implemented.

| Requirement | Concrete planned deliverable | Owner / acceptance |
|---|---|---|
| One-command dashboard | Default `docker compose up`, dashboard :3000, C excluded | B / P01, R01–R05 |
| Chatbot or agent using MCP | Narrow template-based chatbot making real official MCP calls; source support, eligibility, assumptions, downside questions | A+B / M01–M04; mandatory |
| Richer evidence review | Model-backed explanation and challenge handling | C / G01–G05; optional enhancement |
| Headline numbers in fixed format, with ranges | Root claims.json from the displayed immutable audit, official schema validation, low/point/high scenario and basis | A / T05–T07, P02 |
| Short report of findings and method | Root REPORT.md: source scope, cohort, exclusions, arithmetic, assumptions, downside, tests, limitations, AI disclosure | A method; B packaging / P03 |
| Actionable in 30 seconds | Three tiles: spend, ranked/owned action, cost of being wrong; headline gives pilot owner, range, risk | B / U05 |
| Dollar-to-data drilldown | Dollar range → calculation → unique jobs → rule/findings and source fields | A+B / D02–D04, U01 |
| Say how sure you are | Separate accounting verification, scenario assumptions and untested CPU compatibility; no invented probability | A+B / T/D/M |
| Data storytelling | CFO question → target gap → evidence-backed pilot → downside → verification plan | B / four-minute rehearsal |

## The 20% target and our narrow verified contribution

The cut is the CFO's target, not a guaranteed discovery. Show it on the spending tile alongside the audited candidate's contribution. Define the baseline from the supplied sample, time window and reference price; do not compare a next-quarter target to a four-month number without labeling the normalization assumption. For a same-window baseline B, target = 0.20B; audited contribution = [L,H]; remaining gap = [max(0,0.20B-H), max(0,0.20B-L)]. A calculates these values; never add overlapping source recommendations to manufacture 20%. Supplied candidates can be visible as unverified judgments. Our single deeply audited pilot may cover only part of the target; say so.

The slide's 594,000 GPU-hours is rounded; repository metadata gives approximately 594,004. Both are source descriptions until local data checks pass. The dataset is a four-month sample (74,849 jobs, 195 users), not evidence of whole-fleet or next-quarter utilization. The catalogue has 24 rules; the data guide says 23 fire to produce 11,979 findings. Distinguish catalogue size from active detectors.

## Short thesis

Help the CFO decide which part of a proposed GPU-spend cut is defensible: audit a completed zero-compute cohort, show a bounded CPU-placement pilot and its downside, then let the viewer inspect and question the evidence through MCP. Verified allocation accounting does not prove CPU compatibility or realized savings.

## Fast execution order

1. Shared bootstrap: import pinned starter/notices, generate/check data, freeze API v0.3, verify one real MCP call, establish common commit.
2. A: deterministic audit/evidence/claims plus four-intent MCP chatbot. B: three tiles, drilldown, chat UI, packaging and report. C: richer reviewer in its own optional image.
3. Merge A+B first. Verify matching headline/export, M01–M04, clean startup and C-failure resilience. These tests can use B-owned failure stubs.
4. Enable C only after its grounding tests pass. Reserve 30 minutes for integration/demo and 20 for submission; recalculate actual remaining time before starting.

Priority: base dashboard + honest ranged claims + required MCP chat + report are P0. Richer C review is P1. Extra cohorts/charts/model comparisons are P2. Missing C cannot block P0, but missing actual MCP usage means the slide-aligned package is incomplete.
