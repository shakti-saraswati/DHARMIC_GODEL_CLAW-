#!/bin/bash
#
# Alert Script for Dharmic Agent
#
# Sends notifications when critical issues are detected:
#   - Daemon crashes
#   - Email processing failures
#   - Disk space critical
#   - Memory corruption
#
# Notification methods:
#   1. macOS notification (via osascript)
#   2. Email (via configured SMTP)
#   3. Log file with retention
#
# Run via cron every 5 minutes:
#   */5 * * * * /path/to/alert.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ALERT_LOG="$PROJECT_ROOT/logs/alerts.log"
ALERT_STATE="$PROJECT_ROOT/logs/.alert_state"
HEALTH_CHECK="$SCRIPT_DIR/health_check.sh"

# Alert configuration
ALERT_EMAIL="${ALERT_EMAIL:-}"  # Set in environment or .env
COOLDOWN_MINUTES=30  # Don't spam alerts
MAX_ALERTS_PER_HOUR=5

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$ALERT_LOG"
}

check_alert_cooldown() {
    local alert_type="$1"

    if [ ! -f "$ALERT_STATE" ]; then
        echo "{}" > "$ALERT_STATE"
    fi

    # Check last alert time for this type
    LAST_ALERT=$(jq -r ".\"$alert_type\" // 0" "$ALERT_STATE" 2>/dev/null || echo "0")
    NOW=$(date +%s)
    ELAPSED=$((NOW - LAST_ALERT))
    COOLDOWN_SECONDS=$((COOLDOWN_MINUTES * 60))

    if [ "$ELAPSED" -lt "$COOLDOWN_SECONDS" ]; then
        return 1  # Still in cooldown
    fi

    # Check hourly rate limit
    HOUR_AGO=$((NOW - 3600))
    RECENT_ALERTS=$(jq -r 'to_entries | map(select(.value > '"$HOUR_AGO"')) | length' "$ALERT_STATE" 2>/dev/null || echo "0")

    if [ "$RECENT_ALERTS" -ge "$MAX_ALERTS_PER_HOUR" ]; then
        log "WARNING: Alert rate limit reached ($RECENT_ALERTS in last hour)"
        return 1
    fi

    return 0
}

update_alert_state() {
    local alert_type="$1"
    NOW=$(date +%s)

    # Update state file
    TMP=$(mktemp)
    jq ".\"$alert_type\" = $NOW" "$ALERT_STATE" > "$TMP" && mv "$TMP" "$ALERT_STATE"
}

send_macos_notification() {
    local title="$1"
    local message="$2"

    osascript -e "display notification \"$message\" with title \"Dharmic Agent\" subtitle \"$title\""
}

send_email_alert() {
    local subject="$1"
    local body="$2"

    if [ -z "$ALERT_EMAIL" ]; then
        return 0  # Email not configured
    fi

    # Simple mail using macOS mail command
    # Requires mail to be configured
    echo "$body" | mail -s "[Dharmic Agent] $subject" "$ALERT_EMAIL" 2>/dev/null || true
}

alert() {
    local severity="$1"  # CRITICAL | WARNING | INFO
    local alert_type="$2"
    local title="$3"
    local message="$4"

    # Check cooldown
    if ! check_alert_cooldown "$alert_type"; then
        log "[$severity] $title (suppressed - cooldown active)"
        return 0
    fi

    log "[$severity] $title - $message"

    # Send notifications
    send_macos_notification "$title" "$message"

    if [ "$severity" = "CRITICAL" ]; then
        send_email_alert "$title" "$message"
    fi

    # Update state
    update_alert_state "$alert_type"
}

check_daemon_health() {
    if [ ! -x "$HEALTH_CHECK" ]; then
        log "ERROR: Health check script not found: $HEALTH_CHECK"
        return 1
    fi

    # Run health check and capture output
    HEALTH_OUTPUT=$("$HEALTH_CHECK" 2>&1) || HEALTH_EXIT=$?
    HEALTH_EXIT=${HEALTH_EXIT:-0}

    case $HEALTH_EXIT in
        0)
            # Healthy - clear any previous alerts
            if [ -f "$ALERT_STATE" ]; then
                TMP=$(mktemp)
                jq 'del(.daemon_critical, .daemon_degraded)' "$ALERT_STATE" > "$TMP" && mv "$TMP" "$ALERT_STATE"
            fi
            return 0
            ;;
        1)
            # Critical
            CRITICAL_MSG=$(echo "$HEALTH_OUTPUT" | grep "CRITICAL" | head -1 || echo "Daemon health check failed")
            alert "CRITICAL" "daemon_critical" "Daemon Critical Failure" "$CRITICAL_MSG"
            return 1
            ;;
        2)
            # Warning
            WARNING_MSG=$(echo "$HEALTH_OUTPUT" | grep "WARNING" | head -1 || echo "Daemon degraded")
            alert "WARNING" "daemon_degraded" "Daemon Degraded" "$WARNING_MSG"
            return 2
            ;;
        *)
            # Unknown error
            alert "CRITICAL" "daemon_unknown" "Health Check Failed" "Exit code: $HEALTH_EXIT"
            return 1
            ;;
    esac
}

