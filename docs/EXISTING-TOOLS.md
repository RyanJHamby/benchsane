# Does this exist already?

Searched on 2026-11-03. **Nothing found covers the whole request, but most of the pieces exist, and those should be adopted rather than rebuilt.** A search can't prove absence, so this is what turned up rather than an exhaustive survey.

## Build only the gap

The gap is the combination of a cross-stack knowledge base, host checks tied to that knowledge, and one small sound-comparison tool, all fetchable by people and agents in one pinned package.

| Need | Use this | Why not build it | What it doesn't do |
|---|---|---|---|
| Methodology | [Heiser's crimes](https://gernot-heiser.org/benchmarking-crimes.html), [Gregg's checklist](https://brendangregg.com/blog/2018-06-30/benchmarking-checklist.html), [SIGPLAN checklist](https://raw.githubusercontent.com/SIGPLAN/empirical-evaluation/master/checklist/checklist.pdf), [Kalibera & Jones](https://kar.kent.ac.uk/33611/) | Authoritative; cite them, don't compete | Human reading; no tooling or per-stack detail |
| CPU tuning | [`pyperf system tune`](https://pyperf.readthedocs.io/en/stable/user_guide.html) | Mature, reversible with `reset` | Changes the system, which is why benchsane's doctor only reads |
| Microbenchmarks | Google Benchmark, criterion, divan, JMH, `go test` + benchstat, pyperf, BenchmarkDotNet | Each handles language traps a generic tool can't | Single language |
| Whole programs | hyperfine, `perf stat -r` | Better UX than `ab` for one-off timing | Runs commands in batches, not interleaved |
| Regression tracking in CI | [Bencher](https://github.com/bencherdev/bencher), [CodSpeed](https://docs.codspeed.io), github-action-benchmark, [Apache Otava](https://bencher.dev/docs/reference/prior-art/) | A hosted time-series and threshold system is its own product | Not a methodology guide |
| Cross-cloud and suite runs | [PerfKit Benchmarker](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker), [Phoronix Test Suite](https://github.com/kotarou3/phoronix-test-suite) | Huge catalogs | Answers "which machine", not "is my change real" |
| Load | k6 arrival-rate, [wrk2](https://www.github.com/idio/wrk2), fio, iperf3 | Specialized | Single domain |
| LLM inference | [GuideLLM](https://blog.vllm.ai/guidellm/main), [AIPerf](https://lucaberton.com/blog/nvidia-aiperf-llm-inference-benchmarking-guide/), MLPerf, InferenceMAX | Metrics and traffic models are hard | Single domain |
| Agent profile analysis | [PerfLens](https://glama.ai/mcp/servers/link0-o/PerfLens/tree) (Apache-2.0) | Serious evidence pipeline for perf data | Linux only, no general runner, 38 MCP tools, v0.4.0 described as an unpublished candidate |

## Closest matches to the actual idea

- **[PerfLens](https://glama.ai/mcp/servers/link0-o/PerfLens/tree)**: closest in spirit (CLI, MCP and Skill, evidence first). It analyzes profiles after the fact, while benchsane covers methodology before and during the run. They're complementary: use PerfLens when you need to work out *why*. Its rigorous design is worth learning from, but its privileged collector and large tool surface are more than a work laptop needs.
- **[cursor/plugins benchmark-checklist](https://tessl.io/registry/skills/github/cursor/plugins/benchmark-checklist)**: one good SKILL.md following Gregg's seven questions, with alternating runs and a rank-sum test. No per-stack knowledge or tooling. The license wasn't shown on the page I read.
- **[begriffs ai-review critic](https://dev.begriffs.com/ai-review/blob/HEAD:/critic/benchmarking.md)**: about 440 lines instructing an AI to review benchmarks in Gregg's voice. Broad, but high-level, and it's a persona rather than a tool.
- **[CodSpeed's MCP and Skills](https://docsearch.algolia.com/mcp/docs/website/docs.codspeed.io)**: excellent if you adopt CodSpeed, but tied to its data and service.
- **mcpbr, MCP-Bench, SkillsBench**: name collisions. They benchmark agents and skills, not programs.

## Recommendation

1. Build benchsane small, and keep it a thin layer that points at the tools above.
2. In CI, use Bencher or CodSpeed if a project needs history. benchsane's `compare --fail-on-regression` is only for simple gating.
3. Don't build a runner catalog, dashboard, profiler or tuner.

## Not reviewed

ReBench, benchkit (open-s4c), Krun, and conbench came up or were recalled but weren't evaluated. Look at ReBench and benchkit if `ab` grows toward multi-configuration experiments: adopting one is better than extending `ab`.
