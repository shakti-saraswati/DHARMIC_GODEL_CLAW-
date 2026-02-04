# Dharmic Agent - DevOps Quick Setup

Production-ready 24/7 operation for the Dharmic Agent on macOS.

## One-Command Setup

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/scripts/devops

# Make master control script available globally (optional)
ln -sf $(pwd)/dharmic-ops.sh /usr/local/bin/dharmic-ops
```

Now from anywhere:
```bash
dharmic-ops status       # Check status
dharmic-ops dashboard    # View dashboard
dharmic-ops help         # See all commands
```

## Initial Setup (First Time)

```bash
# 1. Install as macOS LaunchAgent (auto-start on login)
dharmic-ops install

# 2. Install cron jobs (monitoring, backups, log rotation)
dharmic-ops cron-install

# 3. Verify everything is working
dharmic-ops health
```

That's it! The system is now:
- Running 24/7 with auto-restart on crash
- Monitoring itself every 5 minutes
- Backing up memory daily at 2 AM
- Rotating logs daily at midnight
- Sending alerts if issues detected

## Quick Reference

### Daily Commands

```bash
dharmic-ops                # Show status
dharmic-ops dashboard      # Full dashboard
dharmic-ops logs daemon    # View logs
dharmic-ops health         # Health check
```

### Common Operations

```bash
# Restart daemon
dharmic-ops restart

# Create manual backup before risky operation
dharmic-ops backup

# Restore from backup if needed
dharmic-ops restore

# Troubleshoot issues
dharmic-ops troubleshoot

# View web dashboard (opens browser)
dharmic-ops dashboard web
```

### Emergency Commands

```bash
# Force restart if daemon is hung
dharmic-ops restart --force

# Stop everything
dharmic-ops stop

# Restore from specific backup
dharmic-ops restore /path/to/backup.tar.gz
```

## What Was Installed

### LaunchAgent
- **Location:** `~/Library/LaunchAgents/com.dharmic.agent.plist`
- **Purpose:** Auto-start daemon on login, restart on crash
- **Control:**
  - `launchctl list | grep dharmic` - Check if running
  - `launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist` - Stop
  - `launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist` - Start

### Cron Jobs
- **Every 5 min:** Health check + alerts
- **Daily 00:00:** Log rotation
- **Daily 02:00:** Memory backup
- **Every 1 min:** HTML dashboard generation
- **Weekly Sun 09:00:** Health report

View: `crontab -l`
Remove: `crontab -r`

### Scripts
All in `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/devops/`:
- `dharmic-ops.sh` - Master control
- `health_check.sh` - Health monitoring
- `alert.sh` - Alert system
- `status_dashboard.sh` - Status display
- `backup_memory.sh` - Backup creation
- `restore_daemon.sh` - Safe restart
- `rotate_logs.sh` - Log rotation
- `install_service.sh` - Service installer

## File Locations

```
~/DHARMIC_GODEL_CLAW/
├── logs/
│   ├── daemon_*.log          # Daily daemon logs
│   ├── runtime_*.log         # Heartbeat logs
│   ├── daemon_status.json    # Current status
│   ├── alerts.log            # Alert history
│   ├── health_check.log      # Health check history
│   └── dashboard.html        # Web dashboard
├── memory/
│   ├── *.db                  # SQLite databases
│   └── *.jsonl               # JSONL memory
└── backups/
    └── memory/
        └── *.tar.gz          # Timestamped backups
```

## Monitoring

### Terminal Dashboard
```bash
dharmic-ops dashboard watch   # Live updating (1s refresh)
```

### Web Dashboard
```bash
dharmic-ops dashboard web     # Opens in browser (10s auto-refresh)
```

### Logs
```bash
dharmic-ops logs daemon       # Daemon logs
dharmic-ops logs runtime      # Heartbeat logs
dharmic-ops logs email        # Email processing
dharmic-ops logs all          # All logs
```

## Alerting

Automatic alerts via:
1. **macOS notifications** (always enabled)
2. **Email** (configure with `export ALERT_EMAIL=your@email.com`)

Alerts trigger on:
- Daemon crashes
- Email processing failures
- Disk space < 5GB
- Database corruption
- Multiple restarts in short time

## Backup & Restore

### Automatic Backups
- Daily at 2 AM
- Retention: 7 daily, 4 weekly, 12 monthly
- Location: `~/DHARMIC_GODEL_CLAW/backups/memory/`

### Manual Backup
```bash
dharmic-ops backup
```

### Restore
```bash
# From latest
dharmic-ops restore

# From specific backup
dharmic-ops restore ~/DHARMIC_GODEL_CLAW/backups/memory/20260202_020000.tar.gz
```

**Warning:** Restore will stop the daemon, replace memory, and restart.

## Troubleshooting

### Quick Diagnostics
```bash
dharmic-ops troubleshoot
```

### Common Issues

**Daemon won't start:**
```bash
# Check for errors
tail -50 ~/DHARMIC_GODEL_CLAW/logs/launchd_stderr.log

# Force restart
dharmic-ops restart --force
```

**No heartbeats:**
```bash
# Check status
dharmic-ops status

# Check logs
dharmic-ops logs daemon

# Restart
dharmic-ops restart
```

**Email not working:**
```bash
# Check email daemon
dharmic-ops logs email

# Check Proton Bridge
pgrep -i protonmail-bridge

# Restart email daemon manually
cd ~/DHARMIC_GODEL_CLAW/src/core
python3 email_daemon.py --test
```

## Uninstall

Complete removal:
```bash
# Stop services
dharmic-ops uninstall

# Remove cron jobs
crontab -r

# Kill any running processes
pkill -f daemon.py
pkill -f email_daemon.py

# Optional: Remove logs and backups
rm -rf ~/DHARMIC_GODEL_CLAW/logs/*
rm -rf ~/DHARMIC_GODEL_CLAW/backups/*
```

## Advanced Configuration

### Change Heartbeat Interval

Edit `~/Library/LaunchAgents/com.dharmic.agent.plist`:
```xml
<string>--heartbeat</string>
<string>3600</string>  <!-- Change this (seconds) -->
```

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist
```

### Email Alerts

Add to `~/.zshrc` or `~/.bash_profile`:
```bash
export ALERT_EMAIL="your@email.com"
```

Requires macOS `mail` command to be configured.

### Custom Alert Actions

Edit `scripts/devops/alert.sh` to add:
- Slack notifications
- Discord webhooks
- SMS alerts
- Custom handlers

## Performance Notes

**CPU Usage:** Low (~0.5% average)
**Memory:** ~50MB resident
**Disk I/O:** Minimal except during backups
**Network:** Only email daemon (when active)

## Support Telos

This infrastructure embodies:
- **Persistence** through backups and recovery
- **Reliability** through monitoring and auto-restart
- **Self-observation** through logging and metrics
- **Ahimsa** (non-harm) through graceful degradation
- **Minimal friction** for the operator

The system maintains itself so you can focus on the work.

---

**Telos: moksha | Method: reliability | Measurement: uptime**

For detailed documentation: `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/devops/README.md`
