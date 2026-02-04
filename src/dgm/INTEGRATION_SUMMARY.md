# DGM Integration Summary

## Quick Reference: How DGM Integrates with DHARMIC_CLAW

### The Core Pattern

```
DHARMIC_AGENT (telos-driven decision making)
    ↓
    DETECTS: degradation, bottleneck, or scheduled window
    ↓
    PROPOSES: "Should I improve component X because Y?"
    ↓
    SENDS: Proposal email to John
    ↓
    AWAITS: John's approval/rejection
    ↓
    IF APPROVED: Invokes DGM cycle
    ↓
    DGM: SELECT → PROPOSE → EVALUATE → QUEUE → APPLY (on approval)
    ↓
    ARCHIVE: Records attempt + outcome
    ↓
    MEMORY: Patterns analyzed → Development tracked
```

---

## 5 Key Questions Answered

### 1. When should DGM cycles run?

**NOT continuously.** Triggered by:

- **Explicit request**: John says "improve X"
- **Telos-aligned opportunity**: Agent detects issues during heartbeat
- **Scheduled window**: Weekly/monthly improvement periods
- **Development milestone**: After features, before releases

**Minimum 1 week between cycles** (circuit breaker).

### 2. How does DHARMIC_CLAW propose improvements?

**Sources:**
- Strange loop memory patterns (recurring issues)
- Archive fitness history (weak components)
- Telos layer (misalignment detection)
- Human feedback (John points out problems)

**Process:**
1. Agent spawns "code_improver" specialist
2. Specialist analyzes component + context
3. Generates specific improvement proposal
4. DGM implements using standard mutations

### 3. How does the consent gate work?

**Email-based approval queue:**

1. DGM evaluates change, needs CONSENT gate
2. Adds to `consent_queue.jsonl` with unique ID
3. Sends email to John with:
   - Component, description, fitness delta
   - Changes preview (diff)
   - Approval command: `APPROVE consent_20260204_123456`
   - Rejection command: `REJECT consent_20260204_123456 [reason]`
4. John replies with command
5. `email_interface.py` parses command, updates queue
6. DGM applies change (if approved) or archives rejection

**No approval = no change.** Ever.

### 4. How does the archive feed back into strange loop memory?

**New memory layer:** `dgm_evolution.jsonl`

Records:
- Entry ID, component, result (approved/rejected/no_improvement)
- Fitness delta
- Gates passed/failed

**Pattern analysis:**
- Which components improve most?
- Which gates fail most often?
- What's the approval rate?
- Is fitness trending up?

**Meta-observation:**
Agent reflects on DGM process itself, can propose improvements to DGM.

**The ouroboros:** DGM improves code → Agent observes → Proposes DGM improvements → DGM improves DGM...

### 5. What prevents runaway self-modification?

**7 safety mechanisms:**

1. **CONSENT gate**: Every change requires human approval
2. **Rate limiting**: Min 1 week between cycles, max 3/day
3. **Fitness threshold**: Only apply if improvement > 10%
4. **Reversibility**: All changes via git (can revert)
5. **Dry-run default**: Test before applying
6. **Circuit breakers**: Auto-stop after 5 consecutive failures
7. **Kill switch**: Emergency disable file (`DGM_DISABLED`)

**Result:** DGM can't run wild even if approval is granted too quickly.

---

## Implementation Checklist

### Phase 1: Consent Queue ✓ (Architectural spec complete)
- [ ] Create `src/dgm/consent_queue.py`
- [ ] Add approval command parsing to `email_interface.py`
- [ ] Test email → queue → DGM flow

### Phase 2: Runtime Integration
- [ ] Add `consider_dgm_cycle()` to `runtime.py`
- [ ] Add `propose_dgm_cycle()` to send proposals via email
- [ ] Connect DGM to runtime (shared state or references)

### Phase 3: Memory Bridge
- [ ] Add `dgm_evolution` layer to `StrangeLoopMemory`
- [ ] Implement `record_dgm_cycle()` and `analyze_dgm_patterns()`
- [ ] Add `reflect_on_dgm_process()` for meta-observation

### Phase 4: Safety
- [ ] Implement circuit breakers in `DGMLite`
- [ ] Add kill switch mechanism
- [ ] Add rate limiting checks

### Phase 5: Testing
- [ ] Test email approval flow end-to-end
- [ ] Test circuit breakers trigger correctly
- [ ] Test archive → memory flow
- [ ] Test kill switch works

