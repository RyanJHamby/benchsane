---
id: mcp-registry-listing
goal: benchsane's read-only MCP server is listed in the official MCP Registry under dev.ryanjhamby/benchsane, pointing at the benchsane PyPI release, so MCP clients and downstream catalogs can find it.
acceptance:
  - python3 -c "import json; d=json.load(open('server.json')); assert d['name']=='dev.ryanjhamby/benchsane' and d['packages'][0]['identifier']=='benchsane'"
  - grep -q "mcp-name: dev.ryanjhamby/benchsane" README.md
scope:
  - server.json
  - README.md
non_goals:
  - no code changes; the MCP server itself is unchanged
  - agents do not publish anything: PyPI upload, DNS records, making the repo public and mcp-publisher publish are Ryan's steps
risk_tier: 3
max_runs: 1
autonomy: inherit
status: draft
---

## Why
Agents and MCP catalogs discover servers through the official registry; downstream catalogs pull from it on their own.
benchsane already ships a read-only stdio server (`benchsane-mcp`, five tools). Listing it is the cheapest distribution
for the tool and links it to ryanjhamby.dev.

## Published entries cannot be removed
Each published registry version is immutable and, as of late 2026, cannot be unpublished. Nothing employer-related, no
private paths and no unverified claims may appear in `server.json`, the PyPI description or the README.

## Ryan's launch steps (in order)
1. Decide charter issue #4 and that 0.1.0 is ready; make the repo public.
2. `mcp-publisher validate` on `server.json`. The file was written without the schema to hand; fix whatever it reports.
   Open question: whether the entry needs `runtimeArguments`/`packageArguments` so clients launch the
   `benchsane-mcp` entry point with the `[mcp]` extra (README config: `uvx --from benchsane[mcp]==0.1.0 benchsane-mcp`).
3. Release 0.1.0 to PyPI. The README (the PyPI description) must keep the `mcp-name` comment; the registry checks it.
4. Namespace: `dev.ryanjhamby/*` needs a DNS TXT record on ryanjhamby.dev (`mcp-publisher login dns`). If you'd rather
   not, switch the name in both files to `io.github.ryanjhamby/benchsane` and log in with GitHub.
5. `mcp-publisher publish`, then `mcp-publisher status` / the registry API to confirm the listing.
6. Log the outcome in journal/decisions.md and on the discoverability ledger.
