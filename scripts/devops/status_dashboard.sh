#!/bin/bash
#
# Dharmic Agent Status Dashboard
#
# Displays comprehensive system status in terminal
# Can also generate HTML dashboard for web viewing
#
# Usage:
#   ./status_dashboard.sh              # Terminal display
#   ./status_dashboard.sh --html       # Generate HTML
#   ./status_dashboard.sh --watch      # Continuous update (1s)
#   ./status_dashboard.sh --json       # JSON output
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
STATUS_FILE="$PROJECT_ROOT/logs/daemon_status.json"
HTML_OUTPUT="$PROJECT_ROOT/logs/dashboard.html"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

get_daemon_status() {
    if [ ! -f "$STATUS_FILE" ]; then
        echo "unknown"
        return 1
    fi

    jq -r '.status // "unknown"' "$STATUS_FILE" 2>/dev/null || echo "unknown"
}

get_daemon_pid() {
    PID_FILE="$PROJECT_ROOT/logs/daemon.pid"

    if [ ! -f "$PID_FILE" ]; then
        echo "none"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo "$PID"
    else
        echo "stale"
        return 1
    fi
}

get_uptime() {
    PID=$(get_daemon_pid)

    if [ "$PID" = "none" ] || [ "$PID" = "stale" ]; then
        echo "N/A"
        return 1
    fi

    # Get process start time (macOS ps)
    START_TIME=$(ps -p "$PID" -o lstart= 2>/dev/null || echo "")

    if [ -z "$START_TIME" ]; then
        echo "N/A"
        return 1
    fi

    # Calculate uptime
    START_TS=$(date -j -f "%a %b %d %T %Y" "$START_TIME" +%s 2>/dev/null || echo "0")
    NOW_TS=$(date +%s)
    UPTIME=$((NOW_TS - START_TS))

    # Format as human readable
    DAYS=$((UPTIME / 86400))
    HOURS=$(( (UPTIME % 86400) / 3600 ))
    MINS=$(( (UPTIME % 3600) / 60 ))

    if [ "$DAYS" -gt 0 ]; then
        echo "${DAYS}d ${HOURS}h ${MINS}m"
    elif [ "$HOURS" -gt 0 ]; then
        echo "${HOURS}h ${MINS}m"
    else
        echo "${MINS}m"
    fi
}

get_heartbeat_info() {
    if [ ! -f "$STATUS_FILE" ]; then
        echo "N/A|N/A"
        return 1
    fi

    LAST_HEARTBEAT=$(jq -r '.details.last_heartbeat // empty' "$STATUS_FILE" 2>/dev/null || echo "")

    if [ -z "$LAST_HEARTBEAT" ]; then
        echo "N/A|N/A"
        return 1
    fi

    # Calculate age
    LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${LAST_HEARTBEAT:0:19}" +%s 2>/dev/null || echo "0")
    NOW_TS=$(date +%s)
    AGE=$((NOW_TS - LAST_TS))

    # Get interval
    INTERVAL=$(jq -r '.heartbeat_interval // 3600' "$STATUS_FILE" 2>/dev/null || echo "3600")

    echo "${AGE}s ago|${INTERVAL}s"
}

get_memory_stats() {
    MEMORY_DIR="$PROJECT_ROOT/memory"

    if [ ! -d "$MEMORY_DIR" ]; then
        echo "N/A|N/A"
        return 1
    fi

    # Count databases
    DB_COUNT=$(find "$MEMORY_DIR" -name "*.db" -type f | wc -l | tr -d ' ')

    # Total size
    TOTAL_SIZE=$(du -sh "$MEMORY_DIR" 2>/dev/null | cut -f1 || echo "0")

    echo "$DB_COUNT|$TOTAL_SIZE"
}

get_log_stats() {
    LOG_DIR="$PROJECT_ROOT/logs"

    if [ ! -d "$LOG_DIR" ]; then
        echo "N/A|N/A"
        return 1
    fi

    # Count log files
    LOG_COUNT=$(find "$LOG_DIR" -name "*.log" -type f | wc -l | tr -d ' ')

    # Total size
    TOTAL_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0")

    echo "$LOG_COUNT|$TOTAL_SIZE"
}

get_disk_usage() {
    df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4"|"$5}'
}

get_email_status() {
    if pgrep -f "email_daemon.py" > /dev/null; then
        EMAIL_LOG="$PROJECT_ROOT/logs/email/email_$(date +%Y%m%d).log"
        if [ -f "$EMAIL_LOG" ]; then
            LAST_CHECK=$(tail -1 "$EMAIL_LOG" | grep -o '^\[.*\]' | tr -d '[]' || echo "N/A")
            echo "running|$LAST_CHECK"
        else
            echo "running|N/A"
        fi
    else
        echo "stopped|N/A"
    fi
}

