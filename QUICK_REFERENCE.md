# DHARMIC_CLAW Process Management - Quick Reference

## TL;DR

**Problem**: 6 Python processes doing the same thing (email, heartbeat, agent lifecycle)
**Solution**: Consolidate to 2 processes with clear separation
**Benefit**: 83% less memory, 67% fewer processes, no race conditions

---

## One-Command Migration

```bash
~/DHARMIC_GODEL_CLAW/scripts/safe_migration.sh
```

**Time**: 2 minutes | **Risk**: LOW | **Rollback**: 2 minutes

---

## Health Check

```bash
~/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh
```

Should show:
- ✓ 2 daemons running (dharmic_claw_heartbeat, clawdbot_watchdog)
- ✓ No orphans
- ✓ ~19MB total memory

---

## Kill Orphans (if needed)

```bash
~/DHARMIC_GODEL_CLAW/scripts/kill_orphans.sh
```

Safely removes redundant daemons without touching primary/watchdog.

---

## Rollback (if migration breaks something)

```bash
cp ~/DHARMIC_GODEL_CLAW/config/launchd_archive/*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist
```

---

## Monitor Logs

```bash
# Primary agent
tail -f ~/DHARMIC_GODEL_CLAW/logs/dharmic_claw_heartbeat.log

# Watchdog
tail -f ~/DHARMIC_GODEL_CLAW/logs/clawdbot_watchdog.log
```

---

## What Gets Removed

| Process | PID | Why Remove |
|---------|-----|------------|
| unified_daemon.py | 28132 | Redundant email/heartbeat |
| integrated_daemon.py | 28866, 78840 | Redundant, features unused |
| daemon.py | 76581 | Legacy, high memory, no LaunchAgent |

---

## What Stays

| Process | PID | Purpose |
|---------|-----|---------|
| dharmic_claw_heartbeat.py | 34292 | THE AGENT (Agno, email, heartbeat, DGM) |
| clawdbot_watchdog.py | 78999 | Infrastructure monitor (gateway health) |

---

## Files

| Purpose | Path |
|---------|------|
| **Full audit** | `/Users/dhyana/DHARMIC_GODEL_CLAW/PROCESS_AUDIT_REPORT.md` |
| **Summary** | `/Users/dhyana/DHARMIC_GODEL_CLAW/MIGRATION_SUMMARY.md` |
| **Diagram** | `/Users/dhyana/DHARMIC_GODEL_CLAW/ARCHITECTURE_DIAGRAM.txt` |
| **This file** | `/Users/dhyana/DHARMIC_GODEL_CLAW/QUICK_REFERENCE.md` |

---

## Scripts

| Purpose | Path |
|---------|------|
| **Automated migration** | `~/DHARMIC_GODEL_CLAW/scripts/safe_migration.sh` |
| **Health check** | `~/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh` |
| **Orphan cleanup** | `~/DHARMIC_GODEL_CLAW/scripts/kill_orphans.sh` |

---

## Next Steps

1. Run health check to confirm current state
2. Run migration script
3. Monitor logs for 24 hours
4. Verify email check-ins every 90 minutes
5. Run health check daily to detect orphans

---

**Prepared by**: SRE Engineer (Claude Code)
**Date**: 2026-02-04
**Status**: READY TO EXECUTE