check_disk_space() {
    AVAILABLE=$(df -g "$PROJECT_ROOT" | tail -1 | awk '{print $4}')

    if [ "$AVAILABLE" -lt 2 ]; then
        alert "CRITICAL" "disk_critical" "Disk Space Critical" "Only ${AVAILABLE}GB remaining"
        return 1
    elif [ "$AVAILABLE" -lt 5 ]; then
        alert "WARNING" "disk_low" "Disk Space Low" "Only ${AVAILABLE}GB remaining"
        return 2
    fi

    return 0
}

check_email_processing() {
    EMAIL_LOG="$PROJECT_ROOT/logs/email/email_$(date +%Y%m%d).log"

    if [ ! -f "$EMAIL_LOG" ]; then
        return 0  # No email log today - might not be running
    fi

    # Check for recent errors
    RECENT_ERRORS=$(tail -100 "$EMAIL_LOG" | grep -i "error" | wc -l | tr -d ' ')

    if [ "$RECENT_ERRORS" -gt 5 ]; then
        alert "WARNING" "email_errors" "Email Processing Errors" "$RECENT_ERRORS errors in last 100 lines"
        return 1
    fi

    return 0
}

check_memory_corruption() {
    MEMORY_DIR="$PROJECT_ROOT/memory"

    # Check if databases are readable
    for db in "$MEMORY_DIR"/*.db; do
        if [ -f "$db" ]; then
            # Quick SQLite integrity check
            if ! sqlite3 "$db" "PRAGMA integrity_check;" > /dev/null 2>&1; then
                alert "CRITICAL" "memory_corrupt" "Memory Corruption" "Database corrupted: $(basename "$db")"
                return 1
            fi
        fi
    done

    return 0
}

check_restart_loops() {
    RESTART_LOG="$PROJECT_ROOT/logs/restart.log"

    if [ ! -f "$RESTART_LOG" ]; then
        return 0
    fi

    # Check for multiple restarts in short time
    RECENT_RESTARTS=$(grep "Daemon Restart Initiated" "$RESTART_LOG" | tail -10 | wc -l | tr -d ' ')

    if [ "$RECENT_RESTARTS" -gt 3 ]; then
        # Check if they're within 1 hour
        FIRST_RESTART=$(grep "Daemon Restart Initiated" "$RESTART_LOG" | tail -10 | head -1 | grep -o '\[.*\]' | tr -d '[]')
        LAST_RESTART=$(grep "Daemon Restart Initiated" "$RESTART_LOG" | tail -1 | grep -o '\[.*\]' | tr -d '[]')

        # Simple time comparison (assumes same day)
        alert "WARNING" "restart_loop" "Frequent Restarts Detected" "$RECENT_RESTARTS restarts detected"
        return 1
    fi

    return 0
}

auto_recovery() {
    # Attempt automatic recovery for certain issues

    RESTART_SCRIPT="$SCRIPT_DIR/restart_daemon.sh"

    # Check if daemon is completely down
    if [ -f "$PROJECT_ROOT/logs/daemon_status.json" ]; then
        STATUS=$(jq -r '.status' "$PROJECT_ROOT/logs/daemon_status.json" 2>/dev/null || echo "unknown")

        if [ "$STATUS" = "error" ] || [ "$STATUS" = "stopped" ]; then
            log "Attempting automatic recovery (daemon status: $STATUS)..."

            if [ -x "$RESTART_SCRIPT" ]; then
                if "$RESTART_SCRIPT"; then
                    alert "INFO" "auto_recovery" "Auto-Recovery Successful" "Daemon restarted automatically"
                    return 0
                else
                    alert "CRITICAL" "auto_recovery_failed" "Auto-Recovery Failed" "Manual intervention required"
                    return 1
                fi
            fi
        fi
    fi

    return 0
}

cleanup_old_alerts() {
    # Keep only last 1000 lines of alert log
    if [ -f "$ALERT_LOG" ]; then
        LINE_COUNT=$(wc -l < "$ALERT_LOG" | tr -d ' ')
        if [ "$LINE_COUNT" -gt 1000 ]; then
            tail -1000 "$ALERT_LOG" > "$ALERT_LOG.tmp"
            mv "$ALERT_LOG.tmp" "$ALERT_LOG"
        fi
    fi
}

main() {
    # Ensure alert state exists
    mkdir -p "$(dirname "$ALERT_STATE")"
    [ -f "$ALERT_STATE" ] || echo "{}" > "$ALERT_STATE"

    # Run checks
    ISSUES=0

    check_daemon_health || ((ISSUES++)) || true
    check_disk_space || ((ISSUES++)) || true
    check_email_processing || ((ISSUES++)) || true
    check_memory_corruption || ((ISSUES++)) || true
    check_restart_loops || ((ISSUES++)) || true

    # Attempt recovery if critical issues found
    if [ "$ISSUES" -gt 0 ]; then
        auto_recovery
    fi

    cleanup_old_alerts

    if [ "$ISSUES" -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

main "$@"
