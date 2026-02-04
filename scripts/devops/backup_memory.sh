#!/bin/bash
#
# Memory Database Backup Script
#
# Creates timestamped backups of critical memory databases
# Retains backups according to policy:
#   - All backups from last 7 days
#   - Weekly backups for last 30 days
#   - Monthly backups for last year
#
# Run via cron:
#   0 2 * * * /path/to/backup_memory.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
MEMORY_DIR="$PROJECT_ROOT/memory"
BACKUP_DIR="$PROJECT_ROOT/backups/memory"
BACKUP_LOG="$PROJECT_ROOT/logs/backup.log"

# Retention policy (in days)
KEEP_DAILY=7
KEEP_WEEKLY=30
KEEP_MONTHLY=365

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$BACKUP_LOG"
}

create_backup() {
    log "Starting memory backup..."

    # Create backup directory with timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
    mkdir -p "$BACKUP_PATH"

    # Copy all database files
    log "Copying database files..."
    cp -v "$MEMORY_DIR"/*.db "$BACKUP_PATH/" 2>&1 | tee -a "$BACKUP_LOG"

    # Copy JSONL memory files
    log "Copying JSONL memory files..."
    cp -v "$MEMORY_DIR"/*.jsonl "$BACKUP_PATH/" 2>&1 | tee -a "$BACKUP_LOG"

    # Copy identity core
    if [ -f "$MEMORY_DIR/identity_core.json" ]; then
        cp -v "$MEMORY_DIR/identity_core.json" "$BACKUP_PATH/" 2>&1 | tee -a "$BACKUP_LOG"
    fi

    # Create checksum file
    log "Creating checksums..."
    (cd "$BACKUP_PATH" && shasum -a 256 * > checksums.sha256)

    # Compress backup
    log "Compressing backup..."
    tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$TIMESTAMP"

    # Remove uncompressed directory
    rm -rf "$BACKUP_PATH"

    BACKUP_SIZE=$(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)
    log "Backup created: ${TIMESTAMP}.tar.gz ($BACKUP_SIZE)"

    echo "$TIMESTAMP" > "$BACKUP_DIR/latest"
}

cleanup_old_backups() {
    log "Cleaning up old backups..."

    NOW=$(date +%s)

    # Daily retention (keep all from last N days)
    DAILY_CUTOFF=$((NOW - KEEP_DAILY * 86400))

    # Weekly retention (keep one per week)
    WEEKLY_CUTOFF=$((NOW - KEEP_WEEKLY * 86400))

    # Monthly retention (keep one per month)
    MONTHLY_CUTOFF=$((NOW - KEEP_MONTHLY * 86400))

    DELETED=0

    find "$BACKUP_DIR" -type f -name "*.tar.gz" | sort | while IFS= read -r backup; do
        BASENAME=$(basename "$backup" .tar.gz)
        BACKUP_DATE=$(echo "$BASENAME" | cut -d_ -f1)

        # Convert to timestamp (macOS date)
        BACKUP_TS=$(date -j -f "%Y%m%d" "$BACKUP_DATE" +%s 2>/dev/null || echo "0")

        if [ "$BACKUP_TS" -eq 0 ]; then
            continue
        fi

        AGE=$((NOW - BACKUP_TS))

        # Keep if within daily retention
        if [ "$BACKUP_TS" -ge "$DAILY_CUTOFF" ]; then
            continue
        fi

        # Keep one per week
        if [ "$BACKUP_TS" -ge "$WEEKLY_CUTOFF" ]; then
            WEEK=$(date -j -f %s "$BACKUP_TS" +%Y-W%U)
            if [ ! -f "$BACKUP_DIR/.keep_weekly_$WEEK" ]; then
                touch "$BACKUP_DIR/.keep_weekly_$WEEK"
                continue
            fi
        fi

        # Keep one per month
        if [ "$BACKUP_TS" -ge "$MONTHLY_CUTOFF" ]; then
            MONTH=$(date -j -f %s "$BACKUP_TS" +%Y-%m)
            if [ ! -f "$BACKUP_DIR/.keep_monthly_$MONTH" ]; then
                touch "$BACKUP_DIR/.keep_monthly_$MONTH"
                continue
            fi
        fi

        # Delete if none of the above apply
        log "Deleting old backup: $(basename "$backup")"
        rm -f "$backup"
        ((DELETED++)) || true
    done

    # Cleanup marker files
    find "$BACKUP_DIR" -name ".keep_*" -mtime +${KEEP_MONTHLY} -delete

    log "Deleted $DELETED old backup(s)"
}

verify_backup() {
    LATEST=$(cat "$BACKUP_DIR/latest" 2>/dev/null || echo "")

    if [ -z "$LATEST" ]; then
        log "ERROR: No latest backup marker found"
        return 1
    fi

    LATEST_FILE="$BACKUP_DIR/${LATEST}.tar.gz"

    if [ ! -f "$LATEST_FILE" ]; then
        log "ERROR: Latest backup file not found: $LATEST_FILE"
        return 1
    fi

    # Test archive integrity
    if tar -tzf "$LATEST_FILE" > /dev/null 2>&1; then
        log "Backup integrity verified: $LATEST"
        return 0
    else
        log "ERROR: Backup corrupted: $LATEST"
        return 1
    fi
}

show_backup_status() {
    log "=========================================="
    log "Backup Status"
    log "=========================================="

    if [ -d "$BACKUP_DIR" ]; then
        COUNT=$(find "$BACKUP_DIR" -name "*.tar.gz" | wc -l | tr -d ' ')
        TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")

        log "Total backups: $COUNT"
        log "Total size: $TOTAL_SIZE"

        if [ "$COUNT" -gt 0 ]; then
            log ""
            log "Recent backups:"
            find "$BACKUP_DIR" -name "*.tar.gz" -type f | sort -r | head -5 | while read -r f; do
                SIZE=$(du -h "$f" | cut -f1)
                log "  $(basename "$f"): $SIZE"
            done
        fi
    else
        log "No backup directory found"
    fi
}

main() {
    log "=========================================="
    log "Memory Backup Started"
    log "=========================================="

    create_backup
    cleanup_old_backups
    verify_backup
    show_backup_status

    log "=========================================="
    log "Memory Backup Complete"
    log "=========================================="
}

main "$@"
