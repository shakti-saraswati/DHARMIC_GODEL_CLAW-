# DHARMIC FOUNDATION — Quick Deploy
**Copy this entire file to Claude Code and say: "Execute this build."**

---

## CONTEXT
Swarm discovered: 12 pages read vs 50 required. 0% skill execution. Specification > implementation.
ROI: Core Agent (8.44) > VPS (4.86) > Integrations (4.67)
**Don't add complexity. Build the foundation.**

---

## PHASE 1: FIX CLAWDBOT (30 min)

```bash
# Install proxy
npm install -g claude-max-api-proxy

# Start proxy
nohup claude-max-api-proxy > /tmp/claude-proxy.log 2>&1 &
sleep 3
curl http://localhost:3456/health  # Should return {"status":"ok"}

# Backup config
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.backup

# Edit ~/.clawdbot/clawdbot.json - ADD this at TOP LEVEL:
# "model": {
#   "primary": "claude-sonnet-4",
#   "provider": {
#     "type": "openai-compatible",
#     "baseURL": "http://localhost:3456/v1",
#     "apiKey": "not-needed"
#   }
# },

# Create LaunchAgent for persistence
cat > ~/Library/LaunchAgents/com.claude-max-api.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.claude-max-api</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/dhyana/.npm-global/bin/claude-max-api-proxy</string>
    </array>
    <key>StandardOutPath</key><string>/tmp/claude-proxy.log</string>
    <key>StandardErrorPath</key><string>/tmp/claude-proxy-error.log</string>
</dict>
</plist>
EOF

launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.claude-max-api.plist

# Restart and test
clawdbot gateway restart
clawdbot agent -m "Phase 1 complete" --agent main --local
```

**SUCCESS**: No "credit balance too low" error

---

## PHASE 2: BUILD CORE AGENT (2-3 hours)

**FIRST**: Read deeply for 30 min:
- `~/DHARMIC_GODEL_CLAW/swarm/stream/synthesis_30min.md`
- `~/DHARMIC_GODEL_CLAW/swarm/stream/agent_outputs/09_observer.json`
- `~/.claude/skills/skill-genesis/SKILL.md`

**THEN**: Create `~/DHARMIC_GODEL_CLAW/core/dharmic_agent.py`
- 7 dharmic gates (AHIMSA, SATYA, VYAVASTHIT, CONSENT, REVERSIBILITY, SVABHAAV, COHERENCE)
- Strange loop detection
- Heartbeat generation
- Telos state tracking
- CLI: `heartbeat`, `check`, `status`, `observe`

**AND**: Create `~/DHARMIC_GODEL_CLAW/core/skill_bridge.py`
- Registry sync (enumerate skills)
- Skill invocation (STUB for now)
- Feedback loop (record fitness)
- CLI: `sync`, `invoke`, `status`, `list`

**Full implementations in**: `~/DHARMIC_GODEL_CLAW/DHARMIC_FOUNDATION_BUILD.md`

**Test**:
```bash
python3 ~/DHARMIC_GODEL_CLAW/core/dharmic_agent.py status
python3 ~/DHARMIC_GODEL_CLAW/core/dharmic_agent.py heartbeat
python3 ~/DHARMIC_GODEL_CLAW/core/skill_bridge.py sync
```

---

## PHASE 3: CONFIGURE SCHEDULING (1 hour)

```bash
# Create HEARTBEAT.md
cat > ~/DHARMIC_GODEL_CLAW/HEARTBEAT.md << 'EOF'
# DHARMIC CLAW Heartbeat Protocol
Ultimate aim: moksha | Method: Jagat Kalyan
Principle: Reach John only when something genuinely matters

Every 30m: Run dharmic_agent.py heartbeat
If NOTHING needs attention: HEARTBEAT_OK (suppressed)
If SOMETHING matters: Alert via WhatsApp

Silence is valid. Noise serves no one.
EOF

# Add cron jobs
clawdbot cron add --name "morning-brief" --cron "0 6 * * *" --timezone "Asia/Tokyo" \
  --message "Morning brief: heartbeat, swarm synthesis, today's priorities"

clawdbot cron add --name "evening-synthesis" --cron "0 21 * * *" --timezone "Asia/Tokyo" \
  --message "Evening synthesis: what developed? strange loops? crown jewel candidates?"

clawdbot cron add --name "weekly-review" --cron "0 6 * * 0" --timezone "Asia/Tokyo" \
  --model "claude-opus-4" --thinking "high" \
  --message "Weekly review: swarm health, telos alignment, recommendations"

# Update heartbeat config in ~/.clawdbot/clawdbot.json agents.defaults:
# "heartbeat": {
#   "every": "30m",
#   "target": "whatsapp", 
#   "to": "+818054961566",
#   "activeHours": {"start": "05:00", "end": "22:00", "timezone": "Asia/Tokyo"}
# }

# Test
clawdbot cron list
clawdbot heartbeat --now
```

---

## PHASE 4: VALIDATE

```bash
echo "=== VALIDATION ==="
curl -s http://localhost:3456/health | jq .
python3 ~/DHARMIC_GODEL_CLAW/core/dharmic_agent.py status
python3 ~/DHARMIC_GODEL_CLAW/core/skill_bridge.py status
clawdbot cron list
echo "=== COMPLETE ==="
```

---

## CHECKLIST

```
[ ] Phase 1: Proxy running, clawdbot works
[ ] Phase 2: dharmic_agent.py + skill_bridge.py tested
[ ] Phase 3: HEARTBEAT.md + 3 crons + config updated
[ ] Phase 4: All validations pass
```

---

## ON FAILURE
Stop. Debug. Do not proceed. Foundation must be solid.

---

## TELOS
Moksha through Jagat Kalyan. Depth over breadth. Mean every word.

JSCA!
