import type { Plugin } from "vite";
import path from "node:path";
import { datasetHandler } from "./dataset-handler.ts";

export function localDatasetPlugin(): Plugin {
  return {
    name: "local-read-only-dataset-preview",
    apply: "serve",
    configureServer(server) {
      const dataset = datasetHandler(path.join(import.meta.dirname, "../.local-data/preview.sqlite"));
      server.httpServer?.once("close", dataset.close);
      server.middlewares.use("/api/datasets", dataset.handle);
    },
  };
}
