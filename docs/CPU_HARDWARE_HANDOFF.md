# Documented CPU hardware scenario — branch follow-up to PR #8

This local A/B follow-up is authorized by Winston and starts at merged main
`a7087eb`. It ports the bounded scenario from private evaluator `ea6e732`.
No source-derived results or private reports are committed. This branch has not
been merged or published; its additive interface is reviewable here before any
other builder adopts it. C is not involved.

## Interface and ownership

A owns `analysis/hardware_scenario.py` and the two read-only feature endpoints:

- `GET /api/cpu-hardware-scenario?dataset_version=...`
- `GET /api/cpu-hardware-scenario/jobs?dataset_version=...&scenario_id=...&status=all&offset=0&limit=25`

The standalone `contracts/cpu-hardware.schema.json` defines `cpu-hardware-1`.
It does not change adopted v0.4 DTOs or canonical audits/claims. The scenario ID
hashes source identities, hardware, assumptions and calculated outputs. A caches
immutable serialized results after canonical checks; each response is decoded
freshly. Missing/changed data fails explicitly, and stale browser or scenario
identity returns 409. The browser's ordered-checksum version is reconciled with
A's canonical fingerprint. Pagination is bounded at 100 jobs.

B displays A's results in the existing three-tile overview and CPU planner.
Hardware results cover ALL resource-fitting historical jobs, not the manual
planner's small-pilot percentage. Manual estimates remain separate. A positive
success-price range cannot overwrite the official 0/0/1 recovery policy.

## Model

Use the unchanged completed zero-SM cohort. Join requested CPU count and decoded
requested RAM by job ID. Single-node fitting requests reserve the larger of
requested cores and ceil(requested MB / 4000), within 48 cores / 192000 MB.
Multi-node placement stays unresolved. Compare this allocation with reserving
all 48 cores; neither allocation implies a speedup. Requests are not peak usage.

Fix runtime at the original duration and additional queue at zero. CPU reference
prices are 0.005 and 0.02 times the official pinned GPU reference rate, expressed
per physical-core-hour. The existing calculator's vCPU unit is explicitly mapped
to one physical core. Assume baseline host costs are included in GPU pricing.
Compute success, failed replacement/full GPU rerun, and extra validation. Losses
are retained; prices, runtime, compatibility and spare capacity are assumptions.
Neither scenario bounds nor hardware fit are confidence or success estimates.
Setup, migration and business-delay costs remain omitted and visible.

The target is 20% of the same historical sample's reference value. Report both
baseline-reduction percentage and percentage of that target, with the remaining
gap. Do not extrapolate to next quarter. The displayed successful range varies
CPU price only; failure costs are shown separately and the failure execution time
is twice baseline under this fixed model. Additional-validation delay is unknown.

## Reproduction and review

Use standard data provisioning and default Compose; the feature requires no
manual import, model key, new service or external network at runtime. Separate
isolated verification commands and actual outcomes will be recorded under
`eval/analysis/HARDWARE_PRODUCT_RESULTS.md`. Detailed receipts stay ignored in
`private-eval/hardware-product/`. Source tests contain invented records only.

Before a merge, review the additive interface and UI scope labels, execute the
backend/unit/build/browser and real-source checks, and record the exact commit.
Human usability/U05 and operational CPU savings remain separate. Nothing here
authorizes publishing private artifacts, merging the branch or enabling C.
