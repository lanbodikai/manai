import { useEffect, useState } from "react";
import type { Audit, DashboardApi, Scenario, Schemas } from "../api/types";
import { errorMessage, validateAuditRequest } from "../api/validation";
import { number, usd } from "../format";

type Pilot = NonNullable<Scenario["cpu_pilot"]>;

/** Single-job assumptions go to A; the browser never computes financial results. */
export function CpuPilot({ api, audit, busy, onSubmit, onEvidence }: {
  api: DashboardApi; audit: Audit; busy: boolean;
  onSubmit: (scenario: Scenario) => void; onEvidence: (id: string) => void;
}) {
  const saved = audit.scenario.cpu_pilot;
  const [jobs, setJobs] = useState<Schemas["EvidenceRef"][]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [baseline, setBaseline] = useState(saved?.baseline_evidence_id ?? "");
  const [mode, setMode] = useState<Pilot["mode"]>(saved?.mode ?? "replacement_success");
  const [vcpus, setVcpus] = useState(saved ? String(saved.cpu_vcpus) : "");
  const [hours, setHours] = useState(saved ? String(saved.cpu_hours) : "");
  const [price, setPrice] = useState(saved?.cpu_vcpu_hour_usd == null ? "" : String(saved.cpu_vcpu_hour_usd));
  const [queue, setQueue] = useState(saved?.extra_queue_hours == null ? "" : String(saved.extra_queue_hours));
  const [cap, setCap] = useState(saved?.trial_cap_hours == null ? "" : String(saved.trial_cap_hours));
  const [boundary, setBoundary] = useState(saved?.baseline_host_costs_included ?? false);
  const [note, setNote] = useState(saved?.assumption_note ?? "");
  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const refs: Schemas["EvidenceRef"][] = [];
        let cursor: string | undefined;
        const seen = new Set<string>();
        do {
          const page = await api.listEvidence(audit.audit_id, { limit: 100, cursor });
          if (!alive) return;
          refs.push(...page.items.filter(r => r.kind === "job"));
          cursor = page.next_cursor ?? undefined;
          if (cursor && seen.has(cursor)) throw new Error("Evidence pagination repeated; reload the audit.");
          if (cursor) seen.add(cursor);
        } while (cursor);
        setJobs(refs);
      } catch (e) { if (alive) setLoadError(errorMessage(e)); }
      finally { if (alive) setLoading(false); }
    })();
    return () => { alive = false; };
  }, [api, audit.audit_id]);
  const result = audit.downside.cpu_pilot;
  const optional = (s: string) => s.trim() === "" ? null : Number(s);
  return <section className="panel cpu-pilot" id="cpu-pilot">
    <div className="section-heading"><div><span className="eyebrow">ONE JOB · ASSUMED SCENARIO</span>
      <h2>CPU pilot: cost and delay</h2></div></div>
    <p className="muted">Choose an eligible job and state the CPU assumptions. These results do not change cohort recovery or claims. No workload is executed.</p>
    <form onSubmit={event => {
      event.preventDefault(); setError("");
      try {
        if (!baseline || !vcpus.trim() || !hours.trim()) throw new Error("Choose a baseline job and enter CPU vCPUs and duration.");
        const cpu_pilot: Pilot = { mode, baseline_evidence_id: baseline, cpu_vcpus: Number(vcpus), cpu_hours: Number(hours),
          cpu_vcpu_hour_usd: optional(price), extra_queue_hours: optional(queue), trial_cap_hours: optional(cap),
          baseline_host_costs_included: boundary, assumption_note: note };
        const scenario = { ...audit.scenario, cpu_pilot };
        validateAuditRequest({ client_request_id: "pilot-form", expected_data_fingerprint: audit.provenance.data_fingerprint,
          recommendation_id: "cpu-placement-pilot", scenario });
        onSubmit(scenario);
      } catch (e) { setError(errorMessage(e)); }
    }} noValidate>
      <div className="form-grid">
        <label>Baseline eligible job<select value={baseline} onChange={e => setBaseline(e.target.value)} disabled={loading || !!loadError}>
          <option value="">{loading ? "Loading eligible jobs…" : "Select a job"}</option>
          {jobs.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
        </select></label>
        <label>Pilot outcome assumption<select value={mode} onChange={e => setMode(e.target.value as Pilot["mode"])}>
          <option value="replacement_success">CPU replacement succeeds</option>
          <option value="replacement_failure">CPU fails; full GPU rerun</option>
          <option value="additional_validation">Additional CPU validation</option>
        </select></label>
        <label>CPU vCPUs<input type="number" min="1" step="1" value={vcpus} onChange={e => setVcpus(e.target.value)} /></label>
        <label>CPU duration (hours)<input type="number" min="0" step="any" value={hours} onChange={e => setHours(e.target.value)} /></label>
        <label>CPU reference USD / vCPU-hour<input type="number" min="0" step="any" placeholder="Unknown" value={price} onChange={e => setPrice(e.target.value)} /></label>
        <label>Extra queue hours<input type="number" min="0" step="any" placeholder="Unknown" value={queue} onChange={e => setQueue(e.target.value)} /></label>
        <label>Assumed trial cap (hours)<input type="number" min="0" step="any" placeholder="Not specified" value={cap} onChange={e => setCap(e.target.value)} /></label>
      </div>
      <label className="pilot-check"><input type="checkbox" checked={boundary} onChange={e => setBoundary(e.target.checked)} />GPU reference price includes baseline host costs</label>
      <p className="small muted">Leave unknown price and queue fields blank. Net reference value stays unknown unless the pricing boundary is confirmed. The trial cap is an assumption, not an enforced stop.</p>
      <label>CPU assumptions and source<textarea rows={2} maxLength={2000} value={note} onChange={e => setNote(e.target.value)} /></label>
      <div className="form-footer"><button className="primary" disabled={busy || loading || !!loadError || !jobs.length}>Model CPU pilot</button>
        {saved && <button type="button" className="secondary" disabled={busy} onClick={() => {
          const { cpu_pilot: _pilot, ...scenario } = audit.scenario; onSubmit(scenario);
        }}>Remove CPU scenario</button>}
      </div>
      {loadError && <p className="error" role="alert">{loadError}</p>}
      {!loading && !loadError && !jobs.length && <p>No eligible baseline jobs in this audit.</p>}
      {error && <p className="error" role="alert">{error}</p>}
    </form>
    {result && <div className="pilot-result" data-testid="cpu-result">
      <h3>Last calculated single-job result</h3>
      <p className="small muted">Inputs above are assumptions. Results and export remain tied to the last successful calculation.</p>
      <dl className="pilot-metrics">
        <div><dt>Recorded baseline GPU-hours</dt><dd>{number(result.baseline.recorded_gpu_hours)} h</dd></div>
        <div><dt>Baseline scheduler duration</dt><dd>{number(result.baseline.elapsed_hours)} h</dd></div>
        <div><dt>Released GPU-hours</dt><dd>{number(result.released_gpu_hours)} h</dd></div>
        <div><dt>Added CPU vCPU-hours</dt><dd>{number(result.added_cpu_vcpu_hours)} vCPU-h</dd></div>
        <div><dt>Released GPU reference value</dt><dd>{usd(result.released_gpu_reference_usd)}</dd></div>
        <div><dt>Added CPU reference cost</dt><dd data-testid="cpu-cost">{result.added_cpu_reference_usd == null ? "Unknown" : usd(result.added_cpu_reference_usd)}</dd></div>
        <div><dt>Net reference value</dt><dd data-testid="cpu-net">{result.net_reference_value_usd == null ? "Unknown" : usd(result.net_reference_value_usd)}</dd></div>
        <div><dt>Runtime change, excluding queue</dt><dd>{result.run_time_change_hours_excluding_queue == null ? "Unknown" : `${number(result.run_time_change_hours_excluding_queue)} h`}</dd></div>
        <div><dt>Completion change, including extra queue</dt><dd data-testid="cpu-delay">{result.completion_change_hours_including_extra_queue == null ? "Unknown" : `${number(result.completion_change_hours_including_extra_queue)} h`}</dd></div>
      </dl>
      <p className="small">Negative net value means added reference cost. Negative time means earlier completion. Neither is an observed outcome.</p>
      <p className="small muted">{result.baseline.accounting_note}</p>
      <button className="text-button" onClick={() => onEvidence(result.baseline.evidence_id)}>Inspect CPU baseline evidence</button>
      {result.limitations.map(l => <p className="small muted" key={l}>{l}</p>)}
    </div>}
  </section>;
}
