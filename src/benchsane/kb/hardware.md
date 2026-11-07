# Hardware

## cpu.identity — Record the exact CPU, not the marketing name
tags: hardware, cpu
status: unverified

Model, stepping, microcode, sockets, physical cores, threads, base and max frequency, cache sizes, ISA levels and BIOS settings (power profile, SNC/NPS, prefetchers). The same cloud instance family or laptop name can hide different silicon.

## cpu.hetero — Heterogeneous cores
tags: hardware, cpu, apple, laptop, arm
status: cited
source: https://boringssl.googlesource.com/boringssl/+/HEAD/third_party/benchmark/docs/reducing_variance.md

Google Benchmark notes that not all CPUs run the same speed on multi-core machines. On hybrid Intel, Apple Silicon and big.LITTLE parts, a run that migrates between performance and efficiency cores becomes bimodal. Pin to one class where possible and check `lscpu -e`, or per-core capacity in `/sys/devices/system/cpu/cpu*/cpu_capacity`.

## cpu.vector-frequency — Wide vectors can change frequency
tags: hardware, cpu, simd
status: unverified

On some x86 parts, heavy AVX2/AVX-512 reduces clock, which can slow neighboring scalar code and sibling threads. A SIMD microbenchmark alone can overstate the gain. Test in the real application and check the frequency (`perf stat -e cycles,task-clock`, `turbostat`).

## cpu.cache-working-set — Working set decides what you measure
tags: hardware, cpu, memory, microbenchmark
status: cited
source: https://boringssl.googlesource.com/boringssl/+/HEAD/third_party/benchmark/docs/reducing_variance.md

A loop that fits in L1 measures different hardware from one that spills to DRAM. Sweep sizes across cache levels. Shrinking a benchmark to fit L1 reduces variance but, as Google Benchmark warns, may optimize for an unrealistic situation. Repeating the same data also trains the branch predictor and prefetchers; use realistic or shuffled inputs.

## cpu.counters — Interpret counters carefully
tags: hardware, cpu, profiling
status: cited
source: https://brendangregg.com/Slides/IntelON2021_ProcessorBenchmarking

Use `perf stat -d` for cycles, instructions, IPC and cache and branch misses as cross-checks: did your change reduce instructions but raise misses? Cycle analysis is hard in the cloud, as Gregg notes: limited PMCs under hypervisors and no PEBS. Multiplexed counters are estimates.

## cpu.timing — Timers and serialization
tags: hardware, cpu, timing, microbenchmark
status: unverified

Bare `rdtsc` isn't serializing: use `rdtscp` plus fence or `lfence; rdtsc`. Confirm `constant_tsc nonstop_tsc` in `/proc/cpuinfo`. TSC counts reference cycles, not core cycles. Arm has `cntvct_el0` at a usually lower frequency. For anything under a few hundred ns, batch operations and divide; timer overhead dominates.

## cpu.arm-x86 — ISA comparisons change more than speed
tags: hardware, cpu, arm, concurrency
status: unverified

x86 has a stronger memory model than Arm, so lock-free code can have very different costs and even hide bugs across ISAs. Compilers and libraries are not equally tuned, so check SIMD paths (does the library have NEON/SVE paths?). Compare by cost and energy as well as raw speed, and fix the build flags per ISA.

## cpu.scaling — Scaling tests need a real baseline
tags: hardware, cpu, concurrency, scaling
status: unverified

Beyond plotted speedup, compare with the best single-threaded implementation (the "COST" idea from McSherry et al.), because a parallel system can scale well simply by being slow. Mark where physical cores end and SMT begins. Fit Amdahl or USL only if you have enough points, and watch for the client saturating first.

## memory.config — Memory configuration
tags: hardware, memory
status: unverified

Record capacity, speed, channels populated, ECC, huge pages and allocator. One DIMM vs a full channel complement has large bandwidth effects. Bandwidth benchmarks (STREAM, Intel MLC) quickly detect misconfigured machines; run one on any machine you don't trust.

