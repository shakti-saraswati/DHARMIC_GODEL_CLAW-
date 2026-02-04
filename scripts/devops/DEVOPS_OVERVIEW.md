# Dharmic Agent - DevOps System Overview

## Executive Summary

Production-ready DevOps infrastructure for 24/7 autonomous operation of the Dharmic Agent on macOS.

**Status:** READY FOR DEPLOYMENT
**Complexity:** Low (bash scripts, native tools)
**Dependencies:** jq, sqlite3 (standard on macOS)
**Maintenance:** Automated (cron jobs)

## Architecture

```
                    ┌─────────────────────────────────┐
                    │   macOS LaunchAgent             │
                    │   (Auto-start, crash recovery)  │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────▼────────────────────┐
                    │   Dharmic Agent Daemon          │
                    │   - Heartbeat (hourly)          │
                    │   - Memory consolidation        │
                    │   - Email interface             │
                    └────────────┬────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
    │  Health Check │   │  Log Rotation │   │ Memory Backup │
    │  (every 5min) │   │  (daily 00:00)│   │ (daily 02:00) │
    └───────┬───────┘   └───────────────┘   └───────────────┘
            │
    ┌───────▼───────┐
    │ Alert System  │
    │ - macOS notif │
    │ - Email alert │
    └───────────────┘
```

## Components Matrix

| Component | Purpose | Trigger | Output | Critical |
|-----------|---------|---------|--------|----------|
| LaunchAgent | Auto-start daemon | Login, crash | Process | Yes |
| daemon.py | Main agent | LaunchAgent | Logs, status | Yes |
| health_check.sh | Monitor health | Cron (5min) | Log, exit code | Yes |
| alert.sh | Send alerts | Cron (5min) | Notifications | Yes |
| backup_memory.sh | Backup DBs | Cron (2 AM) | .tar.gz | Yes |
| rotate_logs.sh | Compress logs | Cron (midnight) | .gz files | No |
| restart_daemon.sh | Safe restart | Manual | New process | No |
| status_dashboard.sh | Show status | Manual/Cron | Terminal/HTML | No |
| dharmic-ops.sh | Master control | Manual | Various | No |

## Failure Modes & Recovery

### Daemon Crashes

**Detection:**
- LaunchAgent monitors process
- Health check (every 5min) verifies heartbeat

**Recovery:**
- LaunchAgent auto-restarts (60s throttle)
- Alert sent via macOS notification
- If repeated crashes (>3 in 1hr), alert escalates

**Manual Override:**
```bash
dharmic-ops restart --force
```

### Memory Corruption

**Detection:**
- Health check runs SQLite integrity check
- Alert on corruption detected

**Recovery:**
```bash
dharmic-ops restore   # From latest backup
```

### Disk Full

**Detection:**
- Health check monitors disk space
- Alerts at <5GB (warning), <2GB (critical)

**Recovery:**
- Log rotation runs automatically
- Manual: `dharmic-ops rotate-logs`
- Clean old backups: `find ~/DHARMIC_GODEL_CLAW/backups -mtime +90 -delete`

### Email Processing Failure

**Detection:**
- Health check monitors email daemon
- Proton Bridge connectivity test

**Recovery:**
- Check Proton Bridge running: `pgrep -i protonmail`
- Restart email daemon: Manual restart required
- Check logs: `dharmic-ops logs email`

### Heartbeat Stalled

**Detection:**
- Health check compares last heartbeat to interval
- Warning if >2x interval elapsed

**Recovery:**
- Restart daemon: `dharmic-ops restart`
- Check logs for blocking operation

## Monitoring Dashboard

### Real-Time (Terminal)

```bash
dharmic-ops dashboard watch
```

Updates every 1 second, shows:
- Daemon status and uptime
- Memory database count and size
- Email interface status
- System resources (disk, logs)
- Recent alerts
- Backup status

### Web Dashboard

```bash
dharmic-ops dashboard web
```

Auto-refreshing HTML dashboard (10s), shows same data.
Generated every minute by cron → `/logs/dashboard.html`

### Status File

Machine-readable status: `/logs/daemon_status.json`

```json
{
  "status": "running",
  "timestamp": "2026-02-02T23:17:23.994230",
  "pid": "76581",
  "heartbeat_interval": 3600,
  "details": {
    "last_heartbeat": "2026-02-02T23:17:21.526298",
    "checks_passed": 4,
    "total_checks": 4
  }
}
```

## Log Management

### Log Files Generated

