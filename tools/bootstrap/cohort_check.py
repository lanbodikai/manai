"""Feasibility only; this is not A's independently verified recovery audit."""
import json
from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parents[2]
required=["id_job","state_name","sm_util_avg","sm_util_max","gpu_hours"]
jobs=pd.read_parquet(root/"data/prepped/jobs.parquet",columns=required)
assert jobs.id_job.is_unique
complete=jobs[required].notna().all(axis=1)
valid=complete & jobs.gpu_hours.ge(0) & jobs.sm_util_avg.between(0,100) & jobs.sm_util_max.between(0,100) & jobs.sm_util_max.ge(jobs.sm_util_avg)
eligible=valid & jobs.state_name.eq("COMPLETED") & jobs.sm_util_avg.eq(0) & jobs.sm_util_max.eq(0) & jobs.gpu_hours.gt(1)
findings=json.loads((root/"data/synthetic/findings.json").read_text())
source=[f for f in findings if f["detectorId"]=="rules::gpu-not-needed"]
source_ids={int(f["metadata"]["job_id"]) for f in source}
cohort_ids=set(jobs.loc[eligible,"id_job"].astype(int))
assert cohort_ids and source_ids==cohort_ids
assert all(f["metadata"]["impact_kind"]=="unused_capacity" for f in source)
print(json.dumps({"result":"PASS","required_columns":required,"unique_job_keys":True,
 "rows":len(jobs),"missing_measurement_rows":int((~complete).sum()),
 "invalid_measurement_rows":int((complete & ~valid).sum()),"eligible_jobs":int(eligible.sum()),
 "source_cohort_matches":True,"compatibility_verified":False,"recovery_estimated":False}))
