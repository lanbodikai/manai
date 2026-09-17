# Cost-optimization decision table and backend action

This is a **B-owned frontend proposal**, requested by the user. It does not change or claim adoption of team API v0.3 or the accepted v0.4 CPU-extension design. A's inspected branch `05c7fa0` implements deterministic audits, but exposes no multi-fix optimization route. A must agree and implement the action before live modeling can succeed. B has not modified the backend or shared contracts.

## Current dollar display

Task headers show reference-dollar amounts: eligible source GPU-hours × $2.50/GPU-hour, labeled Reference cost, not savings. The reference rate was verified from the running supplied /v1/price-book, version 2026-Q3, on 2026-09-17; it is a pinned reference assumption, not an actual bill or live price feed. The earlier 0–25% what-if recovery range and controls were removed at the user's request. No recoverability or net/cash savings are inferred. Dollar displays do not modify claims or backend requests. Validated pilot costs and actual billing evidence are still needed.

## CPU pilot decision planner

Selecting CPU placement or pressing Compare CPU pilot opens the local planner. See src/pilot-model.ts and src/components/CpuPilotPlanner.tsx. This is user-authorized B planning arithmetic, not an adopted shared contract or A financial audit. The sample 20% target uses total recorded hours × pinned GPU price × 0.2; it is not a forecast of next-quarter spend.

Pilot GPU-hours = eligible cohort hours × selected pilot percentage. CPU core-hours are entered independently for equivalent work. For each scenario: avoided GPU value = pilot GPU-hours × recovery × GPU reference price; net reference benefit = avoided value − CPU core-hours × CPU price − implementation − extra retry reserve. Alternative cost = pilot baseline reference cost − net benefit. Low benefit pairs low recovery/high CPU usage; high benefit pairs high recovery/low CPU usage. Losses are preserved. Target contribution uses positive base-case net benefit only, with no cohort extrapolation.

Unknown costs and performance require explicit entries; defaults only supply proposed pilot limits and clearly illustrative 0/50/100 recovery stress levels. Extra spend under full GPU fallback is high CPU cost + setup + reserve, not a guaranteed loss ceiling. Slowdown and spend are compared with proposed stop thresholds, without operational enforcement; business harm remains unpriced. Break-even CPU hours holds base recovery and other costs fixed. This planner covers CPU only, excluding other selected fixes.

The result is a source-bound immutable snapshot. Editing controls leaves displayed/exported results on the last calculation with an unsaved label. cpu-pilot-plan.example.json is a planning artifact, not claims.json or a pilot approval. Existing POST /api/optimizations still sends only fix IDs; it does not transmit these local planner inputs. A must agree DTOs, parity and validation before canonical financial integration. No real benchmark or cash saving is asserted.

## User experience

Open `http://127.0.0.1:3002/#optimization` in explicit local dataset mode. The page presents eight suggested investigations: CPU placement, idle sessions, low GPU activity, imbalance across GPUs, memory sizing, failed array tasks, timeouts and unsuccessful jobs with no GPU compute. Each has an owner role, percentage, source-hour/job counts, a proposed fix, a trade-off and a link to matching findings. Checkboxes select one or several fixes; the combined exposure counts each job once. The CFO view starts with a storage-style outcome bar and two priority task cards; six further tasks and the full decision table expand on demand. The mutually exclusive bar measures recorded allocation by job outcome, not savings. Legend buttons provide plain-language explanations; categories must reconcile to the sample total. Narrow layouts stack the content.

**Percentages describe exposure, not recovery.** The denominator is all recorded GPU-hours in the verified workload sample, including cancelled jobs. Each row's numerator is the sum of source `jobs.gpu_hours` for distinct, non-cancelled jobs linked to that rule's non-synthetic, job-scope findings. We do not sum `impact_gpu_hours`, combine loss/queue/capacity units, or infer a financial saving. CPU candidates additionally require completed state, zero mean/peak SM activity and more than one recorded GPU-hour. The union of selected job IDs determines the selected percentage; duplicated hours removed are shown separately.

All finding lifecycle states are considered in this historical review. `RESOLVED` means a job finding aged out (more than 30 days before window end), not that someone fixed it. The explorer labels it **Historical**, and labels `ACTION_REQUIRED` **Needs review**; raw fields retain the original values. Node/user/cluster findings can remain action-required after jobs end. This is not current monitoring or proof of savings.

