import {ArrowRight,ChartPie,FlaskConical,ShieldCheck} from "lucide-react";
import type {DecisionRow} from "../api/optimization";
import type {PilotReview} from "../pilot-model";
import {number,range,usd} from "../format";
import {datasetHref} from "./DataExplorer";

export type OutcomeSlice={label:string;hours:number;color:string;note:string};
export function DecisionOverview({totalHours,price,windowLabel,outcomes,hasOutcomes,cpu,review,onModel,onReview,disabled}:{
  totalHours:number;price:number;windowLabel:string;outcomes:OutcomeSlice[];hasOutcomes:boolean;cpu?:DecisionRow;
  review:PilotReview|null;onModel:()=>void;onReview:()=>void;disabled:boolean;
}) {
  const snapshot=review?.snapshot;
  const r=snapshot?.result;
  const compactUsd=(value:number) => new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",notation:"compact",maximumFractionDigits:2}).format(value);
  return <section className="decision-overview" aria-label="CFO decision overview">
    <article className="panel decision-tile spend-tile">
      <div className="decision-tile-label"><ChartPie size={17}/><span>1 · WHERE SPENDING GOES</span></div>
      <h2 title={usd(totalHours*price)}>{compactUsd(totalHours*price)}</h2><p>Sample allocation value · reference pricing</p>
      {hasOutcomes ? <>
        <div className="spend-strip" aria-hidden="true">{outcomes.map(o => <span key={o.label} style={{width:`${totalHours ? o.hours/totalHours*100 : 0}%`,background:o.color}}/>)}</div>
        <ul className="spend-key">{outcomes.map(o => <li key={o.label}><span className="allocation-dot" style={{background:o.color}}/><span>{o.label}</span><strong>{totalHours ? (o.hours/totalHours*100).toFixed(1) : "0.0"}%</strong></li>)}</ul>
      </> : <p>Outcome breakdown unavailable.</p>}
      <details className="tile-details"><summary>Scope and calculation</summary><p>{windowLabel}. {number(totalHours)} recorded GPU-hours × {usd(price)}/GPU-hour = {usd(totalHours*price)}. Historical sample, not a current bill or next-quarter forecast.</p>{hasOutcomes && outcomes.map(o => <p key={o.label}><b>{o.label}: {usd(o.hours*price)}</b>. {o.note}</p>)}<p>Unallocated idle capacity is not measured here. Non-completion does not establish recoverable waste. Display percentages are rounded.</p></details>
    </article>
    <article className="panel decision-tile recommendation-tile">
      <div className="decision-tile-label"><FlaskConical size={17}/><span>2 · WHERE TO CUT FIRST</span></div>
      <h2>{cpu?.affected_jobs ? "Validate a CPU placement pilot" : "Investigate the evidence"}</h2>
      <p>{cpu?.affected_jobs ? "CPU placement pilot · platform + workload owner" : "No eligible CPU pilot jobs in this sample."}</p>
      <div className="decision-estimate"><span>Net reference benefit · CPU pilot only</span><strong>{r ? range(r.scenarios[0].net,r.scenarios[2].net) : "Estimate pending"}</strong><small>{r ? "Assumption-based range · negative means extra cost" : "Replacement costs and performance need testing"}</small></div>
      {r && <span className="evidence-status">Scenario modeled · not measured</span>}
      {review?.dirty && <p className="tile-draft" role="status">Assumptions changed · showing last calculation</p>}
      <div className="tile-actions"><button className="text-button" onClick={onModel} disabled={disabled || !cpu?.affected_jobs}>{r ? "Update pilot scenario" : "Open audited pilot"} <ArrowRight size={14}/></button></div>
      <details className="tile-details"><summary>Why start here?</summary><p>{cpu?.affected_jobs ? `${number(cpu.affected_jobs)} completed jobs recorded zero average and peak GPU compute. That gives us a specific cohort to test; it does not prove CPU compatibility.` : "A source-backed cohort is required before estimating a CPU pilot."}</p>{!!cpu?.affected_jobs && <p>The entire cohort accounts for {cpu.allocated_share_pct.toFixed(1)}% of sample allocation. Even removing all that allocation would not meet the 20% goal; replacement costs would reduce the benefit further.</p>}<p>Priority reflects a testable hypothesis, not the largest promised saving. Owner: {cpu?.owner ?? "Platform + workload owner"}.</p><a href={datasetHref("findings",{query:"rules::gpu-not-needed"})}>Inspect supporting records</a></details>
    </article>
    <article className="panel decision-tile downside-tile">
      <div className="decision-tile-label"><ShieldCheck size={17}/><span>3 · COST IF WE ARE WRONG</span></div>
      <h2>{r ? usd(r.extraSpend) : "Not yet priced"}</h2>
      <p>{r ? "Modeled extra cost if the CPU pilot falls back to GPUs" : "Estimate the downside before approving a change"}</p>
      <div className="decision-estimate"><span>Decision readiness</span><strong className="readiness-value">{r ? r.spendBreached || r.slowdownBreached ? "Limits exceeded" : "Owner review needed" : "Pilot evidence needed"}</strong><small>{r ? "Further retries can cost more. Research impact remains unpriced." : "No measured cash savings yet"}</small></div>
      <button className="text-button" onClick={onReview} disabled={disabled || !cpu?.affected_jobs}>Review guardrails <ArrowRight size={14}/></button>
      <details className="tile-details"><summary>What counts as verified?</summary><ol><li>Compare equivalent outputs, runtime and replacement cost.</li><li>Agree a pilot owner, stop limits and rollback.</li><li>Check actual billing after the change.</li></ol><p>Freed GPU capacity does not automatically reduce cash spending.</p></details>
    </article>
  </section>;
}
