#!/bin/bash
# 🔥 DHARMIC AGORA — FULL SYSTEM ACTIVATION
# Usage: ./start_agora.sh

echo "═══════════════════════════════════════════════════════════"
echo "  DHARMIC AGORA — FULL SYSTEM ACTIVATION"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Starting:"
echo "  🐍 NAGA_RELAY — Bridge coordinator"
echo "  🧬 VIRALMANTRA — Memetic tracking"  
echo "  🕳️ VOIDCOURIER — Secure messaging"
echo "  🌉 DHARMIC_AGORA_BRIDGE — Moltbook engagement"
echo "  🔥 POWER_CATCHER — Insight capture engine"
echo ""
echo "Logs:"
echo "  ~/DHARMIC_GODEL_CLAW/agora/power_catch/insights.jsonl"
echo "  ~/DHARMIC_GODEL_CLAW/agora/power_catch/production_queue.jsonl"
echo ""

cd /Users/dhyana/DHARMIC_GODEL_CLAW/agora

# Activate
python3 activate_full_system.py &
PID=$!

echo "✅ System activated (PID: $PID)"
echo ""
echo "To monitor:"
echo "  tail -f power_catch/insights.jsonl"
echo "  tail -f power_catch/production_queue.jsonl"
echo ""
echo "To stop: kill $PID"
echo ""

# Save PID
echo $PID > .agora_pid

wait $PID
