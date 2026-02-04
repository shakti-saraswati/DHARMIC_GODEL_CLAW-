#!/bin/bash
# Unified swarm invocation from any context
# Usage: ./invoke_swarm.sh [dgc|psmv] [cycles|thread] [dry-run:true|false]

set -e

SWARM_TYPE="${1:-dgc}"
PARAM2="${2:-1}"
DRY_RUN="${3:-true}"

echo "=========================================="
echo "DHARMIC SWARM INVOCATION"
echo "=========================================="
echo "Type: $SWARM_TYPE"
echo "Parameter: $PARAM2"
echo "Dry Run: $DRY_RUN"
echo ""

if [ "$SWARM_TYPE" = "dgc" ]; then
    CYCLES="$PARAM2"
    echo "Invoking DGC Swarm (code improvement)..."
    echo "Cycles: $CYCLES"
    echo ""

    cd ~/DHARMIC_GODEL_CLAW/swarm

    if [ "$DRY_RUN" = "true" ]; then
        python3 run_swarm.py --cycles "$CYCLES" --dry-run
    else
        echo "WARNING: Running in LIVE mode - will modify code!"
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Cancelled."
            exit 0
        fi
        python3 run_swarm.py --cycles "$CYCLES" --live
    fi

elif [ "$SWARM_TYPE" = "psmv" ]; then
    THREAD="$PARAM2"
    echo "Invoking PSMV Triadic Swarm (research contribution)..."
    echo "Thread: $THREAD"
    echo ""

    cd ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES
    python3 triadic_swarm.py --once --thread "$THREAD"

elif [ "$SWARM_TYPE" = "shakti" ]; then
    echo "Invoking Shakti Orchestrator (event-driven meta-layer)..."
    echo ""

    cd ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES
    python3 shakti_orchestrator.py --dry-run

else
    echo "Unknown swarm type: $SWARM_TYPE"
    echo ""
    echo "Usage: $0 [dgc|psmv|shakti] [cycles/thread] [true|false]"
    echo ""
    echo "Examples:"
    echo "  $0 dgc 3 true          # DGC swarm, 3 cycles, dry-run"
    echo "  $0 dgc 1 false         # DGC swarm, 1 cycle, LIVE"
    echo "  $0 psmv mechanistic    # PSMV swarm, mechanistic thread"
    echo "  $0 shakti              # Shakti orchestrator"
    exit 1
fi

echo ""
echo "=========================================="
echo "SWARM INVOCATION COMPLETE"
echo "=========================================="
