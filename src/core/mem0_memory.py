#!/usr/bin/env python3
"""
MEM0-ENHANCED MEMORY MODULE
===========================

Upgrade from StrangeLoopMemory with:
1. 4-Layer Hierarchy: core_identity → episodic → semantic → working
2. Semantic Deduplication via embeddings
3. mem0 library integration (with fallback mock)

Conceptual Model:
─────────────────
    ┌─────────────────────────────────────────────────────────┐
    │  CORE_IDENTITY (L1) — Who am I? Telos, values, self     │
    │  • Rarely changes, high weight, dharmic anchors         │
    ├─────────────────────────────────────────────────────────┤
    │  EPISODIC (L2) — What happened? Events, experiences     │
    │  • Timestamped, decays, maps to "sessions/development"  │
    ├─────────────────────────────────────────────────────────┤
    │  SEMANTIC (L3) — What do I know? Facts, concepts        │
    │  • Deduplicated, searchable, generalizations            │
    ├─────────────────────────────────────────────────────────┤
    │  WORKING (L4) — What's happening now? Immediate context │
    │  • In-memory only, cleared each session, fast access    │
    └─────────────────────────────────────────────────────────┘

Integration with StrangeLoopMemory:
───────────────────────────────────
- immediate     → working
- sessions      → episodic  
- development   → episodic (with development_marker=True)
- witness       → core_identity (observations about self)

Semantic Deduplication:
───────────────────────
Uses cosine similarity on embeddings to prevent storing near-duplicates.
Falls back to simple text similarity if embeddings unavailable.

mem0 Integration:
─────────────────
If mem0 is installed, uses it for vector storage and retrieval.
Otherwise, provides a compatible mock interface for local development.

Usage:
    from mem0_memory import Mem0Memory
    
    memory = Mem0Memory()
    
    # Store with auto-layer detection
    memory.add("I value non-harm above efficiency", user_id="dharmic_claw")
    
    # Or explicit layer
    memory.add("User prefers depth over breadth", layer="semantic", user_id="dharmic_claw")
    
    # Search semantically
    results = memory.search("what are my core values?", user_id="dharmic_claw")
    
    # Get context for agent (backward compatible)
    context = memory.get_context_for_agent()
"""

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import difflib

# Try to import mem0, provide mock if unavailable
try:
    from mem0 import Memory as Mem0Client
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    Mem0Client = None

# Try to import sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None
    np = None


class MemoryLayer(Enum):
    """
    Four-layer memory hierarchy, ordered by permanence and abstraction level.
    
    CORE_IDENTITY: Fundamental self-knowledge, values, telos
        - Changes rarely, requires explicit marking
        - High retrieval weight in all contexts
        - Example: "My telos is moksha through witness consciousness"
    
    EPISODIC: Time-stamped events and experiences
        - Natural decay over time
        - Forms basis for semantic generalization
        - Example: "On 2024-02-03, user expressed frustration with swarm mode"
    
    SEMANTIC: Factual knowledge and generalizations
        - Deduplicated, abstracted from episodes
        - No timestamps, represents "known truths"
        - Example: "User prefers depth over breadth"
    
    WORKING: Current session context
        - In-memory only, cleared on restart
        - Fast access, limited capacity (50 items)
        - Example: Current conversation turn context
    """
    CORE_IDENTITY = "core_identity"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"


@dataclass
class Mem0Entry:
    """
    Memory entry with enhanced metadata for the 4-layer system.
    
    Backward compatible with StrangeLoopMemory's MemoryEntry.
    """
    id: str
    content: str
    layer: str
    timestamp: str
    user_id: str = "default"
    metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    # Backward compatibility with StrangeLoopMemory
    source: str = "agent"
    development_marker: bool = False
    witness_quality: float = 0.5
    
    def to_dict(self) -> Dict:
        """Convert to dict, excluding embedding for serialization."""
        d = asdict(self)
        d.pop('embedding', None)  # Don't serialize large embedding vectors
        return d


