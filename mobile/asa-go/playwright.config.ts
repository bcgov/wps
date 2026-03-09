import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:4173",
  },
  webServer: {
    command: "yarn preview",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [
    {
      name: "iphone",
      use: {
        viewport: { width: 430, height: 932 },
        deviceScaleFactor: 3,
      },
    },
    {
      name: "android",
      use: {
        viewport: { width: 412, height: 915 },
        deviceScaleFactor: 2.625,
      },
    },
  ],
});
