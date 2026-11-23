# benchsane

<!-- mcp-name: dev.ryanjhamby/benchsane -->

**Your benchmark might be lying to you. Find out before you publish the number.**

```console
$ uvx benchsane doctor
[WARN] linux.virt: Virtualized (kvm). Compare with interleaving and name the instance type on any number.
       why: benchsane kb show virt.vm
[info] linux.perf_access: perf_event_paranoid=2, but no hardware PMU is exposed: no cycle or cache counters.
[info] linux.aslr: ASLR is full. Off suits chasing a tiny diff in one binary; on with many processes suits claims.
[ok  ] linux.clocksource: Clock source is tsc.
...
Grade: caveated. Same-host comparisons are fine. Disclose the warnings on any number you quote.
```

Unrelated changes can move a benchmark: environment size, link order, turbo, a closed-loop load generator, one lucky process. benchsane catches what it can and explains the rest:

- **`doctor`** checks whether this machine is fit to measure on. It's read-only, and every finding links to an explanation.
- **`ab`** compares two commands properly: fresh processes, randomized interleaving, paired analysis, and an A/A mode that measures your noise floor.
- **`kb`** holds 110+ cards on what goes wrong across languages, compilers, kernels, CPUs, GPUs, clouds and workloads, usable offline.
- **Agents** get the same knowledge as a Skill or a read-only MCP server, so your coding agent stops quoting numbers it shouldn't.

It complements hyperfine, Google Benchmark, JMH, perf and Bencher rather than replacing them. It tells you which to use and how they can mislead you. See [what it builds on](docs/EXISTING-TOOLS.md).

**Curious?** [Check whether your environment variables change a program's speed](examples/layout-bias).

**Status: 0.1.0, early, tested on Linux.** Each card is `cited` (its main claim was checked against the linked sources) or `unverified` (a lead, written without a checked source). [Verifying a card is a great first contribution](CONTRIBUTING.md).

## Install

```bash
uvx benchsane doctor                 # Run with no install
pipx install benchsane               # Or install it
uvx benchsane@0.1.0 doctor           # Or pin it, as you should in shared tooling
```

The core uses only the Python 3.10+ standard library, makes no network calls and sends no telemetry.

## Use

```bash
benchsane doctor                      # Is this machine fit to measure on?
benchsane kb search --tag rust --tag linux
benchsane kb show linux.aslr

# Measure the noise floor, then compare
benchsane ab -a './bench_old' --aa --out bench/runs/2026-11-03-aa
benchsane ab -a './bench_old' -b './bench_new' --env-pad --out bench/runs/2026-11-03-new

# Compare existing hyperfine, Google Benchmark, pyperf or plain-number files
benchsane compare old.json new.json --fail-on-regression

# Use the results elsewhere
benchsane export bench/runs/2026-11-03-new/samples.json --to csv        # Also: bmf, github-benchmark, claim
```

`ab` randomizes order inside each block, runs each command in a fresh process, checks exit codes, discards stdout, and pairs samples within blocks so that shared drift cancels out. It writes `samples.json`, `env.json` and `report.md`, and refuses to overwrite an existing run. Each report includes a one-sentence claim that carries its own evidence, so a number doesn't lose its context when it's pasted elsewhere. All JSON output is versioned, and [the formats are documented](docs/OUTPUT-FORMATS.md).

## Connect an agent

**Skill (start here).** It costs almost no context until it's needed, and it works with anything that reads `SKILL.md`:

```bash
benchsane install-skill                 # .claude/skills/benchsane
benchsane install-skill --dir .agents/skills
```

**MCP.** Use this when a client can't use Skills or the agent has no shell. The server uses stdio and offers five tools: `kb_search`, `kb_get`, `doctor`, `capture_env`, `compare`. None can run a command or change the system.

```json
{
  "mcpServers": {
    "benchsane": {
      "command": "uvx",
      "args": ["--python", "3.12", "--from", "benchsane[mcp]==0.1.0", "benchsane-mcp"]
    }
  }
}
```

## In CI

```yaml
- uses: RyanJHamby/benchsane@v0
  with:
    baseline: results/base.json
    candidate: results/pr.json
    fail-on-regression: true
```

This adds the verdict and the runner's doctor report to the job summary. Shared CI runners are noisy, so [read about the trade-offs](src/benchsane/kb/virtualization.md) first, and use [Bencher](https://github.com/bencherdev/bencher) or [CodSpeed](https://codspeed.io) for history.

## Using it inside a company

See [docs/USING-AT-WORK.md](docs/USING-AT-WORK.md). In short: pin a tag, keep results in your own repo, and keep private cards in your own directory via `BENCHSANE_KB_PATH`.

## Docs

- [The framework](docs/FRAMEWORK.md): the measurement loop and the full configuration matrix
- [Output formats](docs/OUTPUT-FORMATS.md): schemas, metric names, units and exports
- [Existing tools](docs/EXISTING-TOOLS.md): what to adopt rather than rebuild
- [Roadmap](docs/ROADMAP.md): what isn't covered yet

## Contribute

The most useful contribution is a correction with a source. See [CONTRIBUTING.md](CONTRIBUTING.md).

## How this was built

Claude (Anthropic) drafted the code, cards and docs from Ryan Hamby's prompt on 2026-11-03, and the tests were run in a Linux VM. A separate Claude agent then fact-checked the cards against web sources, and its corrections were applied. Most cards remain `unverified`. No human expert has reviewed them yet, so corrections are very welcome. The project has only been run on Linux so far. No performance numbers are claimed.

## License

Apache-2.0
