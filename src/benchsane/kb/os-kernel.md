# OS and kernel

## linux.governor — CPU frequency governor
tags: linux, kernel, cpu
check: linux.governor
status: cited
source: https://rocm.docs.amd.com/projects/llvm-project/en/docs-7.14.1/LLVM/llvm/html/Benchmarking.html

Use `performance` for comparisons: `for i in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $i; done` or `cpupower frequency-set --governor performance`. Ondemand-style governors add ramp-up time that dominates short benchmarks. Many VMs don't expose cpufreq at all; then this isn't under your control. Record it.

## linux.turbo — Turbo and boost
tags: linux, kernel, cpu
check: linux.turbo
status: cited
source: https://boringssl.googlesource.com/boringssl/+/HEAD/third_party/benchmark/docs/reducing_variance.md https://googlers.googlesource.com/maze/linux/+/v3.14/Documentation/cpu-freq/intel-pstate.txt

Boost can vary frequency even under the performance governor, depending on temperature, active cores and instruction mix. Intel: `echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo`. Generic: `echo 0 > /sys/devices/system/cpu/cpufreq/boost`. Note that no_turbo inverts the logic. AMD pstate systems may use `cpuN/cpufreq/boost` or `amd_pstate/cpb_boost`. Our advice: disable it for comparisons, and keep it for numbers meant to represent production.

## linux.smt — Hyperthreading / SMT
tags: linux, kernel, cpu
check: linux.smt
status: cited
source: https://rocm.docs.amd.com/projects/llvm-project/en/docs-7.14.1/LLVM/llvm/html/Benchmarking.html https://lkml.iu.edu/hypermail/linux/kernel/1808.1/04236.html

A sibling thread shares execution resources and caches. Offline siblings (`thread_siblings_list`, then `echo 0 > cpuN/online`) or use `/sys/devices/system/cpu/smt/control`. A cloud vCPU may be one hyperthread (see `cpu.vcpu`). Scaling numbers must state physical cores vs threads. For when to turn it off, see `cpu.smt-choice`.

## linux.aslr — ASLR: the tools disagree for a reason
tags: linux, kernel, layout, bias
check: linux.aslr
status: cited
source: https://boringssl.googlesource.com/boringssl/+/HEAD/third_party/benchmark/docs/reducing_variance.md

