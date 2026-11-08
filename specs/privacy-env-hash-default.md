---
id: privacy-env-hash-default
goal: capture() records the five free-form flag variables as a hash and length by default, and records their values only when called with include_flag_values=True.
acceptance:
  - uv run --extra dev pytest tests/test_capture_privacy.py tests/test_ab_cli.py -q
scope:
  - src/benchsane/capture.py
  - tests/test_capture_privacy.py
non_goals:
  - do not add a CLI flag; `--include-flag-values` is a separate follow-up spec
  - do not change the schema files, the allowlist membership, or other fields of the manifest
  - do not touch ab.py (it already calls capture() with defaults)
  - no new dependencies
  - do not weaken or delete any test; the only edit allowed to the test file is removing the xfail markers
risk_tier: 3
max_runs: 3
autonomy: inherit
status: ready
issue: 13
---

## Context
`src/benchsane/capture.py` `capture()` copies the value of every variable in `ENV_ALLOW` into `env.selected`.
Five of them hold free-form text that can carry usernames, paths or secrets (verified on 2026-11-08 with planted values:
`RUSTFLAGS="-L /Users/x/..."` and `JAVA_TOOL_OPTIONS="-Dpassword=..."` appeared verbatim in the manifest):
`RUSTFLAGS`, `CFLAGS`, `CXXFLAGS`, `LDFLAGS`, `JAVA_TOOL_OPTIONS`. The rest (thread counts, `GOGC`, `NODE_ENV`, ...) are
short numeric or enum values and stay verbatim.

Decision (Ryan, 2026-11-08): hash by default, explicit opt-in for values.

Do this:
1. Add a module constant `FREE_FORM_ENV = ("RUSTFLAGS", "CFLAGS", "CXXFLAGS", "LDFLAGS", "JAVA_TOOL_OPTIONS")`
   (every entry must also be in `ENV_ALLOW`).
2. Add a keyword argument `include_flag_values=False` to `capture()`. For a variable in `FREE_FORM_ENV` that is set, record
   `{"sha256_12": hashlib.sha256(value.encode()).hexdigest()[:12], "length": len(value)}` instead of the string, unless
   `include_flag_values` is true, in which case record the string as today.
3. Update the module docstring to say free-form flag variables are hashed unless opted in.

Run tests with `uv run --extra dev pytest ...`. Remove the five `xfail(strict=True)` markers in
`tests/test_capture_privacy.py` when the behaviour exists; they are strict, so the suite fails until you do.

Known and out of scope: `os.cmdline` (Linux `/proc/cmdline`) and the doctor `checks` details are not covered by this spec.

## Log
- 2026-11-08 draft
- 2026-11-08 ready, issue #13
