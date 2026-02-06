"""
Strange Loop Memory — Self-referential memory with emergent pattern detection.
Uses NetworkX for graph operations. Optional feature (can be disabled).
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: networkx not available. Strange Loop layer disabled.")


class ReferenceType(Enum):
    RELATED = "related"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    DERIVED_FROM = "derived_from"
    META = "meta"


@dataclass
class MemoryPath:
    """Path through memory graph."""
    nodes: List[str]
    total_strength: float
    path_type: str


@dataclass
class EmergentInsight:
    """New insight derived from memory patterns."""
    source_memories: List[str]
    insight_content: str
    confidence: float
    pattern_type: str


GRAPH_SCHEMA = """
-- Memory references (graph edges)
CREATE TABLE IF NOT EXISTS memory_references (
    source_id TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    reference_type TEXT NOT NULL,
    strength REAL DEFAULT 1.0 CHECK(strength BETWEEN 0.0 AND 1.0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, target_id)
);

-- Meta-memories tracking
CREATE TABLE IF NOT EXISTS meta_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_memory_id TEXT UNIQUE NOT NULL REFERENCES memories(id),
    source_memory_ids TEXT NOT NULL,  -- JSON list
    pattern_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_refs_source ON memory_references(source_id);
CREATE INDEX IF NOT EXISTS idx_refs_target ON memory_references(target_id);
CREATE INDEX IF NOT EXISTS idx_refs_type ON memory_references(reference_type);
"""


class StrangeLoopLayer:
    """
    Self-referential memory layer.
    Optional: Can be disabled if not needed.
    """
    
    def __init__(
        self,
        db_path: str = "~/.unified_memory/memory.db",
        enabled: bool = True,
        max_loop_depth: int = 5
    ):
        self.db_path = Path(db_path).expanduser()
        self.enabled = enabled and NETWORKX_AVAILABLE
        self.max_loop_depth = max_loop_depth
        self._graph: Optional[nx.DiGraph] = None
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(GRAPH_SCHEMA)
            conn.commit()
    
    def add_reference(
        self,
        source_id: str,
        target_id: str,
        ref_type: ReferenceType = ReferenceType.RELATED,
        strength: float = 1.0
    ):
        """Create a reference (edge) between two memories."""
        if not self.enabled:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memory_references
                (source_id, target_id, reference_type, strength, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (source_id, target_id, ref_type.value, strength, datetime.utcnow()))
            conn.commit()
        
        self._graph = None  # Invalidate cache
    
    def detect_loops(self, start_id: str) -> List[MemoryPath]:
        """
        Find cyclic paths (strange loops) starting from a memory.
        Limited depth for performance.
        """
        if not self.enabled:
            return []
        
        graph = self._load_graph()
        loops = []
        
        def dfs(current: str, path: List[str], strength: float, depth: int):
            if depth > self.max_loop_depth:
                return
            
            for neighbor in graph.successors(current):
                edge_strength = graph[current][neighbor].get("strength", 1.0)
                new_strength = strength * edge_strength
                
                if neighbor == start_id and len(path) > 1:
                    loops.append(MemoryPath(
                        nodes=path + [neighbor],
                        total_strength=new_strength,
                        path_type="loop"
                    ))
                elif neighbor not in path:
                    dfs(neighbor, path + [neighbor], new_strength, depth + 1)
        
        dfs(start_id, [start_id], 1.0, 0)
        loops.sort(key=lambda x: x.total_strength, reverse=True)
        return loops[:10]  # Top 10
    
    def find_clusters(self, min_size: int = 3) -> List[Set[str]]:
        """Find densely connected memory clusters."""
        if not self.enabled:
            return []
        
        graph = self._load_graph()
        if graph.number_of_nodes() < min_size:
            return []
        
        # Convert to undirected for community detection
        undirected = graph.to_undirected()
        
        try:
            communities = nx.community.greedy_modularity_communities(undirected)
            return [set(c) for c in communities if len(c) >= min_size]
        except:
            return []
    
    def find_contradictions(self) -> List[Tuple[List[str], float]]:
        """Find memory pairs that contradict each other."""
        if not self.enabled:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT source_id, target_id, strength
                FROM memory_references
                WHERE reference_type = 'contradicts'
            """).fetchall()
            
            return [([source, target], strength) for source, target, strength in rows]
    
    def propagate_importance(
        self,
        source_id: str,
        delta: int,
        decay: float = 0.5
    ):
        """Propagate importance changes through reference chain."""
        if not self.enabled:
            return
        
        graph = self._load_graph()
        visited = {source_id}
        
        def propagate(current: str, current_delta: float, depth: int):
            if depth >= 3 or abs(current_delta) < 0.5:
                return
            
            for neighbor in graph.successors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_delta = current_delta * decay
                    
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            UPDATE memories
                            SET importance = MAX(1, MIN(10, importance + ?))
                            WHERE id = ?
                        """, (int(new_delta), neighbor))
                        conn.commit()
                    
                    propagate(neighbor, new_delta, depth + 1)
        
        propagate(source_id, float(delta), 0)
    
    def get_related(self, memory_id: str, max_hops: int = 2) -> List[Tuple[str, float]]:
        """Get memories related within N hops."""
        if not self.enabled:
            return []
        
        graph = self._load_graph()
        related = []
        visited = {memory_id}
        current_level = {memory_id: 1.0}
        
        for hop in range(max_hops):
            next_level = {}
            for node, strength in current_level.items():
                for neighbor in graph.successors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        edge_strength = graph[node][neighbor].get("strength", 1.0)
                        new_strength = strength * edge_strength
                        next_level[neighbor] = new_strength
                        related.append((neighbor, new_strength))
            current_level = next_level
        
        related.sort(key=lambda x: x[1], reverse=True)
        return related
    
    def analyze_self(self) -> Dict[str, Any]:
        """Analyze the memory graph structure."""
        if not self.enabled:
            return {"enabled": False}
        
        graph = self._load_graph()
        
        with sqlite3.connect(self.db_path) as conn:
            total_memories = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            total_refs = conn.execute("SELECT COUNT(*) FROM memory_references").fetchone()[0]
        
        return {
            "enabled": True,
            "total_memories": total_memories,
            "total_references": total_refs,
            "reference_density": total_refs / max(total_memories, 1),
            "graph_nodes": graph.number_of_nodes(),
            "graph_edges": graph.number_of_edges(),
            "has_cycles": not nx.is_directed_acyclic_graph(graph) if graph.number_of_edges() > 0 else False,
            "connected_components": nx.number_weakly_connected_components(graph) if graph.number_of_nodes() > 0 else 0,
        }
    
    def _load_graph(self) -> nx.DiGraph:
        """Load memory graph from database."""
        if self._graph is not None:
            return self._graph
        
        graph = nx.DiGraph()
        
        with sqlite3.connect(self.db_path) as conn:
            # Add all memories as nodes
            rows = conn.execute("SELECT id FROM memories").fetchall()
            for (memory_id,) in rows:
                graph.add_node(memory_id)
            
            # Add references as edges
            rows = conn.execute("""
                SELECT source_id, target_id, reference_type, strength
                FROM memory_references
            """).fetchall()
            for source, target, ref_type, strength in rows:
                graph.add_edge(source, target, type=ref_type, strength=strength)
        
        self._graph = graph
        return graph


if __name__ == "__main__":
    if NETWORKX_AVAILABLE:
        layer = StrangeLoopLayer("/tmp/test_loop.db", enabled=True)
        print("Strange Loop layer initialized")
        stats = layer.analyze_self()
        print(f"Stats: {stats}")
    else:
        print("NetworkX not available")
