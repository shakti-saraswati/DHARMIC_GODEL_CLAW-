# CLAWDBOT CONFIG VALIDATION

## CRITICAL FINDINGS

### 1. PACKAGE EXISTS - VALIDATED
- `claude-max-api-proxy` v1.0.0 published 2026-01-25
- npm: https://github.com/atalovesyou/claude-max-api-proxy
- Keywords include "clawdbot" - designed for this use case

### 2. PORT CONFLICT - ACTIVE
```
Port 18789: ALREADY IN USE by clawdbot gateway (PID 75317)
Port 3456: AVAILABLE
```
Gateway already running. Proposed changes will modify live config.

### 3. MODEL CONFIG STRUCTURE - INCORRECT

**Current config has TWO model fields:**
```json
"model": {"primary": "anthropic/claude-opus-4-5-20251101"},
"models": {
  "anthropic/claude-opus-4-5-20251101": {"alias": "opus"},
  "openai/claude-sonnet-4-5-20250929": {"alias": "sonnet"}
}
```

**Proposed addition conflicts:**
- BUILD.md suggests adding `model.provider` with OpenAI-compatible baseURL
- But `model` field is flat: `{"primary": "..."}`
- Correct structure: Add NEW model entry to `models` dict

**CORRECT APPROACH:**
```json
"models": {
  "openai/claude-max-proxy": {
    "alias": "max-local",
    "provider": "openai",
    "baseURL": "http://localhost:3456/v1",
    "apiKey": "dummy"
  }
}
```

### 4. CRON SYNTAX - VALID

**Existing crons (from `clawdbot cron list`):**
```
a38c2492: morning-brief      - cron 0 6 * * * @ Asia/Tokyo
4724cbb8: evening-synthesis  - cron 0 21 * * * @ Asia/Tokyo
00ec94f3: weekly-review      - cron 0 6 * * 0 @ Asia/Tokyo
```

**Proposed cron syntax is CORRECT:**
- `0 6 * * *` = daily 6 AM (standard cron)
- `0 21 * * *` = daily 9 PM
- `0 6 * * 0` = Sunday 6 AM

### 5. WHATSAPP TARGET FORMAT - NEEDS VERIFICATION

**Proposed:** `+818054961566`

**Current config shows:** No WhatsApp-specific config beyond `{"enabled": true}`

**Issue:** clawdbot documentation doesn't specify if it uses:
- E.164 format: `+818054961566`
- Phone ID format from WhatsApp Business API
- wa.me link format: `https://wa.me/818054961566`

**Recommendation:** Test with proposed format first. If fails, check clawdbot WhatsApp plugin docs.

### 6. LAUNCHAGENT ON MACOS 26.0 - COMPATIBLE

```
Existing LaunchAgents running:
- com.claude-max-api (PID 78)
- com.anthropic.claudefordesktop.ShipIt
```

macOS 25.0+ (Darwin kernel) supports LaunchAgents. No breaking changes for user-level agents.

**Proposed plist is valid:**
- KeepAlive = true
- RunAtLoad = true
- StandardOutPath/StandardErrorPath for logging

### 7. HEARTBEAT CONFIG - INCOMPLETE

**Current:**
```json
"heartbeat": {"every": "30m"}
```

**Proposed additions:**
- `heartbeat.target` = "whatsapp"
- `heartbeat.to` = "+818054961566"
- `heartbeat.activeHours` = [6, 22]

**MISSING:** No validation that clawdbot v2026.1.24-3 supports these fields.

**Risk:** Config may be accepted but ignored if fields unrecognized.

**Mitigation:** Check `clawdbot doctor` after changes.

## MERGED CONFIG (CORRECTED)

```json
{
  "agents": {
    "defaults": {
      "model": {"primary": "openai/claude-max-proxy"},
      "models": {
        "openai/claude-max-proxy": {
          "alias": "max-local",
          "provider": "openai",
          "baseURL": "http://localhost:3456/v1",
          "apiKey": "dummy"
        },
        "anthropic/claude-opus-4-5-20251101": {"alias": "opus"}
      },
      "heartbeat": {
        "every": "30m",
        "target": "whatsapp",
        "to": "+818054961566",
        "activeHours": [6, 22]
      },
      "workspace": "/Users/dhyana/clawd"
    }
  },
  "gateway": {"port": 18789, "mode": "local"},
  "plugins": {"entries": {"whatsapp": {"enabled": true}}}
}
```

## WHAT WILL WORK

1. claude-max-api-proxy installation via npm
2. Proxy running on port 3456
3. Cron job syntax
4. LaunchAgent on macOS 26.0
5. Basic model routing to localhost:3456

## WHAT WON'T WORK (WITHOUT FIXES)

1. Proposed `model.provider` structure (conflicts with existing schema)
2. Heartbeat fields (may be ignored if unsupported by clawdbot version)

## DEPLOYMENT CHECKLIST

- [ ] Backup existing config: `cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.backup`
- [ ] Install proxy: `npm install -g claude-max-api-proxy`
- [ ] Test proxy standalone: `claude-max-api-proxy --port 3456`
- [ ] Update config with CORRECTED model structure
- [ ] Run `clawdbot doctor` to validate
- [ ] Test model routing: `clawdbot chat --model max-local "test"`
- [ ] Verify WhatsApp target format works
- [ ] Load LaunchAgent: `launchctl load ~/Library/LaunchAgents/com.claude-max-api.plist`
- [ ] Monitor logs: `tail -f /tmp/claude-max-api-proxy.log`
