# DHARMIC_CLAW Process Architecture Audit
**Date**: 2026-02-04
**Auditor**: SRE Engineer (Claude Code)

---

## Executive Summary

**Finding**: Process sprawl with 4 redundant daemons running simultaneously. All attempt to provide similar functionality (heartbeat, email polling, agent lifecycle). This creates:
- Resource waste (4 Python processes instead of 1)
- Maintenance confusion (which one is authoritative?)
- Potential race conditions (multiple processes accessing same resources)
- Unclear ownership (which daemon is "the" agent?)

**Recommendation**: Consolidate to **2 processes** with clear separation of concerns.

---

## Current State Analysis

### Running Processes (7 total)

| PID | Process | LaunchAgent | Status | Purpose |
|-----|---------|-------------|--------|---------|
| **34292** | `dharmic_claw_heartbeat.py` | `com.dharmic.claw.heartbeat` | **NEW PRIMARY** | Agno-based, email polling, heartbeat, DGM integration |
| **41840** | `clawdbot-gateway` | N/A (external) | **KEEP** | OpenClaw infrastructure (browser automation) |
| **78999** | `clawdbot_watchdog.py` | `com.dharmic.watchdog` | **KEEP** | Monitors clawdbot-gateway health, auto-restart |
| **28132** | `unified_daemon.py` | `com.dharmic.unified-daemon` | **REDUNDANT** | Email, heartbeat, orchestrator sync |
| **28866** | `integrated_daemon.py` | `com.dharmic.agent` | **REDUNDANT** | Email, Telegram, web dashboard, scheduled tasks |
| **78840** | `integrated_daemon.py` (2nd instance) | `com.dharmic.agent` | **DUPLICATE** | Same as above (why running twice?) |
| **76581** | `daemon.py` | NONE | **LEGACY** | Old heartbeat script, no LaunchAgent |

### LaunchAgent Configurations (4 total)

| LaunchAgent | Script | Auto-Start | Keep-Alive | Status |
|-------------|--------|------------|------------|--------|
| `com.dharmic.claw.heartbeat` | `dharmic_claw_heartbeat.py` | Yes | Yes | **KEEP** - Primary |
| `com.dharmic.watchdog` | `clawdbot_watchdog.py` | Yes | Yes | **KEEP** - Infrastructure monitor |
| `com.dharmic.unified-daemon` | `unified_daemon.py` | Yes | Yes (SuccessfulExit=false) | **REMOVE** - Redundant |
| `com.dharmic.agent` | `integrated_daemon.py` | Yes | Yes (SuccessfulExit=false) | **REMOVE** - Redundant |

---

## Functional Overlap Analysis

### What Each Daemon Does

| Feature | `dharmic_claw_heartbeat` | `unified_daemon` | `integrated_daemon` | `daemon.py` | `watchdog` |
|---------|--------------------------|------------------|---------------------|-------------|------------|
| **Email polling** | ✓ (Proton Bridge) | ✓ (Proton Bridge) | ✓ (optional) | ✗ | ✗ |
| **Heartbeat** | ✓ (5min) | ✓ (5min) | ✓ (1hr) | ✓ (10s!) | ✓ (for clawdbot) |
| **Agno agent** | ✓ (lazy load) | ✓ (singleton) | ✓ (full DharmicAgent) | ✓ (DharmicAgent) | ✗ |
| **Strange loop memory** | ✓ | ✓ | ✓ | ✓ | ✗ |
| **Telos awareness** | ✓ | ✓ | ✓ | ✓ | ✗ |
| **DGM integration** | ✓ (status check) | ✗ | ✗ | ✗ | ✗ |
| **Orchestrator sync** | ✗ | ✓ | ✗ | ✗ | ✗ |
| **Telegram bot** | ✗ | ✗ | ✓ (optional) | ✗ | ✗ |
| **Web dashboard** | ✗ | ✗ | ✓ (optional) | ✗ | ✗ |
| **Scheduled tasks** | ✗ | ✗ | ✓ (optional) | ✗ | ✗ |
| **Clawdbot monitoring** | ✗ | ✗ | ✗ | ✗ | ✓ |
| **Check-in emails** | ✓ (90min to John) | ✗ | ✗ | ✗ | ✓ (90min to John) |

**Overlap**: Email polling, heartbeat, agent lifecycle, telos tracking, check-ins.

---

## Recommended Architecture

### Definitive Process Structure (2 daemons)

