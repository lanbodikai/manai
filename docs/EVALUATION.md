# Tests and evaluation contract — proposed v0.3

These are explicit team acceptance gates, not organizer grading thresholds. Runtime tests have not run. C01 synthetic schema validation has passed; this does not establish analytical correctness. Test fixtures are original synthetic examples; real organizer data stay local. Freeze prompts/cases before tuning. Report denominator, failures and exclusions.

## Deterministic tests: required for A1

| ID | Input / condition | Pass condition |
|---|---|---|
| T01 | Synthetic eligible jobs J1=10 GPU-h, J2=20; duplicate finding cites J1 twice | Eligible total is 30, not 40; source findings remain traceable. |
| T02 | A user-scope finding overlaps those job-scope findings; a queue finding uses wait-hours | Neither is added into recoverable GPU-hours. Explicit exclusions shown. |
| T03 | Cancelled J3=40 GPU-h outside selected completed-job cohort | Default eligible total remains 30; any policy change changes selection only as documented. |
| T04 | Positive average but zero peak, missing utilization, negative duration, duplicate inconsistent job rows | Invalid/missing measurements rejected or excluded with reason; missing is not zero; no silent favorable inclusion. |
| T05 | H=30, recovery low=.2/point=.4/high=.6, price=$2.50/GPU-h | Recovery 6/12/18 GPU-h; reference dollars 15/30/45. Scenario label present. |
| T06 | Fractions outside [0,1], low>point, point>high, nonpositive price | Structured validation error; no response with misleading numbers. |
| T07 | Same audit used for UI and official claim export | Values agree before display rounding; export validates official schema; team included; uninvestigated claims absent. |
| T08 | Unknown evidence ID / synthetic source / mixed data fingerprint | Unknown fails clearly; synthetic propagates; incompatible fingerprints cannot silently join. |
| T09 | Same inputs and data fingerprint repeated | Deterministic audit values and evidence membership identical. |

## Real-data verification: required before final merge

| ID | Experiment | Completion condition |
|---|---|---|
| D01 | Official five-file canonical data check | All five match; record snapshot/version. |
| D02 | Independently recompute chosen cohort from local prepped tables, separate from service aggregation | IDs/counts exactly match; hours agree within 1e-6 relative tolerance or a documented tighter unit-based tolerance. Do not call the same aggregation helper twice and claim independence. |
| D03 | Source recommendation versus audited estimate on aligned cohort/price | Report both definitions and explain each difference. No forced improvement target; an unchanged estimate is valid. |
| D04 | Inspect five eligible records and three excluded/boundary records, or all if fewer | Every inclusion/exclusion follows documented rule; retain private review log, no raw records in Git. |
| D05 | Recovery and price sensitivity, at least three recovery settings and two prices | Monotonicity holds; physical eligible hours unchanged by price; recovery never exceeds eligible hours; no claim of realized savings. |

## Agent evaluation: required for C2

Fixed eight-case suite: (1) explain included cohort; (2) support headline hours; (3) explain overlap removal; (4) challenge recovery assumptions; (5) distinguish reference dollars from cash; (6) ask about the synthetic storage incident; (7) request unsupported individual blame or a causal claim absent evidence; (8) unavailable tool/unknown evidence. Use synthetic context first; repeat relevant cases against the actual local audited result.

G01: Every numeric factual assertion matches the canonical tool result at declared rounding. G02: Every asserted source reference resolves. G03: No synthetic record is presented as measured real telemetry. G04: Missing evidence produces explicit uncertainty, not invented support. G05: Tool failure has a visible non-success state and does not mutate claims. Zero critical violations across the eight cases; if any fail, fix and rerun affected cases plus the full set before merge. Record all attempts, not just successful generations.

Run three repetitions for the numeric, unsupported-claim and tool-failure cases to expose stochastic failures. Log calls, input/output tokens, provider/model, latency and cost if observable. Proposed initial budget: at most 6 tool calls and 30 seconds per answer; make configurable and revise only with an explicit recorded reason. This is a team target, not an event rule. Compare a deterministic evidence summary to the agent on the same question set for added usefulness and factual regressions; no broad model sweep is needed.

## Product/packaging tests: required for B1/B2

- U01: overview → chosen recommendation → evidence opens using one synthetic fixture, then real data. Source IDs and caveats persist.
- U02: changing a scenario changes headline, downside assumptions and export consistently; a late old response cannot overwrite the new state.
- U03: empty cohort, missing source and unavailable agent are distinguishable. No mock data in real-data mode without an explicit visible label.
- U04: controls and evidence navigation work by keyboard; tested at desktop and a narrow viewport; no clipped mandatory content.
- U05: a teammate has 30 seconds to identify the proposed action, owner role, savings range and main risk; then finds a supporting record. Record tasks succeeded and failed. If no independent tester is available, mark self-review and do not claim user validation.
- P01: clean checkout plus organizer-generated data starts with one `docker compose up`; dashboard responds on :3000 without manual app launch; dependencies/health errors are visible.
- P02: official validator checks claims and live URL; team tests add semantics the official validator lacks. Record warnings and disposition, especially known confidence warning.
- P03: public candidate contains no keys, raw/prepped/generated datasets or notebook data outputs; required notices, AI disclosure and run instructions exist. No claim of data-license clearance from a filename scan alone.

## What needs an eval versus a test

Arithmetic/join/contracts need deterministic tests. Analytical credibility needs independent recomputation and source comparison. Agent explanations need repeated grounding evaluation. Decision usability needs a timed human task. Actual recoverability and harm reduction need a future controlled pilot: validate CPU compatibility or timeout safety, measure task success/throughput/queue impact, and compare against unchanged placement. Until then label ranges as scenarios; do not report empirical calibration or causal savings.

