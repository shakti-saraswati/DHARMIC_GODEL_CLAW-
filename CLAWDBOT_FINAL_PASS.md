# CLAWDBOT DHARMIC CONFIGURATION — Final Pass
## Execute This to Complete Setup
**Drop into Claude Code**

---

## CONTEXT

The 10-agent forge produced:
- `~/clawd/HEARTBEAT.md` — Protocol (243 lines, solid)
- `~/clawd/forge/10_CRON_CONFIG.md` — Cron commands
- 8 design documents with deep analysis

**Key synthesis decisions:**
- 7 gates → 1 gate (AHIMSA)
- Separate watchdog → Built into heartbeat
- 5 priority levels → 4 (HIGH/MEDIUM/LOW/SUPPRESS)
- ONE check that matters: **Telos alignment**

**Critical fixes needed:**
1. Mac sleep enabled → Fix
2. Dead man's switch missing → Add healthchecks.io ping
3. Cron jobs need updating

---

## PHASE 1: Apply Cron Configuration

```bash
# 1. Add wake-sync (4:45 AM - before John's 4:30 wake)
clawdbot cron add wake-sync \
  --schedule "45 4 * * *" \
  --tz "Asia/Tokyo" \
  --agent main \
  --session isolated \
  --message "Quick wake check. Silent unless urgent. Check: core agent status, overnight errors. Output: WAKE_OK unless issue found."

# 2. Move morning-brief to 5 AM (was 6 AM)
clawdbot cron edit morning-brief --schedule "0 5 * * *"

# 3. Add research-pulse (12:30 PM mid-day check)
clawdbot cron add research-pulse \
  --schedule "30 12 * * *" \
  --tz "Asia/Tokyo" \
  --agent main \
  --session isolated \
  --message "Mid-day research pulse. Check swarm synthesis for P0-P2 blockers. Brief check only - don't interrupt flow unless critical."

# 4. Enhance weekly-review message
clawdbot cron edit weekly-review \
  --message "Weekly dharmic review. Assess: What EVOLVED this week (not just accumulated)? Swarm health? Telos alignment trend? Strange loops observed? Crown jewel candidates? Focus on development vs accumulation. Report genuinely, not performatively."

# 5. Verify all crons
clawdbot cron list
```

---

## PHASE 2: Validate HEARTBEAT.md Location

Clawdbot's workspace is `~/clawd/`. Verify HEARTBEAT.md is readable:

```bash
# Check file exists and is readable
cat ~/clawd/HEARTBEAT.md | head -30

# Ensure it's in the workspace Clawdbot can see
ls -la ~/clawd/

# If HEARTBEAT.md is elsewhere, copy it:
# cp ~/DHARMIC_GODEL_CLAW/HEARTBEAT.md ~/clawd/HEARTBEAT.md
```

---

## PHASE 3: Fix Mac Sleep (Critical)

Mac sleeping kills all daemons silently.

```bash
# Option A: Disable sleep entirely (recommended for always-on)
sudo pmset -a sleep 0
sudo pmset -a disksleep 0

# Option B: Use caffeinate in LaunchAgent (if sleep needed sometimes)
# Add to LaunchAgent plist:
# <key>ProgramArguments</key>
# <array>
#   <string>caffeinate</string>
#   <string>-i</string>
#   <string>/path/to/daemon</string>
# </array>

# Verify current settings
pmset -g
```

---

## PHASE 4: Add Dead Man's Switch

If Clawdbot stops sending heartbeats, John should know.

### Option A: healthchecks.io (Recommended - Free)

