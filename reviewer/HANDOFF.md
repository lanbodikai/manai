# C Contract 0.4 review and integration handoff — 2026-09-17

## State and exact revisions

**Deterministic C implementation is reviewed and tested within the scopes below.
PR #3 remains draft; final merged-A+B/source-data/container acceptance is pending.**
No C merge into a shared branch or model-provider call was performed.

- Existing branch: `codex/evidence-review-service`.
- Existing PR: https://github.com/lanbodikai/manai/pull/3 → `codex/integration`.
- Pinned integration baseline: `db6f418f2cf4fb761eb560870814331b323eefd0`.
- A implementation exercised over sockets: `adfcd883edebfd8b7100179ab545cc4000fca479`.
- Baseline merge into C: `261254e`; contract adoption: `7fb356b`; reviewer fixes:
  `ebdc00a`; evaluation/real-host runner: `e48e57edecd3fd6745387bbef2f9d894a6e95674`.
- This handoff is a subsequent documentation commit. The exact published head is
  on PR #3; `git rev-parse HEAD` resolves it without a self-referential file hash.
- Latest fetched integration still points at `db6f418`. A+B candidate
  `origin/codex/ab-validated` is `5c4fd8376380b95ff09560ab7a688a5306ed5072`.
  Record the lead-approved merged A+B commit at the next integration pass; the
  candidate was inspected, not merged into C or declared accepted by this pass.

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

Remaining: real-data A→C check at this C revision, image build/run, final proxy/UI
checks and R01–R05 on the approved merged A+B base. Live-model evaluation is
explicitly deferred, not a deterministic-mode dependency. No finding/causal
corroboration or full-source certification is claimed.

## B-owned integration checklist

1. Keep this PR and branch. First approve/merge the A+B candidate into the agreed
   integration branch; record that exact commit. In the later C integration pass,
   merge it into C normally, preserving history and rerun affected C checks.
2. Build `reviewer/Dockerfile` from that checkout. Add service `reviewer:8002`
   under optional Compose profile `reviewer`; set `ANALYSIS_URL=http://analysis:8001`,
   `REVIEWER_MODE=deterministic`, `REVIEWER_MCP_CONTEXT=price_only`. Do not add a C
   dependency or provider requirement to base startup/health/build.
3. Route only the explanations POST to C. Use optional/lazy proxy resolution,
   preserve audit/client-request identity, keep the base result on C errors and
   use a 35-second browser timeout. All other A routes remain on A.
4. On the host with the verified five-file data, create/select a valid A audit
   and run the existing-audit check (substitute the actual service URLs and ID):

   ```sh
   python -m eval.agent.live_review --analysis-url http://127.0.0.1:3000 \
     --reviewer-url http://127.0.0.1:8002 --audit-id AUDIT_ID \
     --output reviewer/.private/merged-ab-real-review.json
   ```

   This runner needs direct access to C's internal `/health` as well as its
   explanations route. Run it inside the integration network when C is not
   host-exposed. Check the public proxy separately; do not add public health
   routes merely for this test.
5. Recheck no-pilot, successful replacement, failed trial/full rerun and extra
   validation; inspect signed/null output and zero false compatibility failures.
   A partial cohort review remains UNKNOWN. Run R01–R05 for absent, crashed,
   slow, malformed and unconfigured C while base chat/evidence/export still work.
6. Keep PR #3 draft until those combined checks are recorded and the lead reviews
   the exact head. Deterministic and future model readiness must stay separate.

**Stop here:** this pass prepared C and its PR; it did not enable C, change B's
Compose/UI, move shared branches, submit the event form or alter the default branch.
