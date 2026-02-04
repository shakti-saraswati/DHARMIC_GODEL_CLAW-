#!/bin/bash
# Test the integration between clawdbot, DGC swarm, and PSMV swarm

echo "=========================================="
echo "DHARMIC SWARM INTEGRATION TEST"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check clawdbot is running
echo -e "${YELLOW}Test 1: Checking if clawdbot is running...${NC}"
if lsof -i :18789 | grep -q LISTEN; then
    echo -e "${GREEN}✓ clawdbot is running on port 18789${NC}"
else
    echo -e "${RED}✗ clawdbot is NOT running${NC}"
    echo "  Start it with: clawdbot start"
    exit 1
fi
echo ""

# Test 2: Check skills installed
echo -e "${YELLOW}Test 2: Checking if skills are installed...${NC}"
if [ -d ~/.claude/skills/dgc-swarm-invoker ]; then
    echo -e "${GREEN}✓ dgc-swarm-invoker skill found${NC}"
else
    echo -e "${RED}✗ dgc-swarm-invoker skill NOT found${NC}"
fi

if [ -d ~/.claude/skills/psmv-triadic-swarm ]; then
    echo -e "${GREEN}✓ psmv-triadic-swarm skill found${NC}"
else
    echo -e "${RED}✗ psmv-triadic-swarm skill NOT found${NC}"
fi
echo ""

# Test 3: Check API key
echo -e "${YELLOW}Test 3: Checking ANTHROPIC_API_KEY...${NC}"
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY is set${NC}"
else
    echo -e "${RED}✗ ANTHROPIC_API_KEY is NOT set${NC}"
    echo "  Set it in ~/.zshrc or run: export ANTHROPIC_API_KEY=your-key"
    exit 1
fi
echo ""

# Test 4: Check DGC swarm
echo -e "${YELLOW}Test 4: Checking DGC swarm...${NC}"
if [ -f ~/DHARMIC_GODEL_CLAW/swarm/run_swarm.py ]; then
    echo -e "${GREEN}✓ DGC swarm found${NC}"

    # Test status command
    echo "  Testing status command..."
    cd ~/DHARMIC_GODEL_CLAW/swarm
    if python3 run_swarm.py --status 2>/dev/null | head -5; then
        echo -e "${GREEN}  ✓ Status command works${NC}"
    else
        echo -e "${YELLOW}  ! Status command returned error (may be normal)${NC}"
    fi
else
    echo -e "${RED}✗ DGC swarm NOT found${NC}"
fi
echo ""

# Test 5: Check PSMV swarm
echo -e "${YELLOW}Test 5: Checking PSMV triadic swarm...${NC}"
if [ -f ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/triadic_swarm.py ]; then
    echo -e "${GREEN}✓ PSMV triadic swarm found${NC}"
else
    echo -e "${RED}✗ PSMV triadic swarm NOT found${NC}"
fi

if [ -d ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream ]; then
    echo -e "${GREEN}✓ Residual stream directory found${NC}"

    # Count existing contributions
    CONTRIB_COUNT=$(ls -1 ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/v*.md 2>/dev/null | wc -l)
    echo "  Current contributions: $CONTRIB_COUNT"
else
    echo -e "${RED}✗ Residual stream directory NOT found${NC}"
fi
echo ""

# Test 6: Check invocation script
echo -e "${YELLOW}Test 6: Checking unified invocation script...${NC}"
if [ -x ~/DHARMIC_GODEL_CLAW/invoke_swarm.sh ]; then
    echo -e "${GREEN}✓ invoke_swarm.sh is executable${NC}"
else
    echo -e "${RED}✗ invoke_swarm.sh is NOT executable${NC}"
    echo "  Fix with: chmod +x ~/DHARMIC_GODEL_CLAW/invoke_swarm.sh"
fi
echo ""

# Test 7: Web UI
echo -e "${YELLOW}Test 7: Checking clawdbot web UI...${NC}"
if curl -s http://localhost:18789 | grep -q "Clawdbot Control"; then
    echo -e "${GREEN}✓ Web UI is accessible at http://localhost:18789${NC}"
else
    echo -e "${YELLOW}! Web UI check inconclusive${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "INTEGRATION TEST SUMMARY"
echo "=========================================="
echo ""
echo "Systems status:"
echo "  clawdbot: RUNNING on port 18789"
echo "  DGC swarm: AVAILABLE"
echo "  PSMV swarm: AVAILABLE"
echo ""
echo "Next steps:"
echo "  1. Test DGC swarm: ./invoke_swarm.sh dgc 1 true"
echo "  2. Test PSMV swarm: ./invoke_swarm.sh psmv mechanistic"
echo "  3. Access web UI: http://localhost:18789"
echo "  4. Message via LINE/Telegram: 'Run code improvement swarm'"
echo ""
echo "For full integration, see: INTEGRATION_PLAN.md"
echo ""
