# manai — A+B cost simulation and evidence review

The current release adds eight-action cost simulation and A-owned Featherless
evidence review. C is excluded. Three detailed mechanisms and five assumption-only
screening estimates remain distinct; no realized savings or workload compatibility
is established. See [release checks and model setup](docs/FEATHERLESS_WRAPUP.md).
Default startup works without a model key. To enable Featherless, use the optional
`service/compose.featherless.yml` overlay with an ignored local environment file.

Track 2: a bounded CPU-placement pilot with traceable evidence, explicit assumptions and downside. The running base uses API v0.4. It does not establish CPU compatibility or realized savings.

**Validated A+B is merged to main.** Independent cross-review and timed usability were explicitly deferred by Winston for this baseline merge; final submission readiness is not claimed. See [the new-main B/C handoff](docs/MAIN_BASELINE_HANDOFF.md). See [actual checks](eval/integration/RESULTS.md), [A/B author handoff](docs/AB_INTEGRATION_HANDOFF.md) and [report/demo](REPORT.md). C remains disabled; multi-fix modeling remains deferred.

## Run

Use Git and Docker Desktop/Engine with Linux containers. No host Node/Python or model key is required to run the product. Check out `main` for the validated baseline. New B revisions are reviewed separately against main.

Provision the organizer data using [data setup](data/README.md). On Windows, `powershell -ExecutionPolicy Bypass -File tools/bootstrap/setup.ps1` downloads/prepares/generates and verifies it. This is data provisioning; app startup is one command:

```sh
docker compose up --build
```

Open http://localhost:3000 for the dashboard and http://localhost:8000/docs for the official API. Default services are api, analysis/MCP and dashboard, plus a one-shot dataset-prep job. That job uses the pinned official preprocessing and verifies the source checksums before publishing a private SQLite snapshot into a named volume. The dashboard reads that volume read-only. No source records are baked into the image or browser bundle. Recreate dataset-prep and dashboard when changing source data.

For an existing data directory set `MANAI_DATA_DIR` to its absolute path. `MANAI_SUBNET` can select an unused local subnet; ports 3000/8000 must be free. Stop only your previous manai stack when changing checkouts. `docker compose down` stops this checkout without deleting its data volume.

## What works

- Overview, immutable recovery scenarios, one-job CPU cost/delay cases, evidence and claims come from A v0.4.
- Data explorer and Decisions share B's read-only dataset routes with its local preview. These are B-owned `preview-1` / `optimization-preview-1` interfaces, separate from A's audit contract. Selections show deduplicated observed exposure; they do not approve or execute changes.
- Overview, Decisions and Model share an immutable eight-action simulation with deduplicated assigned contributions and per-job evidence. Workload execution stays disabled. Simulation exports are separate from audited v0.4 claims.
- The required template chatbot makes real official MCP calls without a model key. A deterministic summary is separately labeled.
- C is excluded. Optional Featherless review runs in A, selects existing evidence facts and preserves explicit unknowns. Its failure leaves calculations and canonical claims unchanged; base MCP chat requires no key.

A 503 on Overview means an actual data/upstream failure, not normal operation. Inspect `docker compose ps` and the api/analysis logs. A dataset preparation error appears in `docker compose logs dataset-prep`; fix the missing or mismatched source files before restarting. Obsolete development URLs such as :13010 may point at a different stack. Use :3000 for this candidate.

## Verification and claims

```sh
docker compose exec -T analysis python -m unittest discover -s tests/analysis -v
docker compose exec -T analysis python -m unittest discover -s tests/base_chat -v
docker compose exec -T analysis python -m eval.analysis.verify_live
```

Frontend checks and real browser commands are in [integration results](eval/integration/RESULTS.md). Local export: `python eval/integration/export_final.py --url http://localhost:3000`. This writes ignored root `claims.json` and a private matching audit using the documented default 0/0/1 fractions. Do not copy example claims. Generated-claims publication and default-branch selection remain explicit release tasks; no final submission is claimed.

## Sources and disclosure

Imported official commit: `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`; [manifest and modifications](UPSTREAM_PROVENANCE.md). Preserve [license](docs/upstream/LICENSE), [attribution](docs/upstream/ATTRIBUTION.md) and [participant agreement](docs/upstream/PARTICIPANT_AGREEMENT.md). Source/prepared/generated data are local and excluded from Git and image contexts.

WE USED CODEX GPT6 Astra

AI assistance: OpenAI Codex with GPT-6 Astra assisted with planning, frontend and integration code, production packaging, tests and handoff documentation, and performed the recorded tool-based checks. The team supplied product choices and scope constraints. Official API/data tooling and MCP server are organizer-provided. The optional live review uses Featherless-hosted `Qwen/Qwen3-30B-A3B-Instruct-2507` to select existing fact IDs; deterministic code calculates and renders numeric claims. No C service is included. Full team disclosure remains a final submission task.
