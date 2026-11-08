---
id: ab-platform-guard
goal: run_ab raises one clear RuntimeError before spawning anything when os.wait4 is unavailable (Windows), and the dead pre-3.9 exit-status fallback is removed.
acceptance:
  - uv run --extra dev pytest tests/test_ab_platform_guard.py tests/test_ab_cli.py -q
scope:
  - src/benchsane/ab.py
  - tests/test_ab_platform_guard.py
non_goals:
  - no Windows support; fail fast only
  - no changes to how metrics are measured, no other files in src/
  - no new dependencies
  - do not weaken or delete any test; the only edit allowed to the test file is removing the xfail marker
risk_tier: 2
max_runs: 3
autonomy: inherit
status: ready
issue: 10
---

## Context
`src/benchsane/ab.py` `_run_once` calls `os.wait4`, which does not exist on Windows. Today that surfaces as an
`AttributeError` after warmup has already spawned processes. `run_ab` already guards `--cpus` the same way
(`hasattr(os, "sched_setaffinity")` then `RuntimeError("--cpus isn't supported on this platform")`); copy that style.

Do this:
1. At the top of `run_ab`, before any capture or spawn, raise
   `RuntimeError("benchsane ab is not supported on this platform (needs os.wait4)")` if `not hasattr(os, "wait4")`.
2. In `_run_once`, replace the `hasattr(os, "waitstatus_to_exitcode")` fallback with a direct call. The package floor is
   Python 3.10 (`requires-python` in pyproject.toml), so the fallback is dead code.
3. In `tests/test_ab_platform_guard.py`, remove the `@pytest.mark.xfail(strict=True, ...)` marker on
   `test_run_ab_fails_fast_without_wait4`. It is strict, so it fails the suite once the guard exists until removed.

Always run tests as `uv run --extra dev pytest ...`: plain `uv run pytest` does not install the dev extra.

## Log
- 2026-11-08 draft
- 2026-11-08 ready, issue #10
