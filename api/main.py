"""MGAI facsimile API.

Layer A mirrors MantisGrid's production API (oracle/routers).
Layer B is the proposed business layer -- it does not exist in the product.

The OpenAPI page at /docs is the challenge spec.
"""
import datetime as dt
import os
import uuid
import json
from collections import Counter

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from . import models as m
from .data_loader import SM_PROXY_CAVEAT, store

# Rate limiting is off unless MGAI_RATE_LIMIT is set (e.g. "60/minute"). The
# budget is per IP, per endpoint.
_RATE = os.environ.get("MGAI_RATE_LIMIT", "").strip()
limiter = Limiter(key_func=get_remote_address,
                  default_limits=[_RATE] if _RATE else [], enabled=bool(_RATE))

app = FastAPI(
    title="MGAI API (hackathon facsimile)",
    version="1.0.0",
    description=(
        "**Layer A** mirrors MantisGrid's production API — same paths and "
        "response models as the real product.\n\n"
        "**Layer B** is a proposed business layer that does **not** exist in the "
        "product yet. Every Layer B response carries `kind`: `fact` (deterministic, "
        "recomputable), `judgment` (a model said so — check `confidence`), or "
        "`simulated` (synthetic, no real signal underneath).\n\n"
        "Judgment endpoints are not always right. Validate them.\n\n"
        "**Pricing:** Layer B endpoints accept optional `usd_per_gpu_hour` and "
        "`usd_per_engineer_hour` query parameters to override defaults. This lets "
        "you model different pricing scenarios without affecting other users.\n\n"
        "**Rate limit:** none by default. Set `MGAI_RATE_LIMIT` (e.g. `60/minute`) "
        "to enable one, applied per IP per endpoint.\n\n"
        "---\n\n"
        "**Data attribution.** Workload telemetry is from the **MIT SuperCloud "
        "TX-GAIA** dataset (HPCA'22 release), accompanying *Enabling Workloads on "
        "Large-Scale GPU Accelerated Systems: Characterization, Opportunities, and "
        "Implications*, and is used under "
        "[CC BY-NC-ND 4.0](http://creativecommons.org/licenses/by-nc-nd/4.0/). "
        "The reliability layer (hardware-fault attribution, the storage incident) "
        "is synthetic and is ours, not MIT's — every synthetic record carries "
        "`metadata.synthetic = true`.\n\n"
        "The publishers note that the release is a *sample* of the workloads that "
        "ran on the system and is **not appropriate for estimating system "
        "utilization** or drawing broader conclusions about the cluster. Figures "
        "here describe this sample over its four-month window, not the cluster.\n\n"
        "Research sponsored by the United States Air Force Research Laboratory and "
        "the United States Air Force Artificial Intelligence Accelerator under "
        "Cooperative Agreement FA8750-19-2-1000."),
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
if _RATE:
    app.add_middleware(SlowAPIMiddleware)

# Default price book — immutable. Endpoints accept query params to override.
DEFAULT_PRICE_BOOK = m.PriceBook(epoch_offset=1750862959)


def _window() -> m.Window:
    s = store()
    f = lambda t: dt.datetime.fromtimestamp(t + DEFAULT_PRICE_BOOK.epoch_offset,
                                            dt.timezone.utc).strftime("%Y-%m-%d")
    return m.Window(start=f(s.t0), end=f(s.t1))


def _usd(gpu_hours: float, usd_per_gpu_hour: float, version: str) -> m.Monetized:
    return m.Monetized(amount=round(gpu_hours * usd_per_gpu_hour, 2),
                       price_book_version=version)


def _price_version(usd_per_gpu_hour: float, usd_per_engineer_hour: float) -> str:
    """Return version string indicating if custom pricing is in use."""
    if (usd_per_gpu_hour == DEFAULT_PRICE_BOOK.usd_per_gpu_hour and
        usd_per_engineer_hour == DEFAULT_PRICE_BOOK.usd_per_engineer_hour):
        return DEFAULT_PRICE_BOOK.version
    return f"{DEFAULT_PRICE_BOOK.version}+custom"


@app.get("/health", tags=["ops"])
def health():
    s = store()
    return {"status": "ok", "findings": len(s.findings), "resources": len(s.resources)}


# ============================================================ Layer A
@app.post("/v1/detect/{integration_id}", response_model=m.DetectResponse,
          tags=["Layer A — the real API"])
def detect(integration_id: str):
    return m.DetectResponse(results=dict(Counter(f["detectorId"] for f in store().findings)))


@app.post("/v1/events/findings", response_model=m.FindingsResponse,
          tags=["Layer A — the real API"])
def findings(req: m.FindingsRequest):
    out = store().findings
    if req.detector_id:
        out = [f for f in out if f["detectorId"] == req.detector_id]
    if req.category:
        out = [f for f in out if f["category"] == req.category]
    if req.severity:
        out = [f for f in out if f["severity"] == req.severity]
    if req.resource_id:
        out = [f for f in out if req.resource_id in f["resourceIds"]]
    total = len(out)
    return m.FindingsResponse(total=total,
                              findings=out[req.offset:req.offset + req.limit])


@app.post("/v1/neighbor", response_model=m.NeighborResponse,
          tags=["Layer A — the real API"])
def neighbor(req: m.NeighborRequest):
    s = store()
    adj: dict[str, set[str]] = {}
    for e in s.edges.itertuples(index=False):
        adj.setdefault(e.sourceId, set()).add(e.destinationId)
        adj.setdefault(e.destinationId, set()).add(e.sourceId)

    graphs = []
    for start in req.resource_ids:
        seen, frontier = {start}, {start}
        for _ in range(max(1, req.hop_count)):
            nxt = set()
            for n in frontier:
                nxt |= adj.get(n, set())
            frontier = nxt - seen
            seen |= frontier
            if not frontier:
                break
        seen = set(list(seen)[:500])          # keep responses answerable
        edges = [m.GraphEdge(source_id=e.sourceId, target_id=e.destinationId,
                             source_name=s.name_of.get(e.sourceId, ""),
                             target_name=s.name_of.get(e.destinationId, ""))
                 for e in s.edges.itertuples(index=False)
                 if e.sourceId in seen and e.destinationId in seen]
        graphs.append(m.StructuralGraph(
            nodes=[m.GraphNode(node_id=n, resource_id=n,
                               resource_name=s.name_of.get(n, "")) for n in seen],
            edges=edges, start_nodes=[start],
            resource_types={n: s.type_of.get(n, "") for n in seen}))
    return m.NeighborResponse(graphs=graphs)


@app.post("/v1/causal", response_model=m.CausalResponse,
          tags=["Layer A — the real API"])
def causal(req: m.CausalRequest):
    """Root-cause analysis. This endpoint is correct -- it resolves a correlated
    cluster of findings to the single resource underneath."""
    s = store()
    f = next((x for x in s.findings if x["id"] == req.finding_id), None)
    if f is None:
        raise HTTPException(404, "finding not found")
    if not f["rootCauses"]:
        return m.CausalResponse(
            findings=[],
            message=(
                "No causal chain for this finding. Causal analysis resolves a "
                "correlated cluster of findings that share a root cause; a finding "
                "with no linked rootCauses has nothing upstream to resolve to. "
                "Findings from 'rules::filesystem-latency-degraded', "
                "'rules::array-mass-failure', 'rules::array-task-failure', "
                "'rules::node-hardware-fault' and attributed "
                "'rules::node-job-failure-burst' findings carry one."))

    root = f["rootCauses"][0]
    root_name = s.name_of.get(root, root)
    kind = s.type_of.get(root)
    if kind == "k8s:job":
        return _causal_array(s, root, root_name)
    if kind == "k8s:node":
        return _causal_machine(s, f, root, root_name)
    if kind == "k8s:namespace":
        return _causal_person(s, f, root, root_name)
    return _causal_volume(s, f, root, root_name)


def _hw_finding_for(s, f, root):
    """The node-hardware-fault finding covering this finding's episode."""
    md = f["metadata"]
    return next((x for x in s.findings
                 if x["detectorId"] == "rules::node-hardware-fault"
                 and root in x.get("rootCauses", [])
                 and x["metadata"].get("window_start") == md.get("window_start")),
                f if f["detectorId"] == "rules::node-hardware-fault" else None)


def _causal_machine(s, f, root: str, root_name: str) -> m.CausalResponse:
    """A burst attributed to the machine. Every number comes from the evidence the
    rule computed: people whose crashes here carry a status they do not produce
    anywhere else."""
    hw = _hw_finding_for(s, f, root)
    if hw is None:
        return m.CausalResponse(findings=[], message=(
            f"{root_name} is named as root cause, but no hardware-fault evidence "
            f"was recorded for this episode."))
    md = hw["metadata"]
    ev = md.get("evidence", [])
    worst_else = max((e["with_status_elsewhere"] / e["jobs_elsewhere"]
                      for e in ev if e["jobs_elsewhere"]), default=0.0)
    confidence = round(1.0 - worst_else, 3)
    chain = [m.CausalChainHop(
        resource_id=root, metric_name=f"exit_status_{md['exit_status']}",
        pattern="failure_signature_unique_to_machine",
        change_pct=round(100.0 * md["failed"] / max(md["jobs"], 1), 1))]
    for e in ev:
        uid = e["user"].removeprefix("u-")
        chain.append(m.CausalChainHop(
            resource_id=next((k for k, v in s.name_of.items()
                              if v == f"ns/u-{uid}"), e["user"]),
            metric_name=f"exit_status_{md['exit_status']}_elsewhere",
            pattern="absent_on_every_other_machine",
            change_pct=round(100.0 * e["with_status_elsewhere"]
                             / max(e["jobs_elsewhere"], 1), 2)))
    return m.CausalResponse(
        message=(f"{len(ev)} different people crashed on {root_name} with exit "
                 f"status {md['exit_status']} ({md.get('exit_meaning', '')}), and "
                 f"none of them produces it anywhere else. Confidence is one minus "
                 f"the highest rate at which any of them hits that status "
                 f"elsewhere."),
        findings=[m.CausalFinding(
            root_cause=(f"{root_name} — {md.get('exit_meaning', 'abnormal exit')} "
                        f"crashes for {len(ev)} people who never hit it elsewhere; "
                        f"{md['failed']} of {md['jobs']} jobs failed"),
            culprit=[m.Culprit(resource_id=root, node=root_name, type="k8s:node",
                               score=confidence)],
            causal_chain=chain, confidence=confidence,
            algorithm_agreement=None, run_seconds=0.0)])


def _causal_person(s, f, root: str, root_name: str) -> m.CausalResponse:
    """A burst attributed to one person's work, with the machine cleared by
    comparison -- everyone else on it at the same time, or the same array's
    identical tasks on other machines."""
    md = f["metadata"]
    ev = md.get("attribution_evidence", {})
    node = md.get("node", "")
    node_id = next((k for k, v in s.name_of.items() if v == node), node)
    if ev.get("check") == "array_siblings":
        confidence = float(ev.get("array_sibling_failure_rate", 0.0))
        cleared = m.CausalChainHop(
            resource_id=node_id, metric_name="same_array_failure_rate_elsewhere",
            pattern="fails_on_other_machines_too",
            change_pct=round(100 * confidence, 1))
        why = (f"they had {node} to themselves, and the same array's tasks on other "
               f"machines failed {confidence:.0%} of the time")
    else:
        confidence = round(float(ev.get("user_failure_rate", 0))
                           - float(ev.get("others_failure_rate") or 0), 3)
        cleared = m.CausalChainHop(
            resource_id=node_id, metric_name="others_failure_rate_same_machine",
            pattern="machine_fine_for_everyone_else",
            change_pct=round(100 * float(ev.get("others_failure_rate") or 0), 1))
        why = (f"everyone else on {node} in the same hours failed "
               f"{float(ev.get('others_failure_rate') or 0):.0%} of the time, "
               f"against {float(ev.get('user_failure_rate', 0)):.0%} for them")
    return m.CausalResponse(
        message=(f"Attributed to one person's work: {why}. The machine is "
                 f"included in the chain as the thing that was ruled out."),
        findings=[m.CausalFinding(
            root_cause=(f"{root_name} — {float(ev.get('share_of_failures', 0)):.0%} "
                        f"of the failures on {node}; {why}"),
            culprit=[m.Culprit(resource_id=root, node=root_name,
                               type="k8s:namespace", score=confidence),
                     m.Culprit(resource_id=node_id, node=node, type="k8s:node",
                               score=round(1.0 - confidence, 3))],
            causal_chain=[m.CausalChainHop(
                resource_id=root, metric_name="user_failure_rate",
                pattern="concentrated_in_one_person",
                change_pct=round(100 * float(ev.get("user_failure_rate", 0)), 1)),
                cleared],
            confidence=confidence, algorithm_agreement=None, run_seconds=0.0)])


def _causal_array(s, root: str, root_name: str) -> m.CausalResponse:
    """A wiped-out array: many failed tasks, one submitted script.

    Every number here is COMPUTED from the findings that name this array as
    their root cause -- nothing is canned. The evidence that the cause is the
    array and not the machines is dispersion: if a node were at fault, the
    failures would concentrate on it. They are spread across many nodes, each
    carrying a small share, and they share one exit code.
    """
    from collections import Counter
    tasks = [x for x in s.findings
             if x["detectorId"] == "rules::array-task-failure"
             and root in x.get("rootCauses", [])]
    if not tasks:
        return m.CausalResponse(findings=[], message=(
            f"{root_name} is an array, but none of its tasks carry a failure "
            f"finding, so there is no correlated cluster to resolve."))
    rec = s.by_id.get(root)
    total = (json.loads(rec.metadata).get("tasks") if rec is not None else None) \
        or len(tasks)
    codes = Counter(x["metadata"].get("exit_code") for x in tasks)
    top_code, top_n = codes.most_common(1)[0]
    code_share = top_n / len(tasks)
    fail_frac = len(tasks) / total
    node_hits = Counter(r for x in tasks for r in x["resourceIds"][1:])
    n_nodes = len(node_hits)
    runtimes = sorted(x["metadata"].get("walltime_sec", 0.0) for x in tasks)
    med_run = runtimes[len(runtimes) // 2]
    confidence = round(fail_frac * code_share, 3)

    culprits = [m.Culprit(resource_id=root, node=root_name, type="k8s:job",
                          score=confidence)]
    for nid, hits in node_hits.most_common(4):
        culprits.append(m.Culprit(resource_id=nid, node=s.name_of.get(nid, ""),
                                  type=s.type_of.get(nid, ""),
                                  score=round(hits / len(tasks), 3)))
    return m.CausalResponse(
        message=(f"Resolved {len(tasks)} failure findings to one array. Node "
                 f"scores are each machine's share of the failures -- low and "
                 f"spread across {n_nodes} machines, which is the evidence "
                 f"against a node cause."),
        findings=[m.CausalFinding(
            root_cause=(f"{root_name} — {len(tasks)} of {total} tasks failed, "
                        f"{code_share:.0%} with exit code {top_code}, spread "
                        f"across {n_nodes} machines (median runtime "
                        f"{med_run:.0f}s)"),
            culprit=culprits,
            causal_chain=[
                m.CausalChainHop(resource_id=root,
                                 metric_name="task_failure_fraction",
                                 pattern="uniform_failure",
                                 change_pct=round(fail_frac * 100, 1)),
                m.CausalChainHop(resource_id=tasks[0]["resourceIds"][0],
                                 metric_name="exit_code",
                                 pattern="identical_exit_code",
                                 change_pct=round(code_share * 100, 1))],
            confidence=confidence, algorithm_agreement=None, run_seconds=0.0)])


def _causal_volume(s, f, root: str, root_name: str) -> m.CausalResponse:
    siblings = [x for x in s.findings if root in x.get("rootCauses", [])]
    nodes = [x["resourceIds"][0] for x in siblings if x["resourceIds"]]
    culprits = [m.Culprit(resource_id=root, node=root_name,
                          type=s.type_of.get(root, ""), score=0.88)]
    for n in nodes[:4]:
        culprits.append(m.Culprit(resource_id=n, node=s.name_of.get(n, ""),
                                  type=s.type_of.get(n, ""), score=0.31))
    md = f["metadata"]
    return m.CausalResponse(findings=[m.CausalFinding(
        root_cause=(f"{root_name} degraded — filesystem p99 latency rose "
                    f"{md.get('fs_latency_p99_ratio', 0)}x, affecting "
                    f"{len(siblings)} nodes"),
        culprit=culprits,
        causal_chain=[
            m.CausalChainHop(resource_id=root, metric_name="fs_latency_p99",
                             pattern="abrupt_rise",
                             change_pct=float(md.get("fs_latency_p99_ratio", 0)) * 100,
                             z_score=11.2),
            m.CausalChainHop(resource_id=nodes[0] if nodes else root,
                             metric_name="gpu_sm_utilization",
                             pattern="abrupt_drop", change_pct=-91.4, z_score=-7.8)],
        # NEUTRALISED FOR IP. The real algorithm names are MantisGrid's and
        # Layer A mirrors the real API, so naming them here discloses them.
        # Kai/Randolph to confirm this is far enough -- the *field* still says we
        # ensemble multiple causal methods and score their agreement.
        confidence=0.74, algorithm_agreement={"method_a": 3, "method_b": 2},
        run_seconds=4.31)])


@app.get("/v1/policies/rules", response_model=m.RuleTemplatesResponse,
         tags=["Layer A — the real API"])
def rules():
    """Every rule in the catalogue, including the ones that found nothing.

    A rule with zero findings is reported as CLEAR rather than omitted. Knowing
    what was checked and came back clean is worth as much as knowing what fired.
    """
    NAMES = {
        "rules::node-failure": ("Node failure", "AVAILABILITY"),
        "rules::node-elevated-failure-rate": ("Node elevated failure rate", "AVAILABILITY"),
        "rules::node-job-failure-burst": ("Node job failure burst", "AVAILABILITY"),
        "rules::node-hardware-fault": ("Node hardware fault", "AVAILABILITY"),
        "rules::filesystem-latency-degraded": ("Filesystem latency degraded", "AVAILABILITY"),
        "rules::gpu-low-utilization": ("GPU low utilization", "PERFORMANCE"),
        "rules::gpu-memory-oversized": ("GPU memory oversized", "PERFORMANCE"),
        "rules::gpu-never-computed": ("GPU allocated and never computed", "PERFORMANCE"),
        "rules::gpu-imbalance": ("GPU imbalance within a job", "PERFORMANCE"),
        "rules::wallclock-kill": ("Killed at the wall clock", "AVAILABILITY"),
        "rules::array-mass-failure": ("Array job mass failure", "AVAILABILITY"),
        "rules::array-task-failure": ("Array task failure", "AVAILABILITY"),
        "rules::gpu-not-needed": ("GPU allocated to a job that did not need one", "COST"),
        "rules::idle-interactive-session": ("Idle interactive session", "COST"),
        "rules::multi-node-low-utilization": ("Multi-node job at low utilization", "COST"),
        "rules::node-under-utilization-slo": ("Node under utilization SLO", "COST"),
        "rules::gpu-pcie-saturated": ("GPU PCIe bandwidth saturated", "PERFORMANCE"),
        "rules::user-repeat-failure": ("User repeat failure", "AVAILABILITY"),
        "rules::timelimit-overreservation": ("Time-limit over-reservation", "COST"),
        "rules::queue-starvation": ("Queue starvation", "COST"),
        "rules::queue-wait-p95-slo": ("Queue wait p95 SLO", "COST"),
        "rules::slow-cancel-of-idle-job": ("Slow cancel of idle job", "COST"),
        "rules::queue-weekly-peak": ("Weekly queue peak", "COST"),
        "rules::unsuccessful-gpu-spend": ("Unsuccessful GPU spend", "COST"),
    }
    counts = Counter(f["detectorId"] for f in store().findings)
    out = []
    for k, (name, cat) in NAMES.items():
        n = counts.get(k, 0)
        out.append(m.RuleTemplate(
            rule_id=k, name=name, category=cat, status="ACTIVE" if n else "CLEAR",
            findings=n,
            summary=(f"{n} active findings" if n else "Evaluated clean — no findings"),
            short_help="Deterministic rule; recomputable from raw data."))
    return m.RuleTemplatesResponse(rules=out)


# ============================================================ Layer B
@app.get("/v1/price-book", response_model=m.PriceBook, tags=["Layer B — proposed"])
def get_price_book():
    """Returns the default price book.

    To model different pricing scenarios, pass `usd_per_gpu_hour` and/or
    `usd_per_engineer_hour` query parameters to the endpoints that use pricing
    (efficiency/summary, queue/latency, resources/underperforming, recommendations).
    """
    return DEFAULT_PRICE_BOOK


@app.get("/v1/efficiency/summary", response_model=m.Envelope, tags=["Layer B — proposed"])
def efficiency_summary(
    usd_per_gpu_hour: float = Query(DEFAULT_PRICE_BOOK.usd_per_gpu_hour,
                                    description="Override GPU hourly rate for monetization")
):
    s = store()
    version = _price_version(usd_per_gpu_hour, DEFAULT_PRICE_BOOK.usd_per_engineer_hour)
    rows = [{"label": "allocated", "gpu_hours": round(s.allocated, 1), "share": 1.0},
            {"label": "computed", "gpu_hours": round(s.computed, 1),
             "share": round(s.computed / s.allocated, 4)},
            {"label": "computed_completed", "gpu_hours": round(s.computed_completed, 1),
             "share": round(s.computed_completed / s.allocated, 4)}]
    return m.Envelope(
        metric="capacity_waterfall", window=_window(), unit="gpu_hours",
        value=round(s.allocated, 1), rows=rows,
        monetized=_usd(s.allocated, usd_per_gpu_hour, version), kind="fact",
        provenance=m.Provenance(
            signals=["dcgm_sm_util", "slurm_alloc"],
            method="sm_weighted_integration@v1",
            caveat=(SM_PROXY_CAVEAT + " Anchored at ALLOCATED, not purchased — this "
                    "release is a job sample, so a purchased-capacity denominator is "
                    "not defensible.")))


@app.get("/v1/waste/breakdown", response_model=m.Envelope, tags=["Layer B — proposed"])
def waste_breakdown():
    s = store()
    return m.Envelope(
        metric="gpu_hours_by_outcome", window=_window(), unit="gpu_hours",
        rows=s.waste_rows(), kind="fact",
        provenance=m.Provenance(
            signals=["slurm_state", "dcgm_exec_time"], method="state_partition@v1",
            caveat=("Deliberately not summed into a 'wasted' total. CANCELLED is "
                    "often deliberate early stopping, not waste — deciding which "
                    "rows count is the analyst's call.")))


@app.get("/v1/queue/latency", response_model=m.Envelope, tags=["Layer B — proposed"])
def queue_latency(
    usd_per_engineer_hour: float = Query(DEFAULT_PRICE_BOOK.usd_per_engineer_hour,
                                         description="Override engineer hourly rate for monetization")
):
    s = store()
    q = s.queue()
    version = _price_version(DEFAULT_PRICE_BOOK.usd_per_gpu_hour, usd_per_engineer_hour)
    return m.Envelope(
        metric="queue_wait", window=_window(), unit="seconds", value=q["p50_sec"],
        rows=[q],
        monetized=m.Monetized(
            amount=round(q["total_wait_hours"] * usd_per_engineer_hour, 2),
            price_book_version=version),
        kind="fact",
        provenance=m.Provenance(
            signals=["slurm_time_submit", "slurm_time_start"], method="wait_percentiles@v1",
            caveat="Monetized at engineer-hour cost, not GPU cost — the tail is salary."))


@app.get("/v1/scaling/efficiency", response_model=m.Envelope, tags=["Layer B — proposed"])
def scaling_efficiency():
    return m.Envelope(
        metric="utilization_by_job_width", window=_window(), unit="percent",
        rows=store().scaling(), kind="judgment", confidence=0.55,
        provenance=m.Provenance(
            signals=["dcgm_sm_util", "slurm_gres"], method="utilization_decay_proxy@v1",
            caveat=("NOT strong scaling efficiency — there is no per-job throughput in "
                    "this data, so no T(1) baseline exists. This is utilization "
                    "conditioned on job width. The distribution is BIMODAL: read "
                    "share_under_5pct and share_over_80pct, not the median.")))


@app.get("/v1/resources/underperforming", response_model=m.Envelope,
         tags=["Layer B — proposed"])
def underperforming(
    entity_type: str = Query("user", pattern="^(user|node)$"),
    limit: int = 10,
    usd_per_gpu_hour: float = Query(DEFAULT_PRICE_BOOK.usd_per_gpu_hour,
                                    description="Override GPU hourly rate for monetization")
):
    """Ranked underperforming resources.

    A judgment endpoint. It aggregates findings per entity. It does not read
    `rootCauses`, so correlated findings sharing one cause are counted as
    independent problems. Validate against /v1/causal before acting.
    """
    s = store()
    if entity_type == "user":
        un = s.jobs[~s.jobs.is_success].groupby("id_user").gpu_hours.sum().nlargest(limit)
        rows = [{"entity_type": "user", "entity_id": f"u-{int(u)}",
                 "unsuccessful_gpu_hours": round(float(v), 1),
                 "monetized_usd": round(float(v) * usd_per_gpu_hour, 2)}
                for u, v in un.items()]
        conf = 0.72
    else:
        agg = s.findings_by_resource()
        nodes = [(rid_, d) for rid_, d in agg.items()
                 if s.type_of.get(rid_) == "k8s:node"]
        nodes.sort(key=lambda kv: -kv[1]["count"])
        rows = [{"entity_type": "node", "entity_id": s.name_of.get(rid_, rid_),
                 "resource_id": rid_, "finding_count": d["count"],
                 "impact_gpu_hours": round(d["impact_gpu_hours"], 1)}
                for rid_, d in nodes[:limit]]
        conf = 0.61
    return m.Envelope(
        metric=f"underperforming_{entity_type}", window=_window(), unit="rank",
        rows=rows, kind="judgment", confidence=conf,
        provenance=m.Provenance(
            signals=["findings", "dcgm_sm_util"],
            method=("unsuccessful_gpu_hours@v2" if entity_type == "user"
                    else "finding_count_per_resource@v1"),
            caveat=("Ranked by finding count. Correlated findings are not collapsed."
                    if entity_type == "node" else None)))


@app.get("/v1/recommendations", response_model=m.RecommendationsResponse,
         tags=["Layer B — proposed"])
def recommendations(
    usd_per_gpu_hour: float = Query(DEFAULT_PRICE_BOOK.usd_per_gpu_hour,
                                    description="Override GPU hourly rate for monetization")
):
    s = store()
    version = _price_version(usd_per_gpu_hour, DEFAULT_PRICE_BOOK.usd_per_engineer_hour)
    agg = s.findings_by_resource()
    low = [f for f in s.findings if f["detectorId"] == "rules::gpu-low-utilization"]
    low_gh = sum(f["metadata"]["impact_gpu_hours"] for f in low)
    nodes = sorted(((r, d) for r, d in agg.items() if s.type_of.get(r) == "k8s:node"),
                   key=lambda kv: -kv[1]["count"])[:5]
    node_fids = [f["id"] for f in s.findings
                 if any(r in f["resourceIds"] for r, _ in nodes)][:20]

    recs = [
        m.Recommendation(
            id="rec_lowutil", title="Move sub-10% utilization workloads to shared allocation",
            action=("Introduce a fractional-GPU queue and require a utilization "
                    "justification above 2 GPUs."),
            estimated_savings=_usd(low_gh * 0.35, usd_per_gpu_hour, version),
            estimated_savings_gpu_hours=round(low_gh * 0.35, 1),
            effort="medium", confidence=0.61,
            finding_ids=[f["id"] for f in low[:20]]),
        m.Recommendation(
            id="rec_drain_nodes", title="Drain the top 5 underperforming nodes",
            action=("These nodes carry the highest finding counts in the fleet. "
                    "Drain and submit for hardware inspection."),
            estimated_savings=_usd(sum(d["impact_gpu_hours"] for _, d in nodes),
                                   usd_per_gpu_hour, version),
            estimated_savings_gpu_hours=round(
                sum(d["impact_gpu_hours"] for _, d in nodes), 1),
            effort="low", confidence=0.58, finding_ids=node_fids),
    ]
    return m.RecommendationsResponse(recommendations=recs)
