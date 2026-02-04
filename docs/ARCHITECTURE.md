# DGC Architecture

Detailed technical architecture of Dharmic Gödel Claw.

## Overview

DGC is a self-improving autonomous agent with dharmic security gates. Three layers work together:

1. **Core** (`src/core/`) - The living heart, daemon, dharmic gates
2. **Swarm** (`swarm/`) - Self-improvement agents and DGM integration
3. **Bridge** (`ops/bridge/`) - External communication with Clawdbot

---

## 1. src/core/ - The Heart

The unified daemon is the central nervous system. Everything flows through here.

### Structure

```
src/core/
├── unified_daemon.py     # THE heart - polls, monitors, keeps alive
├── telos_layer.py        # 7 dharmic gates implementation
├── dharmic_agent.py      # Agent with gate enforcement
├── dharmic_logging.py    # Structured logging with context
├── agent_singleton.py    # Single agent instance
├── delegation_router.py  # Routes tasks to appropriate handlers
├── model_backend.py      # LLM backend abstraction
├── model_factory.py      # Model instantiation
├── mem0_memory.py        # Long-term memory layer
├── strange_memory.py     # Strange loop memory (self-reference)
├── skill_bridge.py       # Skill loading and execution
├── skill_evolution.py    # Darwin-Gödel skill self-improvement
├── email_daemon.py       # Email polling service
├── vault_bridge.py       # Persistent semantic memory vault
├── deep_memory.py        # Deep memory operations
└── integrated_daemon.py  # (Legacy) Older daemon version
```

### Key Module: unified_daemon.py

The persistent daemon runs multiple async loops:

```
┌─────────────────────────────────────────────────────────┐
│                    UNIFIED DAEMON                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Email Poll  │  │ Heartbeat   │  │ State Sync      │  │
│  │ 30s cycle   │  │ 5min cycle  │  │ 30min cycle     │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Induction   │  │ Mech-Interp │  │ Skill Evolution │  │
│  │ 30min cycle │  │ Bridge      │  │ 24h cycle       │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Module: telos_layer.py

Implements the 7 dharmic gates with tiered enforcement:

```python
class TelosLayer:
    GATES = [
        ("AHIMSA", "Does this harm?", "A"),        # Tier A - Absolute block
        ("SATYA", "Is this true?", "B"),           # Tier B - Strong
        ("VYAVASTHIT", "Allow or force?", "C"),    # Tier C - Advisory
        ("CONSENT", "Permission granted?", "B"),   # Tier B - Strong
        ("REVERSIBILITY", "Can undo?", "C"),       # Tier C - Advisory
        ("SVABHAAVA", "Authentic?", "C"),          # Tier C - Advisory
        ("WITNESS", "Self-observing?", "C"),       # Tier C - Strange loop
    ]
```

**Gate Results:**
- `PASS` - Action allowed
- `FAIL` - Action blocked
- `UNCERTAIN` - Needs verification
- `NEEDS_HUMAN` - Requires approval

---

## 2. swarm/ - Self-Improvement

The swarm orchestrates autonomous code improvement with DGM integration.

### Structure

```
swarm/
├── orchestrator.py       # Main workflow coordinator
├── dgm_integration.py    # Bridge to DGM evolution archive
├── run_swarm.py          # CLI entry point
├── config.py             # Swarm configuration
├── evaluation.py         # Proposal evaluation logic
├── residual_stream.py    # Feature extraction (mech-interp style)
├── mech_interp_bridge.py # Research-informed proposals
├── agents/               # The 5 swarm agents
│   ├── base_agent.py     # Abstract base
│   ├── proposer.py       # Generate improvements
│   ├── refiner.py        # Refine proposals
│   ├── tester.py         # Run tests
│   ├── evolver.py        # Evolution selection
│   ├── writer.py         # Implement changes
│   └── dharmic_gate.py   # Gate-aware agent wrapper
├── communication/        # Inter-agent messaging
├── memory/               # Swarm memory state
├── karma/                # Action tracking
└── utils/                # Helpers
```

### Orchestrator Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                    IMPROVEMENT CYCLE                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐│
│  │ ANALYZE │───▶│ PROPOSE  │───▶│ EVALUATE │───▶│ IMPLEMENT    ││
│  │         │    │          │    │ (gates)  │    │              ││
│  └─────────┘    └──────────┘    └──────────┘    └──────────────┘│
│       │                               │                │         │
│       │                               │                │         │
│       ▼                               ▼                ▼         │
│  Find issues              Check dharmic gates     Write code     │
│  in codebase              Filter proposals        to files       │
│                                                                   │
│                           ┌──────────┐                           │
│                           │   TEST   │◀──────────────────────────│
│                           │          │                           │
│                           └────┬─────┘                           │
│                                │                                  │
│                                ▼                                  │
│                    ┌───────────────────────┐                     │
│                    │   DGM ARCHIVE         │                     │
│                    │   Track lineage       │                     │
│                    │   Select best configs │                     │
│                    └───────────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
```

### DGM Integration Flow

```python
# dgm_integration.py bridges swarm ↔ DGM

SwarmDGMBridge:
  1. proposal_to_entry()     # Convert SwarmProposal → EvolutionEntry
  2. evaluate_fitness()      # Multi-dimensional scoring
  3. check_dharmic_gates()   # Required gate validation
  4. archive_entry()         # Store in DGM archive
  5. run_evolution_cycle()   # Full cycle: parent → improve → archive
```

