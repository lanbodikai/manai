# What goes in Git and Docker

## Commit

Application source, original synthetic test fixtures, API contracts, package/dependency lockfiles, Dockerfiles/Compose, executable verification scripts, source notices, provenance manifest and concise test-result summaries. Only `data/README.md` and `data/checksums.txt` are tracked under data/.

## Ignore

`.env` and `.env.*` (except placeholder `.env.example`), PEM/key files, raw/prepped/generated data and downloaded ZIP/Parquet files, private evaluation logs, local screenshots/artifacts, process logs, Python environments/caches, node_modules, dist, test coverage/browser reports and TypeScript build caches. Rules are in root `.gitignore` and apply to every workstream. Do not use `git add -f` to bypass them.

`.dockerignore` also excludes data, credentials, Git metadata, private logs and build artifacts from build context. Data is mounted read-only into runtime services; never COPY it into an image. No base service receives model-provider environment variables.

## Featherless (C only)

Optional local file: `.env.featherless`, with FEATHERLESS_API_KEY and FEATHERLESS_BASE_URL=https://api.featherless.ai/v1. This file is plaintext locally, ignored by Git and excluded from image contexts. Do not print it or run a configuration dump containing its values. Each teammate supplies their own authorized credentials. C must explicitly wire this file only to the optional reviewer after implementation; it is not required or loaded by this bootstrap. No Featherless API call was made by the bootstrap.

## Verify before publishing

`git check-ignore .env.featherless data/raw/dcgm.csv data/prepped/jobs.parquet private-eval/run.json` should identify ignored paths. `git ls-files data` should list only README.md and checksums.txt. Inspect staged paths and the diff for secrets, dataset records and notebook outputs. Ignore rules alone do not remove a file that was already tracked.

The imported example notebook is upstream starter content, not our analytical result; keep future local source-data outputs uncommitted. The source-notice restrictions and required claims/report format still apply at final submission.
