"""Prepare the raw MIT SuperCloud CSVs into two tables: data/prepped/jobs.parquet
(one row per job) and data/prepped/gpus.parquet (one row per GPU per job).

What it does to the raw data:
  - collapses each job's requeue chain to its LAST attempt, keeping the history in
    attempts / nodefail_* columns (restarted jobs are one id_job, several rows)
  - state 7 kept separate as NODE_FAIL (NOT lumped into TIMEOUT)
  - mem_req MEM_PER_CPU bit-flag decoded
  - energy from powerusage_watts_avg x duration (energyconsumed_joules is broken)
  - timestamps are RELATIVE offsets, not epoch
Writes data/prepped/jobs.parquet (job level) and gpus.parquet (gpu level).
"""
import numpy as np, pandas as pd
from pathlib import Path

RAW = Path("data/raw"); OUT = Path("data/prepped"); OUT.mkdir(parents=True, exist_ok=True)
MEM_PER_CPU_FLAG = 9223372036854775808      # 0x8000000000000000
V100_MEM_BYTES   = 32 * 1024**3             # TX-GAIA V100-32GB

STATE = {0:"PENDING", 1:"RUNNING", 3:"COMPLETED", 4:"CANCELLED", 5:"FAILED",
         6:"TIMEOUT", 7:"NODE_FAIL", 11:"UNDECODED_11", 1024:"UNDECODED_1024"}
TERMINAL   = {"COMPLETED","CANCELLED","FAILED","TIMEOUT","NODE_FAIL",
              "UNDECODED_11","UNDECODED_1024"}
SUCCESSFUL = {"COMPLETED"}


