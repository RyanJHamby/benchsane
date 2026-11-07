# The framework

Run `benchsane kb show <id>` on any card named here. `*` means a family: `benchsane kb list` shows them all.

## The loop

| # | Step | Output | Cards |
|---|---|---|---|
| 1 | **Question.** Decision, workload, baseline, smallest effect that matters | `bench/PLAN.md` | `method.question` |
| 2 | **Mode.** Controlled comparison, or representative of production? | Stated in the plan | `method.representative` |
| 3 | **Host.** Check and fix the machine, then record it | `doctor`, `env.json` | `report.minimum` |
| 4 | **Noise floor.** A/A with the identical procedure | Smallest believable effect | `method.aa` |
| 5 | **Measure.** Fresh processes, interleaved, enough blocks | `samples.json` | `method.interleave`, `method.levels` |
| 6 | **Explain.** Watch it run; name the limiter | Notes in the report | `method.active` |
| 7 | **Attack it.** Layout, inputs, errors, physics, other machines | Survives or doesn't | `method.bias`, `method.gregg-checklist` |
| 8 | **Report.** Absolute and ratio, CI, n, host, commit, raw data. See [output formats](OUTPUT-FORMATS.md) | `report.md` | `report.minimum`, `report.crimes` |

## Pick the mode

| | Controlled | Representative |
|---|---|---|
| Question | Is B better than A? | What will production get? |
| Turbo, SMT | Off | As in production |
| Pinning | Yes | As in production |
| Noise | Low | Higher; add runs |
| Valid claim | A relative effect on this host | Absolute capacity or latency at stated load |

## Choosing hardware and settings

**Architecture (Arm, x86, others).** Test your real workload natively on each candidate, and compare cost per unit of work at your latency target. A vCPU isn't a fixed unit across instance types. See `cpu.choose-isa`, `cpu.vcpu` and `cpu.arm-x86`.

**Settings.** The right value depends on your mode, so there's no single best configuration. Whatever you choose, record it and keep it the same on both sides of a comparison.

| Setting | Clean comparison | Production-like number | Check | Cards |
|---|---|---|---|---|
| SMT / hyperthreading | Off, or leave siblings idle | Match production | `lscpu` | `cpu.smt-choice`, `linux.smt` |
| CPU affinity | Pin, chosen from the topology | Usually unpinned, as in production | `taskset -cp`, `lscpu -e` | `cpu.affinity` |
| CPU isolation | Isolate for tail-latency work | Match production | `/sys/devices/system/cpu/isolated` | `linux.isolation` |
| Governor | `performance` | Match production | `doctor` | `linux.governor` |
| Turbo / boost | Off | Match production | `doctor` | `linux.turbo` |
| C-states | Limit only if testing wake-up latency | Match production | `cpupower idle-info` | `linux.cstates` |
| ASLR | Off for a tiny diff in one binary; on with many processes for a claim | On | `doctor` | `linux.aslr` |
| Huge pages / THP | Same on both sides | Match production | `doctor` | `linux.thp` |
| NUMA | Bind CPU and memory to one node | Match production | `numactl --hardware` | `linux.numa` |
| IRQ placement | Away from benchmark cores | Match production | `/proc/interrupts` | `linux.irq` |
| Mitigations | Leave on, unless they're the subject | Match production | `doctor` | `linux.mitigations` |
| BIOS (power, prefetch, SNC/NPS) | Fix and record | Match production | Vendor tools | `cpu.bios` |
| CPU quota vs cpuset | Prefer cpuset | Match production | `doctor` | `linux.cgroups` |

`doctor` reports these, and `ab --cpus 2,3` pins a run on Linux. benchsane doesn't change any of them for you.

## The configuration matrix

Capture everything in the right-hand columns. `capture` automates the rows marked ●; the others are for you to record in the plan.

