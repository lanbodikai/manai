import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
test("real local source charts to jobs, per-card history and raw fields", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByText("Local dataset preview — real source sample"),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Recorded, active, completed" }),
  ).toBeVisible();
  await expect(page.getByText("74,849", { exact: true })).toBeVisible();
  await mkdir(".local-data/evidence", { recursive: true });
  await page.screenshot({
    path: ".local-data/evidence/real-overview.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: /^COMPLETED / }).click();
  await expect(page.getByLabel("Outcome", { exact: true })).toHaveValue(
    "COMPLETED",
  );
  await page
    .getByRole("button", { name: /^Open Job / })
    .first()
    .click();
  await expect(
    page.getByText("Real source record", { exact: true }),
  ).toBeVisible();
  await page.getByText(/All fields in this record/).click();
  await page.getByLabel("Find a field").fill("nodefail");
  await expect(page.getByText("nodefail_nodes", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("link", { name: /^GPUs / }).click();
  await expect(page.getByText("450 matching gpus")).toBeVisible();
  await page
    .getByRole("button", { name: /^Open r/ })
    .first()
    .click();
  await page
    .getByRole("button", { name: "View fields", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("smutilization_pct_max", { exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: ".local-data/evidence/real-gpu-detail.png" });
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("21–40 of 450")).toBeVisible();
  await page.getByRole("link", { name: /^Findings / }).click();
  await expect(page.getByRole("region", { name: "Findings results" })).toBeVisible();
  await page.getByLabel("Search findings").fill("rules::gpu-never-computed");
  await expect(page.getByRole("cell", { name: "rules::gpu-never-computed", exact: true }).first()).toBeVisible();
  await expect(page.getByRole("cell", { name: "rules::array-mass-failure", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: /^Open / }).first().click();
  await expect(page.getByText("Source-derived finding", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog").getByText("Reported impact", { exact: true })).toBeVisible();
  await page.screenshot({ path: ".local-data/evidence/real-finding-detail.png" });
  await page.getByRole("dialog").getByRole("button", { name: /^Job / }).first().click();
  await expect(page.getByText("Real source record", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByLabel("Search findings").fill("rules::filesystem-latency-degraded");
  await expect(page.getByRole("row").filter({ hasText: "Synthetic" }).first()).toBeVisible();
  await page.getByRole("button", { name: /^Open / }).first().click();
  await expect(page.getByText("Synthetic finding", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: /^Open / }).first().click();
  await expect(page.getByText("Synthetic finding", { exact: true })).toBeVisible();
  expect(await page.getByRole("dialog").evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  expect(await page.getByRole("dialog").boundingBox()).toMatchObject({ x: 0, y: 0, width: 390, height: 844 });
  expect(await page.getByRole("dialog").evaluate(el => el.contains(document.activeElement))).toBe(true);
  await page.screenshot({ path: ".local-data/evidence/real-finding-mobile-detail.png" });
  await page.keyboard.press("Escape");
  await page.screenshot({ path: ".local-data/evidence/real-findings-mobile.png", fullPage: true });
  await page.getByRole("link", { name: /^Machines / }).click();
  await expect(page.getByText("225 matching machines")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: ".local-data/evidence/real-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("loaded findings agree with the official API and resolve source links", async ({ request }) => {
  const catalog = await (await request.get("/api/datasets/catalog")).json();
  const official = process.env.MGAI_URL ?? "http://127.0.0.1:8000";
  const health = await request.get(`${official}/health`);
  expect(health.ok()).toBe(true);
  const officialHealth = await health.json();
  expect(catalog.collections.find((c: { key: string }) => c.key === "findings"))
    .toMatchObject({ available: true, count: officialHealth.findings });
  expect(officialHealth.findings).toBeGreaterThan(0);
  for (const detector_id of ["rules::gpu-never-computed", "rules::filesystem-latency-degraded", "rules::node-failure"]) {
    const response = await request.post(`${official}/v1/events/findings`, { data: { detector_id, limit: 3, offset: 0 } });
    expect(response.ok()).toBe(true);
    const source = await response.json();
    expect(source.findings.length).toBeGreaterThan(0);
    const listing = await (await request.get("/api/datasets/findings", { params: { version: catalog.version, query: detector_id } })).json();
    expect(listing.total).toBe(source.total);
    for (const finding of source.findings) {
      const detail = await request.get(`/api/datasets/findings/${encodeURIComponent(finding.id)}`, { params: { version: catalog.version } });
      expect(detail.ok()).toBe(true);
      const { record } = await detail.json();
      expect(record.synthetic).toBe(finding.metadata.synthetic === true);
      expect(record.values.rule).toBe(finding.detectorId);
      expect(record.values.status).toBe(finding.status);
      expect(record.values.impact_gpu_hours).toBe(finding.metadata.impact_gpu_hours ?? null);
      expect(record.values.Node).toBe(finding.metadata.node ?? null);
      expect(record.values.id_job).toBe(finding.metadata.job_id == null ? null : String(finding.metadata.job_id));
      for (const link of record.related) {
        expect((await request.get(`/api/datasets/${link.collection}/${encodeURIComponent(link.id)}`, { params: { version: catalog.version } })).ok()).toBe(true);
      }
    }
  }
});
test("local API is read-only, paginated, version-bound and literal-search-safe", async ({
  request,
}) => {
  const catalog = await (await request.get("/api/datasets/catalog")).json();
  const params = {
    version: catalog.version,
    limit: "20",
    offset: "0",
    sort: "id_job",
    direction: "asc",
    query: "",
    node: "",
    outcome: "",
  };
  const first = await (
    await request.get("/api/datasets/jobs", { params })
  ).json();
  const second = await (
    await request.get("/api/datasets/jobs", {
      params: { ...params, offset: "20" },
    })
  ).json();
  expect(first.total).toBe(74849);
  expect(first.items).toHaveLength(20);
  expect(
    new Set([...first.items, ...second.items].map((r: { id: string }) => r.id))
      .size,
  ).toBe(40);
  expect(
    (
      await request.get("/api/datasets/jobs", {
        params: { ...params, version: "stale" },
      })
    ).status(),
  ).toBe(409);
  expect(
    (
      await request.get("/api/datasets/jobs", {
        params: { ...params, limit: "101" },
      })
    ).status(),
  ).toBe(422);
  expect((await request.post("/api/datasets/catalog")).status()).toBe(405);
  const search = await (
    await request.get("/api/datasets/jobs", {
      params: { ...params, query: "%' OR 1=1 --" },
    })
  ).json();
  expect(search.total).toBe(0);
  const onCard = await (
    await request.get("/api/datasets/jobs", {
      params: { ...params, node: catalog.nodes[0], gpu: "0" },
    })
  ).json();
  expect(onCard.total).toBeGreaterThan(0);
  for (const row of onCard.items.slice(0, 3)) {
    const detail = await (
      await request.get(`/api/datasets/jobs/${row.id}`, {
        params: { version: catalog.version },
      })
    ).json();
    expect(
      detail.record.activity.some(
        (r: { Node: string; gpu_id: number }) =>
          r.Node === catalog.nodes[0] && r.gpu_id === 0,
      ),
    ).toBe(true);
  }
});