get_recent_alerts() {
    ALERT_LOG="$PROJECT_ROOT/logs/alerts.log"

    if [ ! -f "$ALERT_LOG" ]; then
        echo "0"
        return 0
    fi

    # Count alerts in last hour
    ONE_HOUR_AGO=$(date -v-1H "+%Y-%m-%d %H" 2>/dev/null || date --date="1 hour ago" "+%Y-%m-%d %H")
    grep "$ONE_HOUR_AGO" "$ALERT_LOG" 2>/dev/null | wc -l | tr -d ' '
}

get_backup_status() {
    BACKUP_DIR="$PROJECT_ROOT/backups/memory"
    LATEST_FILE="$BACKUP_DIR/latest"

    if [ ! -f "$LATEST_FILE" ]; then
        echo "none|N/A"
        return 1
    fi

    LATEST=$(cat "$LATEST_FILE")
    BACKUP_FILE="$BACKUP_DIR/${LATEST}.tar.gz"

    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        # Extract date from filename
        BACKUP_DATE=$(echo "$LATEST" | cut -d_ -f1)
        echo "$BACKUP_DATE|$SIZE"
    else
        echo "error|N/A"
        return 1
    fi
}

status_indicator() {
    local status="$1"

    case "$status" in
        running|ok|healthy)
            echo -e "${GREEN}●${NC}"
            ;;
        degraded|warning)
            echo -e "${YELLOW}●${NC}"
            ;;
        stopped|error|critical)
            echo -e "${RED}●${NC}"
            ;;
        *)
            echo -e "${BLUE}●${NC}"
            ;;
    esac
}

display_terminal() {
    clear

    echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║         DHARMIC AGENT - STATUS DASHBOARD               ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Daemon Status
    echo -e "${BOLD}${CYAN}DAEMON${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    DAEMON_STATUS=$(get_daemon_status)
    DAEMON_PID=$(get_daemon_pid)
    UPTIME=$(get_uptime)

    echo -e "  Status:   $(status_indicator "$DAEMON_STATUS") $DAEMON_STATUS"
    echo -e "  PID:      $DAEMON_PID"
    echo -e "  Uptime:   $UPTIME"

    IFS='|' read -r HB_AGE HB_INTERVAL <<< "$(get_heartbeat_info)"
    echo -e "  Heartbeat: $HB_AGE (interval: $HB_INTERVAL)"
    echo ""

    # Memory Status
    echo -e "${BOLD}${CYAN}MEMORY${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    IFS='|' read -r DB_COUNT MEM_SIZE <<< "$(get_memory_stats)"
    echo -e "  Databases: $DB_COUNT"
    echo -e "  Total Size: $MEM_SIZE"
    echo ""

    # Email Status
    echo -e "${BOLD}${CYAN}EMAIL INTERFACE${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    IFS='|' read -r EMAIL_STATUS LAST_CHECK <<< "$(get_email_status)"
    echo -e "  Status:     $(status_indicator "$EMAIL_STATUS") $EMAIL_STATUS"
    echo -e "  Last Check: $LAST_CHECK"
    echo ""

    # System Status
    echo -e "${BOLD}${CYAN}SYSTEM${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    IFS='|' read -r DISK_AVAIL DISK_USED <<< "$(get_disk_usage)"
    echo -e "  Disk Available: $DISK_AVAIL (Used: $DISK_USED)"

    IFS='|' read -r LOG_COUNT LOG_SIZE <<< "$(get_log_stats)"
    echo -e "  Log Files:      $LOG_COUNT ($LOG_SIZE)"

    RECENT_ALERTS=$(get_recent_alerts)
    echo -e "  Alerts (1h):    $RECENT_ALERTS"
    echo ""

    # Backup Status
    echo -e "${BOLD}${CYAN}BACKUPS${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    IFS='|' read -r BACKUP_DATE BACKUP_SIZE <<< "$(get_backup_status)"
    echo -e "  Latest:     $BACKUP_DATE"
    echo -e "  Size:       $BACKUP_SIZE"
    echo ""

    # Footer
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Updated: $(date '+%Y-%m-%d %H:%M:%S')"
}

