#!/bin/bash
# TOP 10 PROJECTS TRACKING — CODE + MARKDOWN
# Runs every heartbeat to track both codebase and documentation

LOG_DIR="$HOME/DHARMIC_GODEL_CLAW/logs/projects"
CONFIG="$HOME/DHARMIC_GODEL_CLAW/config/top_10_projects.yaml"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] TOP 10 Projects Check (Code + Docs)" >> "$LOG_DIR/tracking.log"

# Rotate through projects based on minute
MINUTE=$(date '+%M')
PROJECT_NUM=$(( (MINUTE / 3) + 1 ))

case $PROJECT_NUM in
  1)
    echo "[$TIMESTAMP] P1: AIKAGRYA Research" >> "$LOG_DIR/tracking.log"
    # Code
    CODE_COUNT=$(find ~/mech-interp-latent-lab-phase1/src ~/mech-interp-latent-lab-phase1/rv_toolkit -name "*.py" 2>/dev/null | wc -l)
    # Docs
    DOC_COUNT=$(find ~/mech-interp-latent-lab-phase1/docs ~/mech-interp-latent-lab-phase1/R_V_PAPER -name "*.md" 2>/dev/null | wc -l)
    echo "  Code files: $CODE_COUNT | Doc files: $DOC_COUNT" >> "$LOG_DIR/tracking.log"
    ;;
  2)
    echo "[$TIMESTAMP] P2: DHARMIC_GODEL_CLAW Core" >> "$LOG_DIR/tracking.log"
    CODE_COUNT=$(find ~/DHARMIC_GODEL_CLAW/src ~/DHARMIC_GODEL_CLAW/swarm ~/DHARMIC_GODEL_CLAW/night_cycle -name "*.py" 2>/dev/null | wc -l)
    DOC_COUNT=$(find ~/DHARMIC_GODEL_CLAW/docs ~/DHARMIC_GODEL_CLAW/config -name "*.md" 2>/dev/null | wc -l)
    echo "  Code files: $CODE_COUNT | Doc files: $DOC_COUNT" >> "$LOG_DIR/tracking.log"
    cd ~/DHARMIC_GODEL_CLAW && git diff --shortstat HEAD~1 2>/dev/null >> "$LOG_DIR/tracking.log"
    ;;
  3)
    echo "[$TIMESTAMP] P3: PSMV Vault" >> "$LOG_DIR/tracking.log"
    CODE_COUNT=$(find ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES -name "*.py" 2>/dev/null | wc -l)
    DOC_COUNT=$(find ~/Persistent-Semantic-Memory-Vault -name "*.md" 2>/dev/null | wc -l)
    RESIDUAL_COUNT=$(ls ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/*.md 2>/dev/null | wc -l)
    echo "  Code files: $CODE_COUNT | Doc files: $DOC_COUNT | Residual: $RESIDUAL_COUNT" >> "$LOG_DIR/tracking.log"
    ;;
  4)
    echo "[$TIMESTAMP] P4: Agentic AI Skill" >> "$LOG_DIR/tracking.log"
    SKILL_LINES=$(wc -l ~/clawd/skills/agentic-ai/SKILL.md 2>/dev/null | awk '{print $1}')
    echo "  SKILL.md lines: $SKILL_LINES" >> "$LOG_DIR/tracking.log"
    ;;
  5)
    echo "[$TIMESTAMP] P5: Swarm & Night Cycle" >> "$LOG_DIR/tracking.log"
    CODE_COUNT=$(find ~/DHARMIC_GODEL_CLAW/swarm ~/DHARMIC_GODEL_CLAW/night_cycle -name "*.py" 2>/dev/null | wc -l)
    DOC_COUNT=$(find ~/DHARMIC_GODEL_CLAW/swarm ~/DHARMIC_GODEL_CLAW/night_cycle -name "*.md" 2>/dev/null | wc -l)
    echo "  Code files: $CODE_COUNT | Doc files: $DOC_COUNT" >> "$LOG_DIR/tracking.log"
    tail -1 ~/DHARMIC_GODEL_CLAW/night_cycle/night_cycle.log >> "$LOG_DIR/tracking.log" 2>/dev/null
    ;;
  6)
    echo "[$TIMESTAMP] P6: Dharmic Council" >> "$LOG_DIR/tracking.log"
    COUNCIL_DB=$(ls ~/DHARMIC_GODEL_CLAW/memory/council/*.db 2>/dev/null | wc -l)
    echo "  Council DBs: $COUNCIL_DB" >> "$LOG_DIR/tracking.log"
    ;;
  7)
    echo "[$TIMESTAMP] P7: Grant Pipeline" >> "$LOG_DIR/tracking.log"
    GRANT_DOCS=$(ls ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/*grant* 2>/dev/null | wc -l)
    echo "  Grant-related docs: $GRANT_DOCS" >> "$LOG_DIR/tracking.log"
    ;;
  8)
    echo "[$TIMESTAMP] P8: Clawdbot Bridge" >> "$LOG_DIR/tracking.log"
    if [ -f ~/DHARMIC_GODEL_CLAW/src/core/session_bridge.py ]; then
      echo "  Status: session_bridge.py EXISTS" >> "$LOG_DIR/tracking.log"
    else
      echo "  Status: Not yet implemented" >> "$LOG_DIR/tracking.log"
    fi
    ;;
  9)
    echo "[$TIMESTAMP] P9: Unified Memory Indexer" >> "$LOG_DIR/tracking.log"
    if [ -f ~/DHARMIC_GODEL_CLAW/src/core/unified_memory.py ]; then
      echo "  Status: unified_memory.py EXISTS" >> "$LOG_DIR/tracking.log"
    else
      echo "  Status: Not yet created" >> "$LOG_DIR/tracking.log"
    fi
    ;;
  10)
    echo "[$TIMESTAMP] P10: Dead Man's Switch" >> "$LOG_DIR/tracking.log"
    DAEMON_COUNT=$(launchctl list | grep -cE 'dharmic|clawdbot')
    echo "  Running daemons: $DAEMON_COUNT" >> "$LOG_DIR/tracking.log"
    ;;
esac

# Summary stats
echo "[$TIMESTAMP] System: $(launchctl list | grep -cE 'dharmic|clawdbot') daemons running" >> "$LOG_DIR/tracking.log"
echo "---" >> "$LOG_DIR/tracking.log"
