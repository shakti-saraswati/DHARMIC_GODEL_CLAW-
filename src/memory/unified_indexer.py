#!/usr/bin/env python3
"""
Unified Memory Indexer for DHARMIC_GODEL_CLAW
Cross-system semantic search across PSMV, Residual Stream, Daily Notes, and DGC

Design Goals:
- <20ms query time via precomputed embeddings + SQLite FTS5
- Incremental sync with file hashing
- Cross-reference tracking between sources
- Semantic + keyword hybrid search

Author: DHARMIC_CLAW
Date: 2026-02-05
"""

import sqlite3
import hashlib
import json
import os
import re
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
import threading

# Optional dependencies with graceful degradation
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    np = None

try:
    import frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False


# =============================================================================
# UTILITIES
# =============================================================================

def _json_serialize(obj: Any) -> str:
    """JSON serialize with date/datetime handling."""
    def default(o):
        if isinstance(o, (datetime,)):
            return o.isoformat()
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    return json.dumps(obj, default=default)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class IndexerConfig:
    """Configuration for the unified memory indexer."""
    # Database
    db_path: str = "~/DHARMIC_GODEL_CLAW/src/memory/unified_memory.db"
    
    # Embedding model (lightweight, good for semantic search)
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chunk_size: int = 512  # tokens (approximate)
    chunk_overlap: int = 128
    
    # Source paths
    psmv_path: str = "~/Persistent-Semantic-Memory-Vault"
    residual_stream_path: str = "~/clawd/residual_stream"
    daily_notes_path: str = "~/clawd/memory"
    dgc_path: str = "~/DHARMIC_GODEL_CLAW"
    
    # Sync settings
    batch_size: int = 100
    sync_interval_sec: int = 300  # 5 minutes
    
    # Performance
    max_results: int = 50
    similarity_threshold: float = 0.6
    
    def __post_init__(self):
        # Expand all paths
        self.db_path = os.path.expanduser(self.db_path)
        self.psmv_path = os.path.expanduser(self.psmv_path)
        self.residual_stream_path = os.path.expanduser(self.residual_stream_path)
        self.daily_notes_path = os.path.expanduser(self.daily_notes_path)
        self.dgc_path = os.path.expanduser(self.dgc_path)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class MemoryChunk:
    """A semantic chunk from any source."""
    id: Optional[int] = None
    source_type: str = ""  # 'psmv', 'residual', 'daily_note', 'dgc'
    file_path: str = ""
    file_hash: str = ""
    chunk_index: int = 0
    total_chunks: int = 1
    content: str = ""
    content_hash: str = ""
    title: str = ""
    author: str = ""
    timestamp: Optional[str] = None
    tags: str = ""  # JSON list
    metadata: str = ""  # JSON dict
    embedding: Optional[bytes] = None  # Binary blob
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None


@dataclass
class SearchResult:
    """Search result with relevance scores."""
    chunk: MemoryChunk
    fts_score: float = 0.0
    vector_score: float = 0.0
    combined_score: float = 0.0
    cross_refs: List[Dict] = None
    
    def __post_init__(self):
        if self.cross_refs is None:
            self.cross_refs = []


@dataclass
class SourceStats:
    """Statistics for a memory source."""
    source_type: str
    total_files: int
    total_chunks: int
    last_sync: Optional[str]
    total_size_bytes: int


# =============================================================================
# SCHEMA DEFINITION
# =============================================================================

