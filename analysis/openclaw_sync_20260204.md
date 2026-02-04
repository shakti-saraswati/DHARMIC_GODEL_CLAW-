# OpenClaw Upstream Sync — 2026-02-04

## Snapshot
- Repo: `~/DHARMIC_GODEL_CLAW/cloned_source/openclaw`
- HEAD: `f52ca0a712c7c9a7ca917974177515ebe7530393`
- Describe: `v2026.2.1-148-gf52ca0a`
- Remote: `https://github.com/openclaw/openclaw.git`

## Key Upstream Changes (2026.2.1 → 2026.2.2)
- Web UI: new **Agents dashboard** (agents/tools/skills/models/channels/cron)
- Memory: opt‑in **QMD workspace memory** backend
- Config: default **subagent thinking** via `agents.defaults.subagents.thinking`
- Security: new **healthcheck skill** + bootstrap audit guidance
- Security hardening: SSRF guards, strict allowlists (Matrix/Slack/WhatsApp), plugin path validation
- OpenRouter: attribution headers in embedded runner
- Gateway: TLS 1.3 minimum; message timestamps in agent/chat
- Tooling: tool policy conformance snapshot; exec allowlist hardening

## DGC Integration Opportunities
### P0 (Immediate, low risk)
- Add a **healthcheck skill** to DGC (mirror OpenClaw) for uptime + endpoint sanity
- Record/track **subagent thinking level** in DGC config (even if we don’t spawn subagents yet)
- Update DGC docs to reference `.openclaw` paths (avoid legacy `.clawdbot` confusion)

### P1 (High leverage)
- Add optional **QMD memory backend** for DGC deep memory
- Add **SSRF guardrails** to any DGC web/tool fetchers
- Add **OpenRouter attribution** if/when DGC uses OpenRouter

### P2 (Platform polish)
- Mirror OpenClaw’s **Agents dashboard** into DGC web UI (agent files/tools/skills)
- Add gateway timestamping to DGC logs for consistent traceability

## Notes
- OpenClaw is clearly the canonical “clawdbot/moltbot” lineage.
- DGC already scans `.openclaw/skills` via `core/skill_bridge.py` — keep this.

## Next Actions (queued)
1) Implement DGC healthcheck skill + cron wire
2) Add DGC config field for subagent thinking level
3) Add `.openclaw` path references in DGC docs

## Status (2026-02-03)
- Implemented DGC healthcheck runner + web API endpoint
- Added subagent thinking config (agent config + daemon config + status)
- Added OpenClaw compatibility note + docs pointer
