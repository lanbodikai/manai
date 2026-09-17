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
