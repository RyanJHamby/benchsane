"""Randomized, interleaved A/B runner with fresh processes. Executes only what you ask it to."""
from __future__ import annotations

import json
import os
import platform
import random
import shlex
import subprocess
import time

from .capture import capture
from . import formats
from .doctor import GRADE_MEANING, throttle_total
from .stats import drift, ratio_ci, summary, verdict

PAD_MAX = 4096


def _maxrss_bytes(raw):
    # Linux reports KiB. macOS is widely reported as bytes, though its man page says kilobytes.
    return raw if platform.system() == "Darwin" else raw * 1024


def _run_once(cmd, shell, env):
    t0 = time.perf_counter_ns()
    p = subprocess.Popen(cmd, shell=shell, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    # Read stderr before reaping so a chatty process can't block on a full pipe.
    err = p.stderr.read()
    _, status, ru = os.wait4(p.pid, 0)
    t1 = time.perf_counter_ns()
    p.returncode = os.waitstatus_to_exitcode(status)
    p.stderr.close()
    if p.returncode != 0:
        raise RuntimeError(f"command exited {p.returncode}: {err.decode(errors='replace')[-500:]}")
    return {"process.wall_time": (t1 - t0) / 1e9, "process.cpu.user": ru.ru_utime, "process.cpu.system": ru.ru_stime,
            "process.memory.max_rss": _maxrss_bytes(ru.ru_maxrss), "process.context_switches.voluntary": ru.ru_nvcsw,
            "process.context_switches.involuntary": ru.ru_nivcsw, "process.page_faults.major": ru.ru_majflt}


def run_ab(cmd_a, cmd_b=None, runs=30, warmup=2, seed=None, out=None, shell=False, env_pad=False, cpus=None,
           min_effect=0.01, redact=False, progress=None):
    if not hasattr(os, "wait4"):
        raise RuntimeError("benchsane ab is not supported on this platform (needs os.wait4)")
    aa = cmd_b is None
    cmd_b = cmd_a if aa else cmd_b
    names = ("A", "A2") if aa else ("A", "B")
    seed = seed if seed is not None else random.SystemRandom().randrange(2**31)
    rng = random.Random(seed)
    if cpus:
        if not hasattr(os, "sched_setaffinity"):
            raise RuntimeError("--cpus isn't supported on this platform")
        os.sched_setaffinity(0, cpus)
    parse = (lambda c: c) if shell else shlex.split
    argv = {names[0]: parse(cmd_a), names[1]: parse(cmd_b)}
    base_env = dict(os.environ)

    env_before = capture()
    throttle_before = throttle_total()
    for _ in range(warmup):
        for n in names:
            _run_once(argv[n], shell, base_env)

    samples = {n: [] for n in names}
    order_log = []
    started = time.time()
    for i in range(runs):
        order = list(names)
        rng.shuffle(order)
        env = dict(base_env)
        pad = 0
        if env_pad:
            pad = rng.randrange(PAD_MAX)
            env["BENCHSANE_PAD"] = "x" * pad
        for n in order:
            s = _run_once(argv[n], shell, env)
            s["block"] = i
            s["env_pad"] = pad
            samples[n].append(s)
        order_log.append(order)
        if progress:
            progress(i + 1, runs)

    wall = formats.PRIMARY_METRIC
    a = [s[wall] for s in samples[names[0]]]
    b = [s[wall] for s in samples[names[1]]]
    ci = ratio_ci(a, b, paired=True)
    comparison = formats.comparison_record(ci, verdict(ci, min_effect), len(a), len(b), min_effect)
    throttle = throttle_total() - throttle_before
    result = {
        "schema": formats.SCHEMA_RESULT, "tool": formats.tool(), "created_at": formats.now(), "mode": "aa" if aa else "ab",
        "design": {"type": "randomized_blocks", "blocks": runs, "warmup_rounds": warmup, "seed": seed, "env_pad": env_pad,
                   "cpus": sorted(cpus) if cpus else None},
        "arms": {"baseline": names[0], "candidate": names[1]},
        "commands": {names[0]: "<redacted>" if redact else cmd_a, names[1]: "<redacted>" if redact else cmd_b},
        "metrics": formats.METRICS,
        "summary": {n: summary(s[wall] for s in samples[n]) for n in names},
        "comparison": comparison,
        "claim": formats.claim(comparison, env_before),
        "elapsed_seconds": round(time.time() - started, 3), "throttle_events": throttle,
        "warnings": _warnings(a, b, runs, names, samples, throttle, env_before, aa, ci),
        "order": order_log, "samples": samples,
    }
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "samples.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        with open(os.path.join(out, "env.json"), "w", encoding="utf-8") as f:
            json.dump(env_before, f, indent=1)
        with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as f:
            f.write(render_report(result, env_before))
    return result, env_before


def _warnings(a, b, runs, names, samples, throttle, env, aa, ci):
    w = []
    if runs < 10:
        w.append(f"Only {runs} blocks. Treat this as a smoke test; use 30+ for a claim.")
    if min(min(a), min(b)) < 0.005:
        w.append("Runs under 5 ms are dominated by process startup. Use an in-process harness. See startup.cold.")
    for n in names:
        d = drift([s[formats.PRIMARY_METRIC] for s in samples[n]])
        if d is not None and abs(d) > 0.02:
            w.append(f"{n} drifted {d * 100:+.1f}% from first half to second. See stats.drift.")
    if throttle > 0:
        w.append(f"{throttle} thermal throttle events during the run. See linux.thermal.")
    if env.get("grade") != "clean":
        w.append(f"Host grade is {env.get('grade')}. Run `benchsane doctor` for details.")
    if aa and not (ci["lo"] <= 1 <= ci["hi"]):
        w.append("A/A shows a difference: your noise floor is above zero or the procedure has a bias. Don't trust effects smaller than this.")
    return w


def render_report(r, env):
    names = list(r["summary"])
    c = r["comparison"]
    roles = {r["arms"]["baseline"]: "baseline", r["arms"]["candidate"]: "candidate"}
    title = "A/A noise floor" if r["mode"] == "aa" else "A/B comparison"
    lines = [f"# benchsane: {title}", "", f"**Result:** {formats.VERDICT_TEXT[c['verdict']]} {formats.describe(c)}.", "",
             "**Quotable claim:**" if env["grade"] != "smoke" else "**Claim (don't quote this: the host grade is smoke):**", "", f"> {r['claim']}", "",
             "| Arm | Role | Command | n | Median | Min | CV |", "|---|---|---|---:|---:|---:|---:|"]
    for n in names:
        s = r["summary"][n]
        cmd = r["commands"][n].replace("|", "\\|")
        lines.append(f"| {n} | {roles[n]} | `{cmd}` | {s['n']} | {formats.fmt_value(s['median'])} | {formats.fmt_value(s['min'])} | {s['cv'] * 100:.2f}% |")
    d = r["design"]
    lines += ["", "## Method", "",
              f"- Design: randomized blocks in fresh processes, seed {d['seed']}, {d['warmup_rounds']} warmup round(s) discarded",
              f"- Metric: {c['metric']} ({c['unit']}, {c['direction'].replace('_', ' ')})",
              f"- Statistic: {c['statistic'].replace('_', ' ')}, {round(c['ci']['level'] * 100)}% {c['ci']['method'].replace('_', ' ')} interval",
              f"- Practical threshold: {c['min_effect'] * 100:g}%",
              f"- Environment padding: {'on' if d['env_pad'] else 'off'}"]
    if d["cpus"]:
        lines.append(f"- Pinned to CPUs: {', '.join(str(x) for x in d['cpus'])}")
    lines += ["", "## Host", ""]
    cpu = env["cpu"]
    topo = cpu.get("topology") or {}
    cores = f"{topo['physical_cores']} physical cores, " if topo else ""
    lines.append(f"- CPU: {cpu.get('model')} ({cores}{cpu.get('logical')} logical)")
    lines.append(f"- Memory: {env.get('memory_gib')} GiB")
    lines.append(f"- OS: {env['os'].get('distro') or env['os']['system']}, kernel {env['os']['kernel']}, {env['os']['arch']}")
    machine = env.get("machine") or {}
    if machine.get("product"):
        lines.append(f"- Machine: {machine.get('vendor')} {machine.get('product')}")
    if env.get("git"):
        lines.append(f"- Commit: {env['git']['commit'][:12]}{' (dirty)' if env['git']['dirty'] else ''}")
    lines.append(f"- Host grade: **{env['grade']}**. {GRADE_MEANING[env['grade']]}")
    lines.append(f"- Captured: {env['captured_at']}")
    if r["warnings"]:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in r["warnings"]]
    lines += ["", "## Data", "", f"Generated {r['created_at']} by {r['tool']}. Raw data: `samples.json` ({r['schema']}), `env.json` ({env['schema']}).", ""]
    return "\n".join(lines)
