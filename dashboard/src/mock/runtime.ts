import { createMockApi, initialAudit, type Fault } from "./api";
import type { Runtime } from "../api/types";
const faults: Fault[] = [
  "none",
  "empty",
  "source-unavailable",
  "not-found",
  "conflict",
  "invalid",
  "reviewer-unavailable",
  "reviewer-timeout",
  "reviewer-malformed",
];
const selected = new URLSearchParams(location.search).get("demo");
export const runtime: Runtime = {
  mode: "mock",
  api: createMockApi({ fault: faults.find((f) => f === selected) ?? "none" }),
  initialScenario: initialAudit.scenario,
  demoPresentation(overview, audit) {
    // Display-only illustration, confined to the mock adapter. Not a production contract extension.
    const baselineUsd =
      overview.allocated_gpu_hours * audit.scenario.usd_per_gpu_hour;
    const targetUsd = baselineUsd * 0.2;
    const { low, high } = audit.recovery.reference_usd.values;
    return {
      baselineUsd,
      targetUsd,
      gapLow: Math.max(0, targetUsd - high),
      gapHigh: Math.max(0, targetUsd - low),
      contributionLow: baselineUsd ? (low / baselineUsd) * 100 : 0,
      contributionHigh: baselineUsd ? (high / baselineUsd) * 100 : 0,
    };
  },
};
