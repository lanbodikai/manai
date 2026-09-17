// Suggested investigation actions, grounded in the supplied rule catalogue.
// These are not executable infrastructure changes or promises of recovery.
export const optimizationOptions = [
  { id: "cpu-placement", rule: "rules::gpu-not-needed", title: "CPU placement pilot", owner: "Platform + workload owner", fix: "Trial CPU placement for completed jobs with zero GPU compute.", risk: "CPU execution may fail or slow down. Compare output and runtime; keep GPU rollback available." },
  { id: "idle-sessions", rule: "rules::idle-interactive-session", title: "Idle interactive sessions", owner: "Platform", fix: "Trial an idle warning and opt-in timeout for interactive allocations.", risk: "A quiet session may still be useful. Warn the owner and preserve work before releasing it." },
  { id: "low-utilization", rule: "rules::gpu-low-utilization", title: "Long, low-utilization jobs", owner: "Workload owner", fix: "Profile data loading and batching; benchmark a smaller allocation.", risk: "Low GPU activity is not proof that a GPU is unnecessary. Preserve throughput and result quality." },
  { id: "gpu-imbalance", rule: "rules::gpu-imbalance", title: "Uneven work across GPUs", owner: "ML / compute engineering", fix: "Check per-card work distribution and trial better sharding.", risk: "Fewer cards or different sharding can increase memory pressure and completion time." },
  { id: "memory-sizing", rule: "rules::gpu-memory-oversized", title: "Low GPU memory usage", owner: "Platform + workload owner", fix: "Benchmark a smaller suitable GPU or a supported sharing setup.", risk: "Memory peaks and compute needs can differ. Check out-of-memory failures and runtime." },
  { id: "failed-arrays", rule: "rules::array-task-failure", title: "Repeated batch-task failures", owner: "Workload owner", fix: "Validate one task and its inputs before retrying the whole batch.", risk: "A code fix may not resolve every failure. Confirm the cause and validate a small rerun." },
  { id: "timeouts", rule: "rules::wallclock-kill", title: "Jobs stopped by time limits", owner: "Workload owner + scheduler team", fix: "Test checkpoint/restart and review requested walltime.", risk: "Longer reservations can delay other work. Verify checkpoints and queue impact." },
  { id: "startup-failures", rule: "rules::gpu-never-computed", title: "Unsuccessful jobs with no GPU compute", owner: "Workload owner", fix: "Investigate startup, environment and input failures before another GPU run.", risk: "These jobs did not prove CPU compatibility. Diagnose the failure before changing placement." },
] as const;
export const fixIds: readonly string[] = optimizationOptions.map(o => o.id);
export const taskSummary:Record<string,{fix:string;risk:string}> = {
  "cpu-placement":{fix:"Test standard processors",risk:"Slower or unsuccessful jobs"},
  "idle-sessions":{fix:"Warn owners, then release idle sessions",risk:"Useful work could be interrupted"},
  "low-utilization":{fix:"Test a smaller allocation",risk:"Lower throughput or result quality"},
  "gpu-imbalance":{fix:"Balance work across GPUs",risk:"Memory pressure or slower runs"},
  "memory-sizing":{fix:"Test a smaller GPU",risk:"Out-of-memory failures"},
  "failed-arrays":{fix:"Validate one task before retrying",risk:"The underlying fault may remain"},
  "timeouts":{fix:"Save progress before time limits",risk:"Other jobs may wait longer"},
  "startup-failures":{fix:"Fix startup errors before rerunning",risk:"Changing processors may not fix it"},
};
