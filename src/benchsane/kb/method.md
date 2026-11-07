# Method

## method.question — Write the question before the benchmark
tags: method, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

State what decision the number will drive, the workload it stands for, and the effect size that would change that decision. Without this, you cannot tell a good result from a bad one, and selective benchmarking creeps in. Also test where the change should not help: a fair evaluation shows the gain and looks for the degradation.

## method.active — Benchmark actively, not fire-and-forget
tags: method, all
status: cited
source: https://www.brendangregg.com/activebenchmarking.html

While it runs, watch it with other tools (vmstat, iostat, pidstat, perf, nvidia-smi) and name the true limiter. Passive runs produce data that may measure the wrong thing: neighbors, resource controls, a single-threaded client, the network, or disk rather than file-system I/O. If you can't say what limited the result, you don't have a result yet.

## method.aa — Run an A/A test first
tags: method, statistics, all
status: unverified

Compare the baseline against itself using the identical procedure. The apparent difference is your noise floor, and any effect smaller than it isn't evidence. A "significant" A/A means your procedure is broken (drift, ordering, pseudo-replication). `benchsane ab --aa` does this.

## method.interleave — Interleave and randomize run order
tags: method, statistics, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Running all of A and then all of B confounds the change with time: thermal state, page cache, background jobs, neighbors. Heiser advises varying measurement order and repeating points after other points. Randomized blocks (A B, B A, B A ...) are a stricter form of the same idea. `benchsane ab` interleaves by default; hyperfine's multi-command mode runs each command's batch in turn.

## method.bias — Low noise does not mean correct
tags: method, layout, bias, c, cpp, rust, all
status: cited
source: https://users.cs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf https://rocm.docs.amd.com/projects/llvm-project/en/docs-7.14.1/LLVM/llvm/html/Benchmarking.html

Measurement bias is separate from noise. Mytkowicz et al. showed that environment size and link order can flip a conclusion, and LLVM's benchmarking notes say low noise is "required, but not sufficient". A tiny, tight CI can be tightly wrong for that one layout. For small effects (a few percent), sample layouts: vary environment padding (`--env-pad`), link order, or rebuilds, and use a real workload set.

## method.layout-tools — Stabilizer and layout randomization
tags: method, layout, bias, c, cpp
status: cited
source: https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf

Stabilizer repeatedly re-randomizes code, stack and heap layout at runtime so that repeated runs sample the layout space (paper-reported median overhead under 7%). Treat it as the idea to apply: check whether the tool still builds on your compiler before planning around it, and fall back to rebuilds or padding if it doesn't.

## method.sanity — Sanity-check the number against physics
tags: method, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Estimate first: cycles per op, memory bandwidth, line rate, IOPS spec. A result outside what the hardware can do means the benchmark is wrong (optimized away, served from cache, failed silently). Check exit codes and outputs, verify the work happened, and inspect the generated machine code for microbenchmarks.

## method.correctness — Verify the output, not just the time
tags: method, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Fast wrong answers are common: errors returned quickly, truncated results, stale cache hits. Validate results and count errors in every run, and read back transferred data. For load tests, a non-2xx rate above zero invalidates latency percentiles unless you report it alongside them. For inference, report quality with the speed: quantization and short outputs are also "speedups".

## method.representative — Controlled and representative are different goals
tags: method, all
status: unverified

Tuning (no turbo, no SMT, pinned, no ASLR) gives repeatable *comparisons*, not expected production performance. Say which you're doing. For capacity or SLO claims, keep production settings, record them, and accept more noise with more runs.

## method.levels — Repeat at the level where the variance lives
tags: method, statistics, all
status: cited
source: https://kar.kent.ac.uk/33611/

Variance arises between builds, process executions, and in-process iterations. Kalibera and Jones give a method for measuring which level dominates and putting repetition there. Many iterations in a single process cannot make up for a single bad execution.

## method.small-to-large — Sweep, don't sample one point
tags: method, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Sweep input size, load, and thread count. Include random points and pathological sizes (2^n, 2^n±1), not only powers of two. Single points hide cache cliffs, the latency knee, and contention. A chosen range can also hide deficiencies, which is its own form of selective benchmarking.

## method.gregg-checklist — Seven questions for any result
tags: method, reporting, all
status: cited
source: https://brendangregg.com/blog/2018-06-30/benchmarking-checklist.html

Why not double (what's the limiter)? Was it tuned to resemble production? Did it break hardware limits? Did it error? Does it reproduce? Does it matter for real use? Did it even happen? Ask these before believing any number, yours included.