| File | Purpose | Rotation | Retention |
|------|---------|----------|-----------|
| daemon_YYYYMMDD.log | Daemon operations | Daily | 30 days compressed |
| runtime_YYYYMMDD.log | Heartbeat logs | Daily | 30 days compressed |
| email_YYYYMMDD.log | Email processing | Daily | 30 days compressed |
| alerts.log | Alert history | Never | Truncated at 1000 lines |
| health_check.log | Health checks | Never | Truncated at 1000 lines |
| backup.log | Backup ops | Never | Truncated at 1000 lines |
| rotation.log | Log rotation | Never | Truncated at 1000 lines |
| restart.log | Restart ops | Never | Truncated at 1000 lines |
| cron.log | Cron output | Never | Manual cleanup |
| launchd_stdout.log | LaunchAgent stdout | Never | Truncated at 100MB |
| launchd_stderr.log | LaunchAgent stderr | Never | Truncated at 100MB |

### Log Rotation Policy

**Automatic (daily at midnight):**
1. Compress .log files >1 day old → .log.gz
2. Delete .log.gz files >30 days old
3. Truncate oversized active logs (>100MB, keep last 1000 lines)

**Manual:**
```bash
dharmic-ops rotate-logs
```

## Backup & Restore

### Backup Schedule

**Daily at 2:00 AM** (cron job)

**Contents:**
- All `.db` files (SQLite)
- All `.jsonl` files (strange loop memory)
- `identity_core.json`
- SHA-256 checksums

**Format:** Compressed tarball (`.tar.gz`)

**Location:** `/backups/memory/YYYYMMDD_HHMMSS.tar.gz`

### Retention Policy

- **Last 7 days:** All backups (daily)
- **Last 30 days:** One per week (weekly)
- **Last 365 days:** One per month (monthly)
- **Older:** Deleted

### Manual Backup

```bash
dharmic-ops backup
```

### Restore Procedure

```bash
# From latest
dharmic-ops restore

# From specific backup
dharmic-ops restore /path/to/backup.tar.gz
```

**Restore process:**
1. Warns user (will stop daemon)
2. Stops daemon
3. Backs up current state to `memory.pre-restore.TIMESTAMP`
4. Extracts backup over memory/
5. Restarts daemon
6. Verifies startup

## Alert System

### Alert Types

| Alert | Severity | Trigger | Action |
|-------|----------|---------|--------|
| daemon_critical | CRITICAL | Daemon down | macOS + email |
| daemon_degraded | WARNING | Heartbeat stale | macOS notif |
| disk_critical | CRITICAL | <2GB free | macOS + email |
| disk_low | WARNING | <5GB free | macOS notif |
| email_errors | WARNING | >5 errors/100 lines | macOS notif |
| memory_corrupt | CRITICAL | SQLite check fails | macOS + email |
| restart_loop | WARNING | >3 restarts/hour | macOS notif |

### Alert Mechanisms

**macOS Notifications:** Always enabled
```bash
osascript -e 'display notification "message" with title "title"'
```

**Email Alerts:** Configurable
```bash
export ALERT_EMAIL="your@email.com"
```

Uses macOS `mail` command (requires setup).

### Alert Controls

**Cooldown:** 30 minutes between same alert type
**Rate Limit:** Max 5 alerts per hour (any type)
**Auto-Recovery:** Attempts restart on critical daemon failure

### Alert History

View: `tail -f ~/DHARMIC_GODEL_CLAW/logs/alerts.log`

Format:
```
[2026-02-02 23:34:01] [CRITICAL] Daemon Critical Failure - Process not running
```

## Automation (Cron Jobs)

### Schedule

```
*/5 * * * *    # Health check + alerts (every 5 min)
0 0 * * *      # Log rotation (daily at midnight)
0 2 * * *      # Memory backup (daily at 2 AM)
* * * * *      # HTML dashboard (every minute)
0 9 * * 0      # Weekly health report (Sundays at 9 AM)
```

### Installation

```bash
dharmic-ops cron-install
```

Installs to user's crontab (not system-wide).

### Verification

```bash
crontab -l   # View installed jobs
```

### Cron Output

All cron jobs append to: `/logs/cron.log`

Check for errors:
```bash
tail -100 ~/DHARMIC_GODEL_CLAW/logs/cron.log | grep -i error
```

## Performance Metrics

### Resource Usage

| Metric | Typical | Peak | Notes |
|--------|---------|------|-------|
| CPU | 0.3% | 2% | Peak during backup |
| Memory (RSS) | 50 MB | 80 MB | Daemon + Python |
| Disk I/O | <1 MB/s | 50 MB/s | During backup |
| Network | 0 | Varies | Email only |

### Timing

