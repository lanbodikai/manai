# Connected cost simulations — local handoff

Base `605f4cc`; branch `codex/portfolio-simulation`. Resolve the implementation
commit with `git log -1 -- analysis/portfolio.py`. No publication or merge.

## Product

Overview, Decisions and `#model` share one application-level draft and immutable
result. Defaults calculate when the canonical source is ready. Edits require
Recalculate and leave the previous result visibly labeled. Every Decisions row
links to its action assumptions and shows standalone versus assigned contribution.
The standalone amounts overlap and must not be added together.

The primary range is signed net reference cost reduction, with an illustrative
middle case, baseline percentage, share of the historical 20% target and remaining
gap. Failure stress is separate. The primary range is neither a confidence interval
nor a calibrated forecast. Research performance and cash savings are unverified.

Winston expanded the initial three-action plan to all eight during implementation.
CPU placement, checkpoint/restart and idle release are detailed mechanisms. Startup
failure prevention, batch-task validation, low-use allocation reduction, improved
GPU balance and GPU memory right-sizing are **assumption-only screening estimates**.
Their source cohorts are real rule-linked jobs; effectiveness, replacement costs,
hardware feasibility and root causes have not been established.

## Fixed models and accounting

The versioned `contracts/portfolio-presets.json` contains only configuration, no
source records. It is runtime configuration, not a synthetic response fixture.
The three detailed models use the approved presets unchanged.

Let H be recorded GPU-hours, T scheduler hours, g GPU count, p the official GPU
reference price, e enrollment share, and F fixed setup/storage/other dollars.

- CPU: reuse hardware sizing and the existing calculator, with unchanged runtime,
  zero extra queue and physical-core units. CPU price ratios are .02/.0125/.005.
- Checkpoint: n = ceil(T / interval) - 1, floored at zero, puts checkpoints strictly
  before termination. Preserved progress S = n × interval. Avoided replay value is
  e × replay_share × H × S/T × p. Overhead is e × g × (n × checkpoint_time +
  restart_time) × p, charged also to enrolled work with no benefit. Equivalent
  remaining useful work cancels. Failure preserves no progress and retains overhead.
- Idle release: tail fraction = max(0, 1 - release_age/T). Gross released reference
  value = e × H × tail_fraction × p. Mistaken releases add e × mistake_share × H × p
  for a full rerun, only when the job reaches the release age. Failure sets the
  mistaken share to one. Warn 15 minutes before the release age. The release time
  is assumed, not inferred from whole-job average utilization.
- Five screening models: lower/illustrative/upper enrollment .25/.5/.75;
  avoided-allocation fractions .1/.25/.5; extra-cost fractions .1/.05/.02. Net =
  e × H × p × (avoided_fraction - extra_cost_fraction) - F. Failure assumes zero
  avoidance, retains extra cost and adds one enrolled allocation's reference value;
  that failure-cost fraction is editable. Timing remains unknown.
- Fixed F is charged once per selected action in every case, even at zero
  enrollment or empty assigned scope. Zero inputs explicitly mean omitted costs.

Cancelled jobs remain excluded. Detailed timing models reject invalid duration/GPU
count and discrepancies above 10%, measured against g × T; CPU retains its existing
resource-fit rules. Screening models need only valid recorded allocation and make
no timing claim. All exclusions remain in accounting coverage.

Assignment is fixed, not optimized after seeing costs: fitting CPU → idle release
→ remaining timeouts → startup failures → batch-task validation → low utilization
→ GPU imbalance → memory sizing. Only selected, evaluable actions participate.
Each job contributes once. Assignment changes when actions are deselected.

Each complete portfolio case is calculated before taking minimum/maximum; losses
are preserved. The historical baseline includes all unique prepared jobs, including
cancellations. Target = .2 × baseline. Checkpoint contribution is avoided future
replay for equivalent work; normalizing against the historical target does not
claim to retroactively reduce the original bill.

## Additive interface and reproducibility

`portfolio-simulation-1` is separate from active v0.4 and `cpu-hardware-1`.

- `POST /api/portfolio-simulations`: dataset version, selected actions, allocation,
  three case configurations and fixed costs; returns immutable summary/statistics.
- `GET /api/portfolio-simulations/{id}?dataset_version=...`: the frozen summary.
- `GET /api/portfolio-simulations/{id}/evidence`: dataset version, action filter,
  offset and limit (maximum 100). Each row records source inputs, assignment,
  exclusions and all per-job cases.

The service retains 16 snapshots; eviction produces explicit 404 and recalculation
restores an identical source/configuration result. Source drift and stale versions
fail explicitly. Snapshots cannot mutate canonical audits or claims. The JSON
simulation report export is explicitly not claims.json. No new dependency/service.

Run the normal provisioned one-command Compose deployment. The existing isolated
override was used for local verification at loopback port 13111, with a separate
network and read-only canonical data. It does not restart the release stack.

From the worktree, following the mount pattern in HARDWARE_PRODUCT_RESULTS.md:

```text
python -m eval.analysis.verify_portfolio --data <canonical-directory> --output <new-private-run-directory> --source <worktree> --url http://127.0.0.1:13111 --revision <git-head>
node eval/integration/portfolio.cjs http://127.0.0.1:13111 private-eval/portfolio/NEW-BROWSER-RUN
node eval/integration/browser.cjs http://127.0.0.1:13111 base
```

Use the pinned Python image for the verifier. Inside the isolated Compose network,
use `http://dashboard:3000`. Verify Git/Docker exclusions first; use a fresh output
directory. The verifier stores full configurations, code hashes, canonical semantic
fingerprints, per-job evidence, summaries, a private report and failure receipts.
Store runtime image IDs alongside the final manifest. No source-derived outputs
are committed.

## Executed checks

- PS01–PS04 PASS: full canonical population, independent source-cohort reconciliation,
  exclusive assignments, Decimal comparisons for all modeled job cases, standalone
  and portfolio totals, target accounting, immutable result and unchanged source.
- Analysis unit/route tests: 29 PASS, including checkpoint boundaries, no replay,
  no release before threshold, full reruns, losses, monotonicity, screening priority,
  invalid assumptions, snapshot eviction and unchanged claims.
- Existing base MCP-chat tests: 4 PASS. Bootstrap/contract tests: 5 PASS.
- Existing frontend suite: 61 PASS. Typecheck and Node 22 production Docker build:
  PASS; production synthetic-module exclusion remains enabled.
- Portfolio production browser: 7 grouped checks PASS, covering all eight actions,
  cross-page draft/result state, deep links, recalculation, deselection, evidence,
  exports, invalid inputs, service failure/retry and desktop/mobile layout.
- Existing real CPU/MCP/claims browser: eight CPU cases PASS, real MCP calls and
  matching canonical exports. Human U05 and actual workload effects NOT RUN.

The first production build rejected configuration placed under the synthetic
examples directory; moved the genuine runtime configuration without weakening
the bundle check. The first browser run found mobile navigation overflow from the
additional Model entry. Fixed bounded horizontal navigation and reran successfully.
Private failed browser receipts remain preserved; no preset was tuned afterward.

Next owner: A/B review the presentation and assumptions, then a human round to
check understanding of standalone versus combined cost, benchmark versus billing,
and detailed models versus screening. Publishing/merging is a separate decision.
