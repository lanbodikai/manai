import { test, expect } from "@playwright/test";
import { readFile, mkdir } from "node:fs/promises";

test("desktop dollar to source, keyboard modal, assistant and matching claims", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByText("Synthetic demo — no live data or MCP"),
  ).toBeVisible();
  const recovery = page.getByRole("button", {
    name: "Inspect recovery value and evidence",
  });
  await expect(recovery).toHaveText("$15–$45");
  await mkdir("evidence", { recursive: true });
  await page.screenshot({
    path: "evidence/desktop-overview.png",
    fullPage: true,
  });
  await recovery.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByRole("button", { name: /Synthetic completed job J1/ })
    .click();
  await expect(page.getByText("Source and joins")).toBeVisible();
  await page.screenshot({ path: "evidence/evidence-detail.png" });
  await page.keyboard.press("Tab");
  expect(
    await page.evaluate(() =>
      document.querySelector("dialog")?.contains(document.activeElement),
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(recovery).toBeFocused();
  await expect(page.getByLabel("Low recovery (%)")).toHaveCount(0);
  await page.getByRole("link", {name:"Ask about this pilot", exact:true}).click();
  await page.getByRole("button", {name:"Why this pilot?"}).click();
  await expect(page.getByText(/Synthetic example: 30 eligible/)).toBeVisible();
  await page.getByRole("link", {name:"Overview",exact:true}).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download synthetic claims" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("synthetic-claims.example.json");
  const claims = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(claims.recoverable_gpu_hours).toMatchObject({
    low: 6,
    point: 12,
    high: 18,
  });
  expect(claims.recoverable_usd).toMatchObject({
    low: 15,
    point: 30,
    high: 45,
  });
  expect(claims.notes).toContain("demo-audit-1");
  expect(errors).toEqual([]);
});

test("narrow viewport keeps required content and source drawer usable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("link", { name: "Ask about this pilot", exact: true }),
  ).toBeVisible();
  const recovery = page.getByRole("button", {
    name: "Inspect recovery value and evidence",
  });
  await expect(recovery).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "evidence/mobile-overview.png",
    fullPage: true,
  });
  await recovery.click();
  await page
    .getByRole("button", { name: /Synthetic completed job J2/ })
    .click();
  await expect(page.getByText("Source and joins")).toBeVisible();
  expect(
    await page
      .getByRole("dialog")
      .evaluate((el) => el.scrollWidth <= el.clientWidth),
  ).toBe(true);
  await page.screenshot({ path: "evidence/mobile-evidence.png" });
  await page.getByRole("button", { name: "Close evidence" }).click();
});

for (const state of [
  "reviewer-unavailable",
  "reviewer-timeout",
  "reviewer-malformed",
]) {
  test(`optional ${state} preserves base chat and download`, async ({
    page,
  }) => {
    await page.goto(`/?demo=${state}`);
    await page.getByRole("link", {name:"Ask about this pilot",exact:true}).click();
    await page.getByText("Open optional advanced reviewer").click();
    await page.getByLabel("Advanced review question").fill("Why this pilot?");
    await page.getByRole("button", { name: "Ask advanced reviewer" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await page.getByRole("button", { name: "What could go wrong?" }).click();
    await expect(
      page.getByText(/Synthetic example: 30 eligible/),
    ).toBeVisible();
    await page.getByRole("button", { name: "job:J1", exact: true }).click();
    await expect(page.getByText("Source and joins")).toBeVisible();
    await page.getByRole("button", {name:"Close evidence"}).click();
    await page.getByRole("link", {name:"Overview",exact:true}).click();
    await expect(page.getByRole("button", { name: "Download synthetic claims" })).toBeEnabled();
  });
}

test("live entry shows connection failure and never loads mock modules", async ({
  page,
}) => {
  const urls: string[] = [];
  page.on("request", (r) => urls.push(r.url()));
  await page.goto(`http://127.0.0.1:${process.env.MANAI_TEST_HTTP_PORT ?? "3001"}`);
  await expect(
    page.getByRole("heading", { name: "Source data unavailable" }),
  ).toBeVisible();
  await expect(
    page.getByText("Synthetic demo — no live data or MCP"),
  ).toHaveCount(0);
  await expect(
    page.getByText("Live HTTP mode. No synthetic data has been substituted."),
  ).toBeVisible();
  expect(urls.filter((url) => /\/src\/mock\//.test(url))).toEqual([]);
});
