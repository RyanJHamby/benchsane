# Reporting

## report.minimum — Minimum for a quotable number
tags: reporting, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html

Baseline and effect with CI; absolute numbers too (not just ratios); n and what a sample is; hardware, OS, kernel, compiler and flags; workload and input; date and commit; a link to raw results and a one-command reproduction. Missing platform details and relative-only numbers are named crimes. Show sub-benchmark results alongside summaries.

## report.checklist — SIGPLAN empirical evaluation checklist
tags: reporting, method, all
status: cited
source: https://raw.githubusercontent.com/SIGPLAN/empirical-evaluation/master/checklist/checklist.pdf

Run through it before publishing: explicit, scoped claims; appropriate baseline and fair comparison; justified benchmark suite with real applications; enough trials; suitable summary statistics; reporting the distribution; direct metrics covering all important effects; enough detail to repeat; open-loop workload generators; charts whose axes include zero and correctly plotted ratios; sensible precision.

## report.precision — Don't over-report precision
tags: reporting, statistics
status: cited
source: https://raw.githubusercontent.com/SIGPLAN/empirical-evaluation/master/checklist/checklist.pdf

"3.14159 ms" with a 2% CI overstates what you know: match significant figures to the interval. Don't truncate chart axes to dramatize a small gain, and plot ratios in a way that treats 2× faster and 2× slower symmetrically (log axis).

## report.crimes — Heiser's benchmarking crimes
tags: reporting, method, all
status: cited
source: https://gernot-heiser.org/benchmarking-crimes.html https://www.vusec.net/projects/benchmarking-crimes/

Self-review against the list: subsetting; selective data ranges; microbenchmarks as overall performance; throughput drop treated as overhead; percentage point tricks; no significance; arithmetic mean of ratios; calibration data used for evaluation; no true baseline; comparing only against yourself; unfair competitors; outdated state of the art; missing platform; hidden sub-results; relative numbers only. The later SoK paper found tier-1 security papers commit about five on average, so assume yours has some.

## report.cross-machine — Don't transfer numbers between machines
tags: reporting, hardware, all
status: unverified

Numbers from a laptop, a VM and a server aren't interchangeable, and ratios often don't transfer either, since cache sizes, memory bandwidth and core count change which part is limiting. Name the host on every number. If numbers differ across machines, publish both.

## report.licensing — Publication restrictions
tags: reporting, legal
status: unverified

Some commercial software licenses restrict publishing benchmark results (so-called "DeWitt clauses"), and TPC and SPEC names carry reporting rules. Check before you publish a named product comparison.
