import { describe, expect, it, vi } from "vitest";
import { createDemoDatasetApi } from "../src/mock/datasets";
import {
  catalogPayload,
  createDatasetHttpApi,
  detailPayload,
  pagePayload,
  type DatasetQuery,
} from "../src/api/dataset";
const base: DatasetQuery = {
  query: "",
  node: "",
  outcome: "",
  sort: "id_job",
  direction: "asc",
  offset: 0,
  limit: 20,
};
describe("dataset browser boundary", () => {
  it("rejects an outcome breakdown that duplicates labels or does not reconcile to recorded time", async () => {
    const catalog=await createDemoDatasetApi(0).catalog();
    expect(catalogPayload(catalog)).toEqual(catalog);
    const wrongTotal=structuredClone(catalog);
    wrongTotal.summary!.outcomes[0].gpu_hours+=1;
    expect(() => catalogPayload(wrongTotal)).toThrow();
    const duplicate=structuredClone(catalog);
    duplicate.summary!.outcomes[1].outcome=duplicate.summary!.outcomes[0].outcome;
    expect(() => catalogPayload(duplicate)).toThrow();
  });
  it("reconciles original jobs and card activity, paginates without duplicates, and keeps GPU identities separate", async () => {
    const api = createDemoDatasetApi(0),
      catalog = await api.catalog();
    const jobs = await api.list("jobs", base, catalog.version);
    expect(jobs.total).toBe(20);
    expect(
      jobs.items.reduce((sum, j) => sum + Number(j.values.gpu_hours), 0),
    ).toBe(600);
    const first = await api.list(
        "jobs",
        { ...base, limit: 5 },
        catalog.version,
      ),
      second = await api.list(
        "jobs",
        { ...base, limit: 5, offset: 5 },
        catalog.version,
      );
    expect(
      new Set([...first.items, ...second.items].map((r) => r.id)).size,
    ).toBe(10);
    const cards = await api.list(
      "gpus",
      { ...base, sort: "Node" },
      catalog.version,
    );
    expect(
      cards.items.reduce((sum, g) => sum + Number(g.values.gpu_hours), 0),
    ).toBe(600);
    expect(new Set(cards.items.map((g) => g.id)).size).toBe(cards.total);
    expect(
      cards.items.filter((g) => g.values.gpu_id === 0).length,
    ).toBeGreaterThan(1);
    const detail = await api.detail("jobs", "J1", catalog.version);
    expect(detail.record.activity?.[0].maxgpumemoryused_bytes).toBeNull();
    expect(detail.record.related.some((r) => r.collection === "gpus")).toBe(
      true,
    );
  });
  it("filters and sorts all matching records, preserves original snapshots, and rejects stale versions", async () => {
    const api = createDemoDatasetApi(0),
      catalog = await api.catalog();
    const rows = await api.list(
      "jobs",
      { ...base, outcome: "Finished", sort: "gpu_hours", direction: "desc" },
      catalog.version,
    );
    expect(rows.items.map((r) => r.values.gpu_hours)).toEqual([
      150, 120, 20, 10,
    ]);
    const empty = await api.list(
      "jobs",
      { ...base, query: "absent-record" },
      catalog.version,
    );
    expect(empty.total).toBe(0);
    rows.items[0].values.gpu_hours = 999;
    expect(
      (await api.detail("jobs", "J4", catalog.version)).record.values.gpu_hours,
    ).toBe(150);
    await expect(api.list("jobs", base, "old")).rejects.toMatchObject({
      status: 409,
    });
    await expect(
      api.list("jobs", { ...base, limit: 101 }, catalog.version),
    ).rejects.toMatchObject({ status: 422 });
    await expect(
      api.detail("gpus", "gpu-0", catalog.version),
    ).rejects.toMatchObject({ status: 404 });
  });
  it("rejects wrong dataset, collection, record, malformed numbers and duplicate identities", async () => {
    const api = createDemoDatasetApi(0),
      catalog = await api.catalog(),
      page = await api.list("jobs", base, catalog.version),
      detail = await api.detail("jobs", "J1", catalog.version);
    expect(() =>
      pagePayload({ ...page, version: "wrong" }, "jobs", base, catalog.version),
    ).toThrow();
    expect(() =>
      pagePayload(
        { ...page, items: [page.items[0], page.items[0]] },
        "jobs",
        base,
        catalog.version,
      ),
    ).toThrow();
    expect(() =>
      detailPayload(detail, "gpus", "J1", catalog.version),
    ).toThrow();
    expect(() =>
      detailPayload(detail, "jobs", "J2", catalog.version),
    ).toThrow();
    expect(() =>
      catalogPayload({
        ...catalog,
        summary: { ...catalog.summary, gpu_hours: NaN },
      }),
    ).toThrow();
  });
  it("requires explicit HTTP opt-in and never substitutes demo data for connection failures", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockRejectedValue(new Error("offline"));
    await expect(
      createDatasetHttpApi(false, fetcher).catalog(),
    ).rejects.toMatchObject({ code: "DATASET_API_NOT_CONFIGURED" });
    expect(fetcher).not.toHaveBeenCalled();
    await expect(
      createDatasetHttpApi(true, fetcher).catalog(),
    ).rejects.toMatchObject({ status: 503 });
    expect(fetcher).toHaveBeenCalledWith(
      "/api/datasets/catalog",
      expect.anything(),
    );
  });
});
