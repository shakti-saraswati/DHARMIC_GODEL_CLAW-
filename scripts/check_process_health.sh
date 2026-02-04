#!/bin/bash
# DHARMIC_CLAW Process Health Check
# Monitors expected daemons and alerts on orphans

EXPECTED_DAEMONS=("dharmic_claw_heartbeat" "clawdbot_watchdog")
FORBIDDEN_DAEMONS=("unified_daemon" "integrated_daemon" "src/core/daemon.py")

echo "==================================================================="
echo "DHARMIC_CLAW Process Health Check"
echo "==================================================================="
date
echo ""

# Check expected daemons
echo "=== EXPECTED DAEMONS ==="
for daemon in "${EXPECTED_DAEMONS[@]}"; do
    pid=$(pgrep -f "$daemon" | head -1)
    if [ -z "$pid" ]; then
        echo "❌ MISSING: $daemon not running"
        ALERT=1
    else
        mem=$(ps -p "$pid" -o rss= | awk '{print $1/1024 " MB"}')
        echo "✓ RUNNING: $daemon (PID $pid, MEM $mem)"
    fi
done

echo ""
echo "=== ORPHAN CHECK ==="
ORPHANS_FOUND=0

for daemon in "${FORBIDDEN_DAEMONS[@]}"; do
    pids=$(pgrep -f "$daemon")
    if [ -n "$pids" ]; then
        for pid in $pids; do
            cmd=$(ps -p "$pid" -o command= 2>/dev/null)
            # Skip if it's actually dharmic_claw_heartbeat
            if [[ "$cmd" != *"dharmic_claw_heartbeat"* ]]; then
                echo "⚠️  ORPHAN: $daemon running (PID $pid)"
                echo "    Command: $cmd"
                ORPHANS_FOUND=1
            fi
        done
    fi
done

if [ $ORPHANS_FOUND -eq 0 ]; then
    echo "✓ No orphan processes found"
fi

echo ""
echo "=== LAUNCHAGENTS STATUS ==="
launchctl list | grep dharmic | while read line; do
    echo "$line"
done

echo ""
echo "=== RESOURCE SUMMARY ==="
TOTAL_MEM=0
ps aux | grep -E "(dharmic_claw_heartbeat|clawdbot_watchdog)" | grep -v grep | while read line; do
    PID=$(echo "$line" | awk '{print $2}')
    RSS=$(echo "$line" | awk '{print $6}')
    CMD=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
    MEM_MB=$(echo "scale=2; $RSS/1024" | bc)
    echo "PID $PID: ${MEM_MB}MB - $CMD"
    TOTAL_MEM=$(echo "$TOTAL_MEM + $MEM_MB" | bc)
done
echo "Total memory: ${TOTAL_MEM}MB"

echo ""
echo "==================================================================="
