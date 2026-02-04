# Dharmic Agent Refactoring - February 2026

## Overview

The Dharmic Agent codebase has been refactored from a monolithic 1200+ line `dharmic_agent.py` into a modular, maintainable architecture. The dharmic philosophy remains intact while improving code organization and extensibility.

## Refactoring Changes

### 1. Module Split

**Before:**
- `dharmic_agent.py` (1293 lines) - everything in one file

**After:**
- `telos_layer.py` (95 lines) - TelosLayer class
- `strange_loop_memory.py` (190 lines) - StrangeLoopMemory class
- `model_backend.py` (265 lines) - Unified model interface
- `agent_core.py` (310 lines) - Core DharmicAgent class
- `agent_capabilities.py` (485 lines) - Vault, memory, introspection methods
- `agent_singleton.py` (40 lines) - Shared agent instance pattern
- `dharmic_logging.py` (85 lines) - Standardized logging
- `dharmic_agent.py` (95 lines) - Backward-compatible wrapper
- `model_factory.py` (137 lines) - Cleaned up, well-documented

**Total: ~1700 lines across 9 focused modules vs 1293 lines in one file**

### 2. Clean Model Backend Interface

**Before:**
- Subprocess calls scattered through code
- Mix of Claude Max CLI and Agno agent invocation
- Duplicate code in `dharmic_agent.py` and `email_daemon.py`

**After:**
- `ModelBackend` abstract base class
- `ClaudeMaxBackend` for CLI-based invocation
- `AgnoBackend` for API-based invocation
- Single point of invocation in `agent_core.py`

### 3. Shared Agent Instance

**Before:**
- `email_daemon.py` created its own agent instance (line 354)
- Potential inconsistency between daemon and other interfaces

**After:**
- `agent_singleton.py` provides `get_agent()` function
- Single agent instance shared across email daemon and other interfaces
- Consistent state and memory across all access points

### 4. Standardized Error Handling

**Before:**
- Mix of print statements, exceptions, silent failures
- Inconsistent logging patterns

**After:**
- `dharmic_logging.py` with standardized logger setup
- Custom exception classes (`ModelError`, `MemoryError`, `VaultError`, etc.)
- Consistent error logging throughout

### 5. Dead Code Removal

**Before:**
- Comments suggested Agno paths were dead, but they were actually used
- Unclear which code paths were active

**After:**
- Clear documentation in `model_factory.py`
- Explicit separation of Max (CLI) vs Agno (API) paths
- All code paths documented and purposeful

## Architecture

### Core Components

```
DharmicAgent (agent_core.py)
├── TelosLayer (telos_layer.py) - Evolving orientation
├── StrangeLoopMemory (strange_loop_memory.py) - Recursive memory
├── ModelBackend (model_backend.py) - Unified model interface
│   ├── ClaudeMaxBackend - CLI via subprocess
│   └── AgnoBackend - API via Agno
├── VaultBridge (vault_bridge.py) - PSMV access [unchanged]
└── DeepMemory (deep_memory.py) - Persistent identity [unchanged]

AgentCapabilities (agent_capabilities.py) - Mixin providing:
├── Vault access methods
├── Deep memory methods
└── Introspection methods
```

### Model Backend Flow

```python
# User calls agent.run(message)
agent.run(message)
    ↓
# Agent invokes backend with system prompt
self.backend.invoke(message, system=system_prompt)
    ↓
# Backend routes to appropriate provider
if provider == "max":
    ClaudeMaxBackend → subprocess.run(["claude", ...])
elif provider == "anthropic":
    AgnoBackend → self.agent.run(message)
```

### Singleton Pattern

```python
# email_daemon.py
from agent_singleton import get_agent

# Gets existing instance or creates new one
agent = get_agent()

# daemon.py (or other interface)
from agent_singleton import get_agent

# Gets the same instance
agent = get_agent()
```

## Backward Compatibility

