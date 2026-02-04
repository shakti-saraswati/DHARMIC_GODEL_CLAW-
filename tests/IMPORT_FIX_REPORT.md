# Test Import Fix Report

**Date:** 2026-02-04
**Status:** Partial fix - fixtures added; API mismatches remain

## Summary

| Test File | Status | Issue Type |
|-----------|--------|------------|
| test_claude_max.py | ✅ 17 PASSED | Working |
| test_dgm.py | ✅ 14 PASSED | Working |
| test_strange_memory.py | ✅ 11 PASSED | Working |
| test_runtime.py | ⚠️ 12/15 PASSED | 3 tests patch non-existent `DEEP_MEMORY_AVAILABLE` |
| test_telos_layer.py | ❌ 0/6 PASSED | API mismatch - tests expect `telos.telos` dict |
| test_dharmic_agent.py | ❌ 0/20 PASSED | API mismatch - wrong parameter names |
| test_memory.py | ❌ 0/19 PASSED | API mismatch - wrong parameter names |
| test_email_daemon.py | ❌ 3/12 PASSED | Mock patches non-existent `DharmicAgent` |
| test_vault_bridge.py | ⚠️ 18/28 PASSED | 10 tests fail on vault structure/path issues |
| test_telos_comprehensive.py | ⚠️ Mixed | Minor assertion mismatches |

**Total: 111 passed, 77 failed, 9 errors**

## Fixed Issues

### 1. Missing Fixtures (FIXED in conftest.py)
Added the following fixtures that tests expected but didn't exist:
- `mock_telos_config` - Creates temp YAML file with sample telos
- `mock_memory_dir` - Alias for `temp_memory_dir`
- `mock_vault_dir` - Creates mock vault directory structure
- `mock_email_config` - Sets up email env vars
- `temp_dir` - Simple tmp_path alias

## Remaining Issues (Need Manual Attention)

### 2. API Mismatches - Wrong Parameter Names

**test_dharmic_agent.py & test_memory.py:**
- Tests use `StrangeLoopMemory(memory_dir=...)` 
- Actual API: `StrangeLoopMemory(base_path=...)`
- Tests use `TelosLayer(telos_path=...)`
- Actual API: `TelosLayer(telos='moksha', telos_config=dict)`

**test_telos_layer.py:**
- Tests expect `telos.telos` to be a dict
- Actual: `telos.telos` is a string (the telos value like 'moksha')

### 3. API Mismatches - Non-existent Methods

**test_dharmic_agent.py tests methods that don't exist:**
- `telos.evolve_proximate()` - NOT IN TelosLayer
- `telos.get_orientation_prompt()` - Should be `get_orientation()`
- `memory.record_observation()` - Should be `remember()`
- `memory.record_meta_observation()` - NOT IN StrangeLoopMemory
- `memory.record_pattern()` - NOT IN StrangeLoopMemory
- `memory._read_recent()` - NOT IN StrangeLoopMemory
- `memory.layers` attribute - NOT IN StrangeLoopMemory

### 4. Mock Patches for Non-existent Attributes

**test_runtime.py (3 tests):**
```python
@patch('runtime.DEEP_MEMORY_AVAILABLE', False)  # Doesn't exist
```

**test_dharmic_agent.py (many tests):**
```python
@patch('dharmic_agent.AGNO_AVAILABLE', False)  # May not exist
@patch('dharmic_agent.DEEP_MEMORY_AVAILABLE', False)  # Doesn't exist
```

**test_email_daemon.py (9 tests):**
```python
with patch('email_daemon.DharmicAgent')  # DharmicAgent not imported there
```

### 5. Vault Bridge Path Issues

**test_vault_bridge.py:**
- Mock vault structure doesn't match expected paths
- `crown_jewels` path resolution differs from test expectations

## Actual Class APIs (for reference)

### TelosLayer (src/core or core/)
```python
TelosLayer.__init__(self, telos: str = 'moksha', telos_config: Optional[Dict] = None)

# Available methods:
- check_action(action: str, context: dict) -> TelosCheck
- get_orientation() -> str
- get_witness_log() -> list
- clear_witness_log()
```

### StrangeLoopMemory (src/core or core/)
```python
StrangeLoopMemory.__init__(self, base_path: str = '~/DHARMIC_GODEL_CLAW/memory')

# Available methods:
- remember(content: str, layer: str = 'sessions') -> MemoryEntry
- mark_development(observation: str, evidence: str = None) -> MemoryEntry
- witness_observation(content: str) -> MemoryEntry
- recall(layer: str = 'all', limit: int = 10, development_only: bool = False) -> list
- get_status() -> dict
- get_context_for_agent(max_chars: int = 2000) -> str
```

## Recommendations

1. **Short term:** Update test files to use correct API signatures
2. **Medium term:** Either:
   - Add the missing methods to StrangeLoopMemory/TelosLayer, OR
   - Rewrite tests to test actual functionality
3. **Consider:** The tests seem written for a planned API that was never implemented. May need to decide which to align to.

## Files Changed

1. `tests/conftest.py` - Added missing fixtures

## Files Needing Manual Attention

1. `tests/test_dharmic_agent.py` - API rewrite needed
2. `tests/test_memory.py` - API rewrite needed  
3. `tests/test_telos_layer.py` - API rewrite needed
4. `tests/test_runtime.py` - Remove `DEEP_MEMORY_AVAILABLE` patches
5. `tests/test_email_daemon.py` - Fix mock patches
6. `tests/test_vault_bridge.py` - Fix vault path expectations
