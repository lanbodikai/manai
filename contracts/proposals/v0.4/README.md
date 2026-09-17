# CPU pilot cost and delay — proposed API v0.4

**Adopted on Workstream A after recorded A/B agreement.** Winston confirmed B accepted this exact ce6a44e proposal; A recorded acceptance in PR #2 before promotion. The active schema now matches this proposal. B must regenerate clients before switching. The original proposal rationale below is retained as history; its pending-adoption statements are superseded on this branch.

**Reviewable proposal, not the active API.** The runtime and B0 continue using `contracts/openapi.json` v0.3. This directory contains the complete proposed OpenAPI and original synthetic fixtures. A/B agree this version before promoting it and regenerating clients. Publishing the proposal on main is not runtime adoption or a passed implementation gate.

The user requested API/fixtures and an A/B handoff, not implementation of A's calculator in this update. The verified bootstrap remains intact. C stays optional.

## Changes from v0.3

- `Scenario.cpu_pilot` is an optional input. Omit it for the existing recovery-only flow. All nested fields are required when supplied; unknown CPU price, extra queue time and trial cap are explicit nulls.
- `Downside.cpu_pilot` is a required nullable result in v0.4. Null means no quantified pilot scenario was requested. Qualitative risks/guardrails remain available. `status=scenario` means assumed cost/delay was calculated, not that intervention harm was measured.
- `Audit.eligibility.memory_partition` is optional: zero-memory, positive-memory and unknown-memory counts/hours partition the existing broad cohort. Unknown is never folded into zero. The three groups must reconcile to broad totals. This is a priority view, not a new cohort or proof of CPU compatibility.
- Audit/health `contract_version` becomes `0.4` on adoption. Routes, error envelope, Explanation and official Claims shapes do not change.

The existing schemas are closed. Do not insert these fields into v0.3 responses or change its version string without coordinating B's strict validator. The new version deliberately requires an explicit client update.

## Inputs and measurement scope

`cpu_pilot` contains `mode`, `baseline_evidence_id`, `cpu_vcpus`, `cpu_hours`, `cpu_vcpu_hour_usd`, `extra_queue_hours`, `trial_cap_hours`, `baseline_host_costs_included` and `assumption_note`. GPU price remains `Scenario.usd_per_gpu_hour`; do not introduce a second inconsistent GPU rate.

A resolves the baseline evidence to **one eligible job in this audit**, using the same source fingerprint. Source-derived `gpu_count`, elapsed walltime and recorded GPU-hours belong in the output baseline; they are not editable client inputs. Missing/nonpositive required baseline measurements reject that pilot request with `422 INVALID_SCENARIO`, without invalidating previous audits. Unknown/nonmember references use the existing scoped evidence error. Source-version mismatch remains 409.

Baseline evidence must expose completion state, average/peak SM, recorded GPU-hours, GPU count, scheduler walltime and maximum GPU memory with units and missingness. An opaque ID without observations does not demonstrate eligibility. Synthetic evidence keeps its synthetic provenance; real historical observations and hypothetical intervention outcomes remain separately labeled.

**Recorded GPU-hours and scheduler duration are distinct.** A uses recorded allocation `H` for released capacity, and observed scheduler hours `T` for runtime comparison. The prototype uses `g*T` and deliberately chooses a record where it matches; do not generalize that equality to every job. Document discrepancies in `baseline.accounting_note`, and test them when adapting the calculator.

## Deterministic calculation

Let `H` = baseline recorded GPU-hours, `T` = baseline elapsed hours, `v` = assumed vCPUs, `C` = assumed CPU hours, `pG` = GPU reference rate, `pC` = nullable vCPU-hour rate, and `Q` = nullable extra queue/recovery wait relative to baseline. Extra waiting is nonnegative in this limited model. CPU duration must be positive for a successful replacement and nonnegative otherwise. Reject `C > trial_cap_hours` when a cap is supplied; that is input validation, not watchdog enforcement.

