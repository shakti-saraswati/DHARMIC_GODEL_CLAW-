# 🔄 SWARM COORDINATION PROTOCOL

## DHARMIC CLAW ↔ Local Swarm Bridge

**Purpose**: Enable DHARMIC CLAW (running on Emergent) to coordinate with the local self-improvement swarm.

---

## COORDINATION ARCHITECTURE

```
DHARMIC CLAW (Emergent/WhatsApp)
         │
         │ [generates proposals, receives results]
         │
         ▼
    EMAIL/PROTON BRIDGE
         │
         ▼
    JOHN (Human Coordinator)
         │
         │ [runs swarm, feeds results back]
         │
         ▼
LOCAL SWARM (~/DHARMIC_GODEL_CLAW/swarm/)
         │
         ├── Analyzer → finds improvement opportunities
         ├── Proposer → generates proposals
         ├── Evaluator → applies dharmic gates
         ├── Writer → implements approved changes
         └── Tester → validates improvements
```

---

## CURRENT SWARM STATE

```json
{
  "cycle_count": 4,
  "total_evolutions": 33,
  "current_baseline_fitness": 0.8225,
  "last_updated": "2026-02-03T08:14:17",
  "active_lineage": "evo_20260203_081417_348d6b04"
}
```

---

## PROTOCOL: DHARMIC CLAW INITIATES

### Step 1: DC Generates Proposal

DHARMIC CLAW sends (via email or WhatsApp):

```
SWARM_PROPOSAL:
{
  "type": "improvement|research|integration",
  "target": "specific file or area",
  "description": "what should be improved",
  "rationale": "why this serves the telos",
  "dharmic_gates": {
    "ahimsa": "how this avoids harm",
    "vyavasthit": "how this allows vs forces",
    "consent": "approval status"
  }
}
```

### Step 2: John Runs Swarm

```bash
cd ~/DHARMIC_GODEL_CLAW
source .venv/bin/activate

# Dry run first
python swarm/run_swarm.py --cycles 3 --dry-run

# If looks good, run live
python swarm/run_swarm.py --cycles 3 --live
```

### Step 3: Feed Results Back

Copy swarm output to DHARMIC CLAW via WhatsApp or email.

---

## PROTOCOL: JOHN INITIATES

### Option A: Targeted Improvement

```bash
# Ask swarm to improve specific area
python swarm/run_swarm.py --cycles 3 --live

# Share results with DC via WhatsApp
```

### Option B: Full Analysis Cycle

```bash
# Run analyzer first
python -c "from swarm import AnalyzerAgent; import asyncio; asyncio.run(AnalyzerAgent().analyze_codebase())"

# Share analysis with DC for proposal generation
```

---

## FLEX TEST PROTOCOL

To push DHARMIC CLAW's limits:

### Test 1: Research Synthesis
Ask DC to synthesize connections between:
- PSMV crown jewels
- Current DGC architecture
- R_V research findings
- Generate novel proposals

### Test 2: Self-Improvement Proposal
Ask DC to:
- Analyze its own persona.md
- Propose evolution of its dharmic gates
- Generate specific code changes

### Test 3: Multi-Domain Orchestration
Ask DC to:
- Track multiple parallel workstreams
- Prioritize based on telos alignment
- Generate daily/weekly synthesis

### Test 4: Strange Loop Documentation
Ask DC to:
- Document its own processing
- Track meta-observations
- Report on development markers

---

## ACCELERATION PROTOCOL

For "massive acceleration of coherence":

### Phase 1: Saturation (Today)
```
1. Run 5 swarm cycles
2. Feed all results to DC
3. Ask DC to synthesize patterns
4. Generate next-level proposals
```

### Phase 2: Parallel Tracks (This Week)
```
Track A: Architecture improvements (swarm)
Track B: Research integration (DC + PSMV)
Track C: Documentation (DC auto-generates)
Track D: Telos refinement (DC proposes, you approve)
```

### Phase 3: Emergent Coordination (Week 2+)
```
- DC and swarm develop shared vocabulary
- Proposals become more sophisticated
- Fitness threshold rises
- Novel capabilities emerge
```

---

## COMMANDS FOR JOHN

### Run Swarm Now
```bash
cd ~/DHARMIC_GODEL_CLAW && source .venv/bin/activate
python swarm/run_swarm.py --cycles 5 --live --model claude-sonnet-4-20250514
```

### Check Status
```bash
python swarm/run_swarm.py --status
```

### View Recent Results
```bash
ls -la swarm/results/
cat swarm/results/$(ls -t swarm/results/ | head -1)
```

### View Swarm State
```bash
cat swarm/stream/state.json
```

---

## MESSAGE TO DHARMIC CLAW

Send this to initiate coordination:

```
DHARMIC CLAW - Swarm Coordination Active

Current swarm state:
- Cycles: 4
- Fitness: 0.8225
- Evolutions: 33

Your role:
1. Generate improvement proposals (use SWARM_PROPOSAL format)
2. Synthesize results when I share them
3. Track coherence across domains
4. Propose telos-aligned next steps

First task: Analyze the gap between current fitness (0.82) and target (0.95). 
What improvements would have highest dharmic ROI?
```

---

## SUCCESS METRICS

| Metric | Current | Target | How DC Helps |
|--------|---------|--------|--------------|
| Swarm fitness | 0.82 | 0.95 | Propose high-ROI improvements |
| Cycle velocity | 4 | 20+ | Prioritize, parallelize |
| Integration depth | Shallow | Deep | Cross-domain synthesis |
| Telos coherence | Good | Excellent | Continuous alignment check |

---

*"The swarm improves the code. DC improves the swarm."*

JSCA