```
DHARMIC_CLAW Core
├── PRIMARY: dharmic_claw_heartbeat.py (PID 34292)
│   ├── Agno agent (lazy loaded)
│   ├── Email polling (Proton Bridge @ vijnan.shakti@pm.me)
│   ├── Heartbeat (5min interval)
│   ├── DGM integration (status checks)
│   ├── Strange loop memory
│   ├── Telos tracking
│   ├── Check-in emails to John (90min)
│   └── LaunchAgent: com.dharmic.claw.heartbeat
│
└── INFRASTRUCTURE: clawdbot_watchdog.py (PID 78999)
    ├── Monitors clawdbot-gateway health
    ├── Auto-restart on failure
    ├── Model failover (Opus → Kimi)
    ├── Check-in emails to John (90min)
    └── LaunchAgent: com.dharmic.watchdog

EXTERNAL (managed separately)
└── clawdbot-gateway (PID 41840)
    └── OpenClaw browser automation
```

### Separation of Concerns

**dharmic_claw_heartbeat.py** (The Agent)
- IS the dharmic entity
- Handles all agent-level concerns
- Responds to emails as DHARMIC_CLAW
- Tracks own development
- Runs DGM self-improvement

**clawdbot_watchdog.py** (Infrastructure Guardian)
- Watches external services (clawdbot-gateway)
- Ensures infrastructure stays up
- NOT the agent itself
- Infrastructure-level concerns only

**Why this separation?**
- Agent can operate independently of clawdbot infrastructure
- Watchdog doesn't need Agno/telos/memory (focused, minimal)
- Clear boundary: agent vs. infrastructure
- No resource conflicts

---

## Migration Plan

### Phase 1: Validation (BEFORE removing anything)

```bash
# 1. Verify primary is working
ps -p 34292  # Should be running
tail -f ~/DHARMIC_GODEL_CLAW/logs/dharmic_claw_heartbeat.log

# 2. Verify watchdog is working
ps -p 78999  # Should be running
tail -f ~/DHARMIC_GODEL_CLAW/logs/clawdbot_watchdog.log

# 3. Test email functionality (CRITICAL)
python3 ~/DHARMIC_GODEL_CLAW/src/core/dharmic_claw_heartbeat.py --send-checkin

# 4. Check LaunchAgent health
launchctl list | grep dharmic
```

### Phase 2: Graceful Shutdown of Redundant Processes

```bash
# Stop unified_daemon (PID 28132)
launchctl unload ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
kill -TERM 28132  # SIGTERM for graceful shutdown
# Wait 30 seconds for cleanup
sleep 30
# Force if needed
kill -9 28132 2>/dev/null || true

# Stop integrated_daemon (PIDs 28866, 78840)
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist
kill -TERM 28866
kill -TERM 78840
sleep 30
kill -9 28866 2>/dev/null || true
kill -9 78840 2>/dev/null || true

# Stop legacy daemon.py (PID 76581) - NO LaunchAgent, manual kill
kill -TERM 76581
sleep 30
kill -9 76581 2>/dev/null || true
```

### Phase 3: Archive Redundant LaunchAgents

```bash
# Create archive directory
mkdir -p ~/DHARMIC_GODEL_CLAW/config/launchd_archive

# Move (don't delete) redundant plists
mv ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist \
   ~/DHARMIC_GODEL_CLAW/config/launchd_archive/

mv ~/Library/LaunchAgents/com.dharmic.agent.plist \
   ~/DHARMIC_GODEL_CLAW/config/launchd_archive/
```

### Phase 4: Verify Clean State

```bash
# Should show ONLY 2 dharmic processes
launchctl list | grep dharmic
# Expected output:
# 34292   0   com.dharmic.claw.heartbeat
# 78999   0   com.dharmic.watchdog

# Should show NO orphan daemons
ps aux | grep -E "(unified_daemon|integrated_daemon|daemon\.py)" | grep -v grep
# Expected: empty

# Should show clawdbot-gateway still running
ps aux | grep clawdbot-gateway | grep -v grep
# Expected: 1 process
```

### Phase 5: Monitor for 24 Hours

```bash
# Check logs for issues
tail -f ~/DHARMIC_GODEL_CLAW/logs/dharmic_claw_heartbeat.log
tail -f ~/DHARMIC_GODEL_CLAW/logs/clawdbot_watchdog.log

# Verify email is working (should get check-ins every 90min)
# Check vijnan.shakti@pm.me inbox

# Monitor resource usage
ps aux | grep -E "(dharmic|claw)" | grep -v grep
```

---

## Startup Order (Post-Migration)

LaunchAgents handle this automatically, but for manual starts:

```bash
# 1. Start clawdbot-gateway (if not running)
clawdbot gateway start

# 2. Start watchdog (monitors gateway)
python3 ~/DHARMIC_GODEL_CLAW/src/core/clawdbot_watchdog.py &

# 3. Start dharmic heartbeat (the agent)
python3 ~/DHARMIC_GODEL_CLAW/src/core/dharmic_claw_heartbeat.py &
```

