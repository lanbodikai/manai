# Team start here — Track 2 / plan v0.9

**Current integration branch contains the common bootstrap.** Read [BOOTSTRAP_STATUS.md](docs/BOOTSTRAP_STATUS.md) and [BOOTSTRAP_BOUNDARY.md](docs/BOOTSTRAP_BOUNDARY.md) first. README contains the current setup. Older bootstrap recipes below preserve the original workflow; do not repeat imports or recreate existing branches. The :3000 page is a temporary verification page, not B's final dashboard.

Our thesis: audit a completed zero-GPU-compute cohort for a CPU-placement pilot, show a defensible recovery range and downside, and let a CFO/SRE inspect and question the supporting evidence. The pilot's operational savings are unproven. The target is 20%; we show our contribution and remaining gap honestly.

## 1. Get the same plan

Requires Git. For the build, the integration machine needs Docker with Linux containers and `docker compose version` working. Host Python/Node installation is not required if build/runtime work is containerized. C alone needs a model/provider configuration; never paste keys into Git or chat.

```sh
git clone --branch codex/planning https://github.com/lanbodikai/manai.git
cd manai
git log -1 --oneline
```

Existing clone: save your own changes first, then `git fetch origin` and `git switch --track origin/codex/planning` if that local branch does not exist. If it exists, switch to it and `git pull --ff-only`. Do not reset another participant's work.

Read this page, [requirements](docs/REQUIREMENTS.md), [official-doc review](docs/TRACK2_REVIEW.md), and your workstream. The API is [OpenAPI v0.3](contracts/openapi.json); examples are synthetic. Proposed choices remain labeled; do not invent results.

## B may start immediately

Winston authorized [B0 before bootstrap](docs/workstreams/B_PREBOOTSTRAP.md): isolated frontend, explicit synthetic fixtures, typed mock/HTTP adapters and focused UI tests. That file contains the prompt and exact integration steps. It overrides the wait-for-baseline instruction for B0 only. A lead/assigned bootstrap session prepares the shared baseline while B builds the UI. B later merges that baseline and resumes integration coordination.

## 2. Shared bootstrap — lead/assigned session, before full split

The assigned bootstrap session creates `codex/integration` from this published planning branch. This is the shared implementation/PR target, not the final judged branch yet. A helps inspect data and assumptions. C checks the MCP documentation/provider availability without blocking bootstrap.

```sh
git switch -c codex/integration
```

Execute the [upstream import manifest](docs/UPSTREAM.md). Pin official source commit `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`, import only specified Track 2 paths, retain notices and `mcp_layer` name, and record provenance. Official code is available from:

```sh
git clone https://github.com/MantisGridAI/hackathon-2026-official.git ../mantisgrid-official
git -C ../mantisgrid-official checkout --detach 314cca0bba49e1bb137aa9094d1dac4cdf7e4490
```

Use an unused sibling destination; an existing directory must be inspected/reused, not overwritten. Do not copy upstream `.git` or overwrite our planning docs. Read [official data instructions](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/data/README.md); download/extract raw files into `data/raw/`. After import:

```sh
docker compose run --rm prep
docker compose run --rm generate
docker compose run --rm prep python scripts/checksum_data.py
docker compose up -d api
```

All five canonical files must pass the supplied checker. Keep data and generated source records out of Git. Inspect the running official API at `http://localhost:8000/docs`; query one real overview and make one real MCP call using the supplied stdio server. Install/pin its dependencies in the base image so final startup needs no separate MCP command. Do not assume Layer B judgments are validated facts.

Then create the smallest dashboard/service skeleton: :3000 renders one real overview and a visibly synthetic audit fixture through our API; test one success and one error response. Inspect the actual cohort columns/records. Freeze API v0.3 adapters and fixture agreement. No need to finish audit calculations, all views or the reviewer yet.

Record in `docs/BOOTSTRAP_STATUS.md`: exact upstream and contract versions, generator verification, five-file results/data fingerprint, commands, API and MCP results, cohort feasibility, UI success/error check, Docker host, owner names, actual time remaining and blockers. Never mark an unrun check passed.

Commit the bootstrap and push `codex/integration`; share its exact SHA as `BASELINE_COMMIT`. **That is the split gate.** If data is blocked, B may develop labeled fixture UI while A fixes setup, but report partial progress rather than a passed gate. C credentials never gate the base.

## 3. Exact split

| Participant | Owns | Does not own | First reviewable slice |
|---|---|---|---|
| A | `analysis/`, `service/` including `service/base_chat/`, analysis/base-chat tests, methodology, canonical claims | React, root Compose, C's richer reviewer | Real audit → resolving evidence → claims; then minimum MCP chat |
| B | `dashboard/`, root Compose/proxy, UI/integration tests, report, demo, integration branch | Recomputing A's financial results or changing source semantics | Three-view fixture UI; then real A integration |
| C | `agent/`, `reviewer/`, its Dockerfile/tests/evals | Base chatbot, canonical claims, root Compose | Real MCP-backed review service; then grounded model answers |

A's `/api/audits/{audit_id}/chat` is **required**, template-based, real MCP, no model key. C's `/api/audits/{audit_id}/explanations` is **optional richer review**, profile `reviewer`. The base works if C cannot build, crashes, hangs or returns invalid output. C's actual implementation is unnecessary for B's failure tests: use isolated stubs.

## 4. Branches and review

After B announces the baseline, each teammate uses their own clone (or a separate worktree). Fetch and branch from the exact same commit, not whichever branch happens to be newest:

```sh
git fetch origin
git switch -c codex/analysis-service <BASELINE_COMMIT>
# B instead: codex/product-integration
# C instead: codex/evidence-review-service
```

