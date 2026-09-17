// MANAI_MOCK_ONLY — original invented records, never source-data-derived.
import type {
  Catalog,
  Collection,
  DatasetApi,
  DatasetRecord,
  Scalar,
} from "../api/dataset";
import {
  catalogPayload,
  detailPayload,
  pagePayload,
  validateDatasetQuery,
} from "../api/dataset";
import { ApiError } from "../api/validation";
import { collectionInfo } from "../dataset-fields";

const version = "demo-dataset-v1";
const hours = [
  10, 20, 120, 150, 20, 30, 30, 40, 15, 20, 25, 30, 5, 10, 20, 25, 5, 5, 10, 10,
];
const outcomes = ["Finished", "Cancelled", "Timed out", "Failed", "Other"];
const nodes = Array.from(
  { length: 6 },
  (_, i) => `demo-machine-${String(i + 1).padStart(2, "0")}`,
);
const gpuActivity: Record<string, Scalar>[] = [];
const jobs: DatasetRecord[] = hours.map((h, i) => {
  const id = `J${i + 1}`;
  const node = nodes[i % 6];
  const cards = i > 1 && i % 3 === 0 ? 2 : 1;
  const sm = i < 2 ? 0 : [12, 38, 65, 8, 82][i % 5];
  for (let card = 0; card < cards; card++)
    gpuActivity.push({
      id_job: id,
      Node: node,
      gpu_id: cards === 1 ? i % 2 : card,
      gpu_hours: h / cards,
      smutilization_pct_avg: sm,
      smutilization_pct_max: Math.min(100, sm + (sm ? 12 : 0)),
      powerusage_watts_avg: 60 + sm,
      maxgpumemoryused_bytes: i === 0 ? null : 1073741824 * (1 + (i % 8)),
      totalexecutiontime_sec: (h / cards) * 3600,
      state_name: outcomes[Math.floor(i / 4)],
    });
  return {
    id,
    title: `Job ${id}`,
    summary:
      i < 2
        ? "This job finished with no recorded GPU compute. CPU-only compatibility is not tested."
        : `This job ${outcomes[Math.floor(i / 4)].toLowerCase()} and recorded ${h} GPU-hours. Its outcome alone does not establish recoverable savings.`,
    synthetic: true,
    values: {
      id_job: id,
      state_name: outcomes[Math.floor(i / 4)],
      primary_node: node,
      gpu_count: cards,
      gpu_hours: h,
      sm_util_avg: sm,
      sm_util_max: Math.min(100, sm + (sm ? 12 : 0)),
      walltime_sec: (h / cards) * 3600,
      wait_sec: i * 120,
      attempts: 1,
      hit_node_failure: false,
      nodefail_nodes: "[]",
      partition: "demo-partition",
      job_type: "BATCH",
      mem_req_mb: 4096,
      mem_req_is_per_cpu: false,
      is_array_task: false,
    },
    related: [
      { collection: "machines", id: node, label: node },
      ...gpuActivity
        .filter((r) => r.id_job === id)
        .map((r) => ({
          collection: "gpus" as const,
          id: `${node}/gpu-${r.gpu_id}`,
          label: `${node} · GPU ${r.gpu_id}`,
        })),
    ],
    activity: gpuActivity.filter((r) => r.id_job === id),
  };
});
function sum(rows: Record<string, Scalar>[], field: string) {
  return rows.reduce((s, r) => s + Number(r[field] ?? 0), 0);
}
function weighted(rows: Record<string, Scalar>[], field: string) {
  const denominator = sum(rows, "gpu_hours");
  return denominator
    ? rows.reduce((s, r) => s + Number(r.gpu_hours) * Number(r[field]), 0) /
        denominator
    : null;
}
const gpuKeys = [
  ...new Set(gpuActivity.map((r) => `${r.Node}/gpu-${r.gpu_id}`)),
];
const gpus: DatasetRecord[] = gpuKeys.map((id) => {
  const rows = gpuActivity.filter((r) => `${r.Node}/gpu-${r.gpu_id}` === id);
  const node = String(rows[0].Node);
  return {
    id,
    title: `${node} · GPU ${rows[0].gpu_id}`,
    summary:
      "Activity observed while jobs held this card. Unallocated time has no telemetry; this is not whole-fleet utilization.",
    synthetic: true,
    values: {
      Node: node,
      gpu_id: rows[0].gpu_id,
      job_count: rows.length,
      gpu_hours: sum(rows, "gpu_hours"),
      sm_util_weighted: weighted(rows, "smutilization_pct_avg"),
      watts_avg_weighted: weighted(rows, "powerusage_watts_avg"),
    },
    related: [
      { collection: "machines", id: node, label: node },
      ...rows.map((r) => ({
        collection: "jobs" as const,
        id: String(r.id_job),
        label: `Job ${r.id_job}`,
      })),
    ],
    activity: rows,
  };
});
const machines: DatasetRecord[] = nodes.map((node) => {
  const rows = gpuActivity.filter((r) => r.Node === node);
  const jobRows = jobs.filter((j) => j.values.primary_node === node);
  return {
    id: node,
    title: node,
    summary:
      "Workload exposure on this machine within the invented sample. A failure count alone is not evidence of faulty hardware.",
    synthetic: true,
    values: {
      Node: node,
      observed_gpu_count: new Set(rows.map((r) => r.gpu_id)).size,
      job_count: jobRows.length,
      gpu_hours: sum(rows, "gpu_hours"),
      sm_util_weighted: weighted(rows, "smutilization_pct_avg"),
      unsuccessful_jobs: jobRows.filter(
        (j) => j.values.state_name !== "Finished",
      ).length,
    },
    related: gpus
      .filter((g) => g.values.Node === node)
      .map((g) => ({ collection: "gpus", id: g.id, label: g.title })),
    activity: rows,
  };
});
const findings: DatasetRecord[] = [
  ["F1", "J1", "gpu-not-needed", "RESOLVED", "unused_capacity"],
  ["F2", "J2", "gpu-not-needed", "RESOLVED", "unused_capacity"],
  [
    "F3",
    "J1",
    "idle-interactive-session",
    "ACTION_REQUIRED",
    "unused_capacity",
  ],
  ["F4", "J10", "wallclock-kill", "RESOLVED", "lost"],
].map(([id, jobId, rule, status, kind]) => {
  const job = jobs.find((j) => j.id === jobId)!;
  if (id === "F3") job.values.job_type = "INTERACTIVE";
  return {
    id,
    title: `${rule} · ${jobId}`,
    summary:
      "An invented rule match. Another finding can describe the same physical job hours; do not add finding impacts together.",
    synthetic: true,
    values: {
      rule: `rules::${rule}`,
      status,
      Node: job.values.primary_node,
      id_job: jobId,
      impact_gpu_hours: job.values.gpu_hours,
      impact_kind: kind,
      impact_scope: "job",
      isActive: status === "ACTION_REQUIRED",
      synthetic: true,
    },
    related: [
      { collection: "jobs", id: jobId, label: `Job ${jobId}` },
      {
        collection: "machines",
        id: String(job.values.primary_node),
        label: String(job.values.primary_node),
      },
    ],
  };
});
const tables: Record<Collection, DatasetRecord[]> = {
  jobs,
  gpus,
  machines,
  findings,
};
const caveats = [
  "Every record in this browser is invented, not the MIT dataset.",
  "Missing measurements are shown as Not recorded, never zero.",
  "No dataset finding changes the audited savings claim.",
];
const catalog: Catalog = catalogPayload({
  dataset_contract_version: "preview-1",
  version,
  source_label: "Original invented dataset · 20 jobs",
  window_label: "Synthetic window; no production dates",
  synthetic: true,
  nodes,
  collections: Object.entries(tables).map(([key, rows]) => ({
    key,
    count: rows.length,
  })),
  caveats,
  summary: {
    gpu_hours: 600,
    estimated_active_gpu_hours: jobs.reduce(
      (s, j) =>
        s + (Number(j.values.gpu_hours) * Number(j.values.sm_util_avg)) / 100,
      0,
    ),
    estimated_completed_active_gpu_hours: jobs
      .filter((j) => j.values.state_name === "Finished")
      .reduce(
        (s, j) =>
          s + (Number(j.values.gpu_hours) * Number(j.values.sm_util_avg)) / 100,
        0,
      ),
    outcomes: outcomes.map((outcome, i) => ({
      outcome,
      gpu_hours: hours.slice(i * 4, i * 4 + 4).reduce((a, b) => a + b, 0),
    })),
  },
});

