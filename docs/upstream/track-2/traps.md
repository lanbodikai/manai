# Traps

Everything here is a real property of the data or a deliberate design choice. You're
being told before you start rather than losing an afternoon to it.

**One incident is synthetic.** The shared-volume incident — the
`pvc/scratch-lustre-02` volume, its `MOUNTS` edges, and the 121
`filesystem-latency-degraded` findings — is generated; the source telemetry has no
storage records. Every synthetic record carries `metadata.synthetic = true`.
Everything else is computed from the real job, utilization, power and scheduling
data, including every hardware finding.

**Not every failure is hardware.** Most failed jobs are user bugs. Out of 18,587
failures, **10 jobs** end in `NODE_FAIL` — but **31 hit a node failure at some
point**, and 6 of those went on to complete successfully after a requeue. Read
`hit_node_failure`, not `state_name`; filtering on the final state loses two thirds
of the signal.

**And the job's machine is usually not the one that died.** A requeued job is
running somewhere else by construction. Of the 25 node failures where the machine
is known exactly, 18 happened on a different machine from the one the job finished
on. `nodefail_nodes` records where each failure actually happened — see `docs/data.md`.

**Not all hardware failure is recorded.** The scheduler only knows about machines
that stop responding. One machine on this cluster broke for about a week without
ever being marked down, and nearly everything sent to it failed. There is a finding
for it. Finding it yourself, and working out why the obvious methods miss it, is a
good use of an afternoon.

`hardware_attributable_failures` in `claims.json` means **failed jobs genuinely
caused by faulty hardware** — your best estimate. There is more than one defensible
answer: counting only what the scheduler recorded is one, and counting a fault the
scheduler never noticed is another. **It is judged on
`hardware_attributable_rationale`, not auto-scored** — say what you counted and what
you left out. Attributing every failure to infrastructure is the one clearly wrong
answer: it overstates what fixing the hardware would recover.

**Not every bad-looking node is bad.** Some nodes have high raw failure counts
because one person ran a broken script on them repeatedly. Exposure varies wildly
— between **4 and 1,114 jobs per node**. Counts and rates rank differently.

**Cancelled is not failed.** Users cancel deliberately when a run looks wrong;
that's good practice, not waste. It's also **203,930 GPU-hours** — larger than
failed and timeout combined. How you treat it swings your headline number by
roughly 2×.

**Idle time is invisible where you'd look for it.** GPU telemetry is collected
per job — it starts when a job starts and stops when it ends. An unallocated,
idle GPU emits *nothing*. If you compute utilization from telemetry alone you
will silently drop all unallocated time and overstate the cluster badly. Idle
capacity has to come from gaps in the scheduling data.

**One exit code cannot separate user error from infrastructure fault.** Label
individual failures "unsuccessful" and split by state; do not label them
"infrastructure waste." A *pattern* of exit codes is different — several unrelated
people hitting the same crash on one machine and never elsewhere points at the
machine, and that is how the one silent hardware fault in this data shows itself.

**Users are hashed and stay that way.** These tiles identify *where recoverable
capacity is*, not who to blame. A dashboard that ranks employees by waste is a
hostile dashboard and will score lower than one that frames the same data as
capacity.

**Findings overlap, and `impact_gpu_hours` double-counts if you sum it.** Twenty-three
rules run over the same telemetry, so one job trips several — an idle interactive
session is usually also a job that never computed. **18% of the jobs that carry a
finding carry more than one**, and each of those findings describes a slice of the
same physical hours. `docs/rules.md` names the largest overlaps.

Worse, `impact_scope` mixes denominators. A `user`-scope finding covers one
person's entire four months and overlaps every `job`-scope finding underneath it.

```
naive sum of every finding's impact_gpu_hours   931,607 GPU-h   157% of the cluster
job-scope findings only                         537,711 GPU-h    91%
deduplicated to those jobs' real hours          311,373 GPU-h    52%
```

The cluster only ever allocated 594,004 GPU-hours, so the first number is
recovering time that never existed. **Check your total against that ceiling before
you put it on a dashboard.**

**Five rules carry no `impact_gpu_hours` at all**, on purpose.
`queue-starvation`, `queue-wait-p95-slo` and `queue-weekly-peak` are in
engineer-hours of waiting. `timelimit-overreservation` is capacity *blocked by a
reservation* rather than consumed. `node-elevated-failure-rate` reports a rate
against the cluster, not an amount. None of them belongs in a GPU-hour total.

**Thirty-seven findings describe the whole window, not a job.** They carry
`metadata.horizon == "full_window"` — 36 people failing week after week, and one
weekly pattern in the queue. No individual job in them would trip a per-job
threshold; the pattern only exists in aggregate. The queue one is worth reading
before you start:

> One weekday in seven takes 21,151 submissions against a median of 8,866 on
> other days, and the median wait rises to 2,007s from 2s. 16,981 hours of queue
> time accumulate on that one weekday.

**Row-weighted ≠ hour-weighted.** A third of the job records account for
0.012% of the compute. `df.sm_util.mean()` and the GPU-hour-weighted average
answer different questions, and only one of them is about money.

---

## Data quirks

- **Restarted jobs are one job with several attempts.** A job the scheduler restarted
  appears several times in the raw scheduler file under one `id_job`. The prepped
  tables keep the **last** attempt and record the history in `attempts` and the
  `nodefail_*` columns — see `docs/data.md`.
- **Memory requests carry a bit flag.** Raw `mem_req` values above 2⁶³ are Slurm's
  per-CPU flag OR'd with the real value. Subtract `9223372036854775808` to get MB per
  CPU — and do it in integer arithmetic, because a float cannot hold the low bits.
  `mem_req_mb` in the prepped data has this done.
- **Per-job energy doesn't integrate.** `energyconsumed_joules` does not sum correctly
  over long jobs. Use average watts × duration, which is what `energy_wh` is.
- **Timestamps are offsets.** The source data has no calendar. The price book's
  `epoch_offset` maps it to real dates, so everyone's quarters line up.
- **Job outcome codes.** `state` is numeric in the raw data: 3 COMPLETED, 4 CANCELLED,
  5 FAILED, 6 TIMEOUT, **7 NODE_FAIL** (not a kind of timeout — keep it separate),
  11 and 1024 are terminal with no documented meaning. `state_name` decodes it.

## What the publishers ask

The data is a **sample** of the workloads that ran on the cluster, and MIT says it is
*"not appropriate for use in estimating system utilization or any other characteristics
beyond those outlined in the HPCA'22 paper."* Every number here describes this sample
over its four-month window, not the cluster in general. That doesn't restrict what you
build — but if your dashboard quotes a cluster-wide figure, say so on it, because a
careful reader will ask.
