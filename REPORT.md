# MANAI: evidence-led CPU-placement decisions

## Question and claim

Can a bounded CPU-placement pilot reduce GPU allocation for completed jobs with zero observed GPU compute, while preserving useful work? The product audits eligibility and hypothetical trade-offs. It does not demonstrate CPU compatibility, realized savings or a causal improvement. The upstream rule already suggests CPU placement; our contribution is traceable accounting and explicit downside.

## Method and final scenario

A selects completed source jobs with zero average and peak SM utilization and more than one recorded GPU-hour, counts each job once, excludes cancellation and synthetic findings, and retains the source evidence. Recorded allocation is not replaced with GPU count times scheduler duration. Memory partitions prioritize investigation; they do not narrow the eligibility rule or prove compatibility.

The default low/point/high recovery fractions are **0 / 0 / 1**. Without empirical CPU recoverability, a positive lower or central estimate is unjustified. The upper bound is the entire physical eligibility ceiling, not an expected outcome or statistically calibrated interval. Reference dollars use the official price book; they are not cash savings. The current snapshot and exact derived figures are available in the live audit and local claims export.

The optional one-job CPU scenario is separate from cohort recovery. A computes success, failed trial plus full GPU rerun, and extra-validation modes. CPU price, queue delay and original-host pricing boundary can be unknown. Signed net value and completion changes remain signed. These assumed trial outcomes never alter cohort eligibility or its claim export.

## Evidence, limitations and falsification

Five canonical files are checked against the supplied semantic checksums. Independent source recomputation, source-recommendation comparison and sensitivity checks are recorded in [integration results](eval/integration/RESULTS.md). The overview, evidence, immutable audits and claims use A. The Data explorer and Decisions table expose a verified read-only snapshot; decision rows describe overlapping exposure, not recoverable capacity. Their selected union deduplicates jobs. B's separate cohort planner is visibly hypothetical and is not an A audit or submission claim.

A controlled future pilot must compare output correctness, success rate, CPU runtime, queue delay, cost boundary and useful throughput against unchanged GPU placement. The proposal fails if workloads need GPU-specific code, correctness changes, or additional CPU/rerun/queue cost exceeds the benefit. Workload owners and Platform/SRE approve any real trial; this app executes none. Observational telemetry cannot establish future quarterly savings or diagnose hardware faults from failures alone.

## Chat and deployment

The required base chatbot uses actual official MCP calls, bounded templates and audit-scoped citations without a model key. The deterministic evidence summary is separately labeled. C's richer reviewer is optional and currently disabled because compatibility and model grounding remain incomplete. C failures must preserve base results and export.

`docker compose up` starts the base and automatically prepares the private browsing snapshot. See [README](README.md), [actual checks and remaining release gates](eval/integration/RESULTS.md), and [A/B handoff](docs/AB_INTEGRATION_HANDOFF.md). Generate local root claims with `python eval/integration/export_final.py`; the exported audit uses the same default fractions and price as the UI. Generated claims remain ignored pending the lead's resolution of the organizer's root-claims requirement and broad derived-data redistribution wording. This document does not assert final submission readiness.

## Four-minute demo

1. Explain the proposed pilot, owner and unmeasured risk on Overview; model the default scenario and distinguish its ceiling from a forecast.
2. Open evidence and follow an actual source record. Use Data explorer or Decisions to inspect the broader workload and overlapping exposure.
3. Model one successful CPU trial, then a failed trial or unknown CPU price; show that downside changes without changing cohort claims.
4. Ask the base chatbot a supported question, follow its citation, and export the displayed audit. State that CPU compatibility and operational savings still require a controlled pilot.
