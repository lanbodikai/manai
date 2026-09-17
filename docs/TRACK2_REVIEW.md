# Track 2 documentation cross-check — plan v0.7

Reviewed September 17 against the local official snapshot `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`: README, docs/submission.md, api.md, data.md, rules.md, traps.md, data/README.md, mcp_layer/README.md, Makefile, Compose, claims schema and validator. Also re-read the public main-branch README and submission guide; the relevant requirements agree. This is a documentation review, not a runtime or organizer acceptance result.

## What remains correct

- Required product: three tiles, actionable recommendation with owner, downside, evidence drilldown; root docker-compose.yml, claims.json and REPORT.md; dashboard :3000.
- One deeply investigated recommendation is acceptable: submission.md explicitly permits omitted uninvestigated claims. No need to investigate every node, detector or optional extension.
- Our exact cohort matches rules::gpu-not-needed: COMPLETED, sm_util_avg == 0, sm_util_max == 0, gpu_hours > 1; impact kind unused_capacity. Do not confuse it with gpu-never-computed (non-completed, >10 hours).
- A/B/C division is our engineering choice, not an organizer requirement. C can be optional while A+B retain the required working package.

## Corrections and limits

1. **MCP wording differs.** The repo describes chat as an example; the slide explicitly requests a chatbot/agent. Keep real MCP chat in the base to cover the stronger slide requirement. A template-based chatbot is our proposed interpretation, not an organizer-approved design. Label its actual capabilities and show real tool calls. C supplies richer model-backed review when ready.
2. **CPU placement is already in the rules.** Do not claim that recommendation as a novel discovery. Our contribution is reproducible accounting, explicit conversion assumptions, downside, source comparison and understandable evidence. If recomputation confirms the source, report confirmation; do not invent a correction.
3. **A scenario range is not demonstrated calibration.** Final claims need a defensible basis for each bound and the point. Record evidence versus judgment, eligibility ceiling, adoption/compatibility assumptions and why the chosen values follow. If positive recovery has no empirical lower bound, explicitly consider zero; do not use an arbitrary positive floor. Never call a sensitivity interval a statistical confidence interval. The schema explicitly accepts scenario intervals and says recoverable_gpu_hours has no single correct answer: its reasoning and interval honesty are assessed. Other selected claims may be compared with undisclosed ground truth. Our scenario approach is valid when its assumptions are defensible; it does not require inventing a statistical estimator.
4. **Bootstrap checks actual interfaces.** api.md says the running official `/docs` is authoritative. Check endpoint payloads and MCP tool schemas before freezing adapters; our `/api/*` contract is separate. Use metadata.job_id/node joins, not IDs parsed from prose.
5. **One-command means after data provisioning.** Judges first regenerate the five canonical files, then run unattended `docker compose up`. No manual model login or second MCP-start command. Default startup must not require C. Preserve the official api service and ./data mount.
6. **Checksums are semantic for Parquet.** Use the supplied checker rather than raw file hashes. On Windows without make: `docker compose run --rm prep`, `docker compose run --rm generate`, then `docker compose run --rm prep python scripts/checksum_data.py`.
7. **Submission must reach the public default branch.** A local branch/commit or draft PR is not the submission. Once publishing is authorized, B must verify the final default branch, English README AI-use disclosure, required artifacts, event form and working four-minute demo. Bug fixes only after the stated deadline, no new features.
8. **Schema/prose conflict persists.** Prose calls all except team optional; supplied schema requires recoverable_gpu_hours. Include a defensible researched range plus team and validate it. Omit unrelated claims. The official validator checks shape and HTTP response, not analytical correctness.

## Changes to the split gate

Before branching: import/notices/provenance complete; real five-file data check passes; one official API query and actual MCP call succeed; candidate fields and records inspected; a labeled fixture renders through the frontend/backend with success and failure paths; API v0.3 adapters/fixtures agreed; owners and time cutoffs recorded; common baseline committed.

Do not implement the full audit or reviewer before splitting. B can scaffold fixtures while A resolves data issues, but that is partial parallel progress and cannot be called a passed real-data gate. C provider configuration never blocks the base gate.

## Evidence links

- [Track brief](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/README.md)
- [Submission](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/submission.md)
- [Rules](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/rules.md)
- [API](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/docs/api.md)
- [Data setup](https://github.com/MantisGridAI/hackathon-2026-official/blob/314cca0bba49e1bb137aa9094d1dac4cdf7e4490/track-2/data/README.md)