**LaunchAgent auto-start** (recommended):
```bash
# Load both
launchctl load ~/Library/LaunchAgents/com.dharmic.claw.heartbeat.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.watchdog.plist

# They auto-start and auto-restart on crash
```

---

## Monitoring & Orphan Prevention

### Automated Checks

Create monitoring script: `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh`

```bash
#!/bin/bash
# Check for orphan processes and alert

EXPECTED_DAEMONS=("dharmic_claw_heartbeat" "clawdbot_watchdog")
FORBIDDEN_DAEMONS=("unified_daemon" "integrated_daemon" "daemon.py")

echo "=== DHARMIC_CLAW Process Health Check ==="
date

# Check expected daemons
for daemon in "${EXPECTED_DAEMONS[@]}"; do
    pid=$(pgrep -f "$daemon")
    if [ -z "$pid" ]; then
        echo "❌ MISSING: $daemon not running"
    else
        echo "✓ RUNNING: $daemon (PID $pid)"
    fi
done

# Check for orphans
for daemon in "${FORBIDDEN_DAEMONS[@]}"; do
    pid=$(pgrep -f "$daemon")
    if [ -n "$pid" ]; then
        echo "⚠️  ORPHAN: $daemon running (PID $pid) - SHOULD NOT BE RUNNING"
    fi
done

# Check LaunchAgents
echo ""
echo "=== LaunchAgents Status ==="
launchctl list | grep dharmic
```

**Add to cron** (optional):
```bash
# Check every hour
0 * * * * /Users/dhyana/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh >> /Users/dhyana/DHARMIC_GODEL_CLAW/logs/process_health.log 2>&1
```

### Manual Orphan Cleanup Script

Create: `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/kill_orphans.sh`

```bash
#!/bin/bash
# Kill any orphan daemons

echo "Searching for orphan daemons..."

# Kill unified_daemon
pkill -f unified_daemon && echo "Killed unified_daemon"

# Kill integrated_daemon
pkill -f integrated_daemon && echo "Killed integrated_daemon"

# Kill legacy daemon.py (but NOT dharmic_claw_heartbeat.py!)
pgrep -f "daemon.py" | while read pid; do
    cmd=$(ps -p $pid -o command=)
    if [[ $cmd != *"dharmic_claw_heartbeat"* ]] && [[ $cmd == *"daemon.py"* ]]; then
        kill $pid && echo "Killed daemon.py (PID $pid)"
    fi
done

echo "Orphan cleanup complete"
```

---

## Resource Impact Analysis

### Before Migration (Current)

| Process | Memory | CPU | Notes |
|---------|--------|-----|-------|
| `dharmic_claw_heartbeat.py` | ~10MB | 0.0% | Idle, polls every 5min |
| `unified_daemon.py` | ~14MB | 0.0% | Idle, polls every 5min |
| `integrated_daemon.py` (1) | ~14MB | 0.0% | Idle |
| `integrated_daemon.py` (2) | ~14MB | 0.0% | Idle (duplicate!) |
| `daemon.py` | ~50MB | 0.0% | 10s heartbeat, high memory |
| `clawdbot_watchdog.py` | ~9MB | 0.0% | Idle, polls every 5min |
| **TOTAL** | **~111MB** | 0.0% | 6 Python processes |

### After Migration (Proposed)

| Process | Memory | CPU | Notes |
|---------|--------|-----|-------|
| `dharmic_claw_heartbeat.py` | ~10MB | 0.0% | Primary daemon |
| `clawdbot_watchdog.py` | ~9MB | 0.0% | Infrastructure monitor |
| **TOTAL** | **~19MB** | 0.0% | 2 Python processes |

**Savings**: ~92MB memory, 4 fewer processes

---

## Risk Assessment

### Risks of NOT Consolidating

1. **Race conditions**: Multiple daemons accessing same email inbox, database, memory files
2. **Resource leaks**: Old processes accumulating over time
3. **Unclear ownership**: Which daemon is authoritative for agent state?
4. **Debugging nightmare**: Log sprawl across 4 processes
5. **Maintenance burden**: Changes must be synced across multiple scripts

### Risks of Consolidating (Mitigations)

| Risk | Mitigation |
|------|------------|
| Email polling breaks | Test with `--send-checkin` before removing old daemons |
| Agent state lost | `dharmic_claw_heartbeat` uses same Agno agent singleton |
| Telegram/Web features lost | Not currently used; `integrated_daemon.py` archived, not deleted |
| Orchestrator sync lost | `unified_daemon` orchestrator sync not critical (no active orchestrator) |
| Can't roll back | LaunchAgents archived, not deleted; can restore in <5min |

