#!/bin/bash
#
# Install Dharmic Agent as macOS LaunchAgent
#
# This makes the daemon auto-start on login and restart on crashes
#
# Usage:
#   ./install_service.sh              # Install and start
#   ./install_service.sh --uninstall  # Remove service
#   ./install_service.sh --status     # Check service status
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PLIST_SOURCE="$SCRIPT_DIR/com.dharmic.agent.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.dharmic.agent.plist"
SERVICE_NAME="com.dharmic.agent"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INSTALL]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check virtual environment
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        error "Virtual environment not found at $PROJECT_ROOT/.venv"
        error "Run: python3 -m venv $PROJECT_ROOT/.venv"
        exit 1
    fi

    # Check daemon script
    if [ ! -f "$PROJECT_ROOT/src/core/daemon.py" ]; then
        error "Daemon script not found: $PROJECT_ROOT/src/core/daemon.py"
        exit 1
    fi

    # Check plist file
    if [ ! -f "$PLIST_SOURCE" ]; then
        error "Plist file not found: $PLIST_SOURCE"
        exit 1
    fi

    log "Prerequisites OK"
}

install_service() {
    log "Installing Dharmic Agent service..."

    # Create LaunchAgents directory if needed
    mkdir -p "$HOME/Library/LaunchAgents"

    # Check if already installed
    if [ -f "$PLIST_DEST" ]; then
        warn "Service already installed, unloading first..."
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
    fi

    # Copy plist
    log "Copying plist to $PLIST_DEST"
    cp "$PLIST_SOURCE" "$PLIST_DEST"

    # Load service
    log "Loading service..."
    if launchctl load "$PLIST_DEST"; then
        log "Service installed successfully"

        # Wait a moment for startup
        sleep 3

        # Check status
        if launchctl list | grep -q "$SERVICE_NAME"; then
            log "Service is running"
            return 0
        else
            error "Service installed but not running"
            return 1
        fi
    else
        error "Failed to load service"
        return 1
    fi
}

uninstall_service() {
    log "Uninstalling Dharmic Agent service..."

    if [ ! -f "$PLIST_DEST" ]; then
        warn "Service not installed"
        return 0
    fi

    # Unload service
    log "Unloading service..."
    if launchctl unload "$PLIST_DEST" 2>/dev/null; then
        log "Service unloaded"
    else
        warn "Service was not loaded"
    fi

    # Remove plist
    log "Removing plist..."
    rm -f "$PLIST_DEST"

    log "Service uninstalled successfully"
}

show_status() {
    echo "=========================================="
    echo "Dharmic Agent Service Status"
    echo "=========================================="
    echo ""

    # Check if plist exists
    if [ -f "$PLIST_DEST" ]; then
        echo "Installation: INSTALLED"
        echo "Plist: $PLIST_DEST"
    else
        echo "Installation: NOT INSTALLED"
        echo ""
        echo "To install: $0"
        return 0
    fi

    echo ""

    # Check if loaded
    if launchctl list | grep -q "$SERVICE_NAME"; then
        echo "Service: LOADED"

        # Get PID
        PID=$(launchctl list | grep "$SERVICE_NAME" | awk '{print $1}')
        if [ "$PID" != "-" ]; then
            echo "PID: $PID"

            # Get process info
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Status: RUNNING"

                # Get uptime
                START_TIME=$(ps -p "$PID" -o lstart= 2>/dev/null || echo "")
                if [ -n "$START_TIME" ]; then
                    START_TS=$(date -j -f "%a %b %d %T %Y" "$START_TIME" +%s 2>/dev/null || echo "0")
                    NOW_TS=$(date +%s)
                    UPTIME=$((NOW_TS - START_TS))
                    MINS=$((UPTIME / 60))
                    echo "Uptime: ${MINS} minutes"
                fi
            else
                echo "Status: NOT RUNNING (PID exists but process dead)"
            fi
        else
            echo "Status: LOADED BUT NOT STARTED"
        fi
    else
        echo "Service: NOT LOADED"
    fi

    echo ""

    # Check logs
    if [ -f "$PROJECT_ROOT/logs/launchd_stdout.log" ]; then
        echo "Recent logs:"
        echo "----------------------------------------"
        tail -10 "$PROJECT_ROOT/logs/launchd_stdout.log"
    fi

    echo ""
    echo "=========================================="
    echo "Commands:"
    echo "  launchctl unload ~/Library/LaunchAgents/$SERVICE_NAME.plist  # Stop"
    echo "  launchctl load ~/Library/LaunchAgents/$SERVICE_NAME.plist    # Start"
    echo "  tail -f $PROJECT_ROOT/logs/*.log                              # View logs"
    echo "=========================================="
}

enable_autostart() {
    log "Configuring auto-start on login..."

    if [ -f "$PLIST_DEST" ]; then
        # Enable by setting Disabled to false
        /usr/libexec/PlistBuddy -c "Set :Disabled false" "$PLIST_DEST" 2>/dev/null || true
        log "Auto-start enabled"
    else
        error "Service not installed"
        return 1
    fi
}

disable_autostart() {
    log "Disabling auto-start on login..."

    if [ -f "$PLIST_DEST" ]; then
        # Disable by setting Disabled to true
        /usr/libexec/PlistBuddy -c "Set :Disabled true" "$PLIST_DEST" 2>/dev/null || true

        # Reload to apply changes
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        launchctl load "$PLIST_DEST" 2>/dev/null || true

        log "Auto-start disabled"
    else
        error "Service not installed"
        return 1
    fi
}

main() {
    case "${1:-install}" in
        --install|install)
            check_prerequisites
            install_service
            enable_autostart
            echo ""
            show_status
            ;;
        --uninstall|uninstall)
            uninstall_service
            ;;
        --status|status)
            show_status
            ;;
        --enable)
            enable_autostart
            ;;
        --disable)
            disable_autostart
            ;;
        --help|help)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  install      Install and start service (default)"
            echo "  uninstall    Uninstall service"
            echo "  status       Show service status"
            echo "  --enable     Enable auto-start on login"
            echo "  --disable    Disable auto-start on login"
            echo "  help         Show this help"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage"
            exit 1
            ;;
    esac
}

main "$@"
