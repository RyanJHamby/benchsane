"""The MCP compare tool also reads an env.json next to each input; that file must be inside the allowed roots too."""
import asyncio
import json
import os
import sys

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

SECRET = "SECRET-outside-value"
NUMBERS = "1.0 1.1 0.9 1.05 0.95 1.0"


def call_compare(cwd, a, b):
    """Runs the real stdio server with cwd as its working directory; returns (is_error, text).

    Don't assert on error text: SDK 2.x masks tool errors as "Error executing tool compare".
    """
    env = {k: v for k, v in os.environ.items() if k != "BENCHSANE_ALLOWED_DIRS"}

    async def go():
        params = StdioServerParameters(command=sys.executable, args=["-m", "benchsane.mcp_server"], cwd=str(cwd), env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                res = await s.call_tool("compare", {"baseline_path": str(a), "candidate_path": str(b)})
                err = getattr(res, "is_error", None)
                err = getattr(res, "isError", False) if err is None else err  # SDK 1.x spells it isError
                return err, res.content[0].text

    return asyncio.run(go())


@pytest.fixture
def layout(tmp_path):
    work, sub, outside = tmp_path / "work", tmp_path / "work" / "sub", tmp_path / "outside"
    for d in (work, sub, outside):
        d.mkdir()
    (work / "a.txt").write_text(NUMBERS)
    (sub / "b.txt").write_text(NUMBERS)
    return work, sub, outside


@pytest.mark.xfail(strict=True, reason="spec mcp-compare-env-sibling-scope: remove this marker when implemented")
def test_env_json_symlinked_outside_the_roots_is_refused(layout):
    work, sub, outside = layout
    (outside / "secret.json").write_text(json.dumps({"os": {"cmdline": SECRET}}))
    os.symlink(outside / "secret.json", work / "env.json")
    (sub / "env.json").write_text(json.dumps({"os": {"cmdline": "other"}}))
    is_error, text = call_compare(work, work / "a.txt", sub / "b.txt")
    assert SECRET not in text
    assert is_error


def test_env_json_inside_the_roots_is_still_compared(layout):
    work, sub, _ = layout
    (work / "env.json").write_text(json.dumps({"os": {"cmdline": "one"}}))
    (sub / "env.json").write_text(json.dumps({"os": {"cmdline": "two"}}))
    is_error, text = call_compare(work, work / "a.txt", sub / "b.txt")
    assert not is_error
    assert "os.cmdline" in text, "an in-scope env.json must still feed the environment comparison"
