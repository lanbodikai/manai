# A/B integration handoff — 2026-09-17

**Superseding publication update:** the validated baseline is now on main at runtime merge `610f89d` (PR #7). Winston explicitly deferred cross-review/U05 for this baseline merge. PR #4 now targets main for B’s later work. C has since published v0.4 fixes at `75137bb`; the old C findings below are historical, not a verdict on that new revision. Use [the current B/C handoff](MAIN_BASELINE_HANDOFF.md); the earlier branch state and review record below are retained.

Current release candidate: PR [#4](https://github.com/lanbodikai/manai/pull/4), `codex/product-integration` into `codex/integration`. A PR [#2](https://github.com/lanbodikai/manai/pull/2) is merged at integration `db6f418`. Main remains `5a8d995`; this is not a final-main merge announcement. Use [the acceptance record](../eval/integration/RESULTS.md) for exact tested commits and commands.

## Branches before and after

Before this execution (simplified; merge edges omitted):

```text
shared foundation ee529ee / main ce6a44e
  main 5a8d995                 B PR #1 history already merged
  codex/integration ee529ee    lagging main
  codex/analysis-service adfcd88       PR #2 -> integration
  codex/product-integration bde7e7b    PR #4 -> main
  codex/evidence-review-service d4fa017 PR #3 -> integration
```

After integration work:

```text
main 5a8d995
  codex/integration db6f418    existing B history + reviewed A adfcd88
    codex/product-integration
      5166afd                 v0.4 UI / CPU / production packaging
      a6bb59e                 preserves concurrent B commits through e24c78a
      4a260ae                 production Data explorer / Decisions / verification
      2dbc7fc                 preserves B dialog update 788b5ad; read-only action guard
      PR #4 -> integration    pending independent cross-review / U05
  C d4fa017, PR #3            separately checked, not merged or enabled

After remaining gates: PR #4 -> integration -> reviewed final main release
```

## To A's author

Your tested `adfcd88` is included in shared integration `db6f418`. This session reproduced the packaged tests, real-source checks, CPU cases and required MCP classes before merging #2. There is no need to reimplement the calculator or chat. Review PR #4's v0.4 client, CPU field/display mapping, unknown/signed values, observed allocation versus scheduler duration, and immutable claim exports. Confirm the 0/0/1 default means zero empirical recovery with a physical upper ceiling, not a forecast.

B-owned dataset and decision routes reuse the existing read-only snapshot code. They are **not new A contract obligations**. Multi-fix optimization is deferred. A remains the canonical source for audited single-job CPU calculations and claims.

The old local `manai-bootstrap` API was stopped while moving required ports to `manai-release`. The obsolete :13010 preview and A's old :18001 development container can therefore lose their upstream. Use the current :3000 same-origin API for review; when developing A independently, configure its official API URL explicitly or restore its own non-conflicting stack. Do not infer an A arithmetic failure from the stale preview's 503.

## To B's author

Your CFO planner, task table, GPU/machine/findings navigation and commits through `788b5ad` are preserved. Fetch and merge/fast-forward from `origin/codex/product-integration`; do not reset or force-push over the integration commits. The branch contains A's v0.4 history, so a later merge into integration will preserve it.

Production serves :3000 using Node 22, with `dataset-prep` preparing a checksum-verified private snapshot. `tools/dataset-handler.ts` is shared by production and the Vite local-preview plugin. Production enables the read-only HTTP adapter; the multi-fix button is disabled with an explicit label. The separate cohort planner remains hypothetical and does not change A's claims. The explorer's initial search debounce no longer resets quick pagination.

Please cross-check the complete user journey, desktop/narrow layouts and run U05 with a teammate: within 30 seconds identify proposed action, owner, recovery range and main risk, then open a supporting record. Record successes/failures; automated browser checks do not satisfy this gate. Review the read-only page integration and distinctions between the two CPU planners before approving #4.

## C's separate follow-up

At `d4fa017`, container build and 89 tests pass. Real A→C no-pilot and all three CPU-mode requests return `insufficient_evidence`, use actual MCP, preserve claims and reject a missing audit. This is partial compatibility, not enhanced reviewer acceptance:

- `reviewer/validation.py` rejects schema-valid `aggregate` references and nullable aggregate observation columns.
- Its expected GPU-hour/count units differ from A's actual `GPU-hours` / `GPUs` labels.
- The first 100 evidence references can contain no jobs; the CPU baseline must be fetched explicitly rather than silently excluded by the cap.
- Version selection must keep genuine v0.3 and v0.4 schemas distinct after integration promotes the active schema.

C's author owns those fixes and G01–G05 with a real provider if enabled. Do not merge or enable C on the strength of unit tests or 200/insufficient_evidence responses alone. Failure stubs under `eval/integration` test base isolation and are not a deployable reviewer.

## Lead release checklist

1. Obtain independent cross-review and record U05. Address material findings; rerun affected checks.
2. Merge #4 into integration, then review/merge the concrete integration-to-main candidate without squashing away unrelated history.
3. Resolve publication of generated root claims: the supplied submission instructions require them while broadly prohibiting derived-data redistribution. Local export and validation are implemented; no generated source records or claims were published by this session.
4. Confirm the actual A/B/C AI disclosure and change the repository default branch from `codex/planning` to the approved `main`. The current account lacks admin permission for that setting.

The base needs no model key. C is separately not ready. No CPU workload was moved and no operational savings were demonstrated.
