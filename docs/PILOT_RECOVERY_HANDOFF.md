# Pilot & Recovery — feature handoff

User-authorized A+B feature on `codex/pilot-recovery`. This is not an extension of C or the discarded standalone frontend concept.

## Integration baseline and ownership

The branch starts at A's merged integration `db6f418`, initially merges B's `1ac9071`, then incorporates B's newer `788b5ad` task-table updates without modifying either remote source branch. B's PR #4 remains its original work. The feature PR targets `codex/integration` and includes the pending B changes as a prerequisite; review the feature-specific commits separately if #4 has not landed yet. Feature implementation slices are `2619b31` (A calculator/routes) and `8176249` (B panel/startup); subsequent commits contain integration and evaluation records.

A owns deterministic simulation numbers and source resolution. B displays the returned numbers, saves session snapshots and lets the user revise a proposal. C is not called and cannot block this workflow. Existing audits, cohort estimates and `claims.json` retain their meanings and routes.

## Additive contract agreement

The implementation plan was reviewed against A's existing calculator and B's API adapter before the dependent changes. The feature contract is versioned separately in `contracts/pilot-recovery.openapi.json`; the active audit contract remains v0.4. Existing consumers do not need new required fields in Audit, Scenario or Claims.

- `GET /api/audits/{audit_id}/pilot-baselines` resolves eligible job evidence from the immutable audit. Historical fields come from A, not editable browser baseline values. Missing GPU configuration/runtime fields remain unknown.
- `POST /api/audits/{audit_id}/pilot-simulations` accepts a selected evidence reference, proposed CPU trial and explicit assumptions. It calculates a simulation without creating an execution job or changing the audit.
- Baseline and response identity include audit, evidence and data fingerprint. Source changes invalidate the request; the panel must not reuse another audit's response.
- A's existing `assess_cpu_pilot` supplies the compatible single-job calculations. The wrapper adds setup cost, simulated caps, recovery availability, pause status and detailed accounting. B must not implement replacement financial arithmetic.

## Required behavior

Save the original GPU setup, recorded GPU-hours, runtime and reference cost. Save a proposal with correctness criteria, maximum runtime and a trial spending limit. Run one of three hypothetical outcomes:

| Outcome | Cost and timing |
| --- | --- |
| Success | Trial CPU cost plus setup; net benefit is original reference cost minus that total. Preserve negative benefit if the alternative is more expensive. |
| Failure, recovery succeeds | Stop the trial and model a full original GPU rerun. Total includes trial, setup and original GPU reference cost exactly once. Delay includes the failed trial and additional queue wait. |
| Failure, recovery unavailable | Preserve failure details and known cost so far. Show **Paused — owner action required**. Final completion cost, net benefit and completion delay remain unknown. |

`Net benefit = original reference cost − total trial and recovery reference cost`.

Runtime/spend limits stop the **simulated** trial at the first reached limit. A setup cost greater than the entire budget prevents simulated startup; it is not partially spent. Unknown CPU price or setup cost cannot produce a passed spending check. The trial spending cap excludes the separately displayed GPU recovery cost. Every limit is a simulation assumption, not real scheduler enforcement.

Historical telemetry does not include verified checkpoint restoration, so recovery always assumes a full rerun. A planning checkbox cannot verify a checkpoint. GPU-hours are recorded allocation H, not GPU count multiplied by scheduler duration T.

Each run is an alternative comparison against the saved baseline. It is not an additional real workload attempt, so previous alternatives are not summed as real spending. Session history preserves inputs and results for comparison/download; it is not a durable operational log. Revision marks earlier results as using their saved assumptions instead of silently recalculating them.

## Verification and remaining work

Actual commands and outcomes are recorded in `eval/pilot_recovery/RESULTS.md`. Deterministic, API, UI, real-data, container and operational checks must be reported separately. This feature has no model-generated answer, so repeated stochastic G01–G05 evaluation is not applicable to it; those gates still apply to C when enabled.

Before real automatic recovery is possible, the team needs workload-owner authorization; saved runnable image/command/inputs and original placement; a scheduler control API; verified output comparisons; enforced time/budget monitoring; available recovery resources; checkpoint compatibility and restoration tests; idempotent execution records; durable failure history; and measured billing/queue effects. None is established by a successful simulation.

The next owner is A+B for code review and B for integration/merge coordination. Publishing the feature PR does not authorize a merge, a live workload change, or a judged submission.
