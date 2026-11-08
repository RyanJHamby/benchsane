import os
import sys

import pytest

from benchsane.ab import run_ab

PY = sys.executable
CMD = f"{PY} -c 'pass'"


@pytest.mark.xfail(strict=True, reason="spec ab-platform-guard: remove this marker when implemented")
def test_run_ab_fails_fast_without_wait4(monkeypatch):
    # Platforms without os.wait4 (Windows) must get one clear error before any command runs,
    # not an AttributeError after warmup has already spawned processes.
    monkeypatch.delattr(os, "wait4", raising=False)
    spawned = []

    def fake_run_once(*a, **k):
        spawned.append(a)
        raise AssertionError("a command was spawned before the platform check")

    monkeypatch.setattr("benchsane.ab._run_once", fake_run_once)
    with pytest.raises(RuntimeError, match="not supported on this platform"):
        run_ab(CMD, runs=2, warmup=1, seed=1)
    assert spawned == []


def test_exit_code_decoding_still_works():
    with pytest.raises(RuntimeError, match="exited 3"):
        run_ab(f"{PY} -c 'import sys; sys.exit(3)'", runs=1, warmup=0, seed=1)