generate_html() {
    cat > "$HTML_OUTPUT" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Dharmic Agent - Status Dashboard</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0e27;
            color: #e0e0e0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #4fc3f7;
            border-bottom: 2px solid #4fc3f7;
            padding-bottom: 10px;
        }
        .section {
            background: #1a1f3a;
            border: 1px solid #2d3561;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        .section h2 {
            color: #4fc3f7;
            margin-top: 0;
            font-size: 1.2em;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #2d3561;
        }
        .status-item:last-child {
            border-bottom: none;
        }
        .label {
            color: #9e9e9e;
        }
        .value {
            color: #e0e0e0;
            font-weight: bold;
        }
        .indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .indicator.ok { background: #4caf50; }
        .indicator.warning { background: #ff9800; }
        .indicator.error { background: #f44336; }
        .indicator.unknown { background: #2196f3; }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #2d3561;
        }
    </style>
</head>
<body>
    <h1>DHARMIC AGENT - STATUS DASHBOARD</h1>
EOF

    # Generate status data
    DAEMON_STATUS=$(get_daemon_status)
    DAEMON_PID=$(get_daemon_pid)
    UPTIME=$(get_uptime)
    IFS='|' read -r HB_AGE HB_INTERVAL <<< "$(get_heartbeat_info)"
    IFS='|' read -r DB_COUNT MEM_SIZE <<< "$(get_memory_stats)"
    IFS='|' read -r EMAIL_STATUS LAST_CHECK <<< "$(get_email_status)"
    IFS='|' read -r DISK_AVAIL DISK_USED <<< "$(get_disk_usage)"
    IFS='|' read -r LOG_COUNT LOG_SIZE <<< "$(get_log_stats)"
    RECENT_ALERTS=$(get_recent_alerts)
    IFS='|' read -r BACKUP_DATE BACKUP_SIZE <<< "$(get_backup_status)"

    # Map status to indicator class
    case "$DAEMON_STATUS" in
        running) STATUS_CLASS="ok" ;;
        degraded) STATUS_CLASS="warning" ;;
        stopped|error) STATUS_CLASS="error" ;;
        *) STATUS_CLASS="unknown" ;;
    esac

    cat >> "$HTML_OUTPUT" << EOF
    <div class="section">
        <h2>DAEMON</h2>
        <div class="status-item">
            <span class="label">Status</span>
            <span class="value"><span class="indicator $STATUS_CLASS"></span>$DAEMON_STATUS</span>
        </div>
        <div class="status-item">
            <span class="label">PID</span>
            <span class="value">$DAEMON_PID</span>
        </div>
        <div class="status-item">
            <span class="label">Uptime</span>
            <span class="value">$UPTIME</span>
        </div>
        <div class="status-item">
            <span class="label">Heartbeat</span>
            <span class="value">$HB_AGE (interval: $HB_INTERVAL)</span>
        </div>
    </div>

    <div class="section">
        <h2>MEMORY</h2>
        <div class="status-item">
            <span class="label">Databases</span>
            <span class="value">$DB_COUNT</span>
        </div>
        <div class="status-item">
            <span class="label">Total Size</span>
            <span class="value">$MEM_SIZE</span>
        </div>
    </div>

    <div class="section">
        <h2>EMAIL INTERFACE</h2>
        <div class="status-item">
            <span class="label">Status</span>
            <span class="value">$EMAIL_STATUS</span>
        </div>
        <div class="status-item">
            <span class="label">Last Check</span>
            <span class="value">$LAST_CHECK</span>
        </div>
    </div>

    <div class="section">
        <h2>SYSTEM</h2>
        <div class="status-item">
            <span class="label">Disk Available</span>
            <span class="value">$DISK_AVAIL (Used: $DISK_USED)</span>
        </div>
        <div class="status-item">
            <span class="label">Log Files</span>
            <span class="value">$LOG_COUNT ($LOG_SIZE)</span>
        </div>
        <div class="status-item">
            <span class="label">Alerts (1h)</span>
            <span class="value">$RECENT_ALERTS</span>
        </div>
    </div>

    <div class="section">
        <h2>BACKUPS</h2>
        <div class="status-item">
            <span class="label">Latest</span>
            <span class="value">$BACKUP_DATE</span>
        </div>
        <div class="status-item">
            <span class="label">Size</span>
            <span class="value">$BACKUP_SIZE</span>
        </div>
    </div>

    <div class="footer">
        Updated: $(date '+%Y-%m-%d %H:%M:%S')
    </div>
</body>
</html>
EOF

    echo "HTML dashboard generated: $HTML_OUTPUT"
}

output_json() {
    cat << EOF
{
  "daemon": {
    "status": "$(get_daemon_status)",
    "pid": "$(get_daemon_pid)",
    "uptime": "$(get_uptime)",
    "heartbeat": "$(get_heartbeat_info | cut -d'|' -f1)",
    "heartbeat_interval": "$(get_heartbeat_info | cut -d'|' -f2)"
  },
  "memory": {
    "databases": $(get_memory_stats | cut -d'|' -f1),
    "size": "$(get_memory_stats | cut -d'|' -f2)"
  },
  "email": {
    "status": "$(get_email_status | cut -d'|' -f1)",
    "last_check": "$(get_email_status | cut -d'|' -f2)"
  },
  "system": {
    "disk_available": "$(get_disk_usage | cut -d'|' -f1)",
    "disk_used": "$(get_disk_usage | cut -d'|' -f2)",
    "log_files": $(get_log_stats | cut -d'|' -f1),
    "log_size": "$(get_log_stats | cut -d'|' -f2)",
    "recent_alerts": $(get_recent_alerts)
  },
  "backup": {
    "latest": "$(get_backup_status | cut -d'|' -f1)",
    "size": "$(get_backup_status | cut -d'|' -f2)"
  },
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

main() {
    case "${1:-}" in
        --html)
            generate_html
            ;;
        --json)
            output_json
            ;;
        --watch)
            while true; do
                display_terminal
                sleep 1
            done
            ;;
        *)
            display_terminal
            ;;
    esac
}

main "$@"
