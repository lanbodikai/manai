import type { DashboardApi, Schemas } from "./types";
import {createHardwareApi} from "./hardware";
import {createPortfolioApi} from "./portfolio";
import {
  ApiError,
  assertAuditId,
  assertRequestId,
  assertV04,
  parse,
  validateAuditRequest,
} from "./validation";

export function createHttpApi(
  options: {
    fetcher?: typeof fetch;
    baseUrl?: string;
    chatTimeout?: number;
    reviewerTimeout?: number;
  } = {},
): DashboardApi {
  const fetcher = options.fetcher ?? fetch;
  const base = options.baseUrl ?? import.meta.env.VITE_MANAI_API_URL ?? "";
  const auditPath = (id: string) => `/api/audits/${encodeURIComponent(id)}`;
  async function request<K extends keyof Schemas>(
    path: string,
    schema: K,
    body?: unknown,
    timeout = 15000,
  ): Promise<Schemas[K]> {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const timeoutPromise = new Promise<never>((_, reject) => {
      timer = setTimeout(() => {
        controller.abort();
        reject(
          new ApiError(
            "REQUEST_TIMEOUT",
            "The service took too long. Existing results are preserved.",
            504,
            true,
          ),
        );
      }, timeout);
    });
    try {
      return await Promise.race([
        timeoutPromise,
        (async () => {
          const response = await fetcher(base + path, {
            method: body === undefined ? "GET" : "POST",
            headers: {
              Accept: "application/json",
              ...(body === undefined
                ? {}
                : { "Content-Type": "application/json" }),
            },
            ...(body === undefined ? {} : { body: JSON.stringify(body) }),
            signal: controller.signal,
          });
          let payload: unknown;
          try {
            payload = await response.json();
          } catch {
            throw new ApiError(
              "UPSTREAM_RESPONSE_INVALID",
              "The service did not return valid JSON. Check the /api proxy configuration.",
              502,
            );
          }
          if (!response.ok) {
            const { error } = parse("Error", payload);
            throw new ApiError(
              error.code,
              error.message,
              response.status,
              error.retryable,
            );
          }
          if (
            schema === "Health" &&
            payload &&
            typeof payload === "object" &&
            "contract_version" in payload &&
            (payload as { contract_version?: unknown }).contract_version !== "0.4"
          )
            throw new ApiError(
              "UNSUPPORTED_CONTRACT_VERSION",
              `This dashboard requires API v0.4; received v${String((payload as { contract_version?: unknown }).contract_version)}.`,
              426,
              true,
            );
          return parse(schema, payload);
        })(),
      ]);
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(
        "UPSTREAM_UNAVAILABLE",
        "Cannot reach the API. Check the backend connection and retry. No demo data was substituted.",
        503,
        true,
      );
    } finally {
      clearTimeout(timer!);
    }
  }
  async function chat(
    id: string,
    body: Schemas["ExplanationRequest"],
    advanced: boolean,
  ) {
    try {
      parse("ExplanationRequest", body);
    } catch {
      throw new ApiError(
        "INVALID_QUESTION",
        "Enter a question between 1 and 2,000 characters.",
        422,
      );
    }
    const result = await request(
      `${auditPath(id)}/${advanced ? "explanations" : "chat"}`,
      "Explanation",
      body,
      advanced
        ? (options.reviewerTimeout ?? 35000)
        : (options.chatTimeout ?? 12000),
    );
    return assertRequestId(assertAuditId(result, id), body.client_request_id);
  }
  return {
    hardware: createHardwareApi(fetcher, base),
    portfolio: createPortfolioApi(fetcher, base),
    getHealth: async () => assertV04(await request("/api/health", "Health")),
    getOverview: () => request("/api/overview", "Overview"),
    listRecommendations: () =>
      request("/api/recommendations", "Recommendations"),
    createAudit: async (body) => {
      validateAuditRequest(body);
      return assertRequestId(
        await request("/api/audits", "Audit", body),
        body.client_request_id,
      );
    },
    getAudit: async (id) =>
      assertAuditId(await request(auditPath(id), "Audit"), id),
    listEvidence: async (id, page = {}) => {
      const params = new URLSearchParams({ limit: String(page.limit ?? 25) });
      if (page.cursor) params.set("cursor", page.cursor);
      return assertAuditId(
        await request(`${auditPath(id)}/evidence?${params}`, "EvidencePage"),
        id,
      );
    },
    getEvidence: async (id, ref) => {
      const result = assertAuditId(
        await request(
          `${auditPath(id)}/evidence/${encodeURIComponent(ref)}`,
          "EvidenceDetail",
        ),
        id,
      );
      if (result.evidence.id !== ref)
        throw new ApiError(
          "EVIDENCE_ID_MISMATCH",
          "The service returned a different evidence record.",
          502,
        );
      return result;
    },
    askBaseChat: (id, body) => chat(id, body, false),
    explainAudit: (id, body) => chat(id, body, true),
    exportClaims: (id, team) => {
      if (!team.trim() || team.length > 120)
        throw new ApiError(
          "INVALID_TEAM",
          "Enter a team name between 1 and 120 characters.",
          422,
        );
      return request(
        `${auditPath(id)}/claims?team=${encodeURIComponent(team)}`,
        "Claims",
      );
    },
  };
}
