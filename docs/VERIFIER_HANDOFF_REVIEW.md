# Independent CPU-pilot handoff review — 2026-09-17

## Decision

Accept the deterministic CPU-pilot cost/delay model for A's implementation handoff. Preserve the broad completed zero-compute cohort; expose zero/positive/unknown GPU-memory partitions only as investigation priorities. C explains and challenges the canonical result. A/B remain independent of C.

This revises v0.10's qualitative-only implementation recommendation. Qualitative risk remains a valid fallback, but the supplied calculator makes a quantified **hypothetical** cost/delay scenario practical. The existing v0.3 closed schemas are insufficient for CPU units, signed net value and completion delay. A [complete v0.4 proposal](../contracts/proposals/v0.4/README.md) now includes these fields and synthetic fixtures; active v0.3 is unchanged until A/B adopt it together.

User scope: update API/fixtures and handoff for A/B, then publish the validated base update directly to main. No calculator service, frontend changes or optional C implementation are included. The attached document's implementation/PR instructions are recommendations, not additional user authorization.

## Reviewed inputs and provenance

Local attachments: `feedback_result_handoff.md` and `cpu_pilot_base_handoff.zip`. The bundle manifest's seven file hashes matched; the standalone handoff matched its bundled copy byte-for-byte. The bundle contains the calculator, 12 synthetic unit tests, offline real-data harness, usage/results notes and manifest; it does not contain the private row evidence.

- Calculator SHA256: `870f1f42983117dcbf7a00fae10c6d40d1980daa0d9b83213b99418affb16f79`.
- Unit tests SHA256: `45d81d3f46469702a5395657aa4f321146e597930733cce1f2066333f9db0b7c`.
- Data harness SHA256: `d8256d9f4658398aba8fdc4972c3fea481aed8c610bdce149cebda1487a7f282`.
- Handoff SHA256: `211d6899079b5f186f3532318b34bbe8ea3a41d3436d542587bbef6d839d22b8`.

The handoff reviewed old planning revision `588ea66`. Current published integration handoff is `ee529ee`, with verified implementation baseline `7530865`. The bootstrap's progress supersedes the attachment's claim that no common base is available; it does not imply A's full analysis exists.

## Checks actually performed in this review

| Check | Outcome and scope |
|---|---|
| Bundle manifest and standalone handoff comparison | PASS; seven hashes and exact handoff bytes agree. |
| `python -m unittest discover -s tmp/verifier-review -v` | PASS, 12/12 supplied synthetic calculator tests. Run with bundled Python; no workload or model calls. |
| Host offline harness attempt | FAILED before analysis: host PyArrow 19.0.0 raised `Repetition level histogram size mismatch`; no source modification. Bundled Python lacked PyArrow. |
| Same reviewed harness in `manai-bootstrap-analysis-1`, `--track-dir /app` | PASS, RD01–RD17, using pandas 3.0.5 / PyArrow 25.0.1 against read-only data. Ran via `docker exec -i ... python -`, loading the reviewed modules and writing only temporary private outputs. |
| Reported cohort/card/memory results | Reproduced by that harness, including independent row-loop versus Pandas selection and both official prepared-table value hashes. Source rows/results remain local, not committed as fixtures. |
| `python contracts/proposals/v0.4/validate.py` | PASS using host Python/jsonschema: six full examples, eight synthetic cases, schema/reference checks, invalid inputs, signed/unknown values, identity, memory reconciliation and official claims schema. Bundled Python lacked jsonschema; no dependency files were changed. This is proposed C01 coverage, not service acceptance. |
| `docker exec manai-bootstrap-analysis-1 python scripts/checksum_data.py` | PASS, all five canonical files, independently of the verifier's two-table check. |
| `docker exec manai-bootstrap-analysis-1 python -m unittest discover -s tests/bootstrap -v` | PASS, 5/5 existing bootstrap tests in the running verified image. Candidate changes to runtime source, dependencies and active schemas are zero. |
| Document links, protected-path diff and whitespace | PASS. Active v0.3 OpenAPI/examples, service, official API/tools, bootstrap tests, Compose and B's dashboard are unchanged from integration `ee529ee`. |

RD16 checks that sample records are available, not that a human has reviewed them. This review did not repeat the author's private row inspection. The harness checks two prepared-table hashes; the full five-file result above comes from the separate official checker. The harness contains source-derived regression constants, so it was used locally rather than copied into public synthetic tests.

These results corroborate the offline experiment. They do not pass team D02 against A's future service, D03 source comparison, D05 full sensitivity, D06 claim justification, M01–M04 live chatbot, G01–G05 model grounding or UI/packaging completion. Historical observations do not establish CPU compatibility or operational savings.

## Required adaptations before implementation

1. **Measured baseline versus duration:** the prototype calculates `g*T`; its real-data example intentionally uses an exact-accounting job. The application must preserve recorded GPU-hours for allocation and scheduler hours for time; do not substitute one across the full dataset.
2. **Pricing boundary:** the prototype documents original host-cost inclusion but does not encode it as an input. The proposed API makes that assumption explicit and suppresses net value when it is false. CPU cost and GPU rate remain separate units.
3. **Mixed evidence:** a measured baseline is not a synthetic record just because intervention inputs are assumed. Use actual audit/evidence provenance, and label the pilot result `scenario_estimate`. Synthetic test inputs remain synthetic.
4. **Scope and claims:** the pilot is one-job accounting, separate from the broad cohort recovery range. Failure/full rerun and additional validation release no GPU allocation. Do not extrapolate the zero-memory subgroup into guaranteed recovery or claim the CPU cohort corrects the unrelated `rec_lowutil` recommendation.
5. **No implied runtime control:** the assumed trial cap validates scenario input. Stopping a workload, rollback and checkpoint support remain untested and outside this update.

No new model, dependency or service is needed for the proposed calculation. The synthetic fixtures use hand-worked inputs, not organizer-derived records. Keep official claim format unchanged and keep the quantified scenario available without C.

## Next owners

A/B review and adopt the versioned contract, then implement calculator and display respectively. C consumes the same immutable result when assigned. B's already-published v0.3 B0 UI is preserved; this change does not mark that UI integrated. The main branch contains the verified bootstrap plus this proposal, not a finished submission.
