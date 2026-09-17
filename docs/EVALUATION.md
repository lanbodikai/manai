# Tests and evaluation contract — proposed v0.1

These are explicit team acceptance gates, not organizer grading thresholds. Nothing has run yet. Test fixtures are original synthetic examples; real organizer data stay local. Freeze prompts/cases before tuning. Report denominator, failures and exclusions.

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

## Agent evaluation: required for A2

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
