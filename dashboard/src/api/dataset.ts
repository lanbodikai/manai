import { ApiError } from "./validation";

// Frontend-owned preview proposal, NOT part of the frozen shared API v0.3.
export const collections = ["jobs", "gpus", "machines", "findings"] as const;
export type Collection = (typeof collections)[number];
export type Scalar = string | number | boolean | null;
export type DatasetLink = { collection: Collection; id: string; label: string };
export type DatasetRecord = {
  id: string;
  title: string;
  summary: string;
  synthetic: boolean;
  values: Record<string, Scalar>;
  related: DatasetLink[];
  activity?: Record<string, Scalar>[];
};
export type Catalog = {
  dataset_contract_version: "preview-1";
  version: string;
  source_label: string;
  window_label: string;
  synthetic: boolean;
  nodes: string[];
  collections: { key: Collection; count: number | null; available?: boolean }[];
  caveats: string[];
  summary?: {
    gpu_hours: number;
    estimated_active_gpu_hours: number;
    estimated_completed_active_gpu_hours: number;
    outcomes: { outcome: string; gpu_hours: number }[];
  };
};
export type DatasetQuery = {
  query: string;
  outcome: string;
  node: string;
  sort: string;
  direction: "asc" | "desc";
  offset: number;
  limit: number;
  gpu?: string;
};
export type DatasetPage = {
  collection: Collection;
  version: string;
  synthetic: boolean;
  total: number;
  offset: number;
  limit: number;
  items: DatasetRecord[];
  caveats: string[];
};
export type DatasetDetail = {
  collection: Collection;
  version: string;
  record: DatasetRecord;
  caveats: string[];
};
export interface DatasetApi {
  catalog(): Promise<Catalog>;
  list(
    collection: Collection,
    query: DatasetQuery,
    version: string,
  ): Promise<DatasetPage>;
  detail(
    collection: Collection,
    id: string,
    version: string,
  ): Promise<DatasetDetail>;
}
const text = (v: unknown): v is string => typeof v === "string";
const count = (v: unknown): v is number =>
  typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const object = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === "object" && !Array.isArray(v);
const texts = (v: unknown): v is string[] => Array.isArray(v) && v.every(text);
const scalar = (v: unknown) =>
  v === null ||
  typeof v === "string" ||
  typeof v === "boolean" ||
  (typeof v === "number" && Number.isFinite(v));
const values = (v: unknown) => object(v) && Object.values(v).every(scalar);
const validCollection = (v: unknown): v is Collection =>
  collections.includes(v as Collection);
function record(v: unknown): boolean {
  return (
    object(v) &&
    text(v.id) &&
    !!v.id &&
    text(v.title) &&
    text(v.summary) &&
    typeof v.synthetic === "boolean" &&
    values(v.values) &&
    Array.isArray(v.related) &&
    v.related.every(
      (r) =>
        object(r) &&
        validCollection(r.collection) &&
        text(r.id) &&
        text(r.label),
    ) &&
    (v.activity === undefined ||
      (Array.isArray(v.activity) && v.activity.every(values)))
  );
}
const invalid = () =>
  new ApiError(
    "DATASET_RESPONSE_INVALID",
    "The dataset service returned an unexpected response. No sample data was substituted.",
    502,
  );
