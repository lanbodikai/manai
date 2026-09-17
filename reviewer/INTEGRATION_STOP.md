# Isolated website integration: 15-minute stopping point

## Current result

The existing main website can use C through its production explanations proxy.
A full browser simulation passes on a separate branch. Main and the original
C branch/PR were not changed by this integration pass. Stop feature work here.

- New branch: `codex/c-main-integration`.
- Fresh starting main: `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9` (PR #8).
- Existing C imported: `846ee972d1476c1487878c08fd822cecb8ec33eb`.
- Integration merge: `5325858bb787095004980767ad212edb274b0bf0`.
- Narrow-screen fix: `ff82dbf` (four CSS lines only).
- Tested simulation/overlay committed as: `91edaa74e7b1f44e41d01f6c900cc78240939dd9`.
- Active contract 0.4; A source `adfcd883edebfd8b7100179ab545cc4000fca479`.

Only the answer display required a product change: long fingerprints expanded a
390px page to 483px. Answers now wrap identifiers and retain line breaks; the
same browser assertion reports 390px after the fix. All A calculations, shared
contracts, service code, production proxy and root Compose are unchanged.
The B-owned CSS change is isolated and must be included in integration review.

## Functional checks completed

- 123 Python tests: 15 analysis, 4 base MCP chat, 5 contract, 99 reviewer.
- 56 dashboard unit tests, TypeScript, production build and mock-exclusion check.
- 24 deterministic evaluation attempts (eight cases repeated three times).
- Four existing browser regressions: reviewer unavailable, timeout, malformed,
  and unavailable live A without silently loading mock data.
- Full production browser flow: overview → audit → all eight CPU cases → base
  MCP chat → C review → scoped evidence drawer → matching claims download.
  Nine actual C reviews have no false FAIL checks; unknown lineage stays unknown.
- Four simulation phases: no C configured, C available, C process stopped,
  faulty C (503, malformed JSON, wrong audit identity, actual 31-second proxy
  deadline). Base MCP chat, evidence and claims remain usable; Retry works.
- Desktop and 390px layout screenshots inspected; narrow page has no overflow.
- Official submission checker accepts the synthetic claims schema and live URL.
  It reports 3/10 answered categories and a no-confidence warning; this is not
  a real submission or calibrated confidence/savings claim.
- Optional Compose overlay parsed and statically checked for one-way dependency:
  C depends on A; base services do not depend on C. Docker build/run NOT RUN.

The full-flow runner uses actual API, A, C, MCP subprocesses, the production
server and React bundle. It creates two invented jobs plus original findings in
an isolated disk bundle, with its own simulation checksums. Readiness/checksum,
source HTTP, calculators and MCP are real implementations. A simulation-only
entrypoint changes provenance labels to synthetic so results cannot be confused
with organizer telemetry. It does not replace source readiness or audit logic.
No model credentials are passed; no paid model or workload calls are made.

## Reproduce the simulation

Use Python 3.12 with `reviewer/requirements.lock.txt`, Node 22 and local Chrome.
Run from the repository root; choose a new private output directory each time.

```sh
cd dashboard
npm ci --ignore-scripts
npm test
VITE_DATASET_API_ENABLED=true npm run build
cd ..
python -m eval.agent.full_flow --node /path/to/node22 \
  --output-dir reviewer/.private/full-flow-new
```

Actual runtimes here: `/private/tmp/manai-c-isolated/bin/python` and
`/private/tmp/node-v22.14.0-darwin-arm64/bin/node`.
Successful receipt: `reviewer/.private/full-flow-4/receipt.json`. Logs, simulated
source, claims and screenshots stay private/ignored. Runs 1–3 found/diagnosed the
same mobile overflow; run 4 passes the complete flow. The receipt records the
pre-commit parent; the exact tested files were subsequently committed unchanged
as `ff82dbf` and `91edaa7`. Later edits only document the handoff.

## Next 15 minutes on the integration host

1. Check out this branch in an isolated checkout with the verified organizer
   data. Keep the current production deployment available.
2. Build/start the optional reviewer using the supplied overlay:

   ```sh
   REVIEWER_URL=http://reviewer:8002 docker compose \
     -f docker-compose.yml -f reviewer/compose.integration.yml \
     --profile reviewer up -d --build --wait
   ```

   The command assumes shell environment assignment syntax; set `REVIEWER_URL`
   in the host shell first on Windows. Use the team's existing data directory,
   port/project overrides and network configuration. No key is required.
3. Run one real website round: calculate an audit, model a CPU case, ask C,
   open a cited source, download matching claims, stop C and repeat base chat
   and export. Inspect every C FAIL/UNKNOWN rather than requiring an all-clear.
4. Record the real audit ID, exact branch commit and image check. Stop at a
   reviewable result. Merge to main only after the lead authorizes it.

To return to the base flow, stop the optional service with the same Compose
files/project, unset `REVIEWER_URL`, and recreate the dashboard using the base
configuration. Do not require C repair before using A+B.

## Still unverified

Docker/image and full Compose startup/build-failure isolation are unavailable on
this Mac. Organizer-data validation remains pending. Data explorer/cache
preparation was outside this simulation; its read-only production code is
unchanged. Independent human U05 review, live-model quality, workload execution,
automatic rollback and realized savings are not claimed.

Suggested team update:

> We can spend the next 15 minutes connecting C's functionality to the main
> website, since most of the integration is already in place. We'll validate the
> full flow on a separate branch, including failure handling, and stop before
> merging into main.