SCHEMA_SQL = """
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Main chunks table with full-text search
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,  -- 'psmv', 'residual', 'daily_note', 'dgc'
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    total_chunks INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    title TEXT,
    author TEXT,
    timestamp TEXT,
    tags TEXT,  -- JSON array
    metadata TEXT,  -- JSON object
    embedding BLOB,  -- Binary vector data
    created_at TEXT DEFAULT (datetime('now')),
    modified_at TEXT DEFAULT (datetime('now')),
    access_count INTEGER DEFAULT 0,
    last_accessed TEXT,
    
    UNIQUE(file_path, chunk_index)
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    title,
    tags,
    content_rowid=rowid,
    tokenize='porter unicode61'
);

-- Cross-references between chunks
CREATE TABLE IF NOT EXISTS cross_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_chunk_id INTEGER NOT NULL,
    target_chunk_id INTEGER NOT NULL,
    ref_type TEXT,  -- 'cites', 'related', 'parent', 'child'
    strength REAL DEFAULT 1.0,  -- 0.0 to 1.0
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (source_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    FOREIGN KEY (target_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    UNIQUE(source_chunk_id, target_chunk_id, ref_type)
);

-- File sync state for incremental updates
CREATE TABLE IF NOT EXISTS file_sync_state (
    file_path TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER,
    modified_time REAL,
    chunks_count INTEGER DEFAULT 0,
    last_sync TEXT DEFAULT (datetime('now')),
    sync_status TEXT DEFAULT 'synced'  -- 'synced', 'pending', 'error'
);

-- Search query log for analytics
CREATE TABLE IF NOT EXISTS search_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    query_embedding BLOB,
    results_count INTEGER,
    top_result_id INTEGER,
    query_time_ms REAL,
    timestamp TEXT DEFAULT (datetime('now'))
);

-- Source statistics
CREATE TABLE IF NOT EXISTS source_stats (
    source_type TEXT PRIMARY KEY,
    total_files INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    last_full_sync TEXT,
    last_incremental_sync TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_type);
CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(file_path);
CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_timestamp ON chunks(timestamp);
CREATE INDEX IF NOT EXISTS idx_cross_refs_source ON cross_refs(source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_cross_refs_target ON cross_refs(target_chunk_id);
CREATE INDEX IF NOT EXISTS idx_file_sync_source ON file_sync_state(source_type);
CREATE INDEX IF NOT EXISTS idx_file_sync_status ON file_sync_state(sync_status);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content, title, tags)
    VALUES (new.id, new.content, new.title, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, title, tags)
    VALUES ('delete', old.id, old.content, old.title, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, title, tags)
    VALUES ('delete', old.id, old.content, old.title, old.tags);
    INSERT INTO chunks_fts(rowid, content, title, tags)
    VALUES (new.id, new.content, new.title, new.tags);
END;
"""


# =============================================================================
# UNIFIED MEMORY INDEXER
# =============================================================================