export function catalogPayload(v: unknown): Catalog {
  if (
    !object(v) ||
    v.dataset_contract_version !== "preview-1" ||
    !text(v.version) ||
    !v.version ||
    !text(v.source_label) ||
    !text(v.window_label) ||
    typeof v.synthetic !== "boolean" ||
    !texts(v.nodes) ||
    !texts(v.caveats) ||
    !Array.isArray(v.collections) ||
    v.collections.length !== 4 ||
    !v.collections.every(
      (c) =>
        object(c) &&
        validCollection(c.key) &&
        (count(c.count) || (c.count === null && c.available === false)),
    ) ||
    new Set(v.collections.map((c) => c.key)).size !== 4
  )
    throw invalid();
  if (v.summary !== undefined) {
    const s = v.summary;
    const positive = (x: unknown) =>
      typeof x === "number" && Number.isFinite(x) && x >= 0;
    if (
      !object(s) ||
      !positive(s.gpu_hours) ||
      !positive(s.estimated_active_gpu_hours) ||
      !positive(s.estimated_completed_active_gpu_hours) ||
      !Array.isArray(s.outcomes) ||
      !s.outcomes.every(
        (o) => object(o) && text(o.outcome) && positive(o.gpu_hours),
      )
    )
      throw invalid();
  }
  return v as unknown as Catalog;
}
export function pagePayload(
  v: unknown,
  collection: Collection,
  query: DatasetQuery,
  version: string,
): DatasetPage {
  if (
    !object(v) ||
    v.collection !== collection ||
    v.version !== version ||
    typeof v.synthetic !== "boolean" ||
    !count(v.total) ||
    v.offset !== query.offset ||
    v.limit !== query.limit ||
    !texts(v.caveats) ||
    !Array.isArray(v.items) ||
    v.items.length > query.limit ||
    !v.items.every(record) ||
    new Set(v.items.map((r) => r.id)).size !== v.items.length ||
    (v.items.length && v.offset + v.items.length > v.total)
  )
    throw invalid();
  return v as unknown as DatasetPage;
}
export function detailPayload(
  v: unknown,
  collection: Collection,
  id: string,
  version: string,
): DatasetDetail {
  if (
    !object(v) ||
    v.collection !== collection ||
    v.version !== version ||
    !record(v.record) ||
    !object(v.record) ||
    v.record.id !== id ||
    !texts(v.caveats)
  )
    throw invalid();
  return v as unknown as DatasetDetail;
}
export function validateDatasetQuery(q: DatasetQuery) {
  if (
    !text(q.query) ||
    q.query.length > 200 ||
    !text(q.node) ||
    !text(q.outcome) ||
    !text(q.sort) ||
    !["asc", "desc"].includes(q.direction) ||
    !count(q.offset) ||
    !count(q.limit) ||
    q.limit < 1 ||
    q.limit > 100
  )
    throw new ApiError(
      "INVALID_DATASET_QUERY",
      "Use a valid search and a page size between 1 and 100.",
      422,
    );
  if (q.gpu && (!["0", "1"].includes(q.gpu) || !q.node))
    throw new ApiError(
      "INVALID_GPU_FILTER",
      "Select a machine with GPU 0 or 1.",
      422,
    );
}
export function createDatasetHttpApi(
  enabled = false,
  fetcher: typeof fetch = fetch,
): DatasetApi {
  async function request(path: string) {
    if (!enabled)
      throw new ApiError(
        "DATASET_API_NOT_CONFIGURED",
        "The full dataset browser is not connected yet. The analysis service must expose the agreed jobs, GPU, machine and findings routes.",
        503,
      );
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetcher(`/api/datasets${path}`, {
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok)
        throw new ApiError(
          "DATASET_UNAVAILABLE",
          response.status === 409
            ? "The dataset changed. Reload the data explorer."
            : "The dataset could not be loaded. Retry or check the dataset service.",
          response.status,
        );
      return (await response.json()) as unknown;
    } catch (e) {
      if (e instanceof ApiError) throw e;
      throw new ApiError(
        controller.signal.aborted ? "DATASET_TIMEOUT" : "DATASET_UNAVAILABLE",
        controller.signal.aborted
          ? "The dataset request timed out. Retry when the service is ready."
          : "Cannot reach the dataset service or read its response. No sample data was substituted.",
        controller.signal.aborted ? 504 : 503,
      );
    } finally {
      clearTimeout(timeout);
    }
  }
  return {
    catalog: async () => catalogPayload(await request("/catalog")),
    list: async (c, q, version) => {
      validateDatasetQuery(q);
      const params = new URLSearchParams({
        ...q,
        offset: String(q.offset),
        limit: String(q.limit),
        version,
      });
      return pagePayload(await request(`/${c}?${params}`), c, q, version);
    },
    detail: async (c, id, version) =>
      detailPayload(
        await request(
          `/${c}/${encodeURIComponent(id)}?version=${encodeURIComponent(version)}`,
        ),
        c,
        id,
        version,
      ),
  };
}
