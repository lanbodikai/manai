import {useEffect,useRef,useState} from 'react';
import type {DashboardApi} from '../api/types';
import {actions,titles,defaults,validateConfiguration,type Action,type Configuration,type Portfolio,type EvidencePage,type CaseInput} from '../api/portfolio';
import {useDatasetCatalog,datasetHref} from './DataExplorer';
import {number,range,usd} from '../format';

export function usePortfolio(api:DashboardApi,enabled:boolean){
 const {catalog,error:sourceError,retry}=useDatasetCatalog(api);
 const [draft,setDraft]=useState<Configuration|null>(null),[result,setResult]=useState<Portfolio|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');const sequence=useRef(0);
 const currentVersion=useRef(catalog?.version);currentVersion.current=catalog?.version;
 async function calculate(config:Configuration){
  if(!api.portfolio)return;const seq=++sequence.current;setError('');
  try{validateConfiguration(config);setBusy(true);const value=await api.portfolio.calculate(config);
   if(value.synthetic!==catalog?.synthetic)throw new Error('Simulation provenance does not match this workspace.');
   if(seq===sequence.current&&currentVersion.current===config.dataset_version)setResult(value);
  }catch(e){if(seq===sequence.current)setError(e instanceof Error?e.message:'Simulation failed.');}
  finally{if(seq===sequence.current)setBusy(false);}
 }
 useEffect(()=>{
  ++sequence.current;setBusy(false);setResult(null);setDraft(null);setError('');
  if(enabled&&catalog&&!catalog.synthetic&&api.portfolio){const config=defaults(catalog.version);setDraft(config);void calculate(config);}
  return()=>{++sequence.current;};
 },[api,enabled,catalog]);
 const visible=result?.dataset_version===catalog?.version?result:null;
 return {api:api.portfolio,draft,setDraft,result:visible,busy,error:error||(enabled?sourceError:''),
  dirty:!!visible&&JSON.stringify(draft)!==JSON.stringify(visible.configuration),
  calculate:()=>draft&&calculate(draft),retry,enabled:enabled&&!!api.portfolio};
}
export type ModelState=ReturnType<typeof usePortfolio>;
export function PortfolioSummary({model,compact=false}:{model:ModelState;compact?:boolean}){
 const r=model.result;
 return <section className="panel portfolio-summary" aria-label="Combined cost simulation">
  <span className="badge">Simulation · historical reference costs</span><h2>Simulated cost reduction</h2>
  {r?<><strong className="portfolio-headline">{range(r.bounds.net_reference_usd.low,r.bounds.net_reference_usd.high)}</strong>
   <p><b>{number(r.bounds.baseline_reduction_pct.low)}%–{number(r.bounds.baseline_reduction_pct.high)}%</b> of baseline · illustrative case <b>{usd(r.cases[1].net_reference_usd)}</b></p>
   <p>{r.actions.length} actions · {number(r.coverage.assigned_jobs)} uniquely assigned jobs · negative values mean extra cost.</p>
   <p className="small muted">{r.actions.filter(a=>a.model_kind==='detailed_mechanism').length} detailed mechanisms · {r.actions.filter(a=>a.model_kind==='assumption_only_screening').length} assumption-only screening estimates.</p>
   <p><b>{number(r.bounds.target_contribution_pct.low)}%–{number(r.bounds.target_contribution_pct.high)}%</b> of the 20% target. Remaining gap: <b>{range(r.bounds.remaining_target_reference_usd.low,r.bounds.remaining_target_reference_usd.high)}</b>.</p>
   {!compact&&<p>Intervention failure: <b>{range(r.bounds.failure_extra_reference_usd.low,r.bounds.failure_extra_reference_usd.high)} extra</b>. One failed attempt/rerun; business harm and further retries are unpriced.</p>}
   <p className="small muted">Assumption-based scenarios, not confidence intervals or verified cash savings. Checkpoint contribution is avoided future replay; the historical target is a benchmark. Research performance is unverified.</p>
  </>:<p role="status">{model.busy?'Calculating the selected-action simulation…':'Simulation not available yet.'}</p>}
  {(model.dirty||model.busy&&r)&&<p role="status">Assumptions changed · showing previous calculation</p>}
  {model.error&&<p role="alert">{model.error} <button className="text-button" onClick={model.retry}>Reload simulation source</button></p>}
  <a className="text-button" href="#model">Model a scenario →</a>
 </section>;
}

