import { ApiError } from "./validation";
import { fixIds } from "../optimization-options";

// Frontend proposal only. This is separate from the official team v0.3/v0.4 audit contract.
export type DecisionRow = {
  id: string; rule: string; title: string; owner: string; fix: string; risk: string;
  finding_count: number; affected_jobs: number; allocated_gpu_hours: number;
  allocated_share_pct: number; excluded_cancelled_jobs: number;
};
export type DecisionTable = {
  contract_version: "optimization-preview-1"; dataset_version: string; synthetic: boolean;
  total_gpu_hours: number; total_jobs: number; excluded_synthetic_findings: number;
  rows: DecisionRow[];
  selection: { fix_ids: string[]; unique_jobs: number; gpu_hours: number; share_pct: number; overlapping_gpu_hours: number };
};
export type OptimizeRequest = {
  contract_version: "optimization-preview-1"; client_request_id: string;
  expected_dataset_version: string; mode: "model_only";
  cancelled_policy: "exclude"; fix_ids: string[];
};
export type OptimizeReceipt = {
  contract_version: "optimization-preview-1"; client_request_id: string;
  dataset_version: string; mode: "model_only"; fix_ids: string[];
  optimization_id: string; status: "accepted"; synthetic: boolean;
};
export interface OptimizationApi {
  decisions(version: string, selected: string[]): Promise<DecisionTable>;
  submit(request: OptimizeRequest): Promise<OptimizeReceipt>;
}
const object = (v: unknown): v is Record<string, any> => !!v && typeof v === "object" && !Array.isArray(v);
const finite = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v) && v >= 0;
const count = (v: unknown): v is number => finite(v) && Number.isSafeInteger(v);
const text = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;
export const sameFixes = (a: readonly string[], b: readonly string[]) =>
  a.length === b.length && [...a].sort().join("|") === [...b].sort().join("|");
const validFixes = (v: unknown): v is string[] => Array.isArray(v) && v.every(x => typeof x === "string" && fixIds.includes(x)) && new Set(v).size === v.length;
const invalid = () => new ApiError("OPTIMIZATION_RESPONSE_INVALID", "The optimization response does not match this selection or dataset. No results were substituted.", 502);

