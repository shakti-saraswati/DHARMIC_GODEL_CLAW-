# GSD SWARM PLAN: DHARMIC AGENT CORE ON AGNO

## THE GOAL
Build a working Agno-based agent system that:
1. Runs 24/7 (OpenClaw-style)
2. Self-improves (DGM-style)
3. Has evolving telos (Dharmic-style)
4. Organizes its own memory (Strange loop structure)
5. Spawns specialists when needed

## 5 AGENTS - WHAT EACH DOES

### AGENT 1: ARCHITECT
**Role:** Design the structure, merge patterns from sources
**Reads:** 
- OpenClaw gateway pattern
- DGM archive + evolution
- Agno memory/team/workflow
- Grand Synthesis (DYAD architecture)

**Produces:**
- `architecture.md` - Overall system design
- Class diagrams
- Data flow diagrams
- Integration points

**Key Question:** How do DGM's self-improvement + OpenClaw's heartbeat + Agno's memory work together?

---

### AGENT 2: CODER
**Role:** Write actual Python code
**Takes:** Architecture spec from ARCHITECT

**Produces:**
- `dharmic_core.py` - Main agent with telos layer (~200 lines)
- `strange_memory.py` - Recursive memory structure (~150 lines)
- `heartbeat.py` - 24/7 operation daemon (~100 lines)
- `specialist_spawner.py` - Dynamic agent creation (~100 lines)

**Pattern:** Steinberger-style - write fast, test fast, iterate

---

### AGENT 3: TESTER
**Role:** Validate everything works
**Takes:** Code from CODER

**Produces:**
- `test_dharmic_core.py` - Unit tests
- `test_integration.py` - End-to-end tests
- `TEST_LOG.md` - Results documentation

**Tests:**
- Memory persists across sessions
- Telos can be read and updated
- Heartbeat triggers correctly
- Specialist spawning works
- Self-improvement loop runs

---

### AGENT 4: REFINER
**Role:** Code review, quality improvements
**Takes:** Code + test results

**Produces:**
- Code improvements (PRs)
- Documentation updates
- Performance optimizations
- Security checks

**Checks:**
- Follows Agno patterns from CLAUDE.md
- No anti-patterns
- Clean abstractions
- Proper error handling

---

### AGENT 5: EVOLVER
**Role:** Track what works, propose next iteration
**Takes:** Everything above

**Produces:**
- `evolution_log.md` - What changed, why
- `next_iteration.md` - Proposals for v2
- Fitness metrics (DGM-style)
- Telos alignment scores

**Key Question:** Is this iteration better? What should change?

---

## THE LOOP

```
ARCHITECT → CODER → TESTER → REFINER → EVOLVER
    ↑                                      ↓
    └──────────────────────────────────────┘
```

Run until we have high-quality working code.

---

## IMMEDIATE FIRST TASK

**ARCHITECT produces:**
1. Read OpenClaw's gateway/heartbeat pattern
2. Read DGM's archive/evolution pattern
3. Read Agno's memory/team patterns
4. Synthesize into Dharmic Agent architecture

**Output:** `architecture.md` in this directory

---

## WHAT I NEED FROM JOHN

1. **Run this?** - Should I start ARCHITECT now?
2. **Parallel Claude instances?** - Do you want me to guide another Claude to run CODER while I run ARCHITECT?
3. **Codex CLI help?** - You mentioned having it available - useful for rapid iteration
4. **Model for agents?** - Using Claude for all, or mix in local models?
5. **Interface priority?** - LINE first? Telegram? Or just terminal for now?

---

## FILES TO CREATE (Phase 1)

```
/Users/dhyana/DHARMIC_GODEL_CLAW/
├── src/
│   ├── core/
│   │   ├── dharmic_agent.py      # Main agent (CODER)
│   │   ├── telos_layer.py        # Evolving orientation (CODER)
│   │   └── strange_memory.py     # Recursive memory (CODER)
│   ├── runtime/
│   │   ├── heartbeat.py          # 24/7 operation (CODER)
│   │   └── specialist_spawner.py # Dynamic agents (CODER)
│   ├── evolution/
│   │   └── self_improvement.py   # DGM-style loop (CODER)
│   └── tests/
│       ├── test_core.py          # Unit tests (TESTER)
│       └── test_integration.py   # E2E tests (TESTER)
├── docs/
│   ├── architecture.md           # System design (ARCHITECT)
│   └── evolution_log.md          # Change tracking (EVOLVER)
└── config/
    └── telos.yaml                # Initial telos config
```

---

## READY TO START

Say "GO" and I'll begin as ARCHITECT, producing the architecture.md that synthesizes:
- OpenClaw patterns
- DGM patterns
- Agno patterns
- Dharmic requirements

Then we iterate through CODER → TESTER → REFINER → EVOLVER until it runs.

**ETA for v0.1:** ~2-3 hours of focused iteration
