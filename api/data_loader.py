"""Load the projected layer into memory once, at import.

Everything the API serves is a deterministic function of files on disk, so all
aggregation happens here at cold start rather than per request. On Lambda this
runs once per container, not once per invocation.
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PREP, SYN = ROOT / "data" / "prepped", ROOT / "data" / "synthetic"

V100_PER_NODE = 2
SM_PROXY_CAVEAT = ("SM utilization is a proxy for useful work. A data-loader-bound "
                   "or communication-bound job does real work at low SM occupancy.")


class Store:
    def __init__(self):
        self.jobs = pd.read_parquet(PREP / "jobs.parquet")
        self.jobs = self.jobs[self.jobs.state_name.notna()].copy()
        self.jobs["is_success"] = self.jobs.is_success.fillna(False).astype(bool)
        self.jobs["util"] = self.jobs.sm_util_avg.clip(0, 100) / 100

        self.resources = pd.read_parquet(SYN / "resources.parquet")
        self.edges = pd.read_parquet(SYN / "edges.parquet")
        self.findings = json.loads((SYN / "findings.json").read_text())

        # Stable join keys back to jobs.parquet and the node list, so a finding
        # can be joined without parsing the job id out of its prose.
        pods = self.resources[self.resources.type == "k8s:pod"]
        nodes = self.resources[self.resources.type == "k8s:node"]
        rid_to_job = dict(zip(pods.id, pods.resourceId))
        rid_to_node = dict(zip(nodes.id, nodes.name))
        for f in self.findings:
            md = f.setdefault("metadata", {})
            for r in f.get("resourceIds", []):
                if "job_id" not in md and r in rid_to_job:
                    try:
                        md["job_id"] = int(rid_to_job[r])
                    except (TypeError, ValueError):
                        md["job_id"] = str(rid_to_job[r])
                if "node" not in md and r in rid_to_node:
                    md["node"] = rid_to_node[r]

        self.by_id = {r.id: r for r in self.resources.itertuples(index=False)}
        self.name_of = dict(zip(self.resources.id, self.resources.name))
        self.type_of = dict(zip(self.resources.id, self.resources.type))

        j = self.jobs
        self.allocated = float(j.gpu_hours.sum())
        self.computed = float((j.gpu_hours * j.util).sum())
        ok = j[j.is_success]
        self.computed_completed = float((ok.gpu_hours * ok.util).sum())

        # window, in real dates -- the price book carries the epoch offset
        self.t0, self.t1 = float(j.time_submit.min()), float(j.time_end.max())

    # ---- aggregations the endpoints need ----
    def waste_rows(self):
        g = self.jobs.groupby("state_name").gpu_hours.sum().sort_values(ascending=False)
        return [{"state": k, "gpu_hours": round(float(v), 1),
                 "share": round(float(v / self.allocated), 4)} for k, v in g.items()]

    def queue(self):
        w = self.jobs.wait_sec.dropna()
        return {"p50_sec": float(w.median()), "p90_sec": float(w.quantile(.90)),
                "p99_sec": float(w.quantile(.99)), "max_sec": float(w.max()),
                "total_wait_hours": float(w.sum() / 3600), "n_jobs": int(len(w))}

    def scaling(self):
        band = pd.cut(self.jobs.gpu_count, [0, 1, 2, 4, 8, 16, 64],
                      labels=["1", "2", "3-4", "5-8", "9-16", "17-64"])
        g = self.jobs.groupby(band, observed=True).agg(
            jobs=("gpu_hours", "size"), gpu_hours=("gpu_hours", "sum"),
            median_sm_util=("sm_util_avg", "median"),
            share_under_5pct=("sm_util_avg", lambda x: float((x < 5).mean())),
            share_over_80pct=("sm_util_avg", lambda x: float((x > 80).mean())))
        return [{"gpu_count_band": str(i), "jobs": int(r.jobs),
                 "gpu_hours": round(float(r.gpu_hours), 1),
                 "median_sm_util_pct": round(float(r.median_sm_util), 1),
                 "share_under_5pct": round(r.share_under_5pct, 3),
                 "share_over_80pct": round(r.share_over_80pct, 3)}
                for i, r in g.iterrows()]

    def findings_by_resource(self):
        """finding count and impact per resource id."""
        out = {}
        for f in self.findings:
            for rid_ in f["resourceIds"]:
                e = out.setdefault(rid_, {"count": 0, "impact_gpu_hours": 0.0, "owners": []})
                e["count"] += 1
                if f["metadata"].get("impact_scope") == "job":
                    e["impact_gpu_hours"] += f["metadata"].get("impact_gpu_hours") or 0.0
                if f["metadata"].get("owner"):
                    e["owners"].append(f["metadata"]["owner"])
        return out


@lru_cache(maxsize=1)
def store() -> Store:
    return Store()
