---
id: mcp-compare-env-sibling-scope
goal: The MCP `compare` tool also refuses a call when the env.json next to either input resolves outside the allowed roots, so a symlinked env.json cannot read files outside them.
acceptance:
  - uv run --extra dev --extra mcp pytest tests/test_mcp_env_sibling_scope.py tests/test_mcp_compare_scope.py tests/test_mcp.py -q
scope:
  - src/benchsane/mcp_server.py
  - tests/test_mcp_env_sibling_scope.py
non_goals:
  - do not change compare.py, the CLI (`benchsane compare`) or any error-message formatting
  - do not change how the two named paths are checked; only add the sibling env.json check next to them
  - do not catch or race-proof the gap between the check and the open (a different, known follow-up)
  - no new dependencies
  - do not weaken or delete any test; the only edit allowed to the test file is removing the xfail marker
risk_tier: 3
max_runs: 3
autonomy: inherit
status: done
issue: 34
---

## Context
PR #30 made the MCP `compare` tool refuse any input whose real path is outside the server's working directory or
`BENCHSANE_ALLOWED_DIRS`. `compare_mod.compare` also reads a sibling file: `_sibling_env` in `src/benchsane/compare.py`
opens `os.path.join(os.path.dirname(os.path.abspath(path)), "env.json")`. `abspath` does not resolve symlinks and `open`
follows them, so if `env.json` inside an allowed directory is a symlink to a JSON file outside the roots, that file is read.
`diff_env` (capture.py) then echoes any value under eleven fixed keys (`os.cmdline`, `cpu.model`, `toolchains`, ...) into a
warning in the tool result. Reproduced on 2026-11-09: with `work/env.json -> outside/secret.json` and
`{"os": {"cmdline": "SECRET-outside-value"}}`, the scope check passed for both named paths and the result contained
`Environments differ: os.cmdline: 'SECRET-outside-value' vs 'other'`.

Decision (spec author, 2026-11-09, for the owner to confirm): a sibling env.json outside the roots refuses the whole call,
the same as an out-of-scope input, rather than being silently ignored. To use an env.json that lives elsewhere, add its
directory to `BENCHSANE_ALLOWED_DIRS`.

Do this, inside the `compare` tool in `mcp_server.py` (not in compare.py), right after the existing two checks and before
`compare_mod.compare` runs:
1. For each of the two input paths, build the sibling the way `compare.py` does:
   `os.path.join(os.path.dirname(os.path.abspath(path)), "env.json")`. Do not import the private `_sibling_env`.
2. If the sibling exists (use `os.path.lexists`, so a dangling or outside symlink is still checked), run the existing
   `_check_in_scope` on it with the same roots. A symlink resolves through `realpath` to its target, so an outside target is refused.
3. Add one sentence to the tool docstring: an env.json next to an input must also be inside the allowed directories.

Tests drive the real stdio server, so run `uv run --extra dev --extra mcp pytest ...`. The test asserts the secret string is
absent and the call errored; it does not assert on error text (SDK 2.x masks it). Remove the one `xfail(strict=True)` marker in
`tests/test_mcp_env_sibling_scope.py` when the behaviour exists; it is strict, so the suite fails until you do.
`test_env_json_inside_the_roots_is_still_compared` already passes and must keep passing: an in-scope env.json still feeds the
environment comparison.

Known and out of scope: the check and the later open are two steps, so a file swapped in between could still be read; the tool
error text can contain file-derived strings on SDK 1.x.

## Log
- 2026-11-09 draft
- 2026-11-09 ready, issue #34
- 2026-11-09 done, PR #36 (agent run 42696063299; guard and CI green; acceptance command 8 passed on merged main). Closes the sibling env.json gap found in review of PR #30.
