# Statistics

## stats.summary — Report median and a CI, and keep raw samples
tags: statistics, reporting, all
status: unverified
source: https://gernot-heiser.org/benchmarking-crimes.html

Timing data is usually skewed and often multimodal, so mean ± stddev can mislead. Report median plus a bootstrap CI on the ratio, and keep raw samples to re-analyze later. Averages without variance are a benchmarking crime. Rule of thumb from Heiser for tightly controlled systems work: expect under 0.1% stddev, and be concerned above 1%; many real workloads won't reach that, so measure your own floor.

## stats.ratio — Effects are ratios against the baseline
tags: statistics, reporting, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

The baseline is the denominator. 60s to 45s is a 25% improvement, not 33%. 60s to 80s is 33% worse, not 25%. Overhead rising from 6% to 13% more than doubled; "+7" is percentage points. Throughput drop is not overhead: compare cost per unit of work (CPU ÷ throughput).

## stats.geomean — Geometric mean across different benchmarks
tags: statistics, reporting, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Combine normalized scores with the geometric mean, not the arithmetic mean, and always show the per-benchmark results as well, because a summary hides regressions. Arithmetic means make sense only when absolute times themselves are what you care about.

## stats.pseudoreplication — Iterations are not independent samples
tags: statistics, all
status: cited
source: https://kar.kent.ac.uk/33611/

10,000 iterations in one process is not n=10,000. Layout, JIT decisions and allocator state are fixed per process, so samples correlate and CIs come out far too narrow. Use process-level (or build-level) summaries as your samples.

## stats.tail-n — Percentiles need sample count
tags: statistics, latency, all
status: unverified

You need well over 1/(1−p) samples: p99 needs far more than 100, and p99.9 far more than 1,000; aim for at least 10× that before trusting a tail point. Report n. Also, percentiles can't be averaged across windows or hosts: merge histograms (HdrHistogram) instead.

## stats.outliers — Don't delete outliers silently
tags: statistics, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Outliers are often the finding (GC pause, page fault, migration). Discard only under a stated procedure with a stated reason, and report it. Investigate a bimodal distribution rather than summarizing it.

## stats.min — Minimum vs median
tags: statistics, c, cpp, rust
status: unverified

Minimum estimates the undisturbed fast path for deterministic CPU work, and is robust to additive noise, but says nothing about behavior users see and hides real variance sources. Use the median for comparisons, and min only as a supplementary view for deterministic microbenchmarks. State which you used.

## stats.threshold — Practical significance beats a p-value
tags: statistics, all
status: unverified

With enough runs, trivial differences become significant. Set a minimum effect in advance (e.g. 1%), and only claim a difference if the CI excludes no-change and the effect exceeds both this threshold and the A/A noise floor. `benchsane compare --min-effect` applies this.

## stats.multiple — Many comparisons produce false positives
tags: statistics, ci, all
status: unverified

Testing 100 benchmarks at 95% produces about 5 spurious "changes" with no real change. Correct for it (e.g. Benjamini-Hochberg), re-run suspected hits as a separate confirmation, and use change-point detection for time series in CI (e.g. Apache Otava) rather than per-commit thresholds.

## stats.warmup — Verify a steady state exists
tags: statistics, jit, java, javascript, python, dotnet
status: cited
source: https://arxiv.org/abs/1602.00602v6

Barrett et al. found at most 43.5% of (VM, benchmark) pairs consistently reached a steady state of peak performance, even with small deterministic benchmarks under tight control. Some slow down over time. Plot iteration time and don't just drop the first N. Report warmup and steady state separately, and don't assume steady state exists.

## stats.drift — Check for drift
tags: statistics, all
status: unverified

Compare the first and second halves of a run. Trends suggest thermal limits, cache growth, a leak, or burst credits running out. `benchsane ab` reports drift per arm and flags it.
