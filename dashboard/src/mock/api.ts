// MANAI_MOCK_ONLY: this module must never enter the live build.
import { createDemoDatasetApi } from "./datasets";
import { createMockOptimizationApi } from "./optimization";
import auditFixture from "../../../contracts/examples/audit-response.json";
import evidenceFixture from "../../../contracts/examples/evidence-response.json";
import claimsFixture from "../../../contracts/examples/claims-response.json";
import type { Audit, DashboardApi, Schemas, Overview } from "../api/types";
import { ApiError, parse, validateAuditRequest } from "../api/validation";

export type Fault =
  | "none"
  | "empty"
  | "source-unavailable"
  | "not-found"
  | "conflict"
  | "invalid"
  | "reviewer-unavailable"
  | "reviewer-timeout"
  | "reviewer-malformed";
export const initialAudit = parse("Audit", auditFixture);
export const overviewFixture: Overview = parse("Overview", {
  provenance: initialAudit.provenance,
  price_book_version: "synthetic-price-v1",
  usd_per_gpu_hour: 2.5,
  allocated_gpu_hours: 600,
  job_count: 20,
  outcomes: [
    { outcome: "Finished", gpu_hours: 300, reference_usd: 750 },
    { outcome: "Cancelled", gpu_hours: 120, reference_usd: 300 },
    { outcome: "Timed out", gpu_hours: 90, reference_usd: 225 },
    { outcome: "Failed", gpu_hours: 60, reference_usd: 150 },
    { outcome: "Other", gpu_hours: 30, reference_usd: 75 },
  ],
  warnings: [
    "Original invented example, not the MIT sample.",
    "Cancelled work is not automatically waste.",
  ],
});
export const recommendationFixture = parse("Recommendations", {
  provenance: initialAudit.provenance,
  items: [
    {
      id: "cpu-placement-pilot",
      source_recommendation_id: null,
      title: initialAudit.action.title,
      origin: "team",
      kind: "synthetic",
      audit_available: true,
      finding_ids: [],
      caveats: ["CPU compatibility and actual savings remain unverified."],
    },
  ],
});

