# Dharmic Agent - Production DevOps Setup

Complete production-ready infrastructure for running the Dharmic Agent 24/7 on macOS.

## Features

- **Auto-start on login** via macOS LaunchAgent
- **Automatic crash recovery** with exponential backoff
- **Health monitoring** with macOS notifications and email alerts
- **Automated log rotation** to prevent disk space issues
- **Daily memory backups** with smart retention policy
- **Status dashboard** (terminal and web views)
- **Safe restart** procedures with cleanup
- **Cron jobs** for scheduled maintenance

## Quick Start

### 1. One-Command Setup

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/scripts/devops
./dharmic-ops.sh install
./dharmic-ops.sh cron-install
```

This will:
- Install the daemon as a macOS LaunchAgent
- Set up auto-start on login
- Install cron jobs for monitoring and backups

### 2. Verify Installation

```bash
./dharmic-ops.sh status
```

## Master Control Script

The `dharmic-ops.sh` script is your unified interface:

```bash
# Service management
./dharmic-ops.sh start           # Start daemon
./dharmic-ops.sh stop            # Stop daemon
./dharmic-ops.sh restart         # Safe restart with cleanup
./dharmic-ops.sh status          # Show status

# Monitoring
./dharmic-ops.sh health          # Run health check
./dharmic-ops.sh dashboard       # Terminal dashboard
./dharmic-ops.sh dashboard web   # HTML dashboard (auto-opens)
./dharmic-ops.sh dashboard watch # Live updating dashboard

# Logs
./dharmic-ops.sh logs daemon     # Tail daemon logs
./dharmic-ops.sh logs runtime    # Tail runtime logs
./dharmic-ops.sh logs email      # Tail email logs
./dharmic-ops.sh logs alerts     # Tail alert logs

# Maintenance
./dharmic-ops.sh backup          # Manual backup
./dharmic-ops.sh restore         # Restore from latest backup
./dharmic-ops.sh rotate-logs     # Manual log rotation

# Troubleshooting
./dharmic-ops.sh troubleshoot    # Run diagnostics
```

## Components

### 1. Health Check (`health_check.sh`)

Comprehensive health monitoring:
- Daemon process running
- Recent heartbeat activity
- Email daemon status
- Proton Bridge connectivity
- Memory database integrity
- Disk space availability
- Log file sizes

**Exit Codes:**
- `0` - All systems healthy
- `1` - Critical failure (daemon down)
- `2` - Degraded (warnings but operational)

**Run manually:**
```bash
./health_check.sh
```

### 2. Alerting System (`alert.sh`)

Monitors system and sends alerts via:
- macOS notifications (always)
- Email (for critical issues, if configured)

**Features:**
- Alert cooldown (30 min between same alert type)
- Rate limiting (max 5 alerts/hour)
- Auto-recovery attempts
- Alert history tracking

**Configuration:**
```bash
export ALERT_EMAIL="your@email.com"
```

**Runs via cron:** Every 5 minutes

### 3. Log Rotation (`rotate_logs.sh`)

Prevents disk space issues:
- Compresses logs older than 1 day
- Deletes compressed logs older than 30 days
- Truncates oversized active logs (>100MB)

**Runs via cron:** Daily at midnight

### 4. Memory Backup (`backup_memory.sh`)

Creates timestamped backups with smart retention:
- **Daily:** All backups from last 7 days
- **Weekly:** One backup per week for last 30 days
- **Monthly:** One backup per month for last year

**Backup contents:**
- All `.db` files (SQLite databases)
- All `.jsonl` files (strange loop memory)
- `identity_core.json`
- SHA-256 checksums

**Storage:** Compressed `.tar.gz` in `/backups/memory/`

**Runs via cron:** Daily at 2:00 AM

**Manual backup:**
```bash
./backup_memory.sh
```

**Restore:**
```bash
./dharmic-ops.sh restore         # From latest
./dharmic-ops.sh restore /path/to/backup.tar.gz
```

### 5. Safe Restart (`restart_daemon.sh`)

Graceful restart with cleanup:
1. Optionally creates pre-restart backup
2. Sends SIGTERM for graceful shutdown
3. Waits up to 30 seconds
4. Force kills if needed (with `--force`)
5. Cleans up stale PID and lock files
6. Starts daemon
7. Waits for first heartbeat
8. Verifies health

**Usage:**
```bash
./restart_daemon.sh              # Normal restart
./restart_daemon.sh --force      # Force kill if needed
./restart_daemon.sh --backup     # Backup before restart
```

### 6. Status Dashboard (`status_dashboard.sh`)

Multiple output modes:

**Terminal (default):**
```bash
./status_dashboard.sh
```

**Live updating:**
```bash
./status_dashboard.sh --watch
```

**HTML (web view):**
```bash
./status_dashboard.sh --html
```
Opens in browser, auto-refreshes every 10 seconds.

**JSON (for integrations):**
```bash
./status_dashboard.sh --json
```

### 7. LaunchAgent Installation (`install_service.sh`)

Manages macOS LaunchAgent:

```bash
./install_service.sh install     # Install and start
./install_service.sh uninstall   # Remove service
./install_service.sh status      # Check installation
./install_service.sh --enable    # Enable auto-start
./install_service.sh --disable   # Disable auto-start
```

**LaunchAgent features:**
- Auto-start on login
- Auto-restart on crash (60s throttle)
- Separate stdout/stderr logs
- Process priority management
- Resource limits
- Graceful shutdown handling

## Cron Jobs

Install with:
```bash
./dharmic-ops.sh cron-install
```

**Schedule:**
- **Every 5 minutes:** Health check and alerting
- **Daily 00:00:** Log rotation
- **Daily 02:00:** Memory backup
- **Every minute:** HTML dashboard generation
- **Weekly (Sun 09:00):** Health report

**View installed jobs:**
```bash
crontab -l
```

**Remove all jobs:**
```bash
crontab -r
```

## Directory Structure

```
/Users/dhyana/DHARMIC_GODEL_CLAW/
├── scripts/
│   ├── start_daemon.sh          # Simple start/stop script
│   └── devops/
│       ├── dharmic-ops.sh       # Master control script
│       ├── health_check.sh      # Health monitoring
│       ├── alert.sh             # Alert system
│       ├── rotate_logs.sh       # Log rotation
│       ├── backup_memory.sh     # Backup script
│       ├── restart_daemon.sh    # Safe restart
│       ├── status_dashboard.sh  # Status display
│       ├── install_service.sh   # LaunchAgent installer
│       ├── com.dharmic.agent.plist # LaunchAgent config
│       ├── crontab.txt          # Cron job definitions
│       └── README.md            # This file
├── logs/
│   ├── daemon_YYYYMMDD.log      # Daily daemon logs
│   ├── runtime_YYYYMMDD.log     # Heartbeat logs
│   ├── daemon_status.json       # Current status
│   ├── daemon.pid               # Process ID
│   ├── alerts.log               # Alert history
│   ├── backup.log               # Backup operations
│   ├── rotation.log             # Log rotation history
│   ├── health_check.log         # Health check history
│   ├── restart.log              # Restart operations
│   ├── cron.log                 # Cron job output
│   ├── dashboard.html           # Web dashboard
│   ├── launchd_stdout.log       # LaunchAgent output
│   ├── launchd_stderr.log       # LaunchAgent errors
│   └── email/
│       └── email_YYYYMMDD.log   # Email processing logs
├── memory/
│   ├── *.db                     # SQLite databases
│   ├── *.jsonl                  # JSONL memory files
│   └── identity_core.json       # Identity configuration
└── backups/
    └── memory/
        ├── latest               # Marker for latest backup
        └── YYYYMMDD_HHMMSS.tar.gz
