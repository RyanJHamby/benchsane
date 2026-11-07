"""Small, dependency-free statistics. Seeded so reports reproduce."""
from __future__ import annotations

import math
import random
import statistics as st


def summary(xs):
    xs = list(xs)
    med = st.median(xs)
    return {"n": len(xs), "median": med, "mean": st.fmean(xs), "min": min(xs), "max": max(xs),
            "mad": st.median(abs(x - med) for x in xs),
            "cv": (st.stdev(xs) / st.fmean(xs)) if len(xs) > 1 and st.fmean(xs) else 0.0}


def _pct(sorted_xs, q):
    i = q * (len(sorted_xs) - 1)
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (i - lo)


def ratio_ci(a, b, paired=False, level=0.95, resamples=5000, seed=1):
    """Ratio b/a of medians (or median of pairwise ratios) with a percentile-bootstrap CI."""
    rng = random.Random(seed)
    if paired:
        if len(a) != len(b):
            raise ValueError("paired comparison needs equal-length samples")
        logs = [math.log(y / x) for x, y in zip(a, b)]
        point = math.exp(st.median(logs))
        boots = sorted(math.exp(st.median(rng.choices(logs, k=len(logs)))) for _ in range(resamples))
    else:
        point = st.median(b) / st.median(a)
        boots = sorted(st.median(rng.choices(b, k=len(b))) / st.median(rng.choices(a, k=len(a))) for _ in range(resamples))
    alpha = (1 - level) / 2
    return {"ratio": point, "lo": _pct(boots, alpha), "hi": _pct(boots, 1 - alpha), "level": level, "paired": paired}


def verdict(ci, min_effect=0.01):
    """Direction assumes lower is better (time)."""
    r, lo, hi = ci["ratio"], ci["lo"], ci["hi"]
    if lo <= 1 <= hi:
        return "no-detectable-difference"
    if abs(r - 1) < min_effect:
        return "below-threshold"
    return "faster" if r < 1 else "slower"


def drift(xs):
    """Relative change in median between the first and second half of a series."""
    if len(xs) < 8:
        return None
    mid = len(xs) // 2
    return st.median(xs[mid:]) / st.median(xs[:mid]) - 1
