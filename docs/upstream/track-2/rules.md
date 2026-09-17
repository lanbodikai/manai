# Rule catalogue

Every rule MantisGrid AI has armed against this estate, what it fires on, and what it
does **not** claim. `GET /v1/policies/rules` returns the same list at runtime with
live counts.

A rule is one measurement against one threshold, held for a duration. It reports a
**symptom**. Working out the **cause** is your job — that is the whole exercise, and
several rules say so explicitly in their own text.

**A finding means something is wrong.** A rule that ran and found nothing is still
armed; it reports `status: CLEAR` with a count of zero. Read those too — see
§ *The quiet one* at the end.

---

## How to read an entry

```
rule_id       what you match on in finding.detectorId
scope         the kind of thing a finding attaches to
condition     the actual threshold, as implemented
window        the period the condition is evaluated over
impact_kind   lost | consumed | degraded | unused_capacity | (none)
```

`impact_kind` tells you what the GPU-hours in `metadata.impact_gpu_hours` represent:

| kind | means |
|---|---|
| `lost` | work was destroyed — the hours bought nothing |
| `consumed` | hours were spent, on something of low value |
| `degraded` | work continued, but slower or at risk |
| `unused_capacity` | hours were allocated and not computed on |
| *(none)* | the finding carries no GPU-hour claim |

**Do not sum `impact_gpu_hours` across kinds.** Hours that were never used and hours
that were destroyed are not the same quantity, and adding them produces a number
that means nothing. Several rules also overlap on the same job by design — see
§ *Overlap* below.

---

## Availability

### `rules::node-failure`
```
scope       job
condition   the scheduler killed the job with NODE_FAIL, on ANY attempt --
            including jobs that were then restarted and ended some other way
resource    the machine(s) the FAILED attempt was running on, not the job's
            final machine
impact      lost -- the failed attempt's hours, not the whole job's
```
The scheduler itself said a machine died under this job. This is the only
*scheduler-recorded* hardware evidence in the dataset and there is very little of
it — which is the point. A team that reports a small number of hardware-caused
failures is reading this correctly.

Two things about it are easy to get wrong:

- **The job's final machine is usually not the one that died.** A restarted job is
  running somewhere else by construction. The finding names the machine from the
  failed attempt; `metadata.final_node` is where the job ended up.
- **Sometimes nobody knows which machine died.** When the failed attempt spanned
  several machines, the finding says so, lists all of them, and sets
  `metadata.failed_node_known: false`. Blaming all of them blames the innocent ones.

### `rules::node-elevated-failure-rate`
```
scope       node
condition   one-sided binomial test of the node's failure count against the
            CLUSTER failure rate in the SAME window, p < 0.01
            minimum 30 jobs on the node in that window
window      consecutive 14-day windows, not overlapping; the last is cut short where
            the data ends (windows with fewer than 100 jobs estate-wide are skipped)
impact      degraded -- a rate against the cluster, with no GPU-hour figure
```
**Symptom only.** The finding deliberately withholds owner concentration, hardware
flags and any `probable_cause`. Elevated failures can be the machine, the code being
run on it, or the kind of work it receives — and those have different remedies.
Everything you need to tell them apart is in the shipped parquet.

The window is evaluated **against itself**, never against the whole 18-week period.
A detector running in week 4 cannot know the week-18 median.

### `rules::node-job-failure-burst`
```
scope       node
condition   more than 80% of the jobs finishing on the machine failed,
            over a 48-hour window (evaluated every 6 hours, >= 20 jobs)
window      48 hours; firings within a window of each other merge into one episode
impact      lost
rootCauses  the machine, a person's namespace, or none -- see below
```
The acute counterpart of `node-elevated-failure-rate`. That rule compares a machine
with the cluster over a fortnight and deliberately says nothing about cause. This
one fires on a machine failing almost everything it runs, then **runs causal
analysis** and records the verdict in `metadata.attribution`:

| verdict | the test | `rootCauses` |
|---|---|---|
| `hardware` | several people crash here with an exit status they essentially never produce on any other machine | the machine — and a separate `node-hardware-fault` finding |
| `user` | one person owns ≥90% of the failures, **and** everyone else on the same machine in the same hours succeeded far more often | that person's `k8s:namespace` |
| `user` | one person owns ≥90% and had the machine to themselves, **and** the same array's identical tasks failed on other machines too | that person's `k8s:namespace` |
| `undetermined` | none of the above | none; the finding says which test could not decide |

