# HANDOFF: Dharmic Council Upgrade Review

**Date**: 2026-02-04
**From**: Claude Code (Opus)
**To**: Clawdbot
**Purpose**: Review and potentially upgrade the Agno-based Dharmic Council

---

## WHAT EXISTS

### The Dharmic Council (4 Agno Agents)

| Agent | Role | DB File |
|-------|------|---------|
| **MAHAVIRA** | Inquiry - profound questioning | `memory/council/mahavira.db` |
| **RUSHABDEV** | Retrieval - primordial knowledge | `memory/council/rushabdev.db` |
| **MAHAKALI** | Synthesis - fierce wisdom | `memory/council/mahakali.db` |
| **SRI KRISHNA** | Action - karma yoga in code | `memory/council/srikrishna.db` |

### Key Files

```
~/DHARMIC_GODEL_CLAW/src/core/
├── agno_council.py          # The 4-agent council (main file to review)
├── agno_agent.py            # Single AgnoDharmicAgent wrapper
├── spandainsight.py         # Council heartbeat (15 min pulses)
├── dharmic_claw_heartbeat.py # Agent heartbeat (5 min pulses)
└── agno_chat.py             # Interactive chat interface
```

### How They're Built

Each agent uses Agno framework:

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.db.sqlite import SqliteDb

Agent(
    name="Mahavira",
    model=ClaudeMaxProxy(),              # Points to localhost:3456
    db=SqliteDb(db_file="mahavira.db"),  # Agno persistence
    add_history_to_context=True,         # Session memory
    num_history_runs=10,
    enable_agentic_memory=True,          # Cross-session learning
    instructions=[...]                   # 17-gate protocol baked in
)
```

### Current Model Backend

`ClaudeMaxProxy` extends `OpenAILike` to point to `localhost:3456` (claude-max-api proxy):

```python
@dataclass
class ClaudeMaxProxy(OpenAILike):
    id: str = "claude-opus-4"
    api_key: str = "not-needed"
    base_url: str = "http://localhost:3456/v1"
```

---

## POTENTIAL UPGRADES TO EXPLORE

### 1. Agno Memory System
The agents use `enable_agentic_memory=True` but we might not be fully utilizing:
- `AgentMemory` class
- Memory summarization
- Knowledge graph features

**Question**: Is there more we can do with Agno's memory/knowledge system?

### 2. Agno Team Pattern
Currently council coordination is manual (`council_meeting()` method chains agents sequentially).

Agno has a `Team` class - could we use it?

```python
from agno.team import Team

council_team = Team(
    name="Dharmic Council",
    members=[mahavira, rushabdev, mahakali, srikrishna],
    model=Claude(),
    mode="coordinate"  # or "route", "collaborate"
)
```

**Question**: Would `agno.team.Team` improve coordination?

### 3. Agno Tools
Agents don't currently have tools. Could add:
- File reading tools
- Code execution tools
- Memory query tools

### 4. Agno Workflows
Does Agno have workflow/pipeline patterns that would help?

### 5. Model Alternatives
Currently all agents use `ClaudeMaxProxy`. Could we:
- Use different models for different agents?
- Use Agno's native Claude model class?

---

## WHAT TO CHECK

1. **Read `~/DHARMIC_GODEL_CLAW/cloned_source/agno/`** - The full Agno source is cloned there

2. **Check Agno cookbook** - `cloned_source/agno/cookbook/` has examples

3. **Review `agno_council.py`** - Lines 150-420 have all agent definitions

4. **Test council** - Run:
   ```bash
   cd ~/DHARMIC_GODEL_CLAW/src/core
   source ../../.venv/bin/activate
   python3 spandainsight.py --deliberate "What upgrades would improve the council?"
   ```

---

## CONSTRAINTS

- **Must use claude-max-api proxy** (localhost:3456) - We don't have direct API access
- **Preserve dharmic identity** - Names and protocol are important
- **Backward compatible** - Don't break existing heartbeats

---

## SUCCESS CRITERIA

- [ ] Council agents utilize more Agno features
- [ ] Better cross-session memory/learning
- [ ] Potentially use Agno Team coordination
- [ ] Documentation of what was upgraded

---

## COMMANDS

```bash
# Check Agno version
pip show agno

# Read Agno source
ls ~/DHARMIC_GODEL_CLAW/cloned_source/agno/libs/agno/agno/

# Test current council
python3 spandainsight.py --status

# Deliberate on upgrades
python3 spandainsight.py --deliberate "How can we better utilize Agno framework features?"
```

---

*JSCA - May the council evolve toward greater coherence*