const inputs:{key:Exclude<keyof CaseInput,'id'|'screening'>;label:string;min:number;max:number;action:Action;help?:string}[]=[
 {key:'cpu_price_ratio',label:'CPU price / GPU reference rate',min:0,max:10,action:'cpu-placement',help:'USD per physical-core-hour = this ratio × GPU hourly reference price.'},
 {key:'checkpoint_enrollment',label:'Checkpoint enrollment share',min:0,max:1,action:'timeouts'},
 {key:'replay_fraction',label:'Enrolled work otherwise requiring replay',min:0,max:1,action:'timeouts'},
 {key:'interval_minutes',label:'Checkpoint interval (minutes)',min:.25,max:100000,action:'timeouts'},
 {key:'checkpoint_minutes',label:'Time per checkpoint (minutes)',min:0,max:100000,action:'timeouts'},
 {key:'restart_minutes',label:'Restart overhead (minutes)',min:0,max:100000,action:'timeouts'},
 {key:'idle_enrollment',label:'Idle-release enrollment share',min:0,max:1,action:'idle-sessions'},
 {key:'release_hours',label:'Release age (hours after allocation starts)',min:.25,max:100000,action:'idle-sessions'},
 {key:'mistake_fraction',label:'Mistaken release share',min:0,max:1,action:'idle-sessions'},
];
export function PortfolioWorkspace({model,focusAction}:{model:ModelState;focusAction?:string}){
 const d=model.draft,r=model.result;
 const [group,setGroup]=useState('all'),[offset,setOffset]=useState(0),[page,setPage]=useState<EvidencePage|null>(null),[evidenceError,setEvidenceError]=useState(''),[attempt,setAttempt]=useState(0);
 useEffect(()=>{if(focusAction&&actions.includes(focusAction as Action))document.getElementById('model-'+focusAction)?.focus();},[focusAction,!!d]);
 useEffect(()=>{let alive=true;setPage(null);setEvidenceError('');
  if(r&&model.api)void model.api.evidence(r,group,offset).then(p=>{if(alive)setPage(p);}).catch(e=>{if(alive)setEvidenceError(String(e.message));});
  return()=>{alive=false;};
 },[r,model.api,group,offset,attempt]);
 useEffect(()=>setOffset(0),[r?.simulation_id]);
 function changeCase(index:number,key:Exclude<keyof CaseInput,'id'|'screening'>,value:string){if(d)model.setDraft({...d,cases:d.cases.map((c,i)=>i===index?{...c,[key]:value===''?NaN:Number(value)}:c)});}
 function download(){if(!r)return;const url=URL.createObjectURL(new Blob([JSON.stringify({export_kind:'portfolio-simulation-not-official-claims',...r},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='portfolio-simulation.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 return <div className="portfolio-workspace"><header className="page-header"><div><span className="eyebrow">MODEL THE ACTIONS</span><h1>Cost-reduction simulation</h1><p>One calculation shared with Overview and Decisions.</p></div><a href="#overview">Back to overview</a></header>
  <PortfolioSummary model={model}/>
  {d&&<section className="panel portfolio-inputs" aria-label="Simulation assumptions"><h2>Actions and assumptions</h2><p>Presets are illustrative, not measured intervention effectiveness. Shares are workload assumptions, not probabilities or selected job counts.</p>
   {actions.map(action=><section key={action} id={'model-'+action} tabIndex={-1} className="portfolio-action">
    <label><input type="checkbox" checked={d.selected_actions.includes(action)} onChange={e=>model.setDraft({...d,selected_actions:actions.filter(a=>a===action?e.target.checked:d.selected_actions.includes(a))})}/>{titles[action]}</label>
    <p className="small muted">{action==='cpu-placement'?'Successful CPU replacement, unchanged runtime and no added queue. One calculator vCPU models a physical core.':action==='timeouts'?'Avoid replay after timeouts; subtract checkpoint and restart overhead even for enrolled work that does not benefit. Equivalent remaining useful work cancels.':action==='idle-sessions'?'Warn 15 minutes before the release age; prorate the allocation tail and charge full reruns for mistaken releases. This is not an observed inactivity timer.':'Assumption-only screening: enrolled recorded allocation × assumed fraction avoided, minus additional costs. No performance, hardware-fit or root-cause claim.'}</p>
    {action==='cpu-placement'&&<label>CPU allocation<select aria-label="Portfolio CPU allocation" value={d.cpu_allocation} onChange={e=>model.setDraft({...d,cpu_allocation:e.target.value as Configuration['cpu_allocation']})}><option value="memory_adjusted">Requested cores, increased for memory</option><option value="whole_node">Whole 48-core node</option></select></label>}
    <div className="decision-scroll"><table><thead><tr><th>Assumption</th>{d.cases.map(c=><th key={c.id}>{c.id}</th>)}</tr></thead><tbody>{inputs.filter(f=>f.action===action).map(f=><tr key={f.key}><th>{f.label}{f.help&&<small>{f.help}</small>}</th>{d.cases.map((c,i)=><td key={c.id}><input aria-label={`${c.id}: ${f.label}`} type="number" min={f.min} max={f.max} step="any" value={Number.isFinite(c[f.key])?c[f.key]:''} onChange={e=>changeCase(i,f.key,e.target.value)}/></td>)}</tr>)}</tbody></table></div>
    {actions.indexOf(action)>=3&&<div className="decision-scroll"><table><thead><tr><th>Screening assumption · fraction 0–1</th>{d.cases.map(c=><th key={c.id}>{c.id}</th>)}</tr></thead><tbody>{(['enrollment','avoided_fraction','added_cost_fraction','failure_cost_fraction'] as const).map(key=><tr key={key}><th>{key.replaceAll('_',' ')}</th>{d.cases.map((c,i)=>{const a=action as keyof CaseInput['screening'];return <td key={c.id}><input aria-label={`${c.id}: ${titles[action]} ${key}`} type="number" min="0" max="1" step="any" value={Number.isFinite(c.screening[a][key])?c.screening[a][key]:''} onChange={e=>model.setDraft({...d,cases:d.cases.map((v,n)=>n===i?{...v,screening:{...v.screening,[a]:{...v.screening[a],[key]:e.target.value===''?NaN:Number(e.target.value)}}}:v)})}/></td>;})}</tr>)}</tbody></table></div>}
    <div className="portfolio-overheads">{(['setup_usd','storage_usd','other_usd'] as const).map(key=><label key={key}>{key.replace('_usd','').replace('_',' ')} cost ($)<input aria-label={`${titles[action]} ${key}`} type="number" min="0" max="1000000000" step="any" value={Number.isFinite(d.overheads[action][key])?d.overheads[action][key]:''} onChange={e=>model.setDraft({...d,overheads:{...d.overheads,[action]:{...d.overheads[action],[key]:e.target.value===''?NaN:Number(e.target.value)}}})}/></label>)}</div>
   </section>)}
   <p className="small muted">Zero setup, storage or other costs mean omitted costs. Fixed overheads are charged once per selected action in every case, even at zero enrollment.</p>
   <button className="primary" disabled={model.busy} onClick={()=>void model.calculate()}>{model.busy?'Calculating…':'Recalculate'}</button>
   <button className="secondary" disabled={model.busy} onClick={()=>model.setDraft(defaults(d.dataset_version))}>Reset illustrative assumptions</button>
  </section>}
  {r&&<section className="panel" aria-label="Simulation contributions"><h2>Contributions and coverage</h2><p>{number(r.coverage.unique_jobs)} unique diagnosed jobs · {number(r.coverage.overlapping_references_removed)} overlapping references removed · {number(r.coverage.unassigned_jobs)} jobs excluded from calculation ({number(r.coverage.unassigned_gpu_hours)} GPU-hours).</p>
   <p>Assignment order: fitting CPU placement → idle release → remaining timeouts → startup failures → batch-task validation → low utilization → GPU imbalance → memory sizing. Each job contributes once. Standalone diagnosis counts overlap.</p>
   <div className="decision-scroll"><table><thead><tr><th>Action</th><th>Diagnosed / evaluable / assigned jobs</th><th>Lower net</th><th>Illustrative net</th><th>Upper net</th></tr></thead><tbody>{r.actions.map(a=><tr key={a.id}><th>{titles[a.id]}<small>{a.model_kind==='assumption_only_screening'?'Assumption-only screening':'Detailed mechanism'}</small></th><td>{number(a.diagnosed_jobs)} / {number(a.evaluable_jobs)} / {number(a.assigned_jobs)}</td>{a.cases.map(c=><td key={c.id}>{usd(c.net_reference_usd)}</td>)}</tr>)}</tbody></table></div>
   {r.actions.map(a=><details key={a.id}><summary>{titles[a.id]}: accounting and summary statistics</summary>
    <p>Standalone cost reduction (overlaps other actions): {range(Math.min(...a.standalone_cases.map(c=>c.net_reference_usd)),Math.max(...a.standalone_cases.map(c=>c.net_reference_usd)))}. Portfolio columns use only assigned jobs.</p><p>Diagnosed allocation {number(a.diagnosed_gpu_hours)} GPU-hours; assigned {number(a.assigned_gpu_hours)}; excluded {number(a.excluded_gpu_hours)}. Duration median {a.statistics.duration_hours.median===null?'Unknown':number(a.statistics.duration_hours.median)} hours; Q1–Q3 {a.statistics.duration_hours.q1===null?'Unknown':`${number(a.statistics.duration_hours.q1)}–${number(a.statistics.duration_hours.q3!)}`}.</p>
    <p>GPU counts: {JSON.stringify(a.statistics.gpu_counts)}. Accounting discrepancies: {JSON.stringify(a.statistics.accounting_discrepancy)}. GPU memory groups: {JSON.stringify(a.statistics.gpu_memory)}. Exclusion reasons: {JSON.stringify(a.exclusion_reasons)}.</p>
    <div className="decision-scroll"><table><thead><tr><th>Case</th><th>Enrolled GPU-hours</th><th>Gross value</th><th>Intervention cost</th><th>Failure extra cost</th><th>Released / replay avoided GPU-hours</th><th>Modeled elapsed change, summed hours</th></tr></thead><tbody>{a.cases.map(c=><tr key={c.id}><td>{c.id}</td><td>{number(c.enrolled_gpu_hours)}</td><td>{usd(c.gross_reference_usd)}</td><td>{usd(c.intervention_reference_usd)}</td><td>{usd(c.failure_extra_reference_usd)}</td><td>{number(c.released_gpu_hours)} / {number(c.avoided_replay_gpu_hours)}</td><td>{c.modeled_elapsed_change_hours==null?'Unknown':number(c.modeled_elapsed_change_hours)}</td></tr>)}</tbody></table></div>
    <p>Summed timing is a workload-share-weighted scenario, not portfolio makespan or measured research performance.</p></details>)}
   <details><summary>Inspect assigned jobs and exclusions</summary><label>Assignment<select aria-label="Portfolio evidence group" value={group} onChange={e=>{setGroup(e.target.value);setOffset(0);}}><option value="all">All diagnosed jobs</option>{actions.map(a=><option key={a} value={a}>{titles[a]}</option>)}<option value="excluded">Excluded</option></select></label>
    {evidenceError?<p role="alert">{evidenceError} <button onClick={()=>setAttempt(x=>x+1)}>Retry evidence</button></p>:!page?<p role="status">Loading evidence…</p>:<><div className="decision-scroll"><table><thead><tr><th>Job</th><th>Assignment</th><th>Recorded GPU-hours</th><th>Details</th></tr></thead><tbody>{page.items.map(j=><tr key={j.job_id}><td><a href={datasetHref('jobs',{id:j.job_id})}>Job {j.job_id}</a></td><td>{j.assigned_action?titles[j.assigned_action]:'Excluded'}</td><td>{number(Number(j.source.gpu_hours))}</td><td><details><summary>Calculation</summary><pre>{JSON.stringify({exclusions:j.exclusions,cases:j.cases},null,2)}</pre></details></td></tr>)}</tbody></table></div><p>{number(page.total)} jobs.</p><button disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-25))}>Previous jobs</button><button disabled={offset+page.items.length>=page.total} onClick={()=>setOffset(offset+25)}>Next jobs</button></>}
   </details><details><summary>Interpretation and reproducibility</summary><ul>{r.limitations.map(l=><li key={l}>{l}</li>)}</ul><p className="portfolio-identity">Simulation {r.simulation_id} · dataset {r.dataset_version} · {r.configuration.preset_version}</p></details>
   <button className="secondary" onClick={download}>Download simulation report</button>
  </section>}
 </div>;
}