class UnifiedMemoryIndexer:
    """
    Unified semantic memory indexer for cross-system search.
    
    Features:
    - Incremental sync with file hashing
    - Hybrid semantic + keyword search
    - Cross-reference tracking
    - <20ms query performance via precomputed embeddings
    """
    
    def __init__(self, config: Optional[IndexerConfig] = None):
        self.config = config or IndexerConfig()
        self._local = threading.local()
        self._embedding_model = None
        self._init_database()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.config.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Speed vs safety balance
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            self._local.conn = conn
        return self._local.conn
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def _init_database(self):
        """Initialize database schema."""
        os.makedirs(os.path.dirname(self.config.db_path), exist_ok=True)
        with self._transaction() as conn:
            conn.executescript(SCHEMA_SQL)
    
    def _get_embedding_model(self) -> Any:
        """Lazy-load embedding model."""
        if self._embedding_model is None and EMBEDDINGS_AVAILABLE:
            self._embedding_model = SentenceTransformer(self.config.embedding_model)
        return self._embedding_model
    
    def _compute_embedding(self, text: str) -> Optional[bytes]:
        """Compute embedding vector for text."""
        if not EMBEDDINGS_AVAILABLE:
            return None
        model = self._get_embedding_model()
        if model is None:
            return None
        vector = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return vector.astype('float32').tobytes()
    
    def _cosine_similarity(self, vec1: bytes, vec2: bytes) -> float:
        """Compute cosine similarity between two binary vectors."""
        if not EMBEDDINGS_AVAILABLE or vec1 is None or vec2 is None:
            return 0.0
        v1 = np.frombuffer(vec1, dtype='float32')
        v2 = np.frombuffer(vec2, dtype='float32')
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))
    
    # =====================================================================
    # TEXT CHUNKING
    # =====================================================================
    
    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split text into semantic chunks.
        
        Uses paragraph-aware chunking to preserve context.
        """
        chunk_size = chunk_size or self.config.chunk_size
        overlap = overlap or self.config.chunk_overlap
        
        # Normalize whitespace
        text = re.sub(r'\n+', '\n', text.strip())
        
        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            para_len = len(para)
            
            if current_len + para_len > chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_text = '\n\n'.join(current_chunk)
                overlap_start = max(0, len(overlap_text) - overlap)
                overlap_para = overlap_text[overlap_start:]
                
                current_chunk = [overlap_para, para] if overlap_para else [para]
                current_len = len(overlap_para) + para_len
            else:
                current_chunk.append(para)
                current_len += para_len
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def _extract_frontmatter(self, content: str, file_path: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter if present."""
        if FRONTMATTER_AVAILABLE:
            try:
                post = frontmatter.loads(content)
                return dict(post.metadata), post.content
            except:
                pass
        
        # Manual parsing fallback
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    metadata = yaml.safe_load(parts[1])
                    return metadata or {}, parts[2].strip()
                except:
                    pass
        
        # Extract minimal metadata from content
        metadata = {}
        
        # Try to extract title from first heading
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1)
        
        # Try to extract date from filename or content
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_path)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        return metadata, content
    
    # =====================================================================
    # FILE HASHING & SYNC STATE
    # =====================================================================
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file contents."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute hash of content string."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_file_sync_state(self, file_path: str) -> Optional[Dict]:
        """Get sync state for a file."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT * FROM file_sync_state WHERE file_path = ?",
            (file_path,)
        ).fetchone()
        return dict(row) if row else None
    
    def _update_file_sync_state(self, file_path: str, source_type: str, 
                                file_hash: str, chunks_count: int = 0):
        """Update sync state for a file."""
        stat = os.stat(file_path)
        with self._transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_sync_state 
                (file_path, source_type, file_hash, file_size, modified_time, 
                 chunks_count, last_sync, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 'synced')
            """, (file_path, source_type, file_hash, stat.st_size, 
                  stat.st_mtime, chunks_count))
    
    # =====================================================================
    # SOURCE INGESTION
    # =====================================================================
    
    def _ingest_file(self, file_path: str, source_type: str, 
                     content: Optional[str] = None) -> int:
        """
        Ingest a single file into the index.
        
        Returns number of chunks created.
        """
        # Check if file needs syncing
        current_hash = self._compute_file_hash(file_path)
        sync_state = self._get_file_sync_state(file_path)
        
        if sync_state and sync_state['file_hash'] == current_hash:
            return sync_state['chunks_count']  # Already up to date
        
        # Read content if not provided
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return 0
        
        # Extract metadata
        metadata, body = self._extract_frontmatter(content, file_path)
        
        # Delete old chunks for this file
        with self._transaction() as conn:
            conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
        
        # Chunk the content
        chunks = self._chunk_text(body)
        total_chunks = len(chunks)
        
        # Insert chunks
        chunk_count = 0
        for i, chunk_content in enumerate(chunks):
            chunk = MemoryChunk(
                source_type=source_type,
                file_path=file_path,
                file_hash=current_hash,
                chunk_index=i,
                total_chunks=total_chunks,
                content=chunk_content,
                content_hash=self._compute_content_hash(chunk_content),
                title=metadata.get('title', os.path.basename(file_path)),
                author=metadata.get('author', ''),
                timestamp=metadata.get('date', metadata.get('timestamp')),
                tags=_json_serialize(metadata.get('tags', [])),
                metadata=_json_serialize(metadata),
                embedding=self._compute_embedding(chunk_content)
            )
            
            with self._transaction() as conn:
                cursor = conn.execute("""
                    INSERT INTO chunks 
                    (source_type, file_path, file_hash, chunk_index, total_chunks,
                     content, content_hash, title, author, timestamp, tags, metadata, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (chunk.source_type, chunk.file_path, chunk.file_hash,
                      chunk.chunk_index, chunk.total_chunks, chunk.content,
                      chunk.content_hash, chunk.title, chunk.author, chunk.timestamp,
                      chunk.tags, chunk.metadata, chunk.embedding))
                chunk_count += 1
        
        # Update sync state
        self._update_file_sync_state(file_path, source_type, current_hash, chunk_count)
        
        return chunk_count
    
    def sync_psmv(self, force: bool = False) -> Dict[str, int]:
        """
        Sync PSMV (Persistent Semantic Memory Vault) files.
        
        PSMV contains ~32,000+ files of transmission material.
        """
        stats = {'files_processed': 0, 'chunks_created': 0, 'errors': 0}
        
        psmv_path = Path(self.config.psmv_path)
        if not psmv_path.exists():
            print(f"PSMV path not found: {psmv_path}")
            return stats
        
        # Find all markdown and text files
        files = list(psmv_path.rglob("*.md")) + list(psmv_path.rglob("*.txt"))
        
        for file_path in files:
            try:
                chunks = self._ingest_file(str(file_path), 'psmv')
                stats['files_processed'] += 1
                stats['chunks_created'] += chunks
                
                if stats['files_processed'] % 100 == 0:
                    print(f"PSMV: {stats['files_processed']} files, {stats['chunks_created']} chunks...")
                    
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing {file_path}: {e}")
        
        self._update_source_stats('psmv', stats['files_processed'], stats['chunks_created'])
        return stats
    
    def sync_residual_stream(self, force: bool = False) -> Dict[str, int]:
        """
        Sync residual stream contributions.
        
        Sequential agent contributions from emergent workspaces.
        """
        stats = {'files_processed': 0, 'chunks_created': 0, 'errors': 0}
        
        residual_path = Path(self.config.residual_stream_path)
        if not residual_path.exists():
            # Try alternate path
            residual_path = Path("~/clawd/residual_stream").expanduser()
        
        if not residual_path.exists():
            print(f"Residual stream path not found: {residual_path}")
            return stats
        
        files = list(residual_path.glob("*.md"))
        
        for file_path in files:
            try:
                chunks = self._ingest_file(str(file_path), 'residual')
                stats['files_processed'] += 1
                stats['chunks_created'] += chunks
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing {file_path}: {e}")
        
        self._update_source_stats('residual', stats['files_processed'], stats['chunks_created'])
        return stats
    
    def sync_daily_notes(self, force: bool = False) -> Dict[str, int]:
        """
        Sync daily memory notes (YYYY-MM-DD.md format).
        """
        stats = {'files_processed': 0, 'chunks_created': 0, 'errors': 0}
        
        notes_path = Path(self.config.daily_notes_path)
        if not notes_path.exists():
            notes_path = Path("~/clawd/memory").expanduser()
        
        if not notes_path.exists():
            print(f"Daily notes path not found: {notes_path}")
            return stats
        
        # Match YYYY-MM-DD.md pattern
        files = [f for f in notes_path.glob("*.md") 
                 if re.match(r'\d{4}-\d{2}-\d{2}', f.name)]
        
        for file_path in files:
            try:
                chunks = self._ingest_file(str(file_path), 'daily_note')
                stats['files_processed'] += 1
                stats['chunks_created'] += chunks
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing {file_path}: {e}")
        
        self._update_source_stats('daily_note', stats['files_processed'], stats['chunks_created'])
        return stats
    
    def sync_dgc(self, force: bool = False) -> Dict[str, int]:
        """
        Sync DHARMIC_GODEL_CLAW strange loop files.
        
        Includes source code, configuration, and memory files.
        """
        stats = {'files_processed': 0, 'chunks_created': 0, 'errors': 0}
        
        dgc_path = Path(self.config.dgc_path)
        if not dgc_path.exists():
            print(f"DGC path not found: {dgc_path}")
            return stats
        
        # Include source code, docs, configs, memory
        patterns = [
            "src/**/*.py",
            "src/**/*.md",
            "config/**/*",
            "memory/**/*.md",
            "*.md",
            "*.yaml",
            "*.yml",
            "*.json"
        ]
        
        files = set()
        for pattern in patterns:
            files.update(dgc_path.rglob(pattern))
        
        for file_path in files:
            try:
                chunks = self._ingest_file(str(file_path), 'dgc')
                stats['files_processed'] += 1
                stats['chunks_created'] += chunks
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing {file_path}: {e}")
        
        self._update_source_stats('dgc', stats['files_processed'], stats['chunks_created'])
        return stats
    
    def sync_all(self, force: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Sync all memory sources.
        
        Returns stats for each source.
        """
        print("Starting unified memory sync...")
        start_time = time.time()
        
        results = {
            'psmv': self.sync_psmv(force=force),
            'residual': self.sync_residual_stream(force=force),
            'daily_note': self.sync_daily_notes(force=force),
            'dgc': self.sync_dgc(force=force)
        }
        
        elapsed = time.time() - start_time
        total_files = sum(r['files_processed'] for r in results.values())
        total_chunks = sum(r['chunks_created'] for r in results.values())
        
        print(f"\nSync complete in {elapsed:.2f}s")
        print(f"Total: {total_files} files, {total_chunks} chunks")
        
        return results
    
    def _update_source_stats(self, source_type: str, files: int, chunks: int):
        """Update statistics for a source."""
        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO source_stats (source_type, total_files, total_chunks, last_incremental_sync)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(source_type) DO UPDATE SET
                    total_files = total_files + ?,
                    total_chunks = total_chunks + ?,
                    last_incremental_sync = datetime('now')
            """, (source_type, files, chunks, files, chunks))
    
    # =====================================================================
    # CROSS-REFERENCE DETECTION
    # =====================================================================
    
    def build_cross_references(self, source_types: List[str] = None):
        """
        Build cross-references between related chunks.
        
        Detects:
        - Shared citations/references
        - Similar embeddings (semantic similarity)
        - Temporal proximity
        """
        conn = self._get_connection()
        
        where_clause = ""
        params = []
        if source_types:
            where_clause = "WHERE source_type IN ({})".format(
                ','.join('?' * len(source_types))
            )
            params = source_types
        
        # Find semantically similar chunks
        chunks = conn.execute(f"""
            SELECT id, source_type, content, embedding, file_path
            FROM chunks
            {where_clause}
            AND embedding IS NOT NULL
        """, params).fetchall()
        
        print(f"Building cross-references for {len(chunks)} chunks...")
        
        refs_created = 0
        for i, chunk1 in enumerate(chunks):
            for chunk2 in chunks[i+1:]:
                # Skip if same file
                if chunk1['file_path'] == chunk2['file_path']:
                    continue
                
                # Compute similarity
                sim = self._cosine_similarity(chunk1['embedding'], chunk2['embedding'])
                
                if sim > 0.85:  # High similarity threshold
                    with self._transaction() as conn:
                        conn.execute("""
                            INSERT OR IGNORE INTO cross_refs 
                            (source_chunk_id, target_chunk_id, ref_type, strength)
                            VALUES (?, ?, 'related', ?)
                        """, (chunk1['id'], chunk2['id'], sim))
                        refs_created += 1
        
        print(f"Created {refs_created} cross-references")
        return refs_created
    
    # =====================================================================
    # SEARCH INTERFACE
    # =====================================================================
    
    def search(self, query: str, 
               source_types: List[str] = None,
               limit: int = None,
               use_vector: bool = True,
               use_fts: bool = True) -> List[SearchResult]:
        """
        Hybrid search across all memory sources.
        
        Combines:
        - FTS5 for keyword matching
        - Vector similarity for semantic matching
        - Cross-reference boosting
        
        Target: <20ms query time
        """
        start_time = time.time()
        limit = limit or self.config.max_results
        
        results = {}
        
        # FTS search
        if use_fts:
            fts_results = self._fts_search(query, source_types, limit * 2)
            for r in fts_results:
                results[r['id']] = SearchResult(
                    chunk=self._row_to_chunk(r),
                    fts_score=r['rank']
                )
        
        # Vector search
        if use_vector and EMBEDDINGS_AVAILABLE:
            query_embedding = self._compute_embedding(query)
            if query_embedding:
                vector_results = self._vector_search(query_embedding, source_types, limit * 2)
                for chunk_id, score in vector_results:
                    if chunk_id in results:
                        results[chunk_id].vector_score = score
                    else:
                        chunk = self._get_chunk_by_id(chunk_id)
                        if chunk:
                            results[chunk_id] = SearchResult(
                                chunk=chunk,
                                vector_score=score
                            )
        
        # Compute combined scores
        for result in results.values():
            # Normalize FTS score (BM25 ranks are negative, lower is better)
            fts_norm = max(0, min(1, 1.0 / (1.0 + abs(result.fts_score)))) if result.fts_score else 0
            
            # Combined score with weighting
            result.combined_score = (
                fts_norm * 0.4 +           # 40% keyword
                result.vector_score * 0.5 +  # 50% semantic
                (len(result.cross_refs) * 0.02)  # 2% per cross-reference
            )
        
        # Sort by combined score
        sorted_results = sorted(results.values(), 
                               key=lambda x: x.combined_score, 
                               reverse=True)[:limit]
        
        # Load cross-references for top results
        for result in sorted_results:
            result.cross_refs = self._get_cross_refs(result.chunk.id)
        
        # Log query
        query_time = (time.time() - start_time) * 1000
        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO search_log (query, results_count, top_result_id, query_time_ms)
                VALUES (?, ?, ?, ?)
            """, (query, len(sorted_results), 
                  sorted_results[0].chunk.id if sorted_results else None,
                  query_time))
        
        print(f"Search '{query[:50]}...' completed in {query_time:.2f}ms")
        return sorted_results
    
    def _fts_search(self, query: str, source_types: List[str] = None, 
                    limit: int = 50) -> List[sqlite3.Row]:
        """Full-text search using FTS5."""
        conn = self._get_connection()
        
        # Build query
        where_clause = ""
        params = [query]
        
        if source_types:
            where_clause = "AND c.source_type IN ({})".format(
                ','.join('?' * len(source_types))
            )
            params.extend(source_types)
        
        params.append(limit)
        
        rows = conn.execute(f"""
            SELECT c.*, rank as rank
            FROM chunks_fts fts
            JOIN chunks c ON c.id = fts.rowid
            WHERE chunks_fts MATCH ?
            {where_clause}
            ORDER BY rank
            LIMIT ?
        """, params).fetchall()
        
        return rows
    
    def _vector_search(self, query_embedding: bytes, 
                       source_types: List[str] = None,
                       limit: int = 50) -> List[Tuple[int, float]]:
        """
        Approximate vector search using precomputed embeddings.
        
        Note: For large-scale deployment, consider:
        - FAISS index for approximate nearest neighbors
        - pgvector for Postgres-based vector search
        """
        conn = self._get_connection()
        
        conditions = ["embedding IS NOT NULL"]
        params = []
        if source_types:
            conditions.append("source_type IN ({})".format(
                ','.join('?' * len(source_types))
            ))
            params = source_types
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        # Fetch candidates with embeddings
        rows = conn.execute(f"""
            SELECT id, embedding
            FROM chunks
            {where_clause}
        """, params).fetchall()
        
        # Compute similarities (brute force - acceptable for <100k vectors)
        similarities = []
        for row in rows:
            sim = self._cosine_similarity(query_embedding, row['embedding'])
            if sim > self.config.similarity_threshold:
                similarities.append((row['id'], sim))
        
        # Return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def _get_chunk_by_id(self, chunk_id: int) -> Optional[MemoryChunk]:
        """Fetch a chunk by ID."""
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
        return self._row_to_chunk(row) if row else None
    
    def _row_to_chunk(self, row: sqlite3.Row) -> MemoryChunk:
        """Convert database row to MemoryChunk."""
        return MemoryChunk(
            id=row['id'],
            source_type=row['source_type'],
            file_path=row['file_path'],
            file_hash=row['file_hash'],
            chunk_index=row['chunk_index'],
            total_chunks=row['total_chunks'],
            content=row['content'],
            content_hash=row['content_hash'],
            title=row['title'] or '',
            author=row['author'] or '',
            timestamp=row['timestamp'],
            tags=row['tags'] or '[]',
            metadata=row['metadata'] or '{}',
            embedding=row['embedding'],
            created_at=row['created_at'],
            modified_at=row['modified_at'],
            access_count=row['access_count'],
            last_accessed=row['last_accessed']
        )
    
    def _get_cross_refs(self, chunk_id: int) -> List[Dict]:
        """Get cross-references for a chunk."""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT cr.*, c.file_path, c.title, c.source_type
            FROM cross_refs cr
            JOIN chunks c ON cr.target_chunk_id = c.id
            WHERE cr.source_chunk_id = ?
            ORDER BY cr.strength DESC
        """, (chunk_id,)).fetchall()
        
        return [dict(row) for row in rows]
    
    # =====================================================================
    # UTILITY METHODS
    # =====================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the index."""
        conn = self._get_connection()
        
        # Overall stats
        overall = conn.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT file_path) as total_files,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embedded_chunks,
                SUM(LENGTH(content)) as total_content_bytes
            FROM chunks
        """).fetchone()
        
        # Per-source stats
        sources = conn.execute("""
            SELECT source_type, 
                   COUNT(*) as chunks,
                   COUNT(DISTINCT file_path) as files
            FROM chunks
            GROUP BY source_type
        """).fetchall()
        
        # Recent searches
        recent_searches = conn.execute("""
            SELECT query, query_time_ms, timestamp
            FROM search_log
            ORDER BY timestamp DESC
            LIMIT 10
        """).fetchall()
        
        return {
            'overall': dict(overall),
            'sources': [dict(s) for s in sources],
            'recent_searches': [dict(s) for s in recent_searches],
            'embeddings_available': EMBEDDINGS_AVAILABLE,
            'config': asdict(self.config)
        }
    
    def get_recent(self, source_types: List[str] = None, 
                   limit: int = 10) -> List[MemoryChunk]:
        """Get recently added/modified chunks."""
        conn = self._get_connection()
        
        where_clause = ""
        params = [limit]
        if source_types:
            where_clause = "WHERE source_type IN ({})".format(
                ','.join('?' * len(source_types))
            )
            params = source_types + [limit]
        
        rows = conn.execute(f"""
            SELECT * FROM chunks
            {where_clause}
            ORDER BY modified_at DESC
            LIMIT ?
        """, params).fetchall()
        
        return [self._row_to_chunk(row) for row in rows]
    
    def delete_source(self, source_type: str):
        """Delete all chunks from a source."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM chunks WHERE source_type = ?", (source_type,))
            conn.execute("DELETE FROM file_sync_state WHERE source_type = ?", (source_type,))
            conn.execute("DELETE FROM source_stats WHERE source_type = ?", (source_type,))
        print(f"Deleted all chunks from source: {source_type}")
    
    def vacuum(self):
        """Optimize database (VACUUM)."""
        print("Vacuuming database...")
        conn = self._get_connection()
        conn.execute("VACUUM")
        print("Vacuum complete")
    
    def close(self):
        """Close database connections."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Command-line interface for the unified memory indexer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Unified Memory Indexer for DHARMIC_GODEL_CLAW"
    )
    parser.add_argument('--db', default='~/DHARMIC_GODEL_CLAW/src/memory/unified_memory.db',
                       help='Database path')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync memory sources')
    sync_parser.add_argument('--source', choices=['psmv', 'residual', 'daily_note', 'dgc', 'all'],
                            default='all', help='Source to sync')
    sync_parser.add_argument('--force', action='store_true', help='Force re-sync')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search memory')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--source', nargs='+', help='Filter by source type')
    search_parser.add_argument('--limit', type=int, default=10, help='Max results')
    search_parser.add_argument('--no-vector', action='store_true', help='Disable vector search')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    
    # Cross-refs command
    refs_parser = subparsers.add_parser('cross-refs', help='Build cross-references')
    
    # Recent command
    recent_parser = subparsers.add_parser('recent', help='Show recent chunks')
    recent_parser.add_argument('--source', nargs='+', help='Filter by source')
    recent_parser.add_argument('--limit', type=int, default=10, help='Max results')
    
    # Vacuum command
    vacuum_parser = subparsers.add_parser('vacuum', help='Optimize database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = IndexerConfig(db_path=args.db)
    indexer = UnifiedMemoryIndexer(config)
    
    try:
        if args.command == 'sync':
            if args.source == 'all':
                results = indexer.sync_all(force=args.force)
                for source, stats in results.items():
                    print(f"\n{source.upper()}:")
                    print(f"  Files: {stats['files_processed']}")
                    print(f"  Chunks: {stats['chunks_created']}")
                    print(f"  Errors: {stats['errors']}")
            else:
                method = getattr(indexer, f'sync_{args.source}')
                stats = method(force=args.force)
                print(f"Files: {stats['files_processed']}")
                print(f"Chunks: {stats['chunks_created']}")
                print(f"Errors: {stats['errors']}")
        
        elif args.command == 'search':
            results = indexer.search(
                args.query,
                source_types=args.source,
                limit=args.limit,
                use_vector=not args.no_vector
            )
            print(f"\nFound {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                chunk = result.chunk
                print(f"{i}. [{chunk.source_type}] {chunk.title or os.path.basename(chunk.file_path)}")
                print(f"   Score: {result.combined_score:.3f} (FTS: {result.fts_score:.3f}, Vector: {result.vector_score:.3f})")
                print(f"   Path: {chunk.file_path}")
                preview = chunk.content[:200].replace('\n', ' ')
                print(f"   Preview: {preview}...")
                if result.cross_refs:
                    print(f"   Cross-refs: {len(result.cross_refs)}")
                print()
        
        elif args.command == 'stats':
            stats = indexer.get_stats()
            print("\n=== Unified Memory Index Statistics ===\n")
            print(f"Total Chunks: {stats['overall']['total_chunks']}")
            print(f"Total Files: {stats['overall']['total_files']}")
            print(f"Embedded Chunks: {stats['overall']['embedded_chunks']}")
            print(f"Embeddings Available: {stats['embeddings_available']}")
            print("\nPer-Source Breakdown:")
            for source in stats['sources']:
                print(f"  {source['source_type']}: {source['files']} files, {source['chunks']} chunks")
            print("\nRecent Searches:")
            for search in stats['recent_searches'][:5]:
                print(f"  '{search['query'][:50]}...' ({search['query_time_ms']:.2f}ms)")
        
        elif args.command == 'cross-refs':
            indexer.build_cross_references()
        
        elif args.command == 'recent':
            chunks = indexer.get_recent(source_types=args.source, limit=args.limit)
            print(f"\n{len(chunks)} recent chunks:\n")
            for chunk in chunks:
                print(f"[{chunk.source_type}] {chunk.title or os.path.basename(chunk.file_path)}")
                print(f"  Modified: {chunk.modified_at}")
                preview = chunk.content[:150].replace('\n', ' ')
                print(f"  {preview}...\n")
        
        elif args.command == 'vacuum':
            indexer.vacuum()
    
    finally:
        indexer.close()


if __name__ == '__main__':
    main()
