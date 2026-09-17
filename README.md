# manai — verified common-base bootstrap

Track 2: audit a completed zero-GPU-compute cohort for a bounded CPU-placement pilot. Our contribution is the accounting, assumptions, downside and evidence story; CPU placement is already suggested upstream. Real intervention savings remain unproven.

**This branch is the common foundation, not a finished hackathon submission.** The page on :3000 is a labeled integration probe. See [actual gate results](docs/BOOTSTRAP_STATUS.md) and [frozen boundaries](docs/BOOTSTRAP_BOUNDARY.md).

## Setup

Requires Git and Docker Desktop/Engine with Linux containers. No model key or host Python/Node installation is required for this bootstrap.

```sh
git clone --branch codex/integration https://github.com/lanbodikai/manai.git
cd manai
```

Windows PowerShell: run `powershell -ExecutionPolicy Bypass -File tools/bootstrap/setup.ps1`. It verifies generator hashes, downloads missing raw data, prepares/generates the five files and checks their canonical contents. It does not modify machine execution policy. Read [data setup](data/README.md) for equivalent non-Windows steps and source terms.

After data provisioning, the judged startup shape is one unattended command:

```sh
docker compose up
```

Open http://localhost:3000 for the temporary page and http://localhost:8000/docs for the official API. Only api, analysis and the temporary dashboard start by default. Notebook uses the optional notebook profile; reviewer does not exist yet. Stop this checkout with `docker compose down` (no global cleanup commands).

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

- **A:** analysis, audit/evidence/claims APIs and REQUIRED minimum MCP chatbot; inherit service skeleton and MCP utility.
- **B:** dashboard, routing, Compose, report/demo and integration. Keep your existing B0 branch; merge the verified baseline and replace the temporary page.
- **C:** optional richer model-backed reviewer, isolated from base startup. Featherless belongs only here.

Read [current handoffs](docs/CODEX_HANDOFF.md), [team guide](TEAM_START_HERE.md), [B early-work contract](docs/workstreams/B_PREBOOTSTRAP.md), [API v0.3](docs/API_SPEC.md), [evaluation conditions](docs/EVALUATION.md) and [Git/secrets policy](docs/GIT_AND_SECRETS.md). No full workstream is completed by this bootstrap.

## Sources and disclosure

Imported official commit: `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`; [manifest and modifications](UPSTREAM_PROVENANCE.md). Preserve [license](docs/upstream/LICENSE), [attribution](docs/upstream/ATTRIBUTION.md) and [participant agreement](docs/upstream/PARTICIPANT_AGREEMENT.md). Source/prepared/generated data are local and excluded from Git and image contexts.

AI assistance: OpenAI Codex (GPT-6, as identified in this session) generated planning documents, the bootstrap service/probe/page and verification code, and performed recorded tool-based checks. The team supplied product choices and scope constraints. Official API/data tooling and MCP server are organizer-provided. No provider model has yet powered the product. Update this disclosure with actual A/B/C models/frameworks and human modifications before final submission.
