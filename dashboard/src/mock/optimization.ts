// MANAI_MOCK_ONLY: original synthetic measurements, never organizer records.
import { buildDecisionTable, type JobMeasure, type FindingMeasure } from "../../tools/decision-summary";
import { decisionPayload, receiptPayload, validateOptimizeRequest, type OptimizationApi } from "../api/optimization";
import { ApiError } from "../api/validation";
import { demoDecisionSource } from "./datasets";
export const demoDecisionJobs: JobMeasure[] = [
  {id:"decision-job-A",gpu_hours:10,outcome:"COMPLETED",sm_avg:0,sm_max:0},
  {id:"decision-job-B",gpu_hours:20,outcome:"TIMEOUT",sm_avg:3,sm_max:7},
  {id:"decision-job-C",gpu_hours:30,outcome:"CANCELLED",sm_avg:0,sm_max:0},
  {id:"decision-job-D",gpu_hours:40,outcome:"COMPLETED",sm_avg:60,sm_max:80},
];
export const demoDecisionFindings: FindingMeasure[] = [
  {id:"decision-finding-A",rule:"rules::gpu-not-needed",job_id:"decision-job-A",scope:"job",synthetic:0},
  {id:"decision-finding-B",rule:"rules::idle-interactive-session",job_id:"decision-job-A",scope:"job",synthetic:0},
  {id:"decision-finding-C",rule:"rules::idle-interactive-session",job_id:"decision-job-C",scope:"job",synthetic:0},
  {id:"decision-finding-D",rule:"rules::wallclock-kill",job_id:"decision-job-B",scope:"job",synthetic:0},
  {id:"decision-finding-E",rule:"rules::gpu-low-utilization",job_id:"decision-job-B",scope:"job",synthetic:0},
  {id:"decision-finding-F",rule:"rules::filesystem-latency-degraded",job_id:null,scope:"node",synthetic:1},
];
// The entire dataset above is invented; per-finding flags imitate source metadata
// solely to test exclusion. Every response carries synthetic:true.
export function createMockOptimizationApi(delay = 80): OptimizationApi {
  const wait = () => new Promise(resolve => setTimeout(resolve,delay));
  return {
    async decisions(version,selected) {
      await wait();
      if (version !== "demo-dataset-v1") throw new ApiError("DATA_VERSION_MISMATCH","Reload the synthetic dataset.",409);
      const source = demoDecisionSource();
      return decisionPayload(buildDecisionTable(source.jobs,source.findings,version,selected,true),version,selected);
    },
    async submit(request) {
      validateOptimizeRequest(request);
      await wait();
      if (request.expected_dataset_version !== "demo-dataset-v1") throw new ApiError("DATA_VERSION_MISMATCH","Reload the synthetic dataset.",409);
      return receiptPayload({contract_version:request.contract_version,client_request_id:request.client_request_id,dataset_version:request.expected_dataset_version,
        mode:"model_only",fix_ids:[...request.fix_ids],optimization_id:`demo-plan-${request.client_request_id}`,status:"accepted",synthetic:true},request);
    },
  };
}
