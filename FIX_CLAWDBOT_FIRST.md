# FIX CLAWDBOT FIRST
**Run this BEFORE the Master Ops prompt**

---

## The Problem
Clawdbot hits Anthropic API directly (credits) not Claude Max subscription.
Proxy IS running but config doesn't use it.

## Quick Fix

```bash
# 1. Verify proxy running
curl http://localhost:3456/health
# Should return: {"status":"ok"}

# 2. If not running, start it:
nohup claude-max-api-proxy > /tmp/claude-proxy.log 2>&1 &
sleep 3
curl http://localhost:3456/health

# 3. Backup config
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.backup.$(date +%Y%m%d_%H%M)

# 4. Fix config - replace model section
# Edit ~/.clawdbot/clawdbot.json
# Change agents.defaults.model FROM:
#   "model": { "primary": "anthropic/claude-opus-4-5-20251101" }
# TO:
#   "model": {
#     "primary": "claude-sonnet-4",
#     "provider": {
#       "type": "openai-compatible",
#       "baseURL": "http://localhost:3456/v1",
#       "apiKey": "not-needed"
#     }
#   }

# 5. Or use jq:
cat ~/.clawdbot/clawdbot.json | jq '.agents.defaults.model = {
  "primary": "claude-sonnet-4",
  "provider": {
    "type": "openai-compatible",
    "baseURL": "http://localhost:3456/v1",
    "apiKey": "not-needed"
  }
}' > /tmp/clawdbot-fixed.json && mv /tmp/clawdbot-fixed.json ~/.clawdbot/clawdbot.json

# 6. Restart gateway
clawdbot gateway restart

# 7. Test
clawdbot agent -m "Proxy test - this should work!" --agent main --local
```

## Success = No "credit balance too low" error

## Then Run Master Ops
```
Read ~/DHARMIC_GODEL_CLAW/DHARMIC_CLAW_MASTER_OPS.md and execute.
```
