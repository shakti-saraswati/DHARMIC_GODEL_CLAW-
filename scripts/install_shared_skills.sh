#!/usr/bin/env bash
set -euo pipefail

SHARED_ROOT="/Users/Shared/skills-shared"
SKILLS=("cosmic-krishna-coder" "dgc-tui" "dgc-bridge" "dgc")

if [[ ! -d "$SHARED_ROOT" ]]; then
  echo "Shared skills root not found: $SHARED_ROOT" >&2
  exit 1
fi

mkdir -p "$HOME/.openclaw/skills" "$HOME/.clawdbot/skills" "$HOME/.claude/skills"

for s in "${SKILLS[@]}"; do
  if [[ -d "$SHARED_ROOT/$s" ]]; then
    ln -sfn "$SHARED_ROOT/$s" "$HOME/.openclaw/skills/$s"
    ln -sfn "$SHARED_ROOT/$s" "$HOME/.clawdbot/skills/$s"
    ln -sfn "$SHARED_ROOT/$s" "$HOME/.claude/skills/$s"
    echo "linked: $s"
  else
    echo "missing: $SHARED_ROOT/$s" >&2
  fi
done

echo "Done. Skills linked for: $USER"
