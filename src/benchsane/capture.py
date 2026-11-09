"""Environment manifest. Safe to commit: no hostname, username, env values or git remotes
unless explicitly requested with an allowlisted variable. Free-form flag variables
(FREE_FORM_ENV) are recorded as a hash and length unless include_flag_values is true."""
from __future__ import annotations

import glob
import hashlib
import os
import platform
import re

from . import formats
from .doctor import grade, read, run, run_checks

TOOLCHAINS = {
    "gcc": ["gcc", "--version"], "clang": ["clang", "--version"], "rustc": ["rustc", "-V"],
    "cargo": ["cargo", "-V"], "go": ["go", "version"], "java": ["java", "-version"],
    "node": ["node", "--version"], "dotnet": ["dotnet", "--version"], "python": ["python3", "--version"],
    "perf": ["perf", "--version"], "hyperfine": ["hyperfine", "--version"],
}
# Only these variables' values are recorded: they change performance and aren't secrets.
ENV_ALLOW = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "GOMAXPROCS", "GOGC", "GOMEMLIMIT", "GOAMD64",
             "PYTHONHASHSEED", "CUDA_VISIBLE_DEVICES", "NODE_ENV", "MALLOC_ARENA_MAX", "RUSTFLAGS", "CFLAGS", "CXXFLAGS", "LDFLAGS", "JAVA_TOOL_OPTIONS")

# Free-form text that can carry usernames, paths or secrets: hashed unless the caller opts in.
FREE_FORM_ENV = ("RUSTFLAGS", "CFLAGS", "CXXFLAGS", "LDFLAGS", "JAVA_TOOL_OPTIONS")


def _first_line(cmd):
    import subprocess
    import shutil
    if not shutil.which(cmd[0]):
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = (r.stdout or r.stderr).strip()
    # The JVM prints "Picked up JAVA_TOOL_OPTIONS: <value>" first; that would echo the unhashed value.
    lines = [x for x in out.splitlines() if not x.startswith("Picked up ")]
    return lines[0] if lines else None


def _cpuinfo():
    info = {"model": None, "microcode": None, "flags_hash": None}
    text = read("/proc/cpuinfo") or ""
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = (x.strip() for x in line.split(":", 1))
        if k == "model name" and not info["model"]:
            info["model"] = v
        elif k == "microcode" and not info["microcode"]:
            info["microcode"] = v
        elif k in ("flags", "Features") and not info["flags_hash"]:
            info["flags_hash"] = hashlib.sha256(v.encode()).hexdigest()[:12]
    if not info["model"] and platform.system() == "Darwin":
        info["model"] = run(["sysctl", "-n", "machdep.cpu.brand_string"])
    return info


def _caches():
    out = {}
    for level in ("index0", "index1", "index2", "index3"):
        base = f"/sys/devices/system/cpu/cpu0/cache/{level}"
        if os.path.isdir(base):
            out[f"L{read(base + '/level')}{(read(base + '/type') or '?')[0]}"] = read(base + "/size")
    return out


def _topology():
    """Counts only. Linux exposes these per CPU; other systems return an empty result."""
    seen = set()
    for path in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/topology"):
        package = read(path + "/physical_package_id")
        core = read(path + "/core_id")
        if package is not None and core is not None:
            seen.add((package, core))
    if not seen:
        return {}
    logical = len(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/topology"))
    return {"sockets": len({p for p, _ in seen}), "physical_cores": len(seen), "threads_per_core": round(logical / len(seen), 2)}


def _memory():
    m = re.search(r"MemTotal:\s+(\d+) kB", read("/proc/meminfo") or "")
    if m:
        return round(int(m.group(1)) / 1024 / 1024, 1)
    b = run(["sysctl", "-n", "hw.memsize"])
    return round(int(b) / 1024**3, 1) if b and b.isdigit() else None


def _cloud():
    vendor = read("/sys/class/dmi/id/sys_vendor")
    product = read("/sys/class/dmi/id/product_name")
    return {"vendor": vendor, "product": product}


def _git():
    commit = run(["git", "rev-parse", "HEAD"])
    if not commit:
        return None
    return {"commit": commit, "dirty": bool(run(["git", "status", "--porcelain"]))}


def _env_value(name, value, include_flag_values):
    if name in FREE_FORM_ENV and not include_flag_values:
        return {"sha256_12": hashlib.sha256(value.encode()).hexdigest()[:12], "length": len(value)}
    return value


def capture(include_flag_values=False):
    checks = run_checks()
    env = {k: _env_value(k, os.environ[k], include_flag_values) for k in ENV_ALLOW if k in os.environ}
    return {
        "schema": formats.SCHEMA_ENV,
        "tool": formats.tool(),
        "captured_at": formats.now(),
        "os": {"system": platform.system(), "kernel": platform.release(), "arch": platform.machine(),
               "distro": _distro(), "cmdline": read("/proc/cmdline")},
        "cpu": {**_cpuinfo(), "logical": os.cpu_count(), "topology": _topology(), "caches": _caches()},
        "memory_gib": _memory(),
        "machine": _cloud(),
        "gpu": run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,power.limit", "--format=csv,noheader"], timeout=10),
        "toolchains": {k: v for k, v in ((n, _first_line(c)) for n, c in TOOLCHAINS.items()) if v},
        "env": {"size_bytes": sum(len(k) + len(v) + 2 for k, v in os.environ.items()), "selected": env},
        "git": _git(),
        "checks": [c.to_dict() for c in checks],
        "grade": grade(checks),
    }


def _distro():
    text = read("/etc/os-release") or ""
    m = re.search(r'^PRETTY_NAME="?([^"\n]+)', text, re.M)
    return m.group(1) if m else None


# Keys where a difference between two runs undermines a comparison.
COMPARE_KEYS = [("os", "kernel"), ("os", "arch"), ("os", "cmdline"), ("cpu", "model"), ("cpu", "microcode"), ("cpu", "logical"), ("cpu", "topology"),
                ("memory_gib",), ("machine", "product"), ("gpu",), ("toolchains",)]


def diff_env(a, b):
    diffs = []
    for path in COMPARE_KEYS:
        x, y = a, b
        for p in path:
            x = (x or {}).get(p) if isinstance(x, dict) else None
            y = (y or {}).get(p) if isinstance(y, dict) else None
        if x != y:
            diffs.append(f"{'.'.join(path)}: {x!r} vs {y!r}")
    return diffs
