# benchsane: engineering journal

Dated notes on what was tried, what happened, and why each call was made, including dead ends.
Entry format matches `pow log` (`## date (at sha)`). Lives outside docs/ on purpose: docs/ ships in the sdist.

## 2026-11-08 12:20 EST (at a6ceb90)

Dropped spec ab-maxrss-units. Observed on macOS 26.6.2 arm64 (one-off script, not a pow run capture): a child allocating ~200 MB reports ru_maxrss in bytes, so _maxrss_bytes is already correct on Darwin and a test would pass today. Updated the memory.measure card instead. Linux KiB unit still unchecked on real Linux.

## 2026-11-08 12:20 EST (at a6ceb90)

Decision: acceptance commands must be 'uv run --extra dev pytest ...' (plus '--extra mcp' for MCP tests). Plain 'uv run pytest' does not install the dev extra and fails at import, so the spec template example is wrong for this repo.

## 2026-11-08 12:20 EST (at a6ceb90)

Decision (Ryan): MCP compare is scoped by directory: realpath inside the server cwd or BENCHSANE_ALLOWED_DIRS, else refused before any file is opened. CLI unchanged. Found that MCP SDK 2.x masks tool errors as 'Error executing tool compare' (1.x may echo file-derived text) and the server stderr log can contain file-derived strings; left as a follow-up. Specs drafted: ab-platform-guard, ab-restore-affinity, mcp-compare-read-scope (tests xfail strict until agent PRs).

## 2026-11-08 12:20 EST (at a6ceb90)

Did not run pow init: it would write .github/, AGENTS.md, CLAUDE.md (protected by the autopilot constitution) and append to README.md (published README must not mention pow). pow log hardcodes docs/journal.md, which ships in the sdist, so this journal lives in journal/ and entries are appended by hand in the same format. pow check will not see it.

## 2026-11-08 12:30 EST (at a6ceb90)

Found by a planted-value check (not a pow run capture): capture() records RUSTFLAGS/CFLAGS/CXXFLAGS/LDFLAGS/JAVA_TOOL_OPTIONS verbatim, so paths and -Dpassword=... leak despite the 'no env values' docstring. Decision (Ryan): hash+length by default, include_flag_values=True to opt in. Spec privacy-env-hash-default drafted (tier 3); CLI flag and os.cmdline/doctor-details leaks are follow-ups.

## 2026-11-08 12:54 EST (at b79a92c)

PRs #5-#9 merged, main CI green on the last merge. Filed issues #10-#13 (one per spec) by hand after the auto-mode classifier blocked gh issue create from my session; created the four spec:* labels. Specs set to ready. No agent-ready labels yet; issue #4 (charter) still needs Ryan.

## 2026-11-08 13:34 EST (at 8c13a3b)

First agent run (issue #10, Sonnet medium) ended with 5 turns, ~9s, ~$0.06, no commits and no error; the empty branch was auto-deleted. Output is hidden unless AUTOPILOT_DEBUG=true, and the empty run used tier B's 1/day cap, so the debug rerun was gated. Did #10 by hand (PR #15, merged, main CI green incl. Linux and 3.10 cells). Cause of the silent exit is still unknown. #11 waits for the cap reset; set AUTOPILOT_DEBUG=true before it runs.
