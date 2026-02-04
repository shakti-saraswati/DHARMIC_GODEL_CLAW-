#!/bin/bash
#
# Dharmic Agent Health Check
#
# Checks:
# 1. Daemon process running
# 2. Recent heartbeat activity
# 3. Email daemon running (if enabled)
# 4. Proton Bridge running (if email enabled)
# 5. Memory databases accessible
# 6. Disk space adequate
# 7. Log file sizes reasonable
#
# Exit codes:
#   0 - All healthy
#   1 - Critical failure (daemon down)
#   2 - Warning (degraded but operational)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
STATUS_FILE="$PROJECT_ROOT/logs/daemon_status.json"
PID_FILE="$PROJECT_ROOT/logs/daemon.pid"
HEALTH_LOG="$PROJECT_ROOT/logs/health_check.log"
EMAIL_DAEMON_CHECK="${EMAIL_DAEMON_CHECK:-true}"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Counters
CRITICAL=0
WARNING=0
OK=0

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$HEALTH_LOG"
}

check_status() {
    local name="$1"
    local status="$2"
    local message="$3"

    case "$status" in
        ok)
            echo -e "${GREEN}✓${NC} $name: $message"
            ((OK++)) || true
            ;;
        warn)
            echo -e "${YELLOW}⚠${NC} $name: $message"
            ((WARNING++)) || true
            log "WARNING: $name - $message"
            ;;
        critical)
            echo -e "${RED}✗${NC} $name: $message"
            ((CRITICAL++)) || true
            log "CRITICAL: $name - $message"
            ;;
    esac
}

# Check 1: Daemon process running
check_daemon_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            check_status "Daemon Process" "ok" "Running (PID: $PID)"
            return 0
        else
            check_status "Daemon Process" "critical" "Not running (stale PID: $PID)"
            return 1
        fi
    else
        check_status "Daemon Process" "critical" "No PID file found"
        return 1
    fi
}

# Check 2: Recent heartbeat
check_heartbeat() {
    if [ ! -f "$STATUS_FILE" ]; then
        check_status "Heartbeat" "critical" "No status file found"
        return 1
    fi

    # Get last heartbeat timestamp
    LAST_HEARTBEAT=$(jq -r '.details.last_heartbeat // empty' "$STATUS_FILE" 2>/dev/null || echo "")

    if [ -z "$LAST_HEARTBEAT" ]; then
        check_status "Heartbeat" "warn" "No heartbeat recorded yet"
        return 2
    fi

    # Calculate age in seconds (macOS date command)
    LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${LAST_HEARTBEAT:0:19}" +%s 2>/dev/null || echo "0")
    NOW_TS=$(date +%s)
    AGE=$((NOW_TS - LAST_TS))

    # Get configured heartbeat interval
    INTERVAL=$(jq -r '.heartbeat_interval // 3600' "$STATUS_FILE" 2>/dev/null || echo "3600")

    # Allow 2x interval before warning
    MAX_AGE=$((INTERVAL * 2))

    if [ "$AGE" -lt "$MAX_AGE" ]; then
        check_status "Heartbeat" "ok" "Last heartbeat ${AGE}s ago (interval: ${INTERVAL}s)"
        return 0
    else
        check_status "Heartbeat" "warn" "Heartbeat stale: ${AGE}s ago (expected: ${INTERVAL}s)"
        return 2
    fi
}

# Check 3: Email daemon (if enabled)
check_email_daemon() {
    if [ "$EMAIL_DAEMON_CHECK" != "true" ]; then
        check_status "Email Daemon" "ok" "Check disabled"
        return 0
    fi

    if pgrep -f "email_daemon.py" > /dev/null; then
        check_status "Email Daemon" "ok" "Running"
        return 0
    else
        check_status "Email Daemon" "warn" "Not running"
        return 2
    fi
}

