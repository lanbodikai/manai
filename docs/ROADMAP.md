# Engineering roadmap — discussion to two workstreams

## Phase 0 — current: converge and version

Rounds 1 and 2 are complete. Finish Round 3 in QUESTIONS.md. Record explicit answers in DECISIONS.md. Revise thesis/cohort, stack and ownership without deleting earlier decisions. This document is not authorization to start implementation.

## Phase 1 — shared bootstrap before splitting

Once activated, use Builder B as merge coordinator and proposed bootstrap integrator (A reviews data assumptions):

1. Import the minimal pinned starter using UPSTREAM.md; preserve notices and root judging layout.
2. Get official data/preprocessing/generator/check-data/API working. Validate Docker on the intended demo machine. If blocked for 15 minutes, request concrete technical help and narrow packaging work; do not silently waive the container requirement.
3. Inspect the chosen cohort's available columns and coverage. Make a go/no-go decision: keep cohort or explicitly revise D05.
4. Make the full product shell load one overview and a clearly labeled original synthetic audit fixture.
5. Review draft Contract v0.2/OpenAPI and its existing synthetic fixtures, generate shared types if useful, and freeze the agreed version. Check one positive and one failure response end to end.
6. Ensure a common committed baseline exists. If publishing is authorized, establish main before creating workstream PR branches; an empty remote has no useful PR base.

**Split gate:** D05–D08 resolved; import/provenance complete; canonical data verified; one API query works; owner assignments recorded; contract and fixtures committed; mandatory evaluation IDs agreed; remaining-time cutoffs updated. If data access remains blocked, B may scaffold against fixtures while A resolves setup, but call this partial parallel progress, not a passed gate or real-data validation.

## Phase 2 — parallel slices

| Builder A | Builder B |
|---|---|
| Canonical cohort, overlap audit, recovery/downside model | Complete overview → recommendation → detail → evidence journey |
| Actual service responses and claim export | Scenario controls, clear provenance/uncertainty/error states |
| MCP explanation and grounding eval | Compose :3000 startup, browser integration and demo package |
| Independent recomputation and report methodology | End-to-end test, report assembly and four-minute story |

First mergeable slices should land before feature expansion. Keep one recommendation complete. An unfamiliar agent framework, a second cohort or a richer estimator is optional work requiring a scope decision.

## Phase 3 — integration and final evaluation

Merge A's deterministic slice and B's shell, run shared contract tests, then integrate the agent. Freeze a final scenario and regenerate claims/report numbers from the canonical result. Run real-data checks, grounding eval, UI tasks and clean Compose startup. Cross-review one another's diffs and evidence. Ship only claims backed by a recorded run.

## Relative budget proposal

Recompute against 15:00 PDT. Preserve at least 20 minutes for submission/access checks and 30 minutes for integration/demo. If around four hours remain: bootstrap 30 min; parallel slice 80 min; agent and integration 50 min; evaluation/report/demo 50 min; submission 20 min; 10 min contingency. Discussion time reduces the implementation budget; do not pretend otherwise.

## Scope-cut order

Cut extra cohorts, optional charts, animation, broad free-form chat and extra model comparisons first. Preserve the three views, one evidence chain, a functioning bounded agent if feasible, correct claims, source labeling, and required startup. If the agent cannot run, expose that limitation and tell the lead that a desired/possibly expected part is missing; do not label canned text as live tool use.

## PR/merge sequence

P0: approved baseline/contract/import. A1: deterministic audit + tests. B1: complete fixture-backed UI + container service. Merge A1/B1 after cross-review and passing compatible contracts. A2: real MCP explanation + eval. B2: integrated UI, packaging, report/demo. Final integrated checks and lead-authorized merge to judged default branch before the submission buffer. No remote action is automatic while planning.
