# Using benchsane at work

benchsane is built to be fetched into company tooling without bringing anything personal or company-private across the boundary.

## What it does and doesn't touch

| | |
|---|---|
| Network | None, apart from your installer fetching the package. No telemetry. |
| Dependencies | None in the core. The `mcp` extra pulls in the MCP SDK and its dependencies. |
| System changes | None. `doctor` and `capture` only read. Fix commands are printed, never run. |
| Execution | Only `ab`, and only the commands you give it. The MCP server can't run commands. |
| `capture` records | CPU, memory, kernel and boot command line, toolchain versions, allowlisted tuning variables, commit hash |
| `capture` omits | Hostname, username, git remotes, and all other environment values |

Check `/proc/cmdline` and the allowlisted flags (`CFLAGS`, `RUSTFLAGS`, `JAVA_TOOL_OPTIONS` and so on) before sharing an `env.json` outside the company, since those can include internal paths or settings. `samples.json` and `report.md` contain your command lines unless you pass `--redact-commands`.

## Pin it

Install an exact version or, for stronger guarantees, a commit:

```bash
uvx benchsane@0.1.0 doctor
uvx --from git+https://github.com/RyanJHamby/benchsane@<commit-sha> benchsane doctor
```

If security policy requires it, mirror the repo internally and point at the mirror. Nothing in the code depends on the upstream URL, except the fallback command in the Skill's text.

## Keep company knowledge in a private overlay

Don't fork, and don't contribute company facts upstream. Keep cards in a company repo:

```bash
export BENCHSANE_KB_PATH=/path/to/company-repo/bench-kb    # Colon-separated list on Linux and macOS
benchsane kb search "gpu"
```

Overlay cards use the same format. A card with the same id as a bundled one replaces it, which lets you state your company's policy, for example on what `linux.turbo` should be in your fleet. Good candidates are fleet hardware quirks, standard benchmark hosts, SLO definitions, and how you tag results.

For MCP, set the same variable in the server's config:

```json
{
  "mcpServers": {
    "benchsane": {
      "command": "uvx",
      "args": ["--python", "3.12", "--from", "benchsane[mcp]==0.1.0", "benchsane-mcp"],
      "env": { "BENCHSANE_KB_PATH": "/path/to/company-repo/bench-kb" }
    }
  }
}
```

## Keep results in the project being measured

Run with `--out bench/runs/...` inside the project's own repo. Results from work belong there, never in this repo.

## Contributing from work

Check your employer's process for open-source dependencies and outside contributions. If you improve benchsane on company time, confirm that the work can go upstream before you send it. This isn't legal advice.
