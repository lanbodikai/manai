# Official starter import manifest — proposed

Import only after execution is activated. Pin official commit `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`; inspect later upstream changes before adopting them. Do not blindly pull main during the build.

## Layout

Copy the contents needed from official `track-2/` to our repository root so relative paths and judging assumptions hold. Do not nest two complete projects or replace our planning documents. Record actual imported paths and hashes in `UPSTREAM_PROVENANCE.md` when import occurs.

| Official path | Our destination | Use / treatment |
|---|---|---|
| track-2/api/ | api/ | Preserve provided API and its Dockerfile.local; new team logic goes elsewhere. |
| track-2/scripts/prep_data.py, checksum_data.py, validate_submission.py | scripts/ | Preserve preprocessing/checks; keep official validator clearly distinct from team tests. |
| track-2/bin/ + SHA256SUMS | bin/ | Required platform-specific findings generator; verify hashes before use. |
| track-2/requirements*.txt | same | Keep pinned preprocessing/runtime environment. Avoid installing Linux-only packages into host Windows Python. |
| track-2/docker-compose.yml | docker-compose.yml | Keep api/prep/generate; add dashboard :3000 and team service. Notebook can become optional profile. |
| track-2/Makefile | Makefile | Keep prep/generate/check-data/validate; document equivalent Docker commands for Windows. |
| track-2/mcp_layer/ | mcp_layer/ | Preserve package name and API tools; do not rename to mcp. |
| track-2/starter/mgai_client.py | starter/mgai_client.py | Use as reference/fetch helper; cache results, preserve IDs. |
| track-2/starter/claims.schema.json | starter/claims.schema.json | Keep location required by official validator. |
| track-2/starter/claims.example.json | starter/claims.example.json | Mark invented example; never use its values as findings. |
| track-2/starter/notebook.ipynb + Dockerfile | starter/ | Optional local exploratory notebook; not the final dashboard. |
| track-2/data/README.md + checksums.txt | data/README.md + checksums.txt | Track only these instructions/manifests; exclude downloaded/generated data. |
| track-2/docs/ | docs/upstream/ | Preserve original track docs without overwriting our docs. Record that original relative links refer to official layout. |
| root ATTRIBUTION.md, LICENSE, PARTICIPANT_AGREEMENT.md | docs/upstream/ | Preserve notices, link from top-level attribution; review license scope before selecting our own license. |

Our original paths: `analysis/`, `agent/`, `service/`, `dashboard/`, `contracts/`, `tests/`, `eval/`, `docs/workstreams/`, `REPORT.md`, generated root `claims.json` when justified.

## First successful vertical path

Raw data → official prep → official generator → canonical-data check → API → one supplied overview → our audit response → dashboard detail.

Run checksums before interpreting the corpus. Preserve API endpoint configuration: within Compose, use service DNS (`api:8000`), not host localhost. Agent integration may launch the supplied MCP server in-process/stdio as documented; do not rebuild the protocol.

## What to exclude

Track 1 and all external starter stacks from the earlier briefing; `.git` from upstream; raw/derived datasets; secrets; saved notebook outputs containing source rows. Do not ship a duplicate dashboard/compose project. A container built locally is not evidence the public submission starts cleanly.

## Import completion gate

Provenance recorded; expected source files present; correct notices retained; data ignored with two manifest exceptions; generator hashes verified; Compose config valid; canonical five-file check passes; API returns one real response. Record results, not just commands.

## Explicit import checklist

Mark these only after performing them. Reviewed does not mean imported or executed.

- [x] Official Track 2 docs and relevant starter code inspected at the pinned commit.
- [x] Agreement, attribution/license paths, schema and validator identified.
- [ ] Activation of starter import recorded in DECISIONS.md.
- [ ] Import Track 2 code paths from the manifest without copying upstream .git or replacing our planning files.
- [ ] Retain PARTICIPANT_AGREEMENT.md, LICENSE and ATTRIBUTION.md; link notices from the root README/attribution.
- [ ] Preserve source notices verbatim and document any team modifications; do not imply that storing an agreement accepts it for the user.
- [ ] Record upstream commit and imported file hashes in UPSTREAM_PROVENANCE.md.
- [ ] Preserve claims schema and official validator path relationship.
- [ ] Preserve data README/checksums while confirming raw/prepped/generated paths are ignored.
- [ ] Verify generator hashes before execution; use the documented Docker path.
- [ ] Download data only after activation; run prep, generate and canonical-data check.
- [ ] Add the dashboard/service to a single root Compose project; keep the official API service.
- [ ] Test API readiness and a complete fixture-backed page; record actual outcomes.
- [ ] Freeze shared contract/fixtures and baseline commit before all three builders branch.

Copying official files supplies infrastructure and obligations; it does not complete our contribution or its evaluation.

## Mandatory base MCP inclusion

Import the official `mcp_layer/` with API dependencies for A/B's minimum chatbot, independent of C. Preserve its name to avoid shadowing the `mcp` package. Pin the tested MCP client/server dependencies during bootstrap and build them into the base image. Use the documented stdio transport; no external model provider is needed for a template-based client. C's optional model/framework dependencies belong only in its own image.

## Team handoff update — v0.8

User authorized publishing the plan/setup branch. See [TEAM_START_HERE.md](../TEAM_START_HERE.md) for bootstrap execution assignments, current phase, exact branch strategy and A/B/C ownership. No runtime bootstrap has yet been performed. Historical activation questions must not override an explicit subsequent session assignment.