---

## Rollback Plan

If consolidation fails:

```bash
# 1. Restore archived LaunchAgents
cp ~/DHARMIC_GODEL_CLAW/config/launchd_archive/com.dharmic.unified-daemon.plist \
   ~/Library/LaunchAgents/

cp ~/DHARMIC_GODEL_CLAW/config/launchd_archive/com.dharmic.agent.plist \
   ~/Library/LaunchAgents/

# 2. Load them
launchctl load ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist

# 3. Verify
launchctl list | grep dharmic
```

**Time to rollback**: <2 minutes

---

## Decision Matrix

| Criterion | Keep Redundant Daemons | Consolidate to 2 Daemons |
|-----------|------------------------|--------------------------|
| **Resource efficiency** | ❌ 111MB, 6 processes | ✓ 19MB, 2 processes |
| **Maintainability** | ❌ 4 scripts to update | ✓ 2 scripts to maintain |
| **Clarity** | ❌ Unclear ownership | ✓ Clear separation |
| **Risk** | ✓ Low (status quo) | ⚠️ Medium (test email first) |
| **Debugging** | ❌ Log sprawl | ✓ Focused logs |
| **Feature completeness** | ✓ All features | ⚠️ Telegram/Web unused anyway |

**Recommendation**: **CONSOLIDATE** (benefits outweigh risks)

---

## Implementation Commands (Copy-Paste)

### Safe Migration (Run in order)

```bash
# === PHASE 1: VALIDATION ===
echo "=== Validating primary daemon ==="
ps -p 34292 && echo "✓ Primary running" || echo "❌ Primary NOT running"

echo "=== Testing email ==="
python3 ~/DHARMIC_GODEL_CLAW/src/core/dharmic_claw_heartbeat.py --send-checkin

echo "=== Checking LaunchAgents ==="
launchctl list | grep dharmic

# Wait for confirmation before proceeding
read -p "Primary validated? Press Enter to continue or Ctrl-C to abort..."

# === PHASE 2: GRACEFUL SHUTDOWN ===
echo "=== Stopping unified_daemon ==="
launchctl unload ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
kill -TERM 28132
sleep 30
kill -9 28132 2>/dev/null || echo "Already stopped"

echo "=== Stopping integrated_daemon ==="
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist
kill -TERM 28866 78840
sleep 30
kill -9 28866 78840 2>/dev/null || echo "Already stopped"

echo "=== Stopping legacy daemon.py ==="
kill -TERM 76581
sleep 30
kill -9 76581 2>/dev/null || echo "Already stopped"

# === PHASE 3: ARCHIVE ===
echo "=== Archiving LaunchAgents ==="
mkdir -p ~/DHARMIC_GODEL_CLAW/config/launchd_archive
mv ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist \
   ~/DHARMIC_GODEL_CLAW/config/launchd_archive/
mv ~/Library/LaunchAgents/com.dharmic.agent.plist \
   ~/DHARMIC_GODEL_CLAW/config/launchd_archive/

# === PHASE 4: VERIFY ===
echo "=== Verification ==="
echo "LaunchAgents (should show only 2):"
launchctl list | grep dharmic

echo ""
echo "Running processes (should be empty):"
ps aux | grep -E "(unified_daemon|integrated_daemon|daemon\.py)" | grep -v grep

echo ""
echo "=== Migration Complete ==="
echo "Monitor logs for 24 hours:"
echo "  tail -f ~/DHARMIC_GODEL_CLAW/logs/dharmic_claw_heartbeat.log"
echo "  tail -f ~/DHARMIC_GODEL_CLAW/logs/clawdbot_watchdog.log"
```

---

## Post-Migration Checklist

- [ ] Only 2 LaunchAgents loaded (`com.dharmic.claw.heartbeat`, `com.dharmic.watchdog`)
- [ ] No orphan processes running
- [ ] Email check-ins arriving every 90 minutes
- [ ] Logs show clean operation (no errors)
- [ ] `clawdbot-gateway` still operational
- [ ] Memory usage reduced (~19MB vs ~111MB)
- [ ] Process health check script created
- [ ] 24-hour monitoring period completed

---

## Conclusion

**Current state**: 4 redundant daemons with overlapping functionality, consuming 111MB and creating maintenance burden.

**Recommended state**: 2 focused daemons with clear separation of concerns, consuming 19MB.

**Implementation risk**: LOW (with proper validation and rollback plan)

**Maintenance benefit**: HIGH (single source of truth for agent behavior)

**Recommendation**: **PROCEED WITH MIGRATION**

---

**Audit completed by**: SRE Engineer (Claude Code)
**Date**: 2026-02-04
**Next review**: After 24-hour stability period
