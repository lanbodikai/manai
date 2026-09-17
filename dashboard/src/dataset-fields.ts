import type { Collection, Scalar } from "./api/dataset.ts";
import { number } from "./format.ts";
type Field = { key: string; label: string; unit?: string };
export const collectionInfo: Record<
  Collection,
  {
    label: string;
    singular: string;
    description: string;
    grain: string;
    fields: Field[];
  }
> = {
  jobs: {
    label: "Jobs",
    singular: "job",
    description: "What ran, how it ended, and the GPU time it held.",
    grain: "One row per job; final outcome is not the full retry history.",
    fields: [
      { key: "id_job", label: "Job" },
      { key: "state_name", label: "Outcome" },
      { key: "primary_node", label: "First machine" },
      { key: "gpu_count", label: "GPUs" },
      { key: "gpu_hours", label: "GPU time", unit: "h" },
      { key: "sm_util_avg", label: "Avg. GPU activity", unit: "%" },
    ],
  },
  gpus: {
    label: "GPUs",
    singular: "GPU",
    description:
      "Each physical card, identified by its machine and local GPU number.",
    grain:
      "One row per machine + GPU ID. Activity is weighted by recorded GPU-hours, within this sample.",
    fields: [
      { key: "Node", label: "Machine" },
      { key: "gpu_id", label: "GPU ID" },
      { key: "job_count", label: "Jobs observed" },
      { key: "gpu_hours", label: "GPU time", unit: "h" },
      { key: "sm_util_weighted", label: "Weighted activity", unit: "%" },
      { key: "watts_avg_weighted", label: "Avg. power", unit: "W" },
    ],
  },
  machines: {
    label: "Machines",
    singular: "machine",
    description:
      "Compare recorded workload exposure, then inspect the individual cards.",
    grain: "One row per machine. Failed work is not proof of faulty hardware.",
    fields: [
      { key: "Node", label: "Machine" },
      { key: "observed_gpu_count", label: "Cards observed" },
      { key: "job_count", label: "Jobs observed" },
      { key: "gpu_hours", label: "GPU time", unit: "h" },
      { key: "sm_util_weighted", label: "Weighted activity", unit: "%" },
      { key: "unsuccessful_jobs", label: "Jobs not completed" },
    ],
  },
  findings: {
    label: "Findings",
    singular: "finding",
    description:
      "Rule matches to investigate. Historical means aged out, not fixed; Needs review means active within this historical sample.",
    grain:
      "One row per finding. Findings can overlap; their hours must not be added as savings.",
    fields: [
      { key: "rule", label: "Rule" },
      { key: "status", label: "Status" },
      { key: "Node", label: "Machine" },
      { key: "id_job", label: "Job" },
      { key: "impact_gpu_hours", label: "Reported impact", unit: "h" },
      { key: "impact_kind", label: "Impact type" },
      { key: "impact_scope", label: "Scope" },
    ],
  },
};
export function displayValue(value: Scalar | undefined, unit?: string) {
  if (value === undefined || value === null) return "Not recorded";
  const formatted =
    typeof value === "number"
      ? value > 0 && value < 0.01
        ? "<0.01"
        : number(value)
      : typeof value === "boolean"
        ? value
          ? "Yes"
          : "No"
        : value;
  return `${formatted}${unit ? ` ${unit}` : ""}`;
}
export const findingStatusLabel = (value: Scalar | undefined) => value === "RESOLVED" ? "Historical" : value === "ACTION_REQUIRED" ? "Needs review" : displayValue(value);
