# The data

What is in each file, where it came from, and which columns lie to you.

Generated against the real files. Numbers here are measured, not quoted.

---

## Where it comes from

```
data/raw/          88 MB   two CSVs, exactly as MIT published them   you download
data/prepped/      15 MB   the same data, deduped/decoded/joined     scripts/prep_data.py
data/synthetic/    37 MB   MantisGrid's resource model on top        the generator
```

None of it is in the repository. The licence forbids redistributing anything derived
from the source data, so you download the CSVs and generate the other two on your own
machine — `data/README.md` has the steps.

**Real:** every job, every user, every placement, every utilization and power
reading, every outcome. MIT SuperCloud TX-GAIA, HPCA'22 release, used under
[CC BY-NC-ND 4.0](http://creativecommons.org/licenses/by-nc-nd/4.0/) — see the
`../ATTRIBUTION.md`. The publishers note it is a **sample** and is
*"not appropriate for use in estimating system utilization"*; figures here describe
the sample over its window, not the cluster.

**Synthetic:** the PVC, `MOUNTS` edges, and the shared-dependency incident — 121
findings out of 11,979. Everything else is computed from the real telemetry. Every
synthetic record carries `metadata.synthetic = true`.

**Parquet** is a columnar file format. Reading one column does not touch the other
64, which is why the prepped files load instantly. The format and the cleanup are
ours; the content is MIT's.

---

## The cluster, in numbers

| | Measured |
|---|---|
| GPU jobs | 74,849 |
| GPU-hours allocated | 594,004 |
| Nodes | 225 (2x NVIDIA V100 each) |
| Users who ran GPU jobs | **195** |
| Users on the cluster overall | 288 (includes CPU-only work; not in `jobs.parquet`) |
| Exposure spread | 40 to 1,114 jobs per node |
| Window | ~4 months |

---

## `data/prepped/jobs.parquet` — 74,849 rows x 65 columns

One row per job. This is the table you will spend most of your time in.

### Identity and ownership

| Column | Type | Notes |
|---|---|---|
| `id_job` | int64 | primary key, 74,849 distinct |
| `id_user` | float64 | 195 distinct, hashed |
| `id_array_job`, `id_array_task` | float64 | Slurm array membership. **Null for jobs that are not part of an array** — see below |
| `is_array_task` | bool | 39,694 jobs belong to one of 2,129 arrays; 35,155 do not |
| `partition` | str | `gaia`, `normal`, one other |
| `job_type` | str | 4 values |
| `constraints` | str | 3 values, all `xeon-g6`-ish |

### Outcome — read the state notes below before using these

| Column | Type | Notes |
|---|---|---|
| `state` | float64 | numeric Slurm code, 7 distinct |
| `state_name` | str | decoded: COMPLETED, CANCELLED, TIMEOUT, FAILED, NODE_FAIL, UNDECODED_11, UNDECODED_1024 |
| `is_success` | bool | `state_name == COMPLETED` |
| `is_terminal` | bool | **dead column — always True** |
| `exit_code`, `derived_ec` | float64 | Slurm packs these as `(status << 8) \| signal`, so `exit_code // 256` is the exit status — 135 is SIGBUS, 137 SIGKILL. **One exit code cannot tell you whether a job failed because of its code or its machine.** A pattern can: several people hitting a status on one machine that they never hit elsewhere |
| `kill_requid` | float64 | who issued the kill, 153 distinct |
| `attempts`, `nodefail_attempts`, `hit_node_failure` | int, int, bool | requeue history — see *Node failures do not stay put* |
| `nodefail_nodes`, `nodefail_exact`, `nodefail_last_end`, `nodefail_wall_sec` | list, bool, float, float | **where** each node failure happened, which is usually not where the job ended — same section |

### Placement

| Column | Type | Notes |
|---|---|---|
| `primary_node` | str | 225 distinct. **The FIRST node only** — see the warning below |
| `nodelist` | str | the raw Slurm list, stored as a stringified list |
| `n_nodes_listed`, `nodes_alloc` | float64 | job width in nodes |

### Time — all offsets, not calendar dates

| Column | Type | Notes |
|---|---|---|
| `time_submit`, `time_eligible`, `time_start`, `time_end` | float64 | **seconds from an arbitrary origin.** Add the price book's `epoch_offset` to get real dates |
| `wait_sec` | float64 | `time_start - time_submit`. Queue wait |
| `walltime_sec` | float64 | wall-clock runtime |
| `exec_sec` | float64 | GPU execution time from DCGM |
| `timelimit` | float64 | requested limit |
| `time_suspended` | float64 | **dead column — always -1** |

### Resources requested

| Column | Type | Notes |
|---|---|---|
| `gpu_count` | int64 | GPUs held, 1-64 |
| `gpu_hours` | float64 | **MEASURED** — summed DCGM execution time. The money column |
| `gpu_hours_alloc` | float64 | `gpu_count x walltime`. The *derived* figure, for comparison |
| `gpu_hours_ratio` | float64 | measured / allocated. 1.0 for most jobs; see trap 11 |
| `cpus_req` | float64 | |
| `mem_req` | float64 | **RAW AND BOOBY-TRAPPED.** Values above 2^63 have Slurm's per-CPU flag OR'd in. Parse naively and you report exabytes |
| `mem_req_mb` | float64 | decoded in prep. **Use this** |
| `mem_req_is_per_cpu` | bool | what the flag meant |
| `mem_req_total_mb` | float64 | decoded and multiplied out |
| `gres_req`, `gres_alloc` | str | `gpu:volta:1` etc |
| `gres_used` | float64 | **dead column — 100% null** |
| `tres_alloc`, `tres_req` | str | packed `k=v,k=v` strings |
| `array_max_tasks` | float64 | |
| `array_task_pending` | float64 | **dead column — always 0** |
| `priority`, `flags`, `track_steps` | float64 | scheduler internals |

### Utilization and power — joined from DCGM

| Column | Type | Notes |
|---|---|---|
| `sm_util_avg`, `sm_util_max` | float64 | **0-100 percent**, not a fraction. The "is it working" signal |
| `mem_util_avg` | float64 | 0-100 percent |
| `max_gpu_mem_used` | float64 | bytes |
| `mem_used_frac` | float64 | 0-1 fraction. Note the different scale from the two above |
| `watts_avg`, `watts_max` | float64 | |
| `energy_wh` | float64 | computed as avg watts x duration in prep |
| `pcie_rx_avg`, `pcie_tx_avg` | float64 | MB/s |
| `n_nodes_dcgm` | int64 | nodes seen in telemetry |

**Four dead columns**: `gres_used`, `array_task_pending`, `time_suspended`,
`is_terminal`. They carry no information. Do not build anything on them.

---

## `data/prepped/gpus.parquet` — 96,893 rows x 33 columns

**One row per physical GPU per job.** Row count equals the job's `gpu_count`
exactly, for all 74,849 jobs — a 30-GPU job spanning 16 nodes has 30 rows. Most
jobs used one GPU (65,021 of them), which is why 74,849 jobs produce 96,893 rows.

Use it when per-card or per-node detail matters — including per-node failure
counts. `jobs.parquet` already carries the job-level aggregate for most questions.

Key is `(Node, gpu_id, id_job)`, unique across all 96,893 rows. `gpu_id` is 0 or 1;
each node has two V100s.

**Requeued jobs can mix attempts.** For 10 of the 34 requeued jobs, the GPU rows
sit on machines from *different* attempts — job `22427814902` has its expected two
rows, one on each of two machines, though each of its three attempts ran on a
single machine. For those jobs the rows' `Node` values are not one placement, and
their `totalexecutiontime_sec` can include more than one attempt.

**66 rows report more runtime than their job had** — 44 jobs, about 1,700 GPU-hours
in excess of what the jobs' wall-clock allows (one card claims 1,135,500 seconds in a
29,872-second job). Most are not requeues; they are bad readings. Clip
`totalexecutiontime_sec` to the job's `walltime_sec` before trusting any per-card
duration.

