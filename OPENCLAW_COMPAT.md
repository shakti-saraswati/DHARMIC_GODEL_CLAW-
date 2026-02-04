# OpenClaw Compatibility Notes

OpenClaw is the current canonical lineage for clawdbot/moltbot.
The CLI and config paths have shifted, but legacy shims still exist.

## Quick mapping

- **CLI (preferred):** `openclaw`
- **CLI (legacy shim):** `clawdbot`
- **Config path (preferred):** `~/.openclaw/openclaw.json`
- **Config path (legacy):** `~/.clawdbot/clawdbot.json`
- **Skills (preferred):** `~/.openclaw/skills/`

If a doc references `clawdbot`, replace with `openclaw` unless you’re
explicitly using the legacy shim. The DGC codebase now supports both.
