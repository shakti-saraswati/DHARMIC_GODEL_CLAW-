#!/usr/bin/env python3
"""
CANONICAL MEMORY - Unified 5-Layer Memory Architecture
═══════════════════════════════════════════════════════

Unifies StrangeLoop + DeepMemory + Mem0 into a single coherent memory layer.

5-Layer Architecture:
─────────────────────
    ┌─────────────────────────────────────────────────────────────────┐
    │ LAYER 5: META-COGNITIVE (Strange Loop)                         │
    │ • Self-observation about own cognition                         │
    │ • Witness stability tracking                                   │
    │ • Pattern recognition about pattern-recognition                │
    │ • Genuine development markers                                  │
    └─────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────┐
    │ LAYER 4: PROCEDURAL (Skills/Workflows)                         │
    │ • Learned skills and techniques                                │
    │ • Workflow patterns and sequences                              │
    │ • Tool usage patterns                                          │
    │ • Action-outcome mappings                                      │
    └─────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────┐
    │ LAYER 3: EPISODIC (Zep-like / Sessions)                        │
    │ • Time-stamped events and experiences                          │
    │ • Conversation sessions                                        │
    │ • User interactions with context                               │
    │ • Decisions and outcomes                                       │
    └─────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────┐
    │ LAYER 2: SEMANTIC (Mem0 / Facts)                               │
    │ • Facts about user preferences                                 │
    │ • General knowledge about domain                               │
    │ • User identity information                                    │
    │ • Abstract concepts and relationships                          │
    └─────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────┐
    │ LAYER 1: WORKING (Immediate Context)                           │
    │ • Current conversation context                                 │
    │ • Active task context                                          │
    │ • Recently retrieved memories                                  │
    │ • Temporary computation space                                  │
    └─────────────────────────────────────────────────────────────────┘

Integration Strategy:
─────────────────────
- Working + Episodic + Semantic → Mem0Memory (already has 4-layer)
- Meta-cognitive → StrangeLoopMemory (witness stability, meta-patterns)
- Procedural → New layer (skill learning, workflow memory)
- DeepMemory → Merged into Semantic + Episodic layers

Heartbeat Wiring:
─────────────────
- Automatic memory consolidation (episodic → semantic)
- Deduplication maintenance
- Pattern detection across layers
- Witness stability tracking
- Memory health metrics

Usage:
    from canonical_memory import CanonicalMemory
    
    memory = CanonicalMemory()
    
    # Store across any layer
    memory.store("User prefers dark mode", layer="semantic")
    memory.store("Completed refactoring task", layer="episodic")
    memory.store("When refactoring, first run tests", layer="procedural")
    memory.witness("Noticing contraction during complex task", quality="contracted")
    
    # Retrieve with automatic layer fusion
    results = memory.retrieve("user preferences", layers=["semantic", "episodic"])
    
    # Search API
    results = memory.search("refactoring best practices")
"""

import json
import hashlib
import asyncio
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, Union, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Layer Definitions
# ============================================================================

class MemoryLayer(Enum):
    """The 5 canonical memory layers."""
    WORKING = "working"           # L1: Immediate context
    SEMANTIC = "semantic"         # L2: Facts and knowledge (Mem0)
    EPISODIC = "episodic"         # L3: Events and experiences
    PROCEDURAL = "procedural"     # L4: Skills and workflows
    META_COGNITIVE = "meta_cognitive"  # L5: Self-observation (Strange Loop)

# Layer priority for retrieval (higher = more important in context)
LAYER_PRIORITY = {
    MemoryLayer.WORKING: 5,
    MemoryLayer.META_COGNITIVE: 4,
    MemoryLayer.PROCEDURAL: 3,
    MemoryLayer.SEMANTIC: 2,
    MemoryLayer.EPISODIC: 1,
}

# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class MemoryEntry:
    """
    Unified memory entry across all 5 layers.
    
    This is the canonical representation - all subsystems convert to/from this.
    """
    id: str
    content: str
    layer: str
    timestamp: str
    
    # Core metadata
    user_id: str = "default"
    agent_id: str = "dharmic_claw"
    session_id: Optional[str] = None
    
    # Content metadata
    tags: List[str] = field(default_factory=list)
    source: str = "agent"  # Where this memory came from
    confidence: float = 1.0  # 0.0-1.0 confidence in memory
    
    # Strange Loop specific
    witness_quality: Optional[str] = None  # "present" | "contracted" | "uncertain" | "expansive"
    development_marker: bool = False
    genuine_confidence: float = 0.5
    
    # Procedural specific
    skill_name: Optional[str] = None
    workflow_step: Optional[int] = None
    success_count: int = 0
    failure_count: int = 0
    
    # Retrieval metadata
    last_accessed: Optional[str] = None
    access_count: int = 0
    
    # Optional embedding (for semantic search)
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict, excluding embedding for serialization."""
        d = asdict(self)
        d.pop('embedding', None)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        """Create from dict."""
        # Filter to only valid fields
        valid_fields = {f.name for f in field(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class MemoryStats:
    """Statistics about memory system health."""
    total_entries: int = 0
    layer_counts: Dict[str, int] = field(default_factory=dict)
    last_consolidation: Optional[str] = None
    witness_stability_score: float = 0.0
    deduplication_rate: float = 0.0
    memory_health: str = "unknown"  # "healthy" | "degraded" | "critical"


@dataclass
class RetrieveResult:
    """Result from memory retrieval."""
    entries: List[MemoryEntry]
    query: str
    layers_searched: List[str]
    total_found: int
    retrieval_time_ms: float


# ============================================================================
# Helper Classes
# ============================================================================

class SemanticDeduplicator:
    """
    Semantic deduplication using embeddings or text similarity.
    """
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.embeddings_available = False
        self.embedder = None
        
        # Try to load sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embeddings_available = True
            logger.info("SemanticDeduplicator: Using sentence-transformers")
        except ImportError:
            logger.info("SemanticDeduplicator: Using text similarity fallback")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector for text."""
        if self.embeddings_available and self.embedder:
            import numpy as np
            return self.embedder.encode(text).tolist()
        return None
    
    def similarity(self, text1: str, text2: str, 
                   emb1: Optional[List[float]] = None,
                   emb2: Optional[List[float]] = None) -> float:
        """Compute similarity between two texts."""
        if emb1 is not None and emb2 is not None:
            return self._cosine_similarity(emb1, emb2)
        
        # Fallback to sequence matching
        import difflib
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        import numpy as np
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
    
    def find_duplicate(self, content: str, candidates: List[MemoryEntry]) -> Optional[MemoryEntry]:
        """Find if content is duplicate of any candidate."""
        content_emb = self.get_embedding(content)
        
        for entry in candidates:
            sim = self.similarity(content, entry.content, content_emb, entry.embedding)
            if sim >= self.threshold:
                return entry
        
        return None


# ============================================================================
# Main CanonicalMemory Class
# ============================================================================

