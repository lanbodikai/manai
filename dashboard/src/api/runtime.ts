import { createHttpApi } from "./http";
import type { Runtime } from "./types";
import { createDatasetHttpApi } from "./dataset";
export const runtime: Runtime = {
  mode: "http",
  api: {
    ...createHttpApi(),
    datasets: createDatasetHttpApi(
      import.meta.env.VITE_DATASET_API_ENABLED === "true",
    ),
  },
};
