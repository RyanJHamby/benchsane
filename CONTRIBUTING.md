# Contributing

Corrections matter most here. A wrong benchmarking tip is worse than none.

## The easiest useful contribution: verify a card

```bash
benchsane kb list | grep unverified
```

Pick a card you know about. Find a primary source (kernel docs, man page, the tool's own docs, the paper) and either confirm it or fix it. Then set `status: cited`, add the `source:` line, and open a PR. A correction based on your own experience is welcome too: open an issue with your hardware, versions and what you saw.

## Card format

Cards live in `src/benchsane/kb/`:

```markdown
## linux.example — Short title
tags: linux, kernel
status: cited
source: https://primary-source https://optional-second-source

What goes wrong, how to check for it, what to do.
```

- `cited` means you read the sources and they support the card's main claim. Mark anything else `unverified`.
- Keep it short and specific, with commands someone can run.
- Give the reason as well as the rule, and note when the advice depends on the goal.
- Quote no performance number without the hardware and a way to reproduce it.

## Code

```bash
pip install -e '.[dev,mcp]'
pytest
```

The core stays dependency-free and read-only. `doctor` and `capture` may not change the system, and `capture` must not record secrets, hostnames or usernames. New checks need a linked card. If you want to add a big feature, please open an issue first, since [much is out of scope on purpose](docs/ROADMAP.md).

Please disclose substantial AI assistance in the PR, and check its claims yourself.
