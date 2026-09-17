> Latest: real-data Docker website and C failure-isolation acceptance passed.
> See [REAL_HOST_HANDOFF.md](REAL_HOST_HANDOFF.md) for the current pinned receipt.
> The isolated preview is http://127.0.0.1:13012; no main merge was performed.

> Current work moved to a fresh branch from PR #8 main: `codex/c-main-integration`.
> See [INTEGRATION_STOP.md](INTEGRATION_STOP.md) for the tested full-flow simulation,
> mobile fix and 15-minute integration-host stopping point. The PR #3 notes below
> describe the preserved original C branch, not authorization to merge main.

# C Contract 0.4 review and integration handoff — 2026-09-17

## State and exact revisions

**PR #8 main is merged into C without conflicts; deterministic service/proxy
compatibility checks pass. PR #3 remains draft for canonical-data/container
acceptance and final combined browser validation on the integration host.**
No C merge into a shared branch or model-provider call was performed.

- Existing branch: `codex/evidence-review-service`.
- Existing PR: https://github.com/lanbodikai/manai/pull/3 → `codex/integration`.
- Previous runtime baseline (merged PR #7): `610f89d8d2b4b9c1aa07b7e2c12087ec4849adeb`.
- Existing PR target remains `codex/integration` at `982b40795a097624507eefc5d17dc266baf1f0f0`.
  Main now has newer B changes; retargeting the same PR to main would isolate the
  C-only diff. Do not interpret the older integration target as the tested base.
- Previous main publication notes: `7197d03cd4b98813583e8eac86cd723417acfbb8`,
  merged without conflicts at `cae5647efa36d6452543868e97fc91fa56fa0ec3`.
  Only six A/B documentation files changed; tested runtime files are identical.
- Original pinned integration baseline: `db6f418f2cf4fb761eb560870814331b323eefd0`.
- A implementation exercised over sockets: `adfcd883edebfd8b7100179ab545cc4000fca479`.
- Baseline merge into C: `261254e`; contract adoption: `7fb356b`; reviewer fixes:
  `ebdc00a`; evaluation/real-host runner: `e48e57edecd3fd6745387bbef2f9d894a6e95674`.
- This handoff is a subsequent documentation commit. The exact published head is
  on PR #3; `git rev-parse HEAD` resolves it without a self-referential file hash.
- Conflict-free PR #7 merge into C: `c5a9f5d98da0c53d9c6f5d0b7709d202726f1926`.
- Tested C plus production-proxy harness: `a32af3e671a0ccd0a3f2c55c58e495f20b3a016b`.
  Subsequent handoff edits are documentation only. No A/B runtime edits were needed.
- Latest tested main (PR #8): `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9`.
- Current tested C merge: `f16f7b370c4813a8cb431e26fd5d540b19406cb1`; no conflicts.
  C runtime and test harness unchanged; newer B code was adopted from main only.

## Delivered

Active Contract 0.4 comes from `contracts/openapi.json`; no proposal flag, legacy
0.3 fallback or new public DTO. `POST /api/audits/{audit_id}/explanations` preserves
Explanation/Error shapes and uses only A's read-only HTTP endpoints.

C handles A's canonical `GPU-hours` / `GPUs` units and original fixture aliases,
aggregate references and named nullable-column aggregate observations. Aggregate
diagnostics never count as extra jobs or substitute for raw predicate evidence.
The selected pilot job is fetched before pagination and deduplicated. At most
100 distinct details/four pages are fetched; separate targeted/listed counts keep
partial reviews honest. Individual pilot arithmetic can pass while cohort totals
remain unknown. Negative/unknown amounts and H-versus-g×T remain distinct.

The answer gives A's quoted values, compact single-job cost/delay facts, grouped
failed/unknown checks, coverage, caveats and proposed correctness/runtime/recovery
steps. Detailed checks remain in private reports. C never replaces A's claims or
turns a scenario into verified cash savings, CPU safety or automatic rollback.

## Evidence from this pass

After the PR #8 merge, reviewer/contract/deterministic checks and nine production-
proxy scenarios were rerun successfully. The direct-socket result below is from
PR #7; the new run uses the same actual A/C processes through the production proxy.
Current merged-base checks:

- **56/56 dashboard tests PASS**; TypeScript and production build PASS, including
  live-bundle mock exclusion. Existing bundle-size warning remains non-blocking.
- **9/9 production-proxy scenarios PASS** using B's actual built server and A/C
  processes with original synthetic A inputs. 18 actual MCP operations in this PR #8 run;
  scoped citations and immutable audit/claims verified through the proxy.
- Stopping C gives normalized 503 while A audit/claims/health and the dashboard
  page remain available. This is an actual process/proxy test with synthetic data.
- **3/3 existing Chrome browser failure tests PASS**, covering unavailable,
  timeout and malformed reviewer responses. These use B's explicit demo doubles;
  they are not a combined real-data browser or Compose resilience acceptance.
- Contract, A/service, MCP and API source are identical to the previously tested
  A baseline. The dashboard and root Compose remain byte-identical to merged main.

- **99/99 reviewer tests PASS**: includes ten new v0.4 compatibility/budget/output
  cases; existing numeric, identity, timeout, provider-double and failure checks.
- **5/5 active bootstrap contract tests PASS**.
- **24/24 deterministic evaluation attempts PASS** (eight cases × three runs).
- **9/9 actual A→C socket scenarios PASS**, with original synthetic inputs:
  no-pilot plus all eight CPU cases, 18 real MCP operations, resolving citations,
  unchanged A audits/claims, zero false FAIL checks, expected UNKNOWN lineage.
  The actual A missing-audit path also returns normalized 404.
- Isolated Python 3.12.14 dependency check and compile checks PASS. No dependency
  files were changed. Published source changes are C-owned only.
- No paid/live model evaluation. Provider transport checks use explicit doubles.

The socket peer imports actual pinned A routes/calculators but substitutes a
clearly marked synthetic data context and readiness in that isolated process.
It is **not** a canonical five-file or production A+B result. The nine reviews
retain `insufficient_evidence` because real price-book metadata cannot prove
matching audit lineage; this is expected, not an implementation failure.

Full commands, historical failures and private receipt names are in
`eval/agent/RESULTS.md`.

## Host limits and remaining checks

This Mac has no Docker executable or installation. No real A service answered at
localhost ports 8000/8001/18001/8002. The available source directory contains only
`prepped/jobs.parquet` and `prepped/gpus.parquet`; generated
`synthetic/resources.parquet`, `synthetic/edges.parquet` and
`synthetic/findings.json` are absent. Do not relabel old-version checks from B's
host as acceptance of this updated C image.

Remaining: real-data A→C check at this C revision, image build/run, combined
real-data UI checks and full R01–R05 (including Compose startup/build failure).
Production proxy compatibility is now checked with synthetic A inputs. Live-model evaluation is
explicitly deferred, not a deterministic-mode dependency. No finding/causal
corroboration or full-source certification is claimed.

## B-owned integration checklist

1. PR #8 sync is complete at the exact commits above. Keep this PR and branch;
   use the tested main baseline for the remaining integration-host checks.
2. Build `reviewer/Dockerfile` from that checkout. Add service `reviewer:8002`
   under optional Compose profile `reviewer`; set `ANALYSIS_URL=http://analysis:8001`,
   `REVIEWER_MODE=deterministic`, `REVIEWER_MCP_CONTEXT=price_only`. Do not add a C
   dependency or provider requirement to base startup/health/build.
3. The merged production server already has optional `REVIEWER_URL` routing,
   a 31-second proxy deadline and a 35-second browser deadline. Configure the
   reviewer origin only when enabling it. Keep existing base independence and
   request identity checks; verify the public route in the deployment.
4. On the host with the verified five-file data, create/select a valid A audit
   and run the existing-audit check (substitute the actual service URLs and ID):

   ```sh
   python -m eval.agent.live_review --analysis-url http://127.0.0.1:3000 \
     --reviewer-url http://127.0.0.1:8002 --explanations-url http://127.0.0.1:3000 \
     --audit-id AUDIT_ID \
     --output reviewer/.private/merged-ab-real-review.json
   ```

   This runner needs direct access to C's internal `/health` as well as its
   explanations route. `--explanations-url` exercises the public proxy while
   checking deterministic mode via direct internal C health. Run inside the
   integration network when needed; do not expose health merely for this test.
5. Recheck no-pilot, successful replacement, failed trial/full rerun and extra
   validation; inspect signed/null output and zero false compatibility failures.
   A partial cohort review remains UNKNOWN. Run R01–R05 for absent, crashed,
   slow, malformed and unconfigured C while base chat/evidence/export still work.
6. Keep PR #3 draft until those combined checks are recorded and the lead reviews
   the exact head. Deterministic and future model readiness must stay separate.

**Stop here:** this pass synchronized and checked C against merged main; it did not enable C, change B's
Compose/UI, move shared branches, submit the event form or alter the default branch.
