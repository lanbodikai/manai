import { createHttpApi } from "./http";
import type { Runtime } from "./types";
export const runtime: Runtime = { mode: "http", api: createHttpApi() };