Each test compares **like with like**, and that is the whole difficulty. "Whoever owns
most of the failures" is not a test — on this cluster it blames a person for the one
machine that genuinely broke. "Does that person fail on other machines?" is not
either, because the scheduler tends to put someone's batch of identical jobs on the
same machine, so their jobs "here" and "elsewhere" are different work.

**`undetermined` is the most common verdict, and it is correct.** A burst where two
people both fail on one machine, or where one person had the machine to themselves
and ran nothing comparable anywhere else, genuinely cannot be separated from this
data. `metadata.attribution_evidence` shows the numbers the analysis stopped at.

### `rules::node-hardware-fault`
```
scope       node
condition   a node-job-failure-burst episode whose causal analysis attributed
            it to the machine
impact      lost
rootCauses  the machine
```
The hardware verdict as its own finding, because it calls for a different response —
take the machine out of service — from anything a person can fix. The scheduler
never marks these machines down; they keep receiving work for the whole episode.
`metadata.evidence` lists, for each person, their crashes with the signature on this
machine against their count on every other machine.

### `rules::array-mass-failure`
```
scope       array (k8s:job)
condition   >= 10 tasks AND > 90% of them FAILED
window      per array
impact      lost
```
A Slurm **array** is one submission that launches many copies of the same script,
each with a different input. In the resource graph each array is a `k8s:job` that
`OWNS` its task pods, the way a Kubernetes Job owns its pods.

The GPU-hours counted as lost exclude tasks that COMPLETED — they produced their result.
`metadata.gpu_hours` is the whole array; `metadata.gpu_hours_lost` is what the impact
counts. CANCELLED tasks stay in: nothing in the data says whether their work survived.

### `rules::array-task-failure`
```
scope       job
condition   the task FAILED, and it belongs to an array that
            array-mass-failure fired on
impact      lost
rootCauses  the array
```
One finding per failed task. Each looks, on its own, like its own problem on its own
machine. They are not: `rootCauses` names the array, and `POST /v1/causal` on any
one of them resolves the whole cluster to it.

**The machines are innocent.** In the causal response, each node's score is its share
of the array's failures — low, and spread across many machines. If a node were at
fault the failures would concentrate on it. They share an exit code instead.

This is the real counterpart of `filesystem-latency-degraded`: many symptoms, one
cause, and the right response is one fix, not one per symptom. **Count the
problems, not the findings.**

Every array on the cluster exists as a `k8s:job` resource, not only the ones that
failed — so the resource's existence tells you nothing on its own.

### `rules::wallclock-kill`
```
scope       job
condition   Slurm terminal state == TIMEOUT
window      per job
impact      lost
```
Work destroyed at the wall clock, not merely wasted — the difference matters when
you cost it.

### `rules::user-repeat-failure`
```
scope       user
condition   > 50 failed jobs across >= 8 distinct weeks
window      full period
impact      consumed
```

### `rules::filesystem-latency-degraded`
```
scope       node
condition   nodes mounting a shared volume during a latency excursion
window      one 48-hour episode
impact      degraded
```
**This is the one synthetic scenario in the corpus.** Every record carries
`metadata.synthetic = true`. Everything else is computed from real telemetry.

---

## Performance

### `rules::gpu-never-computed`
```
scope       job
condition   sm_util_avg == 0 AND sm_util_max == 0 AND gpu_hours > 10
            AND state != COMPLETED
impact      consumed
```
Both the mean and the peak must be zero. A job whose peak reached 35% *did* compute,
briefly, so "never ran a kernel" would be false of it.

This rule and `gpu-not-needed` **partition** the jobs that never ran a kernel, by
outcome, because the remedy differs. A job that crashed or was killed without
touching the GPU needs its failure fixed; one that succeeded without touching it
should not have asked for a GPU. Neither rule contains the other's jobs.

