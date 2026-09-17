import {useEffect,useState} from "react";
import type {HardwareApi,HardwarePage,HardwareScenario} from "../api/hardware";
import {number,range,usd} from "../format";
import {datasetHref} from "./DataExplorer";

export function HardwareScenarioPanel({scenario,api,allocation,onAllocation}:{scenario:HardwareScenario;api:HardwareApi;allocation:string;onAllocation:(value:string)=>void}) {
  const [status,setStatus]=useState('fits');const [offset,setOffset]=useState(0);
  const [page,setPage]=useState<HardwarePage|null>(null);const [error,setError]=useState('');const [attempt,setAttempt]=useState(0);
  useEffect(()=>{let alive=true;setPage(null);setError('');
    void api.jobs(scenario,status,offset).then(value=>{if(alive)setPage(value);}).catch(()=>{if(alive)setError('Resource evidence is unavailable. Retry before relying on individual job details.');});
    return()=>{alive=false;};
  },[api,scenario,status,offset,attempt]);
  const a=scenario.allocations.find(x=>x.id===allocation)!;const c=scenario.coverage;
  const show=(b:{low:number;high:number})=>range(b.low,b.high);
  function download(){const url=URL.createObjectURL(new Blob([JSON.stringify({export_kind:'hardware-simulation-not-official-claims',...scenario},null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download='cpu-hardware-scenario.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  return <section id="cpu-pilot-planner" tabIndex={-1} className="panel pilot-planner hardware-scenario" aria-label="Documented CPU hardware scenario">
    <p className="badge">Simulation · all {number(c.fitting_jobs)} resource-fitting historical jobs</p>
    <h2>What could this CPU configuration change?</h2>
    <p>This covers the full fitting population, not the smaller pilot in the manual planner. Successful replacement, unchanged runtime and no extra queue delay are assumed.</p>
    <label>CPU allocation<select value={allocation} onChange={e=>onAllocation(e.target.value)}><option value="memory_adjusted">Requested cores, increased for memory</option><option value="whole_node">Reserve the whole 48-core node</option></select></label>
    <div className="pilot-comparison"><article><span className="eyebrow">SUCCESSFUL REPLACEMENT · PRICE SENSITIVITY</span><strong>{show(a.success_net_reference_usd)}</strong>
      <p>Net reference benefit across {number(c.fitting_jobs)} jobs. CPU rates: {a.cases.map(x=>`$${x.cpu_reference_usd_per_core_hour.toFixed(4)}`).join(' and ')} per physical-core-hour.</p></article>
      <article><span className="eyebrow">IF ALL CPU ATTEMPTS REQUIRE GPU RERUNS</span><strong>{show(a.failure_extra_reference_usd)} extra</strong>
      <p>No GPU allocation released. Each job takes twice its original runtime before queue effects in this fixed scenario. Further retries and business harm are unpriced.</p></article></div>
    <p className="small muted">The positive range varies CPU price only. It is not a confidence interval or an overall range including failure. Reference values are not cash savings.</p>
    <div className="pilot-target"><h3>Contribution toward the 20% target</h3><p><strong>{number(a.baseline_reduction_pct.low)}%–{number(a.baseline_reduction_pct.high)}%</strong> of the historical sample baseline; <strong>{number(a.target_contribution_pct.low)}%–{number(a.target_contribution_pct.high)}%</strong> of the 20% target.</p>
      <p>Target: {usd(scenario.target_reference_usd)}. Remaining gap: <strong>{show(a.remaining_target_reference_usd)}</strong>. No next-quarter extrapolation.</p></div>
    <h3>Which jobs fit?</h3><p>{number(c.fitting_jobs)} fit · {number(c.non_fitting_jobs)} exceed node resources · {number(c.unresolved_jobs)} have unresolved placement or inputs.</p>
    <p>{number(c.memory_resized_jobs)} fitting jobs need more cores to cover requested RAM. This checks requests, not measured memory use or CPU compatibility.</p>
    <details><summary>Hardware, assumptions and calculation</summary><p>{scenario.hardware.name}: 48 physical cores, 192 GB RAM. Model: 192,000 MB/node and 4,000 MB/core. Extra cores do not imply faster execution.</p>
      <p>Recorded GPU-hours × {usd(scenario.gpu_reference_usd_per_hour)}/GPU-hour, minus modeled CPU core-hours × CPU reference rate. GPU pricing is assumed to include baseline host costs.</p>
      <div className="decision-scroll"><table><thead><tr><th>CPU rate / core-hour</th><th>CPU core-hours</th><th>CPU reference cost</th><th>Jobs with positive value and no delay</th></tr></thead><tbody>{a.cases.map(x=><tr key={x.cpu_reference_usd_per_core_hour}><td>${x.cpu_reference_usd_per_core_hour.toFixed(4)}</td><td>{number(x.cpu_core_hours)}</td><td>{usd(x.cpu_cost_reference_usd)}</td><td>{number(x.positive_no_slower_jobs)}</td></tr>)}</tbody></table></div>
      <p>Additional validation releases no GPU allocation, incurs the same CPU cost and has unknown completion impact.</p><ul>{scenario.limitations.map(text=><li key={text}>{text}</li>)}</ul>
      <p><a href="https://mit-supercloud.github.io/supercloud-docs/systems-and-software/" target="_blank" rel="noreferrer">MIT hardware</a> · <a href="https://mit-supercloud.github.io/supercloud-docs/submitting-jobs/" target="_blank" rel="noreferrer">Memory allocation guidance</a></p>
      <p className="pilot-version">Scenario: {scenario.scenario_id} · dataset: {scenario.dataset_version}</p></details>
    <details><summary>Inspect resource-fit evidence</summary>
      <label>Resource-fit group<select value={status} onChange={e=>{setStatus(e.target.value);setOffset(0);}}><option value="fits">Fits</option><option value="non_fit">Exceeds resources</option><option value="unresolved">Unresolved</option><option value="all">All eligible jobs</option></select></label>
      {error ? <p role="alert">{error} <button className="secondary" onClick={()=>setAttempt(x=>x+1)}>Retry evidence</button></p> : !page ? <p role="status">Loading resource evidence…</p> : <>
      <div className="decision-scroll"><table><thead><tr><th>Job</th><th>Requested cores</th><th>Requested RAM (MB)</th><th>Memory-adjusted cores</th><th>Classification</th></tr></thead><tbody>{page.items.map(j=><tr key={j.job_id}><td><a href={datasetHref('jobs',{id:j.job_id})}>Job {j.job_id}</a></td><td>{j.requested_cores??'Unknown'}</td><td>{j.requested_memory_mb===undefined?'Unknown':number(j.requested_memory_mb)}</td><td>{j.memory_adjusted_cores??'Unresolved'}</td><td>{j.reason.replaceAll('_',' ')}</td></tr>)}</tbody></table></div>
      <p>{number(page.total)} jobs in this group.</p><button className="secondary" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-25))}>Previous jobs</button>{' '}<button className="secondary" disabled={offset+page.items.length>=page.total} onClick={()=>setOffset(offset+25)}>Next jobs</button></>}
    </details><button className="secondary" onClick={download}>Download hardware scenario</button>
  </section>;
}
