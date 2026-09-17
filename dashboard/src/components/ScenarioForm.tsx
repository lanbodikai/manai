import { useState } from "react";
import { ArrowRight, SlidersHorizontal } from "lucide-react";
import type { Audit, Scenario } from "../api/types";
import { ApiError, validateAuditRequest } from "../api/validation";

export function ScenarioForm({
  initial,
  audit,
  price,
  busy,
  onSubmit,
}: {
  initial?: Scenario;
  audit: Audit | null;
  price: number;
  busy: boolean;
  onSubmit: (s: Scenario) => void;
}) {
  const [low, setLow] = useState(
    initial ? String(initial.recovery_fraction.low * 100) : "",
  );
  const [point, setPoint] = useState(
    initial ? String(initial.recovery_fraction.point * 100) : "",
  );
  const [high, setHigh] = useState(
    initial ? String(initial.recovery_fraction.high * 100) : "",
  );
  const [rate, setRate] = useState(String(initial?.usd_per_gpu_hour ?? price));
  const [note, setNote] = useState(initial?.assumption_note ?? "");
  const [error, setError] = useState("");
  const scenario: Scenario = {
    recovery_fraction: {
      low: Number(low) / 100,
      point: Number(point) / 100,
      high: Number(high) / 100,
    },
    usd_per_gpu_hour: Number(rate),
    cancelled_policy: "exclude",
    interval_kind: "scenario",
    assumption_note: note,
  };
  const dirty =
    !audit || JSON.stringify(audit.scenario) !== JSON.stringify(scenario);
  return (
    <section
      className="panel scenario"
      id="scenario"
      aria-labelledby="scenario-title"
    >
      <div className="section-heading">
        <div>
          <span className="eyebrow">EXPLORE THE ASSUMPTIONS</span>
          <h2 id="scenario-title">What could we recover?</h2>
        </div>
        <SlidersHorizontal size={20} />
      </div>
      <p className="muted">
        Model a range before proposing a pilot. These percentages are
        assumptions, not confidence scores.
      </p>
      <form
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          setError("");
          try {
            if ([low, point, high, rate].some((x) => x.trim() === ""))
              throw new ApiError(
                "INVALID_SCENARIO",
                "Complete all four numeric fields.",
                422,
              );
            validateAuditRequest({
              client_request_id: "form-validation",
              expected_data_fingerprint: "",
              recommendation_id: "cpu-placement-pilot",
              scenario,
            });
            onSubmit(scenario);
          } catch (e) {
            setError(
              e instanceof Error ? e.message : "Check the scenario values.",
            );
          }
        }}
      >
        <div className="form-grid">
          {[
            { label: "Low recovery (%)", value: low, set: setLow },
            { label: "Point recovery (%)", value: point, set: setPoint },
            { label: "High recovery (%)", value: high, set: setHigh },
          ].map((field) => (
            <label key={field.label}>
              {field.label}
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={field.value}
                onChange={(e) => field.set(e.target.value)}
                placeholder="Enter %"
              />
            </label>
          ))}
          <label>
            Reference $ / GPU-hour
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={rate}
              onChange={(e) => setRate(e.target.value)}
            />
          </label>
        </div>
        <label className="note-field">
          Why these assumptions?
          <textarea
            maxLength={2000}
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="State what the pilot needs to verify."
          />
        </label>
        <div className="form-footer">
          <span className="small muted">
            Cancelled jobs excluded · Same cohort
          </span>
          <button className="primary" type="submit">
            Model scenario <ArrowRight size={16} />
          </button>
        </div>
        {dirty && (
          <p className="pending" role="status">
            Pending changes — cards and export still show the last calculated
            scenario.
          </p>
        )}
        {busy && (
          <p role="status" className="muted small">
            Calculating your scenario… You can still change inputs.
          </p>
        )}
        {error && (
          <p className="error" role="alert">
            422 · INVALID_SCENARIO: {error}
          </p>
        )}
      </form>
    </section>
  );
}
