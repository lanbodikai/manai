import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/local",
  outputDir: ".local-data/test-results",
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3002",
    viewport: { width: 1440, height: 1000 },
  },
  webServer: {
    command: "npm run dev:local",
    url: "http://127.0.0.1:3002",
    reuseExistingServer: true,
  },
  reporter: "list",
});
