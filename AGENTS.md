# Working instructions for manai

## Current mode

PLANNING. The user requested several discussion rounds before implementation. Complete planning edits and local versioning; do not import the starter, download data, install dependencies, build features, dispatch builder sessions, or publish until the user activates the corresponding phase. Do not infer activation from a proposed roadmap.

User decisions in this conversation override this file. Keep this mode current when implementation is authorized.

## Read order

Read README.md, docs/DECISIONS.md, docs/QUESTIONS.md and docs/ROADMAP.md. For assigned implementation, also read docs/CONTRACT.md, docs/EVALUATION.md and your workstream file. Check git status and preserve unrelated work.

## Research and product boundaries

- Track 2 only; one deeply verified recommendation inside a complete overview/evidence/downside/agent flow.
- Preserve problem → claim → experiment → falsification. Do not replace the question with whatever the data makes easy.
- Distinguish measured facts, organizer judgments, our assumptions, scenario estimates and synthetic records in data and UI.
- No numeric savings claim until recomputed from the actual local source. Never copy example claim values.
- GPU allocation, SM-weighted activity, recoverable capacity, reference dollar value and cash savings are different quantities.
- Deduplicate at the physical quantity's grain. Never sum overlapping findings or mixed impact scopes/kinds.
- Keep cancellation policy explicit. Do not infer hardware fault from failure count alone. Do not rank individual researchers as wasteful.
- Raw/prepared/generated organizer data stay local and out of Git. Commit only original synthetic test fixtures with no source-data-derived records. Check organizer terms before publishing derived evaluation records; prefer executable evaluation code and aggregate summaries consistent with the submission rules.
- Keep keys in environment variables. Do not print or commit them.

## Engineering

- Reuse the pinned official API, preprocessing and generator. Preserve file structure needed by their tools. Log imported provenance and modifications.
- Use deterministic code for cohorts, joins, money, intervals and claims. An LLM may select evidence tools and explain verified outputs; it must not become the numeric source of truth.
- A failure or missing evidence is an explicit UI state, never a fabricated successful response. A mock is visibly synthetic and cannot satisfy real-data acceptance.
- Scope ownership is in the two workstream files. Propose shared-contract changes first, update its version and fixture, and obtain agreement from the other builder before dependent edits.
- Do not add dependencies/architecture for speculative later features. No model training, generalized autonomous remediation or broad paper reproduction in the initial scope.

## Tests, evaluation and completion

Use docs/EVALUATION.md IDs. Claim only checks actually run. Separate arithmetic correctness, source-data validity, agent grounding, interface usability and operational effect. A unit test does not demonstrate real savings.

A completion report must state commit, implemented scope, test/eval IDs and outcomes, commands run, open limitations and next owner. Do not call a workstream complete merely because its files exist.

## Branches and handoffs

Use `codex/analysis-agent` and `codex/product-integration` after a common baseline exists. Prefer separate worktrees for concurrent sessions. Builder B owns integration files; Builder A owns computation and agent files. Neither silently edits the other's paths.

Local commits are appropriate for authorized work. Push/create PR only when the active task authorizes publishing. Open a draft PR after the first coherent working slice; mark ready after the workstream completion contract passes. Merge only after cross-review, shared checks and lead authorization; never force-push a shared branch or bypass a failed material check.

Use new commits for plan revisions; preserve earlier reasoning in CHANGELOG.md. Do not overwrite an approved decision with an assumption. No subagents or separate tasks are started merely by reading these handoff documents.
