#!/bin/bash
#
# Dharmic Agent Operations - Master DevOps Control Script
#
# Unified interface for all DevOps operations:
#   - Service management (start/stop/restart/status)
#   - Health monitoring
#   - Log management
#   - Backup/restore
#   - Alerting configuration
#   - Quick troubleshooting
#
# Usage: dharmic-ops <command> [options]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

show_banner() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      DHARMIC AGENT - DevOps Management Console          ║
║                                                          ║
║      Telos: moksha | Method: code | State: persistent   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
}

cmd_start() {
    echo -e "${BOLD}Starting Dharmic Agent...${NC}"
    "$PROJECT_ROOT/scripts/start_daemon.sh" "$@"
}

cmd_stop() {
    echo -e "${BOLD}Stopping Dharmic Agent...${NC}"
    "$PROJECT_ROOT/scripts/start_daemon.sh" --stop
}

cmd_restart() {
    echo -e "${BOLD}Restarting Dharmic Agent...${NC}"
    if [ -x "$SCRIPT_DIR/restart_daemon.sh" ]; then
        "$SCRIPT_DIR/restart_daemon.sh" "$@"
    else
        cmd_stop
        sleep 3
        cmd_start
    fi
}

cmd_status() {
    if [ -x "$SCRIPT_DIR/status_dashboard.sh" ]; then
        "$SCRIPT_DIR/status_dashboard.sh"
    else
        "$PROJECT_ROOT/scripts/start_daemon.sh" --status
    fi
}

cmd_health() {
    if [ -x "$SCRIPT_DIR/health_check.sh" ]; then
        "$SCRIPT_DIR/health_check.sh"
    else
        echo "Health check not available"
        exit 1
    fi
}

cmd_logs() {
    local log_type="${1:-daemon}"

    case "$log_type" in
        daemon|d)
            tail -f "$PROJECT_ROOT/logs/daemon_"*.log
            ;;
        runtime|r)
            tail -f "$PROJECT_ROOT/logs/runtime_"*.log
            ;;
        email|e)
            tail -f "$PROJECT_ROOT/logs/email/"*.log
            ;;
        all|a)
            tail -f "$PROJECT_ROOT/logs/"*.log
            ;;
        alerts)
            tail -f "$PROJECT_ROOT/logs/alerts.log"
            ;;
        *)
            echo "Usage: dharmic-ops logs [daemon|runtime|email|all|alerts]"
            exit 1
            ;;
    esac
}

cmd_backup() {
    if [ -x "$SCRIPT_DIR/backup_memory.sh" ]; then
        "$SCRIPT_DIR/backup_memory.sh"
    else
        echo "Backup script not available"
        exit 1
    fi
}

cmd_restore() {
    local backup_file="${1:-latest}"

    echo -e "${YELLOW}⚠ WARNING: This will stop the daemon and restore memory from backup${NC}"
    read -p "Continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        exit 0
    fi

    # Stop daemon
    cmd_stop

    BACKUP_DIR="$PROJECT_ROOT/backups/memory"

    if [ "$backup_file" = "latest" ]; then
        if [ -f "$BACKUP_DIR/latest" ]; then
            backup_file="$BACKUP_DIR/$(cat "$BACKUP_DIR/latest").tar.gz"
        else
            echo "No latest backup found"
            exit 1
        fi
    fi

    if [ ! -f "$backup_file" ]; then
        echo "Backup file not found: $backup_file"
        exit 1
    fi

    echo "Restoring from: $backup_file"

    # Backup current state
    TEMP_BACKUP="$PROJECT_ROOT/memory.pre-restore.$(date +%Y%m%d_%H%M%S)"
    mv "$PROJECT_ROOT/memory" "$TEMP_BACKUP"
    mkdir -p "$PROJECT_ROOT/memory"

    # Extract backup
    tar -xzf "$backup_file" -C "$PROJECT_ROOT/memory" --strip-components=1

    echo "Restore complete. Previous state saved to: $TEMP_BACKUP"
    echo "Starting daemon..."

    cmd_start
}

cmd_install() {
    if [ -x "$SCRIPT_DIR/install_service.sh" ]; then
        "$SCRIPT_DIR/install_service.sh" --install
    else
        echo "Install script not available"
        exit 1
    fi
}

