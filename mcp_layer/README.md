# MCP layer for the MGAI API

An MCP ([Model Context Protocol](https://modelcontextprotocol.io)) server on top
of the Track 2 API, so an LLM agent can call the cluster-efficiency endpoints as
tools instead of you hand-writing HTTP calls.

Built with [FastMCP](https://gofastmcp.com). It imports the FastAPI app
**in-process** — same in-memory `store()`, no extra HTTP hop, no second port. The
data loads once, on the first tool call (a few seconds), and stays in memory.

> **Directory is `mcp_layer/`, not `mcp/`, on purpose.** FastMCP depends on the
> `mcp` PyPI SDK. A local package named `mcp` shadows it and breaks imports
> (`ModuleNotFoundError: No module named 'mcp.server...'`) because the repo root
> is on `sys.path`. Keep the name.

## The server

[`server.py`](server.py) exposes **curated, hand-written tools** with LLM-facing
docstrings that teach the `fact` / `judgment` / `simulated` distinction and when to
validate a judgment against `causal`. An agent reasons better with these
descriptions than with raw endpoint docs.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** in your PATH. `uv` resolves and caches the
  dependencies at launch, so the agent client can start the server with one
  command — no virtualenv to create or activate. On macOS: `brew install uv`.
- **The data prepped.** The server reads `data/prepped/` and `data/synthetic/`,
  exactly like the API, on its first tool call. From the track-2 root:

  ```bash
  make prep        # raw CSVs -> data/prepped/   (see ../data/README.md to download)
  make generate    # data/prepped/ -> data/synthetic/
  ```

## Run

From the **track-2 root** (so `api` and `mcp_layer` are importable):

```bash
make mcp
```

which runs, over stdio (the default transport local agent clients launch):

```bash
uv run --with-requirements requirements.lock.txt --with fastmcp python -m mcp_layer.server
```

`--with-requirements requirements.lock.txt` supplies the API's own dependencies at the
same pinned versions the Docker image uses, and `--with fastmcp` adds FastMCP, all in an
ephemeral, cached environment. Nothing is installed into your system Python.

For a remote / networked client, run HTTP transport instead:

```bash
uv run --with-requirements requirements.lock.txt --with fastmcp \
  fastmcp run mcp_layer/server.py:mcp --transport http --port 9000
```

> Not `uvx`: that runs a *published* package in isolation. This server is local
> code that imports the sibling `api/` package and reads the local data tree, so
> it must run in place from the track-2 root with `uv run`.

## Connect an agent client

Most desktop agent clients launch an MCP server over stdio from a JSON config.
Point it at `uv`, running from the track-2 root:

```json
{
  "mcpServers": {
    "mgai": {
      "command": "uv",
      "args": [
        "run", "--with-requirements", "requirements.lock.txt", "--with", "fastmcp",
        "python", "-m", "mcp_layer.server"
      ],
      "cwd": "/absolute/path/to/track-2"
    }
  }
}
```

The client owns the process — it starts and stops the server for you; you do not
run `make mcp` yourself when using a client this way. `uv` provisions the deps on
first launch.

## Tools (curated server)

**Layer A — the real API (facts you can trust):**

- `health` — store status; call first if other tools error.
- `list_findings` — raw detector findings; filter by detector/category/severity/resource.
- `causal` — **authoritative** root-cause for a finding; use it to *validate* Layer B judgments.
- `neighbor` — structural resource graph within N hops.
- `detect` — per-detector finding counts.
- `list_rules` — full rule catalogue, including rules that evaluated `CLEAR`.

**Layer B — proposed business layer (check `kind`):**

- `price_book` — default USD rates (reference).
- `efficiency_summary` — capacity waterfall, `fact`.
- `waste_breakdown` — GPU-hours by outcome, `fact`.
- `queue_latency` — wait percentiles priced as engineer time, `fact`.
- `scaling_efficiency` — utilization by job width, `judgment` (bimodal — read the shares, not the median).
- `underperforming` — ranked users/nodes, `judgment` (does **not** collapse correlated findings — validate with `causal`).
- `recommendations` — cost cuts with estimated savings, `judgment` (pull the cited `finding_ids` and check `causal`).

Monetizing tools accept `usd_per_gpu_hour` / `usd_per_engineer_hour` to model
different pricing; responses are then tagged `2026-Q3+custom`.

## How the agent should read `kind`

Every Layer B response carries a `kind`:

- **`fact`** — deterministic, recomputable from raw data. Trust it.
- **`judgment`** — a model said so. Check `confidence`, and validate against the
  underlying `findings` / `causal` before acting.
- **`simulated`** — synthetic, no real signal underneath.

`causal` is the one to lean on: it resolves a correlated cluster of findings to
the single resource underneath. `underperforming` and `recommendations` do *not*
read `rootCauses`, so they can double-count one cause as many problems — always
cross-check a blamed node or user against `causal`.

Note: the data is a four-month job **sample**, not the whole cluster. Do not
extrapolate to fleet-wide utilization.
