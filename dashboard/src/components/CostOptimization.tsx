import { useEffect, useRef, useState } from "react";
import { ArrowRight, CheckCircle2, RefreshCw, TriangleAlert } from "lucide-react";
import type { DashboardApi } from "../api/types";
import { decisionPayload, sameFixes, type DecisionTable, type OptimizeReceipt, type OptimizeRequest } from "../api/optimization";
import { errorMessage } from "../api/validation";
import { number, usd } from "../format";
import { datasetHref, useDatasetCatalog } from "./DataExplorer";
import { CpuPilotPlanner } from "./CpuPilotPlanner";
import { OptimizeDialog } from "./OptimizeDialog";
import { DecisionOverview } from "./DecisionOverview";
import type { PilotReview } from "../pilot-model";
import { taskSummary } from "../optimization-options";

export const percent = (value: number) => value > 0 && value < 0.1 ? "<0.1%" : `${value.toFixed(1)}%`;

export function CostOptimization({ api }: { api: DashboardApi }) {
  const { catalog, error: catalogError, retry } = useDatasetCatalog(api);
  const [table, setTable] = useState<DecisionTable | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [sending, setSending] = useState(false);
  const [actionError, setActionError] = useState("");
  const [receipt, setReceipt] = useState<OptimizeReceipt | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pilotOpen, setPilotOpen] = useState(false);
  const [pilotReview, setPilotReview] = useState<PilotReview|null>(null);
  const [reviewWhenReady, setReviewWhenReady] = useState(false);
  // Verified against the supplied API /v1/price-book (2026-Q3), 2026-09-17. Reference pricing, not an actual bill.
  const referencePrice = 2.5;
  const pending = useRef<OptimizeRequest | null>(null);
  const dialogTrigger = useRef<HTMLElement|null>(null);
  const submitSequence = useRef(0);
  const selectionKey = selected.join(",");
  useEffect(() => () => { ++submitSequence.current; }, []);
  useEffect(() => {
    if (!catalog) return;
    let alive = true;
    setLoading(true);
    setLoadError("");
    if (!api.optimization) {
      setLoadError("Cost optimization is not connected to this workspace.");
      setLoading(false);
      return;
    }
    void api.optimization.decisions(catalog.version, selected).then(value => {
      const next = decisionPayload(value,catalog.version,selected);
      if (next.synthetic !== catalog.synthetic) throw new Error("Decision provenance does not match this workspace.");
      if (catalog.summary && Math.abs(next.total_gpu_hours-catalog.summary.gpu_hours) > 0.00001) throw new Error("Decision denominator does not match the source overview.");
      if (alive) setTable(next);
    }).catch(error => { if (alive) setLoadError(errorMessage(error)); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [api,catalog,selectionKey]);
  const visible = table?.dataset_version === catalog?.version ? table : null;
  const current = !!visible && sameFixes(visible.selection.fix_ids,selected) && !loading && !loadError;
  useEffect(() => {
    if(reviewWhenReady && current) {setConfirmOpen(true);setReviewWhenReady(false);}
  },[reviewWhenReady,current]);
  const available = visible?.rows.filter(r => r.affected_jobs > 0).map(r => r.id) ?? [];
  const selectedRows = visible?.rows.filter(r => selected.includes(r.id)) ?? [];
  const actionableRows = visible?.rows.filter((row) => row.affected_jobs > 0) ?? [];
  const inactiveRows = visible?.rows.filter((row) => row.affected_jobs === 0) ?? [];
  function choose(next: string[]) {
    if (sending) return;
    setSelected(next);
    setConfirmOpen(false);
    setReviewWhenReady(false);
    if(!next.includes("cpu-placement")) {setPilotOpen(false);setPilotReview(null);}
    setReceipt(null);
    setActionError("");
    pending.current = null;
    ++submitSequence.current;
  }
  function reload() {
    choose([]);
    setTable(null);
    retry();
  }
  async function optimize() {
    if (!current || !selected.length || !api.optimization || sending || receipt) return;
    const sequence = ++submitSequence.current;
    const request: OptimizeRequest = pending.current ?? {
      contract_version:"optimization-preview-1", client_request_id:crypto.randomUUID(),
      expected_dataset_version:visible!.dataset_version, mode:"model_only", cancelled_policy:"exclude", fix_ids:[...selected],
    };
    pending.current = request;
    setSending(true);
    setActionError("");
    try {
      const result = await api.optimization.submit(request);
      if (sequence === submitSequence.current) setReceipt(result);
    } catch (error) {
      if (sequence === submitSequence.current) setActionError(errorMessage(error));
    } finally {
      if (sequence === submitSequence.current) setSending(false);
    }
  }
  const error = catalogError || loadError;
  const outcomeGroups = [
    { label:"Finished", states:["COMPLETED","Finished"], color:"#597be8", note:"The job completed. Completion alone does not mean all its allocated GPU time was productive." },
    { label:"Cancelled", states:["CANCELLED","Cancelled"], color:"#b2bed3", note:"Someone cancelled this work. That does not establish waste; cancelled jobs are excluded from the proposed fixes below." },
    { label:"Timed out", states:["TIMEOUT","Timed out"], color:"#e8b460", note:"The job reached its time limit. Checkpointing may help, but recovery has not been measured." },
    { label:"Failed", states:["FAILED","NODE_FAIL","Failed"], color:"#d78789", note:"The job ended unsuccessfully. The outcome alone does not identify the cause or prove a hardware fault." },
    { label:"Other", states:[], color:"#b5a2d3", note:"Other or undecoded outcomes need investigation before a decision can be made." },
  ];
  const outcomes = outcomeGroups.map(group => ({...group,hours:(catalog?.summary?.outcomes ?? []).filter(item => group.states.length ? group.states.includes(item.outcome) : !outcomeGroups.some(g => g.states.includes(item.outcome))).reduce((sum,item) => sum+item.gpu_hours,0)}));
  const cpuRow = visible?.rows.find(row => row.id === "cpu-placement");
  const review = selected.includes("cpu-placement") && pilotReview?.snapshot?.source.version === visible?.dataset_version ? pilotReview : null;
  function openPilot() {
    if(!selected.includes("cpu-placement")) choose([...selected,"cpu-placement"]);
    setPilotOpen(true);
    setTimeout(() => document.getElementById("cpu-pilot-planner")?.focus(),0);
  }
  function reviewPilot() {
    const trigger=document.activeElement as HTMLElement|null;
    if(!selected.includes("cpu-placement")) choose([...selected,"cpu-placement"]);
    dialogTrigger.current=trigger;
    setReviewWhenReady(true);
  }
  function downloadReview() {
    if(!visible || !current) return;
    const file={kind:"decision-review-example",status:"not-approved-not-executed",dataset_version:visible.dataset_version,synthetic:visible.synthetic,
      scope:catalog?.window_label,reference_price:{usd_per_gpu_hour:referencePrice,version:"2026-Q3",basis:"reference pricing, not billing"},
      selection:visible.selection,actions:selectedRows.map(row => ({...row,evidence_status:row.id==="cpu-placement" && review ? "scenario-modeled-not-measured" : "needs-testing",evidence_path:datasetHref("findings",{query:row.rule})})),
      cpu_pilot:review?.snapshot ?? null,unsaved_cpu_assumptions:review?.dirty ?? false,
      combined_net_savings:null,verified_cash_savings:null,
      required_before_pilot:["Owner selects actual jobs and verifies equivalent outputs","Benchmark replacement cost and runtime","Agree stop limits and rollback capacity"],
      caveats:["Recorded allocation value is not recoverable savings.","Selected exposure deduplicates job hours; intervention savings are not additive.","CPU scenario covers only its modeled pilot, not all selected actions.","Research harm remains unpriced; no next-quarter extrapolation.","Do not submit this planning export as claims.json."]};
    const url=URL.createObjectURL(new Blob([JSON.stringify(file,null,2)],{type:"application/json"}));
    const a=document.createElement("a");a.href=url;a.download="decision-review.example.json";a.click();setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  return <div className="optimization-page">
    <header className="page-header">
      <div><span className="eyebrow">CFO DECISION REVIEW</span>
        <h1>Prioritize a guarded pilot</h1>
        <p>Investigate the evidence, model the downside, then authorize a measured test.</p>
      </div>
      <a className="secondary" href={datasetHref("findings")}>Inspect source evidence <ArrowRight size={15} /></a>
    </header>
    {error && <div className="panel error-state" role="alert"><TriangleAlert /><h2>Could not load the decision table</h2><p>{error}</p><button className="secondary" onClick={reload} disabled={sending}><RefreshCw size={15} /> Reload data</button></div>}
    {!visible && !error && <div className="panel" role="status">Reading verified findings and job hours…</div>}
    {visible && <>
      <section className="panel decision-brief" aria-labelledby="decision-brief-title">
        <div>
          <span className="eyebrow">CURRENT RECOMMENDATION</span>
          <h2 id="decision-brief-title">Do not change workloads yet.</h2>
          <p>Authorize only a small, owner-reviewed pilot after the evidence, cost boundary, and rollback plan are checked.</p>
        </div>
        <ol>
          <li><strong>1. Investigate</strong><span>Confirm the source records and eligible job scope.</span></li>
          <li><strong>2. Model</strong><span>Price the named pilot and its downside.</span></li>
          <li><strong>3. Authorize</strong><span>Set an owner, stop limits, and a rollback path.</span></li>
        </ol>
      </section>
      <DecisionOverview totalHours={visible.total_gpu_hours} price={referencePrice} windowLabel={catalog?.window_label ?? "Historical sample"} outcomes={outcomes} hasOutcomes={!!catalog?.summary} cpu={cpuRow} review={review} onModel={openPilot} onReview={reviewPilot} disabled={sending || loading || !!loadError}/>
      <section className="panel decision-panel" aria-label="Actions ready for review"><div className="decision-caption"><span>Actionable cohorts · reference value, not savings</span><span className="badge">{visible.synthetic ? "Synthetic example" : "Verified local source"}</span></div>
        <div className="decision-toolbar"><span aria-live="polite">{selected.length ? `${selected.length} ${selected.length===1 ? "action" : "actions"} selected` : "Select an action to review"}</span><div><button className="text-button" disabled={!selected.length || sending} onClick={() => choose([])}>Clear selection</button><button className="primary" disabled={!selected.length || !current || sending} onClick={e => {dialogTrigger.current=e.currentTarget;setConfirmOpen(true);}}>Review selected actions <ArrowRight size={16}/></button></div></div>
        {sending && !confirmOpen && <p className="decision-footnote" role="status">Sending your modeling request…</p>}
        {receipt && !confirmOpen && <div className="optimization-receipt" role="status"><CheckCircle2 size={19}/><p>Modeling request accepted. No workload change or savings has been verified.</p></div>}
        {actionError && !confirmOpen && <div className="optimization-error" role="alert">{actionError} Review the selected actions before retrying.</div>}
        {!actionableRows.length && <div className="empty decision-empty"><TriangleAlert size={18}/><span>No source-backed action is ready in this snapshot. Inspect the evidence or retry after the dataset refreshes.</span></div>}
        <div className="decision-scroll" role="region" aria-label="Cost optimization decision table" tabIndex={0}>
          <table className="decision-table">
            <caption className="sr-only">Select actions backed by an eligible cohort. GPU-time percentages use the full sample allocation as their denominator; row percentages overlap and must not be added.</caption>
            <thead><tr><th><input type="checkbox" aria-label="Select all available fixes" checked={!!available.length && available.every(id => selected.includes(id))} ref={el => { if(el) el.indeterminate = selected.length > 0 && !available.every(id => selected.includes(id)); }} disabled={!available.length || sending} onChange={e => choose(e.target.checked ? available : [])} /></th><th>Task</th><th>GPU time affected</th><th>Potential fix</th><th>Evidence</th></tr></thead>
            <tbody>{actionableRows.map(row => <tr key={row.id} className={selected.includes(row.id) ? "decision-selected" : ""}>
              <td><input type="checkbox" aria-label={`Select ${row.title}`} checked={selected.includes(row.id)} disabled={!row.affected_jobs || sending} onChange={e => choose(e.target.checked ? [...selected,row.id] : selected.filter(id => id !== row.id))} /></td>
              <th scope="row"><span className="decision-title">{row.title}</span><span className="decision-row-cost">{usd(row.allocated_gpu_hours * referencePrice)} <small>reference value</small></span>{row.id === "cpu-placement" && <span className="decision-pilot">Our first pilot</span>}{!row.affected_jobs && <span className="small muted">No eligible jobs in this sample</span>}</th>
              <td><strong className="decision-percentage">{percent(row.allocated_share_pct)}</strong><div className="decision-meter" aria-hidden="true"><span style={{width:`${row.allocated_share_pct}%`}} /></div></td>
              <td><p className="decision-fix">{taskSummary[row.id]?.fix ?? row.fix}</p><span className="row-readiness">{!row.affected_jobs ? "No eligible jobs" : row.id==="cpu-placement" && review ? "Scenario modeled · not measured" : "Needs testing"}</span>{row.id === "cpu-placement" && <button className="text-button pilot-open" aria-label="Compare CPU pilot" disabled={sending || !row.affected_jobs} onClick={openPilot}>Model <ArrowRight size={13}/></button>}</td>
              <td><a className="text-button" href={datasetHref("findings",{query:row.rule})}>{number(row.finding_count)} findings <ArrowRight size={13} /></a><details className="row-source-details"><summary>Details</summary><p>{row.fix}</p><p>Owner: {row.owner}</p><p>{number(row.allocated_gpu_hours)} GPU-hours · {number(row.affected_jobs)} jobs</p><p>{number(row.excluded_cancelled_jobs)} cancelled jobs excluded</p></details></td>
            </tr>)}</tbody>
          </table>
        </div>
        {!!inactiveRows.length && <details className="inactive-opportunities"><summary>{inactiveRows.length} checks have no eligible cohort in this snapshot</summary><div>{inactiveRows.map((row) => <article key={row.id}><strong>{row.title}</strong><span>No eligible jobs in this source window.</span><a href={datasetHref("findings",{query:row.rule})}>Inspect findings <ArrowRight size={13}/></a></article>)}</div></details>}
        <details className="decision-footnote"><summary>About the numbers</summary><p>Percentages use all recorded GPU-hours as the denominator. Task hours exclude cancellation and synthetic findings. Each selected job is counted once. Reference value uses $2.50/GPU-hour for the sample window; it is not a bill or savings estimate.</p></details>
      </section>
      {confirmOpen && <OptimizeDialog rows={selectedRows} share={visible.selection.share_pct} hours={visible.selection.gpu_hours} jobs={visible.selection.unique_jobs} overlap={visible.selection.overlapping_gpu_hours} sending={sending} error={actionError} receipt={receipt} ready={current} review={review} restoreFocus={dialogTrigger.current} onDownload={downloadReview} onProceed={optimize} onReturn={() => setConfirmOpen(false)} />}
      {pilotOpen && selected.includes("cpu-placement") && cpuRow && <CpuPilotPlanner key={visible.dataset_version} source={{version:visible.dataset_version,synthetic:visible.synthetic,cohortHours:cpuRow.allocated_gpu_hours,totalHours:visible.total_gpu_hours,gpuPrice:referencePrice}} onReview={setPilotReview} />}
      <details className="panel technical-decisions"><summary>About the optional 20% spending goal</summary><div className="optional-goal"><h2>What does a 20% cut mean?</h2><p>The hackathon brief asks for 20% lower spending: spend $80 for every $100 previously spent, while preserving research performance. This is an example, not the cluster’s bill. You can investigate opportunities without choosing a target first.</p><p>The pilot model compares against 20% of the historical sample’s reference value. It does not forecast next-quarter savings.</p></div></details>
    </>}
  </div>;
}