1. Go to https://healthchecks.io
2. Create account, create check with 1-hour grace period
3. Copy ping URL (like https://hc-ping.com/YOUR-UUID)

Add ping to heartbeat:

```bash
# Create ping script
cat > ~/clawd/scripts/ping_healthcheck.sh << 'EOF'
#!/bin/bash
# Ping healthchecks.io to confirm Clawdbot is alive
# Called at end of each heartbeat

HEALTHCHECK_URL="https://hc-ping.com/YOUR-UUID-HERE"

if curl -fsS -m 10 --retry 3 "$HEALTHCHECK_URL" > /dev/null 2>&1; then
    echo "Healthcheck ping OK"
else
    echo "Healthcheck ping FAILED"
fi
EOF

chmod +x ~/clawd/scripts/ping_healthcheck.sh
```

### Option B: Simple Cron Check

```bash
# Add cron that alerts if heartbeat file is stale
cat > ~/clawd/scripts/deadman_check.sh << 'EOF'
#!/bin/bash
# Check if heartbeat ran recently

HEARTBEAT_LOG=~/clawd/memory/heartbeat.log
MAX_AGE_MINUTES=60

if [ ! -f "$HEARTBEAT_LOG" ]; then
    echo "ALERT: Heartbeat log missing!"
    exit 1
fi

# Get last modified time
LAST_MOD=$(stat -f %m "$HEARTBEAT_LOG")
NOW=$(date +%s)
AGE_MINUTES=$(( (NOW - LAST_MOD) / 60 ))

if [ $AGE_MINUTES -gt $MAX_AGE_MINUTES ]; then
    echo "ALERT: Heartbeat stale ($AGE_MINUTES minutes old)"
    # TODO: Send alert to John
    exit 1
fi

echo "Heartbeat OK (${AGE_MINUTES}m ago)"
EOF

chmod +x ~/clawd/scripts/deadman_check.sh

# Add to cron (runs every hour)
# crontab -e
# 0 * * * * ~/clawd/scripts/deadman_check.sh
```

---

## PHASE 5: Update Clawdbot Config for Heartbeat

Ensure heartbeat settings are in `~/.clawdbot/clawdbot.json`:

```bash
# Read current config
cat ~/.clawdbot/clawdbot.json | jq '.agents.defaults.heartbeat'

# Should show:
# {
#   "every": "30m",
#   "target": "whatsapp",  (or your preferred channel)
#   "to": "+818054961566",
#   "activeHours": {
#     "start": "05:00",
#     "end": "22:00",
#     "timezone": "Asia/Tokyo"
#   }
# }
```

If heartbeat config is missing or incomplete, update:

```bash
# Backup first
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.backup.$(date +%Y%m%d_%H%M)

# Update heartbeat config (using jq)
cat ~/.clawdbot/clawdbot.json | jq '.agents.defaults.heartbeat = {
  "every": "30m",
  "activeHours": {
    "start": "05:00",
    "end": "22:00",
    "timezone": "Asia/Tokyo"
  }
}' > /tmp/clawdbot_updated.json && mv /tmp/clawdbot_updated.json ~/.clawdbot/clawdbot.json
```

---

## PHASE 6: Create Heartbeat Integration Script

Create script that Clawdbot calls for heartbeat:

```bash
cat > ~/clawd/scripts/dharmic_heartbeat.py << 'EOF'
#!/usr/bin/env python3
"""
DHARMIC CLAW Heartbeat Script
Called every 30 minutes by Clawdbot.

Reads: ~/clawd/HEARTBEAT.md for protocol
Checks: Telos alignment (the ONE check that matters)
Output: HEARTBEAT_OK (silent) or ALERT (message)
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

CLAWD_DIR = Path.home() / "clawd"
DGC_DIR = Path.home() / "DHARMIC_GODEL_CLAW"
LOG_FILE = CLAWD_DIR / "memory" / "heartbeat.log"


def log(status: str, details: str = ""):
    """Append to heartbeat log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {status} | {details}\n")


def check_core_agent() -> tuple[bool, str]:
    """Check if dharmic_agent.py responds."""
    agent_path = DGC_DIR / "core" / "dharmic_agent.py"
    
    if not agent_path.exists():
        return False, "Core agent not found"
    
    try:
        result = subprocess.run(
            ["python3", str(agent_path), "heartbeat"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, "Core agent OK"
        else:
            return False, f"Core agent error: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "Core agent timeout"
    except Exception as e:
        return False, f"Core agent exception: {str(e)[:100]}"


def check_swarm_synthesis() -> tuple[bool, str]:
    """Check if swarm synthesis is recent."""
    synthesis_path = DGC_DIR / "swarm" / "stream" / "synthesis_30min.md"
    
    if not synthesis_path.exists():
        return True, "No synthesis file (OK if swarm not running)"
    
    mtime = synthesis_path.stat().st_mtime
    age_hours = (datetime.now().timestamp() - mtime) / 3600
    
    if age_hours > 4:
        return False, f"Synthesis stale ({age_hours:.1f}h old)"
    
    return True, f"Synthesis fresh ({age_hours:.1f}h)"


def ping_healthcheck():
    """Ping external dead man's switch."""
    import os
    url = os.environ.get("HEALTHCHECK_URL", "")
    if url:
        try:
            subprocess.run(["curl", "-fsS", "-m", "10", url], 
                          capture_output=True, timeout=15)
        except:
            pass  # Don't fail heartbeat if ping fails


def main():
    alerts = []
    
    # CHECK 1: Core agent (required)
    ok, msg = check_core_agent()
    if not ok:
        alerts.append(("HIGH", msg))
    
    # CHECK 2: Swarm synthesis (optional)
    ok, msg = check_swarm_synthesis()
    if not ok:
        alerts.append(("LOW", msg))
    
    # Decision
    if not alerts:
        log("HEARTBEAT_OK")
        print("HEARTBEAT_OK")
    else:
        # Log all, alert on HIGH only
        for severity, msg in alerts:
            log(f"ALERT_{severity}", msg)
            if severity == "HIGH":
                print(f"ALERT: {msg}")
    
    # Ping dead man's switch
    ping_healthcheck()


if __name__ == "__main__":
    main()
EOF

chmod +x ~/clawd/scripts/dharmic_heartbeat.py
```

---

## PHASE 7: Test Everything

```bash
echo "=== CLAWDBOT DHARMIC CONFIG TEST ==="

echo "\n1. Cron Jobs:"
clawdbot cron list

echo "\n2. HEARTBEAT.md:"
head -20 ~/clawd/HEARTBEAT.md

echo "\n3. Mac Sleep Status:"
pmset -g | grep -E "sleep|disksleep"

echo "\n4. Heartbeat Script:"
python3 ~/clawd/scripts/dharmic_heartbeat.py

echo "\n5. Gateway Status:"
curl -s http://localhost:18789/health | head -5 || echo "Gateway not responding"

echo "\n6. Proxy Status:"
curl -s http://localhost:3456/health || echo "Proxy not running"

echo "\n=== TEST COMPLETE ==="
```

---

## PHASE 8: Final Verification

After all phases complete, verify:

```bash
# Final checklist
echo "=== FINAL VERIFICATION ==="

# Crons configured
echo "Crons:"
clawdbot cron list | grep -E "wake-sync|morning-brief|research-pulse|evening-synthesis|weekly-review"

# HEARTBEAT.md accessible
echo "\nHEARTBEAT.md exists: $(test -f ~/clawd/HEARTBEAT.md && echo YES || echo NO)"

# Sleep disabled
echo "Sleep disabled: $(pmset -g | grep -q 'sleep.*0' && echo YES || echo NO)"

# Heartbeat script works
echo "Heartbeat script: $(python3 ~/clawd/scripts/dharmic_heartbeat.py 2>&1 | head -1)"

# Gateway alive
echo "Gateway alive: $(curl -s http://localhost:18789/ > /dev/null && echo YES || echo NO)"

echo "\n=== VERIFICATION COMPLETE ==="
```

---

## SUCCESS CRITERIA

- [ ] 5 cron jobs configured (wake-sync, morning-brief, research-pulse, evening-synthesis, weekly-review)
- [ ] HEARTBEAT.md in ~/clawd/ and readable
- [ ] Mac sleep disabled (or caffeinate configured)
- [ ] Dead man's switch configured (healthchecks.io or local cron)
- [ ] Heartbeat script runs without error
- [ ] Gateway responding

---

## WHAT CLAWDBOT NOW HAS

| Component | Status | Purpose |
|-----------|--------|---------|
| **HEARTBEAT.md** | Ready | Protocol for 30-min checks |
| **5 Cron Jobs** | Configured | Scheduled touchpoints |
| **Watchdog** | Built into heartbeat | Self-observation every cycle |
| **Dead Man's Switch** | Configured | External alert if silent |
| **ONE Gate (AHIMSA)** | Applied | Simplicity over complexity |

---

## AFTER THIS — TALK TO CLAWDBOT

Once complete, open Clawdbot and say:

```
Read ~/clawd/HEARTBEAT.md

This is your heartbeat protocol. You check telos alignment every 30 minutes.
Silence is valid output. Only alert when something genuinely matters.

Confirm you understand the protocol.
```

---

## GUIDING PRINCIPLE

> **"If telos is aligned, everything else follows. If telos drifts, nothing else matters."**

The minimal heartbeat does ONE thing: check telos alignment.
Everything else derives from that.

Silence is valid. Noise serves no one.

**JSCA!**
