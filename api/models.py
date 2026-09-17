"""Response models.

Layer A follows MantisGrid's production API, except where
api/README.md lists a deviation (RuleTemplate fields, edge types, how causal
answers are computed).
Layer B is the proposed business layer and does not exist in the product.
"""
import datetime as dt
from typing import Any, Literal

import pydantic

Kind = Literal["fact", "judgment", "simulated"]


# --------------------------------------------------------------- Layer A
class Finding(pydantic.BaseModel):
    id: str
    integrationId: str
    enterpriseId: str
    detectorId: str
    shortDescription: str
    longDescription: str
    impactDescription: str
    resourceIds: list[str]
    rootCauses: list[str] = []
    status: str
    severity: Literal["CRITICAL", "HIGH", "LOW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    category: Literal["SECURITY", "COMPLIANCE", "PERFORMANCE", "CONFIG",
                      "AVAILABILITY", "COST"]
    priority: str
    detectionTime: str
    isActive: bool
    metadata: dict[str, Any]


class FindingsRequest(pydantic.BaseModel):
    integration_id: str | None = None
    detector_id: str | None = None
    category: str | None = None
    severity: str | None = None
    resource_id: str | None = None
    limit: int = 100
    offset: int = 0


class FindingsResponse(pydantic.BaseModel):
    success: bool = True
    total: int
    findings: list[Finding]


class DetectResponse(pydantic.BaseModel):
    success: bool = True
    message: str = "Detection completed"
    results: dict[str, int] = {}


class GraphNode(pydantic.BaseModel):
    node_id: str
    resource_id: str
    resource_name: str = ""
    metric_name: str = ""


class GraphEdge(pydantic.BaseModel):
    source_id: str
    target_id: str
    source_name: str = ""
    target_name: str = ""


class StructuralGraph(pydantic.BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    start_nodes: list[str] = []
    resource_adjacencies: dict[str, list[str]] = {}
    resource_types: dict[str, str] = {}
    rule_id: str | None = None


class NeighborRequest(pydantic.BaseModel):
    integration_id: str | None = None
    resource_ids: list[str]
    hop_count: int = 1


class NeighborResponse(pydantic.BaseModel):
    success: bool = True
    message: str = "Neighbor lookup completed"
    graphs: list[StructuralGraph] | None = None


class Culprit(pydantic.BaseModel):
    resource_id: str
    node: str
    type: str
    score: float


class CausalChainHop(pydantic.BaseModel):
    resource_id: str
    metric_name: str
    pattern: str
    change_pct: float = 0.0
    z_score: float = 0.0


class CausalFinding(pydantic.BaseModel):
    root_cause: str
    culprit: list[Culprit] | None = None
    causal_chain: list[CausalChainHop] | None = None
    confidence: float = 0.0
    algorithm_agreement: dict[str, int] | None = None
    run_seconds: float = 0.0


class CausalRequest(pydantic.BaseModel):
    integration_id: str | None = None
    finding_id: str
    hop_count: int = 3


class CausalResponse(pydantic.BaseModel):
    success: bool = True
    # Most findings have no causal chain; `message` says why the list is empty.
    message: str = "Causal analysis completed"
    findings: list[CausalFinding] | None = None


class RuleTemplate(pydantic.BaseModel):
    rule_id: str
    name: str
    category: str
    summary: str
    short_help: str = ""
    can_auto_remediate: bool = False
    # A rule that ran and found nothing is listed as CLEAR rather than omitted.
    status: str = "ACTIVE"          # ACTIVE (findings present) | CLEAR (none)
    findings: int = 0


class RuleTemplatesResponse(pydantic.BaseModel):
    success: bool = True
    rules: list[RuleTemplate]


# --------------------------------------------------------------- Layer B
class PriceBook(pydantic.BaseModel):
    version: str = "2026-Q3"
    usd_per_gpu_hour: float = 2.50
    usd_per_kwh: float = 0.15
    usd_per_engineer_hour: float = 95.00
    epoch_offset: int = 0


class Monetized(pydantic.BaseModel):
    amount: float
    currency: str = "USD"
    price_book_version: str


class Window(pydantic.BaseModel):
    start: str
    end: str
    granularity: str = "1d"


class Provenance(pydantic.BaseModel):
    signals: list[str]
    method: str
    caveat: str | None = None


class Envelope(pydantic.BaseModel):
    """Every Layer B response carries this.

    `kind` tells the reader what they are getting:
      fact       deterministic, recomputable from the raw data
      judgment   a model said so; `confidence` is populated
      simulated  synthetic, no real signal underneath
    """
    metric: str
    window: Window
    unit: str
    value: float | None = None
    rows: list[dict[str, Any]] | None = None
    monetized: Monetized | None = None
    kind: Kind
    provenance: Provenance
    confidence: float | None = None


class Recommendation(pydantic.BaseModel):
    id: str
    title: str
    action: str
    estimated_savings: Monetized
    estimated_savings_gpu_hours: float
    effort: Literal["low", "medium", "high"]
    confidence: float
    finding_ids: list[str]
    kind: Kind = "judgment"


class RecommendationsResponse(pydantic.BaseModel):
    recommendations: list[Recommendation]
