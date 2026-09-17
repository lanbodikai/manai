# Full snapshot review coverage — 2026-09-17

Local patch: `service/simulation_review.py`,
`tests/analysis/test_simulation_review.py`, and
`eval/analysis/verify_review_coverage.py`. No publication or runtime restart.
Concurrent dashboard/release edits were left untouched.

The review now checks all scoped frozen records, unique job IDs and per-job
arithmetic. Each action reconciles assigned job count, GPU-hours, gross,
intervention, net and failure amounts with its summary, including fixed costs.
The existing response shape and three-example display limit are preserved.
Unmeasured effectiveness and source-proof checks remain UNKNOWN.

Validation: the patched module and test were copied to `/tmp` inside
`manai-featherless-check-analysis-1`; importlib loaded the patched module under
`service.simulation_review` in separate Python processes. Running services were
not modified. unittest discovery ran the three coverage regressions plus the
existing 30 analysis tests: 33/33 PASS. The regression covers corrupted record
105, duplicate IDs, nonzero fixed overhead, partial coverage and action scoping.
These are arithmetic/grounding checks in the T01/T05/G01/G04 categories, not a
rerun of every acceptance gate with those IDs.

`verify_review_coverage.py` ran through the ASGI routes with actual local data,
actual official MCP and no model key: PASS, 8145/8145 records, 36 checks, zero
failed checks, eight action reconciliations, three examples returned, saved
simulation unchanged. No Featherless call or workload trial was performed.
`git diff --check`: PASS.

After the shared runtime owner incorporates this patch, reproduce with:

```sh
python -m unittest discover -s tests/analysis -v
python -m eval.analysis.verify_review_coverage
```

Next owner: the active release session, to include this local patch in its
commit/build and restart analysis in coordination with its current deployment.
Full snapshot coverage does not independently certify original telemetry,
causality, intervention effectiveness or cash savings.

## Running service update — 2026-09-17

Rebuilt/recreated only `manai-featherless-check-analysis-1` from this workspace's
local coverage patch; dashboard remains at http://127.0.0.1:13121. Container healthy,
dashboard HTTP 200. Patch is uncommitted; HEAD observed after deployment: e4a2ba2
(concurrent dashboard commit; not an immutable identifier for the deployed patch).

Commands completed in the rebuilt container:
- `python -m unittest discover -s tests/analysis -q`: 32 tests PASS (supersedes the earlier reported count for this run).
- `python -m unittest discover -s tests/base_chat -q`: 4 tests PASS.
- `python -m eval.analysis.verify_review_coverage`: PASS through in-process ASGI with actual MCP, no model key; 8145/8145 records, 36 checks, three displayed examples, unchanged snapshot.
- `git diff --check`: PASS.

The model-enabled browser smoke test was blocked before execution by automatic
approval review because it sends local simulation facts/checks to Featherless.
Live HTTP model review remains unverified after restart; user approval for that
external payload is the remaining step. No port-3000 release services changed.

## Live model diagnostic after user-reported 502

User authorized sending simulation facts/checks to Featherless for diagnosis.
Confirmed two prior HTTP 502 responses in service logs; their exact cause was not
recorded by the original catch-all handler. Added safe stage/exception-class
logging and stage-specific errors, without logging payloads or credentials, and
rebuilt/recreated the analysis service again.

`node eval/integration/featherless.cjs http://127.0.0.1:13121`: PASS with actual
Featherless Qwen/Qwen3-30B-A3B-Instruct-2507 and MCP, 36 checks, 8145/8145 coverage,
zero failures; desktop/mobile checks and base MCP chat passed. Private receipt:
`private-eval/featherless-1789681297024`.

`node tmp/review-live-diagnostic.cjs`: three further live requests PASS:
untested-assumptions and downside questions each checked 8145/8145 records;
CPU-placement trace checked 378/378. All returned HTTP 200 with Featherless and
zero failed checks. Original intermittent failure was not reproduced; these
passes establish current functionality, not a demonstrated root-cause fix.

## Exact user question reproduced and fixed

Reproduced HTTP 502 using the user's full eight-action review question via
`node tmp/review-exact-question.cjs`. Safe diagnostics identified the model fact
selection count check. The application rejected selections outside 1–16 IDs.
Changed selection handling to validate every returned ID against the allowed
facts and reject duplicates/empty lists before limiting selected facts to 16.
Mandatory method/assumption facts and all checks remain rendered as before.
No arbitrary model prose or invented facts are accepted.

Rebuilt/recreated the running analysis service. The same exact-question browser
command now returns HTTP 200 with actual Featherless, 8145/8145 record coverage,
and zero failed checks. `python -m unittest discover -s tests/analysis -q` passed
34 tests, including overflow selection and invalid IDs beyond the display limit.
`git diff --check` passed. Changes remain local/uncommitted. This fixes the
reproduced count-limit failure; provider availability is not guaranteed.

## Compact review presentation deployed

Updated `dashboard/src/components/SimulationReview.tsx`: all scoped actions are
shown from the matching immutable simulation, independent of model-selected
facts; three detailed mechanisms and five screening estimates are labeled;
accounting success, unresolved evidence, MCP price_book scope and zero-cost
assumptions are explicit. Raw selected facts remain expandable.

TypeScript check PASS; frontend tests 64/64 PASS. Rebuilt only the dashboard
using its active `work/featherless-review` checkout with the updated component.
`node eval/integration/featherless.cjs http://127.0.0.1:13121` PASS: all eight table
rows, 3/5 mechanism labels, named price_book tool, live Featherless/MCP, desktop
and 390px mobile layout, and base MCP chat. Receipt:
`private-eval/featherless-1789681793542`; desktop screenshot visually inspected.
Verified demo query: "Trace this cost estimate back to its evidence."
Observed result: 27 passed, zero failed, nine unknown, 8145/8145 records.
This is accounting verification, not measured savings. Local changes remain
uncommitted/unpublished; next owner is release coordination for repository
publication. Running dashboard is port 13121, not the older port-3000 release.

## Minimal release on main

Implementation commit: 8cd6a1a (built and run from isolated release checkout).
Root claims.json exported from the canonical 0/0/1 scenario and passes official
schema validation with HTTP 200 at :3000. Only aggregate claims are published;
source/derived tables and private receipts remain excluded. The validator warns
about absent confidence; no empirical confidence is invented.

`docker compose -p manai-release up -d --build --wait`: production build passed;
initial startup encountered a subnet collision with another local stack. Restart
with MANAI_SUBNET=10.254.188.0/24 and the existing provisioned MANAI_DATA_DIR passed:
API, analysis and dashboard healthy, dataset preparation completed. This verifies
an isolated clean source checkout using existing data, not a fresh VM/data download.
Final image tests: analysis 34/34 PASS; base chat 4/4 PASS.

The legacy browser.cjs failed on an obsolete Low recovery label. The current
`node eval/integration/release.cjs http://127.0.0.1:3000` equivalent ran via tmp
using the installed Playwright library and passed: real MCP with no key, 8145/8145
records, zero failures, all eight rows and 3/5 mechanism labels, desktop/mobile,
and base MCP chat. Local receipt: private-eval/base-release-1789682214585.

README includes the one-line `docker compose up --build` startup command after
organizer data setup. Default branch was codex/planning when checked; GitHub denied
this account's request to set main as default (HTTP 404). Repository owner must
select main in settings. Release publication targets main as requested.
