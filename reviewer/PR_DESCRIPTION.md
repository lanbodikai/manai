# Draft: optional Part C evidence validation and guarded model review

Adds a read-only reviewer for immutable A audits. It detects accounting or evidence
disagreements without replacing canonical cohorts, money or claims, and preserves
the existing explanations API. A/B remain independent of C.

## Scope

All C-authored changes are in `reviewer/`, `tests/reviewer/` and `eval/agent/`.
Shared contracts, A/B runtime, official API/MCP, claims and root Compose are not
edited. B owns optional-profile/proxy integration and merges.

The branch starts at main `ce6a44e`. The requested target `codex/integration` was
two pre-existing main documentation commits behind that baseline. Those inherited
commits may appear in the comparison; they are not C-authored. Align the integration
baseline or agree on another target before merging.

## Behavior

- Bounded HTTP audit/evidence retrieval with contract and identity checks.
- Independent arithmetic, coverage, units, duplicate exposure, memory partition
  and optional 0.4 single-job downside checks; pass/fail/unknown outcomes.
- Unchanged official MCP stdio adapter, limited price-book mode and opt-in fixed
  rules/findings/causal plan; unknown source alignment stays unknown.
- Optional one-request model selector. It can select existing facts/checks and
  next-test topics, but cannot generate new numbers, set outcomes or run actions.
- Server-side credentials, isolated dependencies/image, six-operation MCP cap,
  30-second total deadline, bounded concurrency and explicit failure envelopes.

## Verified

- 89 C tests and 5 existing contract tests passed.
- Eight deterministic cases repeated three times: 24/24 passed.
- Same model-adapter route cases passed using an explicitly mocked provider.
- Real official MCP price-book call and final loopback HTTP integration passed.
- Twelve offline checks reproduced the prior pinned two-table trial.
- A/B files unchanged; private receipts/data/secrets excluded from Git and image.

The first cold MCP smoke test timed out under the earlier 8s deadline. Its failure
was retained, startup allowance was increased to 15s within the 30s outer limit,
and the final socket test passed. No hidden runtime retry was added.

## Remaining draft gates

Main's A audit endpoint is still a 404 bootstrap; positive real A→C review and
comparison with A's completed deterministic summary remain untested. Live model
evaluation has 24 NOT RUN entries because provider configuration/spend approval
were unavailable. Full five-file data/MCP finding validation, Docker build and
B's R01–R05 resilience tests remain unrun. No workload replay, tested rollback or
realized savings is claimed. C1/C2 acceptance is not declared complete.

See `reviewer/HANDOFF.md`, `reviewer/AB_IMPROVEMENT_PROPOSALS.md` and
`eval/agent/RESULTS.md` for reproduction and owner actions. AI disclosure: this C
implementation, tests and docs were generated and reviewed using OpenAI Codex.
