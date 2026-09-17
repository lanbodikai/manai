import { Play } from "lucide-react";
import { number, range, usd } from "../format";
import type { ModelState } from "./PortfolioModel";

export function TestingCard({ model }: { model: ModelState }) {
  const result = model.result;
  const percent = (bounds: { low: number; high: number }) => `${number(bounds.low)}%–${number(bounds.high)}%`;
  return (
    <section className="target-panel testing-card" aria-labelledby="testing-title">
      <span className="target-tag">SELECTED ACTIONS · COST SIMULATION</span>
      <h2 id="testing-title">Test the opportunity</h2>
      <dl className="testing-metrics">
        <div><dt>Estimated net reference cost reduction</dt><dd>{result ? range(result.bounds.net_reference_usd.low, result.bounds.net_reference_usd.high) : "Pending"}</dd></div>
        <div><dt>Reduction as a share of baseline</dt><dd>{result ? percent(result.bounds.baseline_reduction_pct) : "Pending"}</dd></div>
        <div><dt>Share of the 20% target</dt><dd>{result ? percent(result.bounds.target_contribution_pct) : "Pending"}</dd></div>
      </dl>
      {result && <p className="testing-source">20% target: {usd(result.target_reference_usd)} of {usd(result.baseline_reference_usd)} historical reference cost. Remaining gap: {range(result.bounds.remaining_target_reference_usd.low, result.bounds.remaining_target_reference_usd.high)}.</p>}
      <p className="testing-source">Uses the selected actions and assumptions in <a href="#model">Model</a>. Estimates are scenarios, not measured savings; negative reductions mean extra cost.</p>
      <button type="button" className="testing-execute" disabled={!model.enabled || !model.draft || model.busy} onClick={() => void model.calculate()}>
        <Play size={17} aria-hidden="true" />{model.busy ? "Calculating…" : "Run cost simulation"}
      </button>
      <p className="testing-feedback" role="status">{!model.enabled ? "Cost simulation unavailable in this mode." : model.busy ? result ? "Calculating · showing previous result." : "Calculating the selected scenario…" : model.dirty ? "Assumptions changed · showing previous calculation. Run again to update." : result ? "Showing the current calculated scenario. No workloads were run." : "Waiting for simulation inputs. No workloads will run."}</p>
      {model.error && <p role="alert">{model.error} <button type="button" onClick={model.retry}>Reload simulation source</button></p>}
    </section>
  );
}