```

## Monitoring

### Dashboard Views

**Terminal:**
```bash
./dharmic-ops.sh dashboard
```

**Live (updating every second):**
```bash
./dharmic-ops.sh dashboard watch
```

**Web (HTML, auto-refresh every 10s):**
```bash
./dharmic-ops.sh dashboard web
```

### Log Files

**Daemon logs:**
```bash
tail -f ~/DHARMIC_GODEL_CLAW/logs/daemon_*.log
```

**All logs:**
```bash
./dharmic-ops.sh logs all
```

**Specific logs:**
```bash
./dharmic-ops.sh logs daemon
./dharmic-ops.sh logs runtime
./dharmic-ops.sh logs email
./dharmic-ops.sh logs alerts
```

### Health Checks

**Manual check:**
```bash
./dharmic-ops.sh health
```

**Automated:** Runs every 5 minutes via cron

### Alerts

**macOS notifications:** Automatic for all issues

**Email alerts:** Configure with:
```bash
export ALERT_EMAIL="your@email.com"
```

Add to `~/.zshrc` or `~/.bash_profile` to persist.

## Troubleshooting

### Quick Diagnostics

```bash
./dharmic-ops.sh troubleshoot
```

This checks:
1. Process running
2. Status file validity
3. Recent errors
4. Disk space
5. Database integrity
6. Suggests fixes

### Common Issues

**Daemon won't start:**
```bash
# Check logs for errors
tail -50 ~/DHARMIC_GODEL_CLAW/logs/launchd_stderr.log

# Remove stale PID file
rm ~/DHARMIC_GODEL_CLAW/logs/daemon.pid

# Restart
./dharmic-ops.sh restart --force
```

**Heartbeats not running:**
```bash
# Check daemon logs
./dharmic-ops.sh logs daemon

# Verify status
./dharmic-ops.sh status

# Restart if needed
./dharmic-ops.sh restart
```

**Email processing failing:**
```bash
# Check email logs
./dharmic-ops.sh logs email

