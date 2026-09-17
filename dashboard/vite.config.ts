import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
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
    },
  ],
  resolve: {
    alias: {
      "@runtime": path.resolve(
        import.meta.dirname,
        mode === "mock" ? "src/mock/runtime.ts" : "src/api/runtime.ts",
      ),
    },
  },
  build: { manifest: true },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
}));
