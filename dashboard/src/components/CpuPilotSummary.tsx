import { ArrowRight, Gauge, Timer, Wallet } from "lucide-react";
import type { Audit } from "../api/types";
import { number, usd } from "../format";

const hours = (value: number | null) =>
  value === null ? "Unknown" : `${number(value)} h`;

/** Render the v0.4 single-job scenario without blending it into cohort recovery. */
export function CpuPilotSummary({
  audit,
  onEvidence,
}: {
  audit: Audit;
  onEvidence: (id: string) => void;
}) {
  const pilot = audit.downside.cpu_pilot;
  if (!pilot) return null;

  return (
    <section className="panel cpu-pilot-summary" aria-labelledby="cpu-pilot-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">SINGLE-JOB PILOT ESTIMATE</span>
          <h2 id="cpu-pilot-title">CPU pilot scenario</h2>
        </div>
        <Gauge size={20} />
      </div>
      <p className="muted">
        One selected job, modeled before a workload change. This is separate from
        the cohort recovery range.
      </p>
      <div className="cpu-pilot-metrics">
        <div>
          <Wallet size={16} />
          <span>Net reference value</span>
          <strong>
            {pilot.net_reference_value_usd === null
              ? "Not priced"
              : usd(pilot.net_reference_value_usd)}
          </strong>
        </div>
        <div>
          <Timer size={16} />
          <span>Completion change</span>
          <strong>{hours(pilot.completion_change_hours_including_extra_queue)}</strong>
        </div>
        <div>
          <Gauge size={16} />
          <span>Released GPU time</span>
          <strong>{number(pilot.released_gpu_hours)} h</strong>
        </div>
      </div>
      <div className="cpu-pilot-actions">
        <button className="secondary" onClick={() => onEvidence(pilot.baseline.evidence_id)}>
          Inspect selected job <ArrowRight size={16} />
        </button>
        <span className="badge">Scenario estimate · not verified</span>
      </div>
      <details className="cpu-pilot-details">
        <summary>Assumptions and limits</summary>
        <p>{pilot.baseline.accounting_note}</p>
        <ul>
          {pilot.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}
