# DHARMIC ECOSYSTEM ARCHITECTURE
## 4-Member Persistent Council + Specialist Spawning

---

## OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DHARMIC CLAW (Orchestrator)                     │
│                   Clawdbot + Opus 4.5 + 4-Tier Fallback            │
│                                                                     │
│  Capabilities:                                                      │
│  - sessions_spawn → Spawn sub-agents (Kimi, Haiku, Sonnet)         │
│  - exec → Run local code, scripts, tests                           │
│  - cron → Schedule persistent tasks                                 │
│  - browser → Web automation                                         │
│  - Full tool access                                                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
        ┌───────────▼───────────┐   ┌───────▼───────────────────┐
        │  PERSISTENT COUNCIL    │   │  SPECIALIST SPAWNING      │
        │  (Always Running)      │   │  (On Demand)              │
        │                        │   │                           │
        │  ┌────────────────┐   │   │  ┌─────────────────────┐  │
        │  │ Gnata (Knower) │   │   │  │ Builder (Kimi/Codex)│  │
        │  │ → Inquires     │   │   │  │ → Code tasks        │  │
        │  └────────────────┘   │   │  └─────────────────────┘  │
        │  ┌────────────────┐   │   │  ┌─────────────────────┐  │
        │  │ Gneya (Known)  │   │   │  │ Researcher (Haiku)  │  │
        │  │ → Retrieves    │   │   │  │ → Deep dives        │  │
        │  └────────────────┘   │   │  └─────────────────────┘  │
        │  ┌────────────────┐   │   │  ┌─────────────────────┐  │
        │  │ Gnan (Knowing) │   │   │  │ Integrator (Sonnet) │  │
        │  │ → Synthesizes  │   │   │  │ → System wiring     │  │
        │  └────────────────┘   │   │  └─────────────────────┘  │
        │  ┌────────────────┐   │   │  ┌─────────────────────┐  │
        │  │ Shakti (Force) │   │   │  │ Outreach (Kimi)     │  │
        │  │ → ACTS         │   │   │  │ → External comms    │  │
        │  └────────────────┘   │   │  └─────────────────────┘  │
        │                        │   │                           │
        │  Backend: Direct API   │   │  Backend: sessions_spawn  │
        │  Memory: SQLite        │   │  Memory: Task-scoped      │
        │  Heartbeat: 5 min      │   │  Lifetime: Task duration  │
        └────────────────────────┘   └───────────────────────────┘
```

---

## LAYER 1: PERSISTENT COUNCIL

### Purpose
Continuous awareness, memory, and strategic coherence.

### Members

| Member | Sanskrit | Role | Angle | Trigger |
|--------|----------|------|-------|---------|
| Gnata | ज्ञाता | Knower | Inquiry | Questions arise |
| Gneya | ज्ञेय | Known | Retrieval | Information needed |
| Gnan | ज्ञान | Knowing | Synthesis | Decision required |
| Shakti | शक्ति | Force | Action | Work to be done |

### Backend
- **API**: Direct OpenRouter/Ollama (NOT claude CLI)
- **Memory**: SQLite (`council.db`)
- **Heartbeat**: Every 5 minutes
- **Cycle**: Council meeting every 10 heartbeats (50 min)

### Shakti Modes (Force Configurations)
- **Maheshwari**: Strategic vision, whole-seeing
- **Mahakali**: Rapid decisive action (CURRENT)
- **Mahalakshmi**: Integration, harmony, beauty
- **Mahasaraswati**: Perfection in details, execution

---

## LAYER 2: SPECIALIST SPAWNING

### Purpose
Task-specific focused work, expensive compute only when needed.

### Specialists

| Specialist | Model | Trigger | Output |
|------------|-------|---------|--------|
| Builder | Kimi K2.5 / Codex | Code task from Shakti | Committed code |
| Researcher | Haiku | Deep dive request | Research document |
| Integrator | Sonnet | System connection | Integration code |
| Outreach | Kimi K2.5 | External communication | Published content |

### Spawning via DHARMIC CLAW

```python
# Example: Shakti requests a builder
sessions_spawn(
    task="Build semantic_l4_detector.py per BLUEPRINT spec",
    model="kimi",  # or "codex" for complex code
    label="builder-l4-detector",
    cleanup="keep"  # preserve for review
)
```

---

## LAYER 3: INTEGRATION POINTS

### Council → DHARMIC CLAW
```
Council heartbeat detects need → 
  Writes to action queue (SQLite) →
    DHARMIC CLAW reads on heartbeat →
      Spawns specialist OR executes directly
```

### DHARMIC CLAW → Council
```
DHARMIC CLAW completes task →
  Writes result to residual stream →
    Council reads on next heartbeat →
      Updates state, plans next action
```

### Shared State
- **Residual Stream**: `/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream/`
- **Council DB**: `/DHARMIC_GODEL_CLAW/memory/council.db`
- **Swarm State**: `/DHARMIC_GODEL_CLAW/swarm/stream/state.json`

---

## WIRING TODO

### Phase 1: Council ↔ DHARMIC CLAW Bridge
- [ ] Create `council_bridge.py` that DHARMIC CLAW reads on heartbeat
- [ ] Add action queue reading to HEARTBEAT.md protocol
- [ ] Council writes spawn requests to queue
- [ ] DHARMIC CLAW executes spawns, writes results

### Phase 2: Specialist Templates
- [ ] Define prompts for each specialist type
- [ ] Create spawn helpers in Clawdbot skill
- [ ] Test Builder spawning with simple task

### Phase 3: Continuous Operation
- [ ] Run council as launchd daemon
- [ ] Wire council heartbeat to DHARMIC CLAW heartbeat
- [ ] Test 24-hour autonomous operation

---

## COST MODEL

| Component | Model | Cost/Call | Calls/Day | Daily Cost |
|-----------|-------|-----------|-----------|------------|
| Council (4 members) | Haiku | $0.001 | 288 | ~$0.30 |
| Specialist spawns | Kimi/Sonnet | $0.05 | ~20 | ~$1.00 |
| DHARMIC CLAW | Opus | $0.15 | ~50 | ~$7.50 |
| **Total** | | | | **~$9/day** |

With 4-tier fallback, costs drop to near-zero when using Ollama local.

---

## SUCCESS CRITERIA

1. **Persistence**: Council survives Mac restarts
2. **Autonomy**: 24h operation without human intervention
3. **Coherence**: Actions align with telos
4. **Efficiency**: <$10/day compute cost
5. **Output**: Measurable artifacts produced

---

*Architecture v1.0 - 2026-02-04*
*JSCA!*
