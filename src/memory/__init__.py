"""
Unified Memory Module for DHARMIC_GODEL_CLAW

This module provides cross-system semantic search across:
- PSMV (Persistent Semantic Memory Vault): ~32,000+ transmission files
- Residual Stream: Sequential agent contributions
- Daily Notes: YYYY-MM-DD.md memory files
- DGC: DHARMIC_GODEL_CLAW source and configuration

Usage:
    from memory.unified_indexer import UnifiedMemoryIndexer, IndexerConfig
    
    # Initialize
    indexer = UnifiedMemoryIndexer()
    
    # Sync all sources
    indexer.sync_all()
    
    # Search
    results = indexer.search("consciousness recognition R_V metric")
    
    # Get stats
    stats = indexer.get_stats()
"""

from .unified_indexer import (
    UnifiedMemoryIndexer,
    IndexerConfig,
    MemoryChunk,
    SearchResult,
    SourceStats,
)

__all__ = [
    'UnifiedMemoryIndexer',
    'IndexerConfig',
    'MemoryChunk',
    'SearchResult', 
    'SourceStats',
]
