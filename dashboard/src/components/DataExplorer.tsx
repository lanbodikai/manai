import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Database,
  FileSearch,
  ListFilter,
  Search,
  Server,
  X,
} from "lucide-react";
import type { DashboardApi } from "../api/types";
import type {
  Catalog,
  Collection,
  DatasetDetail,
  DatasetPage,
  DatasetQuery,
  DatasetLink,
} from "../api/dataset";
import {
  collections,
  catalogPayload,
  pagePayload,
  detailPayload,
} from "../api/dataset";
import { collectionInfo, displayValue, findingStatusLabel } from "../dataset-fields";
import { errorMessage } from "../api/validation";
import { number } from "../format";

export function datasetHref(
  collection: Collection,
  filters: { outcome?: string; node?: string; id?: string; gpu?: string; query?: string } = {},
) {
  const params = new URLSearchParams(
    Object.entries(filters).filter(([, value]) => value),
  );
  return `#data/${collection}${params.size ? `?${params}` : ""}`;
}
export function useDatasetCatalog(api: DashboardApi) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let alive = true;
    setCatalog(null);
    setError("");
    if (!api.datasets) {
      setError("The dataset browser is not connected.");
      return;
    }
    void api.datasets
      .catalog()
      .then((c) => {
        if (alive) setCatalog(catalogPayload(c));
      })
      .catch((e) => {
        if (alive) setError(errorMessage(e));
      });
    return () => {
      alive = false;
    };
  }, [api, reload]);
  return { catalog, error, retry: () => setReload((x) => x + 1) };
}
const icons = {
  jobs: Database,
  gpus: Cpu,
  machines: Server,
  findings: FileSearch,
};
export function DatasetVisuals({
  catalog,
  showCharts = true,
}: {
  catalog: Catalog;
  showCharts?: boolean;
}) {
  const summary = catalog.summary;
  return (
    <section className="dataset-visuals" aria-label="Dataset visual overview">
      <div className="dataset-counts">
        {catalog.collections.map((c) => {
          const Icon = icons[c.key];
          return (
            <a
              key={c.key}
              href={datasetHref(c.key)}
              className="panel dataset-count"
            >
              <span className="tile-icon blue">
                <Icon size={20} />
              </span>
              <div>
                <span>{collectionInfo[c.key].label}</span>
                <strong>
                  {c.count === null ? "Not loaded" : number(c.count)}
                </strong>
              </div>
              <ArrowRight size={16} />
            </a>
          );
        })}
      </div>
      {summary && showCharts && (
        <div className="dataset-charts">
          <section className="panel">
            <span className="eyebrow">FOLLOW THE GPU TIME</span>
            <h2>Recorded, active, completed</h2>
            <p className="muted small">
              Nested stages in this sample. These are not amounts to add
              together.
            </p>
            <div className="stage-chart">
              {[
                { label: "GPU time recorded", value: summary.gpu_hours },
                {
                  label: "Estimated active GPU time",
                  value: summary.estimated_active_gpu_hours,
                },
                {
                  label: "Active time in completed jobs",
                  value: summary.estimated_completed_active_gpu_hours,
                },
              ].map((s, i) => (
                <div className="stage-row" key={s.label}>
                  <div>
                    <span>{s.label}</span>
                    <strong>{number(s.value)} h</strong>
                  </div>
                  <div className="stage-track">
                    <span
                      style={{
                        width: `${summary.gpu_hours ? Math.min(100, (s.value / summary.gpu_hours) * 100) : 0}%`,
                        background: ["#2856e8", "#7798ef", "#24a89a"][i],
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <p className="chart-note">
              Activity is estimated from GPU telemetry. It does not measure
              research value or cash savings.
            </p>
          </section>
          <section className="panel">
            <span className="eyebrow">EXPLORE THE OUTCOMES</span>
            <h2>Where did the time go?</h2>
            <p className="muted small">Select an outcome to browse its jobs.</p>
            <div className="outcome-bars">
              {summary.outcomes.map((o, i) => (
                <a
                  key={o.outcome}
                  href={datasetHref("jobs", { outcome: o.outcome })}
                >
                  <span className="outcome-name">
                    {o.outcome.replaceAll("_", " ")}
                  </span>
                  <span className="outcome-track">
                    <span
                      style={{
                        width: `${summary.gpu_hours ? (o.gpu_hours / summary.gpu_hours) * 100 : 0}%`,
                        background: [
                          "#2856e8",
                          "#7894d4",
                          "#a0b3da",
                          "#c1cce2",
                          "#8097aa",
                          "#5c7093",
                          "#d3dbea",
                        ][i % 7],
                      }}
                    />
                  </span>
                  <strong>{number(o.gpu_hours)} h</strong>
                  <ArrowRight size={13} />
                </a>
              ))}
            </div>
            <p className="chart-note">
              Cancelled work is not automatically waste. Unknown outcomes stay
              separate.
            </p>
          </section>
        </div>
      )}
    </section>
  );
}
export function DatasetSnapshot({ api }: { api: DashboardApi }) {
  const { catalog } = useDatasetCatalog(api);
  return catalog ? (
    <DatasetVisuals catalog={catalog} showCharts={false} />
  ) : (
    <a className="text-button" href={datasetHref("jobs")}>
      Open data explorer <ArrowRight size={15} />
    </a>
  );
}
export function DatasetHome({ api }: { api: DashboardApi }) {
  const { catalog, error, retry } = useDatasetCatalog(api);
  return (
    <>
      <header className="page-header">
        <div>
          <span className="eyebrow">START WITH THE SOURCE</span>
          <h1>GPU data overview</h1>
          <p>Understand the sample. Explore the work behind each number.</p>
        </div>
        <a className="primary" href="#optimization">
          Review cost opportunities <ArrowRight size={16} />
        </a>
      </header>
      {error ? (
        <div className="panel error-state" role="alert">
          <h2>Local dataset not ready</h2>
          <p>{error}</p>
          <button className="secondary" onClick={retry}>
            Retry dataset
          </button>
        </div>
      ) : catalog ? (
        <>
          <div className="dataset-source">
            <span className="badge">
              {catalog.synthetic ? "Synthetic records" : "Real source sample"}
            </span>
            <p>
              {catalog.source_label} · {catalog.window_label}
            </p>
          </div>
          <DatasetVisuals catalog={catalog} />
          <div className="panel dataset-limits">
            <h2>What this view can tell you</h2>
            <p>
              Browse recorded workloads, compare the cards used by a job, and
              follow a machine to its activity. This is historical sample data,
              not a live fleet monitor.
            </p>
            {catalog.caveats.map((c) => (
              <p key={c} className="small muted">
                {c}
              </p>
            ))}
            <p className="small">
              Audited savings scenarios and MCP chat remain with the analysis
              service. This local preview does not invent them.
            </p>
          </div>
        </>
      ) : (
        <p role="status">Opening the local dataset…</p>
      )}
    </>
  );
}
export function DataExplorer({
  api,
  hash,
}: {
  api: DashboardApi;
  hash: string;
}) {
  const route = hash.replace(/^#data\/?/, "").split("?");
  const collection: Collection = collections.includes(route[0] as Collection)
    ? (route[0] as Collection)
    : "jobs";
  const params = new URLSearchParams(route[1]);
  return (
    <ExplorerTable
      key={hash}
      api={api}
      collection={collection}
      initialOutcome={params.get("outcome") ?? ""}
      initialNode={params.get("node") ?? ""}
      initialId={params.get("id") ?? undefined}
      initialGpu={params.get("gpu") ?? ""}
      initialQuery={params.get("query") ?? ""}
    />
  );
}
function ExplorerTable({
  api,
  collection,
  initialOutcome,
  initialNode,
  initialId,
  initialGpu,
  initialQuery,
}: {
  api: DashboardApi;
  collection: Collection;
  initialOutcome: string;
  initialNode: string;
  initialId?: string;
  initialGpu: string;
  initialQuery: string;
}) {
  const { catalog, error: catalogError, retry } = useDatasetCatalog(api);
  const info = collectionInfo[collection];
  const [gpu, setGpu] = useState(initialGpu);
  const [query, setQuery] = useState(initialQuery);
  const [search, setSearch] = useState(initialQuery);
  const [outcome, setOutcome] = useState(initialOutcome);
  const [node, setNode] = useState(initialNode);
  const [sort, setSort] = useState(info.fields[0].key);
  const [direction, setDirection] = useState<"asc" | "desc">("asc");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<DatasetPage | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [detail, setDetail] = useState<DatasetLink | null>(
    initialId ? { collection, id: initialId, label: initialId } : null,
  );
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(query.trim());
      setOffset(0);
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    let alive = true;
    if (!catalog || !api.datasets) return;
    if (
      catalog.collections.find((c) => c.key === collection)?.available === false
    ) {
      setPage(null);
      setBusy(false);
      setError(
        "This collection has not been loaded. Generate the official findings file and rebuild the local preview. Jobs, GPUs and machines remain available.",
      );
      return;
    }
    setBusy(true);
    setError("");
    setPage(null);
    const q: DatasetQuery = {
      query: search,
      outcome,
      node,
      gpu,
      sort,
      direction,
      offset,
      limit: 20,
    };
    void api.datasets
      .list(collection, q, catalog.version)
      .then((p) => {
        if (alive) setPage(pagePayload(p, collection, q, catalog.version));
      })
      .catch((e) => {
        if (alive) setError(errorMessage(e));
      })
      .finally(() => {
        if (alive) setBusy(false);
      });
    return () => {
      alive = false;
    };
  }, [
    api,
    catalog,
    collection,
    search,
    outcome,
    node,
    gpu,
    sort,
    direction,
    offset,
    refresh,
  ]);
  const stateOptions =
    collection === "jobs"
      ? (catalog?.summary?.outcomes.map((o) => o.outcome) ?? [])
      : ["ACTION_REQUIRED", "RESOLVED"];
  const clear = () => {
    setQuery("");
    setSearch("");
    setOutcome("");
    setNode("");
    setGpu("");
    setOffset(0);
  };
  return (
    <div className="data-explorer">
      <header className="page-header">
        <div>
          <span className="eyebrow">FROM THE PICTURE TO THE RECORD</span>
          <h1>Data explorer</h1>
          <p>
            Search the sample. Open any record to see its fields and related
            resources.
          </p>
        </div>
        <a className="text-button" href="#overview">
          <ChevronLeft size={16} />
          Back to overview
        </a>
      </header>
      <nav className="dataset-tabs" aria-label="Dataset collections">
        {collections.map((c) => {
          const Icon = icons[c];
          const total = catalog?.collections.find((x) => x.key === c)?.count;
          return (
            <a
              key={c}
              href={datasetHref(c)}
              aria-current={c === collection ? "page" : undefined}
              className={c === collection ? "selected" : ""}
            >
              <Icon size={18} />
              {collectionInfo[c].label}
              <span>{total == null ? "—" : number(total)}</span>
            </a>
          );
        })}
      </nav>
      <section className="panel dataset-table-panel">
        <div className="section-heading">
          <div>
            <h2>{info.label}</h2>
            <p className="muted">{info.description}</p>
          </div>
          <span className="badge">
            {catalog?.synthetic
              ? "Synthetic sample"
              : catalog
                ? "Source sample"
                : "Not connected"}
          </span>
        </div>
        <p className="grain-note">{info.grain}</p>
        {catalogError ? (
          <div className="dataset-error" role="alert">
            <h3>Dataset connection unavailable</h3>
            <p>{catalogError}</p>
            <button className="secondary" onClick={retry}>
              Retry dataset
            </button>
          </div>
        ) : !catalog ? (
          <p role="status">Loading dataset information…</p>
        ) : (
          <>
            <div className="dataset-toolbar">
              <label className="dataset-search">
                <Search size={17} />
                <span className="sr-only">
                  Search {info.label.toLowerCase()}
                </span>
                <input
                  value={query}
                  maxLength={200}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={`Search ${info.label.toLowerCase()} by ID or field…`}
                />
              </label>
              <label>
                Machine
                <select
                  aria-label="Machine"
                  value={node}
                  onChange={(e) => {
                    setNode(e.target.value);
                    setGpu("");
                    setOffset(0);
                  }}
                >
                  <option value="">All machines</option>
                  {catalog.nodes.map((n) => (
                    <option key={n}>{n}</option>
                  ))}
                </select>
              </label>
              {collection === "jobs" && node && (
                <label>
                  GPU
                  <select
                    aria-label="GPU on selected machine"
                    value={gpu}
                    onChange={(e) => {
                      setGpu(e.target.value);
                      setOffset(0);
                    }}
                  >
                    <option value="">All cards</option>
                    <option value="0">GPU 0</option>
                    <option value="1">GPU 1</option>
                  </select>
                </label>
              )}
              {(collection === "jobs" || collection === "findings") && (
                <label>
                  {collection === "jobs" ? "Outcome" : "Status"}
                  <select
                    aria-label={collection === "jobs" ? "Outcome" : "Status"}
                    value={outcome}
                    onChange={(e) => {
                      setOutcome(e.target.value);
                      setOffset(0);
                    }}
                  >
                    <option value="">
                      All {collection === "jobs" ? "outcomes" : "statuses"}
                    </option>
                    {stateOptions.map((s) => (
                      <option key={s} value={s}>{collection === "findings" ? findingStatusLabel(s) : s}</option>
                    ))}
                  </select>
                </label>
              )}
              {(query || node || outcome) && (
                <button className="text-button" onClick={clear}>
                  Clear filters
                </button>
              )}
            </div>
            <div className="table-status" aria-live="polite">
              <span>
                <ListFilter size={14} />
                {busy
                  ? "Loading matching records…"
                  : page
                    ? `${number(page.total)} matching ${info.label.toLowerCase()}`
                    : "Records unavailable"}
              </span>
              <span>20 records per page</span>
            </div>
            {error ? (
              <div className="dataset-error" role="alert">
                <p>{error}</p>
                <button
                  className="secondary"
                  onClick={() => setRefresh((x) => x + 1)}
                >
                  Retry records
                </button>
              </div>
            ) : (
              page && (
                <>
                  {page.items.length ? (
                    <div
                      className="dataset-table-scroll"
                      role="region"
                      aria-label={`${info.label} results`}
                      tabIndex={0}
                    >
                      <table className="dataset-table">
                        <caption className="sr-only">
                          {info.label} in the selected sample; select a record
                          for full details.
                        </caption>
                        <thead>
                          <tr>
                            {info.fields.map((f) => (
                              <th
                                key={f.key}
                                aria-sort={
                                  sort === f.key
                                    ? direction === "asc"
                                      ? "ascending"
                                      : "descending"
                                    : "none"
                                }
                              >
                                <button
                                  onClick={() => {
                                    setSort(f.key);
                                    setDirection(
                                      sort === f.key && direction === "asc"
                                        ? "desc"
                                        : "asc",
                                    );
                                    setOffset(0);
                                  }}
                                >
                                  {f.label}
                                  {sort === f.key ? (
                                    direction === "asc" ? (
                                      <ArrowUp size={12} />
                                    ) : (
                                      <ArrowDown size={12} />
                                    )
                                  ) : null}
                                </button>
                              </th>
                            ))}
                            <th>Source</th>
                            <th>
                              <span className="sr-only">Open record</span>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {page.items.map((r) => (
                            <tr key={r.id}>
                              {info.fields.map((f, i) => (
                                <td key={f.key}>
                                  {i === 0 ? (
                                    <button
                                      className="record-link"
                                      onClick={() =>
                                        setDetail({
                                          collection,
                                          id: r.id,
                                          label: r.title,
                                        })
                                      }
                                    >
                                      {f.key === "status" ? findingStatusLabel(r.values[f.key]) : displayValue(r.values[f.key], f.unit)}
                                    </button>
                                  ) : (
                                    <span
                                      className={
                                        f.key === "state_name" ||
                                        f.key === "status"
                                          ? "outcome-badge"
                                          : ""
                                      }
                                    >
                                      {f.key === "status" ? findingStatusLabel(r.values[f.key]) : displayValue(r.values[f.key], f.unit)}
                                    </span>
                                  )}
                                </td>
                              ))}
                              <td>
                                <span className="badge">
                                  {r.synthetic ? "Synthetic" : "Source-derived"}
                                </span>
                              </td>
                              <td>
                                <button
                                  className="icon-button"
                                  aria-label={`Open ${r.title}`}
                                  onClick={() =>
                                    setDetail({
                                      collection,
                                      id: r.id,
                                      label: r.title,
                                    })
                                  }
                                >
                                  <ArrowRight size={16} />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="dataset-empty">
                      <FileSearch size={28} />
                      <h3>No records match these filters</h3>
                      <p>Try a different ID, machine or outcome.</p>
                      <button className="secondary" onClick={clear}>
                        Clear filters
                      </button>
                    </div>
                  )}
                  <div className="dataset-pagination">
                    <span>
                      {page.total
                        ? `${number(offset + 1)}–${number(offset + page.items.length)} of ${number(page.total)}`
                        : "0 records"}
                    </span>
                    <div>
                      <button
                        className="secondary"
                        disabled={busy || offset === 0}
                        onClick={() => setOffset(Math.max(0, offset - 20))}
                      >
                        <ChevronLeft size={15} />
                        Previous
                      </button>
                      <button
                        className="secondary"
                        disabled={
                          busy || offset + page.items.length >= page.total
                        }
                        onClick={() => setOffset(offset + 20)}
                      >
                        Next
                        <ChevronRight size={15} />
                      </button>
                    </div>
                  </div>
                </>
              )
            )}
          </>
        )}
      </section>
      {catalog && (
        <p className="dataset-footer">
          {catalog.source_label} · {catalog.window_label}
          <br />
          Source version: <span className="mono">{catalog.version}</span>
        </p>
      )}
      {detail && catalog && api.datasets && (
        <RecordDrawer
          key={`${detail.collection}/${detail.id}`}
          api={api}
          selected={detail}
          version={catalog.version}
          onClose={() => setDetail(null)}
          onNavigate={setDetail}
        />
      )}
    </div>
  );
}
function RecordDrawer({
  api,
  selected,
  version,
  onClose,
  onNavigate,
}: {
  api: DashboardApi;
  selected: DatasetLink;
  version: string;
  onClose: () => void;
  onNavigate: (link: DatasetLink) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [data, setData] = useState<DatasetDetail | null>(null);
  const [error, setError] = useState("");
  const [fields, setFields] = useState("");
  const [activityFields, setActivityFields] = useState<Record<
    string,
    import("../api/dataset").Scalar
  > | null>(null);
  useEffect(() => {
    const prior = document.activeElement as HTMLElement;
    dialog.current?.showModal();
    setData(null);
    setError("");
    setFields("");
    setActivityFields(null);
    let alive = true;
    void api
      .datasets!.detail(selected.collection, selected.id, version)
      .then((d) => {
        if (alive)
          setData(detailPayload(d, selected.collection, selected.id, version));
      })
      .catch((e) => {
        if (alive) setError(errorMessage(e));
      });
    return () => {
      alive = false;
      if (prior?.isConnected) prior.focus();
    };
  }, [api, selected.collection, selected.id, version]);
  const record = data?.collection === selected.collection && data.record.id === selected.id
    ? data.record : undefined;
  const activity = record?.activity ?? [];
  return (
    <dialog
      className="evidence-dialog record-dialog"
      ref={dialog}
      aria-labelledby="record-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div className="drawer-content">
        <div className="section-heading">
          <div>
            <span className="eyebrow">
              {collectionInfo[selected.collection].singular.toUpperCase()}{" "}
              RECORD
            </span>
            <h2 id="record-title">{record?.title ?? selected.label}</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close record"
            onClick={onClose}
          >
            <X />
          </button>
        </div>
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : !record ? (
          <p role="status">Loading the full record…</p>
        ) : (
          <>
            <span className="badge">
                {selected.collection === "findings"
                  ? record.synthetic ? "Synthetic finding" : "Source-derived finding"
                  : record.synthetic ? "Synthetic example" : "Real source record"}
            </span>
            <p className="record-summary">{record.summary}</p>
            {(selected.collection === "gpus" ||
              selected.collection === "machines") && (
              <a
                className="secondary"
                href={datasetHref("jobs", {
                  node: String(record.values.Node),
                  ...(selected.collection === "gpus"
                    ? { gpu: String(record.values.gpu_id) }
                    : {}),
                })}
                onClick={onClose}
              >
                Browse all jobs on this{" "}
                {selected.collection === "gpus" ? "GPU" : "machine"}{" "}
                <ArrowRight size={15} />
              </a>
            )}
            <div className="record-key-metrics">
              {collectionInfo[selected.collection].fields
                .filter((f) =>
                  ["gpu_hours", "sm_util_avg", "sm_util_weighted", "impact_gpu_hours", "impact_kind", "impact_scope"].includes(
                    f.key,
                  ),
                )
                .map((f) => (
                  <div key={f.key}>
                    <span>{f.label}</span>
                    <strong>
                      {displayValue(record.values[f.key], f.unit)}
                    </strong>
                  </div>
                ))}
            </div>
            {activity.length > 0 && (
              <section>
                <h3>
                  {selected.collection === "jobs"
                    ? "Cards used by this job"
                    : "Per-GPU job records"}
                </h3>
                <p className="small muted">
                  Identity: machine + GPU ID + job. Values describe recorded
                  activity, not unallocated time.
                </p>
                <div
                  className="dataset-table-scroll"
                  tabIndex={0}
                  role="region"
                  aria-label="GPU activity records"
                >
                  <table className="dataset-table">
                    <thead>
                      <tr>
                        <th>Machine / GPU</th>
                        <th>Job</th>
                        <th>GPU time</th>
                        <th>Average activity</th>
                        <th>Source fields</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activity.map((r, i) => (
                        <tr key={i}>
                          <td>
                            {displayValue(r.Node)} / {displayValue(r.gpu_id)}
                          </td>
                          <td>
                            <button
                              className="record-link"
                              onClick={() =>
                                onNavigate({
                                  collection: "jobs",
                                  id: String(r.id_job),
                                  label: `Job ${r.id_job}`,
                                })
                              }
                            >
                              {displayValue(r.id_job)}
                            </button>
                          </td>
                          <td>{displayValue(r.gpu_hours, "h")}</td>
                          <td>{displayValue(r.smutilization_pct_avg, "%")}</td>
                          <td>
                            <button
                              className="record-link"
                              onClick={() => setActivityFields(r)}
                            >
                              View fields
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="small muted">
                  Up to 100 related records are shown here. Use the machine
                  filter to browse all matching jobs.
                </p>
                {activityFields && (
                  <div className="selected-activity">
                    <h3>Selected GPU activity record</h3>
                    <p className="small">
                      {String(activityFields.Node)} · GPU{" "}
                      {String(activityFields.gpu_id)} · Job{" "}
                      {String(activityFields.id_job)}
                    </p>
                    <dl className="observations">
                      {Object.entries(activityFields).map(([key, value]) => (
                        <div key={key}>
                          <dt className="mono">{key}</dt>
                          <dd>
                            {value === null ? "Not recorded" : String(value)}
                          </dd>
                        </div>
                      ))}
                    </dl>
                    <button
                      className="text-button"
                      onClick={() => setActivityFields(null)}
                    >
                      Hide GPU fields
                    </button>
                  </div>
                )}
              </section>
            )}
            {record.related.length > 0 && (
              <section>
                <h3>Connected records</h3>
                <div className="related-records">
                  {record.related.map((r, i) => (
                    <button
                      className="secondary"
                      key={`${r.collection}/${r.id}/${i}`}
                      onClick={() => onNavigate(r)}
                    >
                      {r.label}
                      <ArrowRight size={13} />
                    </button>
                  ))}
                </div>
              </section>
            )}
            <details className="record-fields">
              <summary>
                All fields in this record ({Object.keys(record.values).length})
              </summary>
              <label>
                Find a field
                <input
                  value={fields}
                  onChange={(e) => setFields(e.target.value)}
                  placeholder="e.g. memory, state, node"
                />
              </label>
              <dl className="observations">
                {Object.entries(record.values)
                  .filter(([key]) =>
                    key.toLowerCase().includes(fields.toLowerCase()),
                  )
                  .map(([key, value]) => (
                    <div key={key}>
                      <dt className="mono">{key}</dt>
                      <dd>{value === null ? "Not recorded" : String(value)}</dd>
                    </div>
                  ))}
              </dl>
            </details>
            <section className="record-caveats">
              <h3>How to read this record</h3>
              {data?.caveats.map((c) => (
                <p key={c} className="small muted">
                  {c}
                </p>
              ))}
            </section>
            <p className="small mono muted">Dataset: {version}</p>
          </>
        )}
      </div>
    </dialog>
  );
}