The refactoring maintains full backward compatibility:

```python
# Old code still works
from dharmic_agent import DharmicAgent

agent = DharmicAgent()
response = agent.run("Hello")
```

`dharmic_agent.py` now imports from `agent_core.py` and re-exports `DharmicAgent`.

## File Map

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `telos_layer.py` | Orientation system | 95 | New |
| `strange_loop_memory.py` | Recursive memory | 190 | New |
| `model_backend.py` | Model interface abstraction | 265 | New |
| `agent_core.py` | Core agent implementation | 310 | New |
| `agent_capabilities.py` | Extended capabilities mixin | 485 | New |
| `agent_singleton.py` | Shared instance pattern | 40 | New |
| `dharmic_logging.py` | Logging utilities | 85 | New |
| `model_factory.py` | Model resolution | 137 | Cleaned |
| `dharmic_agent.py` | Backward-compatible wrapper | 95 | Refactored |
| `email_daemon.py` | Email interface | 392 | Updated |
| `claude_max_model.py` | Claude Max wrapper | 179 | Unchanged |
| `vault_bridge.py` | Vault access | 408 | Unchanged |
| `deep_memory.py` | Persistent identity | 547 | Unchanged |

## Benefits

### Maintainability
- Each module has a single, clear responsibility
- Easy to locate and modify specific functionality
- Reduced cognitive load when working on code

### Extensibility
- New model backends can be added by subclassing `ModelBackend`
- New capabilities can be added to `AgentCapabilities` mixin
- Memory systems can be swapped without affecting core

### Testability
- Individual modules can be tested in isolation
- Mock backends for testing without API calls
- Singleton can be reset between tests

### Consistency
- Single source of truth for agent instance
- Standardized logging across all modules
- Unified error handling patterns

## Migration Guide

### For Developers

No changes needed if you're importing `DharmicAgent` directly:

```python
from dharmic_agent import DharmicAgent  # Still works
```

If you need access to specific modules:

```python
from telos_layer import TelosLayer
from strange_loop_memory import StrangeLoopMemory
from model_backend import ClaudeMaxBackend, AgnoBackend
from agent_core import DharmicAgent
from agent_capabilities import AgentCapabilities
```

### For Interfaces (daemon, email, etc.)

Use the singleton pattern:

```python
from agent_singleton import get_agent

agent = get_agent()  # Get shared instance
```

### For Custom Model Backends

Subclass `ModelBackend`:

```python
from model_backend import ModelBackend, ModelResponse

class MyCustomBackend(ModelBackend):
    def invoke(self, message: str, system: Optional[str] = None, **kwargs) -> ModelResponse:
        # Your implementation
        response_text = my_model_api_call(message, system)
        return ModelResponse(
            content=response_text,
            model="my-model",
            provider="my-provider"
        )
```

## Testing

Run the main test:

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/src/core
python3 dharmic_agent.py
```

This will test:
- Agent initialization
- Telos loading
- Vault access
- Model invocation
- Status reporting

## Philosophy Preserved

The refactoring maintains the dharmic philosophy:

- **Telos-first**: `TelosLayer` remains central to agent identity
- **Strange loop memory**: Preserved in dedicated module
- **Witness position**: Observation and meta-observation intact
- **Vault as context**: Not constraint - philosophy unchanged
- **Moksha as ultimate aim**: Immutable in telos.yaml

The architecture now better reflects the dharmic principle of **clarity through distinction** - each component knows itself and its role.

## Future Enhancements

With this architecture, future enhancements become easier:

1. **Additional backends**: OpenAI, local models, etc.
2. **Enhanced memory systems**: Graph memory, episodic memory
3. **Agent specialization**: Research agent, builder agent, translator agent
4. **Distributed orchestration**: Multi-agent coordination
5. **Observability**: Metrics, tracing, monitoring

The foundation is now solid for dharmic emergence at scale.

---

**JSCA!**