def load_scheduler():
    # mem_req must be read as TEXT. Values above 2**63 carry Slurm's MEM_PER_CPU
    # flag, and pandas types the column float64 on read -- float64 spacing at that
    # magnitude is 2048, so the low bits (the actual MB figure) are destroyed on
    # read. Read as float64, 111,380 of the 111,438 per-CPU rows come out wrong.
    s = pd.read_csv(RAW/"scheduler_data.csv", low_memory=False,
                    dtype={"mem_req": "string"})

    # --- dedupe -------------------------------------------------------------
    # These are REQUEUE CHAINS, not duplicate records: time_start differs in 90 of
    # 90 groups and state in 88 of 90. One id_job, several scheduling attempts.
    #
    # Keeping only the COMPLETED row would delete every job that never completed:
    # 59 of the 90 groups have no COMPLETED row. Those groups are mostly
    # (CANCELLED, NODE_FAIL) and (FAILED, NODE_FAIL) pairs, and they hold 24 of the
    # 31 NODE_FAIL jobs that carry GPU telemetry.
    #
    # So a job's outcome is its LAST attempt.
    for c in ("time_submit", "time_start", "time_end"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    s["_ord"] = s.time_end.fillna(s.time_start).fillna(s.time_submit)

    # over ALL jobs, not only requeued ones -- a job that hit NODE_FAIL once and
    # was never retried still has one node-failure attempt.
    chains = s.groupby("id_job").agg(
        attempts=("state", "size"),
        nodefail_attempts=("state", lambda x: int((x == 7).sum())))
    # WHERE each node failure happened. Collapsing a chain to its last attempt
    # keeps the final placement and throws away the machines the failed attempt
    # ran on -- and a requeued job's final machines are, by construction, NOT the
    # ones that died. Crediting the failure to them blames machines that did
    # nothing wrong. Recorded here before the collapse.
    _nf = s[s.state == 7].copy()
    _nf["_nodes"] = _nf.nodelist.fillna("").str.findall(r"r\d+-n\d+")
    _nf["_wall"] = (_nf.time_end - _nf.time_start).clip(lower=0).fillna(0)
    nf_where = _nf.groupby("id_job").agg(
        nodefail_nodes=("_nodes", lambda x: sorted({n for l in x for n in l})),
        # exact: every failed attempt ran on ONE machine, so we know which died.
        # A failed 16-machine attempt names 16 candidates and Slurm does not say
        # which of them failed, so crediting all 16 would blame 15 healthy ones.
        nodefail_exact=("_nodes", lambda x: all(len(l) == 1 for l in x)),
        nodefail_last_end=("time_end", "max"),
        # wall-clock seconds the FAILED attempts ran before the machine died. A
        # requeued job that later completed lost only these; its own gpu_hours
        # describe the successful retry, which was not lost at all.
        nodefail_wall_sec=("_wall", "sum"))
    s = (s.sort_values("_ord", kind="stable")
           .groupby("id_job", as_index=False, sort=False).tail(1)
           .drop(columns="_ord"))
    assert s.id_job.is_unique, f"id_job still not unique: {s.id_job.duplicated().sum()} dups"

    # Requeue history is hardware signal: a job the scheduler had to restart four
    # times because the node kept dying says more about that node than its final
    # state does.
    s = s.merge(chains, on="id_job", how="left")
    s["attempts"] = s.attempts.fillna(1).astype(int)
    s["nodefail_attempts"] = s.nodefail_attempts.fillna(0).astype(int)
    # "this job was killed by a node failure at least once", regardless of how it
    # finally ended. 18 of the 24 such jobs end in CANCELLED or FAILED, so final
    # state alone loses most of the hardware signal.
    s["hit_node_failure"] = s.nodefail_attempts > 0
    s = s.merge(nf_where, on="id_job", how="left")
    s["nodefail_nodes"] = s.nodefail_nodes.apply(
        lambda v: list(v) if isinstance(v, (list, np.ndarray)) else [])
    s["nodefail_exact"] = s.nodefail_exact.fillna(False).astype(bool)

    s["state_name"] = s.state.map(STATE).fillna("UNKNOWN_" + s.state.astype(str))
    s["is_terminal"] = s.state_name.isin(TERMINAL)
    s["is_success"]  = s.state_name.isin(SUCCESSFUL)

    # --- mem_req: MEM_PER_CPU high-bit flag, in INTEGER arithmetic ---
    # float64 cannot hold the low bits above 2**63, so this must stay in integers.
    def _mem(v):
        if v is pd.NA or v is None or (isinstance(v, float) and np.isnan(v)):
            return (np.nan, False)
        try:
            iv = int(str(v).strip())
        except (TypeError, ValueError):
            return (np.nan, False)
        return (iv - MEM_PER_CPU_FLAG, True) if iv > MEM_PER_CPU_FLAG else (iv, False)

    dec = s.mem_req.map(_mem)
    s["mem_req_mb"] = [x[0] for x in dec]
    s["mem_req_is_per_cpu"] = [x[1] for x in dec]
    s["mem_req"] = pd.to_numeric(s.mem_req, errors="coerce")   # keep the raw column
    s["mem_req_total_mb"] = np.where(s.mem_req_is_per_cpu,
                                     s.mem_req_mb * s.cpus_req, s.mem_req_mb)

    # --- times are RELATIVE offsets; -1 means "never happened" ---
    for c in ("time_submit","time_eligible","time_start","time_end"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
        s.loc[s[c] < 0, c] = np.nan   # -1 means "never happened"
    s.loc[s.time_eligible > 1e9, "time_eligible"] = np.nan     # out-of-range sentinel
    # --- array membership: decode the "not an array job" sentinel ---
    # Slurm writes id_array_job = 0 and id_array_task = NO_VAL (4294967294) on
    # every job that is not part of an array. The release ANONYMISES those values
    # like any other id, so they arrive as ordinary-looking integers and look like
    # the largest array on the cluster: 35,155 jobs (239,892 raw rows) from 192
    # different users, all sharing ONE task id. A real array is one submission by
    # one person with a distinct task id per element; every other group in the
    # data satisfies that. So the sentinel is identified by its shape rather than
    # by hardcoding an anonymised hash: the group that spans many users while
    # carrying a single task id. Left in, it would make one "array" own a third of
    # the cluster.
    _grp = s.groupby("id_array_job").agg(_u=("id_user", "nunique"),
                                         _t=("id_array_task", "nunique"),
                                         _n=("id_job", "size"))
    _sent = _grp[(_grp._u > 1) & (_grp._t == 1) & (_grp._n > 1000)].index
    s["is_array_task"] = ~s.id_array_job.isin(_sent) & s.id_array_job.notna()
    s.loc[~s.is_array_task, ["id_array_job", "id_array_task"]] = np.nan

    s["wait_sec"]     = s.time_start - s.time_submit
    s["walltime_sec"] = s.time_end   - s.time_start
    s.loc[s.wait_sec < 0, "wait_sec"] = np.nan

    # PRIMARY node only -- the first entry of the nodelist literal. Named
    # explicitly because 1,472 jobs span more than one node and carry 27.8% of the
    # cluster's GPU-hours; calling this column `node` invited attributing a whole
    # 8-node job to one machine, which is how a 2-GPU node ended up credited with
    # 7,258 GPU-hours against a 6,004 ceiling. Per-node attribution comes from
    # gpus.parquet, which has one row per (job, GPU) and a truthful `Node`.
    s["primary_node"] = (s.nodelist.fillna("").str.extract(r"'([^']+)'", expand=False))
    s["n_nodes_listed"] = s.nodelist.fillna("").str.count(r"'[^']+'")
    return s


def load_dcgm():
    d = pd.read_csv(RAW/"dcgm.csv")
    assert set(d.gpu_id.unique()) <= {0,1}, f"gpu_id outside {{0,1}}: {d.gpu_id.unique()}"
    d["gpu_hours"] = d.totalexecutiontime_sec / 3600
    # energyconsumed_joules does not integrate -- derive instead (report Sec.3)
    d["energy_wh"] = d.powerusage_watts_avg * d.totalexecutiontime_sec / 3600
    d["mem_used_frac"] = d.maxgpumemoryused_bytes / V100_MEM_BYTES
    return d


def build():
    s, d = load_scheduler(), load_dcgm()

    agg = d.groupby("id_job").agg(
        gpu_count        = ("gpu_id", "size"),
        gpu_hours        = ("gpu_hours", "sum"),
        energy_wh        = ("energy_wh", "sum"),
        exec_sec         = ("totalexecutiontime_sec", "max"),
        sm_util_avg      = ("smutilization_pct_avg", "mean"),
        sm_util_max      = ("smutilization_pct_max", "max"),
        mem_util_avg     = ("memoryutilization_pct_avg", "mean"),
        max_gpu_mem_used = ("maxgpumemoryused_bytes", "max"),
        mem_used_frac    = ("mem_used_frac", "max"),
        watts_avg        = ("powerusage_watts_avg", "mean"),
        watts_max        = ("powerusage_watts_max", "max"),
        pcie_rx_avg      = ("pcierxbandwidth_megabytes_avg", "mean"),
        pcie_tx_avg      = ("pcietxbandwidth_megabytes_avg", "mean"),
        n_nodes_dcgm     = ("Node", "nunique"),
    ).reset_index()

    jobs = agg.merge(s, on="id_job", how="left", validate="one_to_one")

    # `gpu_hours` above is MEASURED -- the sum of DCGM execution time across the
    # job's GPU rows. It is the better number and it is what every dollar figure in
    # the challenge uses. `gpu_hours_alloc` below is the other reading,
    # `gpu_count x hours`: the two disagree by more than 10% on 5,219 jobs (7%),
    # worst case 19.5x, because DCGM folds every requeue attempt under one job id
    # while the scheduler keeps only the last. Both are kept, named for what they
    # are; `gpu_hours_ratio` is the one over the other.
    jobs["gpu_hours_alloc"] = jobs.gpu_count * jobs.walltime_sec / 3600.0
    jobs["gpu_hours_ratio"] = jobs.gpu_hours / jobs.gpu_hours_alloc.replace(0, np.nan)
    # gpu-level table carries the scheduler context each row needs
    gpus = d.merge(s[["id_job","id_user","state","state_name","is_success",
                      "time_submit","time_start","partition"]],
                   on="id_job", how="left", validate="many_to_one")

    jobs.to_parquet(OUT/"jobs.parquet", index=False)
    gpus.to_parquet(OUT/"gpus.parquet", index=False)

    print(f"jobs.parquet  {jobs.shape}   gpu-hours={jobs.gpu_hours.sum():,.0f}")
    print(f"gpus.parquet  {gpus.shape}")
    print(f"unmatched to scheduler: {jobs.state_name.isna().sum()}")
    print(f"\nstate x gpu-hours:\n{jobs.groupby('state_name').gpu_hours.sum().sort_values(ascending=False).round(0)}")
    return jobs, gpus


if __name__ == "__main__":
    build()