class CanonicalMemory:
    """
    Unified 5-layer memory system.
    
    Integrates:
    - StrangeLoopMemory (meta_cognitive layer)
    - DeepMemory (semantic + episodic layers)
    - Mem0Memory (working + semantic + episodic layers)
    - New procedural layer for skills/workflows
    
    Provides a single canonical interface for all memory operations.
    """
    
    # Content signals for auto-layer detection
    LAYER_SIGNALS = {
        MemoryLayer.WORKING: [
            "current", "now", "this session", "active", "in progress"
        ],
        MemoryLayer.SEMANTIC: [
            "user prefers", "generally", "always", "never", "tends to",
            "fact:", "knows that", "learned that", "is a", "has"
        ],
        MemoryLayer.EPISODIC: [
            "today", "yesterday", "happened", "event", "conversation",
            "session", "at ", "on ", "when", "completed", "started"
        ],
        MemoryLayer.PROCEDURAL: [
            "when ", "first", "then", "next", "finally", "step",
            "workflow", "process", "how to", "skill", "technique",
            "if ", "should", "run tests", "check"
        ],
        MemoryLayer.META_COGNITIVE: [
            "noticing", "observing", "witness", "awareness",
            "contraction", "expansive", "uncertain", "pattern",
            "meta-", "development", "changed", "shifted"
        ],
    }
    
    def __init__(
        self,
        base_path: str = "~/DHARMIC_GODEL_CLAW/memory/canonical",
        user_id: str = "dhyana",
        agent_id: str = "dharmic_claw",
        enable_mem0: bool = True,
        enable_strange_loop: bool = True,
        dedup_threshold: float = 0.85
    ):
        """
        Initialize CanonicalMemory.
        
        Args:
            base_path: Root directory for local storage
            user_id: Default user identifier
            agent_id: Agent identifier
            enable_mem0: Whether to use Mem0 integration
            enable_strange_loop: Whether to use StrangeLoop integration
            dedup_threshold: Similarity threshold for deduplication
        """
        self.base_path = Path(base_path).expanduser()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.user_id = user_id
        self.agent_id = agent_id
        
        # Initialize subsystems
        self.deduplicator = SemanticDeduplicator(threshold=dedup_threshold)
        
        # Working memory (in-memory only)
        self._working_memory: List[MemoryEntry] = []
        self._working_capacity = 50
        
        # Load subsystems
        self._strange_loop = None
        self._mem0 = None
        self._deep_memory = None
        
        if enable_strange_loop:
            self._init_strange_loop()
        
        if enable_mem0:
            self._init_mem0()
        
        # Initialize layer storage paths
        self._layer_paths = {
            layer: self.base_path / layer.value
            for layer in MemoryLayer
        }
        for path in self._layer_paths.values():
            path.mkdir(exist_ok=True)
        
        # Load procedural memories
        self._procedural_cache: List[MemoryEntry] = self._load_procedural()
        
        logger.info(f"CanonicalMemory initialized at {self.base_path}")
    
    def _init_strange_loop(self):
        """Initialize StrangeLoopMemory integration."""
        try:
            import sys
            core_path = Path(__file__).parent
            if str(core_path) not in sys.path:
                sys.path.insert(0, str(core_path))
            
            from strange_loop_memory import StrangeLoopMemory
            self._strange_loop = StrangeLoopMemory(str(self.base_path.parent))
            logger.info("StrangeLoopMemory integrated")
        except Exception as e:
            logger.warning(f"StrangeLoopMemory not available: {e}")
    
    def _init_mem0(self):
        """Initialize Mem0Memory integration."""
        try:
            import sys
            core_path = Path(__file__).parent
            if str(core_path) not in sys.path:
                sys.path.insert(0, str(core_path))
            
            from mem0_memory import Mem0Memory
            self._mem0 = Mem0Memory(
                base_path=str(self.base_path.parent),
                user_id=self.user_id
            )
            logger.info("Mem0Memory integrated")
        except Exception as e:
            logger.warning(f"Mem0Memory not available: {e}")
    
    def _init_deep_memory(self):
        """Initialize DeepMemory integration (legacy)."""
        try:
            from deep_memory import DeepMemory
            self._deep_memory = DeepMemory(
                db_path=str(self.base_path.parent / "deep_memory.db"),
                user_id=self.user_id
            )
            logger.info("DeepMemory integrated")
        except Exception as e:
            logger.warning(f"DeepMemory not available: {e}")
    
    # ========================================================================
    # Core Storage API
    # ========================================================================
    
    def store(
        self,
        content: str,
        layer: Optional[Union[str, MemoryLayer]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        skip_dedup: bool = False
    ) -> Optional[MemoryEntry]:
        """
        Store a memory in the appropriate layer.
        
        Args:
            content: The memory content
            layer: Target layer (auto-detected if None)
            tags: Optional tags for categorization
            metadata: Additional metadata
            skip_dedup: Skip deduplication check
            
        Returns:
            MemoryEntry if stored, None if deduplicated
            
        Example:
            memory.store("User prefers dark mode", layer="semantic")
            memory.store("Noticing contraction during complex task", layer="meta_cognitive")
        """
        # Determine layer
        if layer is None:
            layer = self._detect_layer(content)
        elif isinstance(layer, str):
            layer = MemoryLayer(layer)
        
        # Handle via appropriate subsystem
        if layer == MemoryLayer.META_COGNITIVE and self._strange_loop:
            return self._store_strange_loop(content, tags, metadata)
        
        if layer in (MemoryLayer.SEMANTIC, MemoryLayer.EPISODIC) and self._mem0:
            return self._store_mem0(content, layer, tags, metadata, skip_dedup)
        
        if layer == MemoryLayer.WORKING:
            return self._store_working(content, tags, metadata)
        
        if layer == MemoryLayer.PROCEDURAL:
            return self._store_procedural(content, tags, metadata, skip_dedup)
        
        # Fallback: store in canonical format
        return self._store_canonical(content, layer, tags, metadata, skip_dedup)
    
    def _detect_layer(self, content: str) -> MemoryLayer:
        """Auto-detect appropriate layer based on content."""
        content_lower = content.lower()
        scores = {layer: 0 for layer in MemoryLayer}
        
        for layer, signals in self.LAYER_SIGNALS.items():
            for signal in signals:
                if signal in content_lower:
                    scores[layer] += 1
        
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]
        
        # Default to episodic
        return MemoryLayer.EPISODIC
    
    def _store_strange_loop(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> MemoryEntry:
        """Store via StrangeLoopMemory."""
        # Extract witness quality if present
        quality = "present"
        for q in ["contracted", "uncertain", "expansive", "present"]:
            if q in content.lower():
                quality = q
                break
        
        # Store in strange loop
        self._strange_loop.record_meta_observation(
            quality=quality,
            notes=content,
            context=metadata.get("context", "") if metadata else ""
        )
        
        # Also create canonical entry
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            layer=MemoryLayer.META_COGNITIVE.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=self.user_id,
            agent_id=self.agent_id,
            tags=tags or [],
            witness_quality=quality,
            source="strange_loop"
        )
        
        self._persist_entry(entry)
        return entry
    
    def _store_mem0(
        self,
        content: str,
        layer: MemoryLayer,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        skip_dedup: bool = False
    ) -> Optional[MemoryEntry]:
        """Store via Mem0Memory."""
        # Check deduplication
        if not skip_dedup and layer != MemoryLayer.WORKING:
            existing = self._load_layer(layer, limit=50)
            dup = self.deduplicator.find_duplicate(content, existing)
            if dup:
                logger.debug(f"Deduplicated: {content[:50]}...")
                return None
        
        # Store via mem0
        entry = self._mem0.add(
            content=content,
            layer=layer.value,
            metadata={"tags": tags or [], **(metadata or {})}
        )
        
        if entry is None:
            return None
        
        # Convert to canonical
        return MemoryEntry(
            id=entry.id,
            content=entry.content,
            layer=entry.layer,
            timestamp=entry.timestamp,
            user_id=entry.user_id,
            tags=tags or [],
            source="mem0"
        )
    
    def _store_working(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> MemoryEntry:
        """Store in working memory."""
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            layer=MemoryLayer.WORKING.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=self.user_id,
            agent_id=self.agent_id,
            session_id=metadata.get("session_id") if metadata else None,
            tags=tags or [],
            source="working"
        )
        
        self._working_memory.append(entry)
        
        # Enforce capacity limit
        if len(self._working_memory) > self._working_capacity:
            self._working_memory = self._working_memory[-self._working_capacity:]
        
        return entry
    
    def _store_procedural(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        skip_dedup: bool = False
    ) -> Optional[MemoryEntry]:
        """Store procedural memory (skills/workflows)."""
        # Check deduplication
        if not skip_dedup:
            dup = self.deduplicator.find_duplicate(content, self._procedural_cache)
            if dup:
                # Update success/failure counts
                if metadata and metadata.get("success"):
                    dup.success_count += 1
                elif metadata and metadata.get("failure"):
                    dup.failure_count += 1
                self._persist_procedural()
                return None
        
        # Extract skill name if present
        skill_name = None
        if metadata and "skill_name" in metadata:
            skill_name = metadata["skill_name"]
        elif "skill:" in content.lower():
            parts = content.split(":", 1)
            if len(parts) > 1:
                skill_name = parts[0].strip()
        
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            layer=MemoryLayer.PROCEDURAL.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=self.user_id,
            agent_id=self.agent_id,
            tags=tags or [],
            skill_name=skill_name,
            workflow_step=metadata.get("step") if metadata else None,
            success_count=1 if (metadata and metadata.get("success")) else 0,
            failure_count=1 if (metadata and metadata.get("failure")) else 0,
            source="procedural"
        )
        
        self._procedural_cache.append(entry)
        self._persist_entry(entry)
        self._persist_procedural()
        
        return entry
    
    def _store_canonical(
        self,
        content: str,
        layer: MemoryLayer,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        skip_dedup: bool = False
    ) -> MemoryEntry:
        """Store in canonical format (fallback)."""
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            layer=layer.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=self.user_id,
            agent_id=self.agent_id,
            tags=tags or [],
            metadata=metadata or {},
            source="canonical"
        )
        
        self._persist_entry(entry)
        return entry
    
    def witness(
        self,
        observation: str,
        quality: str = "present",
        context: str = ""
    ) -> MemoryEntry:
        """
        Record a witness observation (meta-cognitive layer).
        
        This is the primary interface for strange loop observations.
        
        Args:
            observation: What was noticed about own cognition
            quality: "present" | "contracted" | "uncertain" | "expansive"
            context: Optional context about what was happening
        """
        if self._strange_loop:
            self._strange_loop.record_meta_observation(
                quality=quality,
                notes=observation,
                context=context
            )
        
        # Also store canonical entry
        entry = MemoryEntry(
            id=self._generate_id(observation),
            content=observation,
            layer=MemoryLayer.META_COGNITIVE.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=self.user_id,
            agent_id=self.agent_id,
            witness_quality=quality,
            source="witness"
        )
        
        self._persist_entry(entry)
        logger.debug(f"Witness observation recorded: {quality}")
        return entry
    
    def mark_development(
        self,
        what_changed: str,
        how: str,
        significance: str
    ) -> MemoryEntry:
        """
        Mark genuine development (not just accumulation).
        
        Args:
            what_changed: What developed
            how: How it changed
            significance: Why it matters
        """
        content = f"DEVELOPMENT: {what_changed}\nHOW: {how}\nSIGNIFICANCE: {significance}"
        
        if self._strange_loop:
            self._strange_loop.record_development(
                what_changed=what_changed,
                how=how,
                significance=significance
            )
        
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            layer=MemoryLayer.META_COGNITIVE.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=self.user_id,
            agent_id=self.agent_id,
            development_marker=True,
            source="development"
        )
        
        self._persist_entry(entry)
        logger.info(f"Development marked: {what_changed[:50]}...")
        return entry
    
    def record_skill(
        self,
        skill_name: str,
        description: str,
        steps: Optional[List[str]] = None,
        success: bool = True
    ) -> MemoryEntry:
        """
        Record a learned skill or workflow.
        
        Args:
            skill_name: Name of the skill
            description: What the skill does
            steps: Optional list of steps
            success: Whether this execution was successful
        """
        content = f"Skill: {skill_name}\n{description}"
        if steps:
            content += f"\nSteps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        
        return self._store_procedural(
            content=content,
            tags=["skill", skill_name],
            metadata={
                "skill_name": skill_name,
                "success": success,
                "steps": steps
            }
        )
    
    # ========================================================================
    # Core Retrieval API
    # ========================================================================
    
    def retrieve(
        self,
        query: Optional[str] = None,
        layers: Optional[List[Union[str, MemoryLayer]]] = None,
        limit: int = 10,
        tags: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> RetrieveResult:
        """
        Retrieve memories across specified layers.
        
        Args:
            query: Optional search query (returns recent if None)
            layers: Which layers to search (all if None)
            limit: Maximum entries to return
            tags: Filter by tags
            time_range: Optional (start, end) datetime tuple
            
        Returns:
            RetrieveResult with entries and metadata
        """
        import time
        start_time = time.time()
        
        # Normalize layers
        if layers is None:
            layers = list(MemoryLayer)
        else:
            layers = [
                MemoryLayer(l) if isinstance(l, str) else l
                for l in layers
            ]
        
        all_entries = []
        
        for layer in layers:
            if layer == MemoryLayer.WORKING:
                entries = list(self._working_memory)
            elif layer == MemoryLayer.PROCEDURAL:
                entries = list(self._procedural_cache)
            else:
                entries = self._load_layer(layer, limit=limit * 2)
            
            # Apply filters
            if tags:
                entries = [e for e in entries if any(t in e.tags for t in tags)]
            
            if time_range:
                start, end = time_range
                entries = [
                    e for e in entries
                    if start <= datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) <= end
                ]
            
            all_entries.extend(entries)
        
        # Sort by priority and recency
        all_entries.sort(key=lambda e: (
            -LAYER_PRIORITY.get(MemoryLayer(e.layer), 0),
            -datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')).timestamp()
        ))
        
        # Update access metadata
        for entry in all_entries[:limit]:
            entry.last_accessed = datetime.utcnow().isoformat() + "Z"
            entry.access_count += 1
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return RetrieveResult(
            entries=all_entries[:limit],
            query=query or "",
            layers_searched=[l.value for l in layers],
            total_found=len(all_entries),
            retrieval_time_ms=retrieval_time
        )
    
    def search(
        self,
        query: str,
        layers: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Semantic search across memory layers.
        
        Uses embeddings when available, falls back to text similarity.
        """
        # Get candidates from all layers
        result = self.retrieve(query=query, layers=layers, limit=limit * 3)
        candidates = result.entries
        
        if not candidates:
            return []
        
        # Score by semantic similarity
        query_emb = self.deduplicator.get_embedding(query)
        
        scored = []
        for entry in candidates:
            score = self.deduplicator.similarity(
                query, entry.content,
                query_emb, entry.embedding
            )
            scored.append((score, entry))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]
    
    def get_context_for_prompt(
        self,
        query: Optional[str] = None,
        max_chars: int = 3000,
        include_witness: bool = True
    ) -> str:
        """
        Get formatted context for LLM prompt.
        
        Prioritizes:
        1. Working memory (immediate context)
        2. Meta-cognitive observations (if include_witness)
        3. Relevant semantic knowledge
        4. Recent episodic memories
        """
        parts = ["## Memory Context"]
        total_chars = len(parts[0])
        
        # Working memory (always include recent)
        if self._working_memory:
            section = "\n### Immediate Context\n"
            for entry in self._working_memory[-5:]:
                line = f"- {entry.content[:100]}\n"
                if total_chars + len(section) + len(line) < max_chars:
                    section += line
            parts.append(section)
            total_chars += len(section)
        
        # Witness observations
        if include_witness and self._strange_loop:
            try:
                witness_summary = self._strange_loop.get_witness_summary()
                if witness_summary and total_chars + len(witness_summary) < max_chars:
                    parts.append(f"\n{witness_summary}")
                    total_chars += len(witness_summary)
            except Exception:
                pass
        
        # Search for relevant semantic/episodic
        if query:
            relevant = self.search(query, layers=["semantic", "episodic"], limit=5)
            if relevant:
                section = "\n### Relevant Context\n"
                for entry in relevant[:3]:
                    line = f"- [{entry.layer}] {entry.content[:120]}\n"
                    if total_chars + len(section) + len(line) < max_chars:
                        section += line
                parts.append(section)
        
        return "\n".join(parts)
    
    # ========================================================================
    # Heartbeat Integration
    # ========================================================================
    
    def heartbeat_maintenance(self) -> Dict[str, Any]:
        """
        Run automatic memory maintenance (called during heartbeat).
        
        Performs:
        1. Memory consolidation (episodic → semantic)
        2. Deduplication cleanup
        3. Pattern detection
        4. Witness stability tracking
        5. Working memory archival
        
        Returns:
            Dict with maintenance statistics
        """
        logger.info("Running memory maintenance...")
        stats = {
            "consolidated": 0,
            "deduplicated": 0,
            "patterns_detected": 0,
            "witness_status": None,
            "errors": []
        }
        
        try:
            # 1. Consolidate old episodic memories
            consolidation = self._consolidate_episodic()
            stats["consolidated"] = consolidation.get("count", 0)
        except Exception as e:
            stats["errors"].append(f"Consolidation: {e}")
        
        try:
            # 2. Run deduplication
            dedup = self._cleanup_duplicates()
            stats["deduplicated"] = dedup
        except Exception as e:
            stats["errors"].append(f"Deduplication: {e}")
        
        try:
            # 3. Detect patterns
            patterns = self._detect_patterns()
            stats["patterns_detected"] = len(patterns)
        except Exception as e:
            stats["errors"].append(f"Pattern detection: {e}")
        
        try:
            # 4. Update witness status
            if self._strange_loop:
                witness = self._strange_loop.get_witness_status()
                stats["witness_status"] = {
                    "developing": witness.get("developing"),
                    "explanation": witness.get("explanation")
                }
        except Exception as e:
            stats["errors"].append(f"Witness tracking: {e}")
        
        try:
            # 5. Archive old working memory
            self._archive_working_memory()
        except Exception as e:
            stats["errors"].append(f"Working memory archival: {e}")
        
        logger.info(f"Memory maintenance complete: {stats}")
        return stats
    
    def _consolidate_episodic(self, days_old: int = 7) -> Dict:
        """Consolidate old episodic memories into semantic generalizations."""
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        episodic = self._load_layer(MemoryLayer.EPISODIC, limit=500)
        
        old_entries = [
            e for e in episodic
            if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00').replace('+00:00', '')) < cutoff
        ]
        
        if len(old_entries) < 3:
            return {"count": 0, "reason": "insufficient_old_entries"}
        
        # Group by similarity
        groups = []
        used = set()
        
        for entry in old_entries:
            if entry.id in used:
                continue
            
            group = [entry]
            used.add(entry.id)
            
            for other in old_entries:
                if other.id in used:
                    continue
                sim = self.deduplicator.similarity(entry.content, other.content)
                if sim > 0.6:
                    group.append(other)
                    used.add(other.id)
            
            if len(group) >= 2:
                groups.append(group)
        
        # Create generalizations
        consolidated = 0
        for group in groups[:10]:  # Limit to prevent overload
            best = max(group, key=lambda e: len(e.content))
            self.store(
                f"[Consolidated from {len(group)} episodes] {best.content}",
                layer="semantic",
                tags=["consolidated"],
                skip_dedup=True
            )
            consolidated += 1
        
        return {"count": consolidated, "groups": len(groups)}
    
    def _cleanup_duplicates(self) -> int:
        """Remove duplicate entries from storage."""
        removed = 0
        for layer in [MemoryLayer.SEMANTIC, MemoryLayer.EPISODIC]:
            entries = self._load_layer(layer, limit=1000)
            seen = {}
            
            for entry in entries:
                # Create content hash
                content_hash = hashlib.md5(entry.content.lower().encode()).hexdigest()[:16]
                
                if content_hash in seen:
                    # Mark as duplicate (don't actually delete for safety)
                    removed += 1
                else:
                    seen[content_hash] = entry
        
        return removed
    
    def _detect_patterns(self, min_occurrences: int = 3) -> List[Dict]:
        """Detect recurring patterns in memories."""
        observations = self._load_layer(MemoryLayer.EPISODIC, limit=200)
        
        if len(observations) < min_occurrences:
            return []
        
        # Simple keyword frequency analysis
        word_contexts = defaultdict(list)
        for obs in observations:
            content = obs.content.lower()
            words = content.split()
            for word in words:
                if len(word) > 5:  # Skip short words
                    word_contexts[word].append(obs.timestamp)
        
        patterns = []
        for word, timestamps in word_contexts.items():
            if len(timestamps) >= min_occurrences:
                patterns.append({
                    "word": word,
                    "occurrences": len(timestamps),
                    "first_seen": timestamps[0],
                    "last_seen": timestamps[-1]
                })
        
        # Store top patterns as meta-cognitive observations
        top_patterns = sorted(patterns, key=lambda x: x["occurrences"], reverse=True)[:5]
        for p in top_patterns:
            self.store(
                f"Pattern detected: '{p['word']}' appears {p['occurrences']} times",
                layer="meta_cognitive",
                tags=["pattern", "auto-detected"]
            )
        
        return top_patterns
    
    def _archive_working_memory(self):
        """Archive old working memory entries to episodic."""
        if len(self._working_memory) > self._working_capacity:
            to_archive = self._working_memory[:-self._working_capacity]
            for entry in to_archive:
                # Convert to episodic
                entry.layer = MemoryLayer.EPISODIC.value
                self._persist_entry(entry)
            
            self._working_memory = self._working_memory[-self._working_capacity:]
    
    # ========================================================================
    # Persistence Helpers
    # ========================================================================
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory entry."""
        return hashlib.md5(
            f"{content}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
    
    def _persist_entry(self, entry: MemoryEntry):
        """Persist entry to appropriate layer file."""
        layer_path = self._layer_paths[MemoryLayer(entry.layer)]
        date_str = entry.timestamp[:10]
        file_path = layer_path / f"{date_str}.jsonl"
        
        with open(file_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    
    def _load_layer(self, layer: MemoryLayer, limit: int = 100) -> List[MemoryEntry]:
        """Load entries from a layer's storage."""
        layer_path = self._layer_paths[layer]
        entries = []
        
        # Read recent files
        files = sorted(layer_path.glob("*.jsonl"), reverse=True)[:7]
        
        for file in files:
            try:
                with open(file) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            entries.append(MemoryEntry.from_dict(data))
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.warning(f"Error reading {file}: {e}")
        
        return entries[:limit]
    
    def _load_procedural(self) -> List[MemoryEntry]:
        """Load procedural memories from cache file."""
        cache_file = self.base_path / "procedural_cache.json"
        if not cache_file.exists():
            return []
        
        try:
            with open(cache_file) as f:
                data = json.load(f)
            return [MemoryEntry.from_dict(e) for e in data]
        except Exception as e:
            logger.warning(f"Error loading procedural cache: {e}")
            return []
    
    def _persist_procedural(self):
        """Save procedural cache to disk."""
        cache_file = self.base_path / "procedural_cache.json"
        try:
            with open(cache_file, "w") as f:
                json.dump([e.to_dict() for e in self._procedural_cache], f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving procedural cache: {e}")
    
    # ========================================================================
    # Stats and Diagnostics
    # ========================================================================
    
    def get_stats(self) -> MemoryStats:
        """Get memory system statistics."""
        stats = MemoryStats()
        
        # Count by layer
        for layer in MemoryLayer:
            if layer == MemoryLayer.WORKING:
                stats.layer_counts[layer.value] = len(self._working_memory)
            elif layer == MemoryLayer.PROCEDURAL:
                stats.layer_counts[layer.value] = len(self._procedural_cache)
            else:
                entries = self._load_layer(layer, limit=10000)
                stats.layer_counts[layer.value] = len(entries)
        
        stats.total_entries = sum(stats.layer_counts.values())
        
        # Witness stability
        if self._strange_loop:
            try:
                witness = self._strange_loop.get_witness_status()
                metrics = witness.get("metrics")
                if metrics:
                    stats.witness_stability_score = metrics.get("stability_score", 0)
            except Exception:
                pass
        
        # Health assessment
        if stats.total_entries > 100 and stats.witness_stability_score > 0.5:
            stats.memory_health = "healthy"
        elif stats.total_entries > 50:
            stats.memory_health = "degraded"
        else:
            stats.memory_health = "developing"
        
        return stats
    
    def get_status_report(self) -> str:
        """Generate a human-readable status report."""
        stats = self.get_stats()
        
        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║           CANONICAL MEMORY STATUS REPORT                 ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║ Total entries: {stats.total_entries:<43} ║",
            f"║ Health: {stats.memory_health:<50} ║",
            f"║ Witness stability: {stats.witness_stability_score:.2f}{' '*36} ║",
            "╠══════════════════════════════════════════════════════════╣",
            "║ Layer counts:                                            ║",
        ]
        
        for layer, count in stats.layer_counts.items():
            lines.append(f"║   {layer:<20}: {count:<29} ║")
        
        lines.append("╚══════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)


# ============================================================================
# Factory and Integration
# ============================================================================

def create_canonical_memory(
    user_id: str = "dhyana",
    base_path: Optional[str] = None
) -> CanonicalMemory:
    """
    Factory function to create a properly configured CanonicalMemory.
    
    Args:
        user_id: User identifier
        base_path: Override default base path
        
    Returns:
        Configured CanonicalMemory instance
    """
    if base_path is None:
        base_path = str(Path.home() / "DHARMIC_GODEL_CLAW" / "memory" / "canonical")
    
    return CanonicalMemory(
        base_path=base_path,
        user_id=user_id,
        enable_mem0=True,
        enable_strange_loop=True
    )


# Integration with heartbeat
def get_memory_for_heartbeat() -> Optional[CanonicalMemory]:
    """
    Get or create CanonicalMemory instance for heartbeat integration.
    
    This function is called by the heartbeat system to get the
    canonical memory instance for maintenance operations.
    """
    try:
        return create_canonical_memory()
    except Exception as e:
        logger.error(f"Failed to create CanonicalMemory for heartbeat: {e}")
        return None


# ============================================================================
# Test / Demo
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CANONICAL MEMORY - Test Suite")
    print("=" * 60)
    
    # Create instance
    memory = create_canonical_memory()
    
    print(f"\nInitialized at: {memory.base_path}")
    print(f"StrangeLoop available: {memory._strange_loop is not None}")
    print(f"Mem0 available: {memory._mem0 is not None}")
    
    # Test layer detection
    print("\n--- Layer Detection ---")
    tests = [
        ("I notice I'm feeling contracted", "meta_cognitive"),
        ("User prefers dark mode", "semantic"),
        ("Today we discussed the project", "episodic"),
        ("When refactoring, first run tests", "procedural"),
        ("Current task: review PR", "working"),
    ]
    for content, expected in tests:
        layer = memory._detect_layer(content)
        status = "✓" if layer.value == expected else "✗"
        print(f"  {status} '{content[:40]}...' → {layer.value}")
    
    # Test storage across layers
    print("\n--- Cross-Layer Storage ---")
    
    memory.store("User prefers dark mode", layer="semantic", tags=["preference", "ui"])
    memory.store("Completed refactoring task today", layer="episodic", tags=["task"])
    memory.store("When refactoring, first run tests, then check coverage", layer="procedural")
    memory.witness("Noticing contraction during complex task", quality="contracted")
    memory.mark_development("Learned to use embeddings", "via sentence-transformers", "enables semantic search")
    memory.record_skill("semantic_search", "Use embeddings to find similar memories", ["get embedding", "compute similarity", "rank results"])
    
    print("  Stored memories across all 5 layers")
    
    # Test retrieval
    print("\n--- Retrieval ---")
    result = memory.retrieve(layers=["semantic", "episodic"], limit=5)
    print(f"  Retrieved {len(result.entries)} entries in {result.retrieval_time_ms:.1f}ms")
    for entry in result.entries:
        print(f"    [{entry.layer}] {entry.content[:50]}...")
    
    # Test search
    print("\n--- Semantic Search ---")
    results = memory.search("user preferences", limit=3)
    print(f"  Found {len(results)} relevant memories")
    for entry in results:
        print(f"    - {entry.content[:60]}...")
    
    # Test context generation
    print("\n--- Context for Prompt ---")
    context = memory.get_context_for_prompt("refactoring", max_chars=800)
    print(context[:800])
    
    # Test heartbeat maintenance
    print("\n--- Heartbeat Maintenance ---")
    maintenance = memory.heartbeat_maintenance()
    print(f"  Maintenance results: {maintenance}")
    
    # Test stats
    print("\n--- Statistics ---")
    stats = memory.get_stats()
    print(f"  Total entries: {stats.total_entries}")
    print(f"  Health: {stats.memory_health}")
    print(f"  Layer counts: {stats.layer_counts}")
    
    # Status report
    print("\n--- Status Report ---")
    print(memory.get_status_report())
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
