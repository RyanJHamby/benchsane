import json

import pytest

from benchsane.compare import LoadError, compare, load


def w(p, obj):
    p.write_text(json.dumps(obj) if not isinstance(obj, str) else obj)
    return str(p)


def test_hyperfine(tmp_path):
    p = w(tmp_path / "h.json", {"results": [{"command": "a", "times": [1.0, 1.1]}, {"command": "b", "times": [2.0, 2.1]}]})
    assert load(p, "b")[0] == [2.0, 2.1]
    with pytest.raises(LoadError):
        load(p)


def test_google_benchmark_units_and_aggregates(tmp_path):
    p = w(tmp_path / "g.json", {"context": {}, "benchmarks": [
        {"name": "BM/1", "run_name": "BM/1", "run_type": "iteration", "real_time": 100, "time_unit": "ns"},
        {"name": "BM/1", "run_name": "BM/1", "run_type": "iteration", "real_time": 200, "time_unit": "ns"},
        {"name": "BM/1_mean", "run_name": "BM/1", "run_type": "aggregate", "real_time": 150, "time_unit": "ns"},
    ]})
    vals, _, kind, independent = load(p)
    assert vals == pytest.approx([1e-7, 2e-7])
    assert kind == "google-benchmark" and independent is False


def test_pyperf_process_level(tmp_path):
    p = w(tmp_path / "p.json", {"benchmarks": [{"metadata": {"name": "x"}, "runs": [{"metadata": {}, "warmups": [[1, 9.0]]}, {"values": [1.0, 3.0]}, {"values": [2.0, 2.0]}]}]})
    assert load(p)[0] == [2.0, 2.0]


def test_plain(tmp_path):
    assert load(w(tmp_path / "x.txt", "1\n2 3\n"))[0] == [1, 2, 3]


def test_rejects_garbage(tmp_path):
    with pytest.raises(LoadError):
        load(w(tmp_path / "x.txt", "not numbers"))
    with pytest.raises(LoadError):
        load(w(tmp_path / "y.json", {"foo": 1}))


def test_compare_warns_about_process_reuse_and_interleaving(tmp_path):
    g = {"context": {}, "benchmarks": [{"name": "B", "run_name": "B", "run_type": "iteration", "real_time": 100 + i, "time_unit": "ns"} for i in range(20)]}
    a = w(tmp_path / "a.json", g)
    b = w(tmp_path / "b.json", g)
    r = compare(a, b)
    text = " ".join(r["warnings"])
    assert "pseudoreplication" in text and "interleav" in text and "env.json" in text