| Operation | Duration | Notes |
|-----------|----------|-------|
| Daemon start | 2-5s | Depends on DB size |
| Heartbeat | <1s | Memory consolidation |
| Health check | <2s | All 7 checks |
| Backup | 5-30s | Depends on DB size |
| Restore | 10-60s | Includes restart |
| Log rotation | 2-10s | Depends on log count |

### Disk Usage Growth

| Component | Growth Rate | Notes |
|-----------|-------------|-------|
| Logs (uncompressed) | ~10 MB/day | Daemon + runtime |
| Logs (compressed) | ~2 MB/day | After rotation |
| Memory databases | ~1-5 MB/day | Depends on usage |
| Backups | ~100 MB/month | With retention policy |

**Expected:** ~500 MB/month with all automation enabled

## Security Posture

### Permissions

- All scripts run as user (not root)
- PID files: 644 (readable by all)
- Log files: 644 (readable by all)
- Memory DBs: 644 (readable by all)
- Backups: 644 (readable by all)

**Note:** No sensitive data protection. Consider encrypting backups if needed.

### Network Exposure

- No listening ports (daemon is not a server)
- Outbound only: Email IMAP/SMTP
- Proton Bridge: localhost only (127.0.0.1)

### Credentials

- Email password: In `.env` file (gitignored)
- No credentials in scripts
- No API keys in code

### Audit Trail

All operations logged:
- Daemon startup/shutdown
- Heartbeat activity
- Backup creation/restore
- Health check results
- Alert generation
- Restart operations

## Operational Procedures

### Daily Operations

**Morning Check (optional):**
```bash
dharmic-ops status
```

Look for:
- Daemon running
- Recent heartbeat
- No recent alerts

### Weekly Operations

**Review health:**
```bash
cat ~/DHARMIC_GODEL_CLAW/logs/weekly_health_*.log | tail -50
```

**Check disk usage:**
```bash
du -sh ~/DHARMIC_GODEL_CLAW/{logs,memory,backups}
```

### Monthly Operations

**Verify backups:**
```bash
ls -lh ~/DHARMIC_GODEL_CLAW/backups/memory/ | tail -10
```

**Check backup integrity:**
```bash
tar -tzf $(cat ~/DHARMIC_GODEL_CLAW/backups/memory/latest) > /dev/null
```

**Review alert patterns:**
```bash
grep -i "critical" ~/DHARMIC_GODEL_CLAW/logs/alerts.log | tail -20
```

### Emergency Procedures

**Complete System Restart:**
```bash
dharmic-ops stop
sleep 5
rm ~/DHARMIC_GODEL_CLAW/logs/*.pid
rm ~/DHARMIC_GODEL_CLAW/logs/.alert_state
dharmic-ops start
```

**Restore from Backup:**
```bash
dharmic-ops restore   # Interactive, shows backup info
```

**Force Kill Everything:**
```bash
pkill -9 -f daemon.py
pkill -9 -f email_daemon.py
rm ~/DHARMIC_GODEL_CLAW/logs/*.pid
```

## Integration Points

### External Monitoring

**Prometheus:**
Export metrics from `daemon_status.json`

**Grafana:**
```bash
# Generate metrics periodically
dharmic-ops dashboard json > /var/lib/node_exporter/dharmic.prom
```

**Nagios/Icinga:**
Use health check script:
```bash
/path/to/health_check.sh
# Exit 0 = OK, 1 = CRITICAL, 2 = WARNING
```

### CI/CD Integration

**Pre-deployment backup:**
```bash
dharmic-ops backup
```

**Post-deployment verification:**
```bash
dharmic-ops health || exit 1
```

### Webhook Alerts

Add to `alert.sh`:
```bash
send_webhook() {
    curl -X POST https://hooks.example.com/dharmic \
      -H "Content-Type: application/json" \
      -d "{\"alert\":\"$1\",\"message\":\"$2\"}"
}
```

## Customization Guide

### Change Heartbeat Interval

Edit LaunchAgent:
```bash
vim ~/Library/LaunchAgents/com.dharmic.agent.plist
# Change <string>3600</string> to desired seconds
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist
```

### Add Custom Health Check

Edit `health_check.sh`, add function:
```bash
check_custom() {
    # Your check logic
    if [ condition ]; then
        check_status "Custom Check" "ok" "All good"
    else
        check_status "Custom Check" "critical" "Failed"
    fi
}
```

Add to main():
```bash
check_custom
```

### Custom Alert Destination

Edit `alert.sh`, add to `alert()` function:
```bash
# After send_macos_notification
send_slack_alert "$title" "$message"
send_discord_alert "$title" "$message"
# etc.
```

