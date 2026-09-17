# Working instructions for manai

## Current mode

CONNECTED PORTFOLIO — LOCAL IMPLEMENTATION. Winston authorized the shared Overview/Decisions/Model cost simulation on `codex/portfolio-simulation` from `605f4cc`, then explicitly expanded it to all eight options. Three detailed mechanisms and five assumption-only screening estimates must remain distinguished. Keep canonical v0.4 claims and manual pilot separate. Private evaluation and local commits are authorized; publication, merge, workload execution and C integration are not. See docs/PORTFOLIO_SIMULATION.md. Earlier narrower/deferred multi-fix wording is superseded only for this local simulation.

BOUNDED HARDWARE SCENARIO — LOCAL FOLLOW-UP. Winston authorized a reproducible branch from merged PR #8/main `a7087eb` to place the bounded CPU hardware simulation in Decisions → Model and show its historical target contribution. Branch `codex/cpu-hardware-product` owns this narrow A/B follow-up. Preserve the manual pilot and active v0.4 claims; no C integration, workloads, publication or merge in this task. See docs/CPU_HARDWARE_HANDOFF.md and eval/analysis/HARDWARE_PRODUCT_RESULTS.md. Earlier publication authorizations below do not publish this new feature.

MAIN BASELINE MERGED. Winston approved publishing validated A+B snapshot 5c4fd83 through integration to main (runtime merge 610f89d), explicitly deferring independent cross-review and U05. Those checks remain pending, not passed. New B revisions target main separately. C must first merge/read the new main and validate compatibility; C remains disabled by default. See docs/MAIN_BASELINE_HANDOFF.md. This status supersedes earlier candidate-only wording below.

A+B INTEGRATION CANDIDATE. This session is authorized to finish and publish A/B integration, including the existing read-only Data explorer and Decisions in the production dashboard. Preserve B history and keep multi-fix backend modeling deferred. C stays disabled. See docs/AB_INTEGRATION_HANDOFF.md and eval/integration/RESULTS.md for current checks and remaining release gates. Earlier narrower assignments below are historical.

INTEGRATION EXECUTION AUTHORIZED. Winston approved this session to review/publish the shared A+B baseline, finish B's v0.4 CPU-pilot UI and Compose integration, validate C separately, and prepare the final release for review. Preserve B's explorer history; defer the proposed multi-fix modeling backend. A is merged into integration at db6f418. Final main publication remains subject to the concrete release review. This authorization supersedes historical no-implementation/no-merge notes within this bounded scope.

WORKSTREAM A ACTIVE in this isolated checkout, explicitly assigned by Winston. Implement and publish A1 then A2 on codex/analysis-service targeting codex/integration; never merge or push to main. BASE gates passed. Winston confirmed B agreement to exact ce6a44e proposal; A accepted and recorded adoption in PR #2 before implementation. Active API is now v0.4 on this branch; B must regenerate its strict client before switching. Preserve B/C ownership. See eval/analysis/RESULTS.md for actual checks, not historical readiness wording.

CPU-PILOT HANDOFF UPDATE. User authorized API/fixtures and A/B handoff, plus direct publication of the validated base update to main. The v0.4 proposal is staged under contracts/proposals/v0.4 for coordinated A/B adoption; active v0.3 remains unchanged. No calculator or other workstream implementation is authorized by merely reading this update. See docs/VERIFIER_HANDOFF_REVIEW.md.

COMMON BASE VERIFIED. Worktree: manai-bootstrap, branch codex/integration. BASE-01 through BASE-07 passed on implementation baseline 7530865. The bootstrap assignment stops here; subsequent A/B/C implementation requires the corresponding session assignment. Preserve B's dashboard files. Read docs/BOOTSTRAP_STATUS.md for actual gate results and docs/BOOTSTRAP_BOUNDARY.md for ownership. Historical planning activation questions do not override this authorization.

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
