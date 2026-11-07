# Roadmap

v0.1 is early. Here is what it doesn't do yet, with the riskiest gaps first. Contributions are welcome.

## Cards we want

- **Benchmark as a test.** Rot detection, keeping benchmarks in CI, a budget for their runtime.
- **Injecting a known slowdown** as a standard calibration step (a `benchsane calibrate`?).
- **Sample-size planning.** Estimate the runs needed from the A/A noise floor and the target effect. Probably the most useful next feature.
- **Regression triage.** Bisecting performance, handling noisy bisects, separating a code change from a toolchain change.
- **Tail-latency diagnosis.** Off-CPU, scheduler latency, GC logs, page faults.
- **Concurrency.** Lock contention, false sharing, thread oversubscription, coordinating multi-thread starts.
- **More workloads.** Browser and frontend, mobile (device thermal limits, release builds, real devices), WebAssembly, serverless cold starts, Kubernetes, embedded, and SIMD-specific work.
- **More languages and runtimes.** Swift and Kotlin for mobile, Ruby, PHP, Zig, and PyPy.
- **More accelerators.** AMD ROCm, Apple MPS, TPU, and multi-GPU interconnects.
- **Cost as a metric.** Dollars per unit of work, with dated pricing.
- **Fair comparison with competitors,** including publishing limits.
- **Security and privacy of results.** What a benchmark result reveals about internal hardware and workloads.

## Known gaps in v0.1

| Gap | Risk | Next step |
|---|---|---|
| **Only tested on one Linux VM** | macOS, bare-metal, GPU and multi-NUMA code paths have never run for real | Run on macOS, bare-metal Linux and a GPU host. Fix what breaks |
| `nvidia-smi` parsing | Untested on a real GPU | Test on a GPU instance |
| Windows | `ab` uses `os.wait4`, so it won't work there. `doctor` is minimal | Decide whether Windows matters at all |
| `ab` measures only wall time plus rusage | No perf counters | Add optional `perf stat` capture |
| Bootstrap at low n | Percentile bootstrap intervals can be narrow on small samples | The false-positive test uses simulated normal data only. Check it on real A/A runs |
| No multi-comparison correction | A suite of many benchmarks will show false hits | Add when `compare` handles suites |
| Unverified cards | Some could be wrong | Upgrade as you use them, and date the checks |
| Card staleness | Versions and tool state go out of date | Add a `verified:` date, and a scheduled link check |
| No evaluation of the Skill | It isn't known to improve what agents do | Try a real task with and without it |

## Out of scope on purpose

- **Auto-tuning.** Print commands, don't run them. On work machines this matters.
- **An `ab` MCP tool.** It would hand agents remote command execution through a second channel, when they already have a shell with its own permissions.
- **Dashboards and history.** Bencher and CodSpeed do it.
- **A benchmark suite.** Your workload is the benchmark. Phoronix and PKB exist for the rest.
