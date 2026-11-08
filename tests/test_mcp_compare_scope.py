import asyncio
import os
import sys

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def call_compare(cwd, a, b, extra_env=None):
    """Runs the real stdio server with cwd as its working directory; returns (is_error, text).

    All inputs are valid number files, so today the only way a call can error is the new scope check.
    Don't assert on the error text: SDK 2.x masks tool errors as "Error executing tool compare".
    """
    env = {k: v for k, v in os.environ.items() if k != "BENCHSANE_ALLOWED_DIRS"}
    env.update(extra_env or {})

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


def write(path, values):
    path.write_text(" ".join(str(v) for v in values))
    return path


@pytest.fixture
def dirs(tmp_path):
    work, outside = tmp_path / "work", tmp_path / "outside"
    work.mkdir()
    outside.mkdir()
    return work, outside


GOOD = [1.0, 1.1, 0.9, 1.05, 0.95, 1.0]


@pytest.mark.xfail(strict=True, reason="spec mcp-compare-read-scope: remove this marker when implemented")
def test_absolute_path_outside_cwd_is_refused(dirs):
    work, outside = dirs
    ok = write(work / "a.txt", GOOD)
    secret = write(outside / "b.txt", GOOD)
    is_error, text = call_compare(work, ok, secret)
    assert is_error


@pytest.mark.xfail(strict=True, reason="spec mcp-compare-read-scope: remove this marker when implemented")
def test_dotdot_escape_is_refused(dirs):
    work, outside = dirs
    ok = write(work / "a.txt", GOOD)
    write(outside / "b.txt", GOOD)
    is_error, text = call_compare(work, ok, "../outside/b.txt")
    assert is_error


@pytest.mark.xfail(strict=True, reason="spec mcp-compare-read-scope: remove this marker when implemented")
def test_symlink_escape_is_refused(dirs):
    work, outside = dirs
    ok = write(work / "a.txt", GOOD)
    target = write(outside / "b.txt", GOOD)
    link = work / "link.txt"
    link.symlink_to(target)
    is_error, text = call_compare(work, ok, link)
    assert is_error


def test_paths_inside_cwd_still_work(dirs):
    work, _ = dirs
    a = write(work / "a.txt", GOOD)
    b = write(work / "b.txt", [x * 2 for x in GOOD])
    is_error, text = call_compare(work, a, b)
    assert not is_error and "verdict" in text


@pytest.mark.xfail(strict=True, reason="spec mcp-compare-read-scope: remove this marker when implemented")
def test_allowed_dirs_env_opens_an_extra_root(dirs):
    work, outside = dirs
    a = write(work / "a.txt", GOOD)
    b = write(outside / "b.txt", [x * 2 for x in GOOD])
    refused, _ = call_compare(work, a, b)  # the same call without the env var must be refused
    assert refused
    is_error, text = call_compare(work, a, b, {"BENCHSANE_ALLOWED_DIRS": str(outside)})
    assert not is_error and "verdict" in text
