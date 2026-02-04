# Unified Memory Indexer

Cross-system semantic search for DHARMIC_GODEL_CLAW.

## Overview

The Unified Memory Indexer creates a searchable index across four memory sources:

1. **PSMV** (Persistent Semantic Memory Vault): ~32,000+ files of transmission material
2. **Residual Stream**: Sequential agent contributions from emergent workspaces  
3. **Daily Notes**: `memory/YYYY-MM-DD.md` session logs
4. **DGC** (DHARMIC_GODEL_CLAW): Source code, configs, and strange loop records

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED MEMORY INDEX                      │
├─────────────────────────────────────────────────────────────┤
│  SQLite + FTS5 + Binary Embeddings                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   chunks     │  │  chunks_fts  │  │  cross_refs      │  │
│  │   (main)     │  │  (search)    │  │  (relations)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Hybrid Search: 40% FTS + 50% Vector + 10% Cross-refs      │
│  Target: <20ms query time                                   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. First-Time Setup

```bash
cd ~/DHARMIC_GODEL_CLAW/src/memory

# Sync all sources (initial indexing - may take 10-30 minutes)
python unified_indexer.py sync --source all

# Build cross-references between related content
python unified_indexer.py cross-refs
```

### 2. Search

```bash
# Basic search
python unified_indexer.py search "consciousness recognition"

# Filter by source
python unified_indexer.py search "R_V metric" --source psmv dgc

# More results
python unified_indexer.py search "moksha" --limit 20
```

### 3. Python API

```python
from memory.unified_indexer import UnifiedMemoryIndexer, IndexerConfig

# Initialize with defaults
indexer = UnifiedMemoryIndexer()

# Or custom configuration
config = IndexerConfig(
    db_path="~/custom_memory.db",
    chunk_size=512,
    embedding_model="all-MiniLM-L6-v2"
)
indexer = UnifiedMemoryIndexer(config)

# Sync specific sources
indexer.sync_psmv()
indexer.sync_daily_notes()

# Search
results = indexer.search(
    query="recursive self-observation",
    source_types=['psmv', 'dgc'],
    limit=10
)

for result in results:
    print(f"Score: {result.combined_score:.3f}")
    print(f"Source: {result.chunk.source_type}")
    print(f"Content: {result.chunk.content[:200]}...")
    print()

# Get statistics
stats = indexer.get_stats()
print(f"Total chunks: {stats['overall']['total_chunks']}")
```

## Database Schema

### chunks
Main content table with metadata and embeddings.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| source_type | TEXT | psmv/residual/daily_note/dgc |
| file_path | TEXT | Full file path |
| content | TEXT | Chunk content |
| embedding | BLOB | Binary vector (384-dim) |
| title | TEXT | Extracted title |
| timestamp | TEXT | Document date |
| metadata | TEXT | JSON metadata |

### chunks_fts (Virtual)
FTS5 virtual table for full-text search.

### cross_refs
Semantic relationships between chunks.

| Column | Description |
|--------|-------------|
| source_chunk_id | Referrer |
| target_chunk_id | Target |
| ref_type | related/cites/parent/child |
| strength | Similarity score (0-1) |

### file_sync_state
Tracks file hashes for incremental sync.

## Performance

- **Query time**: <20ms for typical searches (with precomputed embeddings)
- **Indexing speed**: ~100-200 files/minute (with embeddings)
- **Database size**: ~1KB per chunk (with embeddings)
- **Memory usage**: Minimal (streaming processing)

## Configuration

Environment variables (optional):
```bash
export UNIFIED_MEMORY_DB="~/custom_memory.db"
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
export CHUNK_SIZE="512"
```

## Incremental Sync

The indexer tracks file hashes and only re-indexes changed files:

```python
# Automatic incremental sync
indexer.sync_all()  # Only processes new/changed files

# Force full re-sync
indexer.sync_all(force=True)
```

## Dependencies

Required:
- Python 3.8+
- SQLite 3.25+ (with FTS5 support)

Optional (for semantic search):
```bash
pip install sentence-transformers numpy
```

Without optional dependencies, falls back to keyword-only search.

## CLI Reference

```bash
# Sync commands
python unified_indexer.py sync --source all
python unified_indexer.py sync --source psmv
python unified_indexer.py sync --source daily_note --force

# Search
python unified_indexer.py search "query" [--source psmv] [--limit 10]

# Maintenance
python unified_indexer.py stats
python unified_indexer.py cross-refs
python unified_indexer.py vacuum
python unified_indexer.py recent [--limit 10]
```

## Design Decisions

1. **SQLite**: Single-file, zero-config, ACID compliance
2. **FTS5**: Built-in full-text search with ranking
3. **Binary embeddings**: Stored as BLOBs for portability
4. **Brute-force vector search**: Acceptable for <100k chunks
5. **Paragraph-aware chunking**: Preserves context boundaries
6. **File hashing**: SHA-256 for reliable change detection

## Future Enhancements

- [ ] FAISS integration for approximate nearest neighbors
- [ ] pgvector backend option for Postgres
- [ ] Real-time file watching (inotify/fsevents)
- [ ] Cross-reference visualization
- [ ] Query result caching
- [ ] Multi-modal support (image captions)
