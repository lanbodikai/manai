# Short thesis — v0.1

## Approved direction

A GPU budget recommendation is useful only if an operator can see which workloads support it, which assumptions turn those workloads into recoverable capacity, and what useful work could be harmed. We will build a complete decision dashboard that audits one proposed cut through that chain.

## Proposed product sentence

“Inspect a proposed GPU cut, verify its recoverable range against unique jobs, and decide whether a bounded pilot is worth its downside.”

## Problem → claim → experiment → falsification

- **Problem:** the supplied business recommendations can conceal overlaps and assumption-dependent recoverability. A CFO needs an actionable summary; an SRE needs a traceable calculation.
- **Claim to test:** our audited recommendation makes the calculation and assumptions reproducible, and its agent answers remain grounded in the cited evidence.
- **Experiment:** compare the organizer-provided recommendation with our recomputation for the selected cohort; hold the cohort and price constant when measuring effects of deduplication and assumptions. Run an adversarial grounding test set and a short operator task walkthrough.
- **Falsification:** totals cannot be independently reproduced, evidence links fail, scenario controls change unrelated quantities, or the agent invents facts. A lower estimate alone is not a success criterion.
- **Not established by this hackathon:** actual intervention savings, causal recovery, preserved research throughput or calibrated probability of operational success. Those require a pilot or additional ground truth.

## Complete product, bounded original analysis

Keep all three required views: spending, proposed action, downside. Include one full evidence drill-down and an MCP-backed explanation/challenge path. Use supplied overview/recommendation data with attribution; investigate only one cohort deeply. Surface uninvestigated recommendations as organizer judgments, without counting them in our verified headline.

## Provisional first cohort

Completed jobs with zero average AND maximum GPU compute activity, following the official rule and its scope, are candidates for a CPU-placement pilot. Completion and zero measured GPU use are observations; compatibility with a CPU-only environment is unverified. Eligible GPU-hours are an upper bound on recoverable allocation, not a proven cash saving. Round 2 will choose this or an idle-session cohort.

No numerical outcome, novelty claim or guaranteed 20% reduction is asserted. Show the target and supported gap honestly.