`Node`, `gpu_id`, `id_job` are the keys. Then the DCGM measurements, each as an
avg/max/min triple: `smutilization_pct_*`, `memoryutilization_pct_*`,
`powerusage_watts_*`, `pcierxbandwidth_megabytes_*`,
`pcietxbandwidth_megabytes_*`, plus `maxgpumemoryused_bytes`,
`totalexecutiontime_sec`, `avgsmutilization_pct`, `avgmemoryutilization_pct`.

`energyconsumed_joules` is present and **does not integrate correctly over long
jobs**. Use average watts x duration, which is what `energy_wh` already is.

**`gpu_hours` here is per-GPU and sums to the job total.** Summing across the whole
file is safe — it gives 594,004, matching `jobs.parquet` exactly. But
`groupby('id_job').gpu_hours.first()` matches the job total for only 67,322 of
74,849 jobs: it works for single-GPU jobs and silently understates every wide one.
Take `.sum()`, never `.first()`.

The job-level columns (`state`, `id_user`, `time_*`, `partition`) are joined on
and are ~0.1% null where a DCGM row has no scheduler match.

---

## `data/synthetic/` — the projected layer

| File | Rows | What |
|---|---|---|
| `resources.parquet` | 77,399 | 74,849 `k8s:pod` + 2,129 `k8s:job` + 225 `k8s:node` + 195 `k8s:namespace` + 1 `k8s:persistentvolumeclaim` |
| `edges.parquet` | 198,601 | 81,521 `RUNS_ON` + 74,849 `CONTAINS` + 39,694 `OWNS` (all real) + 2,537 `MOUNTS` (synthetic) |
| `findings.json` | 11,979 | MantisGrid `Finding` records, 23 rules firing — see `docs/rules.md` |

