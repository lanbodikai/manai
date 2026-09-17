"""MGAI client. The fetch layer is done — build on top of it.

    from mgai_client import MGAI
    mg = MGAI()

    mg.efficiency_summary()                     # the capacity waterfall
    mg.waste_breakdown()                        # GPU-hours by outcome
    mg.findings(detector_id="rules::gpu-low-utilization")
    mg.causal(finding_id)                       # root-cause for one finding

Every method returns parsed JSON. `*_df` variants return DataFrames where a table
is the obvious shape.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

BASE = os.environ.get("MGAI_URL", "http://localhost:8000")


class MGAI:
    def __init__(self, base_url: str = BASE, timeout: int = 30):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.s = requests.Session()

    # ---- plumbing ----
    def _get(self, path: str, **params) -> Any:
        r = self.s.get(f"{self.base}{path}", params=params or None, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict) -> Any:
        r = self.s.post(f"{self.base}{path}", json=body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def health(self):
        return self._get("/health")

    # ---- Layer A: MantisGrid's real API ----
    def findings(self, *, detector_id=None, category=None, severity=None,
                 resource_id=None, limit=100, offset=0) -> list[dict]:
        body = {"detector_id": detector_id, "category": category,
                "severity": severity, "resource_id": resource_id,
                "limit": limit, "offset": offset}
        return self._post("/v1/events/findings",
                          {k: v for k, v in body.items() if v is not None})["findings"]

    def all_findings(self, page: int = 500, **filters) -> list[dict]:
        """Every finding matching the filters, paged."""
        out, offset = [], 0
        while True:
            batch = self.findings(limit=page, offset=offset, **filters)
            out += batch
            if len(batch) < page:
                return out
            offset += page

    def findings_df(self, **filters) -> pd.DataFrame:
        """Flat table with metadata unpacked — the shape you usually want."""
        f = self.all_findings(**filters)
        if not f:
            return pd.DataFrame()
        df = pd.json_normalize(f, sep="_")
        df["detectionTime"] = pd.to_datetime(df.detectionTime, format="mixed", utc=True)
        return df

    def neighbor(self, resource_ids: list[str], hop_count: int = 1):
        return self._post("/v1/neighbor", {"resource_ids": resource_ids,
                                           "hop_count": hop_count})

    def causal(self, finding_id: str):
        """Root-cause analysis for one finding. Returns [] when the finding has no
        known root cause."""
        return self._post("/v1/causal", {"finding_id": finding_id})["findings"]

    def rules(self):
        return self._get("/v1/policies/rules")["rules"]

    # ---- Layer B: proposed business layer ----
    def price_book(self):
        return self._get("/v1/price-book")

    # The price book is shared and read-only -- one team's scenario must not move
    # another team's numbers. Pass a rate to the endpoint instead; the response
    # comes back tagged `2026-Q3+custom`.
    def efficiency_summary(self, usd_per_gpu_hour: float | None = None):
        return self._get("/v1/efficiency/summary",
                         **({} if usd_per_gpu_hour is None
                            else {"usd_per_gpu_hour": usd_per_gpu_hour}))

    def waste_breakdown(self):
        return self._get("/v1/waste/breakdown")

    def queue_latency(self, usd_per_engineer_hour: float | None = None):
        return self._get("/v1/queue/latency",
                         **({} if usd_per_engineer_hour is None
                            else {"usd_per_engineer_hour": usd_per_engineer_hour}))

    def scaling_efficiency(self):
        return self._get("/v1/scaling/efficiency")

    def underperforming(self, entity_type: str = "user", limit: int = 10,
                        usd_per_gpu_hour: float | None = None):
        return self._get("/v1/resources/underperforming",
                         entity_type=entity_type, limit=limit,
                         **({} if usd_per_gpu_hour is None
                            else {"usd_per_gpu_hour": usd_per_gpu_hour}))

    def recommendations(self, usd_per_gpu_hour: float | None = None):
        return self._get("/v1/recommendations",
                         **({} if usd_per_gpu_hour is None
                            else {"usd_per_gpu_hour": usd_per_gpu_hour}))["recommendations"]

    # ---- convenience ----
    def rows(self, envelope: dict) -> pd.DataFrame:
        """Layer B responses carry their table in `rows`."""
        return pd.DataFrame(envelope.get("rows") or [])

    def usd(self, gpu_hours: float) -> float:
        return gpu_hours * self.price_book()["usd_per_gpu_hour"]


if __name__ == "__main__":
    mg = MGAI()
    print(mg.health())
    e = mg.efficiency_summary()
    print(f"\n{e['metric']}  ({e['kind']})")
    for r in e["rows"]:
        print(f"   {r['label']:20} {r['gpu_hours']:>10,.0f}  {r['share']:>6.1%}")
    print(f"\n   {e['provenance']['caveat']}")