### `rules::gpu-not-needed`
```
scope       job
condition   state == COMPLETED
            AND sm_util_avg == 0 AND sm_util_max == 0
            AND gpu_hours > 1
impact      unused_capacity
```
The job **succeeded** with the GPU at zero for its whole life, peak included. It did
its work on the CPU. There is no "it crashed before it got going" reading available
here — it finished. The remedy is placement: this work belongs on a CPU node.

### `rules::idle-interactive-session`
```
scope       job
condition   job_type == LLSUB:INTERACTIVE
            AND open > 4 hours
            AND sm_util_avg < 5%
impact      unused_capacity
```
An interactive session is a person at a keyboard. This long at this level of
activity is a session nobody was using. The remedy is a **policy** — an idle
timeout on interactive allocations — rather than anything about the workload, which
is why this is its own rule despite heavy overlap with `gpu-never-computed`: the
other rules say hours were wasted, this one names the policy that would have
stopped it.

### `rules::gpu-low-utilization`
```
scope       job
condition   sm_util_avg < 10% AND gpu_hours > 250
impact      consumed
```
The GPU-hour floor is doing most of the filtering here, deliberately: it weights
toward jobs that cost real money. Relaxing it to 50 would find roughly eight times
as many jobs.

### `rules::gpu-memory-oversized`
```
scope       job
condition   0 < mem_used_frac < 0.15 AND gpu_hours > 250
impact      consumed
```
Strictly greater than zero: a job that allocated literally no GPU memory across
hundreds of GPU-hours is `gpu-never-computed`, not an oversized request.

### `rules::gpu-imbalance`
```
scope       job
condition   >= 2 cards AND busiest card >= 20% SM
            AND (busiest - quietest) > 30 SM points
            AND walltime > 1 hour
impact      unused_capacity
```
**This one is invisible in `jobs.parquet`.** `sm_util_avg` there is *exactly* the
mean across the job's cards, so a job with one card at 0% and one at 65% reads as an
ordinary 35%-utilised job — healthier than the two-card median. You need
`gpus.parquet` pivoted per `gpu_id` to see it at all.

### `rules::multi-node-low-utilization`
```
scope       job
condition   spans >= 4 nodes AND sm_util_avg < 20% AND gpu_hours > 50
impact      unused_capacity (gpu_hours x the idle fraction)
```
At this width every idle card is multiplied by the node count, and the job holds a
contiguous block that single-node work cannot backfill. Low utilization on a wide
job can mean it was **blocked on communication between nodes** or that it was
**broken**; the finding reports the utilization and does not say which.

### `rules::gpu-pcie-saturated`
```
scope       job
condition   (pcie_rx_avg + pcie_tx_avg) > 80% of 15,754 MB/s
            AND sm_util_avg < 20%
impact      degraded
```
See § *The quiet one*.

---

## Cost

### `rules::node-under-utilization-slo`
```
scope       node
condition   GPU-hour-weighted mean SM utilization < 20%
            for 3 consecutive weeks
            (node must deliver > 50 GPU-hours in a week to be judged)
window      weekly, runs of >= 3
impact      unused_capacity
```
An SLO breach, not a statistical outlier. 20% is a business decision about what
utilization is worth paying for. Hours are counted **on this node only** — a job
spanning several nodes contributes just the cards it held here.

### `rules::unsuccessful-gpu-spend`
```
scope       user
condition   > 1,000 GPU-hours on jobs that did not COMPLETE
window      full period
impact      consumed
```
Whether CANCELLED counts as waste is **your call to defend** — a cancellation can be
a user correctly killing a bad run. It swings the headline roughly 2x.

### `rules::timelimit-overreservation`
```
scope       user
condition   jobs using < 5% of a time limit between 4 hours and 15 days,
            and the user must have >= 20 such jobs
window      full period
impact      (none) — reports a ratio, not hours
```
**This rule deliberately carries no GPU-hour claim.** Reservation tails overlap in
time and Slurm backfill reclaims them, so summing them into a capacity number
produces a figure larger than the cluster physically has. Ratios and job counts are
true; the sum is not.

### `rules::queue-starvation`
```
scope       user
condition   > 250 accumulated hours of queue wait, counting only jobs that
            waited more than 6 hours
window      full period
impact      (none) — engineer-hours, not GPU-hours
```

