"""
Mem0 Layer — Vector embeddings for semantic memory search.
"""

import json
import numpy as np
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Any


@dataclass
class SearchResult:
    """Semantic search result."""
    memory_id: str
    similarity: float



# Singleton embedder instance (cached in memory)
_embedder_instance = None

def get_embedder(model_name="all-MiniLM-L6-v2"):
    """Get or create singleton embedder."""
    global _embedder_instance
    if _embedder_instance is None:
        from sentence_transformers import SentenceTransformer
        _embedder_instance = SentenceTransformer(model_name)
        print(f"[INIT] Embedder loaded: {model_name}")
    return _embedder_instance

class EmbeddingModel(ABC):
    """Abstract embedding model interface."""
    
    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class MiniLMEmbedder(EmbeddingModel):
    """Local MiniLM embeddings — default, no API calls."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = get_embedder(model_name)
        self._model_name = model_name
    
    def embed(self, text: str) -> np.ndarray:
        return self.model.encode(text, normalize_embeddings=True)
    
    @property
    def dimensions(self) -> int:
        return 384
    
    @property
    def name(self) -> str:
        return self._model_name


class OpenAIEmbedder(EmbeddingModel):
    """OpenAI API embeddings — higher quality, requires key."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai required. Install: pip install openai")
        self.model = model
    
    def embed(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(
            model=self.model,
            input=text[:8000]  # Token limit safety
        )
        return np.array(response.data[0].embedding)
    
    @property
    def dimensions(self) -> int:
        return 1536 if "small" in self.model else 3072
    
    @property
    def name(self) -> str:
        return f"openai-{self.model}"


VEC_SCHEMA = """
-- Vector embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    memory_id TEXT UNIQUE NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model_name TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Virtual table for vector search (using sqlite-vec if available, else fallback)
CREATE TABLE IF NOT EXISTS vec_index (
    embedding_id TEXT PRIMARY KEY REFERENCES embeddings(id),
    memory_id TEXT UNIQUE NOT NULL
);
"""


class Mem0Layer:
    """
    Vector memory layer with semantic search.
    Uses numpy for similarity if sqlite-vec not available.
    """
    
    def __init__(
        self,
        db_path: str = "~/.unified_memory/memory.db",
        embedding_model: Optional[EmbeddingModel] = None
    ):
        self.db_path = Path(db_path).expanduser()
        self.embedder = embedding_model or MiniLMEmbedder()
        self._vectors: dict = {}  # In-memory cache
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(VEC_SCHEMA)
            conn.commit()
    
    def embed_memory(self, memory_id: str, content: str, context: str = "", tags: List[str] = None) -> str:
        """Generate and store embedding for a memory."""
        # Rich embedding text
        parts = [content, context or ""]
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")
        embedding_text = " | ".join(filter(None, parts))
        
        # Generate embedding
        vector = self.embedder.embed(embedding_text)
        
        # Create ID
        embedding_id = f"emb_{memory_id[:16]}"
        
        # Store
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO embeddings 
                (id, memory_id, vector, model_name, dimensions)
                VALUES (?, ?, ?, ?, ?)
            """, (
                embedding_id, memory_id, vector.tobytes(),
                self.embedder.name, self.embedder.dimensions
            ))
            conn.execute("""
                INSERT OR REPLACE INTO vec_index (embedding_id, memory_id)
                VALUES (?, ?)
            """, (embedding_id, memory_id))
            conn.commit()
        
        # Cache
        self._vectors[memory_id] = vector
        
        return embedding_id
    
    def search_similar(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.6,
        exclude_ids: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Semantic similarity search using cosine similarity."""
        query_vector = self.embedder.embed(query)
        exclude_set = set(exclude_ids or [])
        
        # Load all vectors (for small-medium datasets)
        # For large scale, use sqlite-vec or faiss
        vectors = self._load_vectors()
        
        # Compute similarities
        results = []
        for memory_id, vector in vectors.items():
            if memory_id in exclude_set:
                continue
            similarity = self._cosine_similarity(query_vector, vector)
            if similarity >= threshold:
                results.append(SearchResult(memory_id, similarity))
        
        # Sort by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:top_k]
    
    def get_context_memories(
        self,
        current_context: str,
        recent_memory_ids: List[str],
        max_results: int = 5
    ) -> List[str]:
        """Retrieve memories relevant to current context."""
        # Build rich query from context + recent memories
        query_parts = [current_context]
        
        # Load recent memory contents
        with sqlite3.connect(self.db_path) as conn:
            for mem_id in recent_memory_ids[-3:]:  # Last 3
                row = conn.execute(
                    "SELECT content FROM memories WHERE id = ?", (mem_id,)
                ).fetchone()
                if row:
                    query_parts.append(row[0])
        
        combined_query = " | ".join(query_parts)
        results = self.search_similar(combined_query, top_k=max_results, threshold=0.5)
        
        return [r.memory_id for r in results]
    
    def _load_vectors(self) -> dict:
        """Load all vectors from DB into memory."""
        if self._vectors:
            return self._vectors
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT memory_id, vector, dimensions FROM embeddings
            """).fetchall()
            
            for memory_id, vector_bytes, dims in rows:
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                if len(vector) != dims:
                    vector = vector[:dims]  # Safety
                self._vectors[memory_id] = vector
        
        return self._vectors
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def get_stats(self) -> dict:
        """Get embedding statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
            by_model = conn.execute("""
                SELECT model_name, COUNT(*) FROM embeddings GROUP BY model_name
            """).fetchall()
            
            return {
                "total_embeddings": total,
                "by_model": dict(by_model),
                "dimensions": self.embedder.dimensions,
                "cached_in_memory": len(self._vectors),
            }


if __name__ == "__main__":
    # Test
    layer = Mem0Layer("/tmp/test_vec.db")
    eid = layer.embed_memory("test-1", "AI consciousness research", "R_V metrics", ["consciousness"])
    print(f"Embedded: {eid}")
    results = layer.search_similar("consciousness measurement")
    print(f"Found: {len(results)} matches")
