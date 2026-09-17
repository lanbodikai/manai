import { createHttpApi } from "./http";
import type { Runtime } from "./types";
import { createDatasetHttpApi } from "./dataset";
import { createOptimizationHttpApi } from "./optimization";
export const runtime: Runtime = {
  mode: "http",
  api: {
    ...createHttpApi(),
    optimization: createOptimizationHttpApi({enabled: import.meta.env.VITE_DATASET_API_ENABLED === "true"}),
    datasets: createDatasetHttpApi(
      import.meta.env.VITE_DATASET_API_ENABLED === "true",
    ),
  },
};
