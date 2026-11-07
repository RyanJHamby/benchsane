---
name: benchsane
description: Use when benchmarking, profiling, or comparing the performance of programs or hardware, or when reviewing or quoting a performance number, so the measurement is sound and the claim is backed by captured evidence.
---

# Benchmark with benchsane

Use the `benchsane` CLI if it's on PATH. Otherwise use `uvx benchsane ...`, or the benchsane MCP tools if connected.

## Procedure

1. **State the question.** Decision, workload, baseline, and the smallest effect that matters. Copy `benchsane init`'s plan if the project has none.
2. **Get relevant guidance.** `benchsane kb search --tag <language> --tag <os>`, then `benchsane kb show <id>`. Cards marked unverified come from unsourced knowledge: check commands and thresholds before relying on them, especially when stakes are high.
3. **Check the host.** Run `benchsane doctor`. Tell the user about warnings. Never change system settings (governor, turbo, SMT, ASLR, swap) without being asked; suggest the commands and let the user run them.
4. **Pick the harness.** Whole programs: `benchsane ab`. In-process microbenchmarks: the language's harness (`kb search --tag tools --tag <language>`). Load tests: an open-loop generator.
5. **Measure the noise floor.** `benchsane ab -a '<cmd>' --aa --out bench/runs/<date>-aa`.
6. **Compare.** `benchsane ab -a '<base>' -b '<cand>' --out bench/runs/<date>-<name>`. Add `--env-pad` for effects under about 5%.
7. **Find the limiter.** Watch it during a run with vmstat, pidstat, perf or nvidia-smi. A number you can't explain isn't finished.
8. **Report.** Use the generated report: absolute values and ratio, CI, n, host, commit, warnings.

## Rules

- Never state a number that isn't in a captured run. Never estimate a performance figure and present it as measured.
- Name the host on every number. Don't transfer numbers between machines.
- Report "no detectable difference" as that, not as "no difference".
- Don't drop outliers, narrow the sweep, or rerun until favorable. If you rerun, say so and keep the earlier run.
- `ab` executes the given commands, so only pass commands the user wants run. Results may reveal internal hardware and workload details: don't publish them without asking, and use `--redact-commands` when command lines are sensitive.
- If the repo has its own results or journal convention, follow it and keep benchsane's output alongside it rather than bypassing it.
