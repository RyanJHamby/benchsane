# Workloads

## micro.scope — What a microbenchmark can claim
tags: microbenchmark, reporting
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

A microbenchmark shows a component's cost in isolation. It can't support a claim about system performance. Check the fraction of time this path takes in a real profile (Amdahl) before quoting a win, and back the claim with a macrobenchmark. Pay attention to inputs: a sorted, repeated or tiny input is usually a different program.

## micro.dce — Dead-code elimination and constant folding
tags: microbenchmark, c, cpp, rust, go, java, javascript
status: unverified
source: https://gernot-heiser.org/benchmarking-crimes.html

If the compiler can prove a result unused or known at compile time, your benchmark measures nothing. Symptoms are near-zero time, no scaling with N. Use the harness's sink (`DoNotOptimize`, `black_box`, `Blackhole`, `b.Loop`), feed inputs at runtime, and inspect the machine code. Measure an empty loop to subtract harness overhead.

## latency.coordinated-omission — Coordinated omission
tags: latency, load, network
status: cited
source: https://github.com/giltene/wrk2

Closed-loop generators wait for each response before issuing the next request, so they stop sending during a stall and undersample exactly the bad period. Measure from when a request was *supposed* to be sent. Use a constant arrival rate: wrk2 `-R`, k6 `constant-arrival-rate`, Gatling open injection. A caveat: at least one wrk fork argues wrk2 corrects latency but still doesn't truly send on schedule, so the server sees less queueing than a real open system. The SIGPLAN checklist asks for an open-loop generator for this reason.

## latency.workload-model — Open, closed, or partly open
tags: latency, load
status: cited
source: https://artillery.io/blog/load-testing-workload-models https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations.md

Open: arrivals ignore the system's state (public traffic). Closed: fixed users or connections, each waits (internal client pools, connection-limited systems). Fixed-connection tools report different numbers from arrival-rate ones for the same server. Choose the model your production traffic resembles, and state it. k6 reports `dropped_iterations` when an open test can't start load, which must not be ignored.

## latency.percentiles — Report the distribution at a stated load
tags: latency, load, statistics
status: unverified

Never average latency; show p50, p90, p99, p99.9, max at a given offered load, and sweep load until the knee. A latency number without its load is meaningless, and throughput without a latency SLO is a saturation number. Use HdrHistogram, not linear buckets that truncate the tail. Exclude warmup, and report errors and timeouts.

## latency.generator — The load generator is part of the system
tags: latency, load, network
status: unverified
source: https://github.com/giltene/wrk2

Keep the generator on separate cores or hosts, and monitor its CPU. If achieved rate falls below target, or generator CPU saturates, the results describe the generator. Run on an unloaded generator and check it against a trivially fast server to measure its own limit. Sync clocks if you measure across machines, or measure one-way only with care.

## database.traps — Databases and storage engines
tags: database, storage
status: unverified

State durability (fsync per commit, replication), isolation level, dataset vs memory size, index set and cache warmth. Compare at equal durability. A fresh database is unfragmented, so run long enough for compaction, vacuum and checkpoint cycles to appear. Use a key distribution such as zipfian if real access is skewed. TPC results have licensing and disclosure rules, so say "derived from TPC-C" rather than claiming a TPC result. Vendor licenses may restrict publishing benchmarks.

## distributed.traps — Distributed systems
tags: distributed, network, scaling
status: unverified

Test real network placement and a realistic replica count. Measure during failures, leader changes and rebalancing, not just steady state. Coordinate start and end across clients, use synchronized clocks or client-side timing only, and account for the client fleet's limits. The slowest fan-out leg dominates, so per-node tails compound.

## distributed.training — Distributed GPU training
tags: distributed, gpu, ml, training
status: unverified

Use time-to-accuracy or time-per-epoch at fixed model quality: throughput alone rewards settings that harm convergence. Exclude start-up and checkpoints or report them separately. Break step time into data, forward, backward, communication and optimizer. Identify stragglers per rank. Record batch size per GPU, precision, interconnect, collective library and topology. Also report single-GPU baseline when reporting scaling.

## ml.inference — LLM and model serving
tags: ml, inference, gpu, latency
status: unverified
source: https://lucaberton.com/blog/nvidia-aiperf-llm-inference-benchmarking-guide/

Separate TTFT (dominated by prompt processing), inter-token latency, output throughput and requests per second. Sweep concurrency or arrival rate, and report percentiles and goodput under an SLO. Fix prompt and output lengths (and `ignore_eos` if synthetic), model, quantization and precision, batching policy and KV-cache settings. TTFT without stated prompt length is meaningless, and synthetic random prompts defeat prefix caches, which real traffic may benefit from. Use GuideLLM, AIPerf, or Inference Perf rather than a stopwatch.

## ml.realtime-audio — Streaming audio and voice
tags: ml, inference, audio, latency
status: unverified

Measure time-to-first-audio, real-time factor (seconds of processing per second of audio), per-chunk latency jitter and underruns, and end-to-end turn latency from end of user speech. Use an open-loop stream: audio arrives at wall-clock rate whether or not the server keeps up, so never measure faster than real time and call it streaming latency. Report sample rate, chunk size and codec, concurrent streams per GPU, and quality alongside speed.

## ml.training — Training throughput
tags: ml, gpu, training
status: unverified

Skip early iterations and report them separately, as compile, cache fill and data loader startup distort them. Use real data pipelines, since synthetic data hides input bottlenecks. Note that `torch.backends.cudnn.benchmark` and non-deterministic ops add variance. Fix seeds where possible, and report accuracy alongside speed.

## startup.cold — Startup and cold paths
tags: startup, all
status: unverified

Cold start, warm start and steady state are different quantities. Report each if relevant. For CLIs, runtime is often dominated by process startup, dynamic linking and imports, and hyperfine handles this well. Below a few milliseconds, the spawn overhead dominates, so run the inner loop instead.

## io.output — Benchmark output is part of the benchmark
tags: all, microbenchmark
status: unverified

Writing to a terminal is slow and variable. Redirect stdout to `/dev/null` or a file on tmpfs (`benchsane ab` discards it by default), and verify separately that the output is correct. Logging levels should match production and be recorded.
