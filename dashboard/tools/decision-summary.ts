import { optimizationOptions } from "../src/optimization-options.ts";
import type { DecisionTable } from "../src/api/optimization.ts";

export type JobMeasure = { id: string; gpu_hours: number; outcome: string | null; sm_avg: number | null; sm_max: number | null };
export type FindingMeasure = { id: string; rule: string; job_id: string | null; scope: string | null; synthetic: number };

// Observed exposure only. Never sum finding impact, estimate recovery, or price a fix.
// Shared read-only server aggregation; stays outside the browser bundle.
export function buildDecisionTable(jobs: JobMeasure[], findings: FindingMeasure[], version: string, selected: string[], synthetic = false): DecisionTable {
  const byId = new Map(jobs.map(j => [j.id,j]));
  if (byId.size !== jobs.length || jobs.some(j => !Number.isFinite(j.gpu_hours) || j.gpu_hours < 0)) throw new Error("Invalid unique-job accounting");
  if (new Set(selected).size !== selected.length || selected.some(id => !optimizationOptions.some(o => o.id === id))) throw new Error("Invalid fix selection");
  const total = jobs.reduce((sum,j) => sum + j.gpu_hours,0);
  const percentage = (hours: number) => total ? hours / total * 100 : 0;
  const sets = new Map<string,Set<string>>();
  const rows = optimizationOptions.map(option => {
    const matched = findings.filter(f => !f.synthetic && f.rule === option.rule && f.scope === "job");
    const ids = new Set<string>(), cancelled = new Set<string>();
    for (const finding of matched) {
      const job = finding.job_id ? byId.get(finding.job_id) : undefined;
      if (!job) throw new Error("Finding has no resolvable job");
      if (job.outcome === "CANCELLED") { cancelled.add(job.id); continue; }
      if (option.id === "cpu-placement" && !(job.outcome === "COMPLETED" && job.sm_avg === 0 && job.sm_max === 0 && job.gpu_hours > 1)) throw new Error("CPU finding does not match the source cohort");
      ids.add(job.id);
    }
    sets.set(option.id,ids);
    const hours = [...ids].reduce((sum,id) => sum + byId.get(id)!.gpu_hours,0);
    return { ...option, finding_count:matched.length, affected_jobs:ids.size, allocated_gpu_hours:hours, allocated_share_pct:percentage(hours), excluded_cancelled_jobs:cancelled.size };
  });
  const union = new Set(selected.flatMap(id => [...sets.get(id)!]));
  const hours = [...union].reduce((sum,id) => sum + byId.get(id)!.gpu_hours,0);
  const rowHours = rows.filter(r => selected.includes(r.id)).reduce((sum,r) => sum + r.allocated_gpu_hours,0);
  return { contract_version:"optimization-preview-1", dataset_version:version, synthetic,
    total_gpu_hours:total,total_jobs:jobs.length,excluded_synthetic_findings:findings.filter(f => f.synthetic).length,rows,
    selection:{fix_ids:[...selected],unique_jobs:union.size,gpu_hours:hours,share_pct:percentage(hours),overlapping_gpu_hours:Math.max(0,rowHours-hours)} };
}
