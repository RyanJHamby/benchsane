"""Read-only preflight checks. Nothing here changes system state."""
from __future__ import annotations

import glob
import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass

from . import formats

OK, INFO, WARN, FAIL = "ok", "info", "warn", "fail"
ORDER = {OK: 0, INFO: 1, WARN: 2, FAIL: 3}


@dataclass
class Check:
    id: str
    level: str
    message: str
    fix: str = ""
    card: str = ""

    def to_dict(self):
        return asdict(self)


def read(path, default=None):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return default


def run(cmd, timeout=5):
    if not shutil.which(cmd[0]):
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _governor():
    vals = {read(p) for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor")}
    vals.discard(None)
    if not vals:
        return Check("linux.governor", INFO, "No cpufreq interface exposed (common on VMs); frequency isn't under your control here.", card="linux.governor")
    if vals == {"performance"}:
        return Check("linux.governor", OK, "All CPUs use the performance governor.", card="linux.governor")
    return Check("linux.governor", WARN, f"Governor(s): {', '.join(sorted(vals))}.", "sudo cpupower frequency-set --governor performance", "linux.governor")


def _turbo():
    no_turbo = read("/sys/devices/system/cpu/intel_pstate/no_turbo")
    boost = read("/sys/devices/system/cpu/cpufreq/boost") or read("/sys/devices/system/cpu/cpu0/cpufreq/boost")
    if boost is None and read("/sys/devices/system/cpu/amd_pstate/cpb_boost") is not None:
        boost = read("/sys/devices/system/cpu/amd_pstate/cpb_boost")
    fix = "echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo" if no_turbo is not None else "echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost"
    on = no_turbo == "0" or boost == "1"
    off = no_turbo == "1" or boost == "0"
    if on:
        return Check("linux.turbo", WARN, "Turbo/boost is on. Fine for production-like numbers; disable for tight comparisons.", fix, "linux.turbo")
    if off:
        return Check("linux.turbo", OK, "Turbo/boost is off.", card="linux.turbo")
    return Check("linux.turbo", INFO, "Turbo state not exposed.", card="linux.turbo")


def _smt():
    active = read("/sys/devices/system/cpu/smt/active")
    if active == "1":
        return Check("linux.smt", INFO, "SMT is on. Pin away from siblings, or disable it for tight comparisons.", "echo off | sudo tee /sys/devices/system/cpu/smt/control", "linux.smt")
    if active == "0":
        return Check("linux.smt", OK, "SMT is off.", card="linux.smt")
    return Check("linux.smt", INFO, "SMT state not exposed.", card="linux.smt")


def _aslr():
    v = read("/proc/sys/kernel/randomize_va_space")
    label = {"0": "off", "1": "conservative", "2": "full"}.get(v, "unknown")
    return Check("linux.aslr", INFO, f"ASLR is {label}. Off suits chasing a tiny diff in one binary; on with many processes suits claims.", "setarch $(uname -m) -R ./bench", "linux.aslr")


def _clocksource():
    v = read("/sys/devices/system/clocksource/clocksource0/current_clocksource")
    if v is None:
        return Check("linux.clocksource", INFO, "Clock source not exposed.", card="linux.clocksource")
    if v in ("hpet", "acpi_pm", "xen"):
        return Check("linux.clocksource", WARN, f"Clock source is {v}; timer reads can be slow enough to perturb tight loops.", card="linux.clocksource")
    return Check("linux.clocksource", OK, f"Clock source is {v}.", card="linux.clocksource")


def _thp():
    v = read("/sys/kernel/mm/transparent_hugepage/enabled")
    if v is None:
        return Check("linux.thp", INFO, "THP state not exposed.", card="linux.thp")
    mode = v[v.find("[") + 1:v.find("]")] if "[" in v else v
    return Check("linux.thp", INFO, f"Transparent huge pages: {mode}. Keep it the same across compared runs.", card="linux.thp")


def _swap():
    v = read("/proc/swaps")
    if v is None:
        return Check("linux.swap", INFO, "Swap state not exposed.", card="linux.swap")
    n = max(len(v.splitlines()) - 1, 0)
    if n:
        return Check("linux.swap", WARN, f"{n} swap device(s) active.", "sudo swapoff -a  # or confirm vmstat si/so stay 0", "linux.swap")
    return Check("linux.swap", OK, "No active swap.", card="linux.swap")


def _load():
    try:
        load = os.getloadavg()[0]
    except OSError:
        return Check("common.load", INFO, "Load average unavailable.", card="method.active")
    n = os.cpu_count() or 1
    if load / n > 0.5:
        return Check("common.load", FAIL, f"1-minute load is {load:.2f} on {n} CPUs: this machine is busy.", "Stop other work and re-run.", "method.active")
    if load / n > 0.1:
        return Check("common.load", WARN, f"1-minute load is {load:.2f} on {n} CPUs.", "Stop background work.", "method.active")
    return Check("common.load", OK, f"1-minute load is {load:.2f} on {n} CPUs.", card="method.active")


def _mitigations():
    files = glob.glob("/sys/devices/system/cpu/vulnerabilities/*")
    if not files:
        return Check("linux.mitigations", INFO, "Mitigation state not exposed.", card="linux.mitigations")
    vul = sum(1 for f in files if (read(f) or "").startswith("Vulnerable"))
    return Check("linux.mitigations", INFO, f"{len(files)} vulnerability entries, {vul} reported as vulnerable. Captured for comparison.", card="linux.mitigations")


def _cstates():
    names = [read(p) for p in sorted(glob.glob("/sys/devices/system/cpu/cpu0/cpuidle/state*/name"))]
    names = [n for n in names if n]
    if not names:
        return Check("linux.cstates", INFO, "CPU idle states not exposed (common on VMs).", card="linux.cstates")
    return Check("linux.cstates", INFO, f"CPU idle states: {', '.join(names)}. Deep states can add wake-up latency.", card="linux.cstates")


def _isolation():
    iso = read("/sys/devices/system/cpu/isolated") or ""
    if iso:
        return Check("linux.isolation", OK, f"Isolated CPUs: {iso}. Pin the benchmark to them.", card="linux.isolation")
    return Check("linux.isolation", INFO, "No isolated CPUs. Pinning helps; isolation matters most for tail latency.", "taskset -c N ./bench", "linux.isolation")


def _numa():
    nodes = glob.glob("/sys/devices/system/node/node[0-9]*")
    if len(nodes) > 1:
        return Check("linux.numa", WARN, f"{len(nodes)} NUMA nodes. Unpinned runs may mix local and remote memory.", "numactl --cpunodebind=0 --membind=0 ./bench", "linux.numa")
    return Check("linux.numa", OK, f"{max(len(nodes), 1)} NUMA node.", card="linux.numa")


def _perf_access():
    v = read("/proc/sys/kernel/perf_event_paranoid")
    if v is None:
        return Check("linux.perf_access", INFO, "perf_event isn't available here.", card="linux.perf-access")
    try:
        if int(v) > 2:
            return Check("linux.perf_access", INFO, f"perf_event_paranoid={v}: unprivileged perf is blocked on kernels patched for this level (e.g. Debian, Android).", "sudo sysctl kernel.perf_event_paranoid=1", "linux.perf-access")
    except ValueError:
        pass
    # Arm and hybrid core PMUs have other names, but core PMUs expose a `cpus` file.
    if not os.path.exists("/sys/bus/event_source/devices/cpu") and not glob.glob("/sys/bus/event_source/devices/*/cpus"):
        return Check("linux.perf_access", INFO, f"perf_event_paranoid={v}, but no hardware PMU is exposed: no cycle or cache counters.", card="linux.perf-access")
    return Check("linux.perf_access", OK, f"perf_event_paranoid={v}; hardware PMU exposed.", card="linux.perf-access")


def _power():
    supplies = glob.glob("/sys/class/power_supply/*")
    mains = [s for s in supplies if read(os.path.join(s, "type")) == "Mains"]
    if mains and all(read(os.path.join(s, "online")) == "0" for s in mains):
        return Check("linux.power", FAIL, "Running on battery.", "Plug in.", "linux.power")
    return Check("linux.power", OK, "On AC power or no battery present.", card="linux.power")


def throttle_total():
    total = 0
    for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/thermal_throttle/core_throttle_count"):
        try:
            total += int(read(p, "0"))
        except ValueError:
            pass
    return total


def _thermal():
    paths = glob.glob("/sys/devices/system/cpu/cpu[0-9]*/thermal_throttle/core_throttle_count")
    if not paths:
        return Check("linux.thermal", INFO, "Thermal throttle counters not exposed.", card="linux.thermal")
    return Check("linux.thermal", INFO, f"Thermal throttle events since boot: {throttle_total()}. `benchsane ab` compares before and after.", card="linux.thermal")


def _virt():
    cpuinfo = read("/proc/cpuinfo") or ""
    # The cpuinfo flag is x86 only, so ask systemd too. It exits non-zero when there's no VM.
    name = run(["systemd-detect-virt", "--vm"])
    if " hypervisor" in cpuinfo or (name and name != "none"):
        return Check("linux.virt", WARN, f"Virtualized ({name or 'hypervisor flag set'}). Compare with interleaving and name the instance type on any number.", card="virt.vm")
    return Check("linux.virt", OK, "No hypervisor flag.", card="virt.vm")


def _cgroup_path():
    """This process's cgroup v2 path, or '' if unknown or at the root."""
    for line in (read("/proc/self/cgroup") or "").splitlines():
        if line.startswith("0::"):
            return line[3:].strip("/")
    return ""


def cgroup_cpu_limit():
    """Tightest CPU quota on this cgroup or an ancestor. cpu.max doesn't exist at the root."""
    limits = []
    parts = [p for p in _cgroup_path().split("/") if p and p != ".."]
    for depth in range(len(parts), -1, -1):
        v = read(os.path.join("/sys/fs/cgroup", *parts[:depth], "cpu.max"))
        if v and not v.startswith("max"):
            try:
                quota, period = v.split()
                limits.append(int(quota) / int(period))
            except ValueError:
                pass
    if limits:
        return min(limits)
    quota = read("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
    period = read("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    try:
        if quota and period and int(quota) > 0:
            return int(quota) / int(period)
    except ValueError:
        pass
    return None


def _container():
    inside = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv") or "KUBERNETES_SERVICE_HOST" in os.environ
    if inside:
        return Check("linux.container", WARN, "Inside a container: governor, turbo and SMT belong to the host. Run doctor on the host as well.", card="container.overhead")
    return Check("linux.container", OK, "No container markers found.", card="container.overhead")


def _cgroup():
    limit = cgroup_cpu_limit()
    if limit is not None:
        return Check("linux.cgroup", WARN, f"CPU quota of {limit:.2f} CPUs: bursts can be throttled, which shows up in tail latency.", "Prefer cpusets, or watch nr_throttled in cpu.stat.", "linux.cgroups")
    return Check("linux.cgroup", OK, "No CPU quota set.", card="linux.cgroups")


def _gpu():
    q = None
    for reasons in ("clocks_event_reasons.active", "clocks_throttle_reasons.active"):  # Newer name first.
        q = run(["nvidia-smi", f"--query-gpu=name,persistence_mode,pstate,{reasons},pcie.link.width.current,pcie.link.width.max", "--format=csv,noheader"], timeout=10)
        if q:
            break
    if not q:
        return None
    checks = []
    for i, line in enumerate(q.splitlines()):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            checks.append(Check("gpu.nvidia", INFO, f"GPU {i}: {line}", card="gpu.state"))
            continue
        name, persist, pstate, throttle, width, width_max = parts[:6]
        problems = []
        if persist.lower() != "enabled":
            problems.append("persistence mode off")
        if throttle not in ("0x0000000000000000", "0x0000000000000001", "[N/A]", "[Not Supported]"):
            problems.append(f"throttle reasons {throttle}")
        if width.isdigit() and width_max.isdigit() and int(width) < int(width_max):
            problems.append(f"PCIe x{width} of x{width_max} (may be idle downshift; recheck under load)")
        if problems:
            checks.append(Check("gpu.nvidia", WARN, f"GPU {i} {name}, {pstate}: " + "; ".join(problems) + ".", "sudo nvidia-smi -pm 1", "gpu.state"))
        else:
            checks.append(Check("gpu.nvidia", OK, f"GPU {i} {name}, {pstate}.", card="gpu.state"))
    return checks


def _darwin_checks():
    out = [Check("macos.host", WARN, "macOS has no pinning, governor or isolation controls. Use for relative comparisons; capture numbers others will quote on a named Linux host.", card="macos.limits")]
    translated = run(["sysctl", "-n", "sysctl.proc_translated"])
    if translated == "1":
        out.append(Check("macos.rosetta", FAIL, "This process runs under Rosetta. Native claims are invalid.", "Use an arm64 Python and arm64 binaries.", "macos.rosetta"))
    else:
        out.append(Check("macos.rosetta", OK, "Not running under Rosetta.", card="macos.rosetta"))
    pm = run(["pmset", "-g"]) or ""
    batt = run(["pmset", "-g", "batt"]) or ""
    if "Battery Power" in batt:
        out.append(Check("macos.power", FAIL, "Running on battery.", "Plug in.", "macos.lowpower"))
    elif any(l.split()[:2] == ["lowpowermode", "1"] for l in pm.splitlines()):
        out.append(Check("macos.power", FAIL, "Low Power Mode is on.", "Turn it off.", "macos.lowpower"))
    else:
        out.append(Check("macos.power", OK, "On AC power, Low Power Mode off.", card="macos.lowpower"))
    return out


RISKY_ENV = ("LD_PRELOAD", "DYLD_INSERT_LIBRARIES", "ASAN_OPTIONS", "TSAN_OPTIONS", "UBSAN_OPTIONS", "MALLOC_CONF", "PYTHONDEVMODE", "PYTHONMALLOC", "PYTHONTRACEMALLOC", "RUSTFLAGS", "CARGO_PROFILE_RELEASE_DEBUG")


def _env():
    found = [k for k in RISKY_ENV if k in os.environ]
    if found:
        return Check("common.env", WARN, "Performance-affecting variables are set: " + ", ".join(found) + ".", "Unset them, or record why they're set.", "build.identity")
    return Check("common.env", OK, "No known performance-affecting variables set.", card="build.identity")


def _git():
    if not run(["git", "rev-parse", "--is-inside-work-tree"]):
        return Check("common.git", INFO, "Not in a git repo: you'll need another way to identify the code.", card="build.identity")
    dirty = run(["git", "status", "--porcelain"])
    if dirty:
        return Check("common.git", WARN, "Working tree has uncommitted changes, so this run can't be tied to a commit.", "Commit first.", "build.identity")
    return Check("common.git", OK, "Working tree is clean.", card="build.identity")


def run_checks():
    system = platform.system()
    checks = [_load(), _env(), _git()]
    if system == "Linux":
        for fn in (_governor, _turbo, _smt, _aslr, _clocksource, _thp, _swap, _mitigations, _cstates, _isolation, _numa, _perf_access, _power, _thermal, _virt, _container, _cgroup):
            checks.append(fn())
    elif system == "Darwin":
        checks.extend(_darwin_checks())
    else:
        checks.append(Check("windows.host" if system == "Windows" else "common.platform", WARN, f"benchsane has minimal checks for {system}; a clean result here proves little.", card="windows.basics"))
    gpu = _gpu()
    if gpu:
        checks.extend(gpu)
    return checks


def grade(checks):
    """smoke: don't quote. caveated: compare on this host, disclose. clean: controlled."""
    worst = max((ORDER[c.level] for c in checks), default=0)
    return {3: "smoke", 2: "caveated"}.get(worst, "clean")


GRADE_MEANING = {
    "clean": "Controlled host. Numbers are usable with the host named.",
    "caveated": "Same-host comparisons are fine. Disclose the warnings on any number you quote.",
    "smoke": "Don't quote numbers from this state. Fix the failures first.",
}


def report(checks):
    g = grade(checks)
    return {"schema": formats.SCHEMA_DOCTOR, "tool": formats.tool(), "created_at": formats.now(), "grade": g,
            "meaning": GRADE_MEANING[g], "checks": [c.to_dict() for c in checks]}
