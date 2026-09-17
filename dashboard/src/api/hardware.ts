import Ajv2020 from "ajv/dist/2020";
import schema from "../../../contracts/cpu-hardware.schema.json";
import {ApiError} from "./validation";

export type Bounds={low:number;high:number};
export type HardwareAllocation={id:"memory_adjusted"|"whole_node";cases:{cpu_reference_usd_per_core_hour:number;success_net_reference_usd:number;failure_extra_reference_usd:number;cpu_core_hours:number;cpu_cost_reference_usd:number;positive_no_slower_jobs:number}[];
  success_net_reference_usd:Bounds;failure_extra_reference_usd:Bounds;baseline_reduction_pct:Bounds;target_contribution_pct:Bounds;remaining_target_reference_usd:Bounds};
export type HardwareScenario={contract_version:"cpu-hardware-1";scenario_id:string;dataset_version:string;data_fingerprint:string;synthetic:boolean;kind:"scenario_estimate";
  hardware:{name:string;physical_cores:48;memory_mb:192000;memory_mb_per_core:4000;sources:string[]};
  assumptions:{runtime_ratio:1;extra_queue_hours:0;cpu_price_ratios:number[];baseline_host_costs_included:true;scope:string;range_kind:string};
  gpu_reference_usd_per_hour:number;baseline_reference_usd:number;target_reference_usd:number;
  coverage:{eligible_jobs:number;eligible_gpu_hours:number;fitting_jobs:number;non_fitting_jobs:number;unresolved_jobs:number;fitting_gpu_hours:number;memory_resized_jobs:number};
  allocations:HardwareAllocation[];limitations:string[];compatibility_verified:false;cash_savings_verified:false};
export type HardwareJob={job_id:string;status:"fits"|"non_fit"|"unresolved";reason:string;recorded_gpu_hours:number;scheduler_hours:number|null;gpu_memory_category:string;requested_cores?:number;requested_memory_mb?:number;memory_adjusted_cores?:number};
export type HardwarePage={contract_version:"cpu-hardware-1";scenario_id:string;dataset_version:string;synthetic:boolean;offset:number;limit:number;total:number;items:HardwareJob[]};
export interface HardwareApi {summary(version:string):Promise<HardwareScenario>;jobs(scenario:HardwareScenario,status:string,offset:number):Promise<HardwarePage>}
const ajv=new Ajv2020({strict:false,strictNumbers:true});ajv.addSchema(schema);
export function hardwarePayload(value:unknown,version:string):HardwareScenario {
  if(!ajv.getSchema("cpu-hardware-1#/$defs/summary")!(value)) throw new ApiError("INVALID_HARDWARE_RESULT","Hardware scenario response is invalid.",502);
  const s=value as HardwareScenario;
  if(s.dataset_version!==version) throw new ApiError("DATA_VERSION_MISMATCH","Hardware scenario belongs to another dataset.",409);
  if(new Set(s.allocations.map(a=>a.id)).size!==2 || s.coverage.fitting_jobs+s.coverage.non_fitting_jobs+s.coverage.unresolved_jobs!==s.coverage.eligible_jobs) throw new ApiError("INVALID_HARDWARE_RESULT","Hardware scenario coverage is inconsistent.",502);
  for(const a of s.allocations) for(const key of ["success_net_reference_usd","failure_extra_reference_usd","baseline_reduction_pct","target_contribution_pct","remaining_target_reference_usd"] as const) {
    if(a[key].low>a[key].high) throw new ApiError("INVALID_HARDWARE_RESULT","Hardware scenario range is inverted.",502);
  }
  return s;
}
export function createHardwareApi(fetcher:typeof fetch,base:string):HardwareApi {
  async function read(path:string) {
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),15000);
    try {const response=await fetcher(base+path,{signal:controller.signal,headers:{Accept:"application/json"}});
      if(!response.ok) throw new ApiError("HARDWARE_UNAVAILABLE","Documented hardware scenario is unavailable. Existing tools remain usable.",response.status);
      return await response.json();
    } finally {clearTimeout(timer);}
  }
  return {summary:async(version)=>hardwarePayload(await read('/api/cpu-hardware-scenario?'+new URLSearchParams({dataset_version:version})),version),
    jobs:async(s,status,offset)=>{const value=await read('/api/cpu-hardware-scenario/jobs?'+new URLSearchParams({dataset_version:s.dataset_version,scenario_id:s.scenario_id,status,offset:String(offset),limit:'25'}));
      if(!ajv.getSchema("cpu-hardware-1#/$defs/page")!(value)) throw new ApiError("INVALID_HARDWARE_RESULT","Hardware evidence response is invalid.",502);
      const p=value as HardwarePage;
      if(p.scenario_id!==s.scenario_id || p.dataset_version!==s.dataset_version || p.synthetic!==s.synthetic || p.offset!==offset || p.limit!==25 || p.items.some(j=>status!=="all"&&j.status!==status)) throw new ApiError("SCENARIO_MISMATCH","Hardware evidence does not match the selected scenario.",409);
      return p;
    }};
}
