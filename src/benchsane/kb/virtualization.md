# Virtualization, cloud and CI

## virt.vm — What a VM takes away
tags: virtualization, cloud
check: linux.virt
status: cited
source: https://brendangregg.com/Slides/IntelON2021_ProcessorBenchmarking

Hypervisors limit PMCs and PEBS, and you don't control frequency, turbo or neighbors. Watch steal time (`vmstat` st, `mpstat %steal`). You can compare on a VM with interleaving and more runs, but state the instance type and that it's virtualized. Where numbers must be absolute, prefer bare-metal instances.

## cloud.variance — Instance-to-instance variance
tags: cloud, virtualization
status: unverified

Two instances of one type can differ in CPU stepping, placement and neighbors. A single instance is one sample of the population: repeat across fresh instances if the claim is about the type. Record instance type, region and zone, AMI and date. Keep runs on one instance for A/B, in the same session.

## cloud.burst — Burst credits
tags: cloud, virtualization, storage, network
status: unverified
source: https://docs.aws.amazon.com/ebs/latest/userguide/general-purpose.html

Burstable instances (e.g. T-family), burst-credit volumes such as EBS gp2 (gp3 has a provisioned baseline instead) and bursting network limits give high early numbers, then a cliff. Use fixed-performance instances, or run past credit exhaustion and report both phases.

## container.overhead — Containers change the system under test
tags: container, linux
check: linux.container
status: unverified

Differences are usually due to configuration: CPU quotas (see `linux.cgroups`), overlayfs vs a volume for I/O, bridge networking vs host, seccomp filters on syscalls, memory limits including page cache. Runtimes that read host CPU count may oversize thread pools. Use `--network host`, volumes and cpusets when these aren't the subject, and don't run `--platform` emulation.

## container.seccomp — Tuning from inside a container usually fails
tags: container, linux
status: cited
source: https://boringssl.googlesource.com/boringssl/+/HEAD/third_party/benchmark/docs/reducing_variance.md

`personality(2)` for ASLR control may be blocked by default seccomp, and in our experience `/sys` is often read-only too. Governor, turbo and SMT belong to the host, so run doctor on the host as well.

## ci.noise — Shared CI runners are noisy
tags: ci, cloud
status: cited
source: https://github.com/bencherdev/bencher

Noisy shared CI runners hide real regressions, which is why continuous benchmarking tools push dedicated bare-metal runners. Choices: (a) self-hosted or bare-metal runner for time, (b) instruction-count or CPU simulation for determinism, or (c) running A and B interleaved on the same runner within one job to cancel out host differences.

## ci.instructions — Instruction counts are stable but partial
tags: ci, microbenchmark
status: cited
source: https://github.com/CodSpeedHQ/codspeed

CodSpeed's CPU simulation advertises under 1% variance independent of system load, making it good for catching regressions in CPU-bound code. Our reasoning, not CodSpeed's claim: as a model rather than wall time, it won't reflect scheduling, real contention, I/O or GPU work. Pair it with wall-clock measurement on real hardware before making a speed claim.

## ci.detection — Detect regressions over history
tags: ci, statistics
status: unverified
source: https://bencher.dev/docs/reference/prior-art/

Fixed percentage thresholds alert on noise and miss slow creep. Use statistical thresholds over history (Bencher) or change-point detection (Apache Otava). Confirm automatically by re-running suspect commits with their parent, interleaved, and pin the toolchain so regressions come from your code.
