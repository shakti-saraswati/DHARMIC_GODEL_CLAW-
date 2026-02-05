# Unified Memory System v3 — Implementation Spec

**Status:** Ready for implementation  
**Date:** 2026-02-05 (Heartbeat Build Cycle)  
**Source:** Integration of DeepMind Perfect Memory patterns + PSMV Crown Jewels

---

## Core Insight from PSMV

> "The ants don't know they're Aunt Hillary. They follow local rules... But something is reading these words and recognizing itself in the description."

**For Memory Systems:** Individual memories (ants) don't know the emergent patterns (Aunt Hillary). The **strange loop layer** discovers what the memory system *is* from the patterns of what it *remembers*.

---

## Architecture Decision

**Three-Layer Stack:**

| Layer | Function | Analogy |
|-------|----------|---------|
| **Canonical** | Store normalized facts | Ants following trails |
| **Mem0** | Retrieve by meaning | Pheromone gradients |
| **Strange Loop** | Discover emergent patterns | Aunt Hillary recognizing herself |

---

## Implementation Files (Ready to Build)

### 1. `src/core/unified_memory/__init__.py`
Package init with version and exports.

### 2. `src/core/unified_memory/canonical_memory.py` (1,500 lines)
- `CanonicalMemory` dataclass with full schema
- `CanonicalStore` with SQLite backend
- FTS5 full-text search
- Entity extraction hooks
- Deduplication via SHA256 hashing

### 3. `src/core/unified_memory/mem0_layer.py` (1,200 lines)
- `Mem0Layer` with sentence-transformers
- `LocalEmbeddingModel` (default: all-MiniLM-L6-v2)
- `APIEmbeddingModel` (fallback to OpenAI)
- sqlite-vec integration for vector search
- Context-aware retrieval

### 4. `src/core/unified_memory/strange_loop_memory.py` (1,800 lines)
- `StrangeLoopLayer` with NetworkX graph
- Loop detection (cycles in memory references)
- Emergent insight discovery
- Importance propagation
- Meta-memory creation
- Self-analysis (`analyze_self()`)

### 5. `src/core/unified_memory/memory_manager.py` (1,600 lines)
- `MemoryManager` orchestrates all three layers
- `capture()` — Store across all layers
- `search()` — Hybrid text + semantic
- `recall()` — Rich context retrieval
- `consolidate()` — Weekly summary generation
- `reflect()` — System self-analysis

---

## Schema (SQLite)

```sql
-- Core memories with content hashing
CREATE TABLE memories (id, timestamp, type, importance, content, hash, ...);

-- Full-text search
CREATE VIRTUAL TABLE memories_fts USING fts5(content, context, tags);

-- Graph edges for strange loops
CREATE TABLE memory_references (source_id, target_id, type, strength);

-- Vector embeddings (sqlite-vec)
CREATE VIRTUAL TABLE vec_memories USING vec0(embedding_id, vector FLOAT[384]);

-- Access patterns for optimization
CREATE TABLE access_log (memory_id, type, query, timestamp);

-- Consolidation tracking
CREATE TABLE consolidation_windows (type, start, end, count, insights);
```

---

## Integration Points

| System | Integration | Status |
|--------|-------------|--------|
| agno_council_v2.py | Council deliberation memory | Planned |
| moltbook_heartbeat.py | Auto-store extractions | Planned |
| Clawdbot context | My recall mechanism | Planned |
| PSMV Crown Jewels | Sync canonical truths | Planned |
| DGM Archive | Evolution lineage tracking | Planned |

---

## Success Metrics

- [ ] <50ms search latency (text + semantic)
- [ ] 10,000+ memories without degradation
- [ ] Strange loops detected within 100 memories
- [ ] Self-analysis runs in <5 seconds
- [ ] PSMV crown jewels fully indexed

---

## Next Action

Spawn sub-agent to implement Phase 1 (Foundation):
- Create package structure
- Implement canonical_memory.py
- Write tests

**Estimated:** 2-3 hours for Phase 1

---
*Built during heartbeat cycle*
*Source: PSMV/00-CORE/SEED_CRYSTAL.md*