A pod's `resourceId` is its `id_job`; its `name` is `job-<id>`.

**Users are `k8s:namespace` resources.** Each of the 195 users has one, with a
`CONTAINS` edge to every one of their pods. It exists so a failure can be attributed
to a person's work with a path in the graph to support it — every user has one,
blamed or not.

**Arrays are `k8s:job` resources.** A Slurm array — one submission that launches
many copies of a script — is modelled the way Kubernetes models a Job that owns its
pods: one `k8s:job` per array, with an `OWNS` edge to each task pod. Every array has
one, whether or not anything went wrong in it. (In the MantisGrid product the
watcher derives these owner edges from Kubernetes `ownerReferences`; the product
currently stores them under the edge type `CALLS`, which this dataset renames
`OWNS` because that is what they mean.)

**Join keys.** A finding carries `metadata.job_id` when it is about one job (11,351
of 11,979) and `metadata.node` when it names a node (5,386). User-, cluster- and
array-scoped findings have neither, because they are not about a single job or
machine — join those through `resourceIds`, which always resolve.

**Findings have a lifecycle.** 73% are `RESOLVED` / `isActive: false` — a
job-scoped finding whose job ended more than 30 days before the window closed has
aged out and is history rather than a task. Node-, user- and cluster-scoped
findings and the storage incident stay `ACTION_REQUIRED` regardless, because a
machine or a habit is still there after any single job has ended. **If you filter on `isActive` you will see
about a quarter of the corpus**, which is the actionable quarter.

### The PCIe columns, and a reading of them that does not work

A tempting inference is *"low utilisation plus high PCIe means the GPU was waiting
on input."* It does not hold here, and it is worth knowing why before you build on
it.

**The signature is inverted.** A GPU waiting on slow storage is not moving bytes —
none have arrived yet. Starvation shows up as PCIe *low*, not high.