## memory.measure — Memory measurement traps
tags: hardware, memory, profiling
status: unverified

RSS isn't a total cost: use PSS for shared pages, peak for capacity, and track allocations per op for design work. `ru_maxrss` is KiB on Linux. On macOS it is widely reported as bytes, though Apple's man page says kilobytes; `benchsane ab` assumes bytes, so check this on your Mac. Cgroup accounting includes page cache. Allocators retain freed memory, and GC runtimes grow to fill the heap limit, so report heap settings.

## storage.traps — Storage benchmarks measure the cache by default
tags: hardware, storage
status: unverified

Use `fio` with `direct=1` unless the page cache is the subject. Report block size, queue depth, read/write mix, randomness, file size versus RAM, and fsync policy. A write that hasn't been fsynced isn't durable, so durability settings must match. Precondition SSDs: fresh drives show SLC-cache and clean-block performance that fades under sustained writes. Don't use zeros on compressing or deduplicating storage. Keep the file system and mount options in the record.

## storage.cloud — Cloud storage limits
tags: hardware, storage, cloud
status: unverified

Network volumes have provisioned and burst IOPS and throughput limits, and an instance-level cap. A snapshot-restored volume may lazy-load on first read. Check you're not simply measuring the limit, and run long enough to outlast burst credits. Instance-local NVMe is a separate device class.

## network.traps — Network benchmarks
tags: hardware, network
status: unverified
source: https://www.brendangregg.com/activebenchmarking.html

Loopback isn't a NIC: it skips the hardware and most of the stack. Client limits are a common failure: a single-threaded generator, or a saturated client, or a network throttle can be what you're measuring. Report MTU, RSS queues, offloads (`ethtool -k`), interrupt coalescing (`ethtool -c`), kernel, TCP congestion control, placement and RTT (`ping`). Use `iperf3` to verify capacity before application tests.

## network.cloud — Cloud network limits
tags: hardware, network, cloud
status: unverified
source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html

Instance bandwidth may be "up to" with bursts. Cloud NICs enforce per-flow, PPS and connection-tracking limits, so check driver counters (`ethtool -S`; on EC2 ENA, `*_allowance_exceeded`). Use a placement group or record the zones. Test with multiple flows to see where the limit is.

## gpu.state — GPU state to fix and record
tags: hardware, gpu, ml
check: gpu.nvidia
status: unverified
source: https://docs.nvidia.com/deploy/nvml-api/group__nvmlClocksEventReasons.html

Record model, count, VBIOS, driver, CUDA, framework and precision, power limit, clocks, ECC, persistence mode, MIG, PCIe link width and speed (a degraded link is a common cause of slow results), and topology (`nvidia-smi topo -m`). Log `clocks_event_reasons` (older drivers: `clocks_throttle_reasons`) and temperature during the run with DCGM or `nvidia-smi --query-gpu=... -l 1`. A sagging or throttling GPU isn't the performance of that GPU model.

## gpu.timing — GPU timing is asynchronous
tags: hardware, gpu, ml, timing
status: unverified
source: https://docs.pytorch.org/docs/main/generated/torch.cuda.Event.html

GPU work is queued: timing Python around a call measures enqueue unless you synchronize. In PyTorch call `torch.cuda.synchronize()` before reading the timer, or use `torch.cuda.Event`; synchronize itself can perturb pipelines, so don't synchronize inside production code paths you're measuring end to end. Exclude first-iteration costs (lazy init, shader or graph compile, allocation) and report them separately.

## gpu.utilization — GPU utilization isn't efficiency
tags: hardware, gpu, ml
status: unverified

`nvidia-smi` utilization means "a kernel was running during the sample", not that the GPU is doing useful work. Use throughput, SM activity, memory bandwidth and DCGM profiling metrics to identify limits, and check CPU data loading, which frequently limits "GPU" benchmarks.

## energy.measure — Energy and cost
tags: hardware, energy, cost
status: unverified
source: https://lkml.iu.edu/hypermail/linux/kernel/1311.3/02372.html

