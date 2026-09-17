import Ajv2020 from "ajv/dist/2020";
import contract from "../../../contracts/pilot-recovery.openapi.json";
import type { Audit } from "./types";
import { ApiError } from "./validation";

export type PilotOutcome = "success" | "failure_recovered" | "failure_unavailable";
export interface PilotSimulationRequest {
  client_request_id: string; baseline_evidence_id: string; proposal: string;
  correctness_check: string; cpu_vcpus: number; cpu_hours: number;
  cpu_vcpu_hour_usd: number | null; max_runtime_hours: number;
  max_trial_spend_usd: number; setup_cost_usd: number | null;
  extra_queue_hours: number | null; baseline_host_costs_included: boolean;
  outcome: PilotOutcome; failure_reason: string; recovery_note: string;
}
export interface PilotBaseline {
  evidence_id: string; source_job_id: string; synthetic: boolean;
  state_name: string | null; sm_util_avg: number | null; sm_util_max: number | null;
  max_gpu_mem_used: number | null; gpu_count: number | null;
  elapsed_hours: number | null; recorded_gpu_hours: number | null;
  usd_per_gpu_hour: number | null; original_reference_cost_usd: number | null;
  missing_fields: string[];
}
interface Envelope {
  feature_version: "0.1"; audit_id: string; audit_client_request_id: string;
  data_fingerprint: string; source_version: string; synthetic: boolean;
  simulation_only: true;
}
export interface PilotBaselines extends Envelope {
  items: PilotBaseline[]; total: number; limitations: string[];
}
export interface PilotSimulation extends Envelope {
  simulation_id: string; client_request_id: string;
  execution_performed: false; independent_alternative: true; history_persisted: false;
  compatibility_verified: false; cash_savings_verified: false; live_stop_enforcement_verified: false;
  inputs: PilotSimulationRequest; baseline: PilotBaseline;
  status: "success" | "recovered" | "paused"; effective_outcome: PilotOutcome;
  stop_reason: null | "runtime_limit" | "spend_limit" | "runtime_and_spend_limit" | "setup_exceeds_spend_limit";
  failure_details: {requested_failure_reason: string; effective_failure_reason: string | null; selected_outcome_changed: boolean};
  costs: {currency: "USD"; kind: "reference_estimate"; original_cost_usd: number | null;
    cpu_trial_cost_usd: number | null; setup_cost_usd: number | null; trial_cost_usd: number | null;
    recovery_cost_usd: number | null; cost_so_far_usd: number | null;
    total_cost_to_complete_usd: number | null; net_benefit_usd: number | null};
  timing: {requested_cpu_hours: number; effective_cpu_hours: number; baseline_elapsed_hours: number | null;
    extra_queue_hours: number | null; run_time_change_hours_excluding_queue: number | null;
    completion_change_hours: number | null; total_elapsed_hours_including_queue: number | null};
  capacity: {released_gpu_hours: number | null; remaining_gpu_hours: number | null; added_cpu_vcpu_hours: number};
  limits: {max_runtime_hours: number; max_trial_spend_usd: number; requested_setup_cost_usd: number | null;
    runtime_limit_reached: boolean; spend_limit_status: "within_limit" | "reached" | "unverified" | "blocked_before_start";
    cap_enforcement: "simulation_only"; trial_started: boolean; spend_limit_excludes_recovery: true};
  recovery: {status: "not_required" | "assumed_completed" | "unavailable_paused";
    strategy: "none" | "full_original_gpu_rerun"; checkpoint_verified: false; available_assumed: boolean;
    note: string; recovery_gpu_hours: number | null};
  timeline: {step: "baseline" | "trial" | "recovery" | "result"; status: string; detail: string}[];
  canonical_calculator_reused: boolean;
  calculator_proof: {quantity: string; formula: string; value: number | null; unit: "reference USD"}[];
  possible_causes: {hypothesis: string; next_check: string; evidence_status: "unverified_hypothesis"}[];
  limitations: string[];
}
export interface PilotRecoveryApi {
  getBaselines(audit: Audit, signal?: AbortSignal): Promise<PilotBaselines>;
  simulate(audit: Audit, baseline: PilotBaseline, request: PilotSimulationRequest, signal?: AbortSignal): Promise<PilotSimulation>;
}
const ajv = new Ajv2020({allErrors: true, strict: false, strictNumbers: true});
ajv.addSchema({$id: "pilot-recovery", components: contract.components});
function validate<T>(name: keyof typeof contract.components.schemas, value: unknown): T {
  const check = ajv.getSchema(`pilot-recovery#/components/schemas/${name}`)!;
  if (!check(value)) throw new ApiError("PILOT_RESPONSE_INVALID", `Invalid ${name} response. Existing simulations are preserved.`, 502);
  return value as T;
}
function same(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== "object" || a === null || typeof b !== "object" || b === null) return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const x = a as Record<string, unknown>, y = b as Record<string, unknown>;
  return Object.keys(x).length === Object.keys(y).length && Object.keys(x).every(k => Object.hasOwn(y, k) && same(x[k], y[k]));
}
function scope<T extends Envelope>(payload: T, audit: Audit): T {
  if (payload.audit_id !== audit.audit_id || payload.audit_client_request_id !== audit.client_request_id ||
      payload.data_fingerprint !== audit.provenance.data_fingerprint || payload.source_version !== audit.provenance.source_version ||
      payload.synthetic !== audit.provenance.synthetic) {
    throw new ApiError("PILOT_SCOPE_MISMATCH", "The response belongs to different evidence. Reload baselines before retrying.", 409);
  }
  return payload;
}
export function createPilotRecoveryApi(options: {fetcher?: typeof fetch; baseUrl?: string; timeoutMs?: number; maxBytes?: number} = {}): PilotRecoveryApi {
  const fetcher = options.fetcher ?? fetch;
  const maxBytes = options.maxBytes ?? 2_000_000;
  async function request<T>(path: string, schema: keyof typeof contract.components.schemas, body?: PilotSimulationRequest, external?: AbortSignal): Promise<T> {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    let cancel: (() => void) | undefined;
    const stopped = new Promise<never>((_, reject) => {
      cancel = () => {controller.abort(); reject(new ApiError("PILOT_REQUEST_CANCELLED", "The outdated request was cancelled.", 499));};
      external?.addEventListener("abort", cancel, {once: true});
      if (external?.aborted) cancel();
      timer = setTimeout(() => {controller.abort(); reject(new ApiError("PILOT_REQUEST_TIMEOUT", "The analysis service took too long. Retry; earlier simulations are preserved.", 504, true));}, options.timeoutMs ?? 15000);
    });
    try {
      return await Promise.race([stopped, (async () => {
        if (controller.signal.aborted) throw new ApiError("PILOT_REQUEST_CANCELLED", "The request was cancelled.", 499);
        const response = await fetcher((options.baseUrl ?? "") + path, {
          method: body ? "POST" : "GET", redirect: "error", signal: controller.signal,
          headers: {Accept: "application/json", ...(body ? {"Content-Type": "application/json"} : {})},
          ...(body ? {body: JSON.stringify(body)} : {}),
        });
        if (Number(response.headers.get("content-length")) > maxBytes) throw new ApiError("PILOT_RESPONSE_TOO_LARGE", "The response exceeded the safe reading limit.", 502);
        const reader = response.body?.getReader();
        if (!reader) throw new ApiError("PILOT_RESPONSE_INVALID", "The service returned an empty response.", 502);
        const decoder = new TextDecoder(); let bytes = 0, raw = "";
        try {
          while (true) {
            const {done, value} = await reader.read(); if (done) break;
            bytes += value.byteLength;
            if (bytes > maxBytes) {await reader.cancel(); throw new ApiError("PILOT_RESPONSE_TOO_LARGE", "The response exceeded the safe reading limit.", 502);}
            raw += decoder.decode(value, {stream: true});
          }
        } finally {reader.releaseLock();}
        raw += decoder.decode();
        let payload: unknown;
        try {payload = JSON.parse(raw);} catch {throw new ApiError("PILOT_RESPONSE_INVALID", "The analysis service did not return valid JSON.", 502);}
        if (!response.ok) {
          const result = validate<{error: {code: string; message: string; retryable: boolean}}>("PilotError", payload);
          throw new ApiError(result.error.code, result.error.message, response.status, result.error.retryable);
        }
        return validate<T>(schema, payload);
      })()]);
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError("PILOT_SERVICE_UNAVAILABLE", "Cannot reach the analysis service. Retry when it is available; no sample result was substituted.", 503, true);
    } finally {clearTimeout(timer); if (cancel) external?.removeEventListener("abort", cancel);}
  }
  const path = (audit: Audit) => `/api/audits/${encodeURIComponent(audit.audit_id)}`;
  return {
    getBaselines: async (audit, signal) => {
      const result = scope(await request<PilotBaselines>(`${path(audit)}/pilot-baselines`, "PilotBaselines", undefined, signal), audit);
      if (result.items.length !== result.total || new Set(result.items.map(x => x.evidence_id)).size !== result.items.length)
        throw new ApiError("PILOT_BASELINES_INVALID", "The baseline list is incomplete or contains duplicate evidence.", 502);
      return result;
    },
    simulate: async (audit, baseline, inputs, signal) => {
      try {validate("PilotSimulationRequest", inputs);} catch {throw new ApiError("PILOT_INPUT_INVALID", "Complete the proposal, correctness check and valid numeric assumptions. Failed outcomes need a failure reason.", 422);}
      if (inputs.baseline_evidence_id !== baseline.evidence_id) throw new ApiError("PILOT_BASELINE_MISMATCH", "Select the matching baseline before simulating.", 409);
      const result = scope(await request<PilotSimulation>(`${path(audit)}/pilot-simulations`, "PilotSimulation", inputs, signal), audit);
      if (result.client_request_id !== inputs.client_request_id || !same(result.inputs, inputs))
        throw new ApiError("PILOT_REQUEST_MISMATCH", "The result does not match these assumptions. Earlier simulations are preserved.", 502);
      if (!same(result.baseline, baseline)) throw new ApiError("PILOT_BASELINE_MISMATCH", "The historical baseline changed. Reload before retrying.", 409);
      return result;
    },
  };
}
