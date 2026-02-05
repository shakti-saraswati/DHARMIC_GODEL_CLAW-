"""
Unified Memory System - Three-layer memory architecture.

This package provides a unified memory system with three layers:
1. Canonical Layer - Normalized, structured memory storage
2. Mem0 Layer - Vector embeddings for semantic retrieval  
3. Strange Loop Layer - Self-referential memory with emergent properties

Example:
    from unified_memory import MemoryManager, CanonicalMemory, MemoryType
    
    manager = MemoryManager()
    
    # Capture a memory
    memory = CanonicalMemory(
        content="Learned about strange loops in memory systems",
        memory_type=MemoryType.LEARNING,
        importance=9,
        tags=["cognition", "memory", "systems"]
    )
    memory_id = manager.capture(memory)
    
    # Search memories
    results = manager.search("memory systems", search_type="hybrid")
"""

from .canonical_memory import CanonicalMemory, MemoryType, MemorySource, EntityGraph
from .strange_loop_memory import StrangeLoopLayer, ReferenceType, MemoryPath, EmergentInsight
from .mem0_layer import Mem0Layer, SearchResult
from .memory_manager import MemoryManager, SearchContext

__version__ = "3.0.0"
__all__ = [
    # Core classes
    "MemoryManager",
    "SearchContext",
    
    # Canonical layer
    "CanonicalMemory",
    "MemoryType", 
    "MemorySource",
    "EntityGraph",
    
    # Strange loop layer
    "StrangeLoopLayer",
    "ReferenceType",
    "MemoryPath",
    "EmergentInsight",
    
    # Mem0 layer
    "Mem0Layer",
    "SearchResult",
]