RAPL gives package and DRAM estimates on supported x86, accessed with `perf stat -a -e power/energy-pkg/` (RAPL events are system-wide), and access is commonly restricted. `nvidia-smi` gives GPU power; PDUs are the ground truth for a whole system. `powermetrics` is the option on macOS. Report work per joule or per dollar at a stated load, and report on-demand vs reserved pricing with a date.

## cpu.choose-isa — Arm, x86 or something else
tags: hardware, cpu, arm, x86, riscv, apple, cloud, cost
status: unverified

There's no general answer, so test your real workload on each candidate. Compare cost per unit of work at your latency target, not raw speed or a synthetic score. Before comparing, check whether your hot paths have tuned code for each ISA (SIMD in libraries, crypto, compression, BLAS), how mature the JIT or toolchain is, and whether every dependency has a native build. Never compare through emulation (Rosetta, QEMU, Docker `--platform`). Lock-free code also needs retesting, because Arm's weaker memory model changes both cost and correctness (see `cpu.arm-x86`). Intel and AMD differ too: cache topology and AVX-512 behavior can matter as much as ISA. RISC-V is worth testing only if you're targeting it, since compilers, libraries and available hardware are less mature. A GPU or other accelerator is a different question: measure the whole pipeline, including data transfer and the CPU work around it.

## cpu.vcpu — A vCPU isn't a fixed unit
tags: hardware, cpu, cloud, arm, x86, virtualization
status: cited
source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-optimize-cpu

On EC2, each thread is a vCPU, so an `m5.xlarge` has 2 cores and 4 vCPUs. Comparing "4 vCPU" instances across types can therefore compare 2 cores with 4. AWS lets you set one thread per core on many types, but not on T2, C7a, M7a, R7a, Apple silicon Mac or Graviton instances. Check with `lscpu` (`Thread(s) per core`) rather than assuming. Compare on equal cost or equal measured capacity, and state the thread and core counts.

## cpu.affinity — CPU affinity and pinning
tags: hardware, cpu, linux, numa, latency, concurrency
status: cited
source: https://www.mankier.com/2/sched_setaffinity

Pinning (`taskset -c 2,3 ./bench`) reduces migrations, and a child inherits the mask across fork and exec. Affinity is per thread, and the kernel can silently narrow it to what a cpuset allows, so verify the result with `taskset -cp <pid>` and `ps -eLo pid,tid,psr,comm`. Our advice beyond the man page: choose CPUs from the topology (`lscpu -e`, `lstopo`). Two threads on SMT siblings, on one L3 domain, and across sockets are three different experiments, especially for cross-thread communication. Avoid CPU 0, which often handles housekeeping and interrupts. Bind memory to the same node (`numactl --cpunodebind=N --membind=N`) and keep any load generator on separate cores. Pinning a process to one CPU makes runtime thread pools compete with each other, and JVM and Go runtimes may size themselves from the mask. Production usually doesn't pin, so a pinned result is a clean comparison rather than a capacity number. macOS has no equivalent.

## cpu.smt-choice — Should SMT be on?
tags: hardware, cpu, linux, cloud, concurrency
status: unverified

Off (or leaving siblings idle) gives steadier single-thread comparisons. For capacity numbers, match production. SMT usually adds some throughput per core, while latency-sensitive work can suffer when siblings compete, and the size of either effect depends on the workload, so measure it: run one thread per core first, then add the siblings. On a scaling plot, mark where physical cores run out. Don't quote per-"CPU" numbers without saying whether that means a core or a thread.

## cpu.bios — BIOS and firmware settings
tags: hardware, cpu, memory, numa
status: unverified

Power profile, prefetchers, sub-NUMA clustering (Intel SNC, AMD NPS), memory interleaving and SMT can all change results, and they're invisible to most tools. A server left on a balanced power profile can behave very differently from one set to performance. Record them for any machine you control. On cloud instances you can't see or change them, which is another reason to name the instance type.
