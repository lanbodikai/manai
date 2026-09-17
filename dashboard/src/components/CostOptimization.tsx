import { useEffect, useRef, useState } from "react";
import { ArrowRight, CheckCircle2, CircleHelp, RefreshCw, SlidersHorizontal, TriangleAlert } from "lucide-react";
import type { DashboardApi } from "../api/types";
import { decisionPayload, sameFixes, type DecisionTable, type OptimizeReceipt, type OptimizeRequest } from "../api/optimization";
import { errorMessage } from "../api/validation";
import { number, usd } from "../format";
import { datasetHref, useDatasetCatalog } from "./DataExplorer";

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
  const [showAll, setShowAll] = useState(false);
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
  const shownRows = showAll ? visible?.rows : visible?.rows.slice(0,3);
  return <div className="optimization-page">
    <header className="page-header">
      <div><span className="eyebrow">FROM FINDINGS TO A SMALLER GPU BILL</span>
        <h1>Cost decisions</h1>
        <p>Understand the time. Choose a small change. Check the downside.</p>
      </div>
      <a className="secondary" href={datasetHref("findings")}>Browse findings <ArrowRight size={15} /></a>
    </header>
    <div className="optimization-context"><CircleHelp size={18} />
      <p><strong>Reference cost, not savings.</strong> Task amounts are recorded eligible GPU-hours × $2.50, the supplied 2026-Q3 reference price. They cover this sample window, not a month or an actual bill. Recoverable savings have not been measured.</p>
    </div>
    {error && <div className="panel error-state" role="alert"><TriangleAlert /><h2>Could not load the decision table</h2><p>{error}</p><button className="secondary" onClick={reload} disabled={sending}><RefreshCw size={15} /> Reload data</button></div>}
    {!visible && !error && <div className="panel" role="status">Reading verified findings and job hours…</div>}
    {visible && <>
      <section className="panel allocation-panel" aria-labelledby="allocation-heading">
        <div className="allocation-heading"><div><span className="eyebrow">1 · UNDERSTAND THE BASELINE</span><h2 id="allocation-heading">Where does our GPU time go?</h2><p>{catalog?.window_label} · Recorded allocation, not total cluster capacity</p></div><div><strong>{number(visible.total_gpu_hours)}</strong><span>GPU-hours in this sample</span></div></div>
        {catalog?.summary ? <>
          <div className="allocation-bar" aria-hidden="true">{outcomes.map(group => <span key={group.label} style={{width:`${visible.total_gpu_hours ? group.hours / visible.total_gpu_hours * 100 : 0}%`,background:group.color}} />)}</div>
          <div className="allocation-legend" role="group" aria-label="Explore recorded time by outcome">{outcomes.map(group => <button key={group.label} aria-pressed={activeOutcome === group.label} onClick={() => setActiveOutcome(group.label)}><span className="allocation-dot" style={{background:group.color}} /><span>{group.label}</span><strong>{percent(visible.total_gpu_hours ? group.hours / visible.total_gpu_hours * 100 : 0)}</strong></button>)}</div>
          <p className="allocation-note" aria-live="polite">{outcomes.find(group => group.label === activeOutcome)?.note}</p>
        </> : <p>Outcome breakdown unavailable for this dataset.</p>}
      </section>
      <section className="optimization-stats" aria-label="Optimization context">
        <div className="panel selected-stat"><span className="eyebrow">SELECTED FOR REVIEW</span><strong aria-live="polite">{current ? percent(visible.selection.share_pct) : "Updating…"}</strong><p>{current ? `${number(visible.selection.unique_jobs)} unique jobs · ${number(visible.selection.gpu_hours)} GPU-hours` : "Checking overlapping jobs"}<br />Each job counted once across your selection</p></div>
        <div className="panel"><span className="eyebrow">VERIFIED SAVINGS</span><strong className="unmodeled">Not modeled</strong><p>Recovery, replacement costs and performance effects<br />need a validated backend scenario.</p></div>
      </section>
      <section className="panel decision-panel" aria-labelledby="decision-heading">
        <div className="decision-heading"><div><span className="eyebrow">2 · CHOOSE WHAT TO TEST</span><h2 id="decision-heading">Start with a small, reversible change</h2><p>Three investigations to consider first—not a ranking of proven savings.</p></div>
          <span className="badge">{visible.synthetic ? "Synthetic decision example" : "Verified local source"}</span></div>
        <div className="decision-policy"><span>Cancelled jobs excluded</span><span>{number(visible.excluded_synthetic_findings)} synthetic findings excluded</span><span>Full historical sample, including resolved findings</span></div>
        <div className="decision-tasks">{shownRows?.map(row => <article key={row.id} className={`decision-task ${selected.includes(row.id) ? "task-selected" : ""}`} aria-label={row.title}>
          <input type="checkbox" aria-label={`Select ${row.title}`} checked={selected.includes(row.id)} disabled={!row.affected_jobs || sending} onChange={e => choose(e.target.checked ? [...selected,row.id] : selected.filter(id => id !== row.id))} />
          <div className="task-content"><div className="task-heading"><h3>{row.title}</h3><div className="task-metrics"><div className="task-reference-cost"><strong>{usd(row.allocated_gpu_hours * referencePrice)}</strong><span>Reference cost · not savings</span></div><div className="task-exposure"><strong>{percent(row.allocated_share_pct)}</strong><span>of recorded GPU time</span></div></div></div><p>{row.fix}</p><span className="decision-owner">Owner: {row.owner} · {number(row.affected_jobs)} eligible jobs</span>{!row.affected_jobs && <p>No eligible jobs in this sample.</p>}
          <details><summary>Risk and safeguards</summary><p>{row.risk}</p><p>{row.excluded_cancelled_jobs} cancelled jobs excluded from this opportunity.</p></details>
          <a className="text-button" href={datasetHref("findings",{query:row.rule})}>View {number(row.finding_count)} supporting findings <ArrowRight size={13} /></a></div>
        </article>)}</div>
        <button className="text-button show-opportunities" onClick={() => setShowAll(!showAll)} aria-expanded={showAll}>{showAll ? "Show fewer opportunities" : `Show ${Math.max(0,visible.rows.length-3)} more opportunities`}</button>
        <p className="decision-footnote">Opportunity percentages overlap. Your selected total counts each job only once; it is not an estimate of savings.</p>
      </section>
      <section className="panel optimization-action" aria-labelledby="selection-heading">
        <div className="optimization-selection"><span className="tile-icon blue"><SlidersHorizontal size={22} /></span><div><h2 id="selection-heading">{selected.length ? `${selected.length} ${selected.length === 1 ? "fix" : "fixes"} selected` : "Choose a fix to model"}</h2><p>{selectedRows.length ? selectedRows.map(r => r.title).join(" · ") : "Start with the CPU placement pilot, then compare other opportunities."}</p>
          {current && selected.length > 1 && <p className="overlap-note">{number(visible.selection.overlapping_gpu_hours)} duplicated GPU-hours removed from the combined exposure.</p>}</div></div>
        <div className="optimization-buttons"><button className="text-button" disabled={!selected.length || sending} onClick={() => choose([])}>Clear selection</button><button className="primary" onClick={optimize} disabled={!selected.length || !current || sending || !!receipt}>{sending ? "Sending request…" : receipt ? "Request accepted" : actionError ? "Retry optimization request" : "Model selected changes"}<ArrowRight size={16} /></button></div>
        <p className="optimization-action-note">Requests a backend cost/performance model. It does not move jobs, terminate sessions or change scheduling. Financial results stay unmodeled until the analysis service provides them.</p>
        {actionError && <div className="optimization-error" role="alert"><TriangleAlert size={18} /><div><strong>Optimization was not confirmed</strong><p>{actionError}</p><p>You can still inspect evidence and adjust your selection.</p><button className="text-button" onClick={reload}>Reload dataset</button></div></div>}
        {receipt && <div className="optimization-receipt" role="status"><CheckCircle2 size={19} /><div><strong>{receipt.synthetic ? "Synthetic example — request accepted" : "Backend accepted your modeling request"}</strong><p>Request {receipt.optimization_id}. Acceptance is not a completed optimization or verified savings.</p></div></div>}
      </section>
      <details className="panel technical-decisions"><summary>View detailed decision table and accounting method</summary>
        <div className="decision-scroll" role="region" aria-label="Cost optimization decision table" tabIndex={0}>
          <table className="decision-table">
            <caption className="sr-only">Select suggested fixes. GPU-time percentages use the full sample allocation as their denominator; row percentages overlap and must not be added.</caption>
            <thead><tr><th><input type="checkbox" aria-label="Select all available fixes" checked={!!available.length && available.every(id => selected.includes(id))} ref={el => { if(el) el.indeterminate = selected.length > 0 && !available.every(id => selected.includes(id)); }} disabled={!available.length || sending} onChange={e => choose(e.target.checked ? available : [])} /></th><th>Opportunity / owner</th><th>Share of sample GPU time</th><th>Potential fix / trade-off</th><th>Evidence</th></tr></thead>
            <tbody>{visible.rows.map(row => <tr key={row.id} className={selected.includes(row.id) ? "decision-selected" : ""}>
              <td><input type="checkbox" aria-label={`Select ${row.title} in detailed table`} checked={selected.includes(row.id)} disabled={!row.affected_jobs || sending} onChange={e => choose(e.target.checked ? [...selected,row.id] : selected.filter(id => id !== row.id))} /></td>
              <th scope="row"><span className="decision-title">{row.title}</span><span className="decision-owner">{row.owner}</span>{row.id === "cpu-placement" && <span className="decision-pilot">Our first pilot</span>}{!row.affected_jobs && <span className="small muted">No eligible jobs in this sample</span>}</th>
              <td><strong className="decision-percentage">{percent(row.allocated_share_pct)}</strong><div className="decision-meter" aria-hidden="true"><span style={{width:`${row.allocated_share_pct}%`}} /></div><span className="decision-hours">{number(row.allocated_gpu_hours)} GPU-hours · {number(row.affected_jobs)} jobs</span></td>
              <td><p className="decision-fix">{row.fix}</p><details><summary>What could go wrong?</summary><p>{row.risk}</p></details></td>
              <td><a className="text-button" href={datasetHref("findings",{query:row.rule})}>{number(row.finding_count)} findings <ArrowRight size={13} /></a><span className="small muted">{row.excluded_cancelled_jobs ? `${number(row.excluded_cancelled_jobs)} cancelled jobs excluded` : "Source evidence"}</span></td>
            </tr>)}</tbody>
          </table>
        </div>
        <p className="decision-footnote">The denominator includes all recorded allocation, including cancelled jobs. Row numerators exclude cancellation and synthetic findings. Hours come from unique source jobs, not summed finding impacts; they are not necessarily recoverable.</p>
      </details>
    </>}
  </div>;
}
