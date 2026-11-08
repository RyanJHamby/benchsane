---
id: ab-restore-affinity
goal: run_ab(cpus=...) restores the process's original CPU affinity when it finishes, whether the runs succeed or raise.
acceptance:
  - uv run --extra dev pytest tests/test_ab_affinity.py tests/test_ab_cli.py -q
scope:
  - src/benchsane/ab.py
  - tests/test_ab_affinity.py
non_goals:
  - no change to how --cpus is parsed or validated, and no other files in src/
  - no new dependencies
  - do not weaken or delete any test; the only edit allowed to the test file is removing the two xfail markers
risk_tier: 2
max_runs: 3
autonomy: inherit
---

## Context
`src/benchsane/ab.py` `run_ab` calls `os.sched_setaffinity(0, cpus)` when `cpus` is given and never undoes it. A library
caller (or the MCP server, which is long-lived) is left pinned to those CPUs after `run_ab` returns or raises.

Do this: when `cpus` is set, record `os.sched_getaffinity(0)` before applying, and restore it in a `finally` that wraps
everything after the apply (warmup, measured runs, result writing). Keep the existing
`RuntimeError("--cpus isn't supported on this platform")` guard for platforms without `sched_setaffinity`; check it before
reading the original affinity.

The test fakes `os.sched_getaffinity`/`os.sched_setaffinity` (macOS has neither), so it runs on every OS. Remove the two
`xfail(strict=True)` markers in `tests/test_ab_affinity.py` once the behaviour exists; they are strict, so the suite fails
until you do.

Always run tests as `uv run --extra dev pytest ...`.

## Log
- 2026-11-08 draft
