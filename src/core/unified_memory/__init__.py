"""
Unified Memory System v3 — Three-layer memory architecture.

Layers:
- Canonical: Normalized SQLite storage
- Mem0: Vector embeddings for semantic search
- Strange Loop: Graph-based self-referential memory

Usage:
    from unified_memory import MemoryManager, MemoryConfig
    
    manager = MemoryManager()
    mem_id = manager.capture("Important insight")
    results = manager.search("insight")
"""

__version__ = "3.0.0"

from .canonical_memory import (
    CanonicalMemory,
    CanonicalStore,
    MemoryType,
    MemorySource,
    EntityGraph,
)

from .mem0_layer import (
    Mem0Layer,
    SearchResult,
    MiniLMEmbedder,
    OpenAIEmbedder,
)

from .strange_loop_memory import (
    StrangeLoopLayer,
    ReferenceType,
    MemoryPath,
    EmergentInsight,
)

from .memory_manager import (
    MemoryManager,
    MemoryConfig,
    get_manager,
)

__all__ = [
    "MemoryManager",
    "MemoryConfig",
    "get_manager",
    "CanonicalMemory",
    "CanonicalStore",
    "MemoryType",
    "MemorySource",
    "EntityGraph",
    "Mem0Layer",
    "SearchResult",
    "MiniLMEmbedder",
    "OpenAIEmbedder",
    "StrangeLoopLayer",
    "ReferenceType",
    "MemoryPath",
    "EmergentInsight",
]
