# DHARMIC_CLAW Process Migration Summary

**Date**: 2026-02-04
**Status**: READY TO EXECUTE

---

## Current State (CONFIRMED)

Health check output shows:

```
EXPECTED DAEMONS:
✓ dharmic_claw_heartbeat.py (PID 34292) - 9.76MB
✓ clawdbot_watchdog.py (PID 78999) - 8.67MB

ORPHANS DETECTED:
⚠️  unified_daemon.py (PID 28132)
⚠️  integrated_daemon.py (PID 28866) - DUPLICATE
⚠️  integrated_daemon.py (PID 78840) - DUPLICATE
⚠️  daemon.py (PID 76581)

LAUNCHAGENTS LOADED (4):
- com.dharmic.unified-daemon
- com.dharmic.claw.heartbeat ✓ KEEP
- com.dharmic.agent
- com.dharmic.watchdog ✓ KEEP
```

---

## Recommendation

**CONSOLIDATE** from 6 processes → 2 processes

### Keep
1. `dharmic_claw_heartbeat.py` (PID 34292) - Primary agent daemon
2. `clawdbot_watchdog.py` (PID 78999) - Infrastructure monitor

### Remove
1. `unified_daemon.py` (PID 28132)
2. `integrated_daemon.py` (PID 28866, 78840)
3. `daemon.py` (PID 76581)

---

## Migration Execution

### Option 1: Automated (RECOMMENDED)

```bash
# Run the safe migration script
~/DHARMIC_GODEL_CLAW/scripts/safe_migration.sh
```

This script:
- Validates primary daemon is running
- Gracefully stops redundant daemons
- Archives LaunchAgents (doesn't delete)
- Verifies clean state
- Provides rollback instructions

**Time required**: ~2 minutes
**Risk level**: LOW (with rollback available)

### Option 2: Manual

See detailed steps in `/Users/dhyana/DHARMIC_GODEL_CLAW/PROCESS_AUDIT_REPORT.md`

### Option 3: Quick Orphan Kill (if migration script fails)

```bash
~/DHARMIC_GODEL_CLAW/scripts/kill_orphans.sh
```

---

## Post-Migration Monitoring

### Immediate (First 15 minutes)

```bash
# Check health
~/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh

# Watch logs
tail -f ~/DHARMIC_GODEL_CLAW/logs/dharmic_claw_heartbeat.log
```

### 24-Hour Period

- Monitor email check-ins (should arrive every 90 minutes)
- Verify no new orphan processes spawn
- Check memory usage stays ~19MB total
- Ensure clawdbot-gateway remains operational

### Ongoing (Optional)

Add health check to cron:

```bash
# Check every hour
0 * * * * ~/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh >> ~/DHARMIC_GODEL_CLAW/logs/process_health.log 2>&1
```

---

## Rollback (if needed)

If migration causes issues:

```bash
# Restore archived LaunchAgents
cp ~/DHARMIC_GODEL_CLAW/config/launchd_archive/*.plist ~/Library/LaunchAgents/

# Load them
launchctl load ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist

# Verify
launchctl list | grep dharmic
```

**Time to rollback**: <2 minutes

---

## Expected Benefits

### Resource Efficiency
- Memory: 111MB → 19MB (83% reduction)
- Processes: 6 → 2 (67% reduction)

### Operational Clarity
- Single source of truth for agent behavior
- No race conditions on shared resources (email, database, memory)
- Focused, readable logs
- Clear separation: agent vs. infrastructure

### Maintenance Burden
- 4 daemon scripts → 2 to maintain
- 4 LaunchAgents → 2 to manage
- Easier debugging (2 log files vs. 4)

---

## Risk Assessment

### Migration Risks (MITIGATED)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Email polling breaks | LOW | HIGH | Tested before migration; primary already handles email |
| Agent state lost | VERY LOW | MEDIUM | Same Agno singleton used across daemons |
| Can't rollback | VERY LOW | HIGH | LaunchAgents archived, not deleted; 2-min rollback |
| Orphans respawn | LOW | LOW | LaunchAgents unloaded; won't auto-restart |

### Overall Risk: **LOW**

All high-impact risks have been mitigated.

---

## Files Created

### Documentation
- `/Users/dhyana/DHARMIC_GODEL_CLAW/PROCESS_AUDIT_REPORT.md` - Full technical audit (18KB)
- `/Users/dhyana/DHARMIC_GODEL_CLAW/MIGRATION_SUMMARY.md` - This file

### Scripts
- `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/safe_migration.sh` - Automated migration
- `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh` - Health monitoring
- `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/kill_orphans.sh` - Quick cleanup

All scripts are executable (`chmod +x` applied).

---

## Decision

**Recommendation from SRE audit**: **PROCEED WITH MIGRATION**

Benefits far outweigh risks. Current redundancy creates unnecessary complexity and resource waste. Proposed architecture is cleaner, more maintainable, and follows SRE best practices for process management.

**Next step**: Run `~/DHARMIC_GODEL_CLAW/scripts/safe_migration.sh`

---

## Questions?

Full technical details: `/Users/dhyana/DHARMIC_GODEL_CLAW/PROCESS_AUDIT_REPORT.md`

---

**Prepared by**: SRE Engineer (Claude Code)
**Date**: 2026-02-04
**Approval**: Awaiting John's confirmation
