import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Boxes,
  CircleHelp,
  Database,
  FlaskConical,
  LayoutDashboard,
  MessageSquare,
  ShieldCheck,
  SlidersHorizontal,
  TriangleAlert,
  Wallet,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { Audit, Overview, Runtime, Scenario, Schemas } from "./api/types";
import { assertRequestId, errorMessage } from "./api/validation";
import { number, range, usd } from "./format";
import { ScenarioForm } from "./components/ScenarioForm";
import { CpuPilot } from "./components/CpuPilot";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { ChatPanel } from "./components/ChatPanel";
import { CostOptimization } from "./components/CostOptimization";
import {
  DataExplorer,
  DatasetHome,
  DatasetSnapshot,
  datasetHref,
} from "./components/DataExplorer";

const colors = ["#2856e8", "#9aaee6", "#c1ceec", "#d7dff0", "#e8edf6"];
export function App({ runtime }: { runtime: Runtime }) {
  const { api } = runtime;
  const [hash, setHash] = useState(window.location.hash);
  const dataOpen = hash.startsWith("#data");
  const local = runtime.mode === "local";
  const [overview, setOverview] = useState<Overview | null>(null);
  const [health, setHealth] = useState<Schemas["Health"] | null>(null);
  const [recommendations, setRecommendations] = useState<
    Schemas["Recommendations"] | null
  >(null);
  const [audit, setAudit] = useState<Audit | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState("");
  const [calcError, setCalcError] = useState("");
  const [recommendationError, setRecommendationError] = useState("");
  const [drawer, setDrawer] = useState<{ evidence?: string } | null>(null);
  const [active, setActive] = useState("overview");
  const [team, setTeam] = useState("MANAI");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const [reload, setReload] = useState(0);
  const sequence = useRef(0);
  const currentAuditId = useRef<string | null>(null);
  currentAuditId.current = audit?.audit_id ?? null;
  const mock = runtime.mode === "mock";
  useEffect(() => {
    const change = () => {
      const h = window.location.hash;
      setHash(h);
      setActive(h.startsWith("#data") ? "data" : h.slice(1) || "overview");
    };
    window.addEventListener("hashchange", change);
    change();
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    if (local) {
      setLoading(false);
      return;
    }
    let alive = true;
    setLoading(true);
    setError("");
    setCalcError("");
    setRecommendationError("");
    setCalculating(false);
    setAudit(null);
    setDrawer(null);
    const seq = ++sequence.current;
    void (async () => {
      try {
        const [h, o] = await Promise.all([api.getHealth(), api.getOverview()]);
        if (!alive) return;
        setHealth(h);
        setOverview(o);
        void api
          .listRecommendations()
          .then((r) => {
            if (alive) setRecommendations(r);
          })
          .catch((e) => {
            if (alive) setRecommendationError(errorMessage(e));
          });
        if (h.data_status !== "ready") {
          setError("Data is not ready. Check the analysis service and retry.");
          return;
        }
        if (runtime.initialScenario && h.data_fingerprint) {
          setCalculating(true);
          const request = {
            client_request_id: crypto.randomUUID(),
            expected_data_fingerprint: h.data_fingerprint,
            recommendation_id: "cpu-placement-pilot" as const,
            scenario: runtime.initialScenario,
          };
          try {
            const a = assertRequestId(
              await api.createAudit(request),
              request.client_request_id,
            );
            if (alive && seq === sequence.current) setAudit(a);
          } catch (e) {
            if (alive && seq === sequence.current)
              setCalcError(errorMessage(e));
          } finally {
            if (alive && seq === sequence.current) setCalculating(false);
          }
        }
      } catch (e) {
        if (alive) setError(errorMessage(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
      ++sequence.current;
    };
  }, [api, reload]);
  async function model(scenario: Scenario) {
    const seq = ++sequence.current;
    setCalculating(true);
    setCalcError("");
    const request = {
      client_request_id: crypto.randomUUID(),
      expected_data_fingerprint: health?.data_fingerprint ?? "",
      recommendation_id: "cpu-placement-pilot" as const,
      scenario,
    };
    try {
      const result = assertRequestId(
        await api.createAudit(request),
        request.client_request_id,
      );
      if (seq === sequence.current) {
        setAudit(result);
        setDrawer(null);
        setExportError("");
      }
    } catch (e) {
      if (seq === sequence.current) setCalcError(errorMessage(e));
    } finally {
      if (seq === sequence.current) setCalculating(false);
    }
  }
  async function download() {
    if (!audit) return;
    const id = audit.audit_id;
    setExporting(true);
    setExportError("");
    try {
      const claims = await api.exportClaims(id, team);
      if (currentAuditId.current !== id) {
        setExportError(
          "The calculation changed during export. Download the current result again.",
        );
        return;
      }
      const blob = new Blob([JSON.stringify(claims, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = mock ? "synthetic-claims.example.json" : "claims.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setExportError(errorMessage(e));
    } finally {
      setExporting(false);
    }
  }
  const presentation =
    overview && audit ? runtime.demoPresentation?.(overview, audit) : undefined;
  const pilot = recommendations?.items.find(
    (r) => r.id === "cpu-placement-pilot",
  );
  const nav = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "optimization", label: "Decisions", icon: Wallet },
    { id: "data", label: "Data explorer", icon: Database },
    { id: "scenario", label: "Scenario", icon: SlidersHorizontal },
    { id: "evidence", label: "Evidence", icon: Database },
    { id: "ask", label: "Ask about this pilot", icon: MessageSquare },
  ];
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to dashboard
      </a>
      <aside className="sidebar">
        <a href="#overview" className="brand" aria-label="MANAI home">
          <span className="brand-mark">
            <Boxes size={23} />
          </span>
          manai<span className="brand-dot">.</span>
        </a>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {nav
            .filter((n) => !local || ["overview", "optimization", "data"].includes(n.id))
            .map(({ id, label, icon: Icon }) => (
              <a
                href={`#${id}`}
                key={id}
                aria-label={label}
                className={active === id ? "active" : ""}
                onClick={() => setActive(id)}
                aria-current={active === id ? "page" : undefined}
              >
                <Icon size={19} />
                <span>{label}</span>
                {id === "overview" && <span className="nav-dot" />}
              </a>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <ShieldCheck size={21} />
            <strong>Evidence before action</strong>
            <p>Every recommendation should survive a closer look.</p>
          </div>
          <div className="workspace-avatar">
            <span>M</span>
            <div>
              <strong>MANAI team</strong>
              <small>Track 02 · Cluster efficiency</small>
            </div>
          </div>
        </div>
      </aside>
      <main id="main-content">
        <div className="topbar">
          <span>
            <span className="live-dot" />
            {mock
              ? "Demo workspace"
              : local
                ? "Local dataset workspace"
                : "Analysis workspace"}
          </span>
          <span className="topbar-right">
            <span className="small">
              {local ? "Read-only preview" : "API v0.4"}
            </span>
            <span className="avatar">M</span>
          </span>
        </div>
        {mock && (
          <div className="demo-banner" role="status">
            <FlaskConical size={16} />
            <strong>Synthetic demo — no live data or MCP</strong>
            <span>Illustrative numbers. Not a savings claim.</span>
          </div>
        )}
        {local && (
          <div className="demo-banner local-banner" role="status">
            <Database size={16} />
            <strong>Local dataset preview — real source sample</strong>
            <span>No live monitoring, savings audit or MCP</span>
          </div>
        )}
        {hash === "#optimization" ? (
          <CostOptimization api={api} />
        ) : dataOpen ? (
          <DataExplorer api={api} hash={hash} />
        ) : local ? (
          <DatasetHome api={api} />
        ) : (
          <>
            <header className="page-header" id="overview">
              <div>
                <span className="eyebrow">SPEND LESS. KNOW THE TRADE-OFF.</span>
                <h1>GPU spending overview</h1>
                <p>
                  Find a defensible cut. Understand the cost of being wrong.
                </p>
              </div>
              <span className="period-pill">
                <span className="period-dot" />
                {overview?.provenance.window_label ??
                  (mock ? "Synthetic sample" : "Awaiting source window")}
              </span>
            </header>
            {loading && (
              <div className="panel skeleton" role="status">
                Loading the spending overview…
              </div>
            )}
            {error && (
              <div className="panel error-state" role="alert">
                <TriangleAlert />
                <h2>Source data unavailable</h2>
                <p>{error}</p>
                <button
                  className="primary"
                  onClick={() => setReload((x) => x + 1)}
                >
                  Retry connection
                </button>
                <p className="small">
                  {mock
                    ? "Synthetic mode remains selected."
                    : "Live HTTP mode. No synthetic data has been substituted."}
                </p>
              </div>
            )}
            {!loading && !error && overview && (
              <>
                <div className="decision-line">
                  <span className="badge blue">PROPOSED PILOT</span>
                  <p>
                    Start by testing{" "}
                    <strong>
                      CPU placement for jobs that finished without GPU compute.
                    </strong>{" "}
                    Verify performance before expanding.
                  </p>
                </div>
                <DatasetSnapshot api={api} />
                {recommendationError && (
                  <p className="grain-note" role="status">
                    Pilot recommendations are not available yet. The source
                    overview remains readable. {recommendationError}
                  </p>
                )}
                <div className="tile-grid">
                  <section className="panel tile spending">
                    <div className="tile-label">
                      <span className="tile-icon blue">
                        <Wallet size={18} />
                      </span>
                      <h2>Where the money goes</h2>
                      <span className="step">01</span>
                    </div>
                    <strong className="metric">
                      {presentation
                        ? usd(presentation.baselineUsd)
                        : `${number(overview.allocated_gpu_hours)} h`}
                    </strong>
                    <p className="metric-label">
                      {presentation
                        ? "Reference value · illustrative sample"
                        : "Allocated GPU-hours · source sample"}
                    </p>
                    <div className="tiny-bars" aria-hidden="true">
                      {overview.outcomes.map((o, i) => (
                        <span
                          key={o.outcome}
                          style={{
                            flex: o.gpu_hours || 0.01,
                            background: colors[i % colors.length],
                          }}
                        />
                      ))}
                    </div>
                    <div className="tile-bottom">
                      <span>Spending reduction target</span>
                      <strong>20%</strong>
                    </div>
                    <p className="small muted">
                      A goal, not demonstrated savings.
                    </p>
                  </section>
                  <section className="panel tile opportunity">
                    <div className="tile-label">
                      <span className="tile-icon green">
                        <FlaskConical size={18} />
                      </span>
                      <h2>Where to cut first</h2>
                      <span className="step">02</span>
                    </div>
                    {audit ? (
                      <>
                        <button
                          className="metric metric-link"
                          onClick={() => setDrawer({})}
                          aria-label="Inspect recovery value and evidence"
                        >
                          {range(
                            audit.recovery.reference_usd.values.low,
                            audit.recovery.reference_usd.values.high,
                          )}
                          <ArrowUpRight size={23} />
                        </button>
                        <p className="metric-label">
                          Potential recovery · reference dollars
                        </p>
                        <p className="small muted">{audit.scenario.recovery_fraction.high === 1
                          ? "High bound: eligibility ceiling, not a forecast."
                          : "High bound: assumed recovery, below the physical eligibility ceiling."} CPU recoverability remains unmeasured.</p>
                        <strong className="action-title">
                          Pilot CPU placement
                        </strong>
                        <p className="small muted">
                          {number(audit.recovery.gpu_hours.low)}–
                          {number(audit.recovery.gpu_hours.high)} GPU-hours ·
                          assumed scenario
                        </p>
                        <div className="owner">
                          <span className="owner-dot" />
                          {audit.action.owner_role}
                        </div>
                      </>
                    ) : (
                      <>
                        <strong className="metric empty-metric">
                          Not modeled
                        </strong>
                        <p className="muted">
                          Set recovery assumptions below to explore this pilot.
                        </p>
                        <a className="text-button" href="#scenario">
                          Model a scenario <ArrowRight size={16} />
                        </a>
                      </>
                    )}
                  </section>
                  <section className="panel tile downside">
                    <div className="tile-label">
                      <span className="tile-icon amber">
                        <TriangleAlert size={18} />
                      </span>
                      <h2>If this cut is wrong</h2>
                      <span className="step">03</span>
                    </div>
                    <strong className="risk-headline">
                      Research could
                      <br />
                      run more slowly.
                    </strong>
                    <p className="small">
                      {audit?.downside.mechanisms[0] ??
                        "CPU-only execution may fail or run more slowly."}
                    </p>
                    <div className="tile-bottom">
                      <span>Financial downside</span>
                      <strong>
                        {audit?.downside.money != null
                          ? usd(audit.downside.money)
                          : "Not measured"}
                      </strong>
                    </div>
                    <p className="small muted">
                      Pilot first. Keep the original placement as a rollback.
                    </p>
                  </section>
                </div>
                {calcError && (
                  <p className="error" role="alert">
                    {calcError}{" "}
                    <button
                      className="text-button"
                      onClick={() => setReload((x) => x + 1)}
                    >
                      Reload source
                    </button>
                  </p>
                )}
                {audit && (
                  <div className="audit-status">
                    <span>
                      <span className="status-dot" />
                      {calculating
                        ? "Updating scenario — previous result stays visible"
                        : "Last calculated scenario"}{" "}
                      <span className="mono">{audit.audit_id}</span>
                    </span>
                    <span>
                      Reference price {usd(audit.scenario.usd_per_gpu_hour)} /
                      GPU-hour
                    </span>
                  </div>
                )}
                <div className="middle-grid">
                  <section className="panel chart-panel">
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">THE SPENDING PICTURE</span>
                        <h2>What happened to the work?</h2>
                      </div>
                      <span className="badge">
                        {overview.provenance.synthetic
                          ? "Synthetic"
                          : "Observed"}
                      </span>
                    </div>
                    <p className="muted small">
                      Reference cost by job outcome ·{" "}
                      {usd(overview.usd_per_gpu_hour)} / GPU-hour
                    </p>
                    <div className="chart" aria-label="Spending by job outcome">
                      <ResponsiveContainer width="100%" height={215}>
                        <BarChart
                          data={overview.outcomes}
                          margin={{ top: 22, right: 4, left: -17, bottom: 0 }}
                        >
                          <XAxis
                            dataKey="outcome"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 11, fill: "#78839a" }}
                          />
                          <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 11, fill: "#78839a" }}
                            tickFormatter={(v) => `$${v}`}
                          />
                          <Tooltip
                            formatter={(value) => [
                              usd(Number(value)),
                              "Reference cost",
                            ]}
                            cursor={{ fill: "#f3f6fc" }}
                          />
                          <Bar
                            dataKey="reference_usd"
                            onClick={(_data, index) => {
                              const row = overview.outcomes[index];
                              if (row)
                                window.location.hash = datasetHref("jobs", {
                                  outcome: row.outcome,
                                });
                            }}
                            cursor="pointer"
                            radius={[7, 7, 0, 0]}
                            maxBarSize={48}
                          >
                            {overview.outcomes.map((o, i) => (
                              <Cell
                                key={o.outcome}
                                fill={colors[i % colors.length]}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <details className="chart-data">
                      <summary>View chart values</summary>
                      <table>
                        <caption className="sr-only">
                          Job outcomes in the sample
                        </caption>
                        <thead>
                          <tr>
                            <th>Outcome</th>
                            <th>GPU-hours</th>
                            <th>Reference cost</th>
                          </tr>
                        </thead>
                        <tbody>
                          {overview.outcomes.map((o) => (
                            <tr key={o.outcome}>
                              <td>
                                <a
                                  href={datasetHref("jobs", {
                                    outcome: o.outcome,
                                  })}
                                >
                                  {o.outcome}
                                </a>
                              </td>
                              <td>{number(o.gpu_hours)}</td>
                              <td>{usd(o.reference_usd)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </details>
                    <p className="chart-note">
                      <CircleHelp size={15} />
                      Cancelled work is not automatically wasted.
                    </p>
                  </section>
                  <section className="target-panel">
                    <span className="target-tag">THE 20% QUESTION</span>
                    <h2>
                      How far does
                      <br />
                      this pilot get us?
                    </h2>
                    {presentation ? (
                      <>
                        <p>A small contribution. An honest gap.</p>
                        <div className="target-figure">
                          <strong>
                            {number(presentation.contributionLow)}–
                            {number(presentation.contributionHigh)}%
                          </strong>
                          <span>of the same sample’s reference value</span>
                        </div>
                        <div
                          className="target-track"
                          aria-label={`${number(presentation.contributionLow)} to ${number(presentation.contributionHigh)} percent contribution against 20 percent target`}
                        >
                          <span
                            style={{
                              width: `${Math.min(100, (presentation.contributionHigh / 20) * 100)}%`,
                            }}
                          />
                        </div>
                        <div className="target-labels">
                          <span>Pilot contribution</span>
                          <strong>20% target</strong>
                        </div>
                        <div className="target-gap">
                          <span>Remaining gap</span>
                          <strong>
                            {range(presentation.gapLow, presentation.gapHigh)}
                          </strong>
                        </div>
                        <p className="small">
                          Synthetic same-window illustration at{" "}
                          {usd(audit!.scenario.usd_per_gpu_hour)}/GPU-hour. Not
                          a next-quarter forecast.
                        </p>
                      </>
                    ) : (
                      <>
                        <p>
                          The target is 20%. A verified contribution and
                          matching baseline are not yet available.
                        </p>
                        <p className="small">
                          Awaiting canonical target and gap values from the
                          analysis service.
                        </p>
                      </>
                    )}
                  </section>
                </div>
                <div className="bottom-grid">
                  <ScenarioForm
                    initial={runtime.initialScenario ?? {
                      recovery_fraction: { low: 0, point: 0, high: 1 },
                      usd_per_gpu_hour: overview.usd_per_gpu_hour,
                      cancelled_policy: "exclude", interval_kind: "scenario",
                      assumption_note: "No empirical CPU recoverability: zero low/point; high is the physical eligibility ceiling, not a forecast.",
                    }}
                    audit={audit}
                    price={overview.usd_per_gpu_hour}
                    busy={calculating}
                    onSubmit={(s) => void model(s)}
                  />
                  <section className="panel evidence-preview" id="evidence">
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">
                          ONE RECOMMENDATION, CHECKED CLOSELY
                        </span>
                        <h2>The evidence trail</h2>
                      </div>
                      <Database size={20} />
                    </div>
                    <div className="pilot-row">
                      <span className="tile-icon blue">
                        <BarChart3 size={20} />
                      </span>
                      <div>
                        <strong>{pilot?.title ?? "CPU-placement pilot"}</strong>
                        <p className="small muted">
                          {pilot?.kind === "judgment"
                            ? `${pilot.origin === "team" ? "Team" : "Organizer"} judgment · investigate before action`
                            : mock
                              ? "Synthetic example · not a verified intervention"
                              : "Proposed pilot · compatibility unverified"}
                        </p>
                      </div>
                    </div>
                    {audit ? (
                      <>
                        <div className="evidence-stats">
                          <div>
                            <strong>
                              {number(audit.eligibility.unique_jobs)}
                            </strong>
                            <span>eligible jobs</span>
                          </div>
                          <div>
                            <strong>
                              {number(audit.eligibility.eligible_gpu_hours)} h
                            </strong>
                            <span>eligible GPU time</span>
                          </div>
                          <div>
                            <strong>
                              {number(
                                audit.eligibility
                                  .overlapping_finding_references,
                              )}
                            </strong>
                            <span>overlapping references</span>
                          </div>
                        </div>
                        <p className="small muted">
                          Eligibility is a measured rule match. Recoverability
                          is still an assumption.
                        </p>
                        {!audit.evidence_count && (
                          <p className="empty">
                            No eligible jobs in this calculation.
                          </p>
                        )}
                        <button
                          className="secondary wide"
                          onClick={() => setDrawer({})}
                        >
                          Inspect calculation and source records{" "}
                          <ArrowRight size={16} />
                        </button>
                        <div className="deterministic-summary">
                          <span className="eyebrow">
                            EVIDENCE SUMMARY · DETERMINISTIC
                          </span>
                          <p className="small">{audit.recovery.basis}</p>
                          <p className="small muted">
                            {audit.limitations.join(" ")}
                          </p>
                        </div>
                      </>
                    ) : (
                      <p className="empty">
                        Model a scenario to open its evidence trail.
                      </p>
                    )}
                  </section>
                </div>
                {audit && (
                  <>
                    <CpuPilot key={`pilot-${audit.audit_id}`} api={api} audit={audit} busy={calculating}
                      onSubmit={(s) => void model(s)} onEvidence={(id) => setDrawer({ evidence: id })} />
                    <ChatPanel
                      key={audit.audit_id}
                      api={api}
                      audit={audit}
                      mock={mock}
                      onEvidence={(id) => setDrawer({ evidence: id })}
                    />
                    <section className="export-bar">
                      <div>
                        <h2>Keep the numbers and evidence together.</h2>
                        <p className="muted small">
                          Export this calculation.{" "}
                          {mock
                            ? "The file is a synthetic example, not a submission."
                            : "Export uses the currently displayed audit."}
                        </p>
                      </div>
                      <label>
                        Team
                        <input
                          value={team}
                          maxLength={120}
                          onChange={(e) => setTeam(e.target.value)}
                        />
                      </label>
                      <button
                        className="secondary"
                        disabled={exporting}
                        onClick={() => void download()}
                      >
                        <ArrowDownToLine size={17} />
                        {exporting
                          ? "Preparing…"
                          : mock
                            ? "Download synthetic claims"
                            : "Download claims"}
                      </button>
                    </section>
                    {exportError && (
                      <p className="error" role="alert">
                        {exportError}
                      </p>
                    )}
                  </>
                )}
                <footer>
                  <span>MANAI · Evidence-led GPU decisions</span>
                  <span>
                    {overview.provenance.sample_label} ·{" "}
                    {overview.price_book_version}
                  </span>
                </footer>
              </>
            )}
          </>
        )}
      </main>
      {drawer && audit && (
        <EvidenceDrawer
          key={audit.audit_id}
          api={api}
          audit={audit}
          initialEvidenceId={drawer.evidence}
          onClose={() => setDrawer(null)}
        />
      )}
    </div>
  );
}
