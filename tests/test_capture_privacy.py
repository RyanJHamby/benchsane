import json
import sys

import pytest

from benchsane.ab import run_ab
from benchsane.capture import capture

FREE_FORM = {
    "RUSTFLAGS": "-L /Users/planteduser/secretdir",
    "CFLAGS": "-O2 -I/home/planteduser/include",
    "CXXFLAGS": "-O2 -DTOKEN=PLANTEDTOKEN",
    "LDFLAGS": "-L/home/planteduser/lib",
    "JAVA_TOOL_OPTIONS": "-Dpassword=PLANTEDSECRET",
}
PLANTED = ["planteduser", "PLANTEDTOKEN", "PLANTEDSECRET", "PLANTEDKEY"]


@pytest.fixture
def planted_env(monkeypatch):
    for k, v in FREE_FORM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "PLANTEDKEY")  # never allowlisted
    monkeypatch.setenv("OMP_NUM_THREADS", "4")  # numeric, safe to record verbatim


def leaked(obj):
    text = json.dumps(obj)
    return [p for p in PLANTED if p in text]


def test_capture_does_not_leak_planted_values(planted_env):
    assert leaked(capture()) == []


def test_free_form_vars_are_recorded_as_hash_and_length(planted_env):
    sel = capture()["env"]["selected"]
    for k, v in FREE_FORM.items():
        assert set(sel[k]) == {"sha256_12", "length"}
        assert sel[k]["length"] == len(v)
        assert len(sel[k]["sha256_12"]) == 12


def test_hash_distinguishes_different_flags(planted_env, monkeypatch):
    a = capture()["env"]["selected"]["CFLAGS"]
    monkeypatch.setenv("CFLAGS", "-O3 -I/home/planteduser/include")
    b = capture()["env"]["selected"]["CFLAGS"]
    assert a["sha256_12"] != b["sha256_12"]


def test_numeric_vars_stay_verbatim(planted_env):
    assert capture()["env"]["selected"]["OMP_NUM_THREADS"] == "4"


def test_opt_in_records_flag_values_verbatim(planted_env):
    sel = capture(include_flag_values=True)["env"]["selected"]
    for k, v in FREE_FORM.items():
        assert sel[k] == v


def test_ab_env_record_does_not_leak(planted_env):
    _, env = run_ab(f"{sys.executable} -c 'pass'", runs=1, warmup=0, seed=1)
    assert leaked(env) == []
