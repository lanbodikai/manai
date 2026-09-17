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
  await expect(page.getByRole("alert")).toBeVisible();
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