// The decisions demo uses this same invented dataset and denominator.
export function demoDecisionSource() {
  const state: Record<string,string> = {Finished:"COMPLETED",Cancelled:"CANCELLED","Timed out":"TIMEOUT",Failed:"FAILED",Other:"OTHER"};
  return {
    jobs: jobs.map(j => ({id:j.id,gpu_hours:Number(j.values.gpu_hours),outcome:state[String(j.values.state_name)],sm_avg:Number(j.values.sm_util_avg),sm_max:Number(j.values.sm_util_max)})),
    // All records are invented. The enclosing decision response remains synthetic;
    // these flags represent detector-generated incidents inside that fictional sample.
    findings: findings.map(f => ({id:f.id,rule:String(f.values.rule),job_id:String(f.values.id_job),scope:"job",synthetic:0})),
  };
}

export function createDemoDatasetApi(delay = 120): DatasetApi {
  const wait = () => new Promise((resolve) => setTimeout(resolve, delay));
  function checkVersion(expected: string) {
    if (expected !== version)
      throw new ApiError(
        "DATA_VERSION_MISMATCH",
        "The dataset changed. Reload the explorer.",
        409,
      );
  }
  return {
    async catalog() {
      await wait();
      return structuredClone(catalog);
    },
    async list(collection, q, expected) {
      validateDatasetQuery(q);
      checkVersion(expected);
      await wait();
      if (!collectionInfo[collection].fields.some((f) => f.key === q.sort))
        throw new ApiError(
          "INVALID_SORT",
          "Choose a displayed column to sort.",
          422,
        );
      const query = q.query.toLowerCase().trim();
      const rows = tables[collection].filter(
        (r) =>
          (!query ||
            [r.title, ...Object.values(r.values)]
              .join(" ")
              .toLowerCase()
              .includes(query)) &&
          (!q.outcome ||
            r.values.state_name === q.outcome ||
            r.values.status === q.outcome) &&
          (!q.node || (r.values.Node ?? r.values.primary_node) === q.node) &&
          (!q.gpu ||
            r.activity?.some(
              (a) => a.Node === q.node && String(a.gpu_id) === q.gpu,
            )),
      );
      rows.sort((a, b) => {
        const av = a.values[q.sort],
          bv = b.values[q.sort];
        if (av === null || av === undefined)
          return bv == null ? a.id.localeCompare(b.id) : 1;
        if (bv === null || bv === undefined) return -1;
        const comparison =
          typeof av === "number" && typeof bv === "number"
            ? av - bv
            : String(av).localeCompare(String(bv), undefined, {
                numeric: true,
              });
        return (
          (q.direction === "asc" ? comparison : -comparison) ||
          a.id.localeCompare(b.id)
        );
      });
      return structuredClone(
        pagePayload(
          {
            collection,
            version,
            synthetic: true,
            total: rows.length,
            offset: q.offset,
            limit: q.limit,
            items: rows.slice(q.offset, q.offset + q.limit),
            caveats,
          },
          collection,
          q,
          expected,
        ),
      );
    },
    async detail(collection, id, expected) {
      checkVersion(expected);
      await wait();
      const record = tables[collection].find((r) => r.id === id);
      if (!record)
        throw new ApiError(
          "RECORD_NOT_FOUND",
          "This record is not in the selected dataset.",
          404,
        );
      return structuredClone(
        detailPayload(
          { collection, version, record, caveats },
          collection,
          id,
          expected,
        ),
      );
    },
  };
}
