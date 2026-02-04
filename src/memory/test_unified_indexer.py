#!/usr/bin/env python3
"""
Test suite for Unified Memory Indexer.

Run: python test_unified_indexer.py
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.unified_indexer import (
    UnifiedMemoryIndexer, 
    IndexerConfig, 
    MemoryChunk,
    EMBEDDINGS_AVAILABLE
)


class TestUnifiedMemoryIndexer(unittest.TestCase):
    """Test cases for the unified memory indexer."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_memory.db")
        self.config = IndexerConfig(db_path=self.db_path)
        self.indexer = UnifiedMemoryIndexer(self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.indexer.close()
        shutil.rmtree(self.test_dir)
    
    def test_database_initialization(self):
        """Test that database initializes correctly."""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check tables exist
        conn = self.indexer._get_connection()
        tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('chunks', 'cross_refs', 'file_sync_state')
        """).fetchall()
        self.assertEqual(len(tables), 3)
    
    def test_text_chunking(self):
        """Test paragraph-aware text chunking."""
        text = """
Paragraph one. This is the first paragraph with some content.

Paragraph two. This is the second paragraph with different content.
It has multiple lines.

Paragraph three. Final paragraph here.
""".strip()
        
        chunks = self.indexer._chunk_text(text, chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(len(c) > 0 for c in chunks))
    
    def test_file_hashing(self):
        """Test file hash computation."""
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content for hashing")
        
        hash1 = self.indexer._compute_file_hash(test_file)
        hash2 = self.indexer._compute_file_hash(test_file)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex
    
    def test_content_hashing(self):
        """Test content hash computation."""
        content = "Test content"
        hash1 = self.indexer._compute_content_hash(content)
        hash2 = self.indexer._compute_content_hash(content)
        
        self.assertEqual(hash1, hash2)
    
    def test_file_ingestion(self):
        """Test ingesting a single file."""
        test_file = os.path.join(self.test_dir, "test_note.md")
        content = """---
title: Test Note
date: 2026-02-05
---

# Test Note

This is a test note for the unified memory indexer.

## Section 2

More content here.
"""
        with open(test_file, 'w') as f:
            f.write(content)
        
        chunks = self.indexer._ingest_file(test_file, 'test_source')
        self.assertGreater(chunks, 0)
        
        # Verify in database
        conn = self.indexer._get_connection()
        row = conn.execute(
            "SELECT * FROM chunks WHERE file_path = ?", (test_file,)
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['title'], 'Test Note')
        self.assertEqual(row['source_type'], 'test_source')
    
    def test_incremental_sync(self):
        """Test that unchanged files are skipped."""
        test_file = os.path.join(self.test_dir, "incremental.md")
        with open(test_file, 'w') as f:
            f.write("Test content for incremental sync")
        
        # First sync
        chunks1 = self.indexer._ingest_file(test_file, 'test')
        
        # Second sync (should skip)
        chunks2 = self.indexer._ingest_file(test_file, 'test')
        
        # Should return cached count, not re-index
        self.assertEqual(chunks1, chunks2)
    
    def test_fts_search(self):
        """Test full-text search."""
        test_file = os.path.join(self.test_dir, "searchable.md")
        with open(test_file, 'w') as f:
            f.write("This document contains unique keyword XYZ123 for testing search")
        
        self.indexer._ingest_file(test_file, 'test')
        
        results = self.indexer._fts_search("XYZ123", limit=10)
        self.assertGreater(len(results), 0)
        self.assertIn("XYZ123", results[0]['content'])
    
    def test_stats(self):
        """Test statistics retrieval."""
        # Add some test data
        test_file = os.path.join(self.test_dir, "stats_test.md")
        with open(test_file, 'w') as f:
            f.write("Test content for statistics")
        
        self.indexer._ingest_file(test_file, 'test')
        
        stats = self.indexer.get_stats()
        self.assertIn('overall', stats)
        self.assertIn('sources', stats)
        self.assertGreaterEqual(stats['overall']['total_chunks'], 1)
    
    def test_cross_references(self):
        """Test cross-reference creation."""
        # Create two similar files
        file1 = os.path.join(self.test_dir, "file1.md")
        file2 = os.path.join(self.test_dir, "file2.md")
        
        content = "This is about consciousness recognition and self-awareness."
        
        with open(file1, 'w') as f:
            f.write(content)
        with open(file2, 'w') as f:
            f.write(content)  # Same content = high similarity
        
        self.indexer._ingest_file(file1, 'test')
        self.indexer._ingest_file(file2, 'test')
        
        if EMBEDDINGS_AVAILABLE:
            refs = self.indexer.build_cross_references(['test'])
            # Should detect similarity
            self.assertIsInstance(refs, int)


class TestIndexerConfig(unittest.TestCase):
    """Test configuration handling."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = IndexerConfig()
        self.assertEqual(config.embedding_model, "all-MiniLM-L6-v2")
        self.assertEqual(config.embedding_dim, 384)
        self.assertEqual(config.chunk_size, 512)
    
    def test_path_expansion(self):
        """Test that paths are expanded."""
        config = IndexerConfig(db_path="~/test.db")
        self.assertTrue(config.db_path.startswith('/'))
        self.assertFalse('~' in config.db_path)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestIndexerConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestUnifiedMemoryIndexer))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
