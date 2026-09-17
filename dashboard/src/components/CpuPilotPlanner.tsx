import {useState} from "react";
import {ArrowRight, Download, ShieldCheck, TriangleAlert} from "lucide-react";
import {initialPilotInputs, modelPilot, type PilotInputs, type PilotSource, type PilotResult} from "../pilot-model";
import {number,usd,range} from "../format";
import {datasetHref} from "./DataExplorer";

type Snapshot={inputs:PilotInputs; source:PilotSource; result:PilotResult};
export function CpuPilotPlanner({source}: {source:PilotSource}) {
  const [inputs,setInputs]=useState<PilotInputs>({...initialPilotInputs});
  const [snapshot,setSnapshot]=useState<Snapshot|null>(null);
  const [error,setError]=useState("");
  const dirty=!!snapshot && JSON.stringify(inputs)!==JSON.stringify(snapshot.inputs);
  const field=(key:Exclude<keyof PilotInputs,"basis">,label:string,help?:string) => <label>{label}<input aria-label={label} aria-describedby={help ? `pilot-help-${key}` : undefined} type="number" min="0" max={key.startsWith("recovery") || key==="pilotPercent" ? 100 : undefined} step="any" value={inputs[key]} onChange={e => setInputs({...inputs,[key]:e.target.value})} />{help && <small id={`pilot-help-${key}`}>{help}</small>}</label>;
  function compare(e:React.FormEvent) {
    e.preventDefault();setError("");
    try {setSnapshot({inputs:{...inputs},source:{...source},result:modelPilot(source,inputs)});} catch(e) {setError(e instanceof Error ? e.message : "Unable to model these assumptions.");}
  }
  function download() {
    if(!snapshot) return;
    const file={kind:"cpu-pilot-planning-example",status:"not-approved-not-executed",...snapshot,caveats:["Conditional reference-dollar scenario, not cash savings or a canonical audit.","Pilot is a proportion of cohort GPU-hours; concrete jobs are not selected.","GPU-hours are not CPU core-hours; CPU inputs are independent estimates.","Business harm is unpriced; guardrails are proposed and not enforced.","Do not submit this file as claims.json."]};
    const url=URL.createObjectURL(new Blob([JSON.stringify(file,null,2)],{type:"application/json"}));
    const a=document.createElement("a");a.href=url;a.download="cpu-pilot-plan.example.json";a.click();setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  const r=snapshot?.result;
  return <section id="cpu-pilot-planner" tabIndex={-1} className="panel pilot-planner" aria-labelledby="pilot-heading">
    <div className="pilot-title"><div><span className="eyebrow">3 · REVIEW THE PROPOSED TEST</span><h2 id="pilot-heading">Should we run the CPU pilot?</h2><p>A small test of standard processors (CPUs), before changing more work.</p></div><span className="badge">{source.synthetic ? "Synthetic planning example" : "Planning only · nothing changed"}</span></div>
    {!snapshot && <div className="cfo-pilot-summary"><div><h3>What we recommend</h3><p>Have the platform team test a small group of suitable jobs on standard processors.</p></div><div><h3>What we might save</h3><p><strong>Estimate needed.</strong> Engineering must check the replacement cost before we can show a useful savings range.</p></div><div><h3>What could go wrong</h3><p>Jobs may run more slowly or fail. Start small and keep the option to return to GPUs.</p></div></div>}
    <details className="engineering-details"><summary>Engineering assumptions and pilot limits</summary>
    <p className="pilot-scope">For the platform and workload owners: {number(source.cohortHours)} eligible GPU-hours. This calculation covers the CPU test only, not other selected fixes.</p>
    <form onSubmit={compare} noValidate>
      <fieldset><legend>Set a small pilot and its limits</legend><div className="pilot-fields">
        {field("pilotPercent","Pilot size (% of eligible GPU-hours)","An hours budget, not a count or selection of jobs.")}
        {field("maxSpend","Maximum extra pilot spend ($)","Proposed stop limit, not automatically enforced.")}
        {field("maxSlowdown","Maximum acceptable slowdown (%)","Relative to equivalent GPU work.")}
      </div></fieldset>
      <fieldset><legend>What would equivalent CPU work cost?</legend><p>Enter benchmark results or explicit owner estimates. A CPU core-hour is one core running for one hour; it is not a GPU-hour.</p><div className="pilot-fields">
        {field("cpuPrice","CPU price ($/core-hour)")}{field("cpuLow","CPU core-hours — low")}{field("cpuPoint","CPU core-hours — base")}{field("cpuHigh","CPU core-hours — high")}
        {field("implementation","Implementation cost ($)")}{field("retryReserve","Extra retry / rollback reserve ($)","Exclude the original GPU allocation already included in the baseline.")}{field("worstSlowdown","Worst modeled slowdown (%)","Not measured by this dataset; business cost stays unpriced.")}
      </div></fieldset>
      <details className="pilot-recovery"><summary>Recovery assumptions: {inputs.recoveryLow}% / {inputs.recoveryPoint}% / {inputs.recoveryHigh}%</summary><p>The initial 0 / 50 / 100% values are illustrative stress scenarios, not measured recovery or confidence intervals. Recovery is the fraction of pilot GPU-hours avoided.</p><div className="pilot-fields">{field("recoveryLow","Recovery — low (%)")}{field("recoveryPoint","Recovery — base (%)")}{field("recoveryHigh","Recovery — high (%)")}</div></details>
      <label className="pilot-basis">Assumption source / evidence<textarea value={inputs.basis} onChange={e => setInputs({...inputs,basis:e.target.value})} placeholder="Example: workload-owner estimate; CPU benchmark still required" /></label>
      <p className="pilot-scope">GPU reference price: {usd(source.gpuPrice)}/GPU-hour (supplied 2026-Q3 price book). Reference value uses the historical sample window, not next-quarter billing. Fixed-cost GPUs may release capacity without reducing cash spend.</p>
      <button className="primary" disabled={!source.cohortHours} type="submit">Compare pilot scenarios <ArrowRight size={16}/></button>
      {error && <p role="alert" className="pilot-warning">{error}</p>}
    </form>
    </details>
    {!r && <div className="pilot-placeholder"><ShieldCheck size={22}/><p>Next step: ask the platform owner to complete the estimate and agree when to stop the test. You do not need to enter technical values yourself.</p></div>}
    {r && snapshot && <section className="pilot-results" aria-label="Calculated pilot result">
      {dirty && <p className="pilot-warning" role="status">Unsaved assumptions. Results and downloads still use the last calculated scenario.</p>}
      <div className="pilot-verdict"><TriangleAlert size={22}/><div><h3>{r.spendBreached || r.slowdownBreached ? "Revise this pilot before approval" : r.scenarios[1].net<=0 ? "No positive base-case benefit" : "Candidate for an owner-reviewed pilot"}</h3><p>{r.spendBreached ? "Modeled extra spend exceeds your limit. " : ""}{r.slowdownBreached ? "Modeled slowdown exceeds your limit. " : ""}No workload change has been approved or executed.</p></div></div>
      <div className="pilot-comparison"><article><span className="eyebrow">KEEP CURRENT ALLOCATION · COST</span><strong>{usd(r.baseline)}</strong><p>Reference cost for {number(r.pilotHours)} GPU-hours. Retain the existing execution path; no CPU migration cost.</p></article><article><span className="eyebrow">CPU ALTERNATIVE · MODELED COST</span><strong>{range(r.scenarios[2].afterCost,r.scenarios[0].afterCost)}</strong><p>Remaining GPU allocation + entered CPU, implementation and retry costs.</p><p>Net reference benefit: <b>{range(r.scenarios[0].net,r.scenarios[2].net)}</b>. Negative means a cost increase; business harm is excluded.</p></article></div>
      <details className="engineering-details"><summary>Detailed cost breakdown: low, base and high</summary><div className="pilot-scenario-grid">{r.scenarios.map(s => <article key={s.label}><h4>{s.label}</h4><strong>{usd(s.net)}</strong><dl><dt>GPU value avoided</dt><dd>{usd(s.avoided)}</dd><dt>CPU cost</dt><dd>{usd(s.cpuCost)}</dd><dt>Setup + reserve</dt><dd>{usd(r.overhead)}</dd><dt>Cost after change</dt><dd>{usd(s.afterCost)}</dd></dl></article>)}</div></details>
      <div className="pilot-target"><h3>How much of the 20% target does this pilot cover?</h3><p>{usd(r.contribution)} positive base-case contribution / {usd(r.target)} sample reference-cost target. Remaining gap: <strong>{usd(r.gap)}</strong>.</p><progress max="100" value={r.targetProgress} aria-label="Modeled contribution toward the sample 20 percent target"/><p>{number(r.targetProgress)}% of the target. No scale-up beyond this pilot or next-quarter forecast is assumed.</p></div>
      <div className="pilot-downside"><h3>If this cut is wrong</h3><ul><li><strong>Full GPU fallback:</strong> extra cost of {usd(r.extraSpend)} at the entered high CPU usage plus setup and reserve. Further retries can exceed this scenario.</li><li><strong>Slowdown:</strong> {number(Number(snapshot.inputs.worstSlowdown))}% modeled, versus a {number(Number(snapshot.inputs.maxSlowdown))}% limit. Deadline and researcher impact: <strong>Unpriced downside</strong>.</li><li><strong>Break-even:</strong> {!r.breakEvenPossible ? "Setup and reserve already exceed the base avoided GPU value." : r.breakEvenCpuHours===null ? "No CPU-hour threshold at a zero CPU price; other costs still apply." : `${number(r.breakEvenCpuHours)} CPU core-hours at the entered rate, holding base recovery and other costs fixed.`}</li></ul>
      <h4>Proposed stop and rollback conditions</h4><p>Stop if outputs fail validation, measured slowdown exceeds {number(Number(snapshot.inputs.maxSlowdown))}%, or extra spend reaches {usd(Number(snapshot.inputs.maxSpend))}. Restore GPU placement and preserve job results. The workload owner must select actual jobs, monitor the pilot and confirm rollback capacity.</p></div>
      <details><summary>Calculation and assumption provenance</summary><p>Net reference benefit = avoided GPU-hours × GPU reference price − CPU core-hours × CPU price − implementation cost − retry reserve. Low benefit combines low recovery with high CPU usage; high benefit combines high recovery with low CPU usage. These are stress scenarios, not probability estimates.</p><p>{snapshot.inputs.basis}</p><p className="pilot-version">Dataset: {snapshot.source.version}</p><a href={datasetHref("findings",{query:"rules::gpu-not-needed"})}>Inspect CPU pilot source evidence</a></details>
      <button className="secondary" onClick={download}><Download size={16}/>Download calculated pilot plan</button>
    </section>}
  </section>;
}
