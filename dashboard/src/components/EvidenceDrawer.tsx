import { useEffect, useRef, useState } from "react";
import { X, ArrowLeft, ArrowRight, Database, FileSearch } from "lucide-react";
import type {
  Audit,
  DashboardApi,
  EvidenceDetail,
  Schemas,
} from "../api/types";
import { assertAuditId, ApiError, errorMessage } from "../api/validation";
import { number, range } from "../format";

export function EvidenceDrawer({
  api,
  audit,
  initialEvidenceId,
  onClose,
}: {
  api: DashboardApi;
  audit: Audit;
  initialEvidenceId?: string;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const serial = useRef(0);
  const [page, setPage] = useState<Schemas["EvidencePage"] | null>(null);
  const [detail, setDetail] = useState<EvidenceDetail | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  async function load(cursor?: string) {
    const seq = ++serial.current;
    setBusy(true);
    setError("");
    try {
      const data = assertAuditId(
        await api.listEvidence(audit.audit_id, { limit: 25, cursor }),
        audit.audit_id,
      );
      if (seq === serial.current) {
        setPage(data);
        setDetail(null);
      }
    } catch (e) {
      if (seq === serial.current) setError(errorMessage(e));
    } finally {
      if (seq === serial.current) setBusy(false);
    }
  }
  async function open(ref: string) {
    const seq = ++serial.current;
    setBusy(true);
    setError("");
    try {
      const data = assertAuditId(
        await api.getEvidence(audit.audit_id, ref),
        audit.audit_id,
      );
      if (data.evidence.id !== ref)
        throw new ApiError(
          "EVIDENCE_ID_MISMATCH",
          "Evidence belongs to another record.",
          502,
        );
      if (seq === serial.current) setDetail(data);
    } catch (e) {
      if (seq === serial.current) setError(errorMessage(e));
    } finally {
      if (seq === serial.current) setBusy(false);
    }
  }
  useEffect(() => {
    const prior = document.activeElement as HTMLElement | null;
    dialog.current?.showModal();
    if (initialEvidenceId) void open(initialEvidenceId);
    else void load();
    return () => {
      ++serial.current;
      prior?.focus();
    };
  }, []);
  return (
    <dialog
      className="evidence-dialog"
      ref={dialog}
      aria-labelledby="evidence-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="drawer-content">
        <div className="section-heading">
          <div>
            <span className="eyebrow">FOLLOW THE NUMBERS</span>
            <h2 id="evidence-title">Evidence behind the pilot</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close evidence"
            onClick={onClose}
          >
            <X />
          </button>
        </div>
        <span className="badge">
          {audit.provenance.synthetic
            ? "Synthetic evidence"
            : "Source evidence"}
        </span>
        <div className="calculation">
          <span>Reference value of potential recovery</span>
          <strong>
            {range(
              audit.recovery.reference_usd.values.low,
              audit.recovery.reference_usd.values.high,
            )}
          </strong>
          <p>{audit.recovery.basis}</p>
          <p className="small">
            Eligible: {number(audit.eligibility.eligible_gpu_hours)} GPU-hours ·{" "}
            {number(audit.eligibility.unique_jobs)} unique jobs
          </p>
          <p className="small">Scenario interval · cash savings not verified</p>
        </div>
        <details className="chart-data">
          <summary>Eligibility and pilot safeguards</summary>
          <p className="small">{audit.eligibility.definition}</p>
          <p className="small">{audit.eligibility.coverage_note}</p>
          {audit.downside.assumptions.map((text) => (
            <p className="small" key={text}>
              {text}
            </p>
          ))}
          {audit.downside.guardrails.map((text) => (
            <p className="small" key={text}>
              {text}
            </p>
          ))}
          <p className="small">
            Pilot measures: {audit.downside.pilot_success_metrics.join(", ")}.
          </p>
        </details>
        {busy && <p role="status">Loading evidence…</p>}
        {error && (
          <div className="error" role="alert">
            {error}
            <button className="text-button" onClick={() => void load()}>
              Back to evidence list
            </button>
          </div>
        )}
        {!busy && !error && detail ? (
          <>
            <button className="text-button" onClick={() => void load()}>
              <ArrowLeft size={16} /> Back to evidence list
            </button>
            <h3>{detail.evidence.label}</h3>
            <p className="muted small">
              {detail.source_table} · {detail.evidence.source_id}
            </p>
            <dl className="observations">
              {detail.observations.map((o, i) => (
                <div key={`${o.name}-${i}`}>
                  <dt>{o.name}</dt>
                  <dd>
                    {String(o.value)} <span>{o.unit ?? ""}</span>
                  </dd>
                </div>
              ))}
            </dl>
            <h3>How this record was checked</h3>
            <p>{detail.method}</p>
            <h3>Source and joins</h3>
            <p className="mono small">{JSON.stringify(detail.join_keys)}</p>
            <p className="small">Fields: {detail.source_columns.join(", ")}</p>
            <h3>What this does not prove</h3>
            {detail.caveats.map((x) => (
              <p key={x}>{x}</p>
            ))}
            <p className="muted small">
              {detail.provenance.sample_label} ·{" "}
              {detail.provenance.source_version}
            </p>
          </>
        ) : (
          !busy &&
          !error &&
          page && (
            <>
              <h3>
                Supporting records <span className="count">{page.total}</span>
              </h3>
              {page.items.length ? (
                <div className="evidence-list">
                  {page.items.map((ref) => (
                    <button key={ref.id} onClick={() => void open(ref.id)}>
                      <Database size={18} />
                      <span>
                        <strong>{ref.label}</strong>
                        <small>
                          {ref.kind} · {ref.source_id} ·{" "}
                          {ref.synthetic ? "Synthetic" : "Observed"}
                        </small>
                      </span>
                      <ArrowRight size={16} />
                    </button>
                  ))}
                </div>
              ) : (
                <p className="empty">
                  <FileSearch /> No eligible records in this calculation.
                </p>
              )}
              {page.next_cursor && (
                <button
                  className="secondary"
                  onClick={() => void load(page.next_cursor!)}
                >
                  Next records
                </button>
              )}
            </>
          )
        )}
        <p className="drawer-foot small muted">
          Calculation ID: {audit.audit_id}
          <br />
          Data version: {audit.provenance.data_fingerprint}
        </p>
      </div>
    </dialog>
  );
}
