# Output formats

Every benchsane output uses the same vocabulary, so scripts, agents and people read results the same way.

## Outputs

| File or command | Schema id | For |
|---|---|---|
| `samples.json` from `ab` | `benchsane.result/v1` | Full record of a run, including raw samples |
| `env.json`, `capture` | `benchsane.env/v1` | What the run happened on |
| `compare --json` | `benchsane.comparison/v1` | Comparison of two existing result files |
| `doctor --json` | `benchsane.doctor/v1` | Host findings and grade |
| `report.md` | None (for people) | Result, claim, method, host, warnings, data |

Print a schema with `benchsane schema result` (also `comparison`, `doctor`, `env`). They're JSON Schema draft 2020-12 files, and the test suite validates real output against them.

**Versioning.** Within `v1`, fields may be added but won't be renamed or removed, and meanings won't change. Breaking changes get `v2`. Ignore fields you don't recognize. Until the 1.0 release, a `v1` schema may still change, and any change will be listed in the release notes.

## Labels

| Concept | Label | Notes |
|---|---|---|
| The reference side | `baseline` | The denominator for every change |
| The side being tested | `candidate` | |
| Change | `change_percent` | `(candidate / baseline − 1) × 100`. Positive means a larger value, which for time means slower |
| Ratio | `ratio` | `candidate / baseline`, or the median of paired ratios for `ab` |
| Interval | `ci` | Holds `level`, `method`, and bounds for the ratio and the change |
| Verdict | `verdict` | `faster`, `slower`, `no-detectable-difference` or `below-threshold` |
| Check severity | `level` | `ok`, `info`, `warn` or `fail` |
| Host grade | `grade` | `clean`, `caveated` or `smoke` |
| Timestamps | `created_at`, `captured_at` | ISO 8601 in UTC |

`no-detectable-difference` is deliberately not `no-difference`.

## Metrics

Names and units follow [OpenTelemetry's metric conventions](https://opentelemetry.io/docs/specs/semconv/general/metrics/): hierarchical names, no unit in the name, UCUM units, seconds for durations, and unprefixed bytes.

| Metric | Unit | Better |
|---|---|---|
| `process.wall_time` (primary) | `s` | Lower |
| `process.cpu.user` | `s` | Lower |
| `process.cpu.system` | `s` | Lower |
| `process.memory.max_rss` | `By` | Lower |
| `process.context_switches.voluntary` | `{switch}` | Lower |
| `process.context_switches.involuntary` | `{switch}` | Lower |
| `process.page_faults.major` | `{fault}` | Lower |

Human-readable output scales for reading (`53.56 ms`). JSON and CSV always use the base unit.

## The claim

Each result has a `claim`: one sentence meant to be pasted into a PR, doc or post, with its evidence attached.

```text
Candidate is 12.3% slower than baseline in median process.wall_time (95% CI +10.1% to +14.2%; n=30/30 process runs; <CPU>, <cores> physical cores, Linux <kernel>; host grade clean; <date>; commit <hash>).
```

*The figures above are illustrative, not a measurement.*

Precision follows the interval: one decimal place normally, and two when the interval is narrower than one percentage point. A `smoke`-grade report labels its claim as not for quoting.

## Exports

```bash
benchsane export samples.json --to csv                 # Tidy: one observation per row
benchsane export samples.json --to bmf --name mybench  # Bencher Metric Format
benchsane export samples.json --to github-benchmark    # github-action-benchmark
benchsane export samples.json --to claim               # Just the sentence
```

| Target | Format | Notes |
|---|---|---|
| Spreadsheets, pandas, R | `csv` | Columns: `arm, block, env_pad_bytes, metric, value, unit` |
| [Bencher](https://bencher.dev/docs/reference/bencher-metric-format) | `bmf` | `value` is the median, and the bounds are min and max. BMF has no unit field, so the measure is named `wall-time-seconds` |
| [github-action-benchmark](https://www.github.com/benchmark-action/github-action-benchmark) | `github-benchmark` | Use with `tool: customSmallerIsBetter`. `value` is the median, and `range` is the median absolute deviation |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | `doctor` graded the host `smoke` (or any warning with `--strict`), or a command run by `ab` failed |
| 2 | Bad input or usage |
| 3 | `compare --fail-on-regression` found the candidate slower |

Formats not included yet: JUnit, OpenMetrics and OTLP. They're worth adding only when someone needs them. SARIF doesn't suit `doctor`, because its findings describe a machine rather than a location in code.
