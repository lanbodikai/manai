# What you submit

A git repository. We run it — you don't send us screenshots.

```
submission/
├── docker-compose.yml      brings everything up with one command
├── claims.json             your numbers, machine-readable
├── REPORT.md               your writeup
├── data/                   empty in git -- see below
└── <your dashboard>
```

Building on this folder is the easy way: it already has the compose file, the API and
`data/`. **Keep `docker-compose.yml`, `claims.json` and `REPORT.md` at the repository
root.** If your project lives in a subfolder, that has to be the only
`docker-compose.yml` in the repository — there is nowhere on the form to tell us which
one to use.

## Handing it in

**One form, before September 17, 2026, 3:00pm PDT** — the moment the event ends.
Late submissions are not judged.

**https://forms.gle/UbPSwZhKNfkovM8s5**

It asks for four things:

1. **Your team** — every member, each with their student or career status.
2. **Project title and description**, and which track you are in.
3. **The repository** — public, with keys and secrets removed. **We judge whatever
   the link shows when we open it**: the default branch, at its latest commit when we
   clone. There is no commit to nominate, so make sure the work you want judged is
   merged and pushed before the deadline. Its README must list the AI models, coding
   assistants and agent frameworks you used, and say briefly what was AI-generated and
   what the team wrote. Using AI heavily is expected here; not disclosing it is the
   problem.
4. **A presentation of around four minutes**, showing the project actually working.
   A demo is strongly encouraged.

In English. One project, one track — if your work draws on both, tell us which
track's judging focus to apply.

After the deadline you may fix bugs and repair a broken deployment. You may not add
features.

## How we run it

```bash
git clone <your repository> && cd <it>
# we generate data/ the way you did -- data/README.md, steps 1 to 4
docker compose up          # your dashboard, reachable on :3000
```

- **Don't commit `data/`.** The licence forbids sharing anything generated from the
  source data, so we generate the same five files ourselves — the ones `make check-data`
  checks — and put them in `./data/` before we start. Read your data from there.
- **Keep our `api` service** in `docker-compose.yml` if your dashboard uses the API; it
  reads `./data/` too.
- **One command, unattended.** `docker compose up`, then we open `:3000`. No manual steps,
  no second command. Any stack you like — we judge what it serves, not its source. If it
  doesn't come up, we can't judge it.

## `claims.json`

The dashboard is for the CFO. This file is for us: the same shape for every team, so
the numbers can be read the same way.

`starter/claims.schema.json` lists every field and `starter/claims.example.json` is a
filled-in skeleton. Every value in both is invented — none of it is a hint.

```json
{
  "team": "your team name",

  "recoverable_gpu_hours": {
    "point": 61200, "low": 38000, "high": 84000, "confidence": 0.6,
    "basis": "Sub-10% utilization jobs above 2 GPUs, excluding CANCELLED."
  },
  "recoverable_usd": { "point": 153000, "low": 95000, "high": 210000 },
  "cancelled_is_waste": false,
  "cancelled_rationale": "Deliberate user action on a run that looked wrong.",

  "node_triage": [
    { "node": "rXXXXXXX-nXXXXXX", "window": 0, "cause": "user_code",
      "reasoning": "Grouped this node's FAILED jobs in the window by id_user; one user owned 84% of them.",
      "verdict": "no_action" }
  ],

  "card_imbalance_gpu_hours": { "point": 14000, "low": 11000, "high": 18000 },
  "card_imbalance_rationale": "Pivoted gpus.parquet on gpu_id per job.",

  "incident_root_cause": "<the resource you concluded was responsible>",
  "incident_action_scope": "single_resource",
  "incident_nodes_to_drain": 0,
  "incident_confidence": 0.8,

  "hardware_attributable_failures": 999,
  "hardware_attributable_rationale": "Which failures you counted, and why."
}
```

**Leave out what you didn't investigate.** Every field except `team` is optional. An
omitted field costs you nothing; a confidently wrong one costs a lot.

**Give intervals, not just a point.** `low` and `high` are where calibration is
scored. A wide honest interval that contains the truth beats a narrow one that misses.

**Say how you got there.** `basis`, `rationale` and `reasoning` are what the judges
read. Several of these claims are judged on that text rather than the number.

We have ground truth for some of these fields. You won't be told which.

### Node triage

`rules::node-elevated-failure-rate` fires 113 times across 87 machines, and every one
of those findings is in the data. There is no hidden list. The question is **why**
each one fired — `hardware`, `user_code`, `workload_mix`, or `cannot_determine`.

- The finding tells you the symptom and nothing else. Everything you need to work out
  the cause is in the prepped tables.
- `cannot_determine` is a real answer, not a blank. We'd rather read "here's what I
  ruled out and why nothing was left" than a confident guess.
- A cause with no evidence scores below a different cause backed by a join you show us.
- You don't have to do all 113. Do the ones you can defend.

### Hardware-caused failures

`hardware_attributable_failures` has more than one defensible answer — counting only
what the scheduler recorded is one; counting a fault it never noticed is another. It's
judged on `hardware_attributable_rationale`. Attributing *every* failure to hardware is
the one clearly wrong answer.

## How it's scored

| What | Scored by |
|---|---|
| the running dashboard | judges: actionability, the drill-down, business framing, what you
built on the MantisGrid AI API and its MCP tools, and any original insight |
| `claims.json` | some fields against a ground truth we hold, the rest by judges reading your `basis`, `rationale` and `reasoning`; intervals and confidences are how calibration is scored |
| `REPORT.md` | judges |

What each of these is evaluated on is in the track brief; how much each is worth is in
the participant agreement, which is the document that governs.

## Check it before you submit

```bash
make validate CLAIMS=claims.json                              # checks claims.json
make validate CLAIMS=claims.json URL=http://localhost:3000    # ...and that your dashboard answers
```

Then do what we'll do: clone your repository into a fresh folder, generate `data/`, run
`docker compose up`, and open `:3000`.

---

## Past the three tiles

None of this is required. It is where original insight is found and credited.

- **The drain-cost trade-off.** Pulling a bad node recovers reliability and destroys
  capacity. Where's the threshold? Defend it.
- **Calibration.** The judgment endpoints carry `confidence`. Are they any good? Plot
  predicted confidence against what you can verify in the raw data.
- **The queue tail.** Half of jobs start within 8 seconds; the slowest 1% wait 18 hours
  — **98,213 engineer-hours** of waiting in this window. That's a salary number, not an
  infrastructure number.
- **Width.** At 9+ GPUs, 59% of jobs run under 5% utilization and 9% run above 80%.
  Same allocation, opposite outcomes. Who are the two populations?
- **Argue with us.** Layer B is a guess. Showing, with evidence, that one of its
  endpoints has the wrong shape is exactly what we want.