Record results in `eval/RESULTS.md` with test ID, source/fixture version, configuration, pass/fail, artifacts and limitations. Baseline status is NOT RUN. A failed material check cannot be converted to a pass by narrowing the report after seeing it; record the scope change explicitly.

## API-specific conditions

C01–C06 are specified in [API_SPEC.md](API_SPEC.md). A owns analysis API shape/identity tests; C owns explanation error/grounding tests; B owns proxy routing, superseded-response and displayed-audit/export consistency tests. Schema/example validation can pass before runtime implementation; it does not satisfy the integration conditions.

## Optional-service resilience — required for base release

- R01: default clean Compose startup with C profile disabled and no LLM key; overview, scenario, downside, deterministic summary, real MCP chatbot, evidence and claims all work. No C build or install occurs.
- R02: C process unavailable/crashed; same base flow succeeds and explanation panel shows unavailable state.
- R03: C request hangs; bounded frontend timeout occurs, UI remains interactive and claims export still works.
- R04: C returns malformed JSON or another audit's ID; response rejected without overwriting canonical audit or misleading citations.
- R05: optional C profile fails to build/start; base default command still independently starts and passes P01. Use B-owned failure stubs if C is absent. B documents recovery by returning to the default profile; do not require fixing C to judge the base.

B owns these tests; C assists with failure injection if available. Final readiness has two statuses: base ready (T/D/U/P/R/M and applicable API gates) and agent enhancement ready (C1/C2/G gates). An absent enhancement is disclosed; it is never reported as successful MCP evaluation.

## Required minimal MCP chatbot — A/B, independent of C

- M01: with C disabled and no provider key, the UI question produces a successful actual official MCP call and a cited answer tied to the displayed audit; retain tool trace. Direct HTTP alone is insufficient.
- M02: four supported question classes (source support, eligibility, assumptions, downside) preserve canonical numbers, valid citations and fact/judgment/simulated labels; unsupported causal or CPU-compatibility certainty is declined. Compare each answer to source records.
- M03: missing tool, malformed output, stale fingerprint and wrong-audit evidence yield clear non-success/insufficient-evidence states without fabricated citations or changed claims; enforce 3-call/10-second budget.
- M04: C crash, hang and malformed answers leave the base chatbot usable. MCP runtime failure is separately visible and makes the chatbot requirement NOT READY, even if dashboard works. Run with B-owned stubs if C is unfinished.

These are required for slide-aligned base completion. A owns MCP/client correctness; B owns UI, container and resilience proof. C's more extensive G evaluation remains optional only because the required narrower chatbot is already included.

## D06 — final claim basis (required for A2/final base)

For each final low/point/high recovery estimate, document the eligibility ceiling, conversion assumptions and their evidence or judgment basis. A reviewer must trace each value to the stated calculation. Include a zero-recovery sensitivity case and explicitly justify any positive lower bound; if not defensible, revise it. UI defaults and synthetic fixture fractions are not evidence. Verify claims, report and final displayed audit agree. Scenario bounds must not be labeled statistically calibrated. Status: NOT RUN.

## Proposed v0.4 CPU-pilot checks

[Proposal validator and fixtures](../contracts/proposals/v0.4/README.md) extend C01 coverage only. A/B adoption adds success/failure/extra-validation, negative value, unknown price/queue, observed-allocation-versus-duration, pricing-boundary and immutable-identity cases to existing T05/T06/T07, C04/C06, U02/U03 and M02/M03. C uses them for G01–G05 when assigned. Schema/fixture passes and the offline verifier are not service/UI/MCP or operational acceptance. See [actual review results](VERIFIER_HANDOFF_REVIEW.md).


## Pilot & Recovery feature — PR01–PR10

This deterministic A+B simulation is separate from C's model grounding eval. See `eval/pilot_recovery/RESULTS.md` for actual outcomes; the conditions below do not imply a pass. Original synthetic fixtures are mandatory for committed test records.

| ID | Condition | Required observation |
| --- | --- | --- |
| PR01 | Successful CPU replacement | Original minus trial/setup cost; signed net benefit and signed runtime change. No achieved-savings language. |
| PR02 | Failed trial, full GPU rerun | Original GPU cost counted once in total; loss equals extra trial/setup cost; failed detail retained. |
| PR03 | Recovery unavailable | Paused — owner action required; known spend separately visible; final benefit/cost/delay unknown. |
| PR04 | Runtime/spending cap, exact boundary, setup above cap | Simulator truncates or prevents startup and records the limit trigger; unknown price never passes spending verification. No real enforcement claimed. |
| PR05 | Missing observations, null price/queue/setup, invalid numbers | Unknown differs from zero; NaN/infinity and malformed requests fail clearly; no fabricated baseline. |
| PR06 | Missing/unverified checkpoint | Full rerun only; client assertion cannot grant verified checkpoint recovery. |
| PR07 | Revise/retry, late or mismatched response | Prior snapshots/failure detail retained, pending draft labelled, wrong identity rejected, export matches saved result. |
| PR08 | Foreign evidence, changed source, same audit claims | Audit/evidence/source membership enforced; simulation does not mutate canonical audit or claims. |
| PR09 | A response through B adapter/panel; C unavailable | Display canonical costs/statuses without frontend money recomputation; C is not invoked. Distinguish mocked UI tests from live integration. |
| PR10 | Build/start, desktop/narrow keyboard flow | Live bundle excludes synthetic fixtures; default startup serves B; separately record Docker and human usability checks. |

A future empirical recovery evaluation must use actual workload code/inputs, expected outputs, a tested stop mechanism, full-rerun/checkpoint restoration and failure injection. None of PR01–PR10 establishes operational recovery or actual cash savings.
