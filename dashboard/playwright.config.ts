import { defineConfig } from "@playwright/test";
const mockPort = process.env.MANAI_TEST_MOCK_PORT ?? "3000";
const httpPort = process.env.MANAI_TEST_HTTP_PORT ?? "3001";
export default defineConfig({
  testDir: "./tests/browser",
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${mockPort}`,
    channel: process.env.PLAYWRIGHT_CHANNEL,
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: [["list"]],
  webServer: [
    {
      command: `"${process.execPath}" node_modules/vite/bin/vite.js --mode mock --host 127.0.0.1 --port ${mockPort} --strictPort`,
      url: `http://127.0.0.1:${mockPort}`,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port ${httpPort} --strictPort`,
      url: `http://127.0.0.1:${httpPort}`,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
