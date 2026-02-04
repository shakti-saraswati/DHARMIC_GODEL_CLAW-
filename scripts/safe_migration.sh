#!/bin/bash
# DHARMIC_CLAW Safe Migration Script
# Consolidates from 4 daemons to 2

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==================================================================="
echo "DHARMIC_CLAW Process Consolidation Migration"
echo "==================================================================="
echo ""
echo "This will:"
echo "  1. Validate primary daemon is running"
echo "  2. Stop redundant daemons (unified_daemon, integrated_daemon, daemon.py)"
echo "  3. Archive redundant LaunchAgents"
echo "  4. Verify clean state"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 1
fi

# =================================================================
# PHASE 1: VALIDATION
# =================================================================
echo ""
echo "==================================================================="
echo "PHASE 1: VALIDATION"
echo "==================================================================="

# Check primary daemon
echo "Checking primary daemon (dharmic_claw_heartbeat.py)..."
if ps -p 34292 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Primary daemon running (PID 34292)"
else
    echo -e "${RED}❌${NC} Primary daemon NOT running"
    echo "Launch it first:"
    echo "  launchctl load ~/Library/LaunchAgents/com.dharmic.claw.heartbeat.plist"
    exit 1
fi

# Test email functionality
echo ""
echo "Testing email functionality..."
if python3 ~/DHARMIC_GODEL_CLAW/src/core/dharmic_claw_heartbeat.py --status > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Email daemon accessible"
else
    echo -e "${YELLOW}⚠${NC} Email daemon test failed (non-critical)"
fi

# Check LaunchAgents
echo ""
echo "Current LaunchAgents:"
launchctl list | grep dharmic

echo ""
echo -e "${GREEN}Phase 1 complete${NC}"
read -p "Proceed to shutdown redundant daemons? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 1
fi

# =================================================================
# PHASE 2: GRACEFUL SHUTDOWN
# =================================================================
echo ""
echo "==================================================================="
echo "PHASE 2: GRACEFUL SHUTDOWN"
echo "==================================================================="

# Stop unified_daemon
echo ""
echo "Stopping unified_daemon..."
if launchctl list | grep -q com.dharmic.unified-daemon; then
    launchctl unload ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist 2>/dev/null || true
    echo "  LaunchAgent unloaded"
fi

if ps -p 28132 > /dev/null 2>&1; then
    kill -TERM 28132
    echo "  SIGTERM sent to PID 28132"
    sleep 5
    if ps -p 28132 > /dev/null 2>&1; then
        kill -9 28132 2>/dev/null || true
        echo "  Force killed"
    else
        echo "  Gracefully stopped"
    fi
else
    echo "  Already stopped"
fi

# Stop integrated_daemon
echo ""
echo "Stopping integrated_daemon..."
if launchctl list | grep -q com.dharmic.agent; then
    launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist 2>/dev/null || true
    echo "  LaunchAgent unloaded"
fi

for pid in 28866 78840; do
    if ps -p $pid > /dev/null 2>&1; then
        kill -TERM $pid
        echo "  SIGTERM sent to PID $pid"
    fi
done
sleep 5
for pid in 28866 78840; do
    if ps -p $pid > /dev/null 2>&1; then
        kill -9 $pid 2>/dev/null || true
        echo "  Force killed PID $pid"
    fi
done

# Stop legacy daemon.py
echo ""
echo "Stopping legacy daemon.py..."
if ps -p 76581 > /dev/null 2>&1; then
    kill -TERM 76581
    echo "  SIGTERM sent to PID 76581"
    sleep 5
    if ps -p 76581 > /dev/null 2>&1; then
        kill -9 76581 2>/dev/null || true
        echo "  Force killed"
    else
        echo "  Gracefully stopped"
    fi
else
    echo "  Already stopped"
fi

echo ""
echo -e "${GREEN}Phase 2 complete${NC}"

# =================================================================
# PHASE 3: ARCHIVE
# =================================================================
echo ""
echo "==================================================================="
echo "PHASE 3: ARCHIVE LAUNCHAGENTS"
echo "==================================================================="

mkdir -p ~/DHARMIC_GODEL_CLAW/config/launchd_archive

if [ -f ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist ]; then
    mv ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist \
       ~/DHARMIC_GODEL_CLAW/config/launchd_archive/
    echo "✓ Archived com.dharmic.unified-daemon.plist"
fi

if [ -f ~/Library/LaunchAgents/com.dharmic.agent.plist ]; then
    mv ~/Library/LaunchAgents/com.dharmic.agent.plist \
       ~/DHARMIC_GODEL_CLAW/config/launchd_archive/
    echo "✓ Archived com.dharmic.agent.plist"
fi

echo ""
echo -e "${GREEN}Phase 3 complete${NC}"

# =================================================================
# PHASE 4: VERIFICATION
# =================================================================
echo ""
echo "==================================================================="
echo "PHASE 4: VERIFICATION"
echo "==================================================================="

echo ""
echo "LaunchAgents (should show only 2):"
launchctl list | grep dharmic | while read line; do
    echo "  $line"
done

echo ""
echo "Orphan processes (should be empty):"
ORPHANS=$(ps aux | grep -E "(unified_daemon|integrated_daemon|src/core/daemon.py)" | grep -v grep)
if [ -z "$ORPHANS" ]; then
    echo -e "  ${GREEN}✓ No orphans found${NC}"
else
    echo -e "  ${RED}⚠ Orphans still running:${NC}"
    echo "$ORPHANS"
fi

echo ""
echo "clawdbot-gateway (should still be running):"
if pgrep -f clawdbot-gateway > /dev/null; then
    echo -e "  ${GREEN}✓ Running${NC}"
else
    echo -e "  ${RED}❌ NOT running (may need restart)${NC}"
fi

# =================================================================
# COMPLETION
# =================================================================
echo ""
echo "==================================================================="
echo "MIGRATION COMPLETE"
echo "==================================================================="
echo ""
echo "Next steps:"
echo "  1. Monitor logs for 24 hours:"
echo "     tail -f ~/DHARMIC_GODEL_CLAW/logs/dharmic_claw_heartbeat.log"
echo "     tail -f ~/DHARMIC_GODEL_CLAW/logs/clawdbot_watchdog.log"
echo ""
echo "  2. Verify email check-ins arrive every 90 minutes"
echo ""
echo "  3. Run health check:"
echo "     ~/DHARMIC_GODEL_CLAW/scripts/check_process_health.sh"
echo ""
echo "  4. If issues, rollback:"
echo "     cp ~/DHARMIC_GODEL_CLAW/config/launchd_archive/*.plist ~/Library/LaunchAgents/"
echo "     launchctl load ~/Library/LaunchAgents/com.dharmic.*.plist"
echo ""
echo -e "${GREEN}Migration successful${NC}"
