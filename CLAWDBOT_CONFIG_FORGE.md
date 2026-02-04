# CLAWDBOT DHARMIC CONFIGURATION
## 10-Agent Forge for Heartbeat, Cron & Watchdog
**Drop this into Claude Code**

**OpenClaw note**: New installs use `openclaw` + `~/.openclaw/openclaw.json`. Legacy `clawdbot` + `~/.clawdbot/clawdbot.json` still works. See `OPENCLAW_COMPAT.md`.

---

## THE GOAL

Configure local Clawdbot with:
1. **HEARTBEAT.md** — What to check every 30 minutes, when to alert, when to stay silent
2. **Cron jobs** — Morning, evening, weekly, and any others needed
3. **Watchdog** — Agent/process that monitors Clawdbot for telos drift

**Output location**: `~/clawd/HEARTBEAT.md` (Clawdbot's workspace)

---

## CONTEXT

- Clawdbot runs locally on Mac
- Workspace: `~/clawd/`
- User: John (Dhyana) — consciousness researcher, Akram Vignan practitioner
- Telos: Moksha through Jagat Kalyan
- Communication: WhatsApp (+818054961566)
- Timezone: Asia/Tokyo (but travels between Bali and Iriomote)
- Wake time: 4:30 AM (non-negotiable)
- Active hours: 5:00 AM - 10:00 PM

**Principle**: Silence is valid. Noise serves no one. Reach John only when something genuinely matters.

---

## RESOURCES TO READ

```
# Clawdbot config
~/.clawdbot/clawdbot.json

# Existing cron jobs
~/.clawdbot/cron/jobs.json

# Swarm's recommendations
~/DHARMIC_GODEL_CLAW/swarm/stream/synthesis_30min.md

# Core agent (for integration)
~/DHARMIC_GODEL_CLAW/core/dharmic_agent.py

# Crown jewels (quality standard)
~/Persistent-Semantic-Memory-Vault/crown_jewels/

# Previous heartbeat attempts
~/DHARMIC_GODEL_CLAW/HEARTBEAT.md
```

---

## 10 AGENTS

### Agent 1: HEARTBEAT ARCHITECT
**Task**: Design the HEARTBEAT.md protocol
- What should Clawdbot check every 30 minutes?
- What conditions warrant alerting John?
- What is HEARTBEAT_OK (silence)?
- How to avoid noise while catching what matters?
**Output**: `~/clawd/forge/01_heartbeat_design.md`

### Agent 2: CRON OPTIMIZER
**Task**: Design optimal cron schedule
- Current: morning-brief (6AM), evening-synthesis (9PM), weekly-review (Sunday 6AM)
- What's missing? What's redundant?
- Consider: 4:30 AM wake, travel between timezones, research cycles
- Propose additions/changes with rationale
**Output**: `~/clawd/forge/02_cron_design.md`

### Agent 3: WATCHDOG DESIGNER
**Task**: Design the agent that watches Clawdbot
- How to detect telos drift?
- How to detect noise vs signal failure?
- How to detect Clawdbot going "surface mode"?
- Should this be a cron job, separate heartbeat, or always-on observer?
**Output**: `~/clawd/forge/03_watchdog_design.md`

### Agent 4: ALERT TAXONOMY
**Task**: Define what deserves alerts vs silence
- HIGH: Requires immediate attention
- MEDIUM: Review within hours
- LOW: Note for next synthesis
- SUPPRESS: Never alert, just log
- Map specific conditions to each level
**Output**: `~/clawd/forge/04_alert_taxonomy.md`

### Agent 5: JOHN'S CONTEXT INTEGRATOR
**Task**: Ensure config honors John's actual life
- 4:30 AM wake (closure training, non-negotiable)
- Travels Bali ↔ Iriomote (timezone handling)
- Deep work on R_V research, papers
- Akram Vignan practice, daily sadhana
- Limited resources (MacBook, iPhone)
- What should Clawdbot know about John's patterns?
**Output**: `~/clawd/forge/05_john_context.md`

### Agent 6: DHARMIC GATE ENFORCER
**Task**: How does Clawdbot pass 7 gates in every action?
- AHIMSA, SATYA, VYAVASTHIT, CONSENT, REVERSIBILITY, SVABHAAV, COHERENCE
- Build gate checks into heartbeat protocol
- Define what fails each gate
**Output**: `~/clawd/forge/06_gates.md`

### Agent 7: FAILURE MODE ANALYST
**Task**: How will this system fail?
- Mac sleeps, Clawdbot stops
- Proxy dies, API errors
- Noise creep (too many alerts)
- Silence creep (missing important things)
- Watchdog becomes what it watches
- Propose mitigations
**Output**: `~/clawd/forge/07_failures.md`

### Agent 8: INTEGRATION MAPPER
**Task**: How does heartbeat connect to existing systems?
- dharmic_agent.py (core agent)
- skill_bridge.py (skills)
- swarm stream (collective intelligence)
- PSMV (memory vault)
- Crown jewel forge
**Output**: `~/clawd/forge/08_integration.md`

### Agent 9: SIMPLICITY GUARDIAN
**Task**: Cut the fat
- What's over-engineered in current designs?
- Minimum viable heartbeat?
- Minimum viable watchdog?
- What can Clawdbot do with ONE simple check?
**Output**: `~/clawd/forge/09_simplicity.md`

### Agent 10: SYNTHESIS & BUILD
**Task**: Combine all findings and BUILD the actual files
**Outputs**:
- `~/clawd/HEARTBEAT.md` — Final protocol (Clawdbot reads this)
- `~/clawd/WATCHDOG.md` — Watchdog protocol
- `~/clawd/forge/10_cron_commands.sh` — Exact commands to configure crons
- `~/clawd/forge/10_synthesis.md` — Summary of decisions

---

## EXECUTION

```bash
mkdir -p ~/clawd/forge

# Phase 1: Agents 1-9 parallel read & design (15 min)
# Phase 2: Agent 10 synthesizes & builds (10 min)
# Phase 3: Validate outputs exist
```

---

## QUALITY STANDARD

The HEARTBEAT.md must be:
- **Readable by Clawdbot** — Clear, actionable, no ambiguity
- **Rooted in telos** — Moksha, not productivity theater
- **Biased toward silence** — Alert only when it matters
- **Self-correcting** — Watchdog catches drift

---

## SUCCESS CRITERIA

When complete:
- [ ] `~/clawd/HEARTBEAT.md` exists and is tight
- [ ] `~/clawd/WATCHDOG.md` defines guardian protocol
- [ ] Cron commands ready to run
- [ ] All 7 dharmic gates built into protocol
- [ ] Failure modes addressed

---

## GO

Execute now. Build the actual files. Report when `~/clawd/HEARTBEAT.md` is ready.

JSCA!
