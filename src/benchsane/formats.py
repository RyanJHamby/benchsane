"""One vocabulary for every output: schema ids, metric names, units, verdicts and exports.

Metric names and units follow OpenTelemetry conventions: hierarchical names, no unit in the name,
UCUM units, durations in seconds and sizes in bytes.
"""
from __future__ import annotations

import csv
import datetime as dt
import io

from . import __version__

SCHEMA_RESULT = "benchsane.result/v1"
SCHEMA_COMPARISON = "benchsane.comparison/v1"
SCHEMA_DOCTOR = "benchsane.doctor/v1"
SCHEMA_ENV = "benchsane.env/v1"

PRIMARY_METRIC = "process.wall_time"
METRICS = {
    "process.wall_time": {"unit": "s", "direction": "lower_is_better", "description": "Elapsed time from spawn to exit"},
    "process.cpu.user": {"unit": "s", "direction": "lower_is_better", "description": "User CPU time"},
    "process.cpu.system": {"unit": "s", "direction": "lower_is_better", "description": "System CPU time"},
    "process.memory.max_rss": {"unit": "By", "direction": "lower_is_better", "description": "Peak resident set size"},
    "process.context_switches.voluntary": {"unit": "{switch}", "direction": "lower_is_better", "description": "Voluntary context switches"},
    "process.context_switches.involuntary": {"unit": "{switch}", "direction": "lower_is_better", "description": "Involuntary context switches"},
    "process.page_faults.major": {"unit": "{fault}", "direction": "lower_is_better", "description": "Major page faults"},
}

VERDICT_TEXT = {
    "faster": "Candidate is faster than baseline.",
    "slower": "Candidate is slower than baseline.",
    "no-detectable-difference": "No detectable difference at this sample size. That isn't proof of no difference.",
    "below-threshold": "A difference was detected, but it's below the practical threshold.",
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def tool():
    return f"benchsane {__version__}"


def comparison_record(ci, verdict, n_baseline, n_candidate, min_effect, metric=PRIMARY_METRIC):
    """The same object for every comparison. Change is relative to the baseline."""
    return {
        "metric": metric,
        "unit": METRICS[metric]["unit"],
        "direction": METRICS[metric]["direction"],
        "statistic": "median_of_paired_ratios" if ci["paired"] else "ratio_of_medians",
        "ratio": ci["ratio"],
        "change_percent": (ci["ratio"] - 1) * 100,
        "ci": {"level": ci["level"], "method": "percentile_bootstrap", "ratio_lower": ci["lo"], "ratio_upper": ci["hi"],
               "change_percent_lower": (ci["lo"] - 1) * 100, "change_percent_upper": (ci["hi"] - 1) * 100},
        "n_baseline": n_baseline,
        "n_candidate": n_candidate,
        "min_effect": min_effect,
        "verdict": verdict,
    }


def _decimals(c):
    """Match precision to what the interval supports (see report.precision)."""
    return 2 if c["ci"]["change_percent_upper"] - c["ci"]["change_percent_lower"] < 1 else 1


def describe(c):
    d = _decimals(c)
    level = round(c["ci"]["level"] * 100)
    return f"{c['change_percent']:+.{d}f}% vs baseline ({level}% CI {c['ci']['change_percent_lower']:+.{d}f}% to {c['ci']['change_percent_upper']:+.{d}f}%)"


def fmt_value(value, unit="s"):
    if unit == "s":
        for name, f in (("s", 1), ("ms", 1e3), ("µs", 1e6), ("ns", 1e9)):
            if abs(value) * f >= 1:
                return f"{value * f:.4g} {name}"
        return f"{value * 1e9:.3g} ns"
    if unit == "By":
        for name, f in (("GiB", 1024**3), ("MiB", 1024**2), ("KiB", 1024)):
            if abs(value) >= f:
                return f"{value / f:.4g} {name}"
        return f"{value:.0f} B"
    return f"{value:g}"


def host_line(env):
    if not env:
        return "host not recorded"
    cpu = env.get("cpu") or {}
    topo = cpu.get("topology") or {}
    cores = f"{topo['physical_cores']} physical cores" if topo else f"{cpu.get('logical')} logical CPUs"
    system = (env.get("os") or {}).get("system")
    kernel = (env.get("os") or {}).get("kernel")
    return f"{cpu.get('model') or 'unknown CPU'}, {cores}, {system} {kernel}"


def claim(c, env=None, unit_of_sample="process runs"):
    """A single sentence that is safe to quote: it carries its own evidence."""
    d = _decimals(c)
    level = round(c["ci"]["level"] * 100)
    interval = f"{level}% CI {c['ci']['change_percent_lower']:+.{d}f}% to {c['ci']['change_percent_upper']:+.{d}f}%"
    what = {"faster": f"Candidate is {abs(c['change_percent']):.{d}f}% faster than baseline",
            "slower": f"Candidate is {abs(c['change_percent']):.{d}f}% slower than baseline",
            "no-detectable-difference": "No detectable difference between candidate and baseline",
            "below-threshold": f"Candidate differs from baseline by {c['change_percent']:+.{d}f}%, below the {c['min_effect'] * 100:g}% threshold"}[c["verdict"]]
    parts = [f"{interval}", f"n={c['n_baseline']}/{c['n_candidate']} {unit_of_sample}", host_line(env)]
    if env:
        parts.append(f"host grade {env.get('grade')}")
        parts.append(str(env.get("captured_at", ""))[:10])
        if env.get("git"):
            parts.append(f"commit {env['git']['commit'][:12]}" + (" (dirty)" if env["git"]["dirty"] else ""))
    return f"{what} in median {c['metric']} ({'; '.join(parts)})."


def _arms(result):
    return list(result["samples"])


def to_csv(result):
    """Tidy format: one observation per row."""
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["arm", "block", "env_pad_bytes", "metric", "value", "unit"])
    for arm in _arms(result):
        for s in result["samples"][arm]:
            for m in METRICS:
                w.writerow([arm, s["block"], s["env_pad"], m, s[m], METRICS[m]["unit"]])
    return out.getvalue()


def _name(arm, name):
    return f"{name}/{arm}" if name else arm


def to_bmf(result, name=None):
    """Bencher Metric Format. It has no unit field, so the measure name carries the unit."""
    return {_name(arm, name): {"wall-time-seconds": {"value": s["median"], "lower_value": s["min"], "upper_value": s["max"]}}
            for arm, s in result["summary"].items()}


def to_github_benchmark(result, name=None):
    """github-action-benchmark's customSmallerIsBetter format."""
    return [{"name": _name(arm, name), "unit": "s", "value": s["median"], "range": f"± {s['mad']:.6g}",
             "extra": f"median of {s['n']} process runs; range is median absolute deviation"}
            for arm, s in result["summary"].items()]
