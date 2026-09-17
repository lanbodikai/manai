import { useState } from "react";
import { Play } from "lucide-react";
import { number } from "../format";

/** Display-only inputs reserved for Modeling; this card does no financial calculation. */
export interface TestingEstimates {
  costReductionPercent: number | null;
  gpuHoursSaved: number | null;
}

export function TestingCard({ estimates }: { estimates?: TestingEstimates }) {
  const [previewed, setPreviewed] = useState(false);
  const cost = estimates?.costReductionPercent;
  const hours = estimates?.gpuHoursSaved;
  return (
    <section className="target-panel testing-card" aria-labelledby="testing-title">
      <span className="target-tag">CPU PLACEMENT · DEMO ACTION</span>
      <h2 id="testing-title">Test the opportunity</h2>
      <dl className="testing-metrics">
        <div><dt>Estimated cost reduction</dt><dd>{cost == null ? "Pending" : `${number(cost)}%`}</dd></div>
        <div><dt>Estimated GPU time saved</dt><dd>{hours == null ? "Pending" : `${number(hours)} h`}</dd></div>
      </dl>
      <p className="testing-source">Estimates supplied by Modeling.</p>
      <button type="button" className="testing-execute" onClick={() => setPreviewed(true)}>
        <Play size={17} aria-hidden="true" />Execute testing
      </button>
      <p className="testing-feedback" role="status">{previewed ? "Demo only — no test was started." : "Preview action · no workloads will run."}</p>
    </section>
  );
}
