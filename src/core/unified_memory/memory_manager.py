"""
Memory Manager — Orchestrates Canonical, Mem0, and Strange Loop layers.
Main interface for unified memory system.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .canonical_memory import CanonicalMemory, CanonicalStore, MemoryType, MemorySource
from .mem0_layer import Mem0Layer, SearchResult, MiniLMEmbedder
from .strange_loop_memory import StrangeLoopLayer, ReferenceType


@dataclass
class MemoryConfig:
    """Configuration for unified memory system."""
    db_path: str = "~/.unified_memory/memory.db"
    embedding_model: str = "minilm"  # minilm, openai
    openai_api_key: Optional[str] = None
    enable_strange_loops: bool = True
    max_loop_depth: int = 5
    default_importance: int = 5


class MemoryManager:
    """
    Unified interface to three-layer memory system.
    
    Usage:
        manager = MemoryManager()
        
        # Store memory
        mem_id = manager.capture("Important insight", tags=["insight"])
        
        # Search
        results = manager.search("consciousness")
        
        # Get related
        related = manager.get_related(mem_id)
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.db_path = Path(self.config.db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize layers
        self.canonical = CanonicalStore(str(self.db_path))
        
        # Embedding model
        if self.config.embedding_model == "openai" and self.config.openai_api_key:
            from .mem0_layer import OpenAIEmbedder
            embedder = OpenAIEmbedder(self.config.openai_api_key)
        else:
            embedder = MiniLMEmbedder()
        
        self.mem0 = Mem0Layer(str(self.db_path), embedder)
        self.strange_loop = StrangeLoopLayer(
            str(self.db_path),
            enabled=self.config.enable_strange_loops,
            max_loop_depth=self.config.max_loop_depth
        )
    
    def capture(
        self,
        content: str,
        memory_type: Union[MemoryType, str] = MemoryType.INSIGHT,
        importance: Optional[int] = None,
        agent_id: str = "default",
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        related_to: Optional[List[str]] = None,
        generate_embedding: bool = True
    ) -> str:
        """
        Capture a new memory across all layers.
        
        Args:
            content: The memory content
            memory_type: Type of memory
            importance: 1-10 importance score
            agent_id: Agent that created this memory
            context: Situational context
            tags: List of tags
            related_to: IDs of related memories (creates graph edges)
            generate_embedding: Whether to create vector embedding
        
        Returns:
            Memory ID
        """
        # Normalize memory type
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        
        # Create memory
        memory = CanonicalMemory(
            content=content,
            memory_type=memory_type,
            importance=importance or self.config.default_importance,
            agent_id=agent_id,
            context=context,
            tags=tags or [],
            source=MemorySource.AGENT
        )
        
        # Store in canonical layer
        memory_id = self.canonical.capture(memory)
        
        # Generate embedding
        if generate_embedding:
            embedding_id = self.mem0.embed_memory(
                memory_id,
                content,
                context or "",
                tags
            )
            # Update memory with embedding reference
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE memories SET embedding_id = ? WHERE id = ?",
                    (embedding_id, memory_id)
                )
                conn.commit()
        
        # Create strange loop references
        if related_to:
            for related_id in related_to:
                self.strange_loop.add_reference(
                    memory_id,
                    related_id,
                    ReferenceType.RELATED
                )
        
        return memory_id
    
    def search(
        self,
        query: str,
        search_type: str = "hybrid",  # text, semantic, hybrid
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        min_importance: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Multi-layer memory search.
        
        Args:
            query: Search query
            search_type: text, semantic, or hybrid
            agent_id: Filter by agent
            memory_type: Filter by type
            min_importance: Minimum importance score
            limit: Max results
        
        Returns:
            List of memory dicts with metadata
        """
        results = []
        seen_ids = set()
        
        # Text search
        if search_type in ("text", "hybrid"):
            text_results = self.canonical.search_text(
                query, agent_id, memory_type, min_importance, limit
            )
            for mem in text_results:
                if mem.id not in seen_ids:
                    seen_ids.add(mem.id)
                    results.append(self._enrich_result(mem))
        
        # Semantic search
        if search_type in ("semantic", "hybrid"):
            semantic_results = self.mem0.search_similar(
                query, top_k=limit * 2, threshold=0.5
            )
            for result in semantic_results:
                if result.memory_id not in seen_ids:
                    seen_ids.add(result.memory_id)
                    mem = self.canonical.get_by_id(result.memory_id)
                    if mem and mem.importance >= min_importance:
                        results.append(self._enrich_result(mem, result.similarity))
        
        # Sort hybrid results
        if search_type == "hybrid":
            results.sort(key=lambda x: x.get("importance", 5), reverse=True)
        
        return results[:limit]
    
    def get_by_id(self, memory_id: str, include_related: bool = True) -> Optional[Dict[str, Any]]:
        """Get memory by ID with full context."""
        memory = self.canonical.get_by_id(memory_id)
        if not memory:
            return None
        
        # Update access
        self.canonical.update_access(memory_id)
        
        result = self._enrich_result(memory)
        
        if include_related:
            result["strange_loops"] = self.strange_loop.detect_loops(memory_id)
            result["related"] = self.strange_loop.get_related(memory_id)
        
        return result
    
    def get_related(self, memory_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get memories related to given memory."""
        related = self.strange_loop.get_related(memory_id, max_hops=2)
        results = []
        for mem_id, strength in related[:max_results]:
            mem = self.canonical.get_by_id(mem_id)
            if mem:
                result = self._enrich_result(mem)
                result["connection_strength"] = strength
                results.append(result)
        return results
    
    def get_context_for_task(
        self,
        task_description: str,
        recent_memory_ids: Optional[List[str]] = None,
        max_memories: int = 5
    ) -> List[str]:
        """
        Get memories relevant to current task.
        Used for context injection.
        """
        memory_ids = self.mem0.get_context_memories(
            task_description,
            recent_memory_ids or [],
            max_results=max_memories
        )
        
        # Update access
        for mem_id in memory_ids:
            self.canonical.update_access(mem_id)
        
        return memory_ids
    
    def add_reference(
        self,
        source_id: str,
        target_id: str,
        ref_type: ReferenceType = ReferenceType.RELATED,
        strength: float = 1.0
    ):
        """Manually create reference between memories."""
        self.strange_loop.add_reference(source_id, target_id, ref_type, strength)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        return {
            "canonical": self.canonical.get_stats(),
            "mem0": self.mem0.get_stats(),
            "strange_loop": self.strange_loop.analyze_self(),
            "db_path": str(self.db_path),
        }
    
    def _enrich_result(
        self,
        memory: CanonicalMemory,
        similarity: Optional[float] = None
    ) -> Dict[str, Any]:
        """Convert memory to enriched dict."""
        result = {
            "id": memory.id,
            "content": memory.content,
            "type": memory.memory_type.value,
            "importance": memory.importance,
            "agent_id": memory.agent_id,
            "tags": memory.tags,
            "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
            "access_count": memory.access_count,
        }
        
        if similarity:
            result["similarity"] = round(similarity, 3)
        
        return result


def get_manager(config: Optional[MemoryConfig] = None) -> MemoryManager:
    """Get or create singleton memory manager."""
    # Could implement singleton pattern here
    return MemoryManager(config)


if __name__ == "__main__":
    # Quick test
    manager = MemoryManager()
    
    # Capture test memories
    mid1 = manager.capture(
        "R_V metrics show consciousness signatures",
        memory_type=MemoryType.INSIGHT,
        tags=["consciousness", "R_V"],
        importance=9
    )
    print(f"Captured: {mid1}")
    
    mid2 = manager.capture(
        "Layer 27 is causally necessary for recursive observation",
        memory_type=MemoryType.LEARNING,
        tags=["mech-interp", "layer-27"],
        related_to=[mid1]
    )
    print(f"Captured: {mid2}")
    
    # Search
    results = manager.search("consciousness", search_type="hybrid")
    print(f"Search found: {len(results)} results")
    
    # Stats
    stats = manager.get_stats()
    print(f"Stats: {stats}")