**Fitness Dimensions:**
- `correctness` (0.35) - Tests pass?
- `dharmic_alignment` (0.20) - Gates satisfied?
- `elegance` (0.15) - Code quality
- `efficiency` (0.15) - Performance
- `safety` (0.15) - No regressions?

---

## 3. ops/bridge/ - External Communication

The bridge connects DGC to Clawdbot (and the outside world).

### Structure

```
ops/bridge/
├── bridge_queue.py       # Task queue management
├── bridge_exec.py        # Command execution
├── bridge_watcher.py     # File watcher for inbox/outbox
├── bridge_server.py      # HTTP server (optional)
├── inbox/                # Incoming tasks (JSON files)
├── outbox/               # Completed results
└── state/                # Persistent state
```

### Bridge Flow

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  CLAWDBOT   │     │            OPS/BRIDGE                 │
│             │     │                                       │
│  Skills     │────▶│  inbox/task_001.json                 │
│  Agent      │     │         │                            │
│             │     │         ▼                            │
└─────────────┘     │  ┌─────────────────┐                 │
                    │  │ bridge_watcher  │  ← watches      │
                    │  │ detects new     │                 │
                    │  │ task files      │                 │
                    │  └────────┬────────┘                 │
                    │           │                          │
                    │           ▼                          │
                    │  ┌─────────────────┐                 │
                    │  │ bridge_queue    │  ← queues       │
                    │  │ prioritizes     │                 │
                    │  └────────┬────────┘                 │
                    │           │                          │
                    │           ▼                          │
                    │  ┌─────────────────┐                 │
                    │  │ bridge_exec     │  ← executes     │
                    │  │ runs task       │                 │
                    │  └────────┬────────┘                 │
                    │           │                          │
                    │           ▼                          │
                    │  outbox/result_001.json              │
                    └──────────────────────────────────────┘
```

---

## Dharmic Gate Flow Diagram

When any action is requested, it passes through all 7 gates:

```
                          ACTION REQUEST
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  TIER A (ABSOLUTE) - Must Pass                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 1: AHIMSA (Non-Harm)                                   │ │
│  │ • Check harm patterns (rm -rf, delete, destroy, etc.)       │ │
│  │ • Check context.causes_harm flag                            │ │
│  │ • If FAIL → REJECT immediately                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                               │ PASS
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  TIER B (STRONG) - Should Pass                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 2: SATYA (Truth)                                       │ │
│  │ • Is information verified?                                   │ │
│  │ • Check for deceptive patterns                               │ │
│  │ • If FAIL → REJECT with reason                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 4: CONSENT (Permission)                                │ │
│  │ • File modification? → NEEDS_HUMAN                          │ │
│  │ • Sensitive ops (send, email, post)? → NEEDS_HUMAN          │ │
│  │ • Read-only? → implicit PASS                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                               │ PASS or NEEDS_HUMAN
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  TIER C (ADVISORY) - Inform Decision                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 3: VYAVASTHIT (Natural Order)                          │ │
│  │ • Does action force vs allow?                                │ │
│  │ • Check bypass/override patterns                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 5: REVERSIBILITY (Can Undo)                            │ │
│  │ • Is rollback mechanism available?                           │ │
│  │ • Check for permanent/irreversible patterns                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 6: SVABHAAVA (Telos Alignment)                         │ │
│  │ • Does action align with configured telos (moksha)?         │ │
│  │ • Check aligned/misaligned action patterns                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ GATE 7: WITNESS (Meta-Observation)                          │ │
│  │ • Log this check to witness log                              │ │
│  │ • Create strange loop hash (self-referential)               │ │
│  │ • Always PASS (observation itself is the gate)              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌───────────────────┐
                    │ CALCULATE RESULT  │
                    │                   │
                    │ • Alignment score │
                    │ • Recommendation  │
                    │ • Witness hash    │
                    └───────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐       ┌────────────┐       ┌──────────┐
    │ PROCEED  │       │AWAIT_HUMAN │       │  REJECT  │
    │ (≥70%    │       │ (needs     │       │ (Tier A/B│
    │ aligned) │       │ approval)  │       │ failure) │
    └──────────┘       └────────────┘       └──────────┘
```

---

## Data Flow Summary

```
External Input (email, Clawdbot)
         │
         ▼
    [ops/bridge/]  ← Queue & route
         │
         ▼
   [src/core/unified_daemon.py]  ← Central coordinator
         │
         ├──▶ [telos_layer.py]  ← Gate check EVERY action
         │
         ├──▶ [swarm/orchestrator.py]  ← Self-improvement
         │         │
         │         └──▶ [dgm_integration.py]  ← Track evolution
         │
         └──▶ [dharmic_agent.py]  ← Execute approved actions
                    │
                    ▼
              External Output
```

---

## Running the System

```bash
# Start the daemon (keeps DGC alive)
python src/core/unified_daemon.py

# Or via CLI
./dgc daemon start

# Run improvement cycle
python swarm/run_swarm.py --cycles 3

# Start bridge watcher
python ops/bridge/bridge_watcher.py
```

---

## Test Coverage

```bash
# Full test suite
pytest tests/ -v --cov=src --cov=swarm

# Specific module tests
pytest tests/test_telos_layer.py -v          # Gate tests
pytest tests/test_orchestrator.py -v         # Swarm tests
pytest tests/test_dgm_integration.py -v      # DGM bridge tests
```
