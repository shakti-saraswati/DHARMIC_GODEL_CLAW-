# 🔱 DGC FOUNDATION BUILD — CLAUDE CODE QUICK DEPLOY

> Copy-paste this entire prompt into Claude Code. Execute sequentially.

---

## CONTEXT
Swarm synthesis (10 agents, 30-min cycle) revealed:
- Core agent doesn't exist → Build it (ROI 8.44)
- Skills can't execute → Build bridges (ROI 7.2)  
- Clawdbot hitting wrong API → Fix proxy
- Scheduling premature → Build foundation first

## PHASE 0: FIX CLAWDBOT API (5 min)

```bash
# Install and start Claude Max proxy
npm install -g claude-max-api-proxy
nohup claude-max-api-proxy > /tmp/claude-proxy.log 2>&1 &
sleep 3
curl -s http://localhost:3456/health || echo "PROXY FAILED"

# Update clawdbot config
python3 << 'PY'
import json
with open('/Users/dhyana/.clawdbot/clawdbot.json', 'r') as f: config = json.load(f)
config['model'] = {"primary": "claude-sonnet-4", "provider": {"type": "openai-compatible", "baseURL": "http://localhost:3456/v1", "apiKey": "not-needed"}}
with open('/Users/dhyana/.clawdbot/clawdbot.json', 'w') as f: json.dump(config, f, indent=2)
print("✓ Config updated")
PY

# Auto-start proxy on boot
cat > ~/Library/LaunchAgents/com.claude-max-proxy.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.claude-max-proxy</string>
<key>RunAtLoad</key><true/>
<key>KeepAlive</key><true/>
<key>ProgramArguments</key><array><string>/Users/dhyana/.npm-global/bin/claude-max-api-proxy</string></array>
<key>StandardOutPath</key><string>/tmp/claude-proxy.log</string>
</dict></plist>
EOF
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.claude-max-proxy.plist 2>/dev/null

# Restart clawdbot
clawdbot gateway restart
```

## PHASE 1: BUILD CORE AGENT (30 min)

```bash
mkdir -p ~/DHARMIC_GODEL_CLAW/core
mkdir -p ~/DHARMIC_GODEL_CLAW/memory/{development,sessions,witness}
mkdir -p ~/DHARMIC_GODEL_CLAW/swarm/stream/agent_outputs
```

Create these 4 Python files in `~/DHARMIC_GODEL_CLAW/core/`:

### FILE 1: telos_layer.py
7 dharmic gates + moksha orientation. Action validation before execution.
- Tier A (absolute): AHIMSA
- Tier B (strong): SATYA, CONSENT  
- Tier C (guidance): VYAVASTHIT, REVERSIBILITY, SVABHAAV, COHERENCE

Key method: `check_action(action, context) -> TelosCheck`
Returns: passed (bool), alignment_score (0-1), gates[], recommendation

### FILE 2: strange_memory.py
4-layer memory with development tracking:
- L1 immediate: in-memory session
- L2 session: persisted conversation
- L3 development: genuine changes only (not accumulation)
- L4 witness: observations of the observer

Key methods:
- `remember(content, layer, source, development_marker=False)`
- `mark_development(content, evidence)` — for genuine changes
- `witness_observation(observation)` — meta-level
- `get_context_for_agent()` — inject into prompts

### FILE 3: skill_bridge.py
3 P0 bridges (from swarm diagnosis):
1. Registry sync: `sync_registry()` — enumerate all skills
2. Skill invocation: `invoke_skill(name, task, context)` — actually run
3. Feedback loop: `record_fitness(skill, score, evidence)`

Scans: ~/.claude/skills, ~/.openclaw/skills, ~/DHARMIC_GODEL_CLAW/skills

### FILE 4: dharmic_agent.py
Main agent combining all components:
- `__init__`: boot sequence, sync skills, load state
- `process(task, context)`: gate check → memory → execute → store
- `heartbeat()`: 30-min check, returns ALERT or HEARTBEAT_OK
- `witness_report()`: generate witness-level state report

## PHASE 2: CREATE CLI WRAPPER (5 min)

