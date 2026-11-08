---
id: mcp-compare-read-scope
goal: The MCP `compare` tool reads only files whose real path is inside the server's working directory or a directory listed in BENCHSANE_ALLOWED_DIRS; anything else is refused before any file is opened.
acceptance:
  - uv run --extra dev --extra mcp pytest tests/test_mcp_compare_scope.py tests/test_mcp.py -q
scope:
  - src/benchsane/mcp_server.py
  - tests/test_mcp_compare_scope.py
non_goals:
  - do not change the CLI (`benchsane compare`) or compare.py behaviour; the CLI is the user's own shell
  - do not change error-message formatting in compare.py in this spec
  - no new dependencies
  - do not weaken or delete any test; the only edit allowed to the test file is removing the xfail markers
risk_tier: 3
max_runs: 3
autonomy: inherit
---

## Context
`src/benchsane/mcp_server.py` registers a `compare(baseline_path, candidate_path, ...)` tool that hands
agent-supplied paths straight to `compare_mod.compare`, which opens them (and a sibling `env.json`). An agent can use it
to probe any file the server user can read: files that parse as number lists leak summary statistics, JSON files leak
key/command names through `LoadError` text, and a sibling `env.json` is embedded in the returned claim. The server is
documented as read-only and thin, so this is the one place it reads user-chosen paths.

Decision (Ryan, 2026-11-08): scope by directory, not by a single configured root.

Do this, inside the `compare` tool in `mcp_server.py` (not in compare.py):
1. Build the allowed roots: `os.path.realpath(os.getcwd())` plus each entry of `BENCHSANE_ALLOWED_DIRS`
   (split with `os.pathsep`, ignore empty entries, `realpath` each).
2. For both paths, take `os.path.realpath(path)` (resolves `..` and symlinks; relative paths resolve against the server's cwd).
   If it is not inside any allowed root, raise `ValueError` naming the path and "outside the allowed directories".
   Check with `os.path.commonpath`, not `str.startswith` (so `/work2` is not inside `/work`).
3. Do both checks before calling `compare_mod.compare`, so no file is opened for a refused call.
4. Mention the rule and the env var in the tool docstring.

Tests drive the real stdio server (`cwd` set per test), so they need the `mcp` extra: always run
`uv run --extra dev --extra mcp pytest ...`. The tests deliberately do not assert on error text, because SDK 2.x masks
tool errors as "Error executing tool compare" while 1.x may include the message. Remove the four
`xfail(strict=True)` markers in `tests/test_mcp_compare_scope.py` when the behaviour exists; they are strict, so the
suite fails until you do.

Known and out of scope (follow-up): the tool error text can still contain file-derived strings on SDK 1.x and in the
server's stderr log.

## Log
- 2026-11-08 draft
