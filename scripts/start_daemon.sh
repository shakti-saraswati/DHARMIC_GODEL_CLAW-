#!/bin/bash
#
# Start the Dharmic Agent Daemon
#
# Usage:
#   ./start_daemon.sh           # Start with defaults (1 hour heartbeat)
#   ./start_daemon.sh --fast    # Start with 5 minute heartbeat (for testing)
#   ./start_daemon.sh --stop    # Stop the daemon
#   ./start_daemon.sh --status  # Check daemon status
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"
DAEMON_PATH="$PROJECT_ROOT/src/core/daemon.py"
PID_FILE="$PROJECT_ROOT/logs/daemon.pid"
STATUS_FILE="$PROJECT_ROOT/logs/daemon_status.json"
LOG_DIR="$PROJECT_ROOT/logs"

# Create logs directory if needed
mkdir -p "$LOG_DIR"

# Check for commands
case "$1" in
    --stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            echo "Stopping daemon (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null
            sleep 2
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Process still running, sending SIGKILL..."
                kill -KILL "$PID" 2>/dev/null
            fi
            rm -f "$PID_FILE"
            echo "Daemon stopped"
        else
            echo "No daemon running (no PID file)"
        fi
        exit 0
        ;;

    --status)
        if [ -f "$STATUS_FILE" ]; then
            echo "=== Daemon Status ==="
            cat "$STATUS_FILE"
            echo ""
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if ps -p "$PID" > /dev/null 2>&1; then
                    echo "Process $PID is RUNNING"
                else
                    echo "Process $PID is NOT RUNNING (stale PID file)"
                fi
            fi
        else
            echo "No status file found"
        fi
        exit 0
        ;;

    --fast)
        HEARTBEAT=300  # 5 minutes
        ;;

    *)
        HEARTBEAT=3600  # 1 hour
        ;;
esac

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Daemon already running (PID: $PID)"
        echo "Use --stop to stop it first"
        exit 1
    else
        echo "Removing stale PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Check venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "ERROR: Virtual environment not found at $VENV_PATH"
    echo "Run: python3 -m venv $VENV_PATH && $VENV_PATH/bin/pip install -r $PROJECT_ROOT/requirements.txt"
    exit 1
fi

# Activate venv and start daemon
echo "Starting Dharmic Agent Daemon..."
echo "  Heartbeat: ${HEARTBEAT}s"
echo "  Log dir: $LOG_DIR"
echo ""

source "$VENV_PATH/bin/activate"

# Start in background with nohup
nohup python3 "$DAEMON_PATH" --heartbeat "$HEARTBEAT" --verbose \
    >> "$LOG_DIR/daemon_stdout.log" 2>&1 &

DAEMON_PID=$!
echo "$DAEMON_PID" > "$PID_FILE"

sleep 2

# Check if it started successfully
if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
    echo "Daemon started successfully (PID: $DAEMON_PID)"
    echo ""
    echo "Commands:"
    echo "  ./start_daemon.sh --status   # Check status"
    echo "  ./start_daemon.sh --stop     # Stop daemon"
    echo "  tail -f $LOG_DIR/daemon_*.log  # Watch logs"
else
    echo "ERROR: Daemon failed to start"
    echo "Check logs: $LOG_DIR/daemon_stdout.log"
    exit 1
fi
