> Merge review update: A/B have already adopted active v0.4 on main. The merged frontend reads `contracts/openapi.json` and `contracts/examples/`, with successful-duration/cap validation and main's live CPU controls preserved. The proposal paths and deployment-pending descriptions below record the earlier B review; they are not the current runtime configuration. See `docs/MAIN_BASELINE_HANDOFF.md` and the PR #8 acceptance record.

# API v0.4 frontend integration — B alignment review

Reviewed 17 September 2026 against `5a8d995a624dcd188101de802f75263a512bcc48`, following the user's request to check alignment and acknowledge both versions as official where possible.

## Decision and official references

**The dashboard now uses v0.4 types and runtime validation.** A still owns deployment of the matching service; until it is available, the interface reports a visible compatibility or connection state rather than accepting a v0.3 response as partial data.

| Reference | Status and use |
| --- | --- |
| [v0.3 OpenAPI](../contracts/openapi.json) | Legacy dashboard contract. A v0.3 health response is rejected with a clear compatibility error. |
| [v0.4 OpenAPI](../contracts/proposals/v0.4/openapi.json) and [CPU specification](../contracts/proposals/v0.4/README.md) | Active dashboard contract. Generated types, Ajv validation, mock fixtures and CPU result display use this version. |

These are **manai team contracts**, not official MantisGrid product APIs. The shared proposal documents still require coordinated A/B adoption; this review supplies B's acknowledgment, without inventing A's agreement or changing the active shared schema. The temporary `preview-1` dataset explorer is separate and is not made official by this decision.

## Why the extension fits

- Routes are identical. Only four existing schemas change: `Scenario`, `Downside`, `Audit`, and `Health`. Five CPU/memory schemas are added. Overview, evidence, errors, explanations and claims retain their shapes.
- The old recovery-only request validates under v0.4. Omitting `scenario.cpu_pilot` preserves that workflow; v0.4 still requires `downside.cpu_pilot: null` and the new version marker in the result.
- Cohort recovery remains a low/point/high scenario. The CPU result is explicitly one selected job, with separate GPU reference value, CPU reference cost, signed net reference value and completion-time change. It must never be added to cohort recovery or subtracted from claims.
- Success, failed trial followed by full GPU rerun, and additional validation have distinct accounting. Failure does not double-charge the original GPU run as incremental loss. Losses and earlier completion remain signed values; unknown cost/delay stays null.
- A resolves historical allocation and scheduler duration from evidence. The browser supplies assumptions, not baseline measurements. Recorded GPU-hours must not be replaced by GPU count multiplied by elapsed time.
- Zero/positive/unknown memory partitions organize investigation without changing the broad eligible cohort or asserting CPU compatibility. Cancellation remains excluded. C remains optional and no provider key is necessary for this deterministic model.

For example, the invented fixture's successful replacement releases 20 GPU-hours worth $50 at its reference rate, adds $4.80 of CPU cost, and completes two hours later. Its $45.20 net reference value is a single-job assumption-based result, not measured cash savings or a cohort forecast.

## Compatibility and adoption requirements

1. **Deploy the matching service.** This is not wire-compatible with v0.3. The dashboard now requires v0.4 and can proxy to `MANAI_V04_URL` (default `http://127.0.0.1:8001`), or call `VITE_MANAI_API_URL` directly when CORS is configured. Do not emit v0.4 payloads labeled v0.3, strip extension fields silently, or mix schema versions within an audit.
2. **A supplies canonical calculation and semantic validation.** Validate finite inputs and outputs, positive successful CPU duration, `cpu_hours <= trial_cap_hours` when known, current source fingerprint, eligible evidence membership, baseline observations and memory reconciliation. Resolve the selected stable source reference again when creating the new audit; selecting it from an older audit does not grant membership in the new one.
3. **Frontend safeguards are active.** Types, `strictNumbers`, request validation, v0.4 mock fixtures and CPU-pilot presentation move together. An unsupported version is a visible error; mock, local dataset and HTTP modes remain distinct.
4. **Preserve snapshot identity.** CPU inputs belong in immutable audit identity. Late scenario/evidence/chat replies cannot replace the displayed audit. Changing only CPU trial assumptions must not alter cohort recovery/claims. Reuse the existing audit-scoped evidence, chat and export routes.
5. **Show assumptions and limits plainly.** The UI needs selected-job evidence, outcome mode, vCPUs, assumed CPU runtime, nullable CPU price/extra wait/cap and host-cost boundary. Render the resulting cost and delay beside the existing qualitative risks. Blank means unknown where null is allowed; zero means an explicitly entered zero. Keep pending edits separate from calculated results.
6. **Verify the integration before activation.** A supplies its implementation commit, versioned health response, real immutable audit and resolvable baseline evidence. B verifies the no-pilot flow and all three modes, signed/null outputs, rejected inputs, stale responses, export invariance and C failure isolation. Shared promotion is coordinated with A; it is not performed by this review.

## Actual checks and findings

| Check | Actual result |
| --- | --- |
| Structural OpenAPI comparison using Node | PASS: identical paths; four changed existing schemas; five new schemas. |
| Existing v0.4 `validate.py` | PASS: six complete fixtures, eight pilot cases, references, invalid-input examples, arithmetic, identity, memory partition and unchanged official claims. This verifies fixtures, not a calculator service. |
| Ajv 2020 validation using the dashboard's installed dependency | PASS: all six v0.3 and six v0.4 manifest fixtures. |
| Cross-version request/audit probes | PASS: old request accepted by v0.4; CPU request rejected by v0.3; audits rejected by the opposite version. |
| Positive-infinity input probe | **RESOLVED IN FRONTEND:** `strictNumbers: true` is explicit in Ajv validation. |
| Trial cap probe | **FRONTEND GUARDED:** `cpu_hours > trial_cap_hours` is rejected before request submission. A must enforce the same relationship canonically. |
| Dashboard implementation | Generated types, validation, mock fixtures, v0.4 connection check and CPU-pilot result presentation are implemented and covered by frontend tests. |
| Live v0.4 service, real audit, MCP, Docker and CPU workload experiment | **NOT RUN.** The live service must still be deployed on the configured v0.4 URL; neither synthetic coverage nor schema validation demonstrates CPU compatibility, operational savings or live integration. |

The plain `python` command resolved to a Windows Store alias, and `py` lacked `jsonschema`. The successful validator command used bundled Python with `jsonschema==4.26.0` (matching the backend lock) installed only in ignored `dashboard/.work/contract-review-python`:

```powershell
# From the repository root, after installing jsonschema in the ignored directory:
$env:PYTHONPATH = "$PWD/dashboard/.work/contract-review-python"
& 'C:/Users/lanbo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' contracts/proposals/v0.4/validate.py
```

The Node/Ajv checks use the existing dashboard dependency. No source records, shared schemas or service code were changed. This is builder self-review. Next owner: A deploys the canonical v0.4 service; C can consume the same result independently.
