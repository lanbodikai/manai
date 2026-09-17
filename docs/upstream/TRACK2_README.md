# Track 2 — Cluster efficiency

*Why is this wasteful?* Find the money hiding in a GPU cluster.

> The CFO has been told to cut GPU spend 20% next quarter without slowing research
> down. **Build the view that tells her where to cut, and what it costs her if she's
> wrong.**

She isn't an engineer and she has thirty seconds. She'll forward your screenshot to an
SRE who *will* click into it — and if that path is broken, she stops trusting the
number.

## The cluster

Four months of real telemetry from MIT SuperCloud: **225 machines, 2 × V100 each,
74,849 GPU jobs from 195 researchers, 594,004 GPU-hours.**

**83% of the GPU time it allocated did not turn into completed work.** That's your
starting point, not your answer. The question is which part is actually recoverable,
and what breaks if you're wrong about it.

## Build three tiles

1. **Where the money is going** — spend broken down so a non-engineer can see what's what.
2. **Where to cut** — a specific, ranked, owned recommendation. Not "improve utilization."
3. **What it costs if you're wrong** — the tile most teams skip, and the one we care about most.

Anything past that is open.

## Get started

```bash
# 1. download the raw data into data/raw/        (see data/README.md)
make prep                                       # 2. build the tables
make generate                                   # 3. generate the findings
make check-data                                 # 4. check your data matches everyone else's
make up                                         # 5. API on :8000, notebooks on :8888
```

Then open `starter/notebook.ipynb` — one chart and one drill-down, end to end. You
should be querying within five minutes of having the data.

## What you hand in

A repository we can run with one command, serving your dashboard on `:3000`, plus a
`claims.json` with your numbers and a `REPORT.md`.

**Submit through https://forms.gle/UbPSwZhKNfkovM8s5, before September 17, 2026,
3:00pm PDT.** The form also asks for your team, your project title, and a
presentation of around four minutes showing the project working. Details:
`docs/submission.md`.

## How you're judged

What we evaluate:

- **Actionability** — does a non-engineer know what to *do* after 30 seconds?
- **Cost of being wrong**, and calibration
- **Evidence drill-down** — can you click from a business number to the raw data?
- **Business framing** — every number in dollars, hours or % of capacity
- **Use of the MantisGrid AI API and its MCP tools** — the findings, the causal
  analysis and the rule catalogue are there to be built on. An agent or a chat
  over the data is one way; it is an example, not the brief.
- **Original insight** — what you found that we didn't think to ask for

How much each is worth is in the participant agreement, which is the document that governs.

## The guides

| | |
|---|---|
| `docs/api.md` | the API, with example responses |
| `docs/data.md` | every column in both tables, and what lies to you |
| `docs/rules.md` | every rule that produces findings, and what it doesn't claim |
| `docs/traps.md` | read this before you add anything up |
| `docs/submission.md` | `claims.json`, the dashboard, and ideas beyond the tiles |

## Questions

Ask. We'd rather explain the domain than have you lose hours to something we
could clear up in a minute.
