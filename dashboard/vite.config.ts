import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";
import type { Plugin, ProxyOptions } from "vite";

export default defineConfig(async ({ mode }) => ({
  plugins: [
    react(),
    ...(mode === "dataset-local"
      ? [(await import("./tools/local-dataset-plugin.ts")).localDatasetPlugin()]
      : []),
    {
      name: "assert-live-module-boundary",
      generateBundle(_options, bundle) {
        if (mode === "mock") return;
        for (const chunk of Object.values(bundle)) {
          if (chunk.type !== "chunk") continue;
          const leaked = Object.keys(chunk.modules).find((id) =>
            /\/(src\/mock|contracts\/examples)\//.test(
              id.replaceAll("\\", "/"),
            ),
          );
          if (leaked)
            this.error(`Synthetic module reached the live bundle: ${leaked}`);
        }
      },
    } satisfies Plugin,
  ],
  resolve: {
    alias: {
      "@runtime": path.resolve(
        import.meta.dirname,
        mode === "mock"
          ? "src/mock/runtime.ts"
          : mode === "dataset-local"
            ? "src/api/local-runtime.ts"
            : "src/api/runtime.ts",
      ),
    },
  },
  cacheDir: `node_modules/.vite-${mode}`,
  server: {
    proxy: {
      "/api": {
        target: process.env.MANAI_ANALYSIS_URL || "http://127.0.0.1:8001",
        changeOrigin: true,
        configure(proxy) {
          proxy.on("error", (_error, _request, response) => {
            if ("writeHead" in response && !response.headersSent) {
              response.writeHead(503, { "Content-Type": "application/json" });
              response.end(
                JSON.stringify({
                  error: {
                    code: "UPSTREAM_UNAVAILABLE",
                    message:
                      "The analysis service is not reachable. Start A or set MANAI_ANALYSIS_URL.",
                    retryable: true,
                    request_id: "development-proxy",
                  },
                }),
              );
            }
          });
        },
      } satisfies ProxyOptions,
    },
  },
  build: { manifest: true },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
}));
