import Ajv2020 from 'ajv/dist/2020';
import schema from '../../../contracts/portfolio-simulation.schema.json';
import presets from '../../../contracts/portfolio-presets.json';
import {ApiError} from './validation';
export const actions=['cpu-placement','idle-sessions','timeouts','startup-failures','failed-arrays','low-utilization','gpu-imbalance','memory-sizing'] as const;
export type Action=typeof actions[number];
export const titles:Record<Action,string>={'cpu-placement':'CPU placement','idle-sessions':'Release idle sessions','timeouts':'Checkpoint / restart','startup-failures':'Prevent startup failures','failed-arrays':'Validate batch tasks','low-utilization':'Reduce low-use allocation','gpu-imbalance':'Improve GPU balance','memory-sizing':'Right-size GPU memory'};
export type CaseInput=typeof presets.cases[number];
export type Configuration=Omit<typeof presets,'selected_actions'|'cpu_allocation'>&{dataset_version:string;selected_actions:Action[];cpu_allocation:'memory_adjusted'|'whole_node'};
export const defaults=(version:string)=>({...structuredClone(presets),dataset_version:version}) as Configuration;
export type Bounds={low:number;high:number};
export type Totals={id:string;gross_reference_usd:number;intervention_reference_usd:number;net_reference_usd:number;failure_extra_reference_usd:number;enrolled_gpu_hours:number;released_gpu_hours:number;avoided_replay_gpu_hours:number;overhead_gpu_hours:number;cpu_core_hours:number;modeled_elapsed_change_hours?:number|null;failure_elapsed_change_hours?:number};
export type ActionResult={id:Action;model_kind:string;standalone_cases:{id:string;net_reference_usd:number}[];diagnosed_jobs:number;diagnosed_gpu_hours:number;evaluable_jobs:number;excluded_jobs:number;excluded_gpu_hours:number;assigned_jobs:number;assigned_gpu_hours:number;exclusion_reasons:Record<string,number>;statistics:{duration_hours:{median:number|null;q1:number|null;q3:number|null};gpu_counts:Record<string,number>;accounting_discrepancy:Record<string,number>;gpu_memory:Record<string,number>};cases:Totals[]};
export type Portfolio={contract_version:'portfolio-simulation-1';simulation_id:string;dataset_version:string;data_fingerprint:string;synthetic:boolean;configuration:Configuration;baseline_reference_usd:number;target_reference_usd:number;gpu_reference_usd_per_hour:number;cases:Totals[];bounds:Record<'net_reference_usd'|'failure_extra_reference_usd'|'baseline_reduction_pct'|'target_contribution_pct'|'remaining_target_reference_usd',Bounds>;actions:ActionResult[];coverage:{unique_jobs:number;unique_gpu_hours:number;assigned_jobs:number;unassigned_jobs:number;unassigned_gpu_hours:number;overlapping_references_removed:number;overlapping_gpu_hours_removed:number};limitations:string[]};
export type EvidencePage={simulation_id:string;dataset_version:string;offset:number;limit:number;total:number;items:{job_id:string;diagnoses:Action[];assigned_action:Action|null;exclusions:Record<string,string>;source:Record<string,string|number|null>;cases:Record<string,Totals & {preserved_progress_hours:number;released_tail_hours:number;checkpoints:number}>}[]};
export interface PortfolioApi{calculate(config:Configuration):Promise<Portfolio>;evidence(result:Portfolio,action:string,offset:number):Promise<EvidencePage>}
const ajv=new Ajv2020({strict:false,strictNumbers:true});ajv.addSchema(schema);
function finiteTree(x:unknown):boolean{return typeof x==='number'?Number.isFinite(x):Array.isArray(x)?x.every(finiteTree):x!==null&&typeof x==='object'?Object.values(x).every(finiteTree):true;}
export function validateConfiguration(config:Configuration){
 if(!finiteTree(config)||!ajv.getSchema('portfolio-simulation-1#/$defs/request')!(config)||config.cases.map(c=>c.id).join(',')!=='lower,illustrative,upper')throw new Error('Enter finite assumptions within the displayed limits.');
}
export function portfolioPayload(value:unknown,config:Configuration):Portfolio{
 if(!finiteTree(value)||!ajv.getSchema('portfolio-simulation-1#/$defs/summary')!(value))throw new Error('Invalid portfolio response.');
 const s=value as Portfolio;
 if(s.dataset_version!==config.dataset_version||JSON.stringify(s.configuration)!==JSON.stringify(config))throw new Error('Simulation assumptions or source do not match the request.');
 if(s.cases.map(c=>c.id).join(',')!=='lower,illustrative,upper'||new Set(s.actions.map(a=>a.id)).size!==s.actions.length||s.actions.length!==config.selected_actions.length||s.actions.some(a=>!config.selected_actions.includes(a.id)))throw new Error('Simulation actions or case identities do not match.');
 for(const b of Object.values(s.bounds))if(b.low>b.high)throw new Error('Invalid simulation range.');
 return s;
}
export function createPortfolioApi(fetcher:typeof fetch,base:string):PortfolioApi{
 async function request(path:string,body?:Configuration){
  const c=new AbortController();const timer=setTimeout(()=>c.abort(),60000);
  try{const r=await fetcher(base+path,{method:body?'POST':'GET',signal:c.signal,headers:{'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{})});
   if(!r.ok)throw new ApiError('PORTFOLIO_UNAVAILABLE',r.status===404?'Simulation expired. Recalculate to restore its evidence.':'Simulation unavailable. Check the source and assumptions, then retry.',r.status);
   return await r.json();
  }finally{clearTimeout(timer);}
 }
 return {calculate:async config=>{validateConfiguration(config);return portfolioPayload(await request('/api/portfolio-simulations',config),config);},
 evidence:async(s,action,offset)=>{const p=await request(`/api/portfolio-simulations/${s.simulation_id}/evidence?`+new URLSearchParams({dataset_version:s.dataset_version,action,offset:String(offset),limit:'25'})) as EvidencePage;
  if(!finiteTree(p)||!ajv.getSchema('portfolio-simulation-1#/$defs/page')!(p)||p.simulation_id!==s.simulation_id||p.dataset_version!==s.dataset_version||p.offset!==offset||p.limit!==25||p.items.some(j=>action!=='all'&&(action==='excluded'?j.assigned_action!==null:j.assigned_action!==action)))throw new Error('Evidence does not match this simulation.');
  return p;
 }};
}
