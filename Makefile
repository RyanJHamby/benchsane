.PHONY: check

# The one command that runs everything: the full test suite, including the MCP tests.
# Needs both extras: plain `uv run pytest` fails at collection in a fresh environment.
check:
	uv run --extra dev --extra mcp pytest -q
