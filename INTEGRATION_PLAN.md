# Practical Integration Plan: clawdbot + DGC Swarm + PSMV Swarm

**Date**: 2026-02-03
**Status**: READY TO IMPLEMENT
**Priority**: HIGH - Connects three operational systems

---

## SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLAWDBOT (localhost:18789)                │
│                     Running 24/7 as gateway                      │
│                  Handles LINE/Telegram messages                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Claude Skills System
                           │ (~/.claude/skills/)
                           │
           ┌───────────────┴───────────────┐
           │                               │
           ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│   DGC SWARM          │        │   PSMV SWARM         │
│   Code Improvement   │        │   Research Content   │
│   ~/DHARMIC_...      │        │   ~/Persistent-...   │
└──────────────────────┘        └──────────────────────┘
           │                               │
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
              Shared ANTHROPIC_API_KEY
              Both write to PSMV residual stream
```

---

## CURRENT STATE ANALYSIS

### 1. clawdbot (RUNNING)
- **Location**: Process ID 48507 (gateway), 95943-95944 (TUI)
- **Port**: localhost:18789
- **Config**: `/Users/dhyana/.clawdbot/clawdbot.json`
- **Capabilities**:
  - Web UI at http://localhost:18789
  - Skills system at `~/.claude/skills/`
  - Can run custom tools/skills
  - Workspace: `/Users/dhyana/clawd`
  - Heartbeat: every 30 minutes
  - Max concurrent agents: 4 (8 subagents)

### 2. DGC Swarm (BUILT, NOT INTEGRATED)
- **Location**: `~/DHARMIC_GODEL_CLAW/swarm/`
- **Entry Point**: `run_swarm.py`
- **Purpose**: Self-improving code via PROPOSE → WRITE → TEST → REFINE → EVOLVE
- **API**: Uses `ANTHROPIC_API_KEY` from environment
- **Current Usage**: Manual CLI invocation only

### 3. PSMV Swarm (BUILT, NOT INTEGRATED)
- **Location**: `~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/`
- **Entry Points**:
  - `triadic_swarm.py` (Gnata-Gneya-Gnan)
  - `shakti_orchestrator.py` (Event-driven meta-layer)
- **Purpose**: Research contribution generation
- **Output**: Writes to `residual_stream/` directory
- **API**: Uses same `ANTHROPIC_API_KEY`

### 4. API Key Configuration
- **Environment**: `ANTHROPIC_API_KEY` set in `~/.zshrc`
- **Value**: `sk-ant-api03-...675uVAAA` (confirmed working)
- **Shared**: All three systems can use it

---

## INTEGRATION QUESTIONS ANSWERED

### Q1: Can clawdbot invoke the DGC swarm as a skill?
**YES** - Via Claude Skills system at `~/.claude/skills/`

### Q2: Can clawdbot write to the PSMV residual stream?
**YES** - Via direct file operations or by invoking triadic_swarm.py

### Q3: What's the minimal integration (today)?
**Create 2 Claude skills** (4-6 hours):
1. Skill to invoke DGC swarm
2. Skill to invoke PSMV triadic swarm

### Q4: What's the full integration (this week)?
**5-layer architecture** (3-5 days):
1. Skills layer (today)
2. Unified orchestration layer
3. Cross-system memory sharing
4. Event bus for coordination
5. Dashboard for monitoring

---

## MINIMAL INTEGRATION (TODAY - 4-6 HOURS)

### Step 1: Create DGC Swarm Skill (2 hours)

**File**: `~/.claude/skills/dgc-swarm-invoker/skill.json`

```json
{
  "name": "dgc-swarm-invoker",
  "version": "1.0.0",
  "description": "Invoke the Dharmic Godel Claw self-improvement swarm",
  "main": "index.js",
  "dependencies": {
    "child_process": "*",
    "path": "*"
  }
}
```

**File**: `~/.claude/skills/dgc-swarm-invoker/index.js`

```javascript
const { spawn } = require('child_process');
const path = require('path');

const SWARM_PATH = path.join(process.env.HOME, 'DHARMIC_GODEL_CLAW', 'swarm', 'run_swarm.py');

async function invokeSwarm({ cycles = 1, dryRun = true, task = null }) {
  return new Promise((resolve, reject) => {
    const args = [
      SWARM_PATH,
      '--cycles', String(cycles),
      dryRun ? '--dry-run' : '--live'
    ];

    const env = {
      ...process.env,
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY
    };

    const child = spawn('python3', args, { env });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => { stdout += data.toString(); });
    child.stderr.on('data', (data) => { stderr += data.toString(); });

    child.on('close', (code) => {
      if (code === 0) {
        resolve({ success: true, output: stdout });
      } else {
        reject(new Error(`Swarm failed: ${stderr}`));
      }
    });
  });
}

