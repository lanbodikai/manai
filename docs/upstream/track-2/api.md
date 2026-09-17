# The API

Runs on your machine at `http://localhost:8000` once you've started it
(`docker compose up`). **The interactive spec at `/docs` is the reference** — this
page is a guide to what matters.

## Two layers

**Layer A is MantisGrid's real API** — the same paths and response models as the
product. What you learn here is real.

**Layer B is proposed.** It doesn't exist in the product yet. It's our guess at what a
business layer should look like, and finding out where that guess is wrong is part of
the point. Push back on it.

```
Layer A — the real API
  POST /v1/events/findings              list findings
  POST /v1/causal                       root-cause analysis for one finding
  POST /v1/neighbor                     the resource graph, N hops out
  GET  /v1/policies/rules               every rule, including ones that never fired
  POST /v1/detect/{integration_id}      run detection

Layer B — proposed
  GET  /v1/efficiency/summary           allocated -> computed -> completed
  GET  /v1/waste/breakdown              GPU-hours by job outcome
  GET  /v1/queue/latency                developer wait time
  GET  /v1/scaling/efficiency           utilization vs job width
  GET  /v1/resources/underperforming    ranked, with evidence
  GET  /v1/recommendations              actions and estimated savings
  GET  /v1/price-book                   dollars per GPU-hour, versioned
```

## From Python

`starter/mgai_client.py` is the fetch layer, already written:

```python
from mgai_client import MGAI
mg = MGAI()                                         # reads MGAI_URL, default localhost:8000

mg.efficiency_summary()
mg.rows(mg.waste_breakdown())                       # any Layer B response -> DataFrame
mg.findings_df(detector_id="rules::gpu-imbalance")  # findings, metadata unpacked
mg.causal(finding_id)
```

Downloading every finding takes about 24 requests. Keep the DataFrame rather than
re-fetching, or filter by `detector_id`.

## From an AI agent

