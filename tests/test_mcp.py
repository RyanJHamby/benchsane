import asyncio
import json
import sys

import pytest

pytest.importorskip("mcp")


def test_stdio_roundtrip():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        params = StdioServerParameters(command=sys.executable, args=["-m", "benchsane.mcp_server"])
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                assert names == {"kb_search", "kb_get", "doctor", "capture_env", "compare"}
                found = await s.call_tool("kb_search", {"query": "coordinated omission"})
                assert "latency.coordinated-omission" in found.content[0].text
                doc = await s.call_tool("doctor", {})
                assert "grade" in doc.content[0].text

    asyncio.run(go())
