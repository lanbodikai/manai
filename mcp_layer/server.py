"""Curated MCP server — hand-written tools over the MGAI API, for LLM agents.

The tools are hand-written (rather than auto-generated from the routes) so their
descriptions carry more than the shape of each response — they carry the
*epistemics* an agent needs to answer *"where should we cut GPU spend?"*:

* Layer A (``findings``, ``causal``, ``neighbor``, ``rules``) mirrors the
  production API. ``causal`` is trustworthy; it resolves a correlated
  cluster of findings to the one resource underneath.
* Layer B (``efficiency_summary``, ``waste_breakdown``, ``queue_latency``,
  ``scaling_efficiency``, ``underperforming``, ``recommendations``) is a proposed
  business layer. Every response carries ``kind``:
    - ``fact``      deterministic, recomputable from raw data — trust it.
    - ``judgment``  a model said so — check ``confidence`` and validate.
    - ``simulated`` synthetic, no real signal underneath.

The docstrings below are written to be read by the model at tool-selection time,
so it validates judgments (e.g. against ``causal``) instead of acting on them
blindly.

Tools call the FastAPI route functions **in-process** — no HTTP hop, no second
port, one shared in-memory ``store()``. Data loads once, on the first tool call.

Run it::

    python -m mcp_layer.server
    # or:  fastmcp run mcp_layer/server.py:mcp
    # HTTP:  fastmcp run mcp_layer/server.py:mcp --transport http --port 9000
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from api import main as api
from api import models as m

mcp = FastMCP(
    name="MGAI MCP",
    instructions=(
        "Tools over MantisGrid's GPU-efficiency API for the cluster-efficiency "
        "task: find where GPU spend is wasted.\n\n"
        "Two layers:\n"
        "- Layer A (findings, causal, neighbor, rules) mirrors the production "
        "API. `causal` is authoritative — it resolves correlated findings to "
        "one root cause.\n"
        "- Layer B (efficiency_summary, waste_breakdown, queue_latency, "
        "scaling_efficiency, underperforming, recommendations) is a proposed "
        "business layer. Every response carries `kind`: `fact` (trust it), "
        "`judgment` (a model said so — check `confidence` and validate against "
        "`causal` before acting), or `simulated` (synthetic).\n\n"
        "Rule of thumb: do not act on a `judgment` (rankings, recommendations) "
        "without checking it against the underlying `findings`/`causal` facts. "
        "The data is a four-month job *sample*; do not extrapolate to whole-cluster "
        "utilization."
    ),
)

# The default price book, surfaced so tools can advertise their defaults.
_PB = api.DEFAULT_PRICE_BOOK
GpuRate = Annotated[
    float,
    Field(description=f"USD per GPU-hour for monetization (default {_PB.usd_per_gpu_hour})."),
]
EngRate = Annotated[
    float,
    Field(description=f"USD per engineer-hour for monetization (default {_PB.usd_per_engineer_hour})."),
]


def _dump(model: Any) -> Any:
    """Pydantic model -> plain JSON-able dict (FastMCP serializes the return)."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model


# ============================================================ ops
@mcp.tool
def health() -> dict:
    """Liveness check. Returns store status and how many findings/resources are
    loaded. Call this first if other tools error, to confirm the data is present."""
    return api.health()