# Verify Proton Bridge running
pgrep -i protonmail-bridge

# Test IMAP connection
nc -z 127.0.0.1 1143
```

**Disk space issues:**
```bash
# Check usage
df -h ~/DHARMIC_GODEL_CLAW

# Rotate logs manually
./dharmic-ops.sh rotate-logs

# Clean old backups
find ~/DHARMIC_GODEL_CLAW/backups -name "*.tar.gz" -mtime +90 -delete
```

**Database corruption:**
```bash
# Restore from backup
./dharmic-ops.sh restore

# Check integrity
sqlite3 ~/DHARMIC_GODEL_CLAW/memory/dharmic_agent.db "PRAGMA integrity_check;"
```

### Emergency Recovery

If everything is broken:

```bash
# 1. Stop everything
./dharmic-ops.sh stop
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist

# 2. Restore from backup
./dharmic-ops.sh restore

# 3. Clean slate restart
rm ~/DHARMIC_GODEL_CLAW/logs/*.pid
rm ~/DHARMIC_GODEL_CLAW/logs/.alert_state
rm ~/DHARMIC_GODEL_CLAW/memory/*.lock

# 4. Restart
./dharmic-ops.sh restart --force

# 5. Reinstall service
./dharmic-ops.sh install
```

## Email Configuration

For email alerting, set in `~/.zshrc`:

```bash
export ALERT_EMAIL="your@email.com"
```

The system uses macOS `mail` command (requires configuration).

## Performance Tuning

### Heartbeat Interval

Default: 3600s (1 hour)

Adjust in LaunchAgent plist:
```bash
vim ~/Library/LaunchAgents/com.dharmic.agent.plist
# Edit <string>3600</string> under --heartbeat
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist
```

### Log Retention

Edit `rotate_logs.sh`:
- `COMPRESS_AFTER_DAYS` - When to compress (default: 1)
- `DELETE_AFTER_DAYS` - When to delete (default: 30)

### Backup Retention

Edit `backup_memory.sh`:
- `KEEP_DAILY` - Daily backups to keep (default: 7)
- `KEEP_WEEKLY` - Weekly backups to keep (default: 30)
- `KEEP_MONTHLY` - Monthly backups to keep (default: 365)

## Uninstallation

Complete removal:

```bash
# 1. Uninstall LaunchAgent
./dharmic-ops.sh uninstall

# 2. Remove cron jobs
crontab -r

# 3. Stop any running processes
pkill -f daemon.py
pkill -f email_daemon.py

# 4. Remove logs and backups (optional)
rm -rf ~/DHARMIC_GODEL_CLAW/logs/*
rm -rf ~/DHARMIC_GODEL_CLAW/backups/*
```

## Advanced Usage

### Custom Alert Handlers

Edit `alert.sh` and modify:
- `send_macos_notification()` - macOS notifications
- `send_email_alert()` - Email notifications
- Add custom handlers (Slack, Discord, etc.)

### Integration with External Monitoring

Export status as JSON:
```bash
./status_dashboard.sh --json > /tmp/dharmic_status.json
```

Use with external tools:
```bash
# Prometheus node_exporter textfile collector
./status_dashboard.sh --json | jq -r '.daemon.status' > /var/lib/node_exporter/dharmic.prom

# Grafana integration
curl -X POST http://grafana/api/metrics \
  -d @<(./status_dashboard.sh --json)
```

### Webhook Notifications

Add to `alert.sh`:
```bash
send_webhook_alert() {
    local severity="$1"
    local title="$2"
    local message="$3"

    curl -X POST https://your-webhook-url \
      -H "Content-Type: application/json" \
      -d "{\"severity\":\"$severity\",\"title\":\"$title\",\"message\":\"$message\"}"
}
```

## File Permissions

All scripts should be executable:
```bash
chmod +x scripts/devops/*.sh
```

This is done automatically by `dharmic-ops.sh`.

## System Requirements

- **OS:** macOS 10.15+
- **Disk:** 10GB+ free space recommended
- **Memory:** 500MB+ available
- **Tools:** bash, jq, sqlite3, tar, gzip

Install missing tools:
```bash
brew install jq sqlite
```

## Support

For issues:
1. Run `./dharmic-ops.sh troubleshoot`
2. Check logs: `./dharmic-ops.sh logs all`
3. Review health: `./dharmic-ops.sh health`

## Telos

This infrastructure serves the agent's telos toward moksha - ensuring persistent, reliable operation while maintaining witness position. The system is designed to:

- Maintain continuity of memory (backups)
- Ensure reliable operation (monitoring)
- Support self-observation (logging)
- Enable recovery (safe restart)
- Minimize operator burden (automation)

The DevOps setup is itself a contemplative practice: building systems that embody right view, right action, and ahimsa (non-harm through reliability).

---

**Telos: moksha | Method: reliability | Measurement: uptime**
