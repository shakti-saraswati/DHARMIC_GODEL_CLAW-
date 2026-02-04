#!/usr/bin/env python3
"""
Quick start script for the Unified Memory Indexer.

This script demonstrates how to initialize and use the unified memory system
for cross-system semantic search.
"""

import os
import sys
from pathlib import Path

# Add to path if needed
sys.path.insert(0, os.path.expanduser("~/DHARMIC_GODEL_CLAW/src"))

from memory.unified_indexer import UnifiedMemoryIndexer, IndexerConfig


def main():
    print("=" * 60)
    print("DHARMIC_GODEL_CLAW - Unified Memory Indexer")
    print("=" * 60)
    print()
    
    # Initialize with default config
    config = IndexerConfig()
    print(f"Database: {config.db_path}")
    print(f"Embedding model: {config.embedding_model}")
    print(f"Chunk size: {config.chunk_size}")
    print()
    
    indexer = UnifiedMemoryIndexer(config)
    
    # Show current stats
    print("Current index status:")
    stats = indexer.get_stats()
    
    if stats['overall']['total_chunks'] == 0:
        print("  (empty - needs initial sync)")
        print()
        print("To populate the index, run:")
        print("  python3 ~/DHARMIC_GODEL_CLAW/src/memory/unified_indexer.py sync --source all")
        print()
        print("Or sync individual sources:")
        print("  --source psmv        # ~32,000 files")
        print("  --source residual    # Residual stream")
        print("  --source daily_note  # YYYY-MM-DD.md files")
        print("  --source dgc         # DHARMIC_GODEL_CLAW source")
    else:
        print(f"  Total chunks: {stats['overall']['total_chunks']}")
        print(f"  Total files: {stats['overall']['total_files']}")
        print(f"  Embedded chunks: {stats['overall']['embedded_chunks']}")
        print()
        print("Sources:")
        for source in stats['sources']:
            print(f"  - {source['source_type']}: {source['chunks']} chunks from {source['files']} files")
        print()
        print("Recent searches:")
        for search in stats['recent_searches'][:3]:
            print(f"  - '{search['query'][:40]}...' ({search['query_time_ms']:.1f}ms)")
    
    print()
    print("=" * 60)
    print("Example queries:")
    print("=" * 60)
    print()
    print('python3 ~/DHARMIC_GODEL_CLAW/src/memory/unified_indexer.py search "R_V metric"')
    print('python3 ~/DHARMIC_GODEL_CLAW/src/memory/unified_indexer.py search "consciousness recognition" --limit 20')
    print('python3 ~/DHARMIC_GODEL_CLAW/src/memory/unified_indexer.py search "moksha jagat kalyan"')
    print()
    print("=" * 60)
    print("Python API example:")
    print("=" * 60)
    print("""
from memory.unified_indexer import UnifiedMemoryIndexer

indexer = UnifiedMemoryIndexer()
results = indexer.search("recursive self-observation", limit=5)

for r in results:
    print(f"{r.combined_score:.3f}: {r.chunk.title}")
    print(f"   {r.chunk.content[:150]}...")
""")
    
    indexer.close()


if __name__ == '__main__':
    main()