export function decisionPayload(v: unknown, version: string, selected: string[]): DecisionTable {
  if (!object(v) || v.contract_version !== "optimization-preview-1" || v.dataset_version !== version || typeof v.synthetic !== "boolean" ||
      !finite(v.total_gpu_hours) || !count(v.total_jobs) || !count(v.excluded_synthetic_findings) || !Array.isArray(v.rows) ||
      !validFixes(v.rows.map((r: any) => r?.id)) || v.rows.length !== fixIds.length) throw invalid();
  const percentageMatches = (hours: number, percent: number) => finite(percent) && percent <= 100 &&
    hours <= v.total_gpu_hours + 1e-7 && Math.abs(percent - (v.total_gpu_hours ? hours / v.total_gpu_hours * 100 : 0)) < 1e-7;
  for (const row of v.rows) {
    if (!object(row) || ![row.id,row.rule,row.title,row.owner,row.fix,row.risk].every(text) ||
        !count(row.finding_count) || !count(row.affected_jobs) || row.affected_jobs > v.total_jobs || !count(row.excluded_cancelled_jobs) ||
        !finite(row.allocated_gpu_hours) || !percentageMatches(row.allocated_gpu_hours,row.allocated_share_pct)) throw invalid();
  }
  const s = v.selection;
  if (!object(s) || !validFixes(s.fix_ids) || !sameFixes(s.fix_ids,selected) || !count(s.unique_jobs) || s.unique_jobs > v.total_jobs ||
      !finite(s.gpu_hours) || !finite(s.overlapping_gpu_hours) || !percentageMatches(s.gpu_hours,s.share_pct)) throw invalid();
  const chosen = v.rows.filter((r: DecisionRow) => selected.includes(r.id));
  const sum = chosen.reduce((acc: number, r: DecisionRow) => acc + r.allocated_gpu_hours, 0);
  if (s.gpu_hours > sum + 1e-7 || s.gpu_hours + 1e-7 < Math.max(0,...chosen.map((r: DecisionRow) => r.allocated_gpu_hours)) ||
      Math.abs(sum - s.gpu_hours - s.overlapping_gpu_hours) > 1e-6) throw invalid();
  return v as DecisionTable;
}
export function validateOptimizeRequest(v: OptimizeRequest) {
  if (v.contract_version !== "optimization-preview-1" || !text(v.client_request_id) || !text(v.expected_dataset_version) ||
      v.mode !== "model_only" || v.cancelled_policy !== "exclude" || !validFixes(v.fix_ids) || !v.fix_ids.length)
    throw new ApiError("INVALID_OPTIMIZATION", "Select at least one supported fix to model.", 422);
}
export function receiptPayload(v: unknown, request: OptimizeRequest): OptimizeReceipt {
  if (!object(v) || v.contract_version !== request.contract_version || v.client_request_id !== request.client_request_id ||
      v.dataset_version !== request.expected_dataset_version || v.mode !== "model_only" || v.status !== "accepted" ||
      !text(v.optimization_id) || typeof v.synthetic !== "boolean" || !validFixes(v.fix_ids) || !sameFixes(v.fix_ids,request.fix_ids)) throw invalid();
  return v as OptimizeReceipt;
}
export function createOptimizationHttpApi(options: { fetcher?: typeof fetch; enabled?: boolean; timeoutMs?: number } = {}): OptimizationApi {
  const fetcher = options.fetcher ?? fetch;
  async function request(path: string, body?: OptimizeRequest): Promise<unknown> {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const timeout = new Promise<never>((_,reject) => {
      timer = setTimeout(() => { controller.abort(); reject(new ApiError("OPTIMIZATION_TIMEOUT", "The backend did not confirm the request. Its status is unknown; check with the service before resubmitting.", 504)); }, options.timeoutMs ?? 15000);
    });
    try {
      return await Promise.race([timeout, (async () => {
        const response = await fetcher(path, { method: body ? "POST" : "GET", headers: { Accept:"application/json", ...(body ? {"Content-Type":"application/json"} : {}) }, ...(body ? {body:JSON.stringify(body)} : {}), signal:controller.signal });
        if (!response.ok) {
          if (response.status === 409) throw new ApiError("DATA_VERSION_MISMATCH", "The dataset changed. Reload the decision table before submitting again.", 409);
          if ([404,405,501,503].includes(response.status)) throw new ApiError("OPTIMIZATION_UNAVAILABLE", body ? "The backend optimization action is not available. Your selection is preserved; no optimization result was produced." : "The decision-table service is not available. Load the verified local dataset or connect the backend.", response.status, true);
          throw new ApiError("OPTIMIZATION_REJECTED", "The backend rejected the request. Review the selection and retry.", response.status);
        }
        try { return await response.json(); } catch { throw invalid(); }
      })()]);
    } catch (e) {
      if (e instanceof ApiError) throw e;
      throw new ApiError("OPTIMIZATION_UNAVAILABLE", "Cannot reach the optimization backend. No result was substituted.", 503, true);
    } finally { clearTimeout(timer!); }
  }
  return {
    async decisions(version,selected) {
      if (!options.enabled) throw new ApiError("DECISIONS_NOT_CONFIGURED", "The decision-table backend is not connected. Use the explicit local dataset preview.", 503);
      if (!text(version) || !validFixes(selected)) throw new ApiError("INVALID_SELECTION", "Invalid dataset or fix selection.", 422);
      const q = new URLSearchParams({version, selection:selected.join(",")});
      return decisionPayload(await request(`/api/datasets/decisions?${q}`), version, selected);
    },
    async submit(body) {
      validateOptimizeRequest(body);
      const result = receiptPayload(await request("/api/optimizations",body), body);
      if (result.synthetic) throw new ApiError("SYNTHETIC_OPTIMIZATION_REJECTED", "A live optimization request returned a synthetic receipt.", 502);
      return result;
    },
  };
}
