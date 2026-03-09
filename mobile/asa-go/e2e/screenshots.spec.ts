import { test } from "@playwright/test";
import path from "path";

const SCREENSHOT_DATE = new Date("2025-07-07T12:00:00");
const OUTPUT_DIR = "screenshots";

test.beforeEach(async ({ page }) => {
  await page.clock.setFixedTime(SCREENSHOT_DATE);
});

test("map", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  // Allow extra time for map tiles to finish rendering
  await page.waitForTimeout(3000);
  await page.screenshot({
    path: path.join(OUTPUT_DIR, testInfo.project.name, "map.png"),
  });
});

test("profile", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "Profile" }).click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: path.join(OUTPUT_DIR, testInfo.project.name, "profile.png"),
  });
});

test("advisory", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "Advisory" }).click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: path.join(OUTPUT_DIR, testInfo.project.name, "advisory.png"),
  });
});
