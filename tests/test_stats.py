import random

from benchsane.stats import drift, ratio_ci, summary, verdict


def noisy(center, n, seed, cv=0.01):
    r = random.Random(seed)
    return [r.gauss(center, center * cv) for _ in range(n)]


def test_detects_known_slowdown():
    a, b = noisy(1.0, 30, 1), noisy(1.10, 30, 2)
    ci = ratio_ci(a, b)
    assert ci["lo"] < 1.10 < ci["hi"]
    assert verdict(ci) == "slower"


def test_detects_known_speedup_paired():
    a = noisy(1.0, 30, 3)
    b = [x * 0.9 for x in a]
    ci = ratio_ci(a, b, paired=True)
    assert abs(ci["ratio"] - 0.9) < 1e-9
    assert verdict(ci) == "faster"


def test_paired_cancels_shared_drift():
    # Both arms share a large trend, which unpaired analysis can't separate.
    trend = [1 + i * 0.02 for i in range(30)]
    a = [t * x for t, x in zip(trend, noisy(1.0, 30, 4, 0.002))]
    b = [t * x for t, x in zip(trend, noisy(1.05, 30, 5, 0.002))]
    paired = ratio_ci(a, b, paired=True)
    unpaired = ratio_ci(a, b, paired=False)
    assert (paired["hi"] - paired["lo"]) < (unpaired["hi"] - unpaired["lo"]) / 3
    assert verdict(paired) == "slower"


def test_false_positive_rate_is_sane():
    hits = 0
    trials = 200
    for s in range(trials):
        a, b = noisy(1.0, 30, 1000 + s), noisy(1.0, 30, 5000 + s)
        ci = ratio_ci(a, b, resamples=400, seed=s)
        hits += not (ci["lo"] <= 1 <= ci["hi"])
    # Nominal 5%; percentile bootstraps of medians at n=30 can run a little off.
    assert hits / trials < 0.12


def test_below_threshold():
    assert verdict({"ratio": 1.005, "lo": 1.002, "hi": 1.008}, 0.01) == "below-threshold"


def test_no_difference():
    assert verdict({"ratio": 1.02, "lo": 0.99, "hi": 1.05}, 0.01) == "no-detectable-difference"


def test_reproducible_seed():
    a, b = noisy(1, 20, 6), noisy(1, 20, 7)
    assert ratio_ci(a, b) == ratio_ci(a, b)


def test_drift():
    assert drift(list(range(1, 3))) is None
    assert drift([1.0] * 10 + [1.1] * 10) > 0.09


def test_summary():
    assert summary([1, 2, 3])["median"] == 2
