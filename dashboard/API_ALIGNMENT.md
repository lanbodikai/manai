# API v0.3 and CPU extension v0.4 — B alignment review

Reviewed 17 September 2026 against `5a8d995a624dcd188101de802f75263a512bcc48`, following the user's request to check alignment and acknowledge both versions as official where possible.

## Decision and official references

**Alignment is realistic. B acknowledges v0.3 as the official current team contract and v0.4 as the accepted official CPU-extension specification for implementation.** This is B's acceptance at the user's request, not a claim that A has signed off or that either version's complete service has passed acceptance.

| Reference | Status and use |
| --- | --- |
| [v0.3 OpenAPI](../contracts/openapi.json) | Current runtime/client contract. Bootstrap implements health/overview; full audit/chat integration remains unfinished. |
| [v0.4 OpenAPI](../contracts/proposals/v0.4/openapi.json) and [CPU specification](../contracts/proposals/v0.4/README.md) | Accepted CPU-extension design from B's perspective. Coordinated runtime activation is pending; its existing proposal path is preserved. |

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

1. **Coordinate the version switch.** This is not a drop-in wire-compatible addition. Closed v0.3 schemas reject the new fields and version marker; v0.4 rejects an unmodified v0.3 audit. Current generated TypeScript and Ajv validation use v0.3, and `service/main.py` reports v0.3. Do not emit v0.4 payloads labeled v0.3, strip extension fields silently, or mix schema versions within an audit.
2. **A supplies canonical calculation and semantic validation.** Validate finite inputs and outputs, positive successful CPU duration, `cpu_hours <= trial_cap_hours` when known, current source fingerprint, eligible evidence membership, baseline observations and memory reconciliation. Resolve the selected stable source reference again when creating the new audit; selecting it from an older audit does not grant membership in the new one.
3. **B updates types, validation and presentation together.** Explicitly enable finite-number validation (`strictNumbers: true` or equivalent guards). Select the appropriate supported schema using explicit version handling; an unsupported version is a visible error. Preserve older audits with their own version or return an explicit incompatibility, never reinterpret them. Keep mock, local dataset and HTTP modes distinct.
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
| Positive-infinity input probe | **GAP FOUND:** current `strict: false` configuration accepts positive infinity for `cpu_hours`. An initial assertion expecting rejection failed. Explicit `strictNumbers: true` rejects it. NaN and negative infinity were rejected in the tested field. This review does not change the running validator. |
| Trial cap probe | **SERVICE VALIDATION REQUIRED:** a 12-hour CPU input with a 1-hour cap passes JSON Schema. The specification already requires A to reject this relationship; schema validation alone is insufficient. |
| Active implementation inspection | v0.3 types/validator and bootstrap-only service confirmed; no CPU calculator or v0.4 frontend support found in this checkout. |
| Live v0.4 service, real audit, MCP, Docker, CPU workload experiment and UI adoption | **NOT RUN.** Neither schema acceptance nor synthetic arithmetic demonstrates CPU compatibility, operational savings or live integration. |

The plain `python` command resolved to a Windows Store alias, and `py` lacked `jsonschema`. The successful validator command used bundled Python with `jsonschema==4.26.0` (matching the backend lock) installed only in ignored `dashboard/.work/contract-review-python`:

```powershell
# From the repository root, after installing jsonschema in the ignored directory:
$env:PYTHONPATH = "$PWD/dashboard/.work/contract-review-python"
& 'C:/Users/lanbo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' contracts/proposals/v0.4/validate.py
```

The Node/Ajv checks were read-only inline probes using the existing dashboard dependency. No source records, shared schemas, service code, generated types, runtime behavior or dependency lockfiles were changed. This is builder self-review. Next owner: A confirms adoption and implements the canonical result; B then integrates the version and UI. C can consume the same result independently.