**Saturation is the measurable version, and it never happens.** The V100 link is
PCIe gen3 x16, 15,754 MB/s. Peak observed on this cluster is **4,240 MB/s — 27% of
capacity.** `rules::gpu-pcie-saturated` is armed against exactly this and reports
`CLEAR`.

**And the columns themselves are rough.** A quarter of card-rows have identical
min, avg and max; `pcierxbandwidth_megabytes_max` is pinned at 2147 in 8.8% of rows
(2147 is INT32_MAX in bytes, so those are censored); and the median sits near 1,060
MB/s regardless of job length or utilisation.

A detector built on the tempting inference shipped here until September 2026. It
flagged 799 jobs, of which 553 had `sm_util_avg` of **exactly zero** — they were
not waiting on data, they never asked for any.

> **`docs/rules.md` is the rule catalogue** — every rule that is armed, the exact
> threshold it fires on, and what it explicitly does *not* claim. Read it before
> you read the findings; several rules report a symptom and deliberately withhold
> the cause, and knowing which is which saves you a wrong turn.

### The 11,979 findings

**11,858 (99%) are computed from the real telemetry. 121 are synthetic.**

**A finding means something is wrong.** `GET /v1/policies/rules` lists every rule
that is armed, including the ones that never fired — those show `status: CLEAR`
with a count of zero. Read that endpoint as well as the findings. One armed rule
sits at zero for a reason worth knowing: `rules::gpu-pcie-saturated` watches for
the PCIe bus running above 80% of link capacity while the GPU idles, and this
estate never gets within a factor of three of that. Data movement is not what is
holding these GPUs back.

The one synthetic scenario left is the filesystem incident. A fabricated
hardware-attribution layer (623 findings) was removed in September 2026 — it
existed only to mark invented "bad" machines, and anything invented to make such
a machine findable turns out to be a marker that identifies invented machines.

| Detector | Count | Basis | Scope |
|---|---|---|---|
| `rules::array-task-failure` | 5,044 | real — **carries `rootCauses`**, resolves to its array | job |
| `rules::wallclock-kill` | 1,544 | real | job |
| `rules::gpu-never-computed` | 1,459 | real — never ran a kernel, and did NOT complete | job |
| `rules::slow-cancel-of-idle-job` | 949 | real — **detection latency**, how long a GPU idled before its owner killed the job | job |
| `rules::idle-interactive-session` | 906 | real — an interactive session left open and idle | job |
| `rules::gpu-imbalance` | 689 | real, **per-GPU** — needs `gpus.parquet`; `jobs.parquet` averages the cards | job |
| `rules::gpu-not-needed` | 463 | real — never ran a kernel, and COMPLETED anyway | job |
| `rules::array-mass-failure` | 149 | real — the array itself; carries `rootCauses` | job |
| `rules::filesystem-latency-degraded` | 121 | **synthetic** incident; carries `rootCauses` | node |
| `rules::node-job-failure-burst` | 47 | real — 48-hour burst, **with causal attribution**: machine, person, or undetermined | node |
| `rules::node-hardware-fault` | 1 | real — a burst attributed to the machine; carries `rootCauses` | node |
| `rules::node-elevated-failure-rate` | 113 | real, **consecutive 2-week windows** vs the cluster rate in that same window | node |
| `rules::gpu-memory-oversized` | 108 | real | job |
| `rules::gpu-low-utilization` | 95 | real | job |
| `rules::multi-node-low-utilization` | 63 | real — 4+ nodes at under 20% | job |
| `rules::unsuccessful-gpu-spend` | 54 | real | user |
| `rules::timelimit-overreservation` | 41 | real | user |
| `rules::user-repeat-failure` | 36 | real, **long-horizon** | user |
| `rules::node-under-utilization-slo` | 35 | real, **SLO alert** — under 20% for 3+ consecutive weeks | node |
| `rules::queue-starvation` | 22 | real | user |
| `rules::node-failure` | 31 | real — every NODE_FAIL, on the machine that actually died | job |
| `rules::queue-wait-p95-slo` | 8 | real — p95 queue wait against a 4h target, weekly per partition | cluster |
| `rules::queue-weekly-peak` | 1 | real, **long-horizon** | cluster |
| `rules::gpu-pcie-saturated` | 0 | real, armed, **never fires** — bus peaks at 27% of link | job |

