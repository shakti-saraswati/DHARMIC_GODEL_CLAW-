#!/bin/bash
#
# Log Rotation Script for Dharmic Agent
#
# Rotates logs to prevent disk space issues:
# - Compresses logs older than 1 day
# - Deletes compressed logs older than 30 days
# - Handles daily log files with date stamps
#
# Run via cron:
#   0 0 * * * /path/to/rotate_logs.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$PROJECT_ROOT/logs"
ROTATION_LOG="$LOG_DIR/rotation.log"

# Retention policy
COMPRESS_AFTER_DAYS=1
DELETE_AFTER_DAYS=30
MAX_SIZE_MB=100

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$ROTATION_LOG"
}

compress_old_logs() {
    log "Starting log compression..."

    # Find .log files older than COMPRESS_AFTER_DAYS and not already compressed
    find "$LOG_DIR" -type f -name "*.log" -mtime +${COMPRESS_AFTER_DAYS} ! -name "rotation.log" -print0 | \
    while IFS= read -r -d '' file; do
        if [ ! -f "${file}.gz" ]; then
            log "Compressing: $(basename "$file")"
            gzip -9 "$file"
        fi
    done
}

delete_old_compressed() {
    log "Deleting old compressed logs..."

    # Delete .gz files older than DELETE_AFTER_DAYS
    DELETED=$(find "$LOG_DIR" -type f -name "*.log.gz" -mtime +${DELETE_AFTER_DAYS} -delete -print | wc -l | tr -d ' ')

    if [ "$DELETED" -gt 0 ]; then
        log "Deleted $DELETED compressed log file(s)"
    else
        log "No compressed logs to delete"
    fi
}

truncate_large_files() {
    log "Checking for oversized log files..."

    # Find files over MAX_SIZE_MB that are currently being written to
    # (e.g., daemon_stdout.log, email_daemon_stdout.log)
    find "$LOG_DIR" -type f -name "*_stdout.log" -o -name "*_stderr.log" | \
    while IFS= read -r file; do
        SIZE_MB=$(du -m "$file" 2>/dev/null | cut -f1)
        if [ "${SIZE_MB:-0}" -gt "$MAX_SIZE_MB" ]; then
            log "Truncating large file: $(basename "$file") (${SIZE_MB}MB)"
            # Keep last 1000 lines
            tail -n 1000 "$file" > "${file}.tmp"
            mv "${file}.tmp" "$file"
        fi
    done
}

show_disk_usage() {
    log "Log directory disk usage:"
    du -sh "$LOG_DIR" | tee -a "$ROTATION_LOG"

    log "Largest log files:"
    du -h "$LOG_DIR"/*.log 2>/dev/null | sort -rh | head -5 | tee -a "$ROTATION_LOG" || log "No .log files found"
}

main() {
    log "=========================================="
    log "Log Rotation Started"
    log "=========================================="

    compress_old_logs
    delete_old_compressed
    truncate_large_files
    show_disk_usage

    log "=========================================="
    log "Log Rotation Complete"
    log "=========================================="
}

main "$@"
