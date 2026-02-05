"""Database schema for unified memory system."""

SCHEMA_SQL = """
-- Core memory table (Canonical Layer)
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    memory_type TEXT NOT NULL,
    importance INTEGER NOT NULL CHECK(importance BETWEEN 1 AND 10),
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    context TEXT,
    source TEXT NOT NULL,
    embedding_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed DATETIME,
    FOREIGN KEY (embedding_id) REFERENCES embeddings(id)
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    context,
    content='memories',
    content_rowid='rowid'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS memories_fts_insert AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, context) 
    VALUES (new.rowid, new.content, new.context);
END;

CREATE TRIGGER IF NOT EXISTS memories_fts_update AFTER UPDATE ON memories BEGIN
    UPDATE memories_fts SET 
        content = new.content,
        context = new.context
    WHERE rowid = new.rowid;
END;

CREATE TRIGGER IF NOT EXISTS memories_fts_delete AFTER DELETE ON memories BEGIN
    DELETE FROM memories_fts WHERE rowid = old.rowid;
END;

-- Tags (normalized)
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

-- Entities (people, projects, skills)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    normalized_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_entities (
    memory_id TEXT REFERENCES memories(id) ON DELETE CASCADE,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    role TEXT,
    PRIMARY KEY (memory_id, entity_id)
);

-- Strange Loop: Memory references (graph edges)
CREATE TABLE IF NOT EXISTS memory_references (
    source_id TEXT REFERENCES memories(id) ON DELETE CASCADE,
    target_id TEXT REFERENCES memories(id) ON DELETE CASCADE,
    reference_type TEXT NOT NULL,
    strength REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, target_id)
);

-- Mem0 Layer: Vector embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    memory_id TEXT UNIQUE REFERENCES memories(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model_version TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Memory decay and reinforcement tracking
CREATE TABLE IF NOT EXISTS memory_vitals (
    memory_id TEXT PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,
    base_importance INTEGER NOT NULL,
    current_importance REAL NOT NULL,
    decay_rate REAL DEFAULT 0.01,
    last_reinforced DATETIME,
    reinforcement_count INTEGER DEFAULT 0
);

-- Access patterns for optimization
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT REFERENCES memories(id),
    access_type TEXT NOT NULL,
    query_context TEXT,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Consolidation tracking
CREATE TABLE IF NOT EXISTS consolidation_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_type TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    memory_count INTEGER,
    insights_generated INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
CREATE INDEX IF NOT EXISTS idx_memories_hash ON memories(content_hash);
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories(embedding_id);

-- Strange Loop indexes
CREATE INDEX IF NOT EXISTS idx_refs_source ON memory_references(source_id);
CREATE INDEX IF NOT EXISTS idx_refs_target ON memory_references(target_id);
CREATE INDEX IF NOT EXISTS idx_refs_type ON memory_references(reference_type);

-- Access pattern indexes
CREATE INDEX IF NOT EXISTS idx_access_log_memory ON access_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_access_log_time ON access_log(accessed_at);
"""
