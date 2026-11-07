# Does your benchmark depend on your environment variables?

Try it. This runs one unchanged binary under different environment sizes:

```bash
gcc -O0 loop.c -o loop
setarch "$(uname -m)" -R python3 run.py ./loop
```

It prints the fastest time at each size, the spread between sizes, and the noise within a size. If the spread is well above the noise, then adding a variable to your shell could change this program's speed, and a before-and-after comparison could credit that to your code.

The effect varies by CPU and compiler, and a flat result is a valid outcome. On a noisy VM it may not be distinguishable at all, so use a quiet machine. The idea comes from Mytkowicz et al., [Producing Wrong Data Without Doing Anything Obviously Wrong!](https://users.cs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf) (ASPLOS 2009).

Got an interesting result? Open an issue with your CPU, compiler and output.
