> **Next compatibility target:** main advanced during this acceptance pass to
> `a6ee9f58c8b4556198d4e78cc5802e81f10f1ff3`, discovered by the final fetch.
> Thirteen dashboard/runtime-test files changed, including App, ChatPanel and
> chat styling. This pass certifies the pinned PR #8 runtime only. The new main
> has not been merged or tested with C; preserve this deployment and use a
> subsequent integration pass to sync and verify the changed browser workflow.

# Real-data Docker integration — PASS

2026-09-17. This supersedes the earlier missing-Docker/access blocker below.
The user authorized installing Docker on this Mac and then explicitly authorized
creating the missing organizer-generated files in a separate private data copy.
Original data and committed checksums were not changed.

## Exact revisions and deployment

- Branch: `codex/c-main-integration`; validation commit
  `d32a84f24928c0c68ea064a22f69167268824e7c`.
- Images built from candidate runtime
  `91c704d2a7d9e68bf661d453d5b55f0571e07aeb`. The validation commit adds only
  the real-data browser acceptance runner; runtime source is unchanged.
- Tested A+B main: `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9` (PR #8).
  Fresh fetch confirmed no newer main revision before startup.
- Contract `0.4`; Docker Desktop `4.91.0`, engine `29.8.0`, Linux ARM64.
- Compose project `manai-c-smoke`, website http://127.0.0.1:13012,
  API http://127.0.0.1:18081, subnet `10.254.194.0/24`.
- Optional reviewer profile: deterministic, `price_only`; no provider credentials.
  Dashboard proxy uses `REVIEWER_URL=http://reviewer:8002`.
- Private dataset: `reviewer/.private/real-host-pass/data`. Both prepared tables
  and all three official generated files match committed `data/checksums.txt`.
  All running data mounts are read-only. The original data was copied, not edited.
- Deployment acceptance started at 20:52:44 UTC after installation/build/data
  preparation; final browser round completed at 20:55:53 UTC, within 15 minutes.

## Completed acceptance

All five images built: API, analysis, dashboard, dataset-prep and reviewer.
Dataset preparation completed successfully; all four long-running services are
healthy. C's standalone image health check passed as uid 10001 with networking
unavailable, deterministic mode and Contract 0.4. Container regression: **99/99**;
deterministic fixture evaluation: **24/24** (eight cases, three repetitions).
Those fixtures remain separate from the real-data results below.

The production browser UI completed baseline audit → claims download → failed
CPU trial/full GPU rerun → advanced review → cited evidence drawer → claims export.
The baseline was selected from actual eligible jobs with positive count/duration.
Inputs were explicitly hypothetical: 1 vCPU, 0.5 hours, $0.10/vCPU-hour, no added
queue, 0.5-hour assumed cap; inclusion of baseline host costs was an assumption.
Added CPU cost is **$0.05**, net reference benefit **−$0.05**, added completion time
**0.5 hours**. The full GPU rerun retains recorded GPU allocation once. Cohort
recovery and its claims are unchanged by the single-job scenario.

- Final baseline audit: `49a2fc1e7bf6423b935cab2bffc9e23c`.
- Final CPU audit: `6733c7acbc864e14b474e2bcf1b10505`.
- Source fingerprint: `62fa722b0909528e0c78fa5300064593d0090c0c0dc44012d11effb4fcbf0e2b`.
- Actual A→C live review ran in a one-off reviewer container through B's
  explanations proxy, with evaluation code mounted read-only and private receipts.
- All eight live-review gates pass: 0.4, request/audit identity, resolving scoped
  citations, unchanged audit/claims, live MCP, no provider, check-count reporting.
- Independent review: **253 PASS, 0 FAIL, 5 UNKNOWN**, `insufficient_evidence`.
  Unknown categories: cohort hours, cohort job count, evidence coverage, MCP source
  identity and memory partition membership. None were suppressed.
- Coverage: 100 details of 1,045 audit references; 99 listed records plus the
  selected baseline outside that sample. Whole-cohort totals remain uncertified.
- Stopped only isolated C: website showed unavailable/503; actual base MCP chat,
  evidence drawer, audit retrieval and claims download continued and were unchanged.
  Restarting C and clicking the visible retry action succeeded.
- Desktop and 390px screenshots inspected: review text wraps without horizontal
  overflow. The long review/citation list remains a usability limitation; no
  human usability study was performed.

The first acceptance runner incorrectly expected recorded GPU allocation to equal
GPU count × scheduler duration. Real telemetry differs slightly; A's documented
accounting correctly preserves recorded H independently of scheduler T. The test
was corrected to compare rerun allocation with recorded H. The failed attempt was
retained privately; no application calculation was altered or failure suppressed.
A screenshot rerun then positioned the answer text at the top for visual review.

## Reproduce on this checkout

The private override remains at `reviewer/.private/real-host-pass/host-smoke.yml`.
It replaces published ports with loopback 13012/18081 and subnet with
10.254.194.0/24. Do not run the commands against another project or production.
Use an unused receipt directory because live review refuses to overwrite receipts.

```sh
export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH
export MANAI_DATA_DIR="$PWD/reviewer/.private/real-host-pass/data"
export REVIEWER_URL=http://reviewer:8002

docker run --rm --network none   --mount type=bind,src="$MANAI_DATA_DIR",dst=/app/data,readonly   manai-c-smoke-api python scripts/checksum_data.py

docker compose -p manai-c-smoke -f docker-compose.yml   -f reviewer/compose.integration.yml   -f reviewer/.private/real-host-pass/host-smoke.yml   --profile reviewer up -d --no-build --wait --wait-timeout 360

mkdir -p reviewer/.private/real-host-pass/new-receipt
/private/tmp/node-v22.14.0-darwin-arm64/bin/node   eval/agent/real_host_browser.cjs http://127.0.0.1:13012   "$PWD/reviewer/.private/real-host-pass/new-receipt"
```

The browser runner requires dashboard dev dependencies and installed Chrome.
It includes the one-off `eval.agent.live_review` call, stops/restarts only the
named isolated reviewer and leaves C stopped if any acceptance assertion fails.
It creates hypothetical audits but never executes a workload. Reproducible
standalone live request: POST `/api/audits/{audit_id}/explanations` at the website
origin with `{"client_request_id":"handoff-review","question":"Review cost, evidence coverage and recovery assumptions."}`.
Audits are in memory and disappear if A restarts.

Private receipts and screenshots: `reviewer/.private/real-host-pass/verified/`.
Build/startup logs, image IDs, mount inspection, generator verification,
container regression/evaluation and initial attempts are in the parent directory.
Reviewer image: `sha256:cb8a4b38f73d8fe3329a0c3940971427961c15610d42b2ed4e6541de6556ca64`.
All image IDs are recorded in private `images.json`.

## Stop and handoff

The healthy isolated deployment remains available for review. Main, production
and PR #3 were not modified. No public API/schema/type change was required.
The branch is ready for team review, not automatically approved for a main merge.

B-owned checks for any future deployment: explicitly enable optional reviewer
profile, set explanations proxy target, preserve the existing bounded browser
request timeout, and keep base results/chat/evidence/export usable when C fails.
Those paths passed on pinned PR #8 here; rerun against any newer main/runtime and
its actual deployment configuration before deciding merge readiness.

Pending/out of scope: production deployment, merge into main, exhaustive faults,
Docker build-failure testing, human usability review, model evaluation, workload
execution, enforced trial stops, verified rollback and proven cash savings.

---

## Historical blocked attempt (superseded)

# Real-data host pass: blocked at access preflight

Attempt started 2026-09-17 20:35:13 UTC. This is a blocked execution receipt,
not a real-data acceptance result. The approved plan allows a blocked handoff;
there is no reason to spend the remaining time installing local infrastructure.

## Verified

- Candidate: `codex/c-main-integration` at `003ad777bb5ac275368bfc9e4a491b5fed29e11c`.
- Current main after network fetch: `a7087ebc1a6d08e10f43eb0b32e4c3ff432df5b9`.
- Main has no changes since the pinned PR #8 baseline; the revision gate passes.
- The existing isolated candidate checkout was clean at the start.
- Private overlay prepared for project `manai-c-smoke`, website `127.0.0.1:13012`,
  API `127.0.0.1:18081`, subnet `10.254.194.0/24`.
- Static YAML assertions pass for those settings, optional reviewer profile,
  read-only data mounts and no base dependency on C. This is not a Compose run.

## Blocker

This task executes on the local Mac, not on the integration machine. Docker CLI,
Docker.app and the Docker socket are absent. No DOCKER_HOST or SSH configuration
is available, and the tools expose no connected remote shell for that machine.
The local data directory lacks generated resources, edges and findings. The
repository's documented localhost:3000 address belongs to the separate
integration host and cannot be used from this Mac to reach it.

The user selected the integration host, but its connection and verified dataset
path were not supplied. Those are the missing execution inputs; do not request
passwords or private keys in chat. No infrastructure installation was attempted.

## Not run

Remote Docker/data verification; remote port/subnet collision check; image build;
Compose startup; real audit creation; real CPU trial scenario; browser review;
real scoped citations/claims comparison; stop/restart/retry of C. No real audit
IDs or real-data screenshots exist for this attempt. Prior synthetic simulation
results are unchanged and must not be promoted to real-data acceptance.

No deployment was started and no C service was enabled by this pass. The remote
host's current service state is unverified. Main, production and PR #3 were not
modified. Only this handoff is added to the integration branch.

## Resume on the actual host

1. Supply an existing authorized remote connection or run this task directly on
   the Docker/data machine, with the verified dataset's absolute path.
2. Start a fresh 15-minute window and recheck main against PR #8. Stop if runtime
   changed; do not automatically sync a newer base during this acceptance pass.
3. Use a separate clean checkout of candidate `003ad77` (or a later documented
   documentation-only descendant). Record its exact SHA. Confirm the specified
   ports/subnet/project are unused on that host before creating resources.
4. Recreate the private overlay below on that host. Combine base Compose,
   reviewer/compose.integration.yml and this overlay, always passing project
   `manai-c-smoke`. Set MANAI_DATA_DIR to the verified dataset and REVIEWER_URL
   to http://reviewer:8002; enable only the optional reviewer profile. Do not
   pass provider credentials. Stop startup work at minute 7 if unhealthy.
5. Complete the approved real browser round with one failed CPU trial: one vCPU,
   0.5 hours, USD 0.10/vCPU-hour, zero extra queue, cap 0.5 hours. Mark all CPU
   and baseline-host-cost-boundary inputs as assumptions. Expected added CPU
   reference cost is USD 0.05; verify no duplicate original GPU charge.
6. Use eval.agent.live_review with the dashboard explanations URL and direct
   internal reviewer health. In a one-off reviewer container, mount eval code
   read-only and a private receipt directory writable. Inspect every FAIL and
   UNKNOWN, then stop only C, verify base chat/evidence/export, restart C and retry.
7. Save the real receipt and stop at minute 15. Do not merge main or modify PR #3.

Private overlay (after the two existing Compose files):

```yaml
services:
  api:
    ports: !override ["127.0.0.1:18081:8000"]
  dashboard:
    ports: !override ["127.0.0.1:13012:3000"]
networks:
  default:
    ipam:
      config: !override
        - subnet: 10.254.194.0/24
```

Local preparation files, ignored by Git:
`reviewer/.private/real-host-pass/host-smoke.yml` and
`reviewer/.private/real-host-pass/preflight.json`.
