# MGAI facsimile API

Same app runs locally and on AWS Lambda. `api/main.py` is a plain FastAPI app;
`api/handler.py` wraps it with Mangum for Lambda. No code differs between them.

## Local

```bash
docker compose up                      # -> http://localhost:8000/docs
# or, without docker:
.venv/bin/uvicorn api.main:app --reload
```

## Layers

**Layer A** (`/v1/detect`, `/v1/events/findings`, `/v1/neighbor`, `/v1/causal`,
`/v1/policies/rules`) matches MantisGrid's production API
(`mantisgrid/oracle/api_types.py`), with these known deviations — checked against
the product on 2026-09-10:

| Where | Product | This facsimile |
|---|---|---|
| `RuleTemplate` | `help_link`, a required `params`, `remediations`, `metric_selector` | omits all four; **adds** `status` (`ACTIVE` / `CLEAR`) and `findings` so a rule that never fired is visible |
| Edge types | `RUNS_ON` and `CALLS`. Kubernetes ownership is stored as `CALLS`, a go-gorm workaround | `RUNS_ON`, plus `OWNS` (array → task pod) and `CONTAINS` (user namespace → pod), named for what they mean; `MOUNTS` is synthetic |
| `/v1/causal` | time-series causal discovery over metrics, constrained by the resource graph | computed from each finding's recorded evidence for arrays and bursts; the synthetic volume incident returns a fixed chain. `algorithm_agreement` is `null` on computed answers |
| Resource types | ingests `k8s:job` and `k8s:namespace` among many others | uses them for Slurm arrays and users respectively |

Anything not in that table should match the product. If you find something that
does not, it is a bug in the facsimile.

**Layer B** (`/v1/price-book`, `/v1/efficiency/summary`, `/v1/waste/breakdown`,
`/v1/queue/latency`, `/v1/scaling/efficiency`, `/v1/resources/underperforming`,
`/v1/recommendations`) is proposed and does not exist in the product.

Every Layer B response carries `kind`: `fact` | `judgment` | `simulated`. (No
endpoint currently returns `simulated`; the value is reserved.)

## Pricing

Layer B endpoints that return monetized figures accept optional query parameters
to override the default price book:

- `usd_per_gpu_hour` (default: 2.50) — used by `/v1/efficiency/summary`,
  `/v1/resources/underperforming?entity_type=user`, `/v1/recommendations`
- `usd_per_engineer_hour` (default: 95.00) — used by `/v1/queue/latency`

```bash
# Default pricing
curl http://localhost:8000/v1/efficiency/summary

# Custom GPU rate
curl http://localhost:8000/v1/efficiency/summary?usd_per_gpu_hour=3.50
```

When custom pricing is used, `monetized.price_book_version` returns
`2026-Q3+custom` instead of `2026-Q3` so dashboards can distinguish price
changes from infrastructure changes.

`GET /v1/price-book` returns the default values for reference.

## Rate limiting

**Off by default.** Participants run this API on their own machine, where a limit
only stops them re-running their own notebook. Set `MGAI_RATE_LIMIT` (for example
`60/minute`) to enable one; it is applied per IP *per endpoint*, and an exceeded
limit returns HTTP 429 with no `Retry-After` header.
