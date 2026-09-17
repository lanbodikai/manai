# Frontend/backend API — draft v0.2

Review artifact, not an implemented server. Canonical machine-readable shapes: [OpenAPI](../contracts/openapi.json). [Examples](../contracts/examples/manifest.json) are original synthetic fixtures, not organizer data or measured results. This contract revises the earlier route sketch in CONTRACT.md.

## Architecture and ownership

Browser → React dashboard :3000 → same-origin `/api/*` proxy → team Python service → our analysis functions and provided MantisGrid API/MCP → local data.

Builder A owns team service routes, deterministic calculations, data access, evidence resolution and agent orchestration. Builder B owns the React API client, components, loading/error states and Compose/proxy wiring. Both review schema changes. The official `api` service stays intact on its documented port; team endpoints are not claimed to be MantisGrid product endpoints.

No browser-side provider keys or direct LLM calls. In Compose, use service names rather than host localhost. Internal service port can be 8001; it need not be published to the host. The proposed local judging application has no account/login flow. This is not authorization to expose it publicly on the internet.

## Endpoint list

| Method and route | React client function | Backend function | Used by |
|---|---|---|---|
| GET `/api/health` | `getHealth()` | `get_readiness()` | Startup and readiness banner |
| GET `/api/overview` | `getOverview()` | `load_overview()` | Spending overview |
| GET `/api/recommendations` | `listRecommendations()` | `list_recommendations()` | Supplied judgments plus our pilot candidate |
| POST `/api/audits` | `createAudit(request)` | `create_audit(request)` → select/audit/estimate/build | Scenario form and audited detail |
| GET `/api/audits/{audit_id}` | `getAudit(id)` | `get_audit(id)` | Read immutable result |
| GET `/api/audits/{audit_id}/evidence?limit=25&cursor=...` | `listEvidence(id,page)` | `list_evidence(id,page)` | Paginated supporting records |
| GET `/api/audits/{audit_id}/evidence/{evidence_id}` | `getEvidence(id,ref)` | `resolve_evidence(id,ref)` | Evidence drawer |
| POST `/api/audits/{audit_id}/explanations` | `explainAudit(id,request)` | `explain_audit(id,request)` | MCP-backed question/challenge |
| GET `/api/audits/{audit_id}/claims?team=...` | `exportClaims(id,team)` | `export_claims(id,team)` | Same-scenario claims download |

The only create operation creates a calculation snapshot. No route moves a workload, drains a node, changes official data or executes an operational action. UI buttons say “Model scenario” or “Propose pilot,” not “Apply savings.”

## Audit creation: exact input and output

Input fields: `client_request_id`, `expected_data_fingerprint`, fixed initial `recommendation_id="cpu-placement-pilot"`, and `scenario`.

Scenario contains explicit `recovery_fraction.{low,point,high}`, positive `usd_per_gpu_hour`, `cancelled_policy="exclude"`, `interval_kind="scenario"`, and `assumption_note`. The first cohort is completed zero-compute jobs only; expanding cancellation policy is not a free UI toggle in v0.2. Do not silently introduce a broader cohort.

Example request and full response are in [audit request](../contracts/examples/audit-request.json) and [audit response](../contracts/examples/audit-response.json). They use two invented jobs totaling 30 GPU-hours and explicitly assumed 20/40/60% recovery. The resulting 6/12/18 GPU-hour range is arithmetic, not a benchmark.

Success: HTTP 201 with `Audit`. The record includes `contract_version`, immutable `audit_id`, echoed `client_request_id`, provenance, full scenario, eligibility facts, bounded recovery, reference USD, proposed action, downside, evidence preview/count and limitations.

All fields in the schema's `required` list are mandatory. Empty arrays are valid; unavailable numeric values use explicitly nullable fields only. Required unknown quantities cause an error or a documented excluded cohort, not an invented value. Returning no eligible jobs is a valid audit with zero hours and a clear limitation.

## Identity and consistency

- Generate opaque `audit_id` values. Reuse a prior immutable snapshot only if all semantic inputs, data fingerprint and contract version match. Client request identity is not evidence identity.
- Store snapshots in the team service's bounded in-memory cache for this hackathon; no new database is needed. Set an explicit capacity. Evicted/restarted snapshots return `404 AUDIT_NOT_FOUND`; UI can offer recomputation from preserved scenario input.
- Reject a creation request using a stale expected data fingerprint with `409 DATA_VERSION_MISMATCH`. Existing snapshot evidence/export must not quietly query replacement data; return 409 if original source cannot be resolved.
- Frontend tracks the latest request ID/sequence. Ignore late responses for an old scenario; never display old results under new slider values. AbortController is useful but not sufficient without identity checks.
- Agent answers and claims are tied to audit_id. Changing controls does not silently mutate an existing audit or explanation. Label the last calculated scenario and pending changes.

