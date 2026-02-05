#!/usr/bin/env python3
"""
Unified Memory Indexer — PSMV + Conversations + Code
Builds SQLite database with vector embeddings for unified search.
"""

import os
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np

# Configuration
HOME = Path.home()
PSMV_PATH = HOME / "Persistent-Semantic-Memory-Vault"
CONVERSATIONS_PATH = HOME / "clawd" / "memory"
CODE_PATH = HOME / "DHARMIC_GODEL_CLAW"
DB_PATH = HOME / "DHARMIC_GODEL_CLAW" / "data" / "unified_memory.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class UnifiedMemoryIndexer:
    """Indexes PSMV files, conversations, and code into unified SQLite database."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.init_db()
        
    def init_db(self):
        """Initialize SQLite database with schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Files table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,  -- 'psmv', 'conversation', 'code'
                content_hash TEXT NOT NULL,
                file_type TEXT,
                size_bytes INTEGER,
                modified_time REAL,
                indexed_time REAL DEFAULT (unixepoch()),
                content TEXT,
                metadata TEXT  -- JSON
            )
        """)
        
        # Embeddings table (for future vector integration)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                embedding_model TEXT,
                embedding BLOB,  -- numpy array as bytes
                chunk_index INTEGER DEFAULT 0,
                chunk_text TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # Full-text search virtual table
        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(
                content,
                path,
                source,
                content='files',
                content_rowid='id'
            )
        """)
        
        # Triggers to keep FTS index in sync
        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                INSERT INTO search(rowid, content, path, source) 
                VALUES (new.id, new.content, new.path, new.source);
            END
        """)
        
        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                INSERT INTO search(search, rowid, content, path, source) 
                VALUES ('delete', old.id, old.content, old.path, old.source);
            END
        """)
        
        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                INSERT INTO search(search, rowid, content, path, source) 
                VALUES ('delete', old.id, old.content, old.path, old.source);
                INSERT INTO search(rowid, content, path, source) 
                VALUES (new.id, new.content, new.path, new.source);
            END
        """)
        
        # Stats table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                last_full_index TEXT,
                total_files INTEGER DEFAULT 0,
                total_embeddings INTEGER DEFAULT 0,
                psmv_files INTEGER DEFAULT 0,
                conversation_files INTEGER DEFAULT 0,
                code_files INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_source ON files(source)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_file ON embeddings(file_id)")
        
        self.conn.commit()
        print(f"✅ Database initialized: {self.db_path}")
        
    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]
        
    def index_file(self, file_path: Path, source: str, content: str) -> bool:
        """Index a single file."""
        try:
            content_hash = self.compute_hash(content)
            stat = file_path.stat()
            
            # Check if file already indexed with same hash
            self.cursor.execute(
                "SELECT id FROM files WHERE path = ? AND content_hash = ?",
                (str(file_path), content_hash)
            )
            if self.cursor.fetchone():
                return False  # Already up to date
                
            # Insert or replace
            self.cursor.execute("""
                INSERT OR REPLACE INTO files 
                (path, source, content_hash, file_type, size_bytes, modified_time, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(file_path),
                source,
                content_hash,
                file_path.suffix.lower(),
                len(content.encode('utf-8')),
                stat.st_mtime,
                content[:100000]  # Limit content size for now
            ))
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error indexing {file_path}: {e}")
            return False
            
    def index_psmv(self) -> int:
        """Index all files in PSMV vault."""
        print("\n📚 Indexing PSMV vault...")
        count = 0
        
        if not PSMV_PATH.exists():
            print(f"⚠️  PSMV path not found: {PSMV_PATH}")
            return 0
            
        # Index markdown and text files
        for ext in ['*.md', '*.txt', '*.yaml', '*.yml', '*.json']:
            for file_path in PSMV_PATH.rglob(ext):
                try:
                    content = file_path.read_text(errors='ignore')
                    if self.index_file(file_path, 'psmv', content):
                        count += 1
                        if count % 100 == 0:
                            print(f"  Indexed {count} files...")
                except Exception as e:
                    continue
                    
        self.conn.commit()
        print(f"✅ Indexed {count} PSMV files")
        return count
        
    def index_conversations(self) -> int:
        """Index conversation files."""
        print("\n💬 Indexing conversations...")
        count = 0
        
        if not CONVERSATIONS_PATH.exists():
            print(f"⚠️  Conversations path not found: {CONVERSATIONS_PATH}")
            return 0
            
        for file_path in CONVERSATIONS_PATH.glob('*.md'):
            try:
                content = file_path.read_text(errors='ignore')
                if self.index_file(file_path, 'conversation', content):
                    count += 1
            except Exception as e:
                continue
                
        self.conn.commit()
        print(f"✅ Indexed {count} conversation files")
        return count
        
    def index_code(self) -> int:
        """Index code files."""
        print("\n💻 Indexing code...")
        count = 0
        
        if not CODE_PATH.exists():
            print(f"⚠️  Code path not found: {CODE_PATH}")
            return 0
            
        # Index Python, JavaScript, and config files
        code_extensions = ['*.py', '*.js', '*.ts', '*.yaml', '*.yml', '*.json', '*.md']
        exclude_patterns = ['__pycache__', '.git', 'node_modules', '.venv', 'cloned_source']
        
        for ext in code_extensions:
            for file_path in CODE_PATH.rglob(ext):
                # Skip excluded directories
                if any(pat in str(file_path) for pat in exclude_patterns):
                    continue
                    
                try:
                    content = file_path.read_text(errors='ignore')
                    if len(content) < 500000:  # Skip very large files
                        if self.index_file(file_path, 'code', content):
                            count += 1
                            if count % 100 == 0:
                                print(f"  Indexed {count} files...")
                except Exception as e:
                    continue
                    
        self.conn.commit()
        print(f"✅ Indexed {count} code files")
        return count
        
    def search(self, query: str, source: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search indexed files."""
        if source:
            self.cursor.execute("""
                SELECT f.* FROM files f
                JOIN search s ON f.id = s.rowid
                WHERE search MATCH ? AND f.source = ?
                ORDER BY rank
                LIMIT ?
            """, (query, source, limit))
        else:
            self.cursor.execute("""
                SELECT f.* FROM files f
                JOIN search s ON f.id = s.rowid
                WHERE search MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'path': row['path'],
                'source': row['source'],
                'file_type': row['file_type'],
                'size_bytes': row['size_bytes'],
                'modified_time': row['modified_time']
            })
        return results
        
    def get_stats(self) -> Dict:
        """Get indexing statistics."""
        self.cursor.execute("SELECT COUNT(*) FROM files WHERE source = 'psmv'")
        psmv_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM files WHERE source = 'conversation'")
        conv_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM files WHERE source = 'code'")
        code_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM files")
        total = self.cursor.fetchone()[0]
        
        return {
            'total_files': total,
            'psmv_files': psmv_count,
            'conversation_files': conv_count,
            'code_files': code_count,
            'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
        
    def full_index(self):
        """Run full indexing of all sources."""
        print("=" * 60)
        print("🔍 UNIFIED MEMORY INDEXER — Full Index Run")
        print("=" * 60)
        
        start_time = datetime.now()
        
        psmv_count = self.index_psmv()
        conv_count = self.index_conversations()
        code_count = self.index_code()
        
        # Update stats
        self.cursor.execute("""
            INSERT OR REPLACE INTO stats 
            (id, last_full_index, total_files, psmv_files, conversation_files, code_files)
            VALUES (1, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            psmv_count + conv_count + code_count,
            psmv_count,
            conv_count,
            code_count
        ))
        self.conn.commit()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("✅ INDEXING COMPLETE")
        print("=" * 60)
        print(f"📊 Total files indexed: {stats['total_files']}")
        print(f"   - PSMV: {stats['psmv_files']}")
        print(f"   - Conversations: {stats['conversation_files']}")
        print(f"   - Code: {stats['code_files']}")
        print(f"💾 Database size: {stats['database_size_mb']:.2f} MB")
        print(f"⏱️  Elapsed time: {elapsed:.1f}s")
        print("=" * 60)
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            

def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Memory Indexer")
    parser.add_argument("--index", action="store_true", help="Run full indexing")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--source", choices=['psmv', 'conversation', 'code'], help="Filter by source")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    indexer = UnifiedMemoryIndexer()
    
    try:
        if args.index:
            indexer.full_index()
        elif args.search:
            results = indexer.search(args.search, args.source)
            print(f"\n🔍 Search results for: '{args.search}'")
            print("=" * 60)
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['source']}] {r['path']}")
        elif args.stats:
            stats = indexer.get_stats()
            print("\n📊 Unified Memory Statistics")
            print("=" * 60)
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            parser.print_help()
    finally:
        indexer.close()


if __name__ == "__main__":
    main()