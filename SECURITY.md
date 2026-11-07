# Security policy

## Reporting a vulnerability

Please report privately through GitHub's "Report a vulnerability" (private security advisory) on this repository. Don't open a public issue. Expect an acknowledgement within a week; this is a single-maintainer project, so response times are best-effort.

## What benchsane does and does not do

- Read-only by design: `doctor` and `capture` read system state and never change settings.
- No network calls and no telemetry in the core package.
- `ab` executes the commands you give it, as you. Only pass commands you trust.
- Results can reveal hardware and workload details. See "privacy" in `docs/OUTPUT-FORMATS.md` before sharing them.

## In scope

Anything that makes the tool read more than it documents, write outside its output directory, leak secrets into outputs, execute something the user didn't ask for, or make a pinned install unsafe.

## Supported versions

Only the latest minor release receives fixes while the project is pre-1.0.