## Evidence shape

`EvidenceRef`: ID, kind, source ID, label and synthetic flag. `EvidenceDetail`: audit ID, reference, source table/columns, join keys, typed observations, method, caveats and provenance. Full example: [evidence response](../contracts/examples/evidence-response.json).

Evidence lookup must verify membership in the selected audit, not resolve arbitrary filesystem paths. IDs are opaque to React and URL-encoded. Cursor pagination is opaque; default 25, maximum 100; invalid cursor returns 422. Page ordering is stable for the immutable audit. Browser displays only bounded relevant records, never downloads the entire dataset for a chart.

## Explanation shape and limits

Request: `client_request_id`, `question` (1–2,000 characters). Success: HTTP 200 with answer, audit ID, status (`ok` or `insufficient_evidence`), supporting evidence IDs, limitations, tool trace IDs and usage. Usage has nullable model/token/cost fields when not observed; never fill unknown cost with zero. See [example](../contracts/examples/explanation-response.json).

The agent uses supplied MCP tools and canonical audit/evidence functions. It does not recompute or edit official claims. Proposed bound: six tool calls and 30 seconds per answer, configurable. Exhausting a tool-call budget returns a bounded insufficient-evidence answer only if supported content exists; provider outage is a 503, timeout a 504. Questions requesting unsupported causal certainty should return an explicit insufficient-evidence response, not a fabricated story.

Provider credentials live only in backend environment variables. Do not persist full prompts or source rows in public Git. Tool-trace IDs may refer to local private evaluation logs.

## Claims export

HTTP 200 returns official-schema-compatible JSON, not a team response wrapper. Team name query parameter required (1–120 characters). Set `Content-Disposition: attachment; filename="claims.json"` for download. The returned schema contains only our investigated fields: team, recoverable hours/USD with basis/range/interval_kind, explicit cancellation rationale, and notes. No fabricated probability is required. Example: [claims response](../contracts/examples/claims-response.json).

Validate against the pinned official schema as well as our narrower schema. Final submission export must use the chosen final audit; the interactive UI may create many exploratory audits. Identical audit values drive the dashboard, agent and exported claim; React applies display rounding only.

## Error contract

All team errors return JSON `{ "error": { "code", "message", "retryable", "request_id", "details"? } }`. Backend must normalize framework validation failures to this shape. No stack traces, secrets or raw provider response dumps. See [example](../contracts/examples/error-response.json).

| Status | Typical code | Frontend behavior |
|---|---|---|
| 404 | AUDIT_NOT_FOUND / EVIDENCE_NOT_FOUND | Explain missing/expired result; offer recomputation where possible. |
| 409 | DATA_VERSION_MISMATCH | Refresh source readiness; require a new calculation. |
| 422 | INVALID_SCENARIO / INVALID_CURSOR / INVALID_QUESTION | Show field-level message; preserve input. |
| 429 | REQUEST_BUDGET_EXCEEDED | Stop duplicate requests; show retry guidance. |
| 502 | UPSTREAM_RESPONSE_INVALID | Show source-contract failure; do not substitute zeros. |
| 503 | DATA_NOT_READY / AGENT_UNAVAILABLE / UPSTREAM_UNAVAILABLE | Preserve readable results; clearly mark unavailable action. |
| 504 | EXPLANATION_TIMEOUT | Show bounded timeout; existing audit remains intact. |

Health returns 200 for a live service even if data or agent are unready; its body distinguishes readiness. Data-dependent routes return 503 when unavailable. Compose may use a separate internal readiness predicate; do not infer data readiness merely from HTTP 200.

## Contract test additions

- C01: original fixtures validate against team schemas; claims fixture also validates against pinned official schema. This checks shape, not analytical truth.
- C02: rejected stale data fingerprint leaves existing snapshot unchanged; cross-audit evidence lookup cannot leak unrelated records.
- C03: evidence pagination has no duplicate/missing references and respects maximum page size.
- C04: UI ignores superseded scenario responses; download and explanation use the displayed audit ID.
- C05: framework validation and provider failures use the documented error envelope/status; health remains distinguishable from readiness.
- C06: every implemented operation matches OpenAPI requiredness/types; export is raw claims JSON, not wrapped.

Only C01 can be checked before implementation. C02–C06 remain NOT RUN. After API freeze, both builders work against these fixtures. Any breaking route/field change requires a new contract version, fixtures and cross-review.
