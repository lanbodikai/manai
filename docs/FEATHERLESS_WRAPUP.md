# Featherless simulation review — four-minute wrap-up

Integrated newest main `a6ee9f5` and simulation `af33cc5` on
`codex/featherless-portfolio-review`. Resolve final commit using git log.
Winston explicitly excluded C; its temporary integration was reverted. No C
source, image, service or dependency is included in the resulting tree.

The A-owned `POST /api/portfolio-simulations/{id}/review` follows a frozen result
back to assigned action contributions, configuration and up to 100 scoped job
records. Real official MCP corroborates the reference price. Featherless selects
allowed fact IDs; deterministic code renders amounts and preserves unknown checks.
It does not certify unmeasured effectiveness, causality, cash savings or unseen
records. Source examples stay in local responses and ignored receipts. No key
enters the browser or image. Without a key the endpoint provides an explicitly
labeled deterministic review; existing base chat remains separate.

The dedicated chat page offers Cost simulation review and Base pilot assistant.
Overview/Decisions/Model share the existing simulation. Newest main's removal of
the decision banner and standalone downside card is preserved.

## Recorded checks

- `node node_modules/typescript/bin/tsc --noEmit`: PASS.
- `node node_modules/vitest/vitest.mjs run`: 64/64 PASS.
- `docker exec manai-featherless-check-analysis-1 python -m unittest discover -s tests/analysis -q`: 30/30 PASS, including broken-total and incomplete-coverage review checks.
- Corresponding `tests/base_chat` command: 4/4 PASS.
- Isolated Compose build and verified local dataset preparation: PASS, C absent.
- `node eval/integration/featherless.cjs http://127.0.0.1:13121`: PASS, actual
  Featherless `Qwen/Qwen3-30B-A3B-Instruct-2507`, actual MCP, 27 checks with zero
  FAIL. Coverage is explicitly partial: 100/8145 scoped records. UNKNOWN checks
  remain visible. Base MCP chat still answers; desktop/390px layout checks pass.
- Secret file is ignored. No source-derived records or credentials staged.

First live attempt exposed route ordering behind the generic fallback. Fixed
ordering and reran successfully. Final service and proxy files were copied into
the isolated containers and restarted; a clean image rebuild of those last two
fixes remains pending. Full new-provider fault matrix and independent review
were not completed within the four-minute cutoff. No workloads were executed.

## Run and ownership

Provision normal data, then set the key in an ignored `.env.featherless` file
with FEATHERLESS_API_KEY and REVIEWER_MODEL. Do not print the file or Compose
configuration. The optional model is configured in A:

```text
docker compose --env-file .env.featherless -f docker-compose.yml -f service/compose.featherless.yml up -d --build --wait
```

Default Compose remains usable without a key. The isolated checked website is
http://127.0.0.1:13121/#ask; normal production was not replaced. Publication and
main merge are not performed. Next owner: lead/A+B for final clean rebuild,
provider-failure checks and review/publication. C stays excluded.