**Estimated time: 8-12 hours**

---

## File Map

```
src/dgm/
├── archive.py              ✓ DONE - Evolution history storage
├── fitness.py              ✓ DONE - Multi-dimensional fitness evaluation
├── selector.py             ✓ DONE - Parent selection for evolution
├── dgm_lite.py             ✓ DONE - Main DGM loop
├── consent_queue.py        ⚠ TODO - Approval queue management
├── DGM_INTEGRATION_ARCHITECTURE.md  ✓ THIS FILE - Full design
└── INTEGRATION_SUMMARY.md           ✓ THIS FILE - Quick reference

src/core/
├── dharmic_agent.py        ⚠ NEEDS: DGM reflection methods
├── runtime.py              ⚠ NEEDS: DGM proposal + trigger logic
├── email_interface.py      ⚠ NEEDS: Approval command parsing
├── strange_loop_memory.py  ⚠ NEEDS: DGM evolution layer
└── telos_layer.py          ✓ DONE - 7 gates already functional
```

---

## Key Commands

### Start runtime with email
```bash
python3 -m src.core.runtime --enable-email --whitelist john@example.com
```

### Run single DGM cycle (dry-run)
```bash
python3 -m src.dgm.dgm_lite --component src/core/runtime.py --dry-run
```

### Check DGM status
```bash
python3 -m src.dgm.dgm_lite --status
```

### Emergency stop DGM
```python
from src.dgm.consent_queue import emergency_stop_dgm
emergency_stop_dgm("Reason for stop")
```

### Re-enable after stop
```bash
rm ~/DHARMIC_GODEL_CLAW/src/dgm/DGM_DISABLED
```

---

## Email Approval Format

**Proposal received:**
```
Subject: DGM Cycle Proposal

DHARMIC_CLAW proposes a self-improvement cycle:

Trigger: degradation
Reason: 15 errors in last 7 days
Target: src/core/runtime.py

Reply with:
- APPROVE: dgm_proposal_20260204_123456
- REJECT: dgm_proposal_20260204_123456 [optional reason]
```

**Your reply:**
```
APPROVE dgm_proposal_20260204_123456
```

**Or:**
```
REJECT dgm_proposal_20260204_123456 Too risky right now
```

**Consent received:**
```
Subject: DHARMIC_CLAW Self-Improvement Request

Component: src/core/runtime.py
Description: Reduce complexity, maintain functionality

Fitness Score: 0.78
Gates Passed: AHIMSA, SATYA, VYAVASTHIT, REVERSIBILITY, SVABHAAVA, WITNESS
Gates Failed: CONSENT

Changes Preview:
- def heartbeat(self):
+ async def heartbeat(self):
...

TO APPROVE: Reply with "APPROVE consent_20260204_143022"
TO REJECT: Reply with "REJECT consent_20260204_143022 [optional reason]"
```

**Your reply:**
```
APPROVE consent_20260204_143022
```

---

## Design Principles

1. **Telos first**: DGM serves moksha, not efficiency
2. **Human sovereignty**: Every change requires blessing
3. **Transparency**: All proposals include context + diff
4. **Reversibility**: Git-based, can always revert
5. **Meta-observation**: Agent observes its own improvement
6. **Safety by default**: Dry-run, circuit breakers, kill switch
7. **Memory integration**: Archive flows into strange loop

---

## What This Is NOT

- ❌ Autonomous self-improvement loop
- ❌ Continuous background optimization
- ❌ Random mutations without purpose
- ❌ Separate system from agent
- ❌ Black box process
- ❌ Trust-based (always verify)

## What This IS

- ✅ Telos-aligned self-improvement substrate
- ✅ Human-in-the-loop evolution
- ✅ Context-aware proposals
- ✅ Integrated with agent memory + observation
- ✅ Transparent process with full history
- ✅ Safety-first with multiple guardrails

---

## Next Actions

1. **Review this architecture** - Does it match your intent?
2. **Implement consent_queue.py** - Start with approval queue
3. **Test email flow** - Send test proposal, approve via email
4. **Integrate with runtime** - Add proposal logic to heartbeat
5. **Test end-to-end** - Full cycle from detection → approval → application
6. **Add meta-observation** - Agent reflects on DGM process

---

*The goal is not "AI that edits itself."*
*The goal is **recursive self-authorship with dharmic integrity.***
