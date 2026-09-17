// B-owned planning arithmetic. Not an A audit, measured savings, or execution authorization.
export type PilotInputs = {
  pilotPercent:string; cpuPrice:string; cpuLow:string; cpuPoint:string; cpuHigh:string;
  recoveryLow:string; recoveryPoint:string; recoveryHigh:string;
  implementation:string; retryReserve:string; worstSlowdown:string; maxSlowdown:string; maxSpend:string; basis:string;
};
export const initialPilotInputs: PilotInputs = {
  pilotPercent:"5",cpuPrice:"",cpuLow:"",cpuPoint:"",cpuHigh:"",
  recoveryLow:"0",recoveryPoint:"50",recoveryHigh:"100",implementation:"",retryReserve:"",
  worstSlowdown:"",maxSlowdown:"25",maxSpend:"500",basis:"",
};
export type PilotSource = {version:string; synthetic:boolean; cohortHours:number; totalHours:number; gpuPrice:number};
export function modelPilot(source:PilotSource, input:PilotInputs) {
  const n={} as Record<Exclude<keyof PilotInputs,"basis">,number>;
  for(const key of Object.keys(input) as (keyof PilotInputs)[]) {
    if(key === "basis") continue;
    if(!input[key].trim() || !Number.isFinite(Number(input[key])) || Number(input[key])<0) throw new Error("Complete every numeric assumption with a finite, nonnegative value. Enter 0 explicitly for costs you assume are zero.");
    n[key]=Number(input[key]);
  }
  if(!input.basis.trim()) throw new Error("Explain where the assumptions came from before comparing scenarios.");
  if(!source.version || ![source.cohortHours,source.totalHours,source.gpuPrice].every(v => Number.isFinite(v) && v>=0) || source.cohortHours>source.totalHours || source.cohortHours===0) throw new Error("No valid eligible CPU cohort is available.");
  if(n.pilotPercent<=0 || n.pilotPercent>100) throw new Error("Pilot size must be greater than 0 and at most 100% of eligible GPU-hours.");
  if(n.cpuLow>n.cpuPoint || n.cpuPoint>n.cpuHigh) throw new Error("CPU core-hours must follow low ≤ base ≤ high.");
  if(n.recoveryLow>n.recoveryPoint || n.recoveryPoint>n.recoveryHigh || n.recoveryHigh>100) throw new Error("Recovery must follow 0 ≤ low ≤ base ≤ high ≤ 100%.");
  const pilotHours=source.cohortHours*n.pilotPercent/100;
  const baseline=pilotHours*source.gpuPrice;
  const overhead=n.implementation+n.retryReserve;
  const scenarios=[
    {label:"Low benefit",recovery:n.recoveryLow,cpuHours:n.cpuHigh},
    {label:"Base assumption",recovery:n.recoveryPoint,cpuHours:n.cpuPoint},
    {label:"High benefit",recovery:n.recoveryHigh,cpuHours:n.cpuLow},
  ].map(s => {
    const recoveredHours=pilotHours*s.recovery/100;
    const avoided=recoveredHours*source.gpuPrice;
    const cpuCost=s.cpuHours*n.cpuPrice;
    const net=avoided-cpuCost-overhead;
    return {...s,recoveredHours,avoided,cpuCost,net,afterCost:baseline-net};
  });
  const target=source.totalHours*source.gpuPrice*.2;
  const contribution=Math.max(0,scenarios[1].net);
  const extraSpend=n.cpuHigh*n.cpuPrice+overhead;
  const result={pilotHours,baseline,overhead,scenarios,target,contribution,
    gap:Math.max(0,target-contribution),targetProgress:target ? Math.min(100,contribution/target*100) : 0,
    extraSpend,spendBreached:extraSpend>n.maxSpend,slowdownBreached:n.worstSlowdown>n.maxSlowdown,
    breakEvenCpuHours:n.cpuPrice>0 ? Math.max(0,(scenarios[1].avoided-overhead)/n.cpuPrice) : null,
    breakEvenPossible:scenarios[1].avoided>=overhead};
  if(![pilotHours,baseline,overhead,target,contribution,extraSpend,result.breakEvenCpuHours ?? 0,...scenarios.flatMap(s => [s.recoveredHours,s.avoided,s.cpuCost,s.net,s.afterCost])].every(Number.isFinite)) throw new Error("Assumptions produce values too large to model. Reduce them.");
  return result;
}
export type PilotResult=ReturnType<typeof modelPilot>;
export type PilotSnapshot={inputs:PilotInputs; source:PilotSource; result:PilotResult};
export type PilotReview={snapshot:PilotSnapshot|null; dirty:boolean};
