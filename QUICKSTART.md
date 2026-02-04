# Integration Quick Start Guide

**Status**: READY - All systems operational
**Date**: 2026-02-03
**Integration Level**: MINIMAL (today) → FULL (this week)

---

## Current State (Verified)

**OpenClaw note**: `openclaw` is the canonical CLI and `~/.openclaw/openclaw.json` is the canonical config path. Legacy `clawdbot` still works as a shim. See `OPENCLAW_COMPAT.md`.

```
✓ clawdbot running on port 18789
✓ DGC swarm available (~/DHARMIC_GODEL_CLAW/swarm/)
✓ PSMV swarm available (~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/)
✓ Claude skills installed (dgc-swarm-invoker, psmv-triadic-swarm)
✓ ANTHROPIC_API_KEY configured
✓ 127 existing contributions in residual stream
```

---

## Test It Right Now (5 minutes)

### Via Command Line

```bash
# Test 1: DGC swarm (code improvement) - dry run
cd ~/DHARMIC_GODEL_CLAW
./invoke_swarm.sh dgc 1 true

# Test 2: PSMV triadic swarm (research contribution)
./invoke_swarm.sh psmv mechanistic

# Test 3: Check results
ls -lt ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/ | head -5
```

### Via Clawdbot Web UI

1. Open: http://localhost:18789
2. Use the web interface to message the bot
3. Try: "What skills do you have available?"
4. Try: "Show me the status of the DGC swarm"

### Via LINE or Telegram (if configured)

Message the bot:
- "Run the code improvement swarm in dry-run mode"
- "Generate a research contribution on the mechanistic thread"
- "What's the latest contribution in the residual stream?"

---

## How It Works

```
YOU (via LINE/Telegram/Web)
    ↓
clawdbot (localhost:18789)
    ↓
Claude Skills (~/.claude/skills/)
    ↓ ┌──────────────┬─────────────────┐
    ▼ ▼              ▼                 ▼
dgc-swarm-invoker  psmv-triadic-swarm
    │                │
    ▼                ▼
DGC Swarm        PSMV Swarm
(Code)           (Research)
    │                │
    └────────┬───────┘
             ▼
    Shared PSMV Residual Stream
```

---

## Skills Available

### 1. dgc-swarm-invoker

**Purpose**: Invoke the Dharmic Godel Claw self-improvement swarm for code improvements

**Functions**:
- `invokeSwarm({ cycles, dryRun, model })` - Run improvement cycles
- `getSwarmStatus()` - Get current swarm state

**Example Usage** (from clawdbot):
```
"Run 3 cycles of code improvement in dry-run mode"
"Check the DGC swarm status"
"Improve the code with 1 cycle in live mode"
```

### 2. psmv-triadic-swarm

**Purpose**: Invoke PSMV triadic swarm (Gnata-Gneya-Gnan) for research contributions

**Functions**:
- `invokeTriadicSwarm({ thread })` - Generate research contribution
- `readLatestContribution()` - Read most recent contribution
- `getRecentContributions(n)` - List recent contributions

**Example Usage** (from clawdbot):
```
"Generate a research contribution on mechanistic thread"
"Show me the latest contribution"
"List the 10 most recent contributions"
```

---

## Manual Commands

### DGC Swarm (Code Improvement)

```bash
# Via wrapper script
~/DHARMIC_GODEL_CLAW/invoke_swarm.sh dgc 1 true  # 1 cycle, dry-run
~/DHARMIC_GODEL_CLAW/invoke_swarm.sh dgc 3 false # 3 cycles, LIVE

# Direct invocation
cd ~/DHARMIC_GODEL_CLAW/swarm
python3 run_swarm.py --cycles 1 --dry-run
python3 run_swarm.py --status

# Check results
cat ~/DHARMIC_GODEL_CLAW/swarm/results/run_*.json
```

### PSMV Triadic Swarm (Research)

```bash
# Via wrapper script
~/DHARMIC_GODEL_CLAW/invoke_swarm.sh psmv mechanistic

# Direct invocation
cd ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES
python3 triadic_swarm.py --once --thread mechanistic
python3 triadic_swarm.py --once --thread contemplative
python3 triadic_swarm.py --once --thread engineering

# Check results
ls -lt ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/ | head
```

### Shakti Orchestrator (Event-Driven)

```bash
# Via wrapper script
~/DHARMIC_GODEL_CLAW/invoke_swarm.sh shakti

# Direct invocation
cd ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES
python3 shakti_orchestrator.py --dry-run  # Test mode
python3 shakti_orchestrator.py --status   # Show status
python3 shakti_orchestrator.py            # Live mode (event-driven)
```

---

## What Happens When You Run Each Swarm

### DGC Swarm Flow

```
1. PROPOSE: Agent analyzes code, suggests improvement
2. DHARMIC GATE: Check alignment with Akram Vignan principles
3. WRITE: Implement the proposal
4. TEST: Validate changes, measure fitness
5. REFINE: Fix issues if needed
6. EVOLVE: Archive successful changes
```

Output: Modified code in `~/DHARMIC_GODEL_CLAW/swarm/`
Results: JSON logs in `~/DHARMIC_GODEL_CLAW/swarm/results/`

### PSMV Triadic Swarm Flow

```
PHASE 1: Gnata (Knower) forms query based on stream
PHASE 2: Gneya (Knowable) retrieves relevant context
PHASE 3: Gnan (Knowledge) synthesizes contribution
PHASE 4: Triadic consensus evaluation
  - Gnata: Does it answer the query? (fitness)
  - Gneya: Does it cohere with corpus? (coherence)
  - Gnan: Is it quality synthesis? (confidence)

If consensus achieved (all scores >= thresholds):
  → Write to residual stream
Else:
  → Discard
```

