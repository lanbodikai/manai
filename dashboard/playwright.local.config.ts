import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/local",
  outputDir: ".local-data/test-results",
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3002",
    viewport: { width: 1440, height: 1000 },
    channel: process.env.PLAYWRIGHT_CHANNEL,
  },
  webServer: {
    command: `"${process.execPath}" node_modules/vite/bin/vite.js --mode dataset-local --host 127.0.0.1 --port 3002 --strictPort`,
    url: "http://127.0.0.1:3002",
    reuseExistingServer: true,
  },
  reporter: "list",
});
