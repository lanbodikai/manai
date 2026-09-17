import {useEffect, useMemo, useRef, useState} from "react";
import {ArrowDownToLine, FlaskConical, ShieldCheck, TriangleAlert} from "lucide-react";
import type {Audit, DashboardApi} from "../api/types";
import {ApiError, errorMessage} from "../api/validation";
import {createPilotRecoveryApi, type PilotBaseline, type PilotBaselines, type PilotOutcome,
  type PilotRecoveryApi, type PilotSimulation, type PilotSimulationRequest} from "../api/pilot-recovery";

interface Draft {
  proposal: string; correctness: string; vcpus: string; hours: string; cpuPrice: string;
  maxHours: string; maxSpend: string; setup: string; queue: string; hostIncluded: boolean;
  outcome: PilotOutcome; failure: string; recovery: string;
}
const initialDraft: Draft = {proposal: "", correctness: "", vcpus: "4", hours: "", cpuPrice: "",
  maxHours: "", maxSpend: "", setup: "", queue: "", hostIncluded: false,
  outcome: "success", failure: "", recovery: "Owner must verify the original configuration, GPU capacity and reference outputs. Any recovery requires a full original GPU rerun; no checkpoint is verified."};
interface Saved {result: PilotSimulation; draft: Draft}
const snapshot = <T,>(value: T): T => JSON.parse(JSON.stringify(value));
const decimal = (value: number | null) => value === null ? "Unknown" : value.toLocaleString("en-US", {maximumFractionDigits: 2});
const dollars = (value: number | null) => value === null ? "Unknown" : new Intl.NumberFormat("en-US", {style: "currency", currency: "USD"}).format(value);
const hours = (value: number | null) => value === null ? "Unknown" : `${decimal(value)} h`;
const statusLabel = (status: PilotSimulation["status"]) => status === "paused" ? "Paused — owner action required" : status === "recovered" ? "Failed trial — recovery assumed" : "Successful trial — assumed outcome";
function numeric(value: string, label: string, nullable = false): number | null {
  if (!value.trim()) {if (nullable) return null; throw new Error(`Enter ${label}.`);}
  const result = Number(value);
  if (!Number.isFinite(result) || result < 0) throw new Error(`${label} must be a finite, nonnegative number.`);
  return result;
}
function buildRequest(draft: Draft, baseline: PilotBaseline): PilotSimulationRequest {
  return {client_request_id: crypto.randomUUID(), baseline_evidence_id: baseline.evidence_id,
    proposal: draft.proposal.trim(), correctness_check: draft.correctness.trim(),
    cpu_vcpus: numeric(draft.vcpus, "CPU vCPUs")!, cpu_hours: numeric(draft.hours, "CPU trial hours")!,
    cpu_vcpu_hour_usd: numeric(draft.cpuPrice, "CPU price", true),
    max_runtime_hours: numeric(draft.maxHours, "maximum trial hours")!,
    max_trial_spend_usd: numeric(draft.maxSpend, "maximum trial spend")!,
    setup_cost_usd: numeric(draft.setup, "setup cost", true), extra_queue_hours: numeric(draft.queue, "extra queue hours", true),
    baseline_host_costs_included: draft.hostIncluded, outcome: draft.outcome,
    failure_reason: draft.outcome === "success" ? "" : draft.failure.trim(), recovery_note: draft.recovery.trim()};
}
export function PilotRecoveryPanel({api, audit: suppliedAudit = null, pilotApi: suppliedPilotApi}: {
  api: DashboardApi; audit?: Audit | null; pilotApi?: PilotRecoveryApi;
}) {
  const pilotApi = useMemo(() => suppliedPilotApi ?? createPilotRecoveryApi(), [suppliedPilotApi]);
  const [scopeAudit, setScopeAudit] = useState<Audit | null>(null);
  const [baselines, setBaselines] = useState<PilotBaselines | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState<Draft>(initialDraft);
  const [history, setHistory] = useState<Saved[]>([]);
  const [viewedId, setViewedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [reload, setReload] = useState(0);
  const generation = useRef(0);
  const running = useRef<AbortController | null>(null);
  useEffect(() => {
    const run = ++generation.current, controller = new AbortController();
    running.current?.abort(); setBusy(false); setLoading(true); setLoadError("");
    setBaselines(null); setScopeAudit(null); setSelectedId("");
    void (async () => {
      let current = suppliedAudit;
      if (!current) {
        const [health, overview] = await Promise.all([api.getHealth(), api.getOverview()]);
        if (run !== generation.current) return;
        if (health.data_status !== "ready" || !health.data_fingerprint || health.data_fingerprint !== overview.provenance.data_fingerprint)
          throw new ApiError("PILOT_DATA_NOT_READY", "Baseline evidence is unavailable or has changed. Reload when the analysis data is ready.", 409, true);
        const requestId = crypto.randomUUID();
        current = await api.createAudit({client_request_id: requestId,
          expected_data_fingerprint: health.data_fingerprint, recommendation_id: "cpu-placement-pilot",
          scenario: {recovery_fraction: {low: 0, point: 0, high: 0}, usd_per_gpu_hour: overview.usd_per_gpu_hour,
            cancelled_policy: "exclude", interval_kind: "scenario", assumption_note: "Baseline lookup only; no cohort recovery assumed"}});
        if (current.client_request_id !== requestId || current.provenance.data_fingerprint !== health.data_fingerprint ||
            current.provenance.source_version !== overview.provenance.source_version || current.provenance.synthetic !== overview.provenance.synthetic)
          throw new ApiError("PILOT_SCOPE_MISMATCH", "The baseline lookup returned a different evidence snapshot.", 409);
      }
      if (run !== generation.current) return;
      const result = await pilotApi.getBaselines(current, controller.signal);
      if (run !== generation.current) return;
      setScopeAudit(snapshot(current)); setBaselines(snapshot(result)); setSelectedId(result.items[0]?.evidence_id ?? "");
    })().catch(error => {if (run === generation.current && !controller.signal.aborted) setLoadError(errorMessage(error));})
      .finally(() => {if (run === generation.current) setLoading(false);});
    return () => {++generation.current; controller.abort(); running.current?.abort();};
  }, [api, suppliedAudit, pilotApi, reload]);

  const baseline = baselines?.items.find(item => item.evidence_id === selectedId);
  const viewed = history.find(item => item.result.simulation_id === viewedId);
  const dirty = viewed && (JSON.stringify(draft) !== JSON.stringify(viewed.draft) || selectedId !== viewed.result.baseline.evidence_id || scopeAudit?.audit_id !== viewed.result.audit_id);
  function change<K extends keyof Draft>(key: K, value: Draft[K]) {setDraft(before => ({...before, [key]: value}));}
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (!baseline || !scopeAudit || busy) return;
    setSubmitError("");
    const run = generation.current, controller = new AbortController(); running.current = controller;
    const savedDraft = snapshot(draft), savedBaseline = snapshot(baseline), savedAudit = snapshot(scopeAudit);
    try {
      const request = buildRequest(savedDraft, savedBaseline); setBusy(true);
      const result = await pilotApi.simulate(savedAudit, savedBaseline, request, controller.signal);
      if (run !== generation.current || controller.signal.aborted) return;
      setHistory(before => [...before, {result: snapshot(result), draft: savedDraft}]);
      setViewedId(result.simulation_id);
    } catch (error) {if (run === generation.current && !controller.signal.aborted) setSubmitError(errorMessage(error));}
    finally {if (run === generation.current) setBusy(false);}
  }
  function download() {
    const payload = {format: "manai-pilot-recovery-simulation-history-v0.1", simulation_only: true,
      execution_performed: false, for_claims: false, independent_alternatives: true,
      notice: "Local scenario snapshots, not actual runs or claims. Previous failed alternatives are not charged again.",
      selected_baseline_scope: baselines ? {feature_version: baselines.feature_version,
        audit_id: baselines.audit_id, audit_client_request_id: baselines.audit_client_request_id,
        data_fingerprint: baselines.data_fingerprint, source_version: baselines.source_version,
        synthetic: baselines.synthetic, simulation_only: baselines.simulation_only} : null,
      selected_baseline: baseline ?? null, draft_not_simulated: snapshot(draft),
      selected_simulation_id: viewedId, history: snapshot(history)};
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], {type: "application/json"}));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = "pilot-recovery-simulations.json"; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const field = (key: keyof Draft, label: string, optional = false, note?: string) => <label>{label}
    <input type="number" min="0" step={key === "vcpus" ? "1" : "any"} value={String(draft[key])}
      placeholder={optional ? "Unknown" : "Required"} onChange={event => change(key, event.target.value)} />
    {note && <small>{note}</small>}</label>;
  return <section className="pr-panel" aria-labelledby="pilot-recovery-title">
    <header className="pr-heading"><div><span className="eyebrow">One job · before and after</span>
      <h1 id="pilot-recovery-title">Pilot &amp; Recovery</h1>
      <p>Explore a CPU trial, its limits, and the cost of falling back to the original GPU job.</p></div><span className="badge">Simulation only · no workloads run</span></header>
    <div className="pr-notice">Low GPU use identifies a candidate, not proof it can run on a CPU. Correctness, recovery availability and savings remain unverified. These estimates come from the analysis service; the optional AI reviewer is not required.</div>
    {loading && <p role="status">Loading eligible historical jobs…</p>}
    {loadError && <div className="pr-error" role="alert">{loadError}<div className="pr-actions"><button className="secondary" onClick={() => setReload(value => value + 1)}>Retry baseline lookup</button></div></div>}
    {!loading && baselines && <p className="pr-notice">{suppliedAudit ? "Using the current audit’s evidence and GPU reference rate." : "Baseline lookup only; no cohort recovery assumed. This panel has its own audit and does not change your cohort claim."} {baselines.synthetic ? "Synthetic source — illustrative data." : "Historical source evidence."} Source: {baselines.source_version}.</p>}
    {!loading && baselines && !baselines.items.length && <div className="panel pr-card"><h2>No eligible job baseline</h2><p>The analysis service returned no eligible jobs. No baseline has been invented.</p></div>}
    <div className="pr-grid">
      <form className="panel pr-card" onSubmit={submit} aria-label="Pilot assumptions" noValidate>
        <h2>1. Preserve the original job</h2><p>Select historical evidence to keep with this simulation.</p>
        <label>Historical job<select value={selectedId} onChange={event => setSelectedId(event.target.value)} disabled={loading || !baselines?.items.length}>
          {!baselines?.items.length && <option value="">No baseline available</option>}
          {baselines?.items.map(item => <option key={item.evidence_id} value={item.evidence_id}>{item.source_job_id}{item.synthetic ? " · synthetic" : ""}</option>)}
        </select></label>
        {baseline && <div className="pr-baseline"><strong>Frozen baseline for this proposal</strong><dl>
          <dt>Original GPU allocation</dt><dd>{decimal(baseline.gpu_count)} GPUs</dd>
          <dt>Recorded GPU-hours</dt><dd>{hours(baseline.recorded_gpu_hours)}</dd>
          <dt>Original elapsed time</dt><dd>{hours(baseline.elapsed_hours)}</dd>
          <dt>GPU-hour reference rate</dt><dd>{dollars(baseline.usd_per_gpu_hour)} / GPU-hour</dd>
          <dt>Original reference cost</dt><dd>{dollars(baseline.original_reference_cost_usd)}</dd></dl>
          {!!baseline.missing_fields.length && <p>Unknown baseline fields: {baseline.missing_fields.join(", ")}. Related results may remain unknown.</p>}
          <small>No executable configuration, reference output or verified checkpoint is included in this evidence.</small>
        </div>}
        <fieldset><legend>2. Propose a bounded CPU trial</legend>
          <label>Proposed change<textarea maxLength={2000} value={draft.proposal} onChange={event => change("proposal", event.target.value)} placeholder="Describe the CPU configuration to test." /></label>
          <label>Correctness check<textarea aria-label="Correctness check" maxLength={2000} value={draft.correctness} onChange={event => change("correctness", event.target.value)} placeholder="What reference output and tolerance must match?" /><small>A proposed check only; this simulation does not execute it.</small></label>
          <div className="pr-fields">{field("vcpus", "CPU vCPUs")}{field("hours", "Requested CPU trial hours")}
            {field("maxHours", "Maximum trial hours")}{field("maxSpend", "Maximum trial spend ($)")}</div>
          <small>The trial cap includes CPU time and setup. Full recovery spending is outside this cap. Limits are enforced in the simulation only.</small>
        </fieldset>
        <fieldset><legend>3. Choose an assumed outcome</legend>
          <label>Assumed outcome<select value={draft.outcome} onChange={event => change("outcome", event.target.value as PilotOutcome)}>
            <option value="success">CPU trial succeeds</option><option value="failure_recovered">CPU trial fails; original GPU rerun is available</option><option value="failure_unavailable">CPU trial fails; recovery is unavailable</option>
          </select></label>
          {draft.outcome !== "success" && <label>Failure reason (assumption)<textarea maxLength={2000} value={draft.failure} onChange={event => change("failure", event.target.value)} placeholder="For example, required GPU-only dependency." /></label>}
          <small>If a limit stops an assumed successful trial, the result changes to failure with a full GPU rerun assumed. A stopped run is never displayed as successful.</small>
        </fieldset>
        <fieldset><legend>4. State the costs and recovery assumptions</legend><div className="pr-fields">
          {field("cpuPrice", "CPU price ($ per vCPU-hour)", true)}{field("setup", "Setup cost ($)", true)}
          {field("queue", "Extra queue time (hours)", true)}</div>
          <small>Leave unknown values blank. Enter 0 only when you assume zero cost or no extra wait.</small>
          <label className="pr-check"><input type="checkbox" checked={draft.hostIncluded} onChange={event => change("hostIncluded", event.target.checked)} />I assume the original GPU reference rate includes its host and CPU costs.</label>
          <small>Without a comparable pricing boundary, net benefit stays unknown. These are reference dollars, not a bill or verified cash savings.</small>
          <details><summary>View recovery and evidence details</summary>
            <p>Recovery strategy: rerun the full original GPU job. No verified checkpoint is available, so no checkpoint saving is claimed.</p>
            <label>Recovery assumption / owner action<textarea maxLength={2000} value={draft.recovery} onChange={event => change("recovery", event.target.value)} /></label>
            {baseline && <p>Evidence ID: {baseline.evidence_id}. GPU utilization average: {decimal(baseline.sm_util_avg)}%; maximum: {decimal(baseline.sm_util_max)}%. Recorded maximum GPU memory: {baseline.max_gpu_mem_used === null ? "Unknown" : `${decimal(baseline.max_gpu_mem_used)} bytes`}.</p>}
            {baselines?.limitations.map((item, index) => <p key={index}>{item}</p>)}
          </details>
        </fieldset>
        {submitError && <div className="pr-error" role="alert">{submitError}</div>}
        <div className="pr-actions"><button type="submit" className="primary" disabled={!baseline || !scopeAudit || busy || loading}><FlaskConical size={16}/>{busy ? "Calculating simulation…" : history.length ? "Simulate revised alternative" : "Simulate this pilot"}</button></div>
      </form>
      <div>
        <section className="panel pr-card" aria-label="Saved simulation result">
          <h2>What happens under these assumptions?</h2>
          {viewed ? <>
            {dirty && <p className="pr-dirty" role="status">Pending draft changes. The saved result below still uses its original assumptions; simulate again to create a separate alternative.</p>}
            <div className="pr-state" data-paused={viewed.result.status === "paused"}>
              {viewed.result.status === "paused" ? <TriangleAlert size={22}/> : <ShieldCheck size={22}/>}
              <div><h3>{statusLabel(viewed.result.status)}</h3><p>Historical job {viewed.result.baseline.source_job_id} · simulation {history.indexOf(viewed) + 1}</p></div>
            </div>
            <p><strong>Saved proposal:</strong> {viewed.result.inputs.proposal}</p>
            {viewed.result.failure_details.selected_outcome_changed && <p className="pr-dirty">A trial limit overrode your selected success. This result assumes a full original GPU rerun.</p>}
            {viewed.result.failure_details.effective_failure_reason && <p><strong>Failure / stop:</strong> {viewed.result.failure_details.effective_failure_reason}</p>}
            {viewed.result.stop_reason && <p><strong>Stop reason:</strong> {viewed.result.stop_reason.replaceAll("_", " ")}</p>}
            {viewed.result.limits.spend_limit_status === "unverified" && <p className="pr-notice">Spending limit unverified: an unknown cost prevents confirming the full trial budget. Any known-cost or runtime stop still applies.</p>}
            {viewed.result.status === "paused" && <p className="pr-notice">Next owner action: confirm the original configuration, capacity, inputs and reference outputs before retrying. Completion and total recovery cost remain unknown until a recovery plan is available.</p>}
            <ol className="pr-timeline" aria-label="Simulated sequence">{viewed.result.timeline.map(item => <li key={item.step}><strong>{item.step[0].toUpperCase() + item.step.slice(1)} · {item.status.replaceAll("_", " ")}</strong><span>{item.detail}</span></li>)}</ol>
            <div className="pr-summary"><h3>Reference cost comparison</h3><dl>
              <dt>Original job</dt><dd>{dollars(viewed.result.costs.original_cost_usd)}</dd>
              <dt>CPU trial + setup</dt><dd>{dollars(viewed.result.costs.trial_cost_usd)}</dd>
              <dt>Full GPU recovery</dt><dd>{dollars(viewed.result.costs.recovery_cost_usd)}</dd>
              <dt>Cost so far in this alternative</dt><dd>{dollars(viewed.result.costs.cost_so_far_usd)}</dd>
              <dt>Total cost to complete</dt><dd>{dollars(viewed.result.costs.total_cost_to_complete_usd)}</dd>
              <dt>Net benefit (negative means extra cost)</dt><dd>{dollars(viewed.result.costs.net_benefit_usd)}</dd>
              <dt>Completion change (positive means later)</dt><dd>{hours(viewed.result.timing.completion_change_hours)}</dd>
              <dt>GPU-hours released</dt><dd>{hours(viewed.result.capacity.released_gpu_hours)}</dd></dl></div>
            <details><summary>View saved inputs, limits and calculation details</summary>
              <p>Correctness check proposed: {viewed.result.inputs.correctness_check}</p>
              <p>Trial duration: requested {hours(viewed.result.timing.requested_cpu_hours)}; effective {hours(viewed.result.timing.effective_cpu_hours)}. Runtime limit: {hours(viewed.result.limits.max_runtime_hours)}.</p>
              <p>Trial spending limit: {dollars(viewed.result.limits.max_trial_spend_usd)}; status: {viewed.result.limits.spend_limit_status.replaceAll("_", " ")}. Recovery spending is excluded.</p>
              <p>Original elapsed: {hours(viewed.result.timing.baseline_elapsed_hours)}. Run-time change excluding queue: {hours(viewed.result.timing.run_time_change_hours_excluding_queue)}. Extra queue: {hours(viewed.result.timing.extra_queue_hours)}.</p>
              <p>Recovery: {viewed.result.recovery.strategy.replaceAll("_", " ")}. {viewed.result.recovery.note} Checkpoint verified: no.</p>
              <p>Evidence: {viewed.result.baseline.evidence_id}. Source: {viewed.result.source_version}. Snapshot: {viewed.result.data_fingerprint}.</p>
              {viewed.result.calculator_proof.map(item => <p key={item.quantity}><strong>{item.quantity}:</strong> {item.formula} = {dollars(item.value)}</p>)}
              <ul className="pr-result-notes">{viewed.result.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>
            </details>
            {!!viewed.result.possible_causes.length && <div className="pr-hypotheses"><strong>Possible causes — unverified hypotheses</strong><ul>{viewed.result.possible_causes.map((item, index) => <li key={index}>{item.hypothesis}<br/><strong>Next check:</strong> {item.next_check}</li>)}</ul></div>}
            <div className="pr-actions"><button type="button" className="secondary" disabled={viewed.result.audit_id !== scopeAudit?.audit_id || !baselines?.items.some(item => item.evidence_id === viewed.result.baseline.evidence_id)} onClick={() => {setDraft(snapshot(viewed.draft)); setSelectedId(viewed.result.baseline.evidence_id);}}>Revise this saved alternative</button></div>
          </> : <div className="pr-empty"><FlaskConical size={30}/><h3>Compare before you try it</h3><p>The analysis service will return a bounded scenario. No workload starts when you press Simulate.</p></div>}
        </section>
        <section className="panel pr-card pr-history" aria-label="Simulation history"><h2>Preserve the reasoning</h2>
          <p>History lives in this page and clears on page reload. Download it before leaving.</p>
          <p>Each result is an independent alternative. A previous failed simulation is not charged again. This export is not claims.json or a record of actual runs.</p>
          <ul className="pr-history-list">{history.map((item, index) => <li key={item.result.simulation_id}><button type="button" aria-pressed={viewedId === item.result.simulation_id} onClick={() => setViewedId(item.result.simulation_id)}><span>Alternative {index + 1}<small>{item.result.baseline.source_job_id} · {item.result.inputs.proposal}</small></span><span className="pr-history-outcome">{statusLabel(item.result.status)}</span></button></li>)}</ul>
          <div className="pr-actions"><button type="button" className="secondary" disabled={!baseline && !history.length} onClick={download}><ArrowDownToLine size={16}/>Download simulation history</button></div>
        </section>
      </div>
    </div>
  </section>;
}
