# A downside analysis and A–C handoff

Plan clarification v0.10; API v0.3 unchanged. This defines the existing downside work, not a new service or permission to start other assignments. B can continue its current fixture work.

## Smallest useful result

The decision is whether to propose a limited CPU-placement pilot for the audited completed zero-compute cohort. A must answer: **what could go wrong, what do we know, and what would make us stop?** Historical zero GPU activity establishes eligibility under the selected rule; it does not establish that CPU execution succeeds or saves money.

A owns the canonical downside analysis inside each immutable `Audit.downside`. It works without C or a model key. C reads that result and uses MCP evidence to explain or challenge it. B displays A's result even when C is absent. No extra endpoint, risk score, probability model or automatic remediation is needed.

## A's implementation

Implement the existing `assess_downside(cohort, scenario)` using the validated cohort, source context and explicit assumptions. Pass additional internal context as needed; this does not change the public API. Produce these existing fields:

| Field | Minimum useful content |
|---|---|
| `status` | `unmeasured` when intervention harm has not been quantified. `scenario` only for an explicitly assumed, reproducible harm calculation; it never means measured impact. |
| `mechanisms` | Plausible ways this specific action could harm work: CPU execution failure or slowdown; added CPU queue pressure; retry/rollback work. Describe these as risks, not observed outcomes. Include only relevant mechanisms. |
| `assumptions` | State what the source establishes and what it cannot establish: CPU compatibility, acceptable runtime and CPU capacity remain unknown unless separately verified. Identify any assumption used in a harm estimate. |
| `guardrails` | Workload-owner opt-in; small pilot with original placement available; compare task success and runtime against the existing placement; stop and roll back on task failure or an owner-agreed runtime/queue limit. If limits are not agreed, say they must be set before the pilot. |
| `pilot_success_metrics` | Task completion and output validity, runtime relative to original placement, queue delay and actual GPU allocation avoided. These are proposed measurements, not results. |
| `money`, `money_unit` | Default to `null`, `null`. Unknown downside is not zero. A monetary scenario requires explicit inputs, units and a reproducible basis; v0.3 only permits `reference_usd`, not a claim of measured cash loss. |

Keep this concise enough for B's downside tile: main risk, missing evidence, and a practical stop/rollback condition. Detailed assumptions can live in the expanded audit view and methodology.

Use the audit's existing evidence references and detail routes for observed eligibility/source facts. Explicitly mark proposed risks, guardrails and future measurements in the text; do not invent evidence IDs for an unrun pilot. A's methodology records which observations support the recommendation and which intervention questions remain unanswered.

The default hackathon result is qualitative downside with unknown money. Do not invent a harm-dollar formula to fill the tile, subtract unknown harm from reference recovery, or call the displayed range net savings. If a quantified downside needs new inputs or structured evidence links, propose a versioned contract change before implementation; it is not required for this slice.

## A to C: the bridge uses existing routes

1. C receives `audit_id`, `client_request_id` and `question` at its existing `/explanations` route.
2. C fetches `GET /api/audits/{audit_id}` from A. Its context includes the full scenario, eligibility, recovery, `action`, `downside`, limitations and provenance. Do not send only the headline dollars.
3. C resolves relevant references through A's audit-scoped evidence list/detail routes and retrieves relevant official MCP evidence within its existing budget. Verify source identity before using that evidence to support this audit.
4. C returns the existing `Explanation`: same audit/request identity, answer, supporting evidence IDs, limitations, tool traces and usage. A-supported facts use references that resolve within this audit. If new MCP evidence cannot be resolved through that contract, disclose the limitation; do not fabricate an audit citation or mutate the snapshot.

For a downside question, C's short answer should cover: **risk → supporting facts versus assumptions → missing evidence → pilot check and stop condition**. C may identify a weakness in A's argument, but it cannot change canonical downside, recovery or claims. A can investigate a review finding and issue a new audit when justified; the existing audit remains immutable. There is no synchronous C-to-A writeback or approval gate.

Example question: “What if these workloads actually need GPUs?” A provides the observed zero-activity eligibility and unverified compatibility. C explains that distinction, cites available source evidence, and recommends an opt-in compatibility/runtime check with rollback. It must not claim compatibility, a failure probability or dollar loss without evidence.

## B and the required base chatbot

B reads `Audit.downside` directly and labels it as unmeasured or assumed as appropriate. Render null money as “Not quantified,” preserving the risk explanation and guardrails. Keep C's optional commentary separate from the canonical downside. Pending form edits do not relabel an old audit as a new calculation.

A's required `/chat` downside intent uses the same canonical fields and actual MCP retrieval. A's deterministic summary remains available if MCP fails; that summary must not be presented as a successful live chat answer. C failure leaves both the audit and A's independently functioning chat unchanged.

## Focused verification and handoff

Reuse existing evaluation IDs; no additional test framework or separate release gate:

- **T07 / U02:** a scenario change preserves audit identity across displayed downside, recovery and export. Unknown harm remains unknown; claims are not reduced by invented costs.
- **U03 / R02–R04:** null downside money is distinguishable from zero, and missing/hanging/malformed C responses preserve A's downside, evidence and export.
- **M02–M03:** A's downside chat distinguishes measured eligibility from hypothetical intervention effects, uses real MCP evidence and does not fabricate compatibility or citations on tool failure.
- **G01–G05, existing downside/unsupported-claim cases:** C explains or challenges the same audit without changing numbers; unsupported certainty is declined and citations resolve.

These are interpretations of existing tests, not claims that they have run. Development can use the current synthetic audit's unmeasured downside. Real API/MCP acceptance still requires a recorded live run.

A hands B/C the commit and contract version, one audit ID and data fingerprint from the local running service, a resolvable evidence path, the downside assumptions/unknowns and actual checks run. Do not commit organizer-derived responses. C reports any unsupported conclusion back in its explanation or team handoff; A owns corrections. B integrates A's downside immediately and C's review only when available.