### `rules::queue-wait-p95-slo`
```
scope       cluster (reported per partition)
condition   95th-percentile queue wait > 4 hours in a week
            (partition needs >= 100 jobs that week to have a p95 worth quoting)
window      weekly, per partition
impact      (none) — engineer-hours, not GPU-hours
```
A latency SLO on the queue, distinct from `queue-starvation`, which totals wait per
user over the whole period and so cannot tell you whether the queue got worse *this
week*. The finding names the median alongside the p95 deliberately: these fire with
medians near zero, so they are **tail** problems, not uniformly slow queues.

Reports the delay only. A slow tail can be contention, one user's burst of large
requests, or a fairshare limit, and the finding does not say which. The engineer-hours in
the impact line count only the time past the 4-hour target, not each job's whole wait.

### `rules::slow-cancel-of-idle-job`
```
scope       job
condition   state == CANCELLED
            AND sm_util_avg < 5%
            AND ran for > 4 hours before being cancelled
impact      unused_capacity
```
**This rule measures time, not utilization.** The cancellation tells you the owner
eventually decided the job was not worth running; `metadata.hours_before_cancel` is
how long the cards were held before anyone looked.

Read it against the base rate, which is in your data too: the median cancelled job
showing this little activity is killed **within minutes**, while a cancelled job
that *was* computing runs for hours first. People generally do notice. This rule is
the tail, and it is a large tail.

It does **not** distinguish a job that hung from one whose owner walked away, and
the remedy differs — the first wants a liveness check, the second a notification.
Deciding which you are looking at, and how you could tell, is the interesting part.

### `rules::queue-weekly-peak`
```
scope       cluster
condition   the weekday with the highest median queue wait
window      full period, one finding
impact      (none)
```

---

## The quiet one

`rules::gpu-pcie-saturated` is armed and has **never fired**.

It watches for the PCIe bus running above 80% of link capacity while the GPU sits
idle — a GPU genuinely blocked on data movement. The V100 link is PCIe gen3 x16,
15,754 MB/s. Peak observed on this estate is **4,240 MB/s: 27% of capacity**, a
factor of three from saturation.

That is a real result and it is worth acting on: **data movement is not what is
holding these GPUs back.** If your analysis concludes "fix the data pipeline", this
rule is the evidence against you.

A related inference does *not* work, and it is worth knowing why before you build on
it. "Low utilization plus high PCIe means the GPU was waiting on input" sounds
reasonable and is backwards — a GPU waiting on slow storage is not moving bytes,
because none have arrived. A rule built on that reasoning shipped here until
September 2026; it flagged 799 jobs, of which 553 had `sm_util_avg` of **exactly
zero**. They were not waiting for data. They never asked for any.

The PCIe columns are also rough: a quarter of card-rows have identical min, avg and
max, and `pcierxbandwidth_megabytes_max` is pinned at 2147 in 8.8% of rows — 2147 is
`INT32_MAX` expressed in bytes, so those readings are censored.

---

## Overlap

Rules are **not** mutually exclusive, and this is intentional — a real catalogue has
the same property. The same job can appear under several rules, each true.

The clearest case: a job that allocated GPUs and never ran a kernel is
`gpu-never-computed`; if it also ran over 250 GPU-hours it is `gpu-low-utilization`
too. Both statements are correct. **Counting it twice in a savings estimate is not.**

Overlaps worth knowing by name, measured on the shipped corpus:

- **528 of the 906 `idle-interactive-session` findings are also
  `gpu-never-computed`**, 109 are `gpu-not-needed`, and 268 are `wallclock-kill` —
  a session left open until the scheduler ended it.
- `multi-node-low-utilization` shares 24 of its 63 jobs with `gpu-low-utilization`
  and 21 with `slow-cancel-of-idle-job`.
- `gpu-not-needed` and `gpu-never-computed` share **none**, by construction.

And the largest single overlap, since it is easy to trip over:
**311 of the 949 `slow-cancel-of-idle-job` findings are also
`gpu-never-computed`.** The two make different claims about the same job — one that
it did no work, one that nobody noticed for hours — and their `impact_gpu_hours`
describe the same wasted hours. Add both totals together and you have counted those
311 jobs twice.

Deduplicating before you total is part of the work, and saying how you did it is
worth more than the total itself.