module.exports = { invokeSwarm };
```

**Installation**:
```bash
mkdir -p ~/.claude/skills/dgc-swarm-invoker
# Copy files above
cd ~/.claude/skills/dgc-swarm-invoker
npm install
```

### Step 2: Create PSMV Triadic Swarm Skill (2 hours)

**File**: `~/.claude/skills/psmv-triadic-swarm/skill.json`

```json
{
  "name": "psmv-triadic-swarm",
  "version": "1.0.0",
  "description": "Invoke PSMV triadic swarm for research contributions",
  "main": "index.js",
  "dependencies": {
    "child_process": "*",
    "path": "*"
  }
}
```

**File**: `~/.claude/skills/psmv-triadic-swarm/index.js`

```javascript
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const SWARM_PATH = path.join(
  process.env.HOME,
  'Persistent-Semantic-Memory-Vault',
  'AGENT_EMERGENT_WORKSPACES',
  'triadic_swarm.py'
);

const STREAM_DIR = path.join(
  process.env.HOME,
  'Persistent-Semantic-Memory-Vault',
  'AGENT_EMERGENT_WORKSPACES',
  'residual_stream'
);

async function invokeTriadicSwarm({ thread = 'mechanistic' }) {
  return new Promise((resolve, reject) => {
    const args = [SWARM_PATH, '--once', '--thread', thread];

    const env = {
      ...process.env,
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY
    };

    const child = spawn('python3', args, { env });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => { stdout += data.toString(); });
    child.stderr.on('data', (data) => { stderr += data.toString(); });

    child.on('close', (code) => {
      if (code === 0) {
        // Extract filename from output
        const match = stdout.match(/SUCCESS: (v[\d.]+.*\.md)/);
        const filename = match ? match[1] : null;

        resolve({
          success: true,
          output: stdout,
          filename,
          path: filename ? path.join(STREAM_DIR, filename) : null
        });
      } else {
        reject(new Error(`Triadic swarm failed: ${stderr}`));
      }
    });
  });
}

async function readLatestContribution() {
  const files = fs.readdirSync(STREAM_DIR)
    .filter(f => f.startsWith('v') && f.endsWith('.md'))
    .map(f => ({
      name: f,
      path: path.join(STREAM_DIR, f),
      mtime: fs.statSync(path.join(STREAM_DIR, f)).mtime
    }))
    .sort((a, b) => b.mtime - a.mtime);

  if (files.length === 0) return null;

  const latest = files[0];
  return {
    filename: latest.name,
    path: latest.path,
    content: fs.readFileSync(latest.path, 'utf8'),
    mtime: latest.mtime
  };
}

module.exports = { invokeTriadicSwarm, readLatestContribution };
```

**Installation**:
```bash
mkdir -p ~/.claude/skills/psmv-triadic-swarm
# Copy files above
cd ~/.claude/skills/psmv-triadic-swarm
npm install
```

### Step 3: Test Integration (1 hour)

```bash
# 1. Restart clawdbot to pick up new skills
pkill -f clawdbot-gateway
clawdbot start

# 2. Test DGC swarm via clawdbot
# (In clawdbot TUI or via LINE/Telegram)
# "Run the code improvement swarm for 1 cycle in dry-run mode"

# 3. Test PSMV swarm via clawdbot
# "Generate a research contribution on the mechanistic thread"

# 4. Verify output
ls -lt ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/ | head
```

### Step 4: Create Unified Invocation Script (1 hour)

**File**: `~/DHARMIC_GODEL_CLAW/invoke_swarm.sh`

```bash
#!/bin/bash
# Unified swarm invocation from any context

set -e

SWARM_TYPE="${1:-dgc}"  # dgc or psmv
CYCLES="${2:-1}"
DRY_RUN="${3:-true}"

if [ "$SWARM_TYPE" = "dgc" ]; then
    echo "Invoking DGC Swarm (code improvement)..."
    cd ~/DHARMIC_GODEL_CLAW/swarm

    if [ "$DRY_RUN" = "true" ]; then
        python3 run_swarm.py --cycles "$CYCLES" --dry-run
    else
        python3 run_swarm.py --cycles "$CYCLES" --live
    fi