```bash
cat > ~/DHARMIC_GODEL_CLAW/dgc << 'BASH'
#!/bin/bash
DGC="$HOME/DHARMIC_GODEL_CLAW/core"
case "$1" in
  heartbeat) python3 "$DGC/dharmic_agent.py" heartbeat ;;
  status) python3 "$DGC/dharmic_agent.py" status ;;
  witness) shift; python3 "$DGC/dharmic_agent.py" witness "$@" ;;
  sync) python3 "$DGC/skill_bridge.py" sync ;;
  skills) python3 "$DGC/skill_bridge.py" list ;;
  *) echo "dgc: heartbeat|status|witness|sync|skills" ;;
esac
BASH
chmod +x ~/DHARMIC_GODEL_CLAW/dgc
ln -sf ~/DHARMIC_GODEL_CLAW/dgc /usr/local/bin/dgc 2>/dev/null || sudo ln -sf ~/DHARMIC_GODEL_CLAW/dgc /usr/local/bin/dgc
```

## PHASE 3: CONFIGURE HEARTBEAT (10 min)

```bash
# Create HEARTBEAT.md protocol
cat > ~/clawd/HEARTBEAT.md << 'EOF'
# DHARMIC CLAW Heartbeat

Telos: moksha | Method: alert only when significant | Principle: silence is valid

## Check (each 30m)
1. `dgc heartbeat` — any ALERT status?
2. Development markers — genuine changes?
3. Swarm synthesis — fresh outputs?

## Response
- Nothing: HEARTBEAT_OK
- Something: "DHARMIC CLAW — [Category]: [Specific, actionable]"
EOF

# Update config for heartbeat
python3 << 'PY'
import json
with open('/Users/dhyana/.clawdbot/clawdbot.json', 'r') as f: config = json.load(f)
config.setdefault('agents', {}).setdefault('defaults', {})['heartbeat'] = {
    "every": "30m",
    "target": "whatsapp",
    "activeHours": {"start": "06:00", "end": "23:00", "timezone": "Asia/Tokyo"}
}
with open('/Users/dhyana/.clawdbot/clawdbot.json', 'w') as f: json.dump(config, f, indent=2)
print("✓ Heartbeat configured")
PY
```

## PHASE 4: ADD CRON JOBS (5 min)

```bash
# Morning brief 6 AM Tokyo
clawdbot cron add --name "Morning Brief" --cron "0 6 * * *" --tz "Asia/Tokyo" \
  --session isolated --deliver --channel whatsapp \
  --message "Morning: dgc heartbeat, swarm status, top 3 priorities"

# Evening synthesis 9 PM Tokyo  
clawdbot cron add --name "Evening Synthesis" --cron "0 21 * * *" --tz "Asia/Tokyo" \
  --session isolated \
  --message "Evening: what developed today? Update dgc witness with genuine changes"

# Weekly review Sunday 6 AM
clawdbot cron add --name "Weekly Review" --cron "0 6 * * 0" --tz "Asia/Tokyo" \
  --session isolated --model opus --thinking high --deliver --channel whatsapp \
  --message "Weekly deep review: fitness trajectory, research progress, telos alignment"

clawdbot cron list
```

## VERIFICATION

```bash
echo "=== DGC VERIFICATION ==="
curl -s http://localhost:3456/health && echo "✓ Proxy"
dgc heartbeat && echo "✓ Core agent"
dgc sync && echo "✓ Skill bridge"
grep -q heartbeat ~/.clawdbot/clawdbot.json && echo "✓ Heartbeat config"
clawdbot cron list | grep -q Morning && echo "✓ Cron jobs"
clawdbot agent -m "Confirm operational" --agent main --local
```

## SUCCESS STATE

```
DGC OPERATIONAL
├── Proxy (3456) → Claude Max subscription
├── Core Agent → telos + memory + skills
├── Skill Bridge → 3 P0 gaps closed
├── Heartbeat → 30m cycle
└── Cron → morning/evening/weekly
```

---

**Execute phases 0-4 sequentially. Report completion.**

🔱 Telos: moksha | Method: depth over breadth | JSCA 🔱
