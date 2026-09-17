// Original invented examples only. These fixtures are imported by tests, never the live dashboard.
import auditJson from "../../contracts/examples/audit-response.json";
import baselinesJson from "../../contracts/examples/pilot-recovery/baselines.json";
import requestJson from "../../contracts/examples/pilot-recovery/request-success.json";
import successJson from "../../contracts/examples/pilot-recovery/simulation-success.json";
import recoveredJson from "../../contracts/examples/pilot-recovery/simulation-failure_recovered.json";
import pausedJson from "../../contracts/examples/pilot-recovery/simulation-failure_unavailable.json";
import type {Audit} from "../src/api/types";
import type {PilotBaselines, PilotOutcome, PilotSimulation, PilotSimulationRequest} from "../src/api/pilot-recovery";
export const clone = <T,>(value: T): T => structuredClone(value);
export function baselines(): PilotBaselines {return clone(baselinesJson) as PilotBaselines;}
export function audit(): Audit {
  const result = clone(auditJson) as Audit, source = baselines();
  result.audit_id = source.audit_id; result.client_request_id = source.audit_client_request_id;
  result.provenance.data_fingerprint = source.data_fingerprint; result.provenance.source_version = source.source_version;
  result.provenance.synthetic = true; return result;
}
export const request = () => clone(requestJson) as PilotSimulationRequest;
export function simulation(outcome: PilotOutcome = "success"): PilotSimulation {
  return clone(outcome === "success" ? successJson : outcome === "failure_recovered" ? recoveredJson : pausedJson) as PilotSimulation;
}
export function json(value: unknown, status = 200) {return new Response(JSON.stringify(value), {status, headers: {"Content-Type": "application/json"}});}
