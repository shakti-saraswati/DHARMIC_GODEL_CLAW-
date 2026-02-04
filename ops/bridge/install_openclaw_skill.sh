#!/bin/bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")/../../skills/dgc-bridge" && pwd)"
DEST_DIR="${HOME}/.openclaw/skills/dgc-bridge"

mkdir -p "$DEST_DIR"
cp -R "$SRC_DIR/"* "$DEST_DIR/"

echo "Installed dgc-bridge skill to: $DEST_DIR"
