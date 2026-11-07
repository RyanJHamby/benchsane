# Compilers and builds

## build.identity — Benchmark an identified binary
tags: compiler, build, reproducibility, all
status: unverified

Record commit, dirty state, full compiler version, full flags, dependency lock, and the binary's hash. CMake and Bazel flags hide in cache and toolchain files, so capture compile commands (`compile_commands.json`, `cargo build -v`, `-frecord-gcc-switches`). A mismatch here invalidates the comparison.

## build.same-compiler — Compare with the same compiler
tags: compiler, build, c, cpp
status: cited
source: https://insidehpc.com/2014/05/compiliers-love-messing-benchmarks/

Comparing servers with benchmarks you compile requires matching compilers, or accounting for the difference. Gregg's point, as reported here, is that compilers can mess with a benchmark, so active benchmarking should surface this. Flags and distro defaults matter in the same way.

## build.flags — Flags that change results
tags: compiler, build, c, cpp, rust
status: unverified

Record: `-O` level (O3 isn't always better than O2), `-march`/`-mtune`/`target-cpu` (a `native` binary isn't portable, and the x86-64-v3 baseline differs from v1), LTO, PGO, BOLT, `-fno-omit-frame-pointer`, `-fPIE`/static, `_FORTIFY_SOURCE`, stack protector, CET, `-fno-plt`, `-ffast-math`. Distros turn on hardening by default, so a local build and a distro package are different programs.

## build.pgo — PGO and LTO profiles are data
tags: compiler, build, c, cpp, rust, go
status: unverified

PGO results depend on the training workload. If the training and benchmark workloads match, the gain is inflated. Train on one set and evaluate on another, and commit or identify the profile. See the calibration-versus-evaluation crime.

## build.link-order — Layout shifts between "identical" builds
tags: compiler, build, layout, bias, c, cpp, rust
status: cited
source: https://users.cs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf https://gcc.gnu.org/pipermail/gcc-cvs/2020-June/299793.html

Link order and any unrelated code change shift code alignment. A PR can appear to change performance in an untouched hot loop. Before believing a small effect, rebuild with a shuffled link order or aligned functions (`-falign-functions=32`/`-falign-loops=32` can reduce this particular effect for diagnosis).

## build.debug-info — Profiling builds can differ
tags: compiler, build, profiling
status: unverified

Frame pointers and `-g` are usually cheap but not free for all code; measure the build you profile. Keep debug info with `-g` on the optimized build (or split debug files) to preserve symbolization, instead of profiling a different optimization level.

## build.static — Dynamic linking adds noise
tags: compiler, build, linux
status: cited
source: https://rocm.docs.amd.com/projects/llvm-project/en/docs-7.14.1/LLVM/llvm/html/Benchmarking.html

LLVM recommends static linking when measuring compiler speed to eliminate dynamic loading effects, and tmpfs for program, inputs and outputs to avoid storage variability. Use only when those aren't what you're measuring, and record `ldd` and library versions otherwise.