cmd_uninstall() {
    if [ -x "$SCRIPT_DIR/install_service.sh" ]; then
        "$SCRIPT_DIR/install_service.sh" --uninstall
    else
        echo "Install script not available"
        exit 1
    fi
}

cmd_rotate_logs() {
    if [ -x "$SCRIPT_DIR/rotate_logs.sh" ]; then
        "$SCRIPT_DIR/rotate_logs.sh"
    else
        echo "Log rotation script not available"
        exit 1
    fi
}

cmd_dashboard() {
    local mode="${1:-terminal}"

    if [ ! -x "$SCRIPT_DIR/status_dashboard.sh" ]; then
        echo "Dashboard script not available"
        exit 1
    fi

    case "$mode" in
        web|html)
            "$SCRIPT_DIR/status_dashboard.sh" --html
            HTML_FILE="$PROJECT_ROOT/logs/dashboard.html"
            if [ -f "$HTML_FILE" ]; then
                echo "Dashboard generated: $HTML_FILE"
                open "$HTML_FILE" 2>/dev/null || echo "Open in browser: file://$HTML_FILE"
            fi
            ;;
        watch|w)
            "$SCRIPT_DIR/status_dashboard.sh" --watch
            ;;
        json)
            "$SCRIPT_DIR/status_dashboard.sh" --json
            ;;
        *)
            "$SCRIPT_DIR/status_dashboard.sh"
            ;;
    esac
}

cmd_troubleshoot() {
    echo -e "${BOLD}${CYAN}Dharmic Agent - Troubleshooting${NC}"
    echo ""

    # 1. Check if running
    echo -e "${BOLD}1. Process Check${NC}"
    if pgrep -f "daemon.py" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} Daemon process running"
        PID=$(pgrep -f "daemon.py")
        echo "    PID: $PID"
    else
        echo -e "  ${RED}✗${NC} Daemon process NOT running"
    fi
    echo ""

    # 2. Check status file
    echo -e "${BOLD}2. Status File${NC}"
    if [ -f "$PROJECT_ROOT/logs/daemon_status.json" ]; then
        echo -e "  ${GREEN}✓${NC} Status file exists"
        STATUS=$(jq -r '.status' "$PROJECT_ROOT/logs/daemon_status.json" 2>/dev/null || echo "unknown")
        echo "    Status: $STATUS"
    else
        echo -e "  ${RED}✗${NC} Status file missing"
    fi
    echo ""

    # 3. Check recent errors
    echo -e "${BOLD}3. Recent Errors${NC}"
    if [ -f "$PROJECT_ROOT/logs/launchd_stderr.log" ]; then
        ERRORS=$(tail -50 "$PROJECT_ROOT/logs/launchd_stderr.log" | grep -i "error" | wc -l | tr -d ' ')
        if [ "$ERRORS" -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC} No recent errors"
        else
            echo -e "  ${YELLOW}⚠${NC} $ERRORS error(s) in last 50 lines"
            echo ""
            echo "  Last error:"
            tail -50 "$PROJECT_ROOT/logs/launchd_stderr.log" | grep -i "error" | tail -1
        fi
    else
        echo "  No error log found"
    fi
    echo ""

    # 4. Check disk space
    echo -e "${BOLD}4. Disk Space${NC}"
    AVAILABLE=$(df -g "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE" -gt 10 ]; then
        echo -e "  ${GREEN}✓${NC} ${AVAILABLE}GB available"
    else
        echo -e "  ${YELLOW}⚠${NC} Only ${AVAILABLE}GB available"
    fi
    echo ""

    # 5. Check databases
    echo -e "${BOLD}5. Memory Databases${NC}"
    if [ -d "$PROJECT_ROOT/memory" ]; then
        DB_COUNT=$(find "$PROJECT_ROOT/memory" -name "*.db" | wc -l | tr -d ' ')
        echo -e "  ${GREEN}✓${NC} Memory directory exists ($DB_COUNT databases)"
    else
        echo -e "  ${RED}✗${NC} Memory directory missing"
    fi
    echo ""

    # 6. Suggested actions
    echo -e "${BOLD}Suggested Actions:${NC}"
    if ! pgrep -f "daemon.py" > /dev/null; then
        echo "  → Start daemon: dharmic-ops start"
    fi

    if [ -f "$PROJECT_ROOT/logs/daemon_status.json" ]; then
        STATUS=$(jq -r '.status' "$PROJECT_ROOT/logs/daemon_status.json" 2>/dev/null || echo "unknown")
        if [ "$STATUS" = "error" ]; then
            echo "  → Check logs: dharmic-ops logs daemon"
            echo "  → Restart: dharmic-ops restart"
        fi
    fi
}