Google Benchmark and LLVM say to disable it (`setarch $(uname -m) -R ./bench`, or `echo 0 > /proc/sys/kernel/randomize_va_space`) for lower noise in one process. Disabling freezes you into one layout, which can be biased; with it enabled and many processes, you sample layouts (Stinner's notes tentatively lean this way). So: off when chasing a tiny regression in a single binary; on with many process runs when making a claim. `personality(2)` may be blocked by seccomp in Docker, so `MaybeReenterWithoutASLR` may not work there: confirm that it took effect. Restore the setting afterward: it's a security feature.

## linux.clocksource — Clock source
tags: linux, kernel, timing
check: linux.clocksource
status: unverified

Check `/sys/devices/system/clocksource/clocksource0/current_clocksource`. `tsc` gives fast vDSO `clock_gettime`. `hpet` and `acpi_pm` force slow reads that can perturb tight loops; `xen` can be slow too, and `kvm-clock` is usually fine. The kernel can switch away from TSC if it decides it's unstable: check dmesg. Use a monotonic clock, not wall clock, and measure your timer's overhead.

## linux.thp — Transparent huge pages
tags: linux, kernel, memory
check: linux.thp
status: unverified

`/sys/kernel/mm/transparent_hugepage/enabled` (and `defrag`) can change results a lot for memory-heavy work, and khugepaged adds latency spikes. Results also change as memory fragments over uptime. Match production, record it, and consider a reboot before a final run.

## linux.swap — Swap and memory pressure
tags: linux, kernel, memory
check: linux.swap
status: unverified

Active swap adds huge outliers. Check `/proc/swaps`, `vmstat 1` (si/so), and PSI in `/proc/pressure/memory`. Turn it off for controlled runs or confirm that nothing swapped in the window.

## linux.isolation — Isolating CPUs
tags: linux, kernel, cpu, latency
check: linux.isolation
status: unverified
source: https://vstinner.readthedocs.io/benchmark.html

Boot with `isolcpus=<list> rcu_nocbs=<list>` (optionally `nohz_full=<list>`), then pin with `taskset`. LLVM uses `cset shield -c N1,N2 -k on` at runtime. The default `domain` flag of isolcpus turns off scheduler balancing, so a multi-threaded process pinned to several isolated CPUs can pile onto one unless each thread is pinned; `isolcpus=managed_irq,<list>` keeps balancing. Keep a housekeeping core, and leave a free core for `perf`.

## linux.irq — IRQ and softirq placement
tags: linux, kernel, network, latency
status: unverified

Interrupts landing on your benchmark core produce latency spikes. Check `/proc/interrupts` and `/proc/softirqs`. Set `/proc/irq/*/smp_affinity`, watch out for `irqbalance` undoing it, and keep NIC IRQs on the same NUMA node as the workload.

## linux.mitigations — CPU vulnerability mitigations
tags: linux, kernel, cpu, security
check: linux.mitigations
status: unverified

`/sys/devices/system/cpu/vulnerabilities/*` and the kernel command line (`mitigations=off`). Syscall- and context-switch-heavy workloads are most affected. Compare with them on unless you are specifically studying them; different kernels and microcode mean different mitigations.

## linux.cgroups — CPU quota throttling
tags: linux, kernel, container
check: linux.cgroup
status: unverified

CFS bandwidth limits (`cpu.max`) throttle bursts, causing p99 stalls even at low average usage. Check `nr_throttled` in `cpu.stat`. Prefer cpusets for benchmarking, or report the limit.

## linux.page-cache — Page cache state
tags: linux, kernel, storage
status: unverified
source: https://www.mankier.com/1/hyperfine

First-run vs later-run timings can differ by orders of magnitude. Decide whether you measure cold or warm, and do it consistently. Cold: `sync; echo 3 > /proc/sys/vm/drop_caches` (root). Warm: pre-read inputs and discard one run. Hyperfine's `--prepare` and `--warmup` are built for this. Dirty-page writeback (`vm.dirty_*`) can bill work to a later run.

## linux.numa — NUMA placement
tags: linux, kernel, memory, numa
check: linux.numa
status: unverified

Remote memory is slower and has lower bandwidth, and first-touch determines placement. Run `numactl --hardware`, pin with `numactl --cpunodebind=N --membind=N`, and watch `numastat`. Automatic balancing (`kernel.numa_balancing`) adds migrations mid-run. AMD SNC/NPS BIOS modes change the topology a lot, so record them.

## linux.perf-access — Perf permissions and overhead
tags: linux, kernel, profiling
check: linux.perf_access
status: unverified

`/proc/sys/kernel/perf_event_paranoid` controls access; a level above 2 blocks unprivileged use only on kernels patched for it, such as Debian and Android. Too many events multiplex counters: look for the percent column in `perf stat` and reduce the event set. `perf record` perturbs the workload, so don't take timing and profile from the same run. `perf_event_max_sample_rate` auto-lowers under load.

## linux.scheduler — Kernel version and scheduler
tags: linux, kernel
status: unverified
source: https://kernel.org/doc/html/v6.15/_sources/scheduler/sched-eevdf.rst.txt

Kernel upgrades change the scheduler (EEVDF replaced CFS in 6.6), I/O paths, mitigations and defaults. Record the full version, distro patches, `/proc/cmdline`, and `sysctl -a` for a final run. Don't compare across kernels unless the kernel is the variable.

## linux.power — AC power
tags: linux, kernel, laptop
check: linux.power
status: unverified

Battery operation changes power limits and frequency. Check `/sys/class/power_supply/*/online`. Laptops also throttle thermally during longer runs and on hot surfaces.

## linux.thermal — Thermal throttling
tags: linux, kernel, cpu, thermal
check: linux.thermal
status: unverified

`/sys/devices/system/cpu/cpu*/thermal_throttle/core_throttle_count` is a cumulative counter on Intel. Compare it before and after a run; `benchsane ab` does. Frequency and throttle state are also available via `turbostat`. Check server room/room temperature, since Mytkowicz-era lore isn't the only reason results shift by time of day.

## macos.limits — macOS can't be tuned like Linux
tags: macos, apple, laptop
check: macos.host
status: unverified

No CPU pinning API, no governor, no isolcpus, P and E cores with QoS-driven placement, and thermal behavior specific to each chassis (fanless vs fan differ sharply). Good for relative dev feedback; for numbers others will quote, use a Linux host or say plainly "M-series laptop". Use `taskpolicy`, stay on AC power, close Spotlight/backup activity, and use Instruments or `powermetrics` for insight.

## macos.rosetta — Rosetta invalidates native claims
tags: macos, apple
check: macos.rosetta
status: unverified
source: https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment.md

An x86_64 process on Apple Silicon runs under translation. Check with `sysctl sysctl.proc_translated` and `file ./binary`. Python, Node, Homebrew under `/usr/local`, and Docker `--platform linux/amd64` are the common accidental cases.

## macos.lowpower — Low Power Mode and battery
tags: macos, apple, laptop
check: macos.power
status: unverified

Check `pmset -g | grep lowpowermode` and `pmset -g batt`. Low Power Mode caps performance. Stay on AC.

## windows.basics — Windows
tags: windows
check: windows.host
status: unverified

Use the High performance power plan (`powercfg /l`), `QueryPerformanceCounter` for timing, and exclude your paths from Defender real-time scanning, which can dominate file I/O. Set affinity with `start /affinity`, and use WPR/WPA with ETW for analysis. benchsane's Windows checks are minimal, so don't take a clean doctor run as evidence.

## windows.wsl — WSL2 is a VM
tags: windows, wsl, virtualization
status: unverified

WSL2 runs a Linux kernel in a lightweight VM. File I/O across the `/mnt/c` boundary is much slower than the Linux file system. Treat results as virtualized, and report them as such.

## linux.cstates — CPU idle states
tags: linux, kernel, cpu, latency
check: linux.cstates
status: cited
source: https://access.redhat.com/articles/65410

Waking from a deep C-state can take hundreds of microseconds to milliseconds, which shows up in tail latency and in anything that sleeps between requests. To test whether it's your problem, boot with `processor.max_cstate=1 idle=poll`, or hold `/dev/cpu_dma_latency` open with a value of 0 for the length of the run, which limits the change to that window. Both raise power use and heat, so they're for diagnosis and for measured low-latency setups rather than as defaults. List states with `cpupower idle-info` or `/sys/devices/system/cpu/cpu0/cpuidle/`. A CPU-bound benchmark that never idles is rarely affected, and a server benchmark at low load often is.
