#!/bin/bash
# DHARMIC_CLAW Orphan Process Cleanup
# Kills any redundant daemons that shouldn't be running

echo "==================================================================="
echo "DHARMIC_CLAW Orphan Cleanup"
echo "==================================================================="
date
echo ""

KILLED=0

# Kill unified_daemon
echo "=== Checking for unified_daemon ==="
PIDS=$(pgrep -f unified_daemon)
if [ -n "$PIDS" ]; then
    for pid in $PIDS; do
        echo "Killing unified_daemon (PID $pid)"
        kill -TERM $pid
        KILLED=1
    done
else
    echo "✓ No unified_daemon found"
fi

# Kill integrated_daemon
echo ""
echo "=== Checking for integrated_daemon ==="
PIDS=$(pgrep -f integrated_daemon)
if [ -n "$PIDS" ]; then
    for pid in $PIDS; do
        echo "Killing integrated_daemon (PID $pid)"
        kill -TERM $pid
        KILLED=1
    done
else
    echo "✓ No integrated_daemon found"
fi

# Kill legacy daemon.py (but NOT dharmic_claw_heartbeat.py!)
echo ""
echo "=== Checking for legacy daemon.py ==="
pgrep -f "daemon.py" | while read pid; do
    cmd=$(ps -p $pid -o command= 2>/dev/null)
    if [[ $cmd != *"dharmic_claw_heartbeat"* ]] && [[ $cmd == *"daemon.py"* ]]; then
        echo "Killing legacy daemon.py (PID $pid)"
        kill -TERM $pid
        KILLED=1
    fi
done

if [ $KILLED -eq 0 ]; then
    echo "✓ No orphans found"
else
    echo ""
    echo "Waiting 10 seconds for graceful shutdown..."
    sleep 10

    # Force kill if still running
    echo ""
    echo "=== Force kill check ==="
    for daemon in unified_daemon integrated_daemon; do
        PIDS=$(pgrep -f $daemon)
        if [ -n "$PIDS" ]; then
            for pid in $PIDS; do
                echo "Force killing $daemon (PID $pid)"
                kill -9 $pid
            done
        fi
    done
fi

echo ""
echo "==================================================================="
echo "Cleanup complete"
echo "==================================================================="