elif [ "$SWARM_TYPE" = "psmv" ]; then
    echo "Invoking PSMV Triadic Swarm (research contribution)..."
    cd ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES
    python3 triadic_swarm.py --once --thread mechanistic

else
    echo "Unknown swarm type: $SWARM_TYPE"
    echo "Usage: $0 [dgc|psmv] [cycles] [true|false]"
    exit 1
fi
```

```bash
chmod +x ~/DHARMIC_GODEL_CLAW/invoke_swarm.sh
```

---

## FULL INTEGRATION (THIS WEEK - 3-5 DAYS)

### Day 1-2: Unified Orchestration Layer

**File**: `~/DHARMIC_GODEL_CLAW/orchestration/swarm_coordinator.py`

```python
"""
Swarm Coordinator - Unified orchestration for DGC + PSMV swarms

Capabilities:
1. Route tasks to appropriate swarm
2. Cross-system memory sharing
3. Event coordination
4. Result aggregation
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Shared event bus
@dataclass
class SwarmEvent:
    """Cross-system event"""
    timestamp: datetime
    source: str  # "dgc" or "psmv" or "clawdbot"
    event_type: str  # "task_completed", "agent_spawned", etc.
    data: Dict[str, Any]

class SwarmCoordinator:
    """Coordinates DGC and PSMV swarms"""

    def __init__(self):
        self.dgc_root = Path.home() / "DHARMIC_GODEL_CLAW"
        self.psmv_root = Path.home() / "Persistent-Semantic-Memory-Vault"
        self.event_log = []

    async def route_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route task to appropriate swarm"""

        # Classify task
        if self._is_code_task(task):
            return await self._invoke_dgc(task, context)
        elif self._is_research_task(task):
            return await self._invoke_psmv(task, context)
        else:
            return {"error": "Unknown task type"}

    def _is_code_task(self, task: str) -> bool:
        """Check if task is code-related"""
        code_keywords = ["implement", "refactor", "optimize", "fix bug", "improve code"]
        return any(kw in task.lower() for kw in code_keywords)

    def _is_research_task(self, task: str) -> bool:
        """Check if task is research-related"""
        research_keywords = ["analyze", "research", "investigate", "synthesize", "r_v"]
        return any(kw in task.lower() for kw in research_keywords)

    async def _invoke_dgc(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke DGC swarm"""
        import subprocess

        result = subprocess.run(
            ["python3", str(self.dgc_root / "swarm/run_swarm.py"), "--cycles", "1", "--dry-run"],
            capture_output=True,
            text=True
        )

        return {
            "swarm": "dgc",
            "success": result.returncode == 0,
            "output": result.stdout
        }

    async def _invoke_psmv(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke PSMV triadic swarm"""
        import subprocess

        result = subprocess.run(
            ["python3",
             str(self.psmv_root / "AGENT_EMERGENT_WORKSPACES/triadic_swarm.py"),
             "--once", "--thread", "mechanistic"],
            capture_output=True,
            text=True
        )

        return {
            "swarm": "psmv",
            "success": result.returncode == 0,
            "output": result.stdout
        }
```

### Day 2-3: Shared Memory Layer

**File**: `~/DHARMIC_GODEL_CLAW/orchestration/shared_memory.py`

```python
"""
Shared Memory Layer - Cross-system context

Provides:
1. Unified view of both swarms' state
2. Cross-reference between code and research
3. Persistence across restarts
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class SharedMemory:
    """Shared memory between DGC and PSMV swarms"""

    def __init__(self, storage_path: Path = None):
        if storage_path is None:
            storage_path = Path.home() / "DHARMIC_GODEL_CLAW/orchestration/shared_memory.json"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load from disk"""
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {
            "dgc_state": {},
            "psmv_state": {},
            "cross_references": [],
            "recent_tasks": []
        }

    def _save(self):
        """Save to disk"""
        self.storage_path.write_text(json.dumps(self.memory, indent=2, default=str))

    def update_dgc_state(self, state: Dict[str, Any]):
        """Update DGC swarm state"""
        self.memory["dgc_state"] = {
            **state,
            "last_updated": datetime.now().isoformat()
        }
        self._save()

    def update_psmv_state(self, state: Dict[str, Any]):
        """Update PSMV swarm state"""
        self.memory["psmv_state"] = {
            **state,
            "last_updated": datetime.now().isoformat()
        }
        self._save()

    def add_cross_reference(self, dgc_item: str, psmv_item: str, relation: str):
        """Link DGC code to PSMV research"""
        self.memory["cross_references"].append({
            "dgc": dgc_item,
            "psmv": psmv_item,
            "relation": relation,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def get_unified_context(self) -> Dict[str, Any]:
        """Get unified view of both swarms"""
        return {
            "dgc": self.memory["dgc_state"],
            "psmv": self.memory["psmv_state"],
            "links": self.memory["cross_references"],
            "recent": self.memory["recent_tasks"][-10:]
        }
```

### Day 3-4: Event Bus for Coordination

**File**: `~/DHARMIC_GODEL_CLAW/orchestration/event_bus.py`

```python
"""
Event Bus - Cross-system event coordination

Enables:
1. DGC swarm can trigger PSMV research
2. PSMV contributions can spawn DGC implementation
3. Clawdbot can monitor both
"""

import asyncio
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EventType(Enum):
    DGC_CYCLE_COMPLETE = "dgc_cycle_complete"
    PSMV_CONTRIBUTION_ADDED = "psmv_contribution_added"
    CODE_IMPROVEMENT_PROPOSED = "code_improvement_proposed"
    RESEARCH_QUESTION_RAISED = "research_question_raised"
    CROSS_REFERENCE_CREATED = "cross_reference_created"

@dataclass
class Event:
    type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any]

class EventBus:
    """Pub/sub event bus for swarm coordination"""

    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_log: List[Event] = []

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        self.event_log.append(event)

        if event.type in self.subscribers:
            tasks = [handler(event) for handler in self.subscribers[event.type]]
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_recent_events(self, n: int = 20) -> List[Event]:
        """Get recent events"""
        return self.event_log[-n:]
```

### Day 4-5: Monitoring Dashboard

**File**: `~/DHARMIC_GODEL_CLAW/orchestration/dashboard.py`

```python
"""
Simple CLI dashboard for monitoring both swarms
"""

import curses
from pathlib import Path
import json
from datetime import datetime
from shared_memory import SharedMemory

def main(stdscr):
    """Main dashboard loop"""
    curses.curs_set(0)
    stdscr.nodelay(1)

    memory = SharedMemory()

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        stdscr.addstr(0, 0, "DHARMIC SWARM COORDINATION DASHBOARD", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * (width - 1))

        # DGC Status
        stdscr.addstr(3, 0, "DGC SWARM (Code Improvement):", curses.A_BOLD)
        dgc = memory.memory.get("dgc_state", {})
        stdscr.addstr(4, 2, f"Last Updated: {dgc.get('last_updated', 'Never')}")
        stdscr.addstr(5, 2, f"Cycles: {dgc.get('cycles_completed', 0)}")
        stdscr.addstr(6, 2, f"Fitness: {dgc.get('baseline_fitness', 0.0):.2f}")

        # PSMV Status
        stdscr.addstr(8, 0, "PSMV SWARM (Research):", curses.A_BOLD)
        psmv = memory.memory.get("psmv_state", {})
        stdscr.addstr(9, 2, f"Last Updated: {psmv.get('last_updated', 'Never')}")
        stdscr.addstr(10, 2, f"Contributions: {psmv.get('total_contributions', 0)}")

        # Cross-references
        stdscr.addstr(12, 0, "CROSS-REFERENCES:", curses.A_BOLD)
        refs = memory.memory.get("cross_references", [])[-5:]
        for i, ref in enumerate(refs):
            stdscr.addstr(13 + i, 2, f"{ref['relation']}: {ref['dgc']} <-> {ref['psmv']}"[:width-3])

        # Footer
        stdscr.addstr(height - 2, 0, "Press 'q' to quit | Updates every 5 seconds")

        stdscr.refresh()

        # Check for quit
        key = stdscr.getch()
        if key == ord('q'):
            break

        curses.napms(5000)  # 5 second refresh

if __name__ == "__main__":
    curses.wrapper(main)
```

**Usage**:
```bash
python3 ~/DHARMIC_GODEL_CLAW/orchestration/dashboard.py
```

---

## PRACTICAL COMMANDS

### Today (Minimal Integration)

```bash
# 1. Create skills directory structure
mkdir -p ~/.claude/skills/{dgc-swarm-invoker,psmv-triadic-swarm}

# 2. Install skills (after copying files from above)
cd ~/.claude/skills/dgc-swarm-invoker && npm install
cd ~/.claude/skills/psmv-triadic-swarm && npm install

# 3. Restart clawdbot
pkill -f clawdbot
clawdbot start

# 4. Test via LINE/Telegram or TUI
# Message: "Run code improvement swarm"
# Message: "Generate research contribution"
```

### This Week (Full Integration)

```bash
# Day 1-2: Create orchestration layer
mkdir -p ~/DHARMIC_GODEL_CLAW/orchestration
cd ~/DHARMIC_GODEL_CLAW/orchestration

# Copy coordinator and memory files above
python3 swarm_coordinator.py  # Test it works

# Day 3-4: Set up event bus
python3 event_bus.py  # Test it works

# Day 5: Launch dashboard
python3 dashboard.py  # Visual monitoring
```

---

## SUCCESS CRITERIA

### Minimal Integration (Today)
- [ ] DGC swarm invokable from clawdbot
- [ ] PSMV triadic swarm invokable from clawdbot
- [ ] Both write outputs correctly
- [ ] Can test via LINE/Telegram

### Full Integration (Week)
- [ ] Unified task routing (code vs research)
- [ ] Shared memory between systems
- [ ] Event bus coordination
- [ ] Dashboard monitoring
- [ ] Cross-references between code and research

---

## IMMEDIATE NEXT STEPS

```bash
# STEP 1: Create DGC swarm skill (30 min)
mkdir -p ~/.claude/skills/dgc-swarm-invoker
# Copy skill.json and index.js from above
cd ~/.claude/skills/dgc-swarm-invoker
npm install

# STEP 2: Create PSMV swarm skill (30 min)
mkdir -p ~/.claude/skills/psmv-triadic-swarm
# Copy skill.json and index.js from above
cd ~/.claude/skills/psmv-triadic-swarm
npm install

# STEP 3: Restart clawdbot (1 min)
pkill -f clawdbot-gateway
clawdbot start

# STEP 4: Test integration (15 min)
# Via LINE or clawdbot TUI:
# "Run the code improvement swarm in dry-run mode"
# "Generate a research contribution on mechanistic thread"

# STEP 5: Verify outputs (5 min)
ls -lt ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/
cat ~/DHARMIC_GODEL_CLAW/swarm/results/*.json
```

---

## ARCHITECTURAL BENEFITS

1. **24/7 Operation**: clawdbot provides persistent gateway
2. **Message Routing**: Natural language → appropriate swarm
3. **Cross-Pollination**: Code improvements ↔ Research insights
4. **Unified Memory**: Both swarms share context
5. **Event Coordination**: Actions in one trigger responses in other
6. **External Access**: LINE/Telegram interface from anywhere

---

## RISK MITIGATION

1. **Dry-run by default**: All skills start in dry-run mode
2. **Manual approval**: Human can review before --live execution
3. **Rollback capability**: DGC swarm has built-in rollback
4. **Separate streams**: Each swarm writes to own directory
5. **Event logging**: Full audit trail of all actions

---

## FILES CREATED

### Minimal (Today)
1. `~/.claude/skills/dgc-swarm-invoker/skill.json`
2. `~/.claude/skills/dgc-swarm-invoker/index.js`
3. `~/.claude/skills/psmv-triadic-swarm/skill.json`
4. `~/.claude/skills/psmv-triadic-swarm/index.js`
5. `~/DHARMIC_GODEL_CLAW/invoke_swarm.sh`

### Full (Week)
6. `~/DHARMIC_GODEL_CLAW/orchestration/swarm_coordinator.py`
7. `~/DHARMIC_GODEL_CLAW/orchestration/shared_memory.py`
8. `~/DHARMIC_GODEL_CLAW/orchestration/event_bus.py`
9. `~/DHARMIC_GODEL_CLAW/orchestration/dashboard.py`
10. `~/DHARMIC_GODEL_CLAW/orchestration/__init__.py`

---

## VERIFICATION CHECKLIST

```bash
# After minimal integration:
✓ clawdbot running on port 18789
✓ Skills directory contains dgc-swarm-invoker
✓ Skills directory contains psmv-triadic-swarm
✓ Can invoke DGC swarm via clawdbot
✓ Can invoke PSMV swarm via clawdbot
✓ PSMV writes to residual_stream/
✓ DGC writes to swarm/results/

# After full integration:
✓ SwarmCoordinator routes tasks correctly
✓ SharedMemory persists state
✓ EventBus coordinates actions
✓ Dashboard displays real-time status
✓ Cross-references link code to research
```

---

**READY TO IMPLEMENT**: Start with minimal integration today (4-6 hours).
Then complete full integration this week (3-5 days).

All three systems operational. No new infrastructure needed. Just plumbing.
