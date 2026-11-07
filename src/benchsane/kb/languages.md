# Languages and runtimes

## lang.c-cpp — C/C++ microbenchmarks
tags: c, cpp, microbenchmark
status: unverified

Use Google Benchmark with `benchmark::DoNotOptimize` and `ClobberMemory`, otherwise results may be folded or eliminated; check the disassembly. Build with `-O2/-O3 -DNDEBUG`: CMake with no build type adds no optimization flags. Remove sanitizers and `-D_GLIBCXX_DEBUG`. Record libc, libstdc++/libc++ and allocator (glibc malloc, jemalloc, tcmalloc and mimalloc behave differently). Prevent `-ffast-math` from being inherited unintentionally.

## lang.rust — Rust
tags: rust, microbenchmark
status: unverified

Measure `--release` only, and record `lto`, `codegen-units`, `panic`, `opt-level`, `debug-assertions`, `overflow-checks`, and `RUSTFLAGS` (`-C target-cpu`). Use criterion or divan with `std::hint::black_box`, which is documented as best-effort, so confirm it worked. Record `rustc -vV` and the global allocator. `Cargo.lock` must be committed for a reproducible run.

## lang.go — Go
tags: go, microbenchmark
status: unverified
source: https://tip.golang.org/doc/go1.25 https://go.googlesource.com/website/+show/HEAD/_content/blog/testing-b-loop.md

Use `go test -bench . -benchmem -count=10` (or higher) and compare with `benchstat`. Prefer `b.Loop()` (Go 1.24+), which resists dead-code elimination, over manual `b.N` loops. Record `GOMAXPROCS` (respects Linux cgroup CPU limits by default from Go 1.25, unless set manually or an older `go` line in go.mod keeps the old default), `GOGC`, `GOMEMLIMIT`, `GOAMD64`, and whether a `default.pgo` was picked up. Don't measure with `-race`. Allocation counts are often a more stable signal than time.

## lang.jvm — JVM (Java, Kotlin, Scala)
tags: java, jvm, jit, microbenchmark
status: unverified

Use JMH, as hand-rolled loops are wrong in many ways (OSR, dead code, constant folding, profile pollution). Keep multiple forks (each is a fresh JIT outcome), consume results via `Blackhole`, and read JMH's warnings. Record JDK vendor and version, GC, `-Xms/-Xmx` (equal for benchmarking), `-XX:+AlwaysPreTouch`, tiered compilation settings, and CPU limits, which affect GC and JIT thread ergonomics. For profiling, prefer async-profiler: safepoint-biased profilers mislead.

## lang.python — Python
tags: python, microbenchmark
status: cited
source: https://pyperf.readthedocs.io/en/latest/run_benchmark.html https://docs.python.org/3/_sources/library/timeit.rst.txt

Use pyperf: it spawns multiple processes, records metadata, checks stability, and `compare_to` tests significance. Record the interpreter build (PGO/LTO matter; distro and pyenv builds differ), version, free-threaded or GIL build, JIT setting and `PYTHONHASHSEED`. With native libraries, pin `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS`, and record the BLAS backend. `timeit` disables GC by default, which can flatter allocation-heavy code.

## lang.node — JavaScript and Node
tags: javascript, node, jit, microbenchmark
status: unverified

Tiered JIT and deoptimization make microbenchmarks fragile: V8 can eliminate unused results, and monomorphic loops can flatter code that goes megamorphic in production. Record Node and V8 versions and `NODE_ENV`. Run in fresh processes, consume results, and vary inputs. Browser timers are deliberately coarsened, so don't time tiny operations with `performance.now()`.

## lang.dotnet — .NET
tags: dotnet, jit, microbenchmark
status: unverified

Use BenchmarkDotNet, which handles process isolation, JIT warmup and statistics, and warns on Debug builds. Record runtime version, tiered compilation and PGO settings, and Server vs Workstation GC.

## lang.interop — Cross-language comparisons compare implementations
tags: c, cpp, rust, go, java, python, javascript, reporting
status: unverified

"X is faster than Y" usually compares implementations, compilers, flags, allocators and libraries. Publish every implementation and flags, invite the other side's expert or use their idiomatic version, and compare each language at its reasonable best. Otherwise it's an unfair competitor comparison.