`mcp_layer/` serves the same endpoints as tools for an AI agent, over MCP (Model Context
Protocol). With [uv](https://docs.astral.sh/uv/) installed and the data generated:

```bash
make mcp
```

`mcp_layer/README.md` has the list of tools and the config for connecting an agent
client such as Claude Desktop or Cursor.

---

## `POST /v1/events/findings`

A finding is MantisGrid's unit of "something is wrong here."

```json
{
  "id": "1f9c17fd-978c-5001-878a-7b2919f45bc6",
  "detectorId": "rules::gpu-low-utilization",
  "shortDescription": "Job held 32 GPUs at 0.9% compute utilization",
  "longDescription": "Job 12808277262 held 32 V100s for 492.1 GPU-hours. Average SM utilization was 0.9% while GPU memory sat at 99.2%.",
  "impactDescription": "492.1 GPU-hours consumed.",
  "resourceIds": ["6f0cb7e2-…", "6c175cc4-…", "…"],
  "rootCauses": [],
  "status": "RESOLVED",
  "severity": "LOW",
  "confidence": "HIGH",
  "category": "PERFORMANCE",
  "priority": "P3",
  "detectionTime": "2026-04-02T18:54:29Z",
  "isActive": false,
  "metadata": {
    "gpu_count": 32,
    "sm_util_avg": 0.91,
    "mem_used_frac": 0.9915,
    "impact_gpu_hours": 492.09,
    "impact_kind": "consumed",
    "impact_scope": "job",
    "job_id": 12808277262,
    "node": "r1051355-n750018"
  }
}
```

- **`metadata.job_id` and `metadata.node` are your join keys** back to
  `data/prepped/`. Never parse an ID out of the prose.
- **`impact_kind`** says what the GPU-hours are: `lost` (destroyed, must be rerun),
  `consumed` (finished, wastefully), `degraded` (finished, slowly), `unused_capacity`
  (held, never computed on). **Don't add across kinds.**
- **`impact_scope`** says what the number covers: one job, one node, one person's
  whole four months. **Don't add across scopes either.**
- **Severity is not cost.** That job cost about $1,230 and is `LOW`. Sorting findings
  by severity and calling it a cost ranking is the most common mistake in this track.
- **`status: RESOLVED`** means the job ended long enough ago that the finding has aged
  out. Filtering on `isActive` shows you about a quarter of the corpus.

`docs/rules.md` explains every rule. `docs/traps.md` explains why the column double
counts.

## `POST /v1/causal`

What is actually underneath a finding. Ranked culprits, with scores.

```json
{
  "findings": [{
    "root_cause": "pvc/scratch-lustre-02 degraded — filesystem p99 latency rose 30.3x, affecting 121 nodes",
    "culprit": [
      { "node": "pvc/scratch-lustre-02", "type": "k8s:persistentvolumeclaim", "score": 0.88 },
      { "node": "r1039410-n172107",      "type": "k8s:node",                  "score": 0.31 },
      { "node": "r1039410-n750018",      "type": "k8s:node",                  "score": 0.31 }
    ],
    "confidence": 0.74
  }]
}
```

121 nodes went bad at once. That is not 121 problems.

**Most findings have no causal chain, and that's normal.** Causal analysis resolves a
*cluster* of findings to one thing underneath them; a finding with empty `rootCauses`
has nothing to resolve to, and you get `findings: []` with a `message` saying why.

Five rules produce findings that do resolve, to four kinds of culprit:

| Rule | Resolves to |
|---|---|
| `filesystem-latency-degraded` | the shared volume |
| `array-task-failure`, `array-mass-failure` | the Slurm array (`k8s:job`) |
| `node-job-failure-burst` | a person's `k8s:namespace`, the machine, or nothing |
| `node-hardware-fault` | the machine |

In the array answer, each machine's score is its share of the failures — small and
spread out. That spread is the evidence the machines are *not* the cause.

## `POST /v1/neighbor`

The resource graph, if you want to walk it yourself.

```json
{ "resource_ids": ["6c175cc4-…"], "hop_count": 1 }
```

Returns `nodes` (`resource_id`, `resource_name`), `edges` (`source_id`, `target_id`,
and both names) and `resource_types`. Edge types are `RUNS_ON` (job → machine),
`OWNS` (array → job), `CONTAINS` (user → job) and `MOUNTS` (the synthetic volume).

## `GET /v1/policies/rules`

Every rule that's armed, with its status and finding count. A rule with zero findings
shows `status: CLEAR` — it ran and found nothing, which is itself worth knowing.

---

## Layer B

Every Layer B response carries the same envelope. `kind` is `"fact"` (deterministic,
recomputable) or `"judgment"` (a model said so; `confidence` is filled in). **Facts you
can check. Judgments you should check.** Always read `provenance.caveat` — it says what
the number does *not* mean.

### `GET /v1/efficiency/summary`

```json
{
  "metric": "capacity_waterfall",
  "window": { "start": "2026-02-25", "end": "2026-06-30", "granularity": "1d" },
  "unit": "gpu_hours",
  "rows": [
    { "label": "allocated",          "gpu_hours": 594003.8, "share": 1.0 },
    { "label": "computed",           "gpu_hours": 228903.8, "share": 0.3854 },
    { "label": "computed_completed", "gpu_hours": 100788.8, "share": 0.1697 }
  ],
  "monetized": { "amount": 1485009.6, "currency": "USD", "price_book_version": "2026-Q3" },
  "kind": "fact",
  "provenance": {
    "signals": ["dcgm_sm_util", "slurm_alloc"],
    "method": "sm_weighted_integration@v1",
    "caveat": "SM utilization is a proxy for useful work. A data-loader-bound or communication-bound job does real work at low SM occupancy. …"
  },
  "confidence": null
}
```

### `GET /v1/waste/breakdown`

GPU-hours by how each job ended:

| state | GPU-hours | share |
|---|---|---|
| COMPLETED | 229,041 | 38.6% |
| CANCELLED | 203,930 | 34.3% |
| TIMEOUT | 107,952 | 18.2% |
| FAILED | 50,033 | 8.4% |
| NODE_FAIL | 2,028 | 0.3% |

We deliberately don't sum these into a "waste" total. Which rows count is your call —
see `docs/traps.md` on `CANCELLED`.

### `GET /v1/recommendations`

```json
{
  "id": "rec_lowutil",
  "title": "Move sub-10% utilization workloads to shared allocation",
  "action": "Introduce a fractional-GPU queue and require a utilization justification above 2 GPUs.",
  "estimated_savings": { "amount": 53430.03, "currency": "USD", "price_book_version": "2026-Q3" },
  "estimated_savings_gpu_hours": 21372.0,
  "effort": "medium",
  "confidence": 0.61,
  "finding_ids": ["866a5584-…", "afc9f337-…", "…"],
  "kind": "judgment"
}
```

`finding_ids` is the click-through path: business number → recommendation → findings →
resources → raw data. Keep it intact and your dashboard survives an SRE clicking in.

### `GET /v1/price-book`

```json
{ "version": "2026-Q3", "usd_per_gpu_hour": 2.5, "usd_per_kwh": 0.15,
  "usd_per_engineer_hour": 95.0, "epoch_offset": 1750862959 }
```

Read-only. To model a different price, pass it on the request:

```bash
curl "localhost:8000/v1/efficiency/summary?usd_per_gpu_hour=3.50"
```

The response's `price_book_version` becomes `2026-Q3+custom`, so a dashboard can tell
a price change from an infrastructure change. `epoch_offset` maps the data's relative
timestamps to real dates.