## GET `/api/datasets/decisions`

Query parameters:

- `version`: the exact `catalog.version` from `/api/datasets/catalog`.
- `selection`: comma-separated unique supported fix IDs, or empty for no selection.

The local Vite middleware implements this read-only route against the verified SQLite cache. It returns `DecisionTable` from [optimization.ts](src/api/optimization.ts): `contract_version="optimization-preview-1"`, source version, synthetic flag, full sample denominator/count, excluded synthetic-finding count, eight rows and a deduplicated selection summary. Unknown/repeated fix IDs return 422; a changed version returns 409; missing findings return 503. All rows preserve the eight IDs in [optimization-options.ts](src/optimization-options.ts).

`dataset_version` identifies the preview's checksum combination; it is **not assumed to equal A's existing audit fingerprint**. During production adoption, A must serve a matching catalogue/decision snapshot or agree an explicit mapping. Do not forward it as an official audit fingerprint without that agreement. Normal production mode uses `VITE_DATASET_API_ENABLED=true` only after these dataset routes are connected. Source aggregation is dev-only and excluded from the live production bundle.

## POST `/api/optimizations` — action proposal, backend pending

The **Model selected changes** button calls this route via the existing same-origin `/api` proxy. The local dataset middleware does not intercept it, acknowledge it or invent a result. Missing A returns an explicit error while retaining selections and access to evidence. No financial result is shown until implemented by A. HTTP acceptance alone will not count as successful optimization or live-data acceptance.

Request example (original synthetic identifiers):

```json
{
  "contract_version": "optimization-preview-1",
  "client_request_id": "example-request-001",
  "expected_dataset_version": "example-source-version",
  "mode": "model_only",
  "cancelled_policy": "exclude",
  "fix_ids": ["cpu-placement", "idle-sessions"]
}
```

Suggested acceptance receipt:

```json
{
  "contract_version": "optimization-preview-1",
  "client_request_id": "example-request-001",
  "dataset_version": "example-source-version",
  "mode": "model_only",
  "fix_ids": ["cpu-placement", "idle-sessions"],
  "optimization_id": "example-plan-001",
  "status": "accepted",
  "synthetic": false
}
```

The request supplies selected actions, not client-calculated savings. A must recompute membership from its immutable source snapshot and reject unsupported fixes explicitly. Neither this route nor its UI grants permission to move workloads, terminate sessions or modify infrastructure. A should use the existing v0.3 recovery and v0.4 single-job CPU scenario contract when adding financial assumptions/results; other fixes currently have no agreed recovery estimator. Do not invent default recovery fractions or assume all exposed hours are recoverable.

The frontend validates version/request/selection identity, accepts only `status=accepted`, rejects synthetic receipts in HTTP mode, and keeps **Backend net savings: Not modeled** after acceptance. The follow-up financial-result API/UI is not specified or implemented in this change. Retries for an unchanged selection reuse the same `client_request_id`; A must implement idempotency and reject that ID with different inputs. The client does not automatically retry. A 15-second timeout reports an unknown request status rather than claiming cancellation. Unmounting or changing the selection prevents late responses from appearing as the current result.

## Verification scope

Unit tests cover cancellation/synthetic exclusion, duplicate findings, overlapping fixes, invalid/empty accounting, stale identities, finite percentages, unknown/wrong/synthetic receipts, HTTP errors, request timeout, stable retry identity and superseded selections. The synthetic demo uses the same invented dataset as its explorer and is kept out of HTTP bundles.

Local browser checks use real source percentages and the actual unavailable action route, verify keyboard checkbox selection, evidence links and mobile cards, and separately intercept the action to test a matching acceptance receipt. **That intercepted receipt is UI coverage only, not a running optimizer.** Source-based screenshots remain in ignored `.local-data/evidence/`.

An independent read-only Pandas check against the original prepared tables matched the CPU and idle-session selections and their union. It used source column conditions rather than the decision aggregation implementation. Actual figures were 2.01785% CPU exposure, 5.39872% non-cancelled idle-session exposure and 6.82145% for their deduplicated union. These are historical sample exposure figures, not estimates of achievable savings.

Live multi-fix financial modeling, v0.4 CPU calculations, actual interventions, MCP grounding and whole-application Compose integration remain **NOT RUN**. Next owner: A reviews the route/identity semantics and delivers the canonical modeling endpoint; B connects its financial result UI after the contract is agreed.