cmd_cron_install() {
    echo -e "${BOLD}Installing cron jobs...${NC}"

    CRONTAB_FILE="$SCRIPT_DIR/crontab.txt"

    if [ ! -f "$CRONTAB_FILE" ]; then
        echo "Crontab file not found: $CRONTAB_FILE"
        exit 1
    fi

    # Show what will be installed
    echo ""
    echo "The following jobs will be installed:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep -v "^#" "$CRONTAB_FILE" | grep -v "^$"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    read -p "Install these cron jobs? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        crontab "$CRONTAB_FILE"
        echo -e "${GREEN}✓${NC} Cron jobs installed"
        echo ""
        echo "View with: crontab -l"
        echo "Remove with: crontab -r"
    else
        echo "Cancelled"
    fi
}

show_help() {
    cat << EOF
${BOLD}Dharmic Agent DevOps Management${NC}

${BOLD}USAGE:${NC}
  dharmic-ops <command> [options]

${BOLD}SERVICE MANAGEMENT:${NC}
  start             Start the daemon
  stop              Stop the daemon
  restart [--force] Restart the daemon (--force to kill if needed)
  status            Show current status
  install           Install as macOS LaunchAgent
  uninstall         Remove LaunchAgent

${BOLD}MONITORING:${NC}
  health            Run health check
  dashboard [mode]  Show status dashboard
                    Modes: terminal (default), web, watch, json
  logs [type]       Tail log files
                    Types: daemon, runtime, email, all, alerts

${BOLD}MAINTENANCE:${NC}
  backup            Create memory backup
  restore [file]    Restore from backup (default: latest)
  rotate-logs       Rotate and compress old logs
  troubleshoot      Run diagnostic checks

${BOLD}AUTOMATION:${NC}
  cron-install      Install cron jobs for monitoring/backups

${BOLD}EXAMPLES:${NC}
  dharmic-ops start
  dharmic-ops dashboard watch
  dharmic-ops logs daemon
  dharmic-ops backup
  dharmic-ops troubleshoot

${BOLD}QUICK STATUS:${NC}
  dharmic-ops        # Same as 'dharmic-ops status'

${BOLD}FILES:${NC}
  Project:    $PROJECT_ROOT
  Scripts:    $SCRIPT_DIR
  Logs:       $PROJECT_ROOT/logs
  Memory:     $PROJECT_ROOT/memory
  Backups:    $PROJECT_ROOT/backups

EOF
}

main() {
    # Make all scripts executable
    chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true

    # No arguments = show status
    if [ $# -eq 0 ]; then
        show_banner
        echo ""
        cmd_status
        exit 0
    fi

    COMMAND="$1"
    shift

    case "$COMMAND" in
        start)
            cmd_start "$@"
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart "$@"
            ;;
        status|s)
            cmd_status
            ;;
        health|check)
            cmd_health
            ;;
        logs|log|l)
            cmd_logs "$@"
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$@"
            ;;
        install)
            cmd_install
            ;;
        uninstall)
            cmd_uninstall
            ;;
        rotate-logs)
            cmd_rotate_logs
            ;;
        dashboard|dash|d)
            cmd_dashboard "$@"
            ;;
        troubleshoot|trouble|t)
            cmd_troubleshoot
            ;;
        cron-install|cron)
            cmd_cron_install
            ;;
        help|h|-h|--help)
            show_help
            ;;
        *)
            echo "Unknown command: $COMMAND"
            echo "Use 'dharmic-ops help' for usage"
            exit 1
            ;;
    esac
}

main "$@"
