import { describe, expect, it, vi } from "vitest";
import {
  createMockApi,
  initialAudit,
  overviewFixture,
  recommendationFixture,
} from "../src/mock/api";
import { createHttpApi } from "../src/api/http";
import { parse } from "../src/api/validation";
import type { Schemas } from "../src/api/types";
import requestFixture from "../../contracts/examples/audit-request.json";
import auditFixture from "../../contracts/examples/audit-response.json";
import evidenceFixture from "../../contracts/examples/baseline-evidence.json";
import explanationFixture from "../../contracts/examples/explanation-response.json";
import claimsFixture from "../../contracts/examples/claims-response.json";
import errorFixture from "../../contracts/examples/error-response.json";

const request = () => {
  const value = structuredClone(parse("AuditRequest", requestFixture));
  delete value.scenario.cpu_pilot;
  return value;
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("v0.4 contract", () => {
  it("checks every shared example and dashboard-specific fixtures", () => {
    for (const [name, data] of [
      ["AuditRequest", requestFixture],
      ["Audit", auditFixture],
      ["EvidenceDetail", evidenceFixture],
      ["Explanation", explanationFixture],
      ["Claims", claimsFixture],
      ["Error", errorFixture],
      ["Overview", overviewFixture],
      ["Recommendations", recommendationFixture],
    ] as const)
      expect(() => parse(name, data)).not.toThrow();
  });
  it("rejects schema drift, non-finite input, and invalid order", async () => {
    expect(() =>
      parse("Overview", { ...overviewFixture, invented_field: true }),
    ).toThrow();
    const api = createMockApi({ delay: 0 });
    for (const invalid of [
      { low: -0.1, point: 0.4, high: 0.6 },
      { low: 0.8, point: 0.4, high: 0.9 },
      { low: 0.2, point: 0.4, high: 1.1 },
      { low: NaN, point: 0.4, high: 0.6 },
      { low: 0, point: 0.4, high: Infinity },
    ]) {
      const r = request();
      r.scenario.recovery_fraction = invalid;
      await expect(api.createAudit(r)).rejects.toMatchObject({
        code: "INVALID_SCENARIO",
        status: 422,
      });
    }
    const r = request();
    r.scenario.usd_per_gpu_hour = 0;
    await expect(api.createAudit(r)).rejects.toMatchObject({
      code: "INVALID_SCENARIO",
    });
    const capped = structuredClone(parse("AuditRequest", requestFixture));
    capped.scenario.cpu_pilot!.trial_cap_hours = 1;
    await expect(api.createAudit(capped)).rejects.toMatchObject({
      code: "INVALID_SCENARIO",
      status: 422,
    });
  });
});

describe("mock snapshots and export", () => {
  it("returns two matching immutable scenarios and exports the requested one", async () => {
    const api = createMockApi({ delay: 0 });
    const first = await api.createAudit(request());
    const secondRequest = request();
    secondRequest.scenario.recovery_fraction = { low: 0, point: 0.5, high: 1 };
    secondRequest.scenario.usd_per_gpu_hour = 4;
    const second = await api.createAudit(secondRequest);
    expect(first.recovery.gpu_hours).toEqual({ low: 6, point: 12, high: 18 });
    expect(second.recovery.reference_usd.values).toEqual({
      low: 0,
      point: 60,
      high: 120,
    });
    const claims = await api.exportClaims(first.audit_id, "Test team");
    expect(claims.recoverable_usd).toMatchObject(
      first.recovery.reference_usd.values,
    );
    expect(claims.notes).toContain(first.audit_id);
    first.eligibility.eligible_gpu_hours = 999;
    expect(
      (await api.getAudit(first.audit_id)).eligibility.eligible_gpu_hours,
    ).toBe(30);
    const page = await api.listEvidence(first.audit_id, { limit: 1 });
    expect(page.items).toHaveLength(1);
    expect(page.next_cursor).toBe("1");
    expect(
      (
        await api.listEvidence(first.audit_id, {
          cursor: page.next_cursor!,
          limit: 1,
        })
      ).items[0].id,
    ).toBe("job:J2");
    await expect(
      api.getEvidence(first.audit_id, "not-a-member"),
    ).rejects.toMatchObject({ status: 404 });
    await expect(
      api.listEvidence(first.audit_id, { cursor: "nonsense" }),
    ).rejects.toMatchObject({ status: 422 });
    expect(
      (await api.getEvidence(first.audit_id, "job:J2")).observations.find(o => o.column === "gpu_hours")?.value,
    ).toBe(20);
  });
  it("handles empty cohorts and stale data explicitly", async () => {
    const emptyApi = createMockApi({ fault: "empty", delay: 0 });
    const empty = await emptyApi.createAudit(request());
    expect(empty.recovery.gpu_hours).toEqual({ low: 0, point: 0, high: 0 });
    expect((await emptyApi.listEvidence(empty.audit_id)).items).toEqual([]);
    const r = request();
    r.expected_data_fingerprint = "stale";
    await expect(
      createMockApi({ delay: 0 }).createAudit(r),
    ).rejects.toMatchObject({ status: 409 });
  });
  it.each([
    "reviewer-unavailable",
    "reviewer-timeout",
    "reviewer-malformed",
  ] as const)("keeps base chat and export usable during %s", async (fault) => {
    const api = createMockApi({ delay: 0, fault });
    const a = await api.createAudit(request());
    const q = { client_request_id: "q", question: "What could go wrong?" };
    await expect(api.explainAudit(a.audit_id, q)).rejects.toThrow();
    const answer = await api.askBaseChat(a.audit_id, q);
    expect(answer.audit_id).toBe(a.audit_id);
    expect(answer.tool_trace_ids).toEqual([]);
    expect(answer.usage.tool_calls).toBe(0);
    expect(
      (await api.exportClaims(a.audit_id, "Demo")).recoverable_gpu_hours.point,
    ).toBe(12);
    expect(
      (
        await api.askBaseChat(a.audit_id, {
          ...q,
          question: "Name a bad employee",
        })
      ).status,
    ).toBe("insufficient_evidence");
  });
});

describe("HTTP adapter never substitutes fixtures", () => {
  it("uses a configured v0.4 origin and reports a stale service clearly", async () => {
    const health = {
      service: "ok",
      contract_version: "0.4",
      data_status: "ready",
      data_fingerprint: "fixture-v1",
      agent_status: "unconfigured",
      mode: "synthetic_fixture",
    };
    const fetcher = vi.fn().mockResolvedValue(json(health));
    await expect(
      createHttpApi({ fetcher, baseUrl: "http://127.0.0.1:8014" }).getHealth(),
    ).resolves.toMatchObject({ contract_version: "0.4" });
    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8014/api/health",
      expect.objectContaining({ method: "GET" }),
    );
    await expect(
      createHttpApi({
        fetcher: vi.fn().mockResolvedValue(json({ ...health, contract_version: "0.3" })),
      }).getHealth(),
    ).rejects.toMatchObject({ code: "UNSUPPORTED_CONTRACT_VERSION", status: 426 });
  });
  it.each([404, 409, 422, 429, 502, 503, 504])(
    "preserves structured HTTP %s errors",
    async (status) => {
      const api = createHttpApi({
        fetcher: vi.fn().mockResolvedValue(json(errorFixture, status)),
      });
      await expect(api.getOverview()).rejects.toMatchObject({
        status,
        code: errorFixture.error.code,
      });
    },
  );
  it("rejects network, HTML and malformed payloads without a mock fallback", async () => {
    await expect(
      createHttpApi({
        fetcher: vi.fn().mockRejectedValue(new Error("offline")),
      }).getOverview(),
    ).rejects.toMatchObject({ status: 503 });
    await expect(
      createHttpApi({
        fetcher: vi.fn().mockResolvedValue(new Response("<html>app</html>")),
      }).getOverview(),
    ).rejects.toMatchObject({ status: 502 });
    await expect(
      createHttpApi({
        fetcher: vi.fn().mockResolvedValue(json({})),
      }).getOverview(),
    ).rejects.toMatchObject({ status: 502 });
  });
  it("rejects mismatched audit, evidence and request identities", async () => {
    const api = createHttpApi({
      fetcher: vi
        .fn()
        .mockImplementation(() =>
          Promise.resolve(
            json({ ...evidenceFixture, audit_id: initialAudit.audit_id }),
          ),
        ),
    });
    await expect(
      api.getEvidence("another-audit", "job:J1"),
    ).rejects.toMatchObject({ code: "AUDIT_ID_MISMATCH" });
    await expect(
      api.getEvidence(initialAudit.audit_id, "job:J1"),
    ).rejects.toMatchObject({ code: "EVIDENCE_ID_MISMATCH" });
    const chat = createHttpApi({
      fetcher: vi.fn().mockResolvedValue(
        json({ ...explanationFixture, audit_id: initialAudit.audit_id }),
      ),
    });
    await expect(
      chat.askBaseChat(initialAudit.audit_id, {
        client_request_id: "different",
        question: "Why?",
      }),
    ).rejects.toMatchObject({ code: "REQUEST_ID_MISMATCH" });
    const wrongAuditChat = createHttpApi({
      fetcher: vi.fn().mockResolvedValue(
        json({ ...explanationFixture, audit_id: initialAudit.audit_id }),
      ),
    });
    await expect(
      wrongAuditChat.askBaseChat("another-audit", {
        client_request_id: explanationFixture.client_request_id,
        question: "Why?",
      }),
    ).rejects.toMatchObject({ code: "AUDIT_ID_MISMATCH" });
  });
  it("uses separate chat routes and independent timeouts", async () => {
    const fetcher = vi.fn<typeof fetch>((url, init) => {
      if (String(url).endsWith("/explanations")) return new Promise(() => {});
      const body = JSON.parse(
        String(init?.body),
      ) as Schemas["ExplanationRequest"];
      return Promise.resolve(
        json({
          ...explanationFixture,
          audit_id: initialAudit.audit_id,
          client_request_id: body.client_request_id,
        }),
      );
    });
    const api = createHttpApi({
      fetcher,
      reviewerTimeout: 15,
      chatTimeout: 100,
    });
    const q = { client_request_id: "q", question: "Why this pilot?" };
    await expect(
      api.explainAudit(initialAudit.audit_id, q),
    ).rejects.toMatchObject({ status: 504 });
    expect((await api.askBaseChat(initialAudit.audit_id, q)).audit_id).toBe(
      initialAudit.audit_id,
    );
    expect(fetcher.mock.calls.map((c) => c[0])).toEqual([
      `/api/audits/${initialAudit.audit_id}/explanations`,
      `/api/audits/${initialAudit.audit_id}/chat`,
    ]);
  });
});