Every rule is deterministic and recomputable from the prepped parquet. **`docs/rules.md`
writes each one out** — the exact condition, threshold, scope and window, and what it
deliberately does not claim.

### Some findings describe the whole window, not a job

`metadata.horizon == "full_window"` marks the 37 findings that describe a pattern
across the four months rather than scoring one job — 36 people failing week after
week, and one weekly pattern in the queue. No individual job in them would trip a
per-job threshold — that is the point. The queue one:

> One weekday in seven takes 21,151 submissions against a median of 8,866 on other
> days, and the median wait rises to 2,007s from 2s.

### Five rules deliberately carry no `impact_gpu_hours`

`queue-starvation`, `queue-wait-p95-slo` and `queue-weekly-peak` are denominated in
**engineer-hours** of waiting. `timelimit-overreservation` is **capacity blocked by a
reservation**, which is not capacity consumed and is not part of the 594,004
GPU-hours allocated. `node-elevated-failure-rate` reports a rate against the cluster,
not an amount. Putting any of them in the same column as consumption invites a total
that exceeds the cluster. They carry their numbers in metadata instead.

### Summing `impact_gpu_hours` does not give you a recoverable total

| | GPU-h | vs the 594,004 allocated |
|---|---|---|
| naive sum of every finding | 931,607 | **157%** |
| job-scope findings only | 537,711 | 91% |
| deduplicated to those jobs' actual hours | 311,373 | 52% |

18% of the jobs that carry a finding carry more than one. Two findings on one job each describe a
slice of the same physical hours, so the column double-counts. And `impact_scope`
mixes denominators: a `user`-scope finding covers one person's entire four months
and overlaps every `job`-scope finding beneath it. **Adding across scopes produces
a number that means nothing** — which is why the naive total is impossible rather
than merely wrong.

---

## State codes

| Code | Name | |
|---|---|---|
| 0 | PENDING | never ran |
| 1 | RUNNING | at window close |
| 3 | COMPLETED | |
| 4 | CANCELLED | deliberate. 203,930 GPU-h — larger than FAILED + TIMEOUT combined |
| 5 | FAILED | 18,587 jobs |
| 6 | TIMEOUT | |
| 7 | **NODE_FAIL** | 10 jobs ended here — but **31 hit a node failure at some point**. See below |
| 11, 1024 | undecoded | terminal, no documented meaning. 1,021 GPU-h |

---

### Node failures do not stay put — and the job's machine is usually not the one that died

A job the scheduler had to restart is one `id_job` with several attempts. Its
`state_name` is the **last** attempt, so a job killed by a node failure and then
successfully rerun reads `COMPLETED`.

```
jobs whose final state is NODE_FAIL       10
jobs that hit a node failure at any point 31    <- start here
node-failure attempts in total            39

final state of those 31:
  NODE_FAIL 10 · CANCELLED 7 · COMPLETED 6 · FAILED 5 · TIMEOUT 3
```

**Filtering on `state_name == "NODE_FAIL"` loses two thirds of the hardware
signal.** `attempts`, `nodefail_attempts` and `hit_node_failure` carry the requeue
history.

**And `primary_node` / `nodelist` do not tell you where the failure happened.** They
describe the job's *final* attempt. A restarted job is, by construction, running
somewhere other than the machine that died. Of the 25 failures where we know
exactly which machine failed, **18 happened on a different machine from the one
the job finished on.** Attribute a node failure to a job's final machine and you
will blame the wrong machine nearly three times in four.

Four columns record where each failure actually happened:

