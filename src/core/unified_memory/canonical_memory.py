"""
Canonical Memory Layer — Normalized, structured memory storage.
"""

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class MemoryType(Enum):
    LEARNING = "learning"
    DECISION = "decision"
    INSIGHT = "insight"
    EVENT = "event"
    INTERACTION = "interaction"
    META = "meta"


class MemorySource(Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    EXTERNAL = "external"
    INFERRED = "inferred"


@dataclass
class EntityGraph:
    people: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EntityGraph":
        return cls(**data)


@dataclass
class CanonicalMemory:
    content: str
    memory_type: MemoryType
    importance: int = 5
    agent_id: str = "default"
    context: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    entities: Optional[EntityGraph] = None
    source: MemorySource = MemorySource.AGENT
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    embedding_id: Optional[str] = None
    loop_refs: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    content_hash: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.entities is None:
            self.entities = EntityGraph()
        if self.content_hash is None:
            self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        normalized = f"{self.memory_type.value}:{self.agent_id}:{self.content.lower().strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    def normalize_tags(self) -> List[str]:
        normalized = []
        for tag in self.tags:
            clean = ''.join(c.lower() for c in tag if c.isalnum() or c == '-')
            if clean:
                normalized.append(clean)
        return list(set(normalized))
    
    def to_db_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "memory_type": self.memory_type.value,
            "importance": self.importance,
            "agent_id": self.agent_id,
            "content": self.content,
            "content_hash": self.content_hash,
            "context": self.context,
            "source": self.source.value,
            "embedding_id": self.embedding_id,
            "loop_refs": json.dumps(self.loop_refs),
            "entities": json.dumps(self.entities.to_dict()) if self.entities else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> "CanonicalMemory":
        return cls(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else None,
            memory_type=MemoryType(row["memory_type"]),
            importance=row["importance"],
            agent_id=row["agent_id"],
            content=row["content"],
            content_hash=row["content_hash"],
            context=row["context"],
            source=MemorySource(row["source"]),
            embedding_id=row["embedding_id"],
            loop_refs=json.loads(row["loop_refs"]) if row["loop_refs"] else [],
            entities=EntityGraph.from_dict(json.loads(row["entities"])) if row["entities"] else EntityGraph(),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            access_count=row["access_count"],
            last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
        )


SCHEMA_SQL = """
-- Core memories table
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    memory_type TEXT NOT NULL,
    importance INTEGER NOT NULL CHECK(importance BETWEEN 1 AND 10),
    agent_id TEXT NOT NULL DEFAULT 'default',
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    context TEXT,
    source TEXT NOT NULL,
    embedding_id TEXT,
    loop_refs TEXT DEFAULT '[]',
    entities TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed DATETIME,
    FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE SET NULL
);

-- Full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    context,
    content_rowid=id,
    tokenize='porter'
);

-- Tags
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    usage_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS memory_tags (
    memory_id TEXT REFERENCES memories(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, tag_id)
);

-- Access logging
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT REFERENCES memories(id),
    access_type TEXT NOT NULL,
    query_context TEXT,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_memories_hash ON memories(content_hash);
CREATE INDEX IF NOT EXISTS idx_access_log_memory ON access_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_access_log_time ON access_log(accessed_at);
"""


class CanonicalStore:
    """SQLite-backed canonical memory storage."""
    
    def __init__(self, db_path: str = "~/.unified_memory/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
    
    def capture(self, memory: CanonicalMemory) -> str:
        """Store memory. Returns memory ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM memories WHERE content_hash = ?",
                (memory.content_hash,)
            )
            if cursor.fetchone():
                raise ValueError(f"Duplicate memory: similar content exists")
            
            data = memory.to_db_dict()
            conn.execute("""
                INSERT INTO memories 
                (id, timestamp, memory_type, importance, agent_id, content, content_hash,
                 context, source, embedding_id, loop_refs, entities, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["timestamp"], data["memory_type"], data["importance"],
                data["agent_id"], data["content"], data["content_hash"], data["context"],
                data["source"], data["embedding_id"], data["loop_refs"], data["entities"],
                data["created_at"], data["updated_at"]
            ))
            
            for tag in memory.normalize_tags():
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                conn.execute("""
                    INSERT INTO memory_tags (memory_id, tag_id)
                    SELECT ?, id FROM tags WHERE name = ?
                """, (memory.id, tag))
                conn.execute("UPDATE tags SET usage_count = usage_count + 1 WHERE name = ?", (tag,))
            
            # Get the rowid for FTS
            row = conn.execute("SELECT rowid FROM memories WHERE id = ?", (memory.id,)).fetchone()
            if row:
                conn.execute("""
                    INSERT INTO memories_fts (rowid, content, context)
                    VALUES (?, ?, ?)
                """, (row[0], memory.content, memory.context or ""))
            
            conn.commit()
        
        return memory.id
    
    def get_by_id(self, memory_id: str) -> Optional[CanonicalMemory]:
        """Retrieve memory by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            return CanonicalMemory.from_db_row(row) if row else None
    
    def search_text(
        self,
        query: str,
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        min_importance: int = 1,
        limit: int = 20
    ) -> List[CanonicalMemory]:
        """Full-text search using FTS5."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            sql = """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                AND m.importance >= ?
            """
            params = [query, min_importance]
            
            if agent_id:
                sql += " AND m.agent_id = ?"
                params.append(agent_id)
            
            if memory_type:
                sql += " AND m.memory_type = ?"
                params.append(memory_type.value)
            
            sql += " ORDER BY m.importance DESC, rank LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            return [CanonicalMemory.from_db_row(row) for row in rows]
    
    def update_access(self, memory_id: str):
        """Update access count and timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memories 
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), memory_id))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            by_type = conn.execute("""
                SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type
            """).fetchall()
            by_agent = conn.execute("""
                SELECT agent_id, COUNT(*) FROM memories GROUP BY agent_id
            """).fetchall()
            
            return {
                "total_memories": total,
                "by_type": dict(by_type),
                "by_agent": dict(by_agent),
            }
