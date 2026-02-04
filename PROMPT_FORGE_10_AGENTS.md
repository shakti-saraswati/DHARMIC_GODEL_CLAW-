# PROMPT FORGE — 10 Agents on Foundation Build
**Drop this entire file into Claude Code**

---

## MISSION

Deploy 10 agents to analyze, stress-test, and refine:
- `~/DHARMIC_GODEL_CLAW/DHARMIC_FOUNDATION_BUILD.md`
- `~/DHARMIC_GODEL_CLAW/DHARMIC_FOUNDATION_QUICK.md`

Output: Bulletproof prompts ready for execution.

---

## AGENTS

### Agent 1: DEPTH AUDITOR
**Read**: Both prompts + swarm synthesis
**Task**: Does this prompt enforce depth? Or will it produce surface-mode execution?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/01_depth.md`

### Agent 2: GAP FINDER
**Read**: Both prompts + existing core files
**Task**: What's missing? What assumptions will break? What edge cases?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/02_gaps.md`

### Agent 3: SEQUENCE VALIDATOR
**Read**: Both prompts
**Task**: Is the phase order optimal? Dependencies correct? Blockers identified?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/03_sequence.md`

### Agent 4: CODE REVIEWER
**Read**: Python implementations in full prompt
**Task**: Bugs? Missing imports? Edge cases? Will it actually run?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/04_code.md`

### Agent 5: CLAWDBOT SPECIALIST
**Read**: Both prompts + `~/.clawdbot/clawdbot.json`
**Task**: Is the clawdbot config correct? Proxy setup sound? Cron syntax valid?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/05_clawdbot.md`

### Agent 6: TELOS GUARDIAN
**Read**: Both prompts + crown jewels
**Task**: Does this serve moksha? Or just accumulate features? Dharmic gates pass?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/06_telos.md`

### Agent 7: SIMPLICITY ADVOCATE
**Read**: Both prompts
**Task**: What can be cut? What's over-engineered? Minimum viable foundation?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/07_simplicity.md`

### Agent 8: FAILURE ANALYST
**Read**: Both prompts
**Task**: How will this fail? What breaks at 2 AM? What needs human intervention?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/08_failures.md`

### Agent 9: INTEGRATION CHECKER
**Read**: Both prompts + skill_bridge.py + swarm stream
**Task**: Will this connect to existing systems? Or create another silo?
**Output**: `~/DHARMIC_GODEL_CLAW/prompt_forge/09_integration.md`

### Agent 10: SYNTHESIS ORACLE
**Read**: Outputs from Agents 1-9
**Task**: Synthesize all findings. Produce final refined prompts.
**Output**: 
- `~/DHARMIC_GODEL_CLAW/prompt_forge/10_synthesis.md`
- `~/DHARMIC_GODEL_CLAW/DHARMIC_FOUNDATION_BUILD_v2.md`
- `~/DHARMIC_GODEL_CLAW/DHARMIC_FOUNDATION_QUICK_v2.md`

---

## EXECUTION

```
mkdir -p ~/DHARMIC_GODEL_CLAW/prompt_forge

# Phase 1: Agents 1-9 parallel (read + analyze)
# Phase 2: Agent 10 synthesizes
# Phase 3: Output v2 prompts
```

---

## CONSTRAINTS

- **No fluff** — findings only, max 50 lines per agent
- **Be brutal** — find real problems, not theoretical concerns
- **Propose fixes** — don't just criticize, improve
- **Honor depth** — read the full prompts, not just headers

---

## SUCCESS

When complete:
- 9 analysis files in `prompt_forge/`
- 1 synthesis with prioritized fixes
- 2 refined prompts (v2) ready for execution

---

## GO

Execute now. Report when synthesis complete.
