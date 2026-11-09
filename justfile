set shell := ["bash", "-c"]

# run the test suite
test:
	uv run pytest -q

# check the environment and the install
doctor:
	uv run benchsane doctor

# run the MCP server over stdio
mcp:
	uv run benchsane-mcp
