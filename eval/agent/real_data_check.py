"""Reproduce the prior offline trial; never pretend this is A→C integration.

Reads two official prepared tables, writes aggregate receipts only to a private
exclusive output. No A calculators or private source rows enter Git.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def semantic_digest(path):
    # Exact official checksum algorithm: compression-independent, file-order values.
    digest = hashlib.sha256()
    table = pq.read_table(path)
    for column in table.column_names:
        digest.update(json.dumps([column, table.column(column).to_pylist()], default=str, separators=(",", ":")).encode())
    return digest.hexdigest()


def check(data, expected_path):
    expected = {line.split()[1]: line.split()[0] for line in expected_path.read_text().splitlines() if line.strip() and not line.startswith("#")}
    names = ["prepped/jobs.parquet", "prepped/gpus.parquet"]
    hashes = {name: semantic_digest(data / name) for name in names}
    matches = {name: hashes[name] == expected.get(name) for name in names}
    if not all(matches.values()):
        raise ValueError("Prepared source tables do not match the pinned official value hashes; prior snapshot references do not apply")
    jobs = pd.read_parquet(data / names[0])
    eligible = jobs.loc[(jobs.state_name == "COMPLETED") & jobs.sm_util_avg.eq(0) & jobs.sm_util_max.eq(0) & jobs.gpu_hours.gt(1)]
    groups = {"zero_memory": eligible.loc[eligible.max_gpu_mem_used.eq(0)],
              "positive_memory": eligible.loc[eligible.max_gpu_mem_used.gt(0)],
              "unknown_memory": eligible.loc[eligible.max_gpu_mem_used.isna()]}
    summary = lambda frame: {"jobs": len(frame), "recorded_gpu_hours": float(frame.gpu_hours.sum())}
    totals = summary(eligible)
    partitions = {key: summary(frame) for key, frame in groups.items()}
    checks = {
        "pinned_prepared_hashes": all(matches.values()),
        "unique_physical_jobs": not eligible.id_job.duplicated().any(),
        "prior_cohort_count": totals["jobs"] == 463,
        "prior_cohort_hours": math.isclose(totals["recorded_gpu_hours"], 11986.121408333333),
        "prior_zero_memory_count": partitions["zero_memory"]["jobs"] == 287,
        "prior_zero_memory_hours": math.isclose(partitions["zero_memory"]["recorded_gpu_hours"], 6881.705525),
        "prior_positive_memory_count": partitions["positive_memory"]["jobs"] == 176,
        "prior_positive_memory_hours": math.isclose(partitions["positive_memory"]["recorded_gpu_hours"], 5104.415883333333),
        "memory_count_reconciles": sum(p["jobs"] for p in partitions.values()) == totals["jobs"],
        "memory_hours_reconcile": math.isclose(sum(p["recorded_gpu_hours"] for p in partitions.values()), totals["recorded_gpu_hours"]),
        "no_cancelled_or_failed_jobs": eligible.state_name.eq("COMPLETED").all(),
        "finite_positive_recorded_hours": eligible.gpu_hours.map(lambda n: math.isfinite(n) and n > 1).all(),
    }
    return {"scope": "Offline prepared-table reproduction only; not a real A audit or a five-file gate", "prepared_value_hashes": hashes,
            "checks": {k: bool(v) for k, v in checks.items()}, "historical_exposure": totals, "memory_partition": partitions,
            "limitations": ["No completed workload replay, causal attribution, demonstrated CPU compatibility or savings.",
                            "The three generator outputs were not verified here; full source identity and MCP findings remain unverified.",
                            "Broad eligibility remains unchanged; memory partition is only a proposed pilot prioritization aid."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect", type=Path, default=Path(__file__).resolve().parents[2] / "data/checksums.txt")
    args = parser.parse_args()
    report = check(args.data, args.expect)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(json.dumps({"passed": sum(report["checks"].values()), "total": len(report["checks"]), "scope": report["scope"]}))
    raise SystemExit(0 if all(report["checks"].values()) else 1)


if __name__ == "__main__":
    main()
