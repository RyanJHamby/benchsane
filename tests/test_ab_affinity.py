import os
import sys

import pytest

from benchsane.ab import run_ab

PY = sys.executable


@pytest.fixture
def fake_affinity(monkeypatch):
    # Fakes the Linux affinity calls so the behaviour is testable on any OS (macOS has neither).
    state = {"cpus": {0, 1, 2, 3}, "calls": []}

    def get(pid):
        return set(state["cpus"])

    def set_(pid, cpus):
        state["cpus"] = set(cpus)
        state["calls"].append(set(cpus))

    monkeypatch.setattr(os, "sched_getaffinity", get, raising=False)
    monkeypatch.setattr(os, "sched_setaffinity", set_, raising=False)
    return state


def test_affinity_restored_after_success(fake_affinity):
    run_ab(f"{PY} -c 'pass'", runs=1, warmup=0, seed=1, cpus={1})
    assert {1} in fake_affinity["calls"], "affinity was never applied"
    assert fake_affinity["cpus"] == {0, 1, 2, 3}


def test_affinity_restored_after_failure(fake_affinity):
    with pytest.raises(RuntimeError, match="exited 3"):
        run_ab(f"{PY} -c 'import sys; sys.exit(3)'", runs=1, warmup=0, seed=1, cpus={1})
    assert {1} in fake_affinity["calls"], "affinity was never applied"
    assert fake_affinity["cpus"] == {0, 1, 2, 3}


def test_affinity_untouched_without_cpus(fake_affinity):
    run_ab(f"{PY} -c 'pass'", runs=1, warmup=0, seed=1)
    assert fake_affinity["calls"] == []