# Check 4: Proton Bridge (if email enabled)
check_proton_bridge() {
    if [ "$EMAIL_DAEMON_CHECK" != "true" ]; then
        check_status "Proton Bridge" "ok" "Check disabled"
        return 0
    fi

    # Check if Proton Bridge is running
    if pgrep -i "protonmail-bridge" > /dev/null || pgrep -i "bridge" > /dev/null | grep -q proton; then
        # Try to connect to IMAP port
        if nc -z 127.0.0.1 1143 2>/dev/null; then
            check_status "Proton Bridge" "ok" "Running and accepting connections"
            return 0
        else
            check_status "Proton Bridge" "warn" "Running but IMAP port not available"
            return 2
        fi
    else
        check_status "Proton Bridge" "warn" "Not running"
        return 2
    fi
}

# Check 5: Memory databases
check_databases() {
    MEMORY_DIR="$PROJECT_ROOT/memory"

    if [ ! -d "$MEMORY_DIR" ]; then
        check_status "Memory Databases" "critical" "Memory directory not found"
        return 1
    fi

    # Check critical databases exist and are readable
    CRITICAL_DBS=("dharmic_agent.db" "deep_memory.db")
    MISSING=()

    for db in "${CRITICAL_DBS[@]}"; do
        if [ ! -f "$MEMORY_DIR/$db" ]; then
            MISSING+=("$db")
        fi
    done

    if [ ${#MISSING[@]} -eq 0 ]; then
        # Check total size
        TOTAL_SIZE=$(du -sh "$MEMORY_DIR" | cut -f1)
        check_status "Memory Databases" "ok" "All present ($TOTAL_SIZE)"
        return 0
    else
        check_status "Memory Databases" "critical" "Missing: ${MISSING[*]}"
        return 1
    fi
}

# Check 6: Disk space
check_disk_space() {
    # Get available space in GB (macOS df)
    AVAILABLE=$(df -g "$PROJECT_ROOT" | tail -1 | awk '{print $4}')

    if [ "$AVAILABLE" -gt 10 ]; then
        check_status "Disk Space" "ok" "${AVAILABLE}GB available"
        return 0
    elif [ "$AVAILABLE" -gt 5 ]; then
        check_status "Disk Space" "warn" "Only ${AVAILABLE}GB available"
        return 2
    else
        check_status "Disk Space" "critical" "Only ${AVAILABLE}GB available"
        return 1
    fi
}

# Check 7: Log file sizes
check_log_sizes() {
    LOG_DIR="$PROJECT_ROOT/logs"

    # Check if any log file exceeds 100MB
    LARGE_LOGS=$(find "$LOG_DIR" -type f -name "*.log" -size +100M 2>/dev/null || true)

    if [ -z "$LARGE_LOGS" ]; then
        TOTAL_SIZE=$(du -sh "$LOG_DIR" | cut -f1)
        check_status "Log Files" "ok" "All under 100MB (total: $TOTAL_SIZE)"
        return 0
    else
        COUNT=$(echo "$LARGE_LOGS" | wc -l | tr -d ' ')
        check_status "Log Files" "warn" "$COUNT file(s) over 100MB - rotation needed"
        return 2
    fi
}

# Main execution
main() {
    echo "============================================"
    echo "Dharmic Agent Health Check"
    echo "$(date)"
    echo "============================================"
    echo ""

    check_daemon_process
    check_heartbeat
    check_email_daemon
    check_proton_bridge
    check_databases
    check_disk_space
    check_log_sizes

    echo ""
    echo "============================================"
    echo "Summary:"
    echo "  ✓ OK: $OK"
    echo "  ⚠ Warnings: $WARNING"
    echo "  ✗ Critical: $CRITICAL"
    echo "============================================"

    if [ "$CRITICAL" -gt 0 ]; then
        echo "Status: CRITICAL"
        exit 1
    elif [ "$WARNING" -gt 0 ]; then
        echo "Status: DEGRADED"
        exit 2
    else
        echo "Status: HEALTHY"
        exit 0
    fi
}

main "$@"
