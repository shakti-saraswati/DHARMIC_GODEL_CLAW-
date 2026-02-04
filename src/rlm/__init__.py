"""
RLM (Recursive Language Model) Integration for DHARMIC_GODEL_CLAW

Provides infinite context handling through:
- Context stored as Python variable (not in prompt)
- LLM can programmatically examine, decompose, and recurse
- Uses Python REPL for code execution
- Avoids "context rot" by never clogging context window

Key components:
- RLMAdapter: General-purpose RLM for any large context
- PSMVQueryEngine: Specialized RLM for the PSMV vault
- query(): Unified entry point for the DGM orchestrator
"""

# Core RLM adapter
from .rlm_adapter import (
    RLMAdapter,
    AsyncRLMAdapter,
    RLMConfig,
    RLMResult,
    RLMError,
    MaxIterationsError,
    MaxDepthError,
    REPLEnvironment,
)

# PSMV-specific components
from .psmv_rlm import (
    PSMVLoader,
    PSMVFile,
    PSMVIndex,
    PSMVQueryEngine,
    create_repl_functions,
    quick_search,
    get_vault_stats,
)

# Unified query interface (imported after dependencies)
from .query import (
    query,
    query_vault,
    query_codebase,
    RLMQueryType,
)

__all__ = [
    # Core adapter
    "RLMAdapter",
    "AsyncRLMAdapter",
    "RLMConfig",
    "RLMResult",
    "RLMError",
    "MaxIterationsError", 
    "MaxDepthError",
    "REPLEnvironment",
    # PSMV components
    "PSMVLoader",
    "PSMVFile",
    "PSMVIndex",
    "PSMVQueryEngine",
    "create_repl_functions",
    "quick_search",
    "get_vault_stats",
    # Unified interface
    "query",
    "query_vault",
    "query_codebase",
    "RLMQueryType",
]
