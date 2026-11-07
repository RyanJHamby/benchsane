# Tool picker

## tools.cli — Whole-program timing
tags: tools, all
status: unverified

`hyperfine`: CLI commands, warmups, prepare steps, JSON export. `perf stat -r N`: counters and repeated runs on Linux. `benchsane ab`: interleaved A/B with A/A and rusage. Avoid bash `time` in a loop for anything you'll quote.

## tools.harness — Per-language harnesses
tags: tools, c, cpp, rust, go, java, python, javascript, dotnet
status: unverified

C/C++: Google Benchmark, nanobench. Rust: criterion, divan. Go: `testing` + benchstat. JVM: JMH. Python: pyperf, pytest-benchmark, pytest-codspeed. JS: tinybench, mitata. .NET: BenchmarkDotNet. Always use these rather than writing your own loop.

## tools.profile — Finding why
tags: tools, profiling
status: unverified

Linux: perf + FlameGraph, bpftrace, Tracy/samply. JVM: async-profiler, JFR. Python: py-spy, scalene, memray. Go: pprof. GPU: Nsight, PyTorch profiler, DCGM. Causal: Coz. Tail-latency causes: off-CPU analysis. Apple: Instruments.

## tools.load — Load generators
tags: tools, latency, load, network, storage
status: unverified

HTTP: k6 (arrival-rate executor), wrk2, Gatling, Vegeta. Network: iperf3, netperf. Storage: fio. Memory: STREAM, Intel MLC, lmbench. Databases: sysbench, YCSB, pgbench. System-level: Phoronix Test Suite. Cloud comparisons: PerfKit Benchmarker.

## tools.ml — ML inference and training
tags: tools, ml, gpu, inference
status: unverified
source: https://blog.vllm.ai/guidellm/main https://inferencex.semianalysis.com/about

Inference: GuideLLM (vLLM project, sweep and constant-rate modes), NVIDIA AIPerf (formerly GenAI-Perf), Kubernetes Inference Perf, SemiAnalysis InferenceX (formerly InferenceMAX) for public comparisons. MLPerf Inference and Training for standardized submissions. Check each one's current state before adopting.

## tools.ci — Continuous benchmarking
tags: tools, ci
status: unverified
source: https://bencher.dev/docs/reference/prior-art/

Bencher (bare-metal runners, thresholds, self-hostable), CodSpeed (CPU simulation, walltime on macro runners, PR reports), github-action-benchmark (simple, free, shared-runner noise is your problem), Conbench, Apache Otava (change detection).

## tools.agent — Agent-facing performance tools
tags: tools, profiling, agent
status: cited
source: https://glama.ai/mcp/servers/link0-o/PerfLens/tree

PerfLens: Linux profile analysis via CLI, MCP and Skill; normalizes pyperf, Google Benchmark and hyperfine JSON, and keeps evidence and hypotheses apart. It isn't a benchmark runner and has a large surface (38 MCP tools scored by Glama), and v0.4.0 was described as a candidate. CodSpeed offers a hosted MCP server and Skills over its own data. Mcpbr and MCP-Bench benchmark agents and MCP servers, not programs: not the same problem.