export function createMockApi(
  options: {
    fault?: Fault;
    delay?: number;
    auditDelay?: (request: Schemas["AuditRequest"]) => number;
  } = {},
): DashboardApi {
  const snapshots = new Map<string, Audit>();
  let counter = 0;
  const fault = options.fault ?? "none";
  const wait = (ms = options.delay ?? 250) =>
    new Promise((resolve) => setTimeout(resolve, ms));
  function get(id: string): Audit {
    const audit = snapshots.get(id);
    if (!audit)
      throw new ApiError(
        "AUDIT_NOT_FOUND",
        "This calculation has expired or does not exist. Model it again.",
        404,
      );
    return structuredClone(audit);
  }
  function evidence(id: string, ref: string) {
    const audit = get(id);
    const member = audit.evidence_preview.find((e) => e.id === ref);
    if (!member)
      throw new ApiError(
        "EVIDENCE_NOT_FOUND",
        "This source is not part of the selected calculation.",
        404,
      );
    const record = structuredClone(evidenceFixture);
    return parse("EvidenceDetail", {
      ...record,
      audit_id: id,
      evidence: member,
      join_keys: { id_job: member.source_id },
      observations: record.observations.map((o) => ({
        ...o,
        value: o.unit === "gpu_hours" ? (ref === "job:J1" ? 10 : 20) : o.value,
      })),
    });
  }
  async function answer(
    id: string,
    request: Schemas["ExplanationRequest"],
    advanced: boolean,
  ) {
    const started = performance.now();
    parse("ExplanationRequest", request);
    await wait();
    const audit = get(id);
    if (advanced && fault === "reviewer-unavailable")
      throw new ApiError(
        "AGENT_UNAVAILABLE",
        "Advanced reviewer is unavailable. Base chat still works.",
        503,
        true,
      );
    if (advanced && fault === "reviewer-timeout")
      throw new ApiError(
        "EXPLANATION_TIMEOUT",
        "Advanced reviewer timed out. Your calculation is unchanged.",
        504,
        true,
      );
    if (advanced && fault === "reviewer-malformed")
      throw new ApiError(
        "UPSTREAM_RESPONSE_INVALID",
        "Advanced reviewer returned an invalid response.",
        502,
      );
    const supported =
      /why|support|eligible|eligibility|assum|risk|wrong|downside|recover/i.test(
        request.question,
      );
    return parse("Explanation", {
      audit_id: id,
      client_request_id: request.client_request_id,
      status: supported ? "ok" : "insufficient_evidence",
      answer: supported
        ? `Synthetic example: ${audit.eligibility.eligible_gpu_hours} eligible GPU-hours support a scenario of ${audit.recovery.gpu_hours.low}–${audit.recovery.gpu_hours.high} recoverable GPU-hours. These jobs completed with no recorded GPU compute. CPU-only compatibility has not been tested; a pilot could fail or run more slowly. The recovery fractions are assumptions, not observed savings.`
        : "This demo only covers pilot support, eligibility, recovery assumptions and downside. It cannot establish CPU compatibility or unsupported causal claims.",
      supporting_evidence_ids: supported
        ? audit.evidence_preview.map((x) => x.id)
        : [],
      limitations: ["Mock answer. No MCP tools or model have run."],
      tool_trace_ids: [],
      usage: {
        tool_calls: 0,
        input_tokens: null,
        output_tokens: null,
        estimated_usd: null,
        latency_ms: performance.now() - started,
        model: null,
        provider: null,
      },
    });
  }
  return {
    datasets: createDemoDatasetApi(options.delay),
    optimization: createMockOptimizationApi(options.delay),
    async getHealth() {
      await wait();
      return parse("Health", {
        service: "ok",
        contract_version: "0.3",
        data_status: "ready",
        data_fingerprint: "synthetic-fixture-v1",
        agent_status: "unconfigured",
        mode: "synthetic_fixture",
      });
    },
    async getOverview() {
      await wait();
      return structuredClone(overviewFixture);
    },
    async listRecommendations() {
      await wait();
      return structuredClone(recommendationFixture);
    },
    async createAudit(input) {
      const body = validateAuditRequest(input);
      await wait(options.auditDelay?.(body) ?? options.delay ?? 350);
      if (
        fault === "conflict" ||
        body.expected_data_fingerprint !== "synthetic-fixture-v1"
      )
        throw new ApiError(
          "DATA_VERSION_MISMATCH",
          "Source data changed. Reload before modeling another scenario.",
          409,
          true,
        );
      if (fault === "invalid")
        throw new ApiError(
          "INVALID_SCENARIO",
          "Demo validation rejected this scenario.",
          422,
        );
      const audit = structuredClone(initialAudit);
      audit.audit_id = `demo-audit-${++counter}`;
      audit.client_request_id = body.client_request_id;
      audit.scenario = structuredClone(body.scenario);
      if (fault === "empty") {
        audit.eligibility.unique_jobs = 0;
        audit.eligibility.overlapping_finding_references = 0;
        audit.eligibility.eligible_gpu_hours = 0;
        audit.evidence_preview = [];
        audit.evidence_count = 0;
        audit.limitations.push("No eligible jobs in this demo state.");
      }
      for (const key of ["low", "point", "high"] as const) {
        audit.recovery.gpu_hours[key] =
          audit.eligibility.eligible_gpu_hours *
          body.scenario.recovery_fraction[key];
        audit.recovery.reference_usd.values[key] =
          audit.recovery.gpu_hours[key] * body.scenario.usd_per_gpu_hour;
      }
      audit.recovery.basis = `${audit.eligibility.eligible_gpu_hours} unique eligible GPU-hours × assumed recovery fractions (${Object.values(
        body.scenario.recovery_fraction,
      )
        .map((n) => `${n * 100}%`)
        .join(" / ")}).`;
      parse("Audit", audit);
      snapshots.set(audit.audit_id, structuredClone(audit));
      return audit;
    },
    async getAudit(id) {
      await wait();
      return get(id);
    },
    async listEvidence(id, page = {}) {
      await wait();
      const audit = get(id);
      const start = Number(page.cursor ?? 0);
      const limit = page.limit ?? 25;
      if (
        !Number.isInteger(start) ||
        start < 0 ||
        start > audit.evidence_count ||
        !Number.isInteger(limit) ||
        limit < 1 ||
        limit > 100
      )
        throw new ApiError("INVALID_CURSOR", "Invalid evidence page.", 422);
      return parse("EvidencePage", {
        audit_id: id,
        items: audit.evidence_preview.slice(start, start + limit),
        total: audit.evidence_count,
        next_cursor:
          start + limit < audit.evidence_count ? String(start + limit) : null,
      });
    },
    async getEvidence(id, ref) {
      await wait();
      if (fault === "source-unavailable")
        throw new ApiError(
          "UPSTREAM_UNAVAILABLE",
          "Source evidence is currently unavailable. The calculation is preserved.",
          503,
          true,
        );
      if (fault === "not-found")
        throw new ApiError(
          "EVIDENCE_NOT_FOUND",
          "This source record could not be found.",
          404,
        );
      return evidence(id, ref);
    },
    askBaseChat: (id, request) => answer(id, request, false),
    explainAudit: (id, request) => answer(id, request, true),
    async exportClaims(id, team) {
      await wait();
      const audit = get(id);
      if (!team.trim() || team.length > 120)
        throw new ApiError(
          "INVALID_TEAM",
          "Enter a team name between 1 and 120 characters.",
          422,
        );
      return parse("Claims", {
        ...claimsFixture,
        team,
        recoverable_gpu_hours: {
          ...audit.recovery.gpu_hours,
          interval_kind: "scenario",
          basis: audit.recovery.basis,
        },
        recoverable_usd: {
          ...audit.recovery.reference_usd.values,
          interval_kind: "scenario",
          basis: `Reference value at $${audit.scenario.usd_per_gpu_hour}/GPU-hour; cash savings not verified.`,
        },
        notes: `Synthetic demo only; do not submit. Audit ${id}.`,
      });
    },
  };
}
