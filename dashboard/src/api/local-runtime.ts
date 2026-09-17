import { createHttpApi } from "./http";
import { createDatasetHttpApi } from "./dataset";
import type { Runtime } from "./types";
// This explicit dev mode serves only locally prepared records. No mock imports.
export const runtime: Runtime = {
  mode: "local",
  api: { ...createHttpApi(), datasets: createDatasetHttpApi(true) },
};
