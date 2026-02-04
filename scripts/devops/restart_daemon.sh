#!/bin/bash
#
# Safe Daemon Restart Script
#
# Performs graceful shutdown with cleanup, then restarts daemon
# Can be used for:
#   - Manual restarts
#   - Recovery from errors
#   - After configuration changes
#
# Usage:
#   ./restart_daemon.sh              # Normal restart
#   ./restart_daemon.sh --force      # Force kill if graceful fails
#   ./restart_daemon.sh --backup     # Create backup before restart
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
START_DAEMON="$PROJECT_ROOT/scripts/start_daemon.sh"
PID_FILE="$PROJECT_ROOT/logs/daemon.pid"
STATUS_FILE="$PROJECT_ROOT/logs/daemon_status.json"
RESTART_LOG="$PROJECT_ROOT/logs/restart.log"

# Options
FORCE_KILL=false
CREATE_BACKUP=false
WAIT_TIMEOUT=30

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$RESTART_LOG"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_KILL=true
                shift
                ;;
            --backup)
                CREATE_BACKUP=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--force] [--backup]"
                exit 1
                ;;
        esac
    done
}

create_backup_if_requested() {
    if [ "$CREATE_BACKUP" = true ]; then
        log "Creating pre-restart backup..."
        if [ -x "$SCRIPT_DIR/backup_memory.sh" ]; then
            "$SCRIPT_DIR/backup_memory.sh"
        else
            log "WARNING: backup_memory.sh not found or not executable"
        fi
    fi
}

stop_daemon() {
    log "Stopping daemon..."

    if [ ! -f "$PID_FILE" ]; then
        log "No PID file found - daemon not running"
        return 0
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        log "Process $PID not running - removing stale PID file"
        rm -f "$PID_FILE"
        return 0
    fi

    # Try graceful shutdown first
    log "Sending SIGTERM to process $PID..."
    kill -TERM "$PID" 2>/dev/null || true

    # Wait for process to exit
    WAITED=0
    while ps -p "$PID" > /dev/null 2>&1; do
        sleep 1
        ((WAITED++)) || true

        if [ "$WAITED" -ge "$WAIT_TIMEOUT" ]; then
            if [ "$FORCE_KILL" = true ]; then
                log "Timeout - force killing process $PID"
                kill -KILL "$PID" 2>/dev/null || true
                sleep 2
                break
            else
                log "ERROR: Process did not exit within ${WAIT_TIMEOUT}s"
                log "Use --force to force kill"
                return 1
            fi
        fi
    done

    # Cleanup
    rm -f "$PID_FILE"
    log "Daemon stopped successfully"
    return 0
}

stop_email_daemon() {
    log "Checking for email daemon..."

    EMAIL_PID=$(pgrep -f "email_daemon.py" || true)

    if [ -n "$EMAIL_PID" ]; then
        log "Stopping email daemon (PID: $EMAIL_PID)..."
        kill -TERM "$EMAIL_PID" 2>/dev/null || true
        sleep 2

        if ps -p "$EMAIL_PID" > /dev/null 2>&1; then
            if [ "$FORCE_KILL" = true ]; then
                log "Force killing email daemon"
                kill -KILL "$EMAIL_PID" 2>/dev/null || true
            fi
        fi
    fi
}

cleanup_stale_files() {
    log "Cleaning up stale files..."

    # Remove stale PID files
    find "$PROJECT_ROOT/logs" -name "*.pid" -type f | while read -r pid_file; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file" 2>/dev/null || echo "")
            if [ -n "$PID" ] && ! ps -p "$PID" > /dev/null 2>&1; then
                log "Removing stale PID file: $(basename "$pid_file")"
                rm -f "$pid_file"
            fi
        fi
    done

    # Remove stale lock files
    find "$PROJECT_ROOT/memory" -name "*.lock" -type f -mmin +60 2>/dev/null | while read -r lock_file; do
        log "Removing stale lock file: $(basename "$lock_file")"
        rm -f "$lock_file"
    done
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check virtual environment
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        log "ERROR: Virtual environment not found at $PROJECT_ROOT/.venv"
        return 1
    fi

    # Check start script
    if [ ! -x "$START_DAEMON" ]; then
        log "ERROR: Start script not found or not executable: $START_DAEMON"
        return 1
    fi

    # Check memory directory
    if [ ! -d "$PROJECT_ROOT/memory" ]; then
        log "ERROR: Memory directory not found"
        return 1
    fi

    log "Prerequisites OK"
    return 0
}

start_daemon() {
    log "Starting daemon..."

    # Use the existing start script
    if "$START_DAEMON"; then
        log "Daemon started successfully"
        return 0
    else
        log "ERROR: Failed to start daemon"
        return 1
    fi
}

verify_startup() {
    log "Verifying startup..."

    # Wait for PID file
    WAITED=0
    while [ ! -f "$PID_FILE" ] && [ "$WAITED" -lt 10 ]; do
        sleep 1
        ((WAITED++)) || true
    done

    if [ ! -f "$PID_FILE" ]; then
        log "ERROR: PID file not created"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    # Verify process is running
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Daemon running with PID: $PID"

        # Wait for first heartbeat
        log "Waiting for first heartbeat..."
        WAITED=0
        while [ "$WAITED" -lt 30 ]; do
            if [ -f "$STATUS_FILE" ]; then
                STATUS=$(jq -r '.status' "$STATUS_FILE" 2>/dev/null || echo "unknown")
                if [ "$STATUS" = "running" ]; then
                    log "First heartbeat received - daemon healthy"
                    return 0
                fi
            fi
            sleep 1
            ((WAITED++)) || true
        done

        log "WARNING: No heartbeat within 30s - daemon may be unhealthy"
        return 2
    else
        log "ERROR: Process $PID not running"
        return 1
    fi
}

main() {
    log "=========================================="
    log "Daemon Restart Initiated"
    log "=========================================="

    parse_args "$@"

    create_backup_if_requested

    if ! check_prerequisites; then
        log "Prerequisites check failed - aborting"
        exit 1
    fi

    stop_email_daemon

    if ! stop_daemon; then
        log "Failed to stop daemon - aborting"
        exit 1
    fi

    cleanup_stale_files

    # Brief pause before restart
    sleep 2

    if ! start_daemon; then
        log "Failed to start daemon"
        exit 1
    fi

    if ! verify_startup; then
        log "Daemon started but verification failed"
        exit 2
    fi

    log "=========================================="
    log "Daemon Restart Complete"
    log "=========================================="
}

main "$@"