| Column | Meaning |
|---|---|
| `nodefail_nodes` | the machines the failed attempt(s) were running on |
| `nodefail_exact` | `True` when every failed attempt ran on a single machine, so that machine is the one that died |
| `nodefail_last_end` | when the most recent failed attempt ended — i.e. when the machine died |
| `nodefail_wall_sec` | how long the failed attempt(s) had run before the failure |

**Only 25 of the 31 are located exactly.** The other 6 failed while running across
4, 4, 8, 8, 16, 16 machines, and the scheduler does not record which of them
failed. Crediting the failure to every machine in the list blames the innocent ones
along with the guilty one.

**The lost work is the failed attempt, not the job.** Failed attempts account for
7,772 GPU-hours (`nodefail_wall_sec` × `gpu_count`). A restarted job's own
`gpu_hours` mostly describe the retry, which was not lost.

### Two columns that used to mislead

**`primary_node` is not "the node the job ran on".** 1,472 jobs span more than one
node and carry **27.8% of the cluster's GPU-hours**. This column holds the *first*
entry of the Slurm nodelist, and nothing else.

```
job 63323698635 ran on 8 nodes
  primary_node = r9648383-n303766     gpu_hours = 3,840.2
  truth: 480.0 GPU-h on each of the 8
```

**For anything per-node, use `gpus.parquet`**, which has one row per (job, GPU) and
a truthful `Node`. Group by that. Attributing a job's whole `gpu_hours` to its
`primary_node` is how you claim a 2-GPU node delivered more hours than it physically
has. (This column was called `node` and documented as "use this one", which is how
that mistake got made in the first place.)

**`gpu_hours` is measured, not derived.** It is the sum of DCGM execution time
across the job's GPUs — not `gpu_count × walltime`. Both are shipped:

```
gpu_hours        594,004   measured, from DCGM
gpu_hours_alloc  593,980   gpu_count x walltime
```

They agree in aggregate and disagree on **5,219 jobs (7%) by more than 10%**, worst
case 19.5×, because DCGM folds every requeue attempt under one job id while the
scheduler keeps only the last. `gpu_hours_ratio` is the quotient, so you can find
them. The measured figure is the better one and is what every dollar number here
uses — but if you recompute from the formula and get a different answer, this is
why, and the difference is not an error.

### Arrays: the largest one is not an array

In the raw release, the jobs that are **not** part of any array still carry an
array id — Slurm writes `id_array_job = 0` and a `NO_VAL` task id, and the release
anonymises both like any other value. They arrive looking like the biggest array on
the cluster: 35,155 jobs from 192 different users, all sharing one task id. A real
array is one submission by one person. We null those ids and set
`is_array_task = False`; if you work from the raw CSVs, do the same, or one fake
"array" will own nearly half the jobs.

## Traps, in one place

1. **`mem_req` carries a bit flag.** Use `mem_req_mb`.
2. **`energyconsumed_joules` does not integrate.** Use `energy_wh`.
3. **Timestamps are offsets**, not dates. Add `epoch_offset`.
4. **`sm_util_avg` is 0-100; `mem_used_frac` is 0-1.** Different scales, adjacent columns.
5. **Exit codes cannot attribute fault.** Split by state; do not label "infrastructure waste".
6. **Idle GPUs emit nothing.** DCGM starts with the job. Unallocated time is invisible; it has to come from gaps in the scheduling data.
7. **Row-weighted != hour-weighted.** A third of rows account for 0.016% of compute.
8. **Four dead columns.** Listed above.
9. **Duplicate `id_job` rows** existed in the raw data. Already fixed in prepped.
10. **`gpus.parquet` grain is per-GPU.** `.first()` per job understates wide jobs; use `.sum()`. See above.
11. **`gpu_hours` is measured DCGM time, not `gpu_count x walltime`.** They differ
    by >10% on 5,219 jobs. Compare with `gpu_hours_alloc`; see above.
12. **`primary_node` is the first node only.** 1,472 multi-node jobs carry 27.8%
    of the GPU-hours. Use `gpus.parquet` for anything per-node.