| Layer | Must record | Auto | Changes results via | Cards |
|---|---|---|---|---|
| **Code** | Commit, dirty state, dependency lock, binary hash | ● commit, dirty | Everything | `build.identity` |
| **Language runtime** | Version, GC, JIT tier, interpreter build, thread settings | ● versions | Warmup, GC, inlining | `lang.*`, `stats.warmup` |
| **Compiler** | Exact version, all flags, LTO, PGO/BOLT profile, `-march`, hardening | ● version | Codegen, layout | `build.*` |
| **Libraries** | libc, allocator, BLAS, CUDA, libstdc++ vs libc++ | | Allocation, math speed | `lang.c-cpp`, `lang.python` |
| **Environment** | Env size and tuning variables, cwd, locale | ● | Stack alignment, behavior | `method.bias` |
| **OS** | Distro, version, background services | ● distro | Scheduling, I/O | `macos.*`, `windows.*` |
| **Kernel** | Version, cmdline, scheduler, mitigations | ● | Syscall cost, scheduling | `linux.scheduler`, `linux.mitigations` |
| **Kernel tuning** | Governor, turbo, C-states, SMT, ASLR, THP, swap, isolation, NUMA balancing, clocksource | ● via doctor | Frequency, memory, timers | `linux.*` |
| **CPU** | ISA, model, stepping, microcode, sockets, cores vs threads, affinity, caches, ISA flags, BIOS | ● except stepping and BIOS | IPC, frequency, topology | `cpu.*` |
| **Memory** | Capacity, speed, channels, NUMA nodes, huge pages | ● capacity, nodes | Bandwidth, latency | `memory.*`, `linux.numa` |
| **Storage** | Device, file system, mount options, block size, queue depth, durability | | Caches, tail latency | `storage.*`, `linux.page-cache` |
| **Network** | NIC, driver, MTU, offloads, queues, placement, RTT | | Throughput, tail, limits | `network.*`, `linux.irq` |
| **GPU** | Model, driver, CUDA, framework, power limit, clocks, ECC, PCIe, topology | ● model, driver, limit | Throughput, throttling | `gpu.*` |
| **Virtualization** | Instance type, region and zone, image, hypervisor | ● partly | Steal, PMU, burst | `virt.vm`, `cloud.*` |
| **Container** | Image digest, CPU quota vs cpuset, memory limit, network mode, storage driver | ● markers, quota | Throttling, I/O | `container.*`, `linux.cgroups` |
| **Physical** | AC or battery, chassis, ambient temperature, time | ● power on Linux and macOS | Throttling | `linux.power`, `linux.thermal` |
| **Workload** | Input data, size, distribution, load model, offered rate, duration | | The whole answer | `latency.*`, `micro.scope`, `ml.*` |
| **Harness** | Tool, version, reps, warmup, what one sample means, order, seed | ● for `ab` | Statistics | `stats.*` |

## Picking by workload

| You're measuring | Tool | Report | Main trap | Cards |
|---|---|---|---|---|
| A function | Language harness | Median time, allocations | Dead-code elimination, unrealistic input | `micro.*`, `lang.*` |
| A CLI or batch job | `ab`, hyperfine | Median wall, CPU, RSS | Startup dominates; page cache | `startup.cold`, `linux.page-cache` |
| A service | k6, wrk2 | Percentiles at offered rate; errors; the knee | Coordinated omission; saturated client | `latency.*` |
| Storage | fio | IOPS, bandwidth, latency at QD and block size | Page cache; unconditioned SSD; burst | `storage.*` |
| Network | iperf3, netperf | Throughput, RTT, retransmits | Loopback; per-flow limits | `network.*` |
| Memory | STREAM, MLC, allocation counts | Bandwidth, latency, PSS | NUMA; RSS isn't cost | `memory.*`, `linux.numa` |
| A database | sysbench, YCSB, pgbench | Throughput and tail at stated durability | Fits in RAM; unequal durability | `database.traps` |
| LLM serving | GuideLLM, AIPerf | TTFT, ITL, goodput under SLO | No prompt length; closed loop | `ml.inference` |
| Voice or streaming | Real-time stream replay | Time to first audio, RTF, jitter | Faster-than-real-time input | `ml.realtime-audio` |
| Training | Framework profiler, DCGM | Time to accuracy, step breakdown | Async GPU timing; synthetic data | `ml.training`, `gpu.timing`, `distributed.training` |
| Hardware or cloud type | PKB, Phoronix, your workload | Per-workload results, cost and energy | One instance; burst credits | `cloud.*`, `energy.measure` |

## Two-minute checks

1. Did it exit 0, and is the output correct?
2. Is the result possible? Compare it with hardware limits.
3. Is the machine idle before you start? (`uptime`)
4. Did you run the optimized build?
5. Does doubling the work double the time? If not, something was optimized away or is limiting.
6. Does A vs A show no difference?
7. Does injecting a known slowdown get detected? (`sleep`, or a known-slow path.) If not, your rig can't see the effects you care about.
8. Is your measurement overhead small? Run with and without the timer or profiler.
9. Is one sample really independent of the last?
10. Could anything except your change differ? Diff `env.json`.

## How the pieces fit

```text
           cards (src/benchsane/kb/*.md) + your private overlay
                                 |
      +--------------+-----------+------------+
      |              |                        |
    CLI          Agent Skill            MCP server (read-only)
   people       workflow, loads         for clients with no shell
                  on demand
      |              |                        |
      +--- doctor, capture, ab, compare ------+
                     |
       your project: bench/PLAN.md, bench/runs/<date>-<name>/
```

**Why cards and one package.** One source of truth prevents the KB, checks and agent instructions from drifting apart. Tests make each `doctor` finding resolve to a card.

**Why the Skill comes first and MCP second.** A Skill's metadata costs [around 100 tokens until triggered](https://www.developersdigest.tech/blog/mcp-servers-vs-agent-skills-2026), while MCP schemas are [often loaded up front](https://parallel.ai/articles/mcp-vs-skills-vs-clis). The workflow is instructions plus a CLI, which suits a Skill. MCP remains for clients without a shell, or for a remote host you want to check.

**Why `doctor` never fixes anything.** Disabling ASLR or changing governors on a shared or work machine is a real change with security and fleet implications, and it isn't always right for the question at hand. `pyperf system tune` exists for people who want this.

**Why `ab` is small.** Its only reasons to exist are fresh processes, randomized interleaving, pairing, A/A and capture. Anything fancier belongs to the tools in [EXISTING-TOOLS](EXISTING-TOOLS.md).
