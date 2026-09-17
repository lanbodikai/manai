import { useEffect, useRef, useState } from "react";
import { ArrowRight, CheckCircle2, CircleHelp, RefreshCw, SlidersHorizontal, TriangleAlert } from "lucide-react";
import type { DashboardApi } from "../api/types";
import { decisionPayload, sameFixes, type DecisionTable, type OptimizeReceipt, type OptimizeRequest } from "../api/optimization";
import { errorMessage } from "../api/validation";
import { number, usd } from "../format";
import { datasetHref, useDatasetCatalog } from "./DataExplorer";
import { CpuPilotPlanner } from "./CpuPilotPlanner";

export const percent = (value: number) => value > 0 && value < 0.1 ? "<0.1%" : `${value.toFixed(1)}%`;

export function CostOptimization({ api, modelAvailable = true }: { api: DashboardApi; modelAvailable?: boolean }) {
  const { catalog, error: catalogError, retry } = useDatasetCatalog(api);
  const [table, setTable] = useState<DecisionTable | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [sending, setSending] = useState(false);
  const [actionError, setActionError] = useState("");
  const [receipt, setReceipt] = useState<OptimizeReceipt | null>(null);
  const [pilotOpen, setPilotOpen] = useState(false);
  const [activeOutcome, setActiveOutcome] = useState("Finished");
  // Verified against the supplied API /v1/price-book (2026-Q3), 2026-09-17. Reference pricing, not an actual bill.
  const referencePrice = 2.5;
  const pending = useRef<OptimizeRequest | null>(null);
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
  const available = visible?.rows.filter(r => r.affected_jobs > 0).map(r => r.id) ?? [];
  const selectedRows = visible?.rows.filter(r => selected.includes(r.id)) ?? [];
  function choose(next: string[]) {
    if (sending) return;
    setSelected(next);
    if(!next.includes("cpu-placement")) setPilotOpen(false);
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
  return <div className="optimization-page">
    <header className="page-header">
      <div><span className="eyebrow">FROM FINDINGS TO A SMALLER GPU BILL</span>
        <h1>Optimization opportunities</h1>
        <p>Review the tasks. Compare the impact. Choose what to investigate.</p>
      </div>
      <a className="secondary" href={datasetHref("findings")}>Browse findings <ArrowRight size={15} /></a>
    </header>
    <div className="optimization-context"><CircleHelp size={18} />
      <p><strong>Cost involved is not money saved.</strong> Amounts beside a task show the estimated value of the computing time involved. Savings still need investigation.</p>
    </div>
    {error && <div className="panel error-state" role="alert"><TriangleAlert /><h2>Could not load the decision table</h2><p>{error}</p><button className="secondary" onClick={reload} disabled={sending}><RefreshCw size={15} /> Reload data</button></div>}
    {!visible && !error && <div className="panel" role="status">Reading verified findings and job hours…</div>}
    {visible && <>
      <section className="panel decision-panel" aria-labelledby="decision-heading"><div className="decision-heading"><div><h2 id="decision-heading">Choose an opportunity to investigate</h2><p>Select a task, review the proposed fix and check the risk before making a change.</p></div><span className="badge">{visible.synthetic ? "Synthetic example" : "Verified local source"}</span></div>
        <div className="decision-scroll" role="region" aria-label="Cost optimization decision table" tabIndex={0}>
          <table className="decision-table">
            <caption className="sr-only">Select suggested fixes. GPU-time percentages use the full sample allocation as their denominator; row percentages overlap and must not be added.</caption>
            <thead><tr><th><input type="checkbox" aria-label="Select all available fixes" checked={!!available.length && available.every(id => selected.includes(id))} ref={el => { if(el) el.indeterminate = selected.length > 0 && !available.every(id => selected.includes(id)); }} disabled={!available.length || sending} onChange={e => choose(e.target.checked ? available : [])} /></th><th>Opportunity / owner</th><th>Share of sample GPU time</th><th>Potential fix / trade-off</th><th>Evidence</th></tr></thead>
            <tbody>{visible.rows.map(row => <tr key={row.id} className={selected.includes(row.id) ? "decision-selected" : ""}>
              <td><input type="checkbox" aria-label={`Select ${row.title}`} checked={selected.includes(row.id)} disabled={!row.affected_jobs || sending} onChange={e => choose(e.target.checked ? [...selected,row.id] : selected.filter(id => id !== row.id))} /></td>
              <th scope="row"><span className="decision-title">{row.title}</span><span className="decision-owner">{row.owner}</span><span className="decision-row-cost">{usd(row.allocated_gpu_hours * referencePrice)} <small>reference cost · not savings</small></span>{row.id === "cpu-placement" && <span className="decision-pilot">Our first pilot</span>}{!row.affected_jobs && <span className="small muted">No eligible jobs in this sample</span>}</th>
              <td><strong className="decision-percentage">{percent(row.allocated_share_pct)}</strong><div className="decision-meter" aria-hidden="true"><span style={{width:`${row.allocated_share_pct}%`}} /></div><span className="decision-hours">{number(row.allocated_gpu_hours)} GPU-hours · {number(row.affected_jobs)} jobs</span></td>
              <td><p className="decision-fix">{row.fix}</p>{row.id === "cpu-placement" && <button className="text-button pilot-open" disabled={sending} onClick={() => { if(!selected.includes(row.id)) choose([...selected,row.id]); setPilotOpen(true); setTimeout(() => document.getElementById("cpu-pilot-planner")?.focus(),0); }}>Compare CPU pilot <ArrowRight size={13}/></button>}<details><summary>What could go wrong?</summary><p>{row.risk}</p></details></td>
              <td><a className="text-button" href={datasetHref("findings",{query:row.rule})}>{number(row.finding_count)} findings <ArrowRight size={13} /></a><span className="small muted">{row.excluded_cancelled_jobs ? `${number(row.excluded_cancelled_jobs)} cancelled jobs excluded` : "Source evidence"}</span></td>
            </tr>)}</tbody>
          </table>
        </div>
        <p className="decision-footnote">The denominator includes all recorded allocation, including cancelled jobs. Row numerators exclude cancellation and synthetic findings. Hours come from unique source jobs, not summed finding impacts; they are not necessarily recoverable.</p>
      </section>
      <section className="optimization-stats compact-selection" aria-label="Optimization context">
        <div className="panel selected-stat"><span className="eyebrow">SELECTED FOR REVIEW</span><strong aria-live="polite">{current ? percent(visible.selection.share_pct) : "Updating…"}</strong><p>{current ? `${number(visible.selection.unique_jobs)} unique jobs · ${number(visible.selection.gpu_hours)} GPU-hours` : "Checking overlapping jobs"}<br />Each job counted once across your selection</p></div>
        <div className="panel"><span className="eyebrow">SAVINGS STATUS</span><strong className="unmodeled">Estimate needed</strong><p>Percentages describe affected GPU time, not guaranteed savings. Select Compare CPU pilot to assess its possible benefit and risk.</p></div>
      </section>
      <section className="panel optimization-action" aria-labelledby="selection-heading">
        <div className="optimization-selection"><span className="tile-icon blue"><SlidersHorizontal size={22} /></span><div><h2 id="selection-heading">{selected.length ? `${selected.length} ${selected.length === 1 ? "fix" : "fixes"} selected` : "Choose a fix to model"}</h2><p>{selectedRows.length ? selectedRows.map(r => r.title).join(" · ") : "Start with the CPU placement pilot, then compare other opportunities."}</p>
          {current && selected.length > 1 && <p className="overlap-note">{number(visible.selection.overlapping_gpu_hours)} duplicated GPU-hours removed from the combined exposure.</p>}</div></div>
        <div className="optimization-buttons"><button className="text-button" disabled={!selected.length || sending} onClick={() => choose([])}>Clear selection</button><button className="primary" onClick={optimize} disabled={!modelAvailable || !selected.length || !current || sending || !!receipt}>{!modelAvailable ? "Multi-fix modeling not yet available" : sending ? "Sending request…" : receipt ? "Request accepted" : actionError ? "Retry optimization request" : "Model selected changes"}<ArrowRight size={16} /></button></div>
        <p className="optimization-action-note">{modelAvailable ? "Requests the separate backend model using selected fix IDs only." : "This table supports read-only investigation. Multi-fix calculation is not connected; use Scenario for the audited CPU pilot."} Local CPU planner assumptions are not submitted by this button. It does not approve or execute a pilot. Canonical financial results remain unavailable until the analysis service provides them.</p>
        {actionError && <div className="optimization-error" role="alert"><TriangleAlert size={18} /><div><strong>Optimization was not confirmed</strong><p>{actionError}</p><p>You can still inspect evidence and adjust your selection.</p><button className="text-button" onClick={reload}>Reload dataset</button></div></div>}
        {receipt && <div className="optimization-receipt" role="status"><CheckCircle2 size={19} /><div><strong>{receipt.synthetic ? "Synthetic example — request accepted" : "Backend accepted your modeling request"}</strong><p>Request {receipt.optimization_id}. Acceptance is not a completed optimization or verified savings.</p></div></div>}
      </section>
      {pilotOpen && selected.includes("cpu-placement") && cpuRow && <CpuPilotPlanner key={visible.dataset_version} source={{version:visible.dataset_version,synthetic:visible.synthetic,cohortHours:cpuRow.allocated_gpu_hours,totalHours:visible.total_gpu_hours,gpuPrice:referencePrice}} />}
      <details className="panel technical-decisions"><summary>View spending goal and GPU-time breakdown</summary><div className="optional-goal"><h2>What does a 20% cut mean?</h2><p>The hackathon brief asks for 20% lower spending: spend $80 for every $100 previously spent, while preserving research performance. This is an example, not the cluster’s bill. You can investigate opportunities without choosing a target first.</p></div>      <section className="panel allocation-panel" aria-labelledby="allocation-heading">
        <div className="allocation-heading"><div><span className="eyebrow">1 · UNDERSTAND THE BASELINE</span><h2 id="allocation-heading">Where does our GPU time go?</h2><p>{catalog?.window_label} · Recorded allocation, not total cluster capacity</p></div><div><strong>{number(visible.total_gpu_hours)}</strong><span>GPU-hours in this sample</span></div></div>
        {catalog?.summary ? <>
          <div className="allocation-bar" aria-hidden="true">{outcomes.map(group => <span key={group.label} style={{width:`${visible.total_gpu_hours ? group.hours / visible.total_gpu_hours * 100 : 0}%`,background:group.color}} />)}</div>
          <div className="allocation-legend" role="group" aria-label="Explore recorded time by outcome">{outcomes.map(group => <button key={group.label} aria-pressed={activeOutcome === group.label} onClick={() => setActiveOutcome(group.label)}><span className="allocation-dot" style={{background:group.color}} /><span>{group.label}</span><strong>{percent(visible.total_gpu_hours ? group.hours / visible.total_gpu_hours * 100 : 0)}</strong></button>)}</div>
          <p className="allocation-note" aria-live="polite">{outcomes.find(group => group.label === activeOutcome)?.note}</p>
        </> : <p>Outcome breakdown unavailable for this dataset.</p>}
      </section>
      </details>
    </>}
  </div>;
}
