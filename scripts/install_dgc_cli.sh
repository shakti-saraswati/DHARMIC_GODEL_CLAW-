#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="$HOME/.local/bin"
TARGET="$TARGET_DIR/dgc"

mkdir -p "$TARGET_DIR"
ln -sf "$ROOT/scripts/dgc" "$TARGET"

cat <<MSG
DGC CLI installed:
  $TARGET

If you don't already have ~/.local/bin in PATH, add this to your shell:
  export PATH="$HOME/.local/bin:$PATH"

Usage:
  dgc init --target /path/to/repo
  dgc verify --target /path/to/repo --dry-run
MSG
