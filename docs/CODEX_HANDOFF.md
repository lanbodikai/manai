# Current handoff — common bootstrap

Verified implementation baseline: `7530865eeca4fe87daf91b5cc275af378bd42fb7`. All BASE gates passed. Read BOOTSTRAP_STATUS.md for commands and gate results; BOOTSTRAP_BOUNDARY.md freezes ownership and API v0.3. The published planning branch remains historical planning; use codex/integration for implementation. Workstream prompts in TEAM_START_HERE.md apply with the baseline below, not a placeholder. Do not redo the official import.

## A

Branch codex/analysis-service from the verified baseline. Inherit service/main.py, source.py and mcp_client.py. Implement the documented A1/A2 contract, including canonical audit/evidence/claims and REQUIRED /chat without model keys. Preserve overview/error behavior; run T/D/API/M conditions including D06 range justification. Feasibility probe results are not an independent recovery audit. PR to codex/integration for B review.

## B

Keep codex/product-integration and B0 work. Fetch origin, merge the verified integration baseline into your branch, resolve only owned conflicts, then wire the existing HTTP adapter to A. Replace tools/bootstrap/page with dashboard's :3000 implementation through root Compose. Preserve official api/data mounts and base independence; keep C optional. Run B1/B2 U/P/M/R conditions. Do not overwrite dashboard work with the temporary verification page. PR to codex/integration.

## C

Branch codex/evidence-review-service from the verified baseline. Use contracts/examples for development until A exposes real immutable audits. Implement richer /explanations only; keep own dependencies/image under reviewer profile and coordinate root Compose changes with B. Featherless configuration is optional and local; no key was required or tested by bootstrap. Complete C1/C2 and G evaluation before enabling. PR to codex/integration; do not block A+B.

Every handoff records actual commit, versions, checks and remaining work. No force pushes, final default-branch change or event submission is part of this baseline task.
