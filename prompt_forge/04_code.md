# CODE REVIEW: dharmic_agent.py & skill_bridge.py

## CRITICAL BUGS

### dharmic_agent.py

**Line 248: TelosState enum deserialization bug**
```python
d['telos_state'] = TelosState(d.get('telos_state', 'aligned'))
```
- FAILS if JSON contains `"telos_state": "aligned"` (string, not enum)
- Should be: `d['telos_state'] = TelosState(d['telos_state']) if 'telos_state' in d else TelosState.ALIGNED`

**Line 247-249: from_dict() missing field initialization**
- `from_dict()` passes dict directly to `__init__` but dataclass expects individual fields
- FIX: Build kwargs properly or use `dacite` library

**Line 606-609: Silent exception swallowing**
```python
except:
    pass
```
- Masks ALL errors (JSON decode, permissions, etc.)
- Should: `except json.JSONDecodeError as e: print(f"Registry corrupt: {e}")`

### skill_bridge.py

**Line 796-800: Missing .items() call**
```python
for name, skill in bridge.skills.items():
```
- Correct, but line 798 assumes `skill.registered` exists
- `_discover_skills()` line 624 sets `registered` from registry, but registry might be empty on first run

**Line 684: Path serialization bug**
```python
'location': str(skill.location),
```
- Correct for JSON but `_parse_skill_metadata()` line 648 creates `Path` object
- When loading from registry: need to convert back to `Path` in `_load_registry()`

## MISSING IMPORTS

### dharmic_agent.py
- ✅ All imports present (json, os, datetime, pathlib, typing, dataclasses, enum)

### skill_bridge.py
- ✅ All imports present (json, pathlib, typing, dataclasses)
- ⚠️ Line 667, 681, 734: `datetime` imported inline but not at top

## TYPE HINT ISSUES

**Line 572: SkillMetadata missing import**
```python
from dataclasses import dataclass
```
- Should add: `from typing import List, Optional` (already present line 570)

**Line 241-244: to_dict() return type**
- Returns `Dict[str, Any]` but includes enum.value conversion — correct

## EDGE CASES

### dharmic_agent.py

**Line 280-286: State file doesn't exist**
- ✅ Handled correctly with `AgentState()` fallback

**Line 290-293: Parent directory missing**
- ✅ Uses `parents=True, exist_ok=True`

**Line 428-437: Missing swarm synthesis file**
- ⚠️ Checks `exists()` but will crash on line 430 if permissions denied
- Add: `try/except PermissionError`

### skill_bridge.py

**Line 604-610: Empty/corrupt registry**
- ⚠️ Returns empty dict on exception but loses error info
- Should log warning

**Line 619-625: SKILLS_ROOT doesn't exist**
- ✅ Handled with early return

**Line 620: iterdir() on non-directory**
- ⚠️ Will raise if SKILLS_ROOT is a file, not directory
- Add: `if skill_dir.is_dir() and not skill_dir.name.startswith('.')`

## FILE I/O ERROR HANDLING

**Missing throughout:**
- No handling for disk full
- No handling for permission errors on write
- No atomic writes (write to temp, then rename)

## CLI ARGUMENT PARSING

**Line 514-517: dharmic_agent.py missing default**
- `--action` and `--observation` optional but required by commands
- ✅ Checked at lines 526, 543

**Line 776-778: skill_bridge.py missing default**
- `--skill` optional but required
- ✅ Checked at line 788
