import json
import os
import sys

from benchsane import cli
from benchsane.ab import run_ab
from benchsane.capture import capture, diff_env

PY = sys.executable


def sleeper(ms):
    return f"{PY} -c 'import time; time.sleep({ms / 1000})'"


def test_detects_injected_slowdown(tmp_path):
    # Mechanism test, not a sensitivity test: the effect is large against Python's startup
    # noise so a shared CI runner cannot hide it (10ms vs 30ms flaked on a macOS runner).
    # How small an effect is detectable is measured by the M4 calibration runs.
    r, env = run_ab(sleeper(20), sleeper(120), runs=12, warmup=1, seed=1, out=str(tmp_path / "x"))
    assert r["comparison"]["verdict"] == "slower"
    assert r["comparison"]["ratio"] > 1.2
    assert all(len(v) == 12 for v in r["samples"].values())
    assert {tuple(o) for o in r["order"]} == {("A", "B"), ("B", "A")}
    for name in ("samples.json", "env.json", "report.md"):
        assert os.path.exists(tmp_path / "x" / name)


def test_aa_mode(tmp_path):
    r, _ = run_ab(sleeper(5), runs=10, warmup=0, seed=2)
    assert r["mode"] == "aa" and set(r["samples"]) == {"A", "A2"}


def test_failed_command_aborts():
    try:
        run_ab(f"{PY} -c 'raise SystemExit(3)'", runs=2, warmup=0)
    except RuntimeError as e:
        assert "exited 3" in str(e)
    else:
        raise AssertionError("should abort")


def test_chatty_stderr_does_not_deadlock():
    cmd = f"{PY} -c 'import sys; sys.stderr.write(\"x\" * 200000)'"
    r, _ = run_ab(cmd, runs=2, warmup=0)
    assert r["summary"]["A"]["n"] == 2


def test_env_pad_varies_and_matches_in_block():
    r, _ = run_ab(sleeper(1), runs=6, warmup=0, seed=3, env_pad=True)
    a, b = r["samples"]["A"], r["samples"]["A2"]
    assert [s["env_pad"] for s in a] == [s["env_pad"] for s in b]
    assert len({s["env_pad"] for s in a}) > 1


def test_redaction(tmp_path):
    run_ab(sleeper(1) + " ", sleeper(1), runs=2, warmup=0, out=str(tmp_path / "r"), redact=True)
    text = (tmp_path / "r" / "samples.json").read_text() + (tmp_path / "r" / "report.md").read_text()
    assert "time.sleep" not in text


def test_capture_leaks_nothing(monkeypatch):
    monkeypatch.setenv("MY_SECRET_TOKEN", "hunter2-do-not-leak")
    import socket
    env = capture()
    text = json.dumps(env)
    assert "hunter2-do-not-leak" not in text
    assert "MY_SECRET_TOKEN" not in text
    host = socket.gethostname()
    if len(host) > 3 and host not in ("localhost", "vm"):
        assert host not in text
    assert "remote" not in (env.get("git") or {})


def test_diff_env():
    a, b = capture(), capture()
    assert diff_env(a, b) == []
    b["cpu"]["model"] = "other"
    assert any("cpu.model" in d for d in diff_env(a, b))


def test_cli_end_to_end(tmp_path, capsys):
    out = tmp_path / "run"
    assert cli.main(["ab", "-a", sleeper(1), "--aa", "--runs", "2", "--warmup", "0", "--out", str(out)]) == 0
    assert cli.main(["ab", "-a", sleeper(1), "--aa", "--runs", "2", "--out", str(out)]) == 2  # Won't overwrite evidence.
    assert cli.main(["compare", str(out / "samples.json"), str(out / "samples.json")]) == 2  # Arm must be explicit.
    assert cli.main(["compare", str(out / "samples.json"), str(out / "samples.json"), "--select-baseline", "A", "--select-candidate", "A2"]) == 0
    assert cli.main(["kb", "show", "nope"]) == 2
    assert cli.main(["kb", "list", "--tag", "gpu"]) == 0
    assert cli.main(["init", str(tmp_path)]) == 0
    assert (tmp_path / "bench" / "PLAN.md").exists()
    skills = tmp_path / "skills"
    assert cli.main(["install-skill", "--dir", str(skills)]) == 0
    assert (skills / "benchsane" / "SKILL.md").read_text().startswith("---")
    assert cli.main(["install-skill", "--dir", str(skills)]) == 2


def test_compare_flags_regression(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text(" ".join(str(1 + i * 0.001) for i in range(20)))
    b.write_text(" ".join(str(2 + i * 0.001) for i in range(20)))
    assert cli.main(["compare", str(a), str(b), "--fail-on-regression"]) == 3


def test_topology_is_comparable():
    topo = capture()["cpu"]["topology"]
    if topo:
        assert topo["physical_cores"] >= 1 and topo["sockets"] >= 1


def test_report_names_pinned_cpus(tmp_path):
    if not hasattr(os, "sched_setaffinity"):
        return
    before = os.sched_getaffinity(0)
    try:
        cpu = min(before)
        run_ab(sleeper(1), runs=2, warmup=0, cpus={cpu}, out=str(tmp_path / "p"))
    finally:
        os.sched_setaffinity(0, before)
    assert f"Pinned to CPUs: {cpu}" in (tmp_path / "p" / "report.md").read_text()
