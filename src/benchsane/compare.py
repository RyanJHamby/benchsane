"""Load samples from common benchmark formats and compare them."""
from __future__ import annotations

import json
import os

from . import formats
from .capture import diff_env
from .stats import ratio_ci, summary, verdict

UNIT = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0}


class LoadError(ValueError):
    pass


def load(path, select=None):
    """Returns (samples, unit, source_kind, independent). 'path' may be file or file:name."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            return [float(x) for x in text.split()], "s", "plain", True
        except ValueError as e:
            raise LoadError(f"{path}: not JSON and not a list of numbers") from e
    if isinstance(data, dict) and str(data.get("schema", "")).startswith("benchsane.result/"):
        arm = select
        if arm not in data["samples"]:
            raise LoadError(f"{path}: choose an arm with --select-baseline/--select-candidate; have {sorted(data['samples'])}")
        return [s[formats.PRIMARY_METRIC] for s in data["samples"][arm]], "s", "benchsane", True
    if isinstance(data, dict) and "results" in data and data["results"] and "times" in data["results"][0]:
        results = data["results"]
        chosen = _choose(results, select, lambda r: r.get("command"), path)
        return list(chosen["times"]), "s", "hyperfine", True
    if isinstance(data, dict) and "benchmarks" in data and "context" in data:
        rows = [b for b in data["benchmarks"] if b.get("run_type", "iteration") == "iteration"]
        names = sorted({b.get("run_name", b["name"]) for b in rows})
        name = select or (names[0] if len(names) == 1 else None)
        if name is None:
            raise LoadError(f"{path}: several benchmarks; choose with --select. Have: {names[:20]}")
        vals = [b["real_time"] * UNIT.get(b.get("time_unit", "ns"), 1e-9) for b in rows if b.get("run_name", b["name"]) == name]
        if not vals:
            raise LoadError(f"{path}: no iterations for {name!r}")
        return vals, "s", "google-benchmark", False
    if isinstance(data, dict) and "benchmarks" in data:
        benches = data["benchmarks"]
        chosen = _choose(benches, select, lambda b: (b.get("metadata") or {}).get("name"), path)
        vals = [sum(r["values"]) / len(r["values"]) for r in chosen["runs"] if r.get("values")]
        return vals, "s", "pyperf", True
    raise LoadError(f"{path}: unrecognized format (supported: benchsane, hyperfine, Google Benchmark, pyperf, plain numbers)")


def _choose(items, select, key, path):
    if select is None:
        if len(items) == 1:
            return items[0]
        raise LoadError(f"{path}: several entries; choose with --select. Have: {[key(i) for i in items][:20]}")
    for it in items:
        if key(it) == select:
            return it
    raise LoadError(f"{path}: {select!r} not found. Have: {[key(i) for i in items][:20]}")


def _sibling_env(path):
    candidate = os.path.join(os.path.dirname(os.path.abspath(path)), "env.json")
    if os.path.exists(candidate):
        try:
            with open(candidate, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def compare(path_a, path_b, select_a=None, select_b=None, min_effect=0.01, level=0.95):
    a, _, kind_a, ind_a = load(path_a, select_a)
    b, _, kind_b, ind_b = load(path_b, select_b)
    if len(a) < 2 or len(b) < 2:
        raise LoadError("need at least two samples per side")
    if min(a) <= 0 or min(b) <= 0:
        raise LoadError("samples must be positive")
    ci = ratio_ci(a, b, paired=False, level=level)
    warnings = []
    if min(len(a), len(b)) < 10:
        warnings.append(f"Only {min(len(a), len(b))} samples on one side; aim for 30+ process-level runs.")
    if not (ind_a and ind_b):
        warnings.append("Samples are repetitions inside one process family (Google Benchmark). Their CI may be too narrow; run separate processes. See stats.pseudoreplication.")
    warnings.append("These runs weren't interleaved in one session, so time-related drift is mixed into the effect. Prefer `benchsane ab`. See method.interleave.")
    env_a, env_b = _sibling_env(path_a), _sibling_env(path_b)
    if env_a and env_b:
        diffs = diff_env(env_a, env_b)
        if diffs:
            warnings.append("Environments differ: " + "; ".join(diffs))
    else:
        warnings.append("No env.json next to one or both inputs, so environments couldn't be compared.")
    comparison = formats.comparison_record(ci, verdict(ci, min_effect), len(a), len(b), min_effect)
    return {"schema": formats.SCHEMA_COMPARISON, "tool": formats.tool(), "created_at": formats.now(),
            "baseline": {"source_format": kind_a, "summary": summary(a)}, "candidate": {"source_format": kind_b, "summary": summary(b)},
            "metrics": {comparison["metric"]: formats.METRICS[comparison["metric"]]}, "comparison": comparison,
            "claim": formats.claim(comparison, env_b, "samples"), "warnings": warnings}
