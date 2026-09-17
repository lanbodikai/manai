"""Read-only local MCP connection. No provider or model credentials required."""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@asynccontextmanager
async def connect_official():
    # Deliberately exclude model credentials from this data-tool subprocess.
    allowed = {key: value for key, value in os.environ.items()
               if key in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME"}}
    allowed["PYTHONUNBUFFERED"] = "1"
    params = StdioServerParameters(command=sys.executable,
        args=["-m", "mcp_layer.server"], cwd=str(Path(__file__).resolve().parent.parent), env=allowed)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
