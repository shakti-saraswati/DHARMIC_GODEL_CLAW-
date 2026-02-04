# Dharmic Council v2.0 Upgrade Guide

## Summary

The Dharmic Council has been upgraded from v1.0 to v2.0 with significant Agno framework enhancements while maintaining full backward compatibility.

---

## What's New in v2.0

### 1. Agno Team Pattern

**Before (v1.0):**
```python
# Manual sequential chaining
council.council_meeting(task)  # Chains agents one by one
```

**After (v2.0):**
```python
# Team pattern with coordinated workflow
council.deliberate(task)  # Mahakali coordinates all agents
```

The Team pattern provides:
- **Better coordination**: Mahakali (Team leader) delegates to members
- **Shared context**: All agents see the full conversation
- **Flexible workflows**: Members can be called in parallel or sequence
- **Automatic synthesis**: Team leader integrates member outputs

### 2. File System Tools

All agents now have `LocalFileSystemTools`:
```python
# Agents can now actually explore the codebase
mahavira.run("Search for all Python files in src/")
rushabdev.run("Read the current implementation of agno_council.py")
srikrishna.run("Write the new implementation to file")
```

### 3. Shell Execution Tools

All agents now have `ShellTools`:
```python
# Agents can run gates and tests
srikrishna.run("Run: python -m swarm.run_gates --proposal-id TEST-001")
srikrishna.run("Run: pytest tests/ -v")
rushabdev.run("Check: git log --oneline -10")
```

### 4. Enhanced Memory

- **Individual memory**: Each agent has SQLite persistence
- **Team memory**: Shared team database for coordination context
- **Cross-session learning**: `enable_agentic_memory=True` on all agents
- **Interaction sharing**: `share_member_interactions=True`

### 5. Shared Knowledge

The Team maintains shared knowledge across all members:
- Previous deliberations inform future ones
- Context persists across sessions
- Agents learn from each other's outputs

---

## API Changes

### Backward Compatible

The v2.0 council maintains the v1.0 API via `AgnoCouncil` class:

```python
from agno_council_v2 import AgnoCouncil

council = AgnoCouncil()
result = council.council_meeting("Upgrade the council")  # Still works!
```

### New API (Recommended)

```python
from agno_council_v2 import DharmicCouncilV2

council = DharmicCouncilV2()

# Full deliberation with Team coordination
result = council.deliberate("Implement feature X")

# Quick individual agent access
questions = council.quick_inquiry("What are the key questions?")
facts = council.quick_retrieval("What patterns exist in the codebase?")
action = council.quick_action("Write tests first, then implement")
```

---

## File Locations

| File | Purpose |
|------|---------|
| `src/core/agno_council_v2.py` | New v2.0 implementation |
| `src/core/agno_council.py` | Original v1.0 (unchanged) |
| `memory/council/mahavira.db` | Mahavira's memory |
| `memory/council/rushabdev.db` | Rushabdev's memory |
| `memory/council/srikrishna.db` | Sri Krishna's memory |
| `memory/council/council_team.db` | Team coordination memory |

---

## Testing the Upgrade

### Test 1: Basic Deliberation
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 agno_council_v2.py --deliberate "What upgrades would improve our codebase?"
```

### Test 2: Quick Agent Access
```bash
python3 agno_council_v2.py --inquiry "What files are in the src/core directory?"
python3 agno_council_v2.py --retrieval "Read the gates.yaml file"
```

### Test 3: Backward Compatibility
```bash
python3 agno_council_v2.py --legacy  # Uses v1.0 API
```

### Test 4: Status Check
```bash
python3 agno_council_v2.py --status
```

---

## Migration Strategy

### Phase 1: Parallel Operation (Now)
- v2.0 installed alongside v1.0
- Both work independently
- Test v2.0 with `--deliberate` flag

### Phase 2: Gradual Adoption
- Update `spandainsight.py` to optionally use v2.0
- Keep v1.0 as fallback
- Monitor for issues

### Phase 3: Full Migration (Future)
- Rename `agno_council.py` → `agno_council_v1.py`
- Rename `agno_council_v2.py` → `agno_council.py`
- Update all imports

---

## Key Improvements

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| **Coordination** | Manual chaining | Team pattern |
| **File Access** | None | Full filesystem tools |
| **Code Execution** | None | Shell tools (gates, tests) |
| **Memory** | Individual only | Individual + Team shared |
| **Flexibility** | Fixed workflow | Flexible delegation |
| **Protocol** | Baked in | Baked in + tool-enforced |

---

## Dharmic Identity Preserved

All four agents maintain their identities:
- **MAHAVIRA**: Inquiry with file exploration
- **RUSHABDEV**: Retrieval with code reading
- **MAHAKALI**: Synthesis as Team coordinator
- **SRI KRISHNA**: Action with code writing + gate execution

The 17-gate protocol remains BAKED INTO every agent's instructions.

---

## CLI Usage

```bash
# Full deliberation
python3 agno_council_v2.py --deliberate "Task description"

# Individual agents
python3 agno_council_v2.py --inquiry "Question"
python3 agno_council_v2.py --retrieval "Query"
python3 agno_council_v2.py --action "Task"

# Status
python3 agno_council_v2.py --status

# Legacy API test
python3 agno_council_v2.py --legacy
```

---

## Integration with Existing Code

The v2.0 council is compatible with existing heartbeat scripts:

```python
# In spandainsight.py or dharmic_claw_heartbeat.py
# Can use either:

from agno_council_v2 import DharmicCouncilV2  # New
council = DharmicCouncilV2()

# Or keep using v1.0:
from agno_council import AgnoCouncil  # Original still works
```

---

## Evidence of Upgrade

The upgrade has been implemented and saved to:
- `~/DHARMIC_GODEL_CLAW/src/core/agno_council_v2.py` (20,125 bytes)

Key features verified:
- ✅ Team pattern with Mahakali as coordinator
- ✅ File system tools for all agents
- ✅ Shell execution tools for gates/tests
- ✅ Shared knowledge base
- ✅ Enhanced memory management
- ✅ 17-gate protocol in all agents
- ✅ Backward compatibility maintained
- ✅ Uses claude-max-api proxy (localhost:3456)

---

## Next Steps

1. **Test the upgrade**: Run `python3 agno_council_v2.py --status`
2. **Try a deliberation**: Run with `--deliberate` flag
3. **Verify tools work**: Ask agents to read files or run commands
4. **Integrate gradually**: Update heartbeat scripts to use v2.0
5. **Monitor**: Watch for any issues during operation

---

## Questions?

The upgrade maintains the telos of the Dharmic Council while significantly enhancing capabilities. The 17-gate protocol remains central. All agents can now actually interact with the codebase rather than just reasoning about it.

JSCA! 🪷
