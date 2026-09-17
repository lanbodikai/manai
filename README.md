# manai — evidence-led GPU decisions

Track 2: audit a completed zero-GPU-compute cohort for a bounded CPU-placement pilot. Our contribution is the accounting, assumptions, downside and evidence story; CPU placement is already suggested upstream. Real intervention savings remain unproven.

**This feature branch combines the current A service and B dashboard with a Pilot & Recovery simulation panel.** It preserves the existing Decisions planner, audits, evidence and claims. C remains optional. See [feature handoff](docs/PILOT_RECOVERY_HANDOFF.md) and [actual verification results](eval/pilot_recovery/RESULTS.md); this is not a claim of final submission readiness.

## Pilot & Recovery

Open **Pilot & Recovery** in the sidebar. Load historical candidates through A, save one baseline, define a CPU proposal and correctness criterion, set runtime/spending limits, and simulate success, failure with recovery, or recovery unavailable. Unknown measurements stay unknown; losses stay negative. A calculates all financial results. No workload is run or controlled.

The panel uses the adopted audit API v0.4 plus the additive [Pilot & Recovery contract v0.1](contracts/pilot-recovery.openapi.json). Historical telemetry has no verified checkpoint; failure recovery assumes a full original GPU rerun. An unavailable recovery pauses the simulation and leaves final cost/benefit unknown. Saved alternatives remain visible while editing/retrying and can be downloaded; session history is memory-only and clears on reload.

Net benefit = original reference cost − total trial and recovery reference cost. These are assumed reference values, not actual bills or achieved savings. Limits are enforced in the simulator only. C has no role in the calculation or readiness of this panel.

## Setup

Requires Git and Docker Desktop/Engine with Linux containers. No model key or host Python/Node installation is required for this bootstrap.

```sh
git clone --branch codex/pilot-recovery https://github.com/lanbodikai/manai.git
cd manai
```

Windows PowerShell: run `powershell -ExecutionPolicy Bypass -File tools/bootstrap/setup.ps1`. It verifies generator hashes, downloads missing raw data, prepares/generates the five files and checks their canonical contents. It does not modify machine execution policy. Read [data setup](data/README.md) for equivalent non-Windows steps and source terms.

After data provisioning, the judged startup shape is one unattended command:

```sh
docker compose up
```

Open http://localhost:3000 for B's React dashboard and http://localhost:8000/docs for the official API. The dashboard proxies `/api/` to A. Only api, analysis and dashboard start by default; no C image, model key or reviewer process is required. Notebook retains its optional profile. Stop this checkout with `docker compose down` (no global cleanup commands).

Docker is required for the documented default startup. This feature was developed with Node 22.14 and Python 3.12 for local checks; the exact container and real-data gate status is recorded in the feature results. Local HTTP development uses A on :8001 and `cd dashboard && npm ci && npm run dev`; a missing A/data service is shown as an error, never a synthetic fallback. B's separate local dataset/Decisions preview API remains a dev-only capability; this feature does not silently advertise it as a production backend route.

If another local checkout already uses our subnet, set MANAI_SUBNET to a verified unused subnet before starting (PowerShell example: `$env:MANAI_SUBNET='10.254.198.0/24'`). Ports 3000/8000 must be free; stop only your previous manai stack when moving checkouts.

## Reproduce bootstrap checks

```sh
docker compose run --rm prep python scripts/checksum_data.py
docker compose exec -T analysis python -m unittest discover -s tests/bootstrap -v
docker compose exec -T analysis python -m tools.bootstrap.cohort_check
docker compose exec -T analysis python -m tools.bootstrap.mcp_probe
docker compose exec -T analysis python -m tools.bootstrap.verify_live
```

The MCP probe makes actual local tool calls; it is not a model-backed chatbot. The claims schema check uses an explicitly synthetic example and does not generate submission claims.

## Team split

- **A:** analysis, audit/evidence/claims APIs, pilot simulation calculations and REQUIRED minimum MCP chatbot.
- **B:** dashboard, Pilot & Recovery display, routing, Compose, report/demo and integration. Existing B screens are preserved.
- **C:** optional richer model-backed reviewer, isolated from base startup. Featherless belongs only here.

Read [current handoffs](docs/CODEX_HANDOFF.md), [team guide](TEAM_START_HERE.md), [B early-work contract](docs/workstreams/B_PREBOOTSTRAP.md), [adopted API v0.4](docs/API_SPEC.md), [evaluation conditions](docs/EVALUATION.md) and [Git/secrets policy](docs/GIT_AND_SECRETS.md). The Pilot & Recovery feature does not establish final workstream or submission readiness.

## Sources and disclosure

Imported official commit: `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`; [manifest and modifications](UPSTREAM_PROVENANCE.md). Preserve [license](docs/upstream/LICENSE), [attribution](docs/upstream/ATTRIBUTION.md) and [participant agreement](docs/upstream/PARTICIPANT_AGREEMENT.md). Source/prepared/generated data are local and excluded from Git and image contexts.

AI assistance: OpenAI Codex (GPT-6, as identified in this session) generated planning documents, the bootstrap service/probe/page and verification code, and performed recorded tool-based checks. The team supplied product choices and scope constraints. Official API/data tooling and MCP server are organizer-provided. No provider model has yet powered the product. Update this disclosure with actual A/B/C models/frameworks and human modifications before final submission.

AI disclosure for this feature: OpenAI Codex generated the additive simulator, API, panel, tests, packaging integration and documentation, and used parallel code review. Existing A/B authorship and organizer attribution are retained. No model/provider powers the simulation, and no provider key was used.