# ============================================================ Layer A — the real API
@mcp.tool
def list_findings(
    detector_id: str | None = None,
    category: Literal["SECURITY", "COMPLIANCE", "PERFORMANCE", "CONFIG",
                      "AVAILABILITY", "COST"] | None = None,
    severity: Literal["CRITICAL", "HIGH", "LOW"] | None = None,
    resource_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List detector findings (Layer A, deterministic fact).

    Findings are the raw evidence — each is one rule firing on one or more
    resources. Filter by `detector_id` (e.g. `rules::gpu-low-utilization`),
    `category` (COST/PERFORMANCE/AVAILABILITY are the useful ones here),
    `severity`, or a specific `resource_id`. Page with `limit`/`offset`.

    A finding's `rootCauses` links it upstream; pass a finding's `id` to `causal`
    to collapse a correlated cluster to its single cause. Use `list_rules` first
    to see which detectors fired."""
    req = m.FindingsRequest(
        detector_id=detector_id, category=category, severity=severity,
        resource_id=resource_id, limit=limit, offset=offset,
    )
    return _dump(api.findings(req))


@mcp.tool
def causal(finding_id: str, hop_count: int = 3) -> dict:
    """Root-cause analysis for one finding (Layer A, authoritative).

    This is the endpoint to trust. Given a finding `id`, it resolves the
    correlated cluster of findings that share a cause down to the single resource
    underneath (a machine, an array job, a person's workload, or a volume), with a
    computed `confidence` and the evidence chain.

    Many findings have no upstream cause; then `findings` is empty and `message`
    explains why. Findings from `rules::filesystem-latency-degraded`,
    `rules::array-mass-failure`, `rules::array-task-failure`,
    `rules::node-hardware-fault`, and attributed `rules::node-job-failure-burst`
    carry a chain.

    Use this to VALIDATE Layer B judgments: if `underperforming` or
    `recommendations` blames a node, check whether `causal` attributes the failures
    to the node or to something else (a person's job, a shared array)."""
    req = m.CausalRequest(finding_id=finding_id, hop_count=hop_count)
    return _dump(api.causal(req))


@mcp.tool
def neighbor(resource_ids: list[str], hop_count: int = 1) -> dict:
    """Structural graph around one or more resources (Layer A, fact).

    Returns the resource graph (nodes, typed edges, adjacencies) within
    `hop_count` hops of each starting `resource_id`. Edges: `RUNS_ON`,
    `OWNS` (array -> task pod), `CONTAINS` (user namespace -> pod), `MOUNTS`.
    Use it to understand what a resource is connected to before reasoning about
    blast radius or shared causes. Responses are capped at 500 nodes."""
    req = m.NeighborRequest(resource_ids=resource_ids, hop_count=hop_count)
    return _dump(api.neighbor(req))


@mcp.tool
def detect(integration_id: str = "default") -> dict:
    """Run detection and return the per-detector finding counts (Layer A, fact).

    A quick histogram: which detectors fired and how many findings each produced.
    Cheaper than paging `list_findings` when you only want the shape of the
    problem space. `list_rules` gives the same counts plus names, categories, and
    which rules evaluated CLEAR."""
    return _dump(api.detect(integration_id))


@mcp.tool
def list_rules() -> dict:
    """The full rule catalogue with status and finding counts (Layer A, fact).

    Every rule, including ones that found nothing (`status: CLEAR`) — knowing what
    was checked and came back clean matters as much as what fired. Each rule has a
    `category` (COST / PERFORMANCE / AVAILABILITY). Start here to map the terrain,
    then drill into `list_findings(detector_id=...)`."""
    return _dump(api.rules())


# ============================================================ Layer B — proposed business layer
@mcp.tool
def price_book() -> dict:
    """The default price book (USD per GPU-hour, kWh, engineer-hour).

    Reference values only. To model a different price, pass `usd_per_gpu_hour` /
    `usd_per_engineer_hour` to the tools that monetize (`efficiency_summary`,
    `queue_latency`, `underperforming`, `recommendations`); their responses come
    back tagged `2026-Q3+custom`."""
    return _dump(api.get_price_book())


@mcp.tool
def efficiency_summary(usd_per_gpu_hour: GpuRate = _PB.usd_per_gpu_hour) -> dict:
    """The capacity waterfall: allocated -> computed -> computed_completed GPU-hours
    (Layer B, `kind=fact`).

    The headline number for "how much GPU did we pay for vs. actually use". Rows
    give each stage in GPU-hours and as a share of allocated. Monetized at
    `usd_per_gpu_hour`. Anchored at ALLOCATED (not purchased) — this is a job
    sample, so a purchased-capacity denominator is not defensible. SM utilization
    is a proxy: a data-loader- or comms-bound job does real work at low SM
    occupancy."""
    return _dump(api.efficiency_summary(usd_per_gpu_hour))


@mcp.tool
def waste_breakdown() -> dict:
    """GPU-hours partitioned by job outcome/state (Layer B, `kind=fact`).

    Deliberately NOT summed into a single "wasted" total: CANCELLED is often
    deliberate early stopping, not waste. Deciding which rows count as waste is
    your call — read the states and decide."""
    return _dump(api.waste_breakdown())


@mcp.tool
def queue_latency(usd_per_engineer_hour: EngRate = _PB.usd_per_engineer_hour) -> dict:
    """Queue-wait percentiles, monetized as engineer time (Layer B, `kind=fact`).

    p50/p90/p99/max wait in seconds plus total wait-hours. Monetized at
    engineer-hour cost, not GPU cost — the tail is salary (people waiting), not
    idle silicon."""
    return _dump(api.queue_latency(usd_per_engineer_hour))


@mcp.tool
def scaling_efficiency() -> dict:
    """Utilization by job width / GPU-count band (Layer B, `kind=judgment`,
    confidence ~0.55).

    NOT strong-scaling efficiency: there is no per-job throughput here, so no T(1)
    baseline exists. This is utilization conditioned on job width. The distribution
    is BIMODAL — read `share_under_5pct` and `share_over_80pct`, not the median."""
    return _dump(api.scaling_efficiency())


@mcp.tool
def underperforming(
    entity_type: Literal["user", "node"] = "user",
    limit: int = 10,
    usd_per_gpu_hour: GpuRate = _PB.usd_per_gpu_hour,
) -> dict:
    """Ranked underperforming users or nodes (Layer B, `kind=judgment`).

    Aggregates findings per entity. IMPORTANT: it does NOT read `rootCauses`, so
    correlated findings that share one cause are counted as independent problems —
    a node can look bad because one person's job kept crashing on it. Before acting
    on a name here, validate with `causal` on the relevant findings.

    `entity_type='user'` ranks by unsuccessful GPU-hours (monetized);
    `entity_type='node'` ranks by finding count and impact GPU-hours."""
    return _dump(api.underperforming(entity_type, limit, usd_per_gpu_hour))


@mcp.tool
def recommendations(usd_per_gpu_hour: GpuRate = _PB.usd_per_gpu_hour) -> dict:
    """Actionable cost-cut recommendations with estimated savings (Layer B,
    `kind=judgment`).

    Each recommendation has an action, estimated savings (GPU-hours + USD), an
    effort level, a confidence, and the `finding_ids` it rests on. These are
    model judgments built on aggregated findings — pull the cited findings and run
    `causal` before treating a saving as real. Estimates use `usd_per_gpu_hour`."""
    return _dump(api.recommendations(usd_per_gpu_hour))


if __name__ == "__main__":
    mcp.run()
