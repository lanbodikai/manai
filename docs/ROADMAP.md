# Engineering roadmap — discussion to three workstreams

Current execution status overrides historical discussion below: see [BOOTSTRAP_STATUS.md](BOOTSTRAP_STATUS.md) and [BOOTSTRAP_BOUNDARY.md](BOOTSTRAP_BOUNDARY.md). Shared bootstrap is authorized and implemented; only recorded passing gates count.
## Phase 0 — current: converge and version

Rounds 1 and 2 are complete. Finish Round 3 in QUESTIONS.md. Record explicit answers in DECISIONS.md. Revise thesis/cohort, stack and ownership without deleting earlier decisions. This document is not authorization to start implementation.

## B0 — authorized early frontend work

B can start now under [B_PREBOOTSTRAP.md](workstreams/B_PREBOOTSTRAP.md) using original fixtures and API v0.3. A lead/assigned bootstrap session prepares the baseline independently. B0 does not prove the real-data split gate or submission readiness. B later merges the verified baseline into the same branch and proceeds with B1/B2.

## Phase 1 — shared bootstrap before splitting

The lead/assigned bootstrap session executes setup while B may work on B0; A reviews data assumptions. B coordinates product integration after the baseline:

1. Import the minimal pinned starter using UPSTREAM.md; preserve notices and root judging layout.
2. Get official data/preprocessing/generator/check-data/API working. Validate Docker on the intended demo machine. Verify one actual MCP tool call and the running official /docs payloads; C provider setup is not a prerequisite. If blocked for 15 minutes, request concrete technical help and narrow packaging work; do not silently waive the container requirement.
3. Inspect the chosen cohort's available columns and coverage. Make a go/no-go decision: keep cohort or explicitly revise D05.
4. Make the full product shell load one overview and a clearly labeled original synthetic audit fixture.
5. Review draft Contract v0.3/OpenAPI and its existing synthetic fixtures, generate shared types if useful, and freeze the agreed version. Check one positive and one failure response end to end.
6. Ensure a common committed baseline exists. Create and publish codex/integration as the shared bootstrap/PR base per TEAM_START_HERE.md. Do not assume main exists; the final judged default branch is a separate lead-coordinated step.

**Split gate:** D05–D08 resolved; import/provenance complete; canonical data verified; one real API query and one actual MCP tool call work; official live /docs and MCP tool schemas inspected; owner assignments recorded; contract and fixtures committed; mandatory evaluation IDs agreed; remaining-time cutoffs updated. If data access remains blocked, B may scaffold against fixtures while A resolves setup, but call this partial parallel progress, not a passed gate or real-data validation.

## Phase 2 — parallel slices (three participants)

| A — analysis/audit service | B — product/integration | C — reviewer service |
|---|---|---|
| Cohort, deduplication, scenarios | Full three-view product journey | MCP evidence retrieval and bounded explanation |
| Immutable audit/evidence/claims API | Same-origin routing to A and C | Read A's immutable audit via HTTP |
| Arithmetic and source verification | Containers, UI tasks, report/demo | Grounding, tool-failure and budget eval |

First mergeable slices should land before feature expansion. Keep one recommendation complete. An unfamiliar agent framework, a second cohort or a richer estimator is optional work requiring a scope decision.

## Phase 3 — integration and final evaluation

Merge A's deterministic slice and B's shell, run shared contract tests, then integrate C's reviewer only if ready; the base proceeds independently. Freeze a final scenario and regenerate claims/report numbers from the canonical result. Run real-data checks, base MCP checks, optional C grounding eval, UI tasks and clean Compose startup. Cross-review one another's diffs and evidence. Ship only claims backed by a recorded run.

## Relative budget proposal

Recompute against 15:00 PDT. Preserve at least 20 minutes for submission/access checks and 30 minutes for integration/demo. If around four hours remain: bootstrap 30 min; parallel slice 80 min; agent and integration 50 min; evaluation/report/demo 50 min; submission 20 min; 10 min contingency. Discussion time reduces the implementation budget; do not pretend otherwise.

## Scope-cut order

Cut extra cohorts, optional charts, animation, broad free-form chat and extra model comparisons first. Preserve the three views, one evidence chain, the required minimal live MCP chatbot, correct claims, source labeling, and required startup. If the base chatbot cannot run, mark the slide-aligned submission incomplete and tell the lead that a required part is missing; do not label canned text as live tool use.

## PR/merge sequence

P0: approved baseline/contract/import. A1: deterministic audit + tests. B1: complete fixture-backed UI + container service. Merge A1/B1 after cross-review and passing compatible contracts. A2: real-data sensitivity and contract integration. C1: reviewer service/tool integration. C2: MCP explanation plus grounding eval. B2: integrated UI, packaging, report/demo. Final integrated checks and lead-authorized merge to judged default branch before the submission buffer. No remote action is automatic while planning.

## Release independence

A+B base completion is not gated on C. Finish deterministic summary, required minimal MCP chatbot and M01–M04/R01–R05; keep C behind its optional profile. If C misses the feature freeze, ship the honest base package with its working minimal chatbot and mark the richer reviewer unavailable. The one-command base remains executable regardless of C's dependencies/provider state.
