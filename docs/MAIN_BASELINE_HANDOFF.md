# Main baseline and next B/C work

Winston authorized this sequence and explicitly deferred independent cross-review and the timed U05 usability check for the baseline merge. Both remain pending; this is not final submission acceptance.

- Frozen tested snapshot: `5c4fd8376380b95ff09560ab7a688a5306ed5072` (`codex/ab-validated`).
- Integration merge: `982b407`, [PR #6](https://github.com/lanbodikai/manai/pull/6).
- Main runtime merge: `610f89d8d2b4b9c1aa07b7e2c12087ec4849adeb`, [PR #7](https://github.com/lanbodikai/manai/pull/7). Its complete tree equals the frozen snapshot. Later publication notes change documentation only.
- Automated evidence: [results and commands](../eval/integration/RESULTS.md). Production remains http://localhost:3000 on the integration host; API health reports v0.4 / real / ready. Browser checks passed before publication; merges did not change the tested code.

```text
validated A+B 5c4fd83
  integration 982b407
    main 610f89d (+ publication notes)
      B follow-up: 7a3b201 + main merge 2692216 -> PR #4 -> main
      C: 75137bb -> merge current main -> compatibility checks -> PR #3
      Pilot & Recovery: PR #5 remains a separate, unmerged feature
```

## B author

PR #4 now contains only the newer B follow-up relative to main. `2692216` merges the main baseline into your existing branch without changing the `7a3b201` file tree. Fetch and fast-forward if possible; merge normally if you have local work. Never force-push shared history. The newer CFO/spending/pilot/downside changes are preserved but were not covered by this integration run's earlier acceptance results. Run affected unit/browser and real production checks on the new revision, keep it a separate PR, and record the still-deferred human check.

Preserve production `dataset-prep`, the read-only dataset routes, A v0.4 CPU inputs/results, actual MCP chat and canonical audit/claim identity. Newer frontend estimates remain labeled hypotheses/scenarios. The deferred multi-fix action must not imply execution or fabricated success.

## C author: start with compatibility against main

Your current published head was `75137bb` when this handoff was prepared. Your updated handoff reports fixes for active v0.4, aggregate observations, live units and targeted pilot baseline retrieval. The old `d4fa017` integration findings are historical; this session has not revalidated the newer C against real main data.

1. Fetch and merge `origin/main` into `codex/evidence-review-service`, preserving history and the working A/B production packaging. Record the exact main and C commits. Retain only C-owned changes when resolving conflicts.
2. Build/run the current C image in isolation. Use main's actual A service and official data, with deterministic C and no provider key. On the integration host, the A-compatible same-origin base URL is `http://127.0.0.1:3000`; C's HTTP client appends `/api/...`. That address is local to this host, not remotely accessible from the C author's machine. Container clients require an explicitly configured reachable A URL. Old :13010/:18001 previews are not the new baseline.
3. Check no-pilot plus the eight real CPU cases (success, failure/rerun, extra validation, loss, unknown price, unknown queue, unknown pricing boundary, earlier completion). Use the supplied `eval.agent.live_review` runner for existing audit IDs; retain detailed outputs privately. Independently inspect its FAIL/UNKNOWN counts: exit0 alone verifies transport/identity/citation invariants, not zero semantic failures.
4. Verify scoped citations, unchanged A audits and claims, actual MCP traces, no false aggregate/unit failures, selected-job retrieval despite pagination, and honest incomplete cohort coverage. Unknown lineage is not automatically a failure; explain it rather than fabricating proof.
5. Re-run base resilience with the optional reviewer path before proposing enablement. Default startup, overview, scenarios, evidence, MCP chat and exports must continue working without C. Live-model evaluation remains separate and deferred; no paid provider calls are authorized here.

Useful C command after obtaining a real main audit and starting C:

```sh
python -m eval.agent.live_review --analysis-url http://127.0.0.1:3000 --reviewer-url http://127.0.0.1:18002 --audit-id AUDIT_ID --output reviewer/.private/main-compatibility.json
```

The output path must be new. Never commit real source records or review receipts. Keep PR #3 draft until its actual remaining gates pass; do not merge C merely because the A+B baseline is now on main.

## Lead

Main publication is complete. Human review/U05, generated root-claims publication disposition, full team AI disclosure and the repository default-branch setting remain open. The configured default was `codex/planning`; changing it requires owner/admin access. Root `claims.json` remains a local export. No newer B, Pilot & Recovery, C or workload-execution feature was included in this baseline merge.