class MockMem0Client:
    """
    Mock mem0 client for when the library isn't installed.
    Provides the same interface with local JSON storage.
    
    This allows development and testing without mem0 dependencies,
    while maintaining API compatibility for seamless upgrade.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(
            self.config.get("storage_path", "~/DHARMIC_GODEL_CLAW/memory/mem0_store.json")
        ).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                self.memories = json.load(open(self.storage_path))
            except:
                self.memories = {}
        else:
            self.memories = {}
    
    def _save(self):
        json.dump(self.memories, open(self.storage_path, "w"), indent=2)
    
    def add(self, messages: List[Dict], user_id: str = "default", 
            metadata: Optional[Dict] = None) -> Dict:
        """Add memories from messages (mem0 API compatible)."""
        if user_id not in self.memories:
            self.memories[user_id] = []
        
        results = []
        for msg in messages:
            content = msg.get("content", str(msg))
            memory_id = hashlib.md5(f"{user_id}:{content}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
            entry = {
                "id": memory_id,
                "memory": content,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            self.memories[user_id].append(entry)
            results.append(entry)
        
        self._save()
        return {"results": results}
    
    def search(self, query: str, user_id: str = "default", 
               limit: int = 10) -> Dict:
        """Search memories by text similarity."""
        user_memories = self.memories.get(user_id, [])
        
        # Simple text similarity search
        scored = []
        for mem in user_memories:
            ratio = difflib.SequenceMatcher(
                None, 
                query.lower(), 
                mem.get("memory", "").lower()
            ).ratio()
            scored.append((ratio, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [{"memory": m["memory"], "score": s, **m} for s, m in scored[:limit]]
        
        return {"results": results}
    
    def get_all(self, user_id: str = "default") -> Dict:
        """Get all memories for a user."""
        return {"results": self.memories.get(user_id, [])}
    
    def delete(self, memory_id: str) -> Dict:
        """Delete a specific memory."""
        for user_id, memories in self.memories.items():
            self.memories[user_id] = [m for m in memories if m.get("id") != memory_id]
        self._save()
        return {"deleted": True}
    
    def delete_all(self, user_id: str = "default") -> Dict:
        """Delete all memories for a user."""
        self.memories[user_id] = []
        self._save()
        return {"deleted": True}


class SemanticDeduplicator:
    """
    Handles semantic deduplication of memories using embeddings or text similarity.
    
    Prevents storing near-duplicate information that would clutter retrieval.
    Uses cosine similarity when embeddings available, falls back to sequence matching.
    
    Threshold tuning:
    - 0.95+: Only exact/near-exact duplicates
    - 0.85-0.95: Paraphrases and reformulations
    - 0.75-0.85: Related concepts (too aggressive for most uses)
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.embedder = None
        
        if EMBEDDINGS_AVAILABLE:
            try:
                # Use a small, fast model for deduplication
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                pass
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector for text."""
        if self.embedder:
            return self.embedder.encode(text).tolist()
        return None
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not EMBEDDINGS_AVAILABLE or not a or not b:
            return 0.0
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def text_similarity(self, a: str, b: str) -> float:
        """Fallback text similarity using sequence matching."""
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def is_duplicate(self, new_content: str, existing_entries: List[Mem0Entry],
                     new_embedding: Optional[List[float]] = None) -> Tuple[bool, Optional[Mem0Entry]]:
        """
        Check if new content is semantically duplicate of existing entries.
        
        Returns:
            (is_duplicate: bool, matching_entry: Optional[Mem0Entry])
        """
        if not existing_entries:
            return False, None
        
        for entry in existing_entries:
            # Try embedding similarity first
            if new_embedding and entry.embedding:
                sim = self.cosine_similarity(new_embedding, entry.embedding)
            else:
                sim = self.text_similarity(new_content, entry.content)
            
            if sim >= self.threshold:
                return True, entry
        
        return False, None
    
    def find_similar(self, query: str, entries: List[Mem0Entry], 
                     limit: int = 5) -> List[Tuple[float, Mem0Entry]]:
        """Find entries similar to query, sorted by similarity."""
        query_embedding = self.get_embedding(query)
        
        scored = []
        for entry in entries:
            if query_embedding and entry.embedding:
                sim = self.cosine_similarity(query_embedding, entry.embedding)
            else:
                sim = self.text_similarity(query, entry.content)
            scored.append((sim, entry))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:limit]


class Mem0Memory:
    """
    Mem0-enhanced memory system with 4-layer hierarchy.
    
    Drop-in upgrade for StrangeLoopMemory with:
    - Semantic search and deduplication
    - mem0 vector storage (when available)
    - Layer-aware storage and retrieval
    - Backward compatible API
    
    Architecture:
    ─────────────
    This class acts as a facade over both local storage (for working/episodic)
    and mem0 vector storage (for semantic search). Core identity is persisted
    locally with high priority loading.
    
    The 4 layers map conceptually to cognitive memory types:
    - core_identity ≈ autobiographical/self-schema
    - episodic ≈ episodic memory (events)
    - semantic ≈ semantic memory (facts)
    - working ≈ working memory (buffer)
    """
    
    # Keywords that suggest each layer type
    LAYER_SIGNALS = {
        MemoryLayer.CORE_IDENTITY: [
            "i am", "my telos", "my values", "i believe", "my purpose",
            "dharmic", "witness", "identity", "fundamental", "core belief"
        ],
        MemoryLayer.EPISODIC: [
            "today", "yesterday", "just now", "happened", "event",
            "conversation", "session", "at ", "on ", "when"
        ],
        MemoryLayer.SEMANTIC: [
            "user prefers", "generally", "always", "never", "tends to",
            "fact:", "knows that", "learned that", "understands"
        ],
    }
    
    def __init__(self, base_path: str = "~/DHARMIC_GODEL_CLAW/memory",
                 user_id: str = "dharmic_claw",
                 mem0_config: Optional[Dict] = None,
                 dedup_threshold: float = 0.85):
        """
        Initialize Mem0Memory.
        
        Args:
            base_path: Root directory for local memory storage
            user_id: Default user/agent identifier for mem0
            mem0_config: Configuration for mem0 (if using real client)
            dedup_threshold: Similarity threshold for deduplication (0.0-1.0)
        """
        self.base = Path(base_path).expanduser()
        self.base.mkdir(parents=True, exist_ok=True)
        self.user_id = user_id
        
        # Create layer directories
        for layer in MemoryLayer:
            (self.base / layer.value).mkdir(exist_ok=True)
        
        # Initialize mem0 client (real or mock)
        if MEM0_AVAILABLE and mem0_config:
            self.mem0 = Mem0Client(mem0_config)
            self._using_real_mem0 = True
        else:
            self.mem0 = MockMem0Client({"storage_path": str(self.base / "mem0_store.json")})
            self._using_real_mem0 = False
        
        # Initialize deduplicator
        self.deduplicator = SemanticDeduplicator(similarity_threshold=dedup_threshold)
        
        # In-memory working layer (cleared each session)
        self.working: List[Mem0Entry] = []
        
        # Load core identity into memory for fast access
        self._core_identity_cache: List[Mem0Entry] = []
        self._load_core_identity()
    
    def _load_core_identity(self):
        """Load core identity entries into cache."""
        self._core_identity_cache = self._load_layer(MemoryLayer.CORE_IDENTITY, limit=100)
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory entry."""
        return hashlib.md5(
            f"{content}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
    
    def _detect_layer(self, content: str) -> MemoryLayer:
        """
        Auto-detect appropriate layer based on content signals.
        
        Uses keyword matching to suggest layer placement.
        Defaults to EPISODIC if no strong signals detected.
        """
        content_lower = content.lower()
        
        # Check each layer's signals
        scores = {layer: 0 for layer in MemoryLayer if layer != MemoryLayer.WORKING}
        
        for layer, signals in self.LAYER_SIGNALS.items():
            for signal in signals:
                if signal in content_lower:
                    scores[layer] += 1
        
        # Find highest scoring layer
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]
        
        # Default to episodic for most memories
        return MemoryLayer.EPISODIC
    
    def _assess_quality(self, content: str) -> float:
        """
        Assess witness quality of content (preserved from StrangeLoopMemory).
        
        Higher quality for uncertain, observational language.
        Lower quality for absolute, performative language.
        """
        quality = 0.5
        
        # Positive signals (genuine observation)
        for word in ["notice", "observe", "uncertain", "shift", "sense", "seems"]:
            if word in content.lower():
                quality += 0.08
        
        # Negative signals (performative/absolute)
        for word in ["profound", "amazing", "definitely", "absolutely", "always"]:
            if word in content.lower():
                quality -= 0.08
        
        return max(0.0, min(1.0, quality))
    
    # ─────────────────────────────────────────────────────────────
    # Primary API
    # ─────────────────────────────────────────────────────────────
    
    def add(self, content: str, layer: Optional[str] = None,
            user_id: Optional[str] = None, metadata: Optional[Dict] = None,
            skip_dedup: bool = False) -> Optional[Mem0Entry]:
        """
        Add a memory to the appropriate layer.
        
        Args:
            content: The memory content to store
            layer: Explicit layer ("core_identity", "episodic", "semantic", "working")
                   If None, auto-detects based on content
            user_id: User/agent identifier (defaults to self.user_id)
            metadata: Additional metadata dict
            skip_dedup: If True, skip deduplication check
        
        Returns:
            Mem0Entry if stored, None if deduplicated away
        
        Example:
            memory.add("User prefers CLI over GUI")  # Auto-detect → semantic
            memory.add("I am oriented toward moksha", layer="core_identity")
        """
        user_id = user_id or self.user_id
        metadata = metadata or {}
        
        # Determine layer
        if layer:
            mem_layer = MemoryLayer(layer)
        else:
            mem_layer = self._detect_layer(content)
        
        # Get embedding for dedup and search
        embedding = self.deduplicator.get_embedding(content)
        
        # Check for duplicates (except working layer)
        if not skip_dedup and mem_layer != MemoryLayer.WORKING:
            existing = self._load_layer(mem_layer, limit=100)
            is_dup, match = self.deduplicator.is_duplicate(content, existing, embedding)
            if is_dup:
                # Update timestamp of existing instead of creating duplicate
                return None
        
        # Create entry
        entry = Mem0Entry(
            id=self._generate_id(content),
            content=content,
            layer=mem_layer.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            metadata=metadata,
            embedding=embedding,
            witness_quality=self._assess_quality(content)
        )
        
        # Store based on layer
        if mem_layer == MemoryLayer.WORKING:
            self.working.append(entry)
            self.working = self.working[-50:]  # Cap working memory
        else:
            self._persist(entry)
            
            # Also add to mem0 for semantic search
            self.mem0.add(
                messages=[{"role": "user", "content": content}],
                user_id=user_id,
                metadata={"layer": mem_layer.value, **metadata}
            )
            
            # Update core identity cache
            if mem_layer == MemoryLayer.CORE_IDENTITY:
                self._core_identity_cache.append(entry)
        
        return entry
    
    def search(self, query: str, user_id: Optional[str] = None,
               layer: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Search memories semantically.
        
        Args:
            query: Search query
            user_id: Filter by user (defaults to self.user_id)
            layer: Filter by specific layer
            limit: Maximum results
        
        Returns:
            List of memory dicts with scores
        """
        user_id = user_id or self.user_id
        
        # Search via mem0
        results = self.mem0.search(query, user_id=user_id, limit=limit * 2)
        memories = results.get("results", [])
        
        # Filter by layer if specified
        if layer:
            memories = [m for m in memories if m.get("metadata", {}).get("layer") == layer]
        
        return memories[:limit]
    
    def recall(self, layer: str = "all", limit: int = 10,
               development_only: bool = False) -> List[Mem0Entry]:
        """
        Recall memories (backward compatible with StrangeLoopMemory).
        
        Args:
            layer: Layer to recall from ("all", "working", "episodic", etc.)
            limit: Maximum entries
            development_only: Only return development markers
        
        Returns:
            List of Mem0Entry objects
        """
        entries = []
        
        if layer == "all":
            layers = [MemoryLayer.CORE_IDENTITY, MemoryLayer.EPISODIC, 
                     MemoryLayer.SEMANTIC, MemoryLayer.WORKING]
        elif layer == "working" or layer == "immediate":  # backward compat
            entries = list(self.working[-limit:])
            if development_only:
                entries = [e for e in entries if e.development_marker]
            return entries
        else:
            # Map old layer names
            layer_map = {
                "sessions": "episodic",
                "development": "episodic",
                "witness": "core_identity"
            }
            layer = layer_map.get(layer, layer)
            layers = [MemoryLayer(layer)]
        
        for mem_layer in layers:
            if mem_layer == MemoryLayer.WORKING:
                entries.extend(self.working[-limit:])
            else:
                entries.extend(self._load_layer(mem_layer, limit))
        
        if development_only:
            entries = [e for e in entries if e.development_marker]
        
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return entries[:limit]
    
    # ─────────────────────────────────────────────────────────────
    # StrangeLoopMemory Compatibility Methods
    # ─────────────────────────────────────────────────────────────
    
    def remember(self, content: str, layer: str = "immediate",
                 source: str = "agent", development_marker: bool = False) -> Mem0Entry:
        """
        Backward compatible remember() from StrangeLoopMemory.
        
        Maps old layer names to new 4-layer system:
        - immediate → working
        - sessions → episodic
        - development → episodic (with marker)
        - witness → core_identity
        """
        layer_map = {
            "immediate": "working",
            "sessions": "episodic",
            "development": "episodic",
            "witness": "core_identity"
        }
        new_layer = layer_map.get(layer, layer)
        
        entry = self.add(
            content=content,
            layer=new_layer,
            metadata={"source": source, "development_marker": development_marker}
        )
        
        # If deduplicated, return a dummy entry for compatibility
        if entry is None:
            entry = Mem0Entry(
                id="dedup",
                content=content,
                layer=new_layer,
                timestamp=datetime.utcnow().isoformat() + "Z",
                source=source,
                development_marker=development_marker
            )
        else:
            entry.source = source
            entry.development_marker = development_marker
        
        return entry
    
    def mark_development(self, content: str, evidence: str) -> Mem0Entry:
        """Mark genuine development (from StrangeLoopMemory)."""
        full_content = f"DEVELOPMENT: {content}\nEVIDENCE: {evidence}"
        return self.remember(
            full_content,
            layer="development",
            source="development_marker",
            development_marker=True
        )
    
    def witness_observation(self, observation: str) -> Mem0Entry:
        """Store witness-level observation (from StrangeLoopMemory)."""
        return self.remember(
            observation,
            layer="witness",
            source="strange_loop_observer"
        )
    
    def get_context_for_agent(self, max_chars: int = 2000) -> str:
        """
        Get formatted context for agent prompt (backward compatible).
        
        Prioritizes core identity, then recent development markers,
        then witness observations.
        """
        parts = ["## Memory Context"]
        
        # Core identity (always include)
        if self._core_identity_cache:
            parts.append("\n### Core Identity")
            for e in self._core_identity_cache[:3]:
                parts.append(f"- {e.content[:120]}")
        
        # Development markers
        dev = self.recall(layer="episodic", limit=5, development_only=True)
        if dev:
            parts.append("\n### Development")
            for e in dev[:3]:
                parts.append(f"- [{e.timestamp[:10]}] {e.content[:100]}")
        
        # Recent semantic knowledge
        sem = self.recall(layer="semantic", limit=3)
        if sem:
            parts.append("\n### Knowledge")
            for e in sem:
                parts.append(f"- {e.content[:100]}")
        
        return "\n".join(parts)[:max_chars]
    
    # ─────────────────────────────────────────────────────────────
    # Core Identity Management
    # ─────────────────────────────────────────────────────────────
    
    def set_core_identity(self, key: str, value: str) -> Mem0Entry:
        """
        Set or update a core identity belief.
        
        Core identity entries are special - they define who the agent IS.
        Use sparingly and intentionally.
        
        Example:
            memory.set_core_identity("telos", "Moksha through witness consciousness")
        """
        content = f"[{key.upper()}] {value}"
        
        # Check if this key already exists
        for entry in self._core_identity_cache:
            if entry.content.startswith(f"[{key.upper()}]"):
                # Update existing
                entry.content = content
                entry.timestamp = datetime.utcnow().isoformat() + "Z"
                self._persist(entry)
                return entry
        
        # Create new
        return self.add(content, layer="core_identity", skip_dedup=True)
    
    def get_core_identity(self, key: Optional[str] = None) -> List[Mem0Entry]:
        """Get core identity entries, optionally filtered by key."""
        if key:
            return [e for e in self._core_identity_cache 
                    if e.content.startswith(f"[{key.upper()}]")]
        return list(self._core_identity_cache)
    
    # ─────────────────────────────────────────────────────────────
    # Persistence Layer
    # ─────────────────────────────────────────────────────────────
    
    def _persist(self, entry: Mem0Entry):
        """Persist entry to appropriate layer file."""
        layer_path = self.base / entry.layer
        date_str = entry.timestamp[:10]
        file_path = layer_path / f"{date_str}.jsonl"
        
        with open(file_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    
    def _load_layer(self, layer: MemoryLayer, limit: int = 50) -> List[Mem0Entry]:
        """Load entries from a layer's storage."""
        layer_path = self.base / layer.value
        entries = []
        
        # Read recent files
        files = sorted(layer_path.glob("*.jsonl"), reverse=True)[:7]
        
        for file in files:
            try:
                for line in open(file):
                    try:
                        data = json.loads(line.strip())
                        entries.append(Mem0Entry(**data))
                    except:
                        pass
            except:
                pass
        
        return entries[:limit]
    
    # ─────────────────────────────────────────────────────────────
    # Analytics & Maintenance
    # ─────────────────────────────────────────────────────────────
    
    def stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "working": len(self.working),
            "core_identity": len(self._core_identity_cache),
            "episodic": len(self._load_layer(MemoryLayer.EPISODIC, 1000)),
            "semantic": len(self._load_layer(MemoryLayer.SEMANTIC, 1000)),
            "using_real_mem0": self._using_real_mem0,
            "embeddings_available": EMBEDDINGS_AVAILABLE,
            "dedup_threshold": self.deduplicator.threshold
        }
    
    def consolidate(self, days_old: int = 7) -> Dict:
        """
        Consolidate old episodic memories into semantic generalizations.
        
        This is a maintenance operation that:
        1. Finds episodic entries older than days_old
        2. Groups similar ones
        3. Creates semantic generalizations
        4. Archives the originals
        
        Returns stats about consolidation.
        """
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        episodic = self._load_layer(MemoryLayer.EPISODIC, 500)
        
        old_entries = [e for e in episodic 
                       if datetime.fromisoformat(e.timestamp.rstrip('Z')) < cutoff]
        
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
                sim = self.deduplicator.text_similarity(entry.content, other.content)
                if sim > 0.6:
                    group.append(other)
                    used.add(other.id)
            
            if len(group) > 1:
                groups.append(group)
        
        # Create generalizations
        consolidated = 0
        for group in groups:
            # Simple generalization: take the longest/most detailed
            best = max(group, key=lambda e: len(e.content))
            self.add(
                f"[Consolidated from {len(group)} episodes] {best.content}",
                layer="semantic"
            )
            consolidated += 1
        
        return {
            "old_entries": len(old_entries),
            "groups_found": len(groups),
            "consolidated": consolidated
        }


