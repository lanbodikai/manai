import { test, expect } from "@playwright/test";
test("sample data explorer filters, links job to GPU, and exposes full source fields", async ({
  page,
}) => {
  await page.goto("/#data/jobs");
  await expect(
    page.getByRole("heading", { name: "Data explorer" }),
  ).toBeVisible();
  await page.getByLabel("Outcome", { exact: true }).selectOption("Finished");
  await expect(page.getByText("4 matching jobs")).toBeVisible();
  await page.getByRole("button", { name: "Open Job J1", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByRole("button", { name: "View fields", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("Selected GPU activity record", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Not recorded", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "demo-machine-01 · GPU 0", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "demo-machine-01 · GPU 0", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByLabel("Search jobs").fill("nothing-matches");
  await expect(page.getByText("No records match these filters")).toBeVisible();
  await page.screenshot({ path: "evidence/dataset-empty.png" });
});
test("mobile data explorer scrolls its table without overflowing the page", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#data/gpus");
  await expect(
    page.getByRole("region", { name: "GPUs results" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "evidence/dataset-mobile.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: /^Open demo-machine/ })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(
    await page
      .getByRole("dialog")
      .evaluate((el) => el.scrollWidth <= el.clientWidth),
  ).toBe(true);
});
