# Production and human usability review

Self-review, 17 September 2026. This is a proposed next iteration, not implemented scope or independent user validation. The B0 app is a synthetic interaction prototype; it is not production-ready. B0 implementation remains unchanged by this review.

## Evidence reviewed

Inspected the actual B0 desktop/mobile screenshots and source; the supplied Track 2 notebook, official data/traps/rules/API guides, API calculation code, and local raw CSV column headers in the existing workspace. The local starter identifies upstream commit `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`. No raw records were copied into this branch, no dataset was regenerated, and no reported dataset aggregates below were independently recomputed.

Sources: [official data guide](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/data.md), [traps](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/traps.md), [rules](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/rules.md), [starter](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/starter/notebook.ipynb).

## The main product gap

The app explains a modeled number, but does not yet support a decision from assumption selection through a controlled pilot. A CFO should leave with a proposed action, accountable owner, plausible capacity range, cash-savings status, and conditions for stopping. More unrelated charts would not fix this.

### 1. Separate completion, GPU activity and cash

The supplied API computes activity as `sum(gpu_hours * sm_util_avg / 100)` and completed activity from that same expression restricted to successful jobs. Its approximately 83% headline compares completed activity with the recorded GPU-hour baseline. Our outcome chart groups hours by terminal state; it cannot explain that headline by itself. Activity is a telemetry-based proxy, not a direct measurement of useful research output.

Propose a labeled progression: GPU time recorded → estimated active GPU time → active time in completed jobs, alongside the separate outcome breakdown. Do not sum its nested stages. Show cancelled jobs separately and avoid treating all non-completion as recoverable waste. The sample cannot establish whole-fleet idle capacity: per-job telemetry omits unallocated GPUs. Scope any scheduler-gap analysis to the sample and its coverage limits.

Display the source window, sample scope, source version, price version, and a visible distinction between reference dollar value and actual bill savings. Real dollars require billing/contract evidence that this dataset does not supply. A owns canonical additional figures; v0.3 currently lacks the activity progression and baseline/target/gap fields.

### 2. Make the downside useful without inventing a dollar loss

“Research could run more slowly” and “Not measured” are honest but do not tell someone how to proceed. Put the audit's rollback rule, workload-owner involvement and pilot success measures close to the recommendation. A richer pilot plan needs proposed cohort, maximum exposure, runtime/completion/queue measures, owner, review date, and explicit stop conditions. Label all thresholds as proposed until agreed. Historical job duration and queue wait can describe the baseline, not predict CPU-only runtime.

CPU cost, rerun cost and research-delay value are absent. Show those missing inputs rather than implying gross reference GPU savings equal net cash benefit. A future scenario may accept clearly labeled finance assumptions; it must not manufacture measured harm.

### 3. Explain why this candidate comes first

The official guide reports 463 `gpu-not-needed` findings: completed jobs, both average and maximum GPU activity zero, and more than one GPU-hour. That supports investigating CPU placement. It does not verify CPU-only compatibility or give a defensible recovery percentage. The app currently shows one candidate without comparing it with alternatives; “first” is an editorial choice, not a verified ranking.

Add “Why start here?” explaining the inclusion rule, evidence quality and reversibility, and “What we have not investigated.” Later, independently audit candidates such as idle-session timeouts or GPU imbalance. The guide reports 689 imbalance findings that require per-card `gpus.parquet`; job averages conceal them. Do not imply those counts are savings. Do not add candidates just to fill the 20% target: findings overlap, and queue wait and reservation tails have different units.

### 4. Make assumptions understandable before making them adjustable

Three percentage fields ask a new user to supply expertise they do not have. Rename the section to “How much of this GPU time could a pilot avoid?” Explain the fraction's denominator with a concrete example. Offer a zero-recovery stress test; put low/central/high and price override in an expanded editor. Any named preset must show its rationale and source, not merely arbitrary “conservative” or “safe” numbers. Do not call the low bound guaranteed or the range a confidence interval.

Keep original-versus-proposed results side by side. Give the result a readable scenario name, preserve dirty inputs and offer Reset. Current immutable audit identity and stale-response protection provide a good foundation; session persistence and stable share links do not exist yet.

### 5. Explain the evidence before exposing its schema

The drawer currently moves quickly into `sm_util_avg`, source columns and join keys. Start with: “This job finished. No GPU compute was recorded. It held this many GPU-hours. CPU-only execution remains untested.” Show inclusion/exclusion criteria, measurement completeness, overlap removal, and recorded-versus-estimated labels. Keep raw IDs, joins, fingerprints and rule thresholds in Technical details. Add search, sorting and backward pagination when A provides real evidence volumes; current fixtures contain just two records.

Historical findings also need a clear status. The guide says 73% are resolved; historical cost is not automatically a task someone can act on today. Distinguish “evidence from the sample” from “current actionable issue.” Keep the synthetic storage incident explicitly marked if ever surfaced. Do not rank researchers by waste or infer a hardware fault from one failed job. Node-failure history and actual failed-node attribution matter because requeues change placement.

## Interactions that feel technical rather than human

| Current element | Friction | Proposed change |
| --- | --- | --- |
| MCP evidence chatbot / Template-based / API v0.3 | Exposes implementation before explaining value | “Ask about this recommendation”; technical mode in details |
| GPU-hours | Familiar to engineers, unclear to a CFO | Explain once: one GPU reserved/recorded for one hour; retain the precise dataset definition in details |
| Low / point / high recovery | Unexplained expertise requirement | Plain-language outcome range with explicit assumptions |
| `demo-audit-1` beside the result | Identifier is more prominent than decision state | “Scenario 1 · calculated from these assumptions”; ID in details |
| Dollar figure as main evidence entry | Clickability may not be obvious | Keep linked dollars and add a visible “See how we calculated this” action |
| Technical 422/409/error code text | Tells users what failed internally | Field-level explanation and specific recovery action; codes in expandable details |
| Two chat panels | User must understand our architecture | One main question panel; clearly optional “Challenge this recommendation” disclosure |
| Team field and JSON export | Submission mechanics interrupt decision-making | Put technical claims in an export menu; later add a shareable decision brief |
| Tiny muted labels, icon-only narrow navigation | Harder scanning and discoverability | Larger key caveats, stronger contrast, text labels on mobile; retain accessible names |
| Long page of equally weighted information | No obvious next action | Three-card summary, then a clear “Review pilot plan” path; details progressively revealed |

## Suggested delivery order

1. Complete B0 packaging and preserve its honest synthetic boundary.
2. B1: connect verified A data/MCP and same-audit export; negotiate missing baseline/activity/target fields. Keep missing values explicitly unavailable.
3. Simplify terminology, scenario editing and evidence summaries; expose canonical pilot safeguards. These UI changes can stay in B-owned paths.
4. Add a decision brief and audit comparison only after the necessary contract and persistence support is agreed.
5. Run an independent 30-second task: identify action, owner, range, risk, then locate one supporting record. Record failures rather than claim intuitive usability from self-review.

For deployment beyond this local judging app, separately address access control, saved-audit persistence/retention, secure transport and configuration, monitoring, recovery and larger-data performance. Those requirements depend on the deployment context and are not reasons to add a login flow to B0.