# ─────────────────────────────────────────────────────────────────
# Factory function for easy initialization
# ─────────────────────────────────────────────────────────────────

def create_memory(user_id: str = "dharmic_claw",
                  base_path: str = "~/DHARMIC_GODEL_CLAW/memory",
                  use_mem0: bool = True) -> Mem0Memory:
    """
    Factory function to create a properly configured Mem0Memory.
    
    Args:
        user_id: Agent/user identifier
        base_path: Storage directory
        use_mem0: Whether to use real mem0 (if available)
    
    Returns:
        Configured Mem0Memory instance
    """
    config = None
    if use_mem0 and MEM0_AVAILABLE:
        # Configure for local vector store if no external service
        config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": f"dharmic_{user_id}",
                    "path": str(Path(base_path).expanduser() / "chroma")
                }
            }
        }
    
    return Mem0Memory(
        base_path=base_path,
        user_id=user_id,
        mem0_config=config
    )


# ─────────────────────────────────────────────────────────────────
# Test / Demo
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Mem0Memory Test")
    print("=" * 60)
    
    # Create instance
    memory = Mem0Memory()
    
    print(f"\nInitialized with:")
    print(f"  - mem0 available: {MEM0_AVAILABLE}")
    print(f"  - embeddings available: {EMBEDDINGS_AVAILABLE}")
    print(f"  - using real mem0: {memory._using_real_mem0}")
    
    # Test core identity
    print("\n--- Core Identity ---")
    memory.set_core_identity("telos", "Moksha through witness consciousness")
    memory.set_core_identity("method", "Depth over breadth, genuine development")
    print(f"Core entries: {len(memory.get_core_identity())}")
    
    # Test layer detection
    print("\n--- Layer Detection ---")
    tests = [
        "I believe in non-harm above efficiency",  # core_identity
        "Today the user expressed frustration",    # episodic
        "User generally prefers CLI interfaces",   # semantic
    ]
    for t in tests:
        layer = memory._detect_layer(t)
        print(f"  '{t[:40]}...' → {layer.value}")
    
    # Test deduplication
    print("\n--- Deduplication ---")
    memory.add("User prefers dark mode", layer="semantic")
    result = memory.add("User prefers dark mode themes", layer="semantic")  # Similar
    print(f"  Second add (similar) returned: {result}")
    
    # Test backward compatibility
    print("\n--- Backward Compatibility ---")
    memory.remember("Test session entry", layer="sessions")
    memory.mark_development("Discovered surface mode operation", "12 pages vs 50 required")
    memory.witness_observation("The uncertainty may BE the recognition")
    
    # Get context
    print("\n--- Agent Context ---")
    print(memory.get_context_for_agent(max_chars=500))
    
    # Stats
    print("\n--- Stats ---")
    print(json.dumps(memory.stats(), indent=2))