Output: New v*.md file in `residual_stream/`
Format: v2-compliant markdown with full metadata

---

## File Locations

### Integration Files (Created Today)

```
~/.claude/skills/dgc-swarm-invoker/
  ├── skill.json
  └── index.js

~/.claude/skills/psmv-triadic-swarm/
  ├── skill.json
  └── index.js

~/DHARMIC_GODEL_CLAW/
  ├── INTEGRATION_PLAN.md     # Full integration plan
  ├── QUICKSTART.md           # This file
  ├── TEST_INTEGRATION.sh     # Test script
  └── invoke_swarm.sh         # Unified CLI wrapper
```

### Swarm Code

```
~/DHARMIC_GODEL_CLAW/swarm/
  ├── run_swarm.py           # DGC entry point
  ├── orchestrator.py        # Main loop
  ├── agents/                # Proposer, Writer, Tester, etc.
  └── results/               # Execution logs

~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/
  ├── triadic_swarm.py       # PSMV entry point
  ├── shakti_orchestrator.py # Event-driven meta-layer
  └── residual_stream/       # Research contributions (127 files)
```

---

## Next Steps

### Today (Minimal Integration - COMPLETE)

- [x] Create Claude skills for both swarms
- [x] Create unified CLI wrapper
- [x] Test all integrations
- [x] Verify clawdbot connectivity

**You can now invoke both swarms from clawdbot!**

### This Week (Full Integration)

See `INTEGRATION_PLAN.md` for:

1. **Day 1-2**: Unified orchestration layer
   - SwarmCoordinator to route tasks
   - Auto-classify code vs research tasks

2. **Day 2-3**: Shared memory layer
   - Cross-system state tracking
   - Link code improvements to research contributions

3. **Day 3-4**: Event bus
   - DGC changes trigger PSMV analysis
   - PSMV insights spawn DGC implementations

4. **Day 4-5**: Monitoring dashboard
   - Real-time status of both swarms
   - Unified view via CLI

---

## Troubleshooting

### Skill not found

```bash
# Restart clawdbot to pick up new skills
pkill -f clawdbot-gateway
clawdbot start
```

### API key issues

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Set temporarily
export ANTHROPIC_API_KEY=your-key-here

# Set permanently (add to ~/.zshrc)
echo 'export ANTHROPIC_API_KEY=your-key-here' >> ~/.zshrc
source ~/.zshrc
```

### Python errors

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip3 install anthropic watchdog
```

### Port already in use

```bash
# Check what's on port 18789
lsof -i :18789

# Kill old clawdbot
pkill -f clawdbot

# Restart
clawdbot start
```

---

## Understanding the Architecture

### Why Three Systems?

1. **clawdbot**: 24/7 gateway, handles messaging, persistent presence
2. **DGC swarm**: Code improvement engine, Darwin-Gödel patterns
3. **PSMV swarm**: Research contribution engine, triadic consensus

### How They Connect

- **Shared API key**: All use same Anthropic account
- **Shared output**: Both write to PSMV residual stream
- **Skill invocation**: clawdbot calls swarms via Node.js skills
- **CLI wrapper**: Direct shell access via `invoke_swarm.sh`

### Benefits of Integration

1. Message "improve the code" → DGC swarm runs
2. Message "research R_V contraction" → PSMV swarm runs
3. Both accessible via LINE/Telegram from anywhere
4. Results automatically stored in residual stream
5. 24/7 operation via clawdbot persistence

---

## Example Conversations

### With clawdbot (via LINE/Telegram)

**You**: "What can you do?"

**Bot**: "I can invoke two swarms:
1. DGC swarm - code improvement (propose → write → test → refine)
2. PSMV triadic swarm - research contributions (Gnata-Gneya-Gnan)

Current status: 127 contributions in residual stream. DGC baseline fitness: 0.5"

**You**: "Run code improvement in dry-run mode"

**Bot**: "Invoking DGC swarm with 1 cycle in dry-run mode..."
[Shows output]
"Completed. No files modified (dry-run). Success rate: 1/1"

**You**: "Generate a research contribution on mechanistic interpretability"

**Bot**: "Invoking PSMV triadic swarm on mechanistic thread..."
[Shows triadic consensus scores]
"Contribution written: v11.7_mechanistic_analysis_triadic_20260203.md"

---

## Performance Notes

- **DGC swarm**: ~2-5 minutes per cycle (depends on complexity)
- **PSMV swarm**: ~3-7 minutes per contribution (3 LLM calls + consensus)
- **Shakti orchestrator**: Event-driven, responds within seconds
- **Clawdbot response**: ~1-2 seconds to invoke, then swarm time

---

## Security & Safety

1. **Dry-run by default**: All DGC operations start in dry-run
2. **Manual approval**: Human reviews before --live execution
3. **Triadic consensus**: PSMV requires all 3 agents to agree
4. **Dharmic gate**: DGC has ethical alignment filter
5. **Event logging**: Full audit trail of all operations
6. **Rollback**: DGC swarm can revert changes

---

## Resources

- **Integration Plan**: `~/DHARMIC_GODEL_CLAW/INTEGRATION_PLAN.md`
- **DGC Swarm Code**: `~/DHARMIC_GODEL_CLAW/swarm/`
- **PSMV Swarm Code**: `~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/`
- **Clawdbot Config**: `~/.clawdbot/clawdbot.json`
- **Skills**: `~/.claude/skills/`

---

**Ready to use. All systems operational.**

Test command: `~/DHARMIC_GODEL_CLAW/TEST_INTEGRATION.sh`
