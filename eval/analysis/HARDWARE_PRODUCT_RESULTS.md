# Bounded hardware product verification — 2026-09-17

Base: merged PR #8/main `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9`.
Branch: `codex/cpu-hardware-product`. Resolve the implementation commit with
`git log -1 -- analysis/hardware_scenario.py`. Private manifests record the exact
revision and hashes of evaluation inputs; runtime receipts record Docker images.
This is a local follow-up, not a release or merge approval.

## Product fit

Use **Decisions → Model** on the CPU-placement row, or **Inspect hardware scenario**
in the overview tile. The documented-hardware view covers the whole resource-fitting
historical population. It compares memory-adjusted cores with an exclusive node,
shows the successful replacement price range beside the full-rerun downside, and
expresses contribution both as baseline reduction and as share of the 20% target.
The remaining gap stays visible. The range varies price under assumed success;
it does not measure migration success or cover failure outcomes.

The existing manual small-pilot planner stays separate and starts without CPU
cost/runtime assumptions. A computes the new values; B displays the response.
No second frontend calculator, generalized optimizer, extra service or C work
was introduced. The scenario download is explicitly distinct from official claims.

## Checks executed

| Check | Outcome |
|---|---|
| Analysis unit/route tests, including invented array-metadata regression | 21/21 PASS |
| Existing base MCP-chat regressions | 4/4 PASS |
| Existing bootstrap/contract checks | 5/5 PASS |
| Dashboard unit tests | 61/61 PASS |
| Typecheck + production build + synthetic-marker exclusion scan | PASS, including actual Node 22 Docker build |
| HP01–HP05 independent real-source witness | PASS; exact cohort/fit identities, paginated groups, Decimal costs/target, stale-source rejection, pre/post semantic checksums |
| Hardware production browser witness | 8/8 PASS; model navigation, both allocations, target gap, evidence pagination, export, manual-scope isolation, desktop/mobile, outage/recovery |
| Existing production browser CPU cases | 8/8 PASS; real MCP, canonical v0.4 recovery and claims preserved |
| Desktop/mobile screenshot inspection | PASS; no page overflow at 390px |
| Independent human usability/U05 | NOT RUN |
| Operational CPU compatibility, output correctness, runtime, billing savings | NOT TESTED |

The host dashboard tests used Node 24.15.0; the production image builds/runs Node
22. No lockfile or dependency changes were made. Vite retains its large-chunk
warning; this is not a failed build.

Private receipts live under `private-eval/hardware-product/`; existing base-browser
receipts use `private-eval/integration/`. No real job rows or result totals are
included in this committed record.

Failed attempts were retained: first live run preceded dashboard readiness after
a Windows port conflict; second live run exposed array-valued prepared metadata.
The calculator fix added an original synthetic regression test. The first browser
attempt was interrupted without a verdict; the second used an overly strict select
label. Corrected the witness selector; the final browser run passed all checks.

## Reproduce on a provisioned machine

Default `docker compose up --build` includes the feature with the existing base
services. For isolated verification, run from this worktree in PowerShell:

```powershell
$env:MANAI_DATA_DIR = 'C:/path/to/canonical/data'
docker compose -p manai-hardware-check -f docker-compose.yml -f eval/integration/compose.hardware.yml up -d --build --wait
```

The override publishes only loopback ports 13111 (dashboard) and 18031 (official
API), on a separate network/volume. It mounts canonical data read-only. Check that
these ports and the declared subnet are available before starting. No other stack
is restarted. Verify `git check-ignore private-eval/hardware-product/probe.json`
and `.dockerignore` before generating local receipts.

```powershell
$source = (Get-Location).Path.Replace('\','/')
$revision = git rev-parse HEAD
New-Item -ItemType Directory -Force private-eval/hardware-product | Out-Null
docker run --rm --network manai-hardware-check_default --mount "type=bind,source=$source,target=/app,readonly" --mount "type=bind,source=$env:MANAI_DATA_DIR,target=/canonical,readonly" --mount "type=bind,source=$source/private-eval/hardware-product,target=/receipts" -e PYTHONDONTWRITEBYTECODE=1 --entrypoint python manai-hardware-check-analysis:latest -m eval.analysis.verify_hardware_product --data /canonical --output /receipts/NEW-RUN --revision $revision
node eval/integration/hardware.cjs http://127.0.0.1:13111 private-eval/hardware-product/NEW-BROWSER-RUN
node eval/integration/browser.cjs http://127.0.0.1:13111 base
```

Use a new output name every time; the independent and hardware-browser witnesses
refuse to overwrite prior attempts. The browser witness needs the locked dashboard
dependencies (`npm ci` in dashboard) and local Edge, or a supported installed
Playwright channel. Source and semantic fingerprints must remain unchanged.
Keep each run's `docker compose images`, `git status`, image IDs and container
mount/network configuration with the private manifest. Stop only this preview:

```powershell
docker compose -p manai-hardware-check -f docker-compose.yml -f eval/integration/compose.hardware.yml down
```

Next owner: A/B review the narrow feature contract and Model presentation before
publishing. Human rounds should check whether users distinguish full population
from pilot, simulated benefit from cash savings, and percent of baseline from
percent of target. Workload-owner CPU measurements would be the next evidence
needed to replace the runtime/compatibility assumptions; they are not a merge
prerequisite for a correctly labeled simulation demo.
