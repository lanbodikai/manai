# Working instructions for manai

## Current mode

TEAM HANDOFF. The user authorized committing and publishing the plan/setup branch for teammates. Publish `codex/planning` now. Runtime bootstrap has not run. TEAM_START_HERE.md provides explicit bootstrap and A/B/C assignment prompts: when the team lead supplies one to a session, execute that assignment and update its phase status; do not re-ask historical planning questions already resolved. Merely reading the roadmap does not launch work or other agents.

B0 is explicitly authorized before the shared split gate: see docs/workstreams/B_PREBOOTSTRAP.md. A session assigned B0 may implement and publish the isolated fixture-driven frontend now, without waiting for bootstrap. Its file boundaries and mock-versus-live acceptance limits take precedence over earlier B wait instructions.

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
- Scope ownership is in the three workstream files. Propose shared-contract changes first, update its version and fixture, and obtain agreement from the other builder before dependent edits.
- Do not add dependencies/architecture for speculative later features. No model training, generalized autonomous remediation or broad paper reproduction in the initial scope.

## Tests, evaluation and completion

Use docs/EVALUATION.md IDs. Claim only checks actually run. Separate arithmetic correctness, source-data validity, agent grounding, interface usability and operational effect. A unit test does not demonstrate real savings.

A completion report must state commit, implemented scope, test/eval IDs and outcomes, commands run, open limitations and next owner. Do not call a workstream complete merely because its files exist.

## Branches and handoffs

Use `codex/analysis-service`, `codex/product-integration` and `codex/evidence-review-service` after a common baseline exists. Prefer separate worktrees for concurrent sessions. B owns product/integration files; A owns computation/audit service; A also owns the minimal MCP chatbot; C owns the enhanced explanation service. Do not silently edit another owner's paths.

Local commits are appropriate for authorized work. Push/create PR only when the active task authorizes publishing. Open a draft PR after the first coherent working slice; mark ready after the workstream completion contract passes. Merge only after cross-review, shared checks and lead authorization; never force-push a shared branch or bypass a failed material check.

Use new commits for plan revisions; preserve earlier reasoning in CHANGELOG.md. Do not overwrite an approved decision with an assumption. No subagents or separate tasks are started merely by reading these handoff documents.

## Base product independence — explicit user requirement

A+B must operate without C. Default `docker compose up` builds/starts only the base services and required official dependencies. Put C behind an optional Compose `reviewer` profile; do not add it to the base build, readiness checks or startup dependency chain. Enable it separately with one documented profile command when it is validated.

Every base function works without a model key: overview, scenario calculation, downside, evidence drill-down, deterministic evidence summary, minimal live MCP chatbot and claims export. Label the deterministic summary as such; never call it a live agent answer. A+C failure must not be conflated: if A/data fail, show an actual data failure; if C fails, preserve all existing results.

C errors/timeouts/malformed outputs affect only the optional explanation panel. Do not block page load or claim export waiting for C. Execute R01–R05 resilience tests before final base completion; M01–M04 are required for the base MCP chatbot; G01–G05 are required before marking C complete/enabled. Report slide-aligned base readiness and enhanced reviewer readiness separately.

The deck explicitly requests a chatbot or agent using MCP. Keep a small template-based chatbot in A/B with real MCP calls and no model key. Static text, API-only calls or synthetic fixtures cannot satisfy this gate. C remains optional; the required MCP tool runtime is part of the base. See docs/REQUIREMENTS.md.
