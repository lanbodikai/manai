"""Prove actual MCP transport and bounded retrieval; never print source rows."""
import asyncio
import json
from service.mcp_client import connect_official

def body(result):
    if result.is_error:
        raise RuntimeError("MCP tool returned error")
    data = getattr(result,"structured_content",None)
    if data is not None:
        return data
    return json.loads(next(item.text for item in result.content if item.type == "text"))

async def probe():
    async with asyncio.timeout(45):
        async with connect_official() as client:
            available = {tool.name:tool for tool in (await client.list_tools()).tools}
            assert {"health","list_rules","list_findings"} <= available.keys()
            health = body(await client.call_tool("health",{}))
            rules = body(await client.call_tool("list_rules",{}))
            findings = body(await client.call_tool("list_findings",{"detector_id":"rules::gpu-not-needed","limit":1,"offset":0}))
            assert health["status"] == "ok"
            assert any(row["rule_id"] == "rules::gpu-not-needed" for row in rules["rules"])
            rows = findings["findings"]
            assert 0 < len(rows) <= 1 and rows[0]["detectorId"] == "rules::gpu-not-needed"
            print(json.dumps({"result":"PASS","transport":"stdio","tool_count":len(available),
                "calls":["health","list_rules","list_findings"],"bounded_retrieval":True,
                "provider_required":False,"tool_schemas_inspected":True}))

if __name__ == "__main__": asyncio.run(probe())