Replace the placeholder before executing. Do not run all three branch commands in one shared working directory. Keep generated data local per checkout; rerun the official setup where needed. Share commit IDs and contract/data versions, not raw datasets.

Open draft PRs into `codex/integration` once a coherent slice is testable. A1/B1 can merge separately after their checks and cross-review; partial fixture slices must stay labeled. B coordinates merges; A reviews arithmetic/evidence, B reviews API/UI/startup, C can review source/tool grounding but cannot block the base merely by being absent. Changes to shared schemas need affected owners' agreement, fixtures and version updates.

Required final base checks: T01–T09, D01–D06, applicable C01–C06 API checks, M01–M04 live-chat checks, U01–U05, P01–P03, R01–R05. See [exact conditions](docs/EVALUATION.md). C adds G01–G05 and repeated eight-case evaluation before enabling its enhancement. `C01` in the API test list is a test ID, not participant C.

Do not claim all checks passed just because a PR merges. End every handoff with commit, scope, commands/results, NOT RUN checks, limitations and next owner. Preserve at least 30 minutes for integration/demo and 20 for submission; recompute against the actual event deadline, do not trust an old schedule.

Final publishing into the judged default branch and event-form submission are separate lead-coordinated steps. Do not assume `main` exists in this initially empty remote. Before judging, ensure the intended final branch is the default or merge into the existing default with lead authorization; verify it on GitHub. No force pushes or automatic default-branch changes.

## 5. Copy-paste session prompts

For immediate B work, use B_PREBOOTSTRAP.md instead of the post-bootstrap B prompt below.

Each prompt below is an implementation assignment when supplied by the team lead to that session. It supersedes the historical planning-only mode only within that assignment. The current published branch itself does not prove implementation has begun.

### Shared bootstrap session (B first)

```text
Execute the shared bootstrap for manai in TEAM_START_HERE.md, section 2.
Start from origin/codex/planning and create codex/integration. You are assigned
to import the pinned official Track 2 starter/notices, provision local data,
verify checksums, get one real API query and MCP call working, inspect the
approved cohort and create the minimal frontend/backend fixture path.
Read AGENTS.md, docs/UPSTREAM.md, TRACK2_REVIEW.md, ROADMAP.md, API_SPEC.md and
EVALUATION.md. Preserve unrelated work and keep data/secrets out of Git.
Update phase/status documentation to reflect this assignment. Record actual
checks in docs/BOOTSTRAP_STATUS.md. Commit and push codex/integration, then
report the exact common baseline SHA and whether the split gate passed.
Stop at the split gate; do not implement all A/B/C work or dispatch agents.
```

### A — analysis and required minimum chatbot

```text
Implement Workstream A from <BASELINE_COMMIT> in your own checkout/worktree,
branch codex/analysis-service. Read AGENTS.md, TEAM_START_HERE.md,
docs/workstreams/A_ANALYSIS_SERVICE.md, CONTRACT.md, API_SPEC.md,
TRACK2_REVIEW.md and EVALUATION.md (all docs paths under docs/).
Own deterministic cohort/dedup/scenario/downside/audit/evidence/claims and
the REQUIRED /chat route using real official MCP calls, supported-question
templates and no model key or C dependency. API contract is v0.3.
Deliver A1 then A2 with their actual T/D/API/M checks, including D06's final
range basis. CPU placement is already upstream; do not invent novelty,
compatibility or realized savings. Preserve B/C ownership.
Commit/push your branch and open draft slices targeting codex/integration.
Request B review when slice conditions pass; B coordinates merges.
Report commits, actual checks, data/contract versions and remaining blockers.
```

### B — product and integration

```text
Implement Workstream B from <BASELINE_COMMIT> in your own checkout/worktree,
branch codex/product-integration. Read AGENTS.md, TEAM_START_HERE.md,
docs/workstreams/B_PRODUCT_INTEGRATION.md, CONTRACT.md, API_SPEC.md,
TRACK2_REVIEW.md and EVALUATION.md (all docs paths under docs/).
Own three tiles, dollar-to-source drilldown, scenario UI, required A /chat
interface, Compose/proxy, report/demo and merge coordination. Show the 20%
target and audited contribution/gap using A's canonical values. Build B1
with labeled fixtures, then B2 with real A routes. API contract is v0.3.
Default startup must work with no C build, DNS host, process or model key.
C /explanations is optional under reviewer profile. Verify U/P/R and shared
API/M checks; use failure stubs without waiting for C. Preserve A arithmetic.
Commit/push slices and open draft PRs to codex/integration. Cross-review and
merge A/B slices only after their stated checks pass. Enable C after its
checks pass. No force push, default-branch change or event submission.
Report startup command, commits, actual checks and separate base/C readiness.
```

### C — optional richer evidence review

```text
Implement Workstream C from <BASELINE_COMMIT> in your own checkout/worktree,
branch codex/evidence-review-service. Read AGENTS.md, TEAM_START_HERE.md,
docs/workstreams/C_EVIDENCE_REVIEW_SERVICE.md, CONTRACT.md, API_SPEC.md,
TRACK2_REVIEW.md and EVALUATION.md (all docs paths under docs/).
Own only optional reviewer/agent service, its Dockerfile/tests/evals at
/api/audits/{audit_id}/explanations. Read A audits/evidence over HTTP and
use official MCP tools; never change canonical money, cohorts or claims.
A/B own the required minimum /chat. Keep your dependencies isolated.
Deliver C1 real MCP/tool service then C2 model-backed review with G01–G05,
the repeated eight-case suite, source identity and bounded failure handling.
Keep provider keys server-side; report missing configuration honestly.
Commit/push slices and open draft PRs to codex/integration for A/B review.
B owns root Compose and merges. Your blockers cannot stop A+B.
Handoff commits, config variable names, tool/eval evidence and limitations.
```