| Mode | Released GPU-hours | Remaining GPU-hours | Runtime change before extra queue |
|---|---:|---:|---:|
| `replacement_success` | H | 0 | C - T |
| `replacement_failure` | 0 | H | C |
| `additional_validation` | 0 | H | unknown |

Failure assumes a full original GPU rerun at the original runtime, no reused CPU progress. The original GPU cost is part of both baselines and must not be charged twice as incremental loss. Additional validation retains the original run; its completion impact is unknown because scheduling/contention is not modeled.

- Added vCPU-hours = `v*C`.
- Released GPU reference value = `released_gpu_hours*pG`.
- Added CPU reference cost = `v*C*pC`, or null when the rate is unknown.
- Net reference value = released GPU value minus CPU cost **only when** CPU cost is known and `baseline_host_costs_included=true`; otherwise null. That flag records an assumption that the original GPU rate covers original host/CPU costs. Migration/setup/storage/business-delay costs remain excluded.
- Total completion change = runtime change + Q only when both are known. Preserve negative values (earlier completion) and negative net reference value (loss).

Keep legacy `downside.money` and `money_unit` null for this feature. Those fields cannot express several metrics or signed net value safely. B renders named metrics from `cpu_pilot`, with units and unknown states. `evidence_kind=scenario_estimate`; compatibility, cash savings and tested stop enforcement stay false.

This result covers **one job**, while `Audit.recovery` covers the selected cohort under its existing recovery assumptions. Do not sum pilot output into cohort recovery, extrapolate one job's runtime to the whole cohort, subtract it from official claims, or label it realized/net cohort savings. `Claims` stays unchanged.

## Fixtures and checks

`examples/manifest.json` maps six complete payloads to their schemas. `pilot-cases.json` contains eight hand-worked, original synthetic cases: success, failure, additional validation, expensive CPU loss, unknown CPU price, unknown queue, incomplete pricing boundary and earlier completion. Baseline J2 is invented: 2 GPUs, 10 hours and 20 recorded GPU-hours. None of these fixtures is copied from organizer data.

Run from the repository root:

```sh
python contracts/proposals/v0.4/validate.py
```

Requires `jsonschema` (already present in the bootstrap runtime). This checks schemas, fixture arithmetic/identity, negative and unknown values, and unchanged official claims. It is not a test of A's service, B's UI or C's live answers. Prototype unit tests and the offline data verifier were run separately; see the review record.

## A/B/C adoption handoff

1. **A/B:** review this exact proposal commit, agree field names and one-job scope, then promote OpenAPI/examples together. No promotion is implied by publication. Include C in review of consumed output; C availability cannot block the base.
2. **A:** adapt the pure calculator under owned paths, resolve server-side baseline evidence, preserve recorded allocation, normalize errors and include pilot assumptions in immutable snapshot identity. Recompute on pilot-input changes. Recovery/claims must not change solely because CPU trial assumptions changed. Add finite-input/output, cap, baseline mismatch, pricing-boundary and evidence-membership cases.
3. **B:** regenerate types/validators; implement pilot controls and cost/delay/unknown display against these fixtures, then real A. Keep B0 working until the coordinated switch. Display selected-job scope alongside the separate cohort recovery range. Verify late responses, drill-down and export remain tied to the displayed audit. Keep C failure isolated.
4. **C:** consume the same `downside.cpu_pilot`; explain failure versus extra validation, negative value and unknowns with MCP evidence. Do not recompute canonical money or infer probabilities/compatibility. Existing Explanation schema suffices; baseline IDs must resolve within the audit.

Use existing T05/T06/T07, C01/C04/C06, U02/U03, M02/M03 and optional G01–G05 cases. Add focused cases to their coverage, not a new testing framework. API/interaction/model tests remain NOT RUN until those implementations exist. The base chatbot must explain these fields without C or provider keys.
