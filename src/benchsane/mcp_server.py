"""Thin, read-only MCP server over stdio. It can't run commands or change the system."""
from __future__ import annotations

import os
import sys

from . import capture as capture_mod
from . import compare as compare_mod
from . import doctor as doctor_mod
from . import kb as kb_mod


def _allowed_roots() -> list[str]:
    roots = [os.path.realpath(os.getcwd())]
    roots += [os.path.realpath(d) for d in os.environ.get("BENCHSANE_ALLOWED_DIRS", "").split(os.pathsep) if d]
    return roots


def _check_in_scope(path: str, roots: list[str]) -> None:
    real = os.path.realpath(path)
    for root in roots:
        try:
            if os.path.commonpath([real, root]) == root:
                return
        except ValueError:  # different drives
            continue
    raise ValueError(f"{path!r} is outside the allowed directories")


def build():
    try:  # SDK 2.x
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:  # SDK 1.x
        from mcp.server.fastmcp import FastMCP as Server

    server = Server("benchsane")

    @server.tool()
    def kb_search(query: str = "", tags: list[str] | None = None, limit: int = 10) -> list[dict]:
        """Search benchmarking guidance. Filter with tags such as linux, rust, gpu, latency, cloud. Returns id, title, status and a snippet."""
        return [{"id": c.id, "title": c.title, "tags": c.tags, "status": c.status, "snippet": c.body[:200]}
                for c in kb_mod.search(query, tags, limit=limit)]

    @server.tool()
    def kb_get(card_id: str) -> dict:
        """Get one knowledge card by id. 'status: unverified' means it has no fetched source yet; check before relying on it."""
        card = kb_mod.load_all().get(card_id)
        if card is None:
            raise ValueError(f"unknown card {card_id!r}; use kb_search")
        return card.to_dict()

    @server.tool()
    def doctor() -> dict:
        """Read-only preflight of the machine this server runs on: grade plus findings linked to cards. Changes nothing."""
        checks = doctor_mod.run_checks()
        return doctor_mod.report(checks)

    @server.tool()
    def capture_env() -> dict:
        """Environment manifest for this machine. Omits hostname, username, git remotes and non-allowlisted environment values."""
        return capture_mod.capture()

    @server.tool()
    def compare(baseline_path: str, candidate_path: str, select_baseline: str | None = None,
                select_candidate: str | None = None, min_effect: float = 0.01) -> dict:
        """Compare two result files (hyperfine, Google Benchmark, pyperf, benchsane or plain numbers). Lower is assumed better.
        Only files inside the server's working directory or a directory listed in BENCHSANE_ALLOWED_DIRS
        (os.pathsep-separated) are read; other paths are refused."""
        roots = _allowed_roots()
        _check_in_scope(baseline_path, roots)
        _check_in_scope(candidate_path, roots)
        return compare_mod.compare(baseline_path, candidate_path, select_baseline, select_candidate, min_effect)

    return server


def main():
    try:
        server = build()
    except ImportError:
        print("benchsane-mcp needs the 'mcp' extra (Python 3.10+): pip install 'benchsane[mcp]'", file=sys.stderr)
        return 1
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
