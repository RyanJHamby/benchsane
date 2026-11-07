#!/usr/bin/env python3
"""Run one unchanged binary under many environment sizes and report the spread.

Nothing about the program changes. Only the bytes above the stack do, as in Mytkowicz et al.,
"Producing Wrong Data Without Doing Anything Obviously Wrong!" (ASPLOS 2009).
Whether an effect appears depends on your CPU and compiler. A flat result is a valid outcome.
Run it with ASLR off so the stack start isn't randomized:

    gcc -O0 loop.c -o loop
    setarch "$(uname -m)" -R python3 run.py ./loop

Compare the spread across sizes with the spread within one size, which is your noise.
"""
import statistics as st
import subprocess
import sys
import time

binary = sys.argv[1] if len(sys.argv) > 1 else "./loop"
SIZES = range(0, 4096, 64)
REPEATS = 5


def once(pad):
    env = {"PAD": "x" * pad}
    t0 = time.perf_counter()
    subprocess.run([binary], env=env, check=True)
    return time.perf_counter() - t0


rows = []
for pad in SIZES:
    times = [once(pad) for _ in range(REPEATS)]
    rows.append((pad, min(times), st.pstdev(times) / st.fmean(times)))
    print(f"env+{pad:<5} min {min(times) * 1000:9.2f} ms", flush=True)

mins = [r[1] for r in rows]
print(f"\nmin across sizes: {min(mins) * 1000:.2f} ms, max: {max(mins) * 1000:.2f} ms, spread: {(max(mins) / min(mins) - 1) * 100:.1f}%")
print(f"typical within-size noise (median CV): {st.median(r[2] for r in rows) * 100:.2f}%")
print("fastest size:", rows[mins.index(min(mins))][0], "bytes; slowest size:", rows[mins.index(max(mins))][0], "bytes")