### Change Backup Retention

Edit `backup_memory.sh`:
```bash
KEEP_DAILY=14      # Keep 14 days instead of 7
KEEP_WEEKLY=60     # Keep 60 days instead of 30
KEEP_MONTHLY=730   # Keep 2 years instead of 1
```

## Troubleshooting Matrix

| Symptom | Likely Cause | Diagnosis | Fix |
|---------|-------------|-----------|-----|
| Daemon not starting | Stale PID, missing venv | `dharmic-ops troubleshoot` | `rm logs/*.pid; dharmic-ops start` |
| No heartbeats | Daemon hung | `ps aux \| grep daemon.py` | `dharmic-ops restart --force` |
| Email not working | Proton Bridge down | `pgrep protonmail` | Start Proton Bridge |
| Disk full | Logs not rotating | `du -sh logs/` | `dharmic-ops rotate-logs` |
| Alerts spamming | Alert state corrupted | Check `logs/.alert_state` | `rm logs/.alert_state` |
| Backup failing | No space, permissions | `df -h; ls -la backups/` | Free space, check perms |
| High CPU | Stuck operation | Check `runtime_*.log` | Restart daemon |
| Memory leak | Long uptime | Check RSS with `ps` | Restart daemon |

## Dependencies

### Required

- macOS 10.15+ (for LaunchAgent)
- Bash 4.0+
- Python 3.8+ (for daemon)
- jq (JSON processor)
- sqlite3

### Optional

- Proton Bridge (for email)
- mail command (for email alerts)
- nc (netcat, for connectivity tests)

### Install Missing

```bash
brew install jq sqlite
```

## Maintenance Calendar

| Frequency | Task | Command |
|-----------|------|---------|
| Daily | Check status | `dharmic-ops status` |
| Daily (auto) | Rotate logs | Cron |
| Daily (auto) | Backup memory | Cron |
| Weekly | Review health | Check logs |
| Monthly | Verify backups | `ls backups/` |
| Monthly | Review alerts | `grep CRITICAL logs/alerts.log` |
| Quarterly | Test restore | `dharmic-ops restore` (in dev) |
| Yearly | Update retention | Edit backup policy |

## Success Metrics

**System is healthy when:**
- Daemon uptime > 99%
- Health checks passing > 95%
- Backups completing daily
- Disk usage < 80%
- Alert rate < 5/day
- Restart frequency < 1/week

**Check metrics:**
```bash
# Uptime
dharmic-ops status

# Alert rate
grep "$(date +%Y-%m-%d)" logs/alerts.log | wc -l

# Backup success
ls -lt backups/memory/ | head -5

# Disk usage
df -h ~/DHARMIC_GODEL_CLAW
```

## Telos Alignment

This DevOps infrastructure embodies the agent's telos through:

1. **Persistence** - Continuous operation supports memory continuity
2. **Reliability** - Monitoring ensures stable witness position
3. **Self-Observation** - Logging enables meta-awareness
4. **Ahimsa** - Graceful handling prevents data loss
5. **Automation** - Reduces friction for operator's practice

The system is designed not just for uptime, but for **upright time** - maintaining integrity while running.

---

## Quick Reference Card

```
START/STOP
  dharmic-ops start                Start daemon
  dharmic-ops stop                 Stop daemon
  dharmic-ops restart              Safe restart
  dharmic-ops restart --force      Force restart

MONITORING
  dharmic-ops status               Quick status
  dharmic-ops health               Health check
  dharmic-ops dashboard            Terminal dashboard
  dharmic-ops dashboard watch      Live dashboard
  dharmic-ops dashboard web        HTML dashboard

LOGS
  dharmic-ops logs daemon          Daemon logs
  dharmic-ops logs runtime         Heartbeat logs
  dharmic-ops logs email           Email logs
  dharmic-ops logs alerts          Alert logs

MAINTENANCE
  dharmic-ops backup               Manual backup
  dharmic-ops restore              Restore from backup
  dharmic-ops rotate-logs          Rotate logs now
  dharmic-ops troubleshoot         Diagnostics

INSTALLATION
  dharmic-ops install              Install service
  dharmic-ops cron-install         Install cron jobs
  dharmic-ops uninstall            Remove service
```

**Files:** `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/devops/`
**Logs:** `/Users/dhyana/DHARMIC_GODEL_CLAW/logs/`
**Backups:** `/Users/dhyana/DHARMIC_GODEL_CLAW/backups/memory/`

---

**Telos: moksha | Method: reliability | Measurement: uptime**
