#!/usr/bin/env bash
# Idempotent toolchain setup. Safe on a laptop, a VPS, or a cloud session.
set -euo pipefail

usage() { echo "usage: bootstrap.sh [--dry-run]"; }
die() { echo "bootstrap: $1" >&2; exit 1; }

DRY=0
case "${1:-}" in
  "") ;;
  --dry-run) DRY=1 ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; die "unknown argument: $1" ;;
esac

run() { if [ "$DRY" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }

cd "$(dirname "$0")/.." || die "cannot cd to repo root"

# Install mise if missing (per-user, no root needed), then the pinned tools.
if ! command -v mise >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/mise" ]; then
    export PATH="$HOME/.local/bin:$PATH"
  elif command -v brew >/dev/null 2>&1; then
    run brew install mise
  elif command -v curl >/dev/null 2>&1; then
    echo "bootstrap: installing mise from mise.run" >&2
    if [ "$DRY" = 1 ]; then echo "[dry-run] curl -fsSL https://mise.run | sh"; else curl -fsSL https://mise.run | sh; fi
    export PATH="$HOME/.local/bin:$PATH"
  else
    die "mise missing and no brew or curl to install it"
  fi
fi

if [ "$DRY" = 1 ]; then
  echo "[dry-run] mise trust && mise install"
else
  command -v mise >/dev/null 2>&1 || die "mise not on PATH after install"
  mise trust --quiet mise.toml
  mise install --quiet
fi

# Repo-specific dependency installs (idempotent). `make check` needs both extras.
if [ "$DRY" = 1 ]; then
  echo "[dry-run] mise exec -- uv sync --extra dev --extra mcp"
else
  mise exec -- uv sync --extra dev --extra mcp
fi
echo "bootstrap: ok"
