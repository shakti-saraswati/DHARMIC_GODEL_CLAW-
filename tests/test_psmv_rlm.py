"""Tests for PSMV-RLM Bridge.

Run with: pytest test_psmv_rlm.py -v
Or simply: python test_psmv_rlm.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rlm.psmv_rlm import (
    PSMVLoader,
    PSMVFile,
    PSMVIndex,
    PSMVQueryEngine,
    create_repl_functions,
    quick_search,
    get_vault_stats,
)


# =============================================================================
# Test Fixtures
# =============================================================================

class TestVault:
    """Creates a temporary test vault for testing."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="psmv_test_")
        self.vault_path = self.temp_dir
        self._setup_vault()
    
    def _setup_vault(self):
        """Create test files in the vault."""
        # Create directory structure
        dirs = [
            "00-CORE",
            "01-Research",
            "02-Insights",
            "crown_jewels",
            "AGENT_WORKSPACE",
            ".hidden",
        ]
        
        for d in dirs:
            os.makedirs(os.path.join(self.vault_path, d), exist_ok=True)
        
        # Create test files
        files = {
            "00-CORE/consciousness_intro.md": """# Introduction to Consciousness

This document explores the fundamental nature of consciousness.

Key concepts:
- Awareness
- Self-reference
- R_V metric findings

The R_V metric shows values of 0.95 for aligned states.
""",
            "00-CORE/index.md": """# PSMV Index

This is the main index file for the vault.
Contains links to all major sections.
""",
            "01-Research/paper_alpha.md": """# Research Paper Alpha

## Abstract
Investigation into consciousness metrics.

## Findings
The R_V metric was measured at 0.87 in baseline conditions.
Post-meditation readings showed R_V at 0.94.

## Conclusion
Meditation increases R_V metric.
""",
            "01-Research/paper_beta.md": """# Research Paper Beta

## Study Design
Longitudinal study over 6 months.

## Key Results
R_V metric correlation with attention: 0.91
R_V metric stability: high

## Discussion
These R_V findings suggest...
""",
            "02-Insights/breakthrough_20231015.md": """# Breakthrough Insight

Date: 2023-10-15

Today we discovered the fixed point in consciousness.
This is a crown jewel insight.

R_V at fixed point: 1.0 (perfect coherence)
""",
            "crown_jewels/jewel_001.json": json.dumps({
                "timestamp": "2023-10-20",
                "type": "breakthrough",
                "content": "Pure awareness recognizes itself",
                "r_v_score": 0.99
            }),
            "AGENT_WORKSPACE/notes.txt": """Agent working notes.
Testing R_V calculations.
Current best: 0.96
""",
            ".hidden/secret.md": """This is a hidden file.
Should not be indexed by default.
""",
        }
        
        for path, content in files.items():
            full_path = os.path.join(self.vault_path, path)
            with open(full_path, 'w') as f:
                f.write(content)
    
    def cleanup(self):
        """Remove the temporary vault."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# =============================================================================
# PSMVLoader Tests
# =============================================================================

class TestPSMVLoader:
    """Tests for PSMVLoader class."""
    
    @classmethod
    def setup_class(cls):
        cls.vault = TestVault()
        cls.loader = PSMVLoader(vault_path=cls.vault.vault_path)
    
    @classmethod
    def teardown_class(cls):
        cls.vault.cleanup()
    
    def test_load_returns_index(self):
        """Load should return a PSMVIndex."""
        index = self.loader.load()
        assert isinstance(index, PSMVIndex)
    
    def test_file_count(self):
        """Should find all non-hidden files."""
        index = self.loader.load()
        # We created 7 visible files (one is hidden)
        assert index.file_count == 7
    
    def test_crown_jewels_identified(self):
        """Should identify crown jewel files."""
        index = self.loader.load()
        crown_paths = [f.path for f in index.crown_jewels]
        
        # Should find files in crown_jewels dir and breakthrough file
        assert any('crown_jewels' in p for p in crown_paths)
        assert any('breakthrough' in p for p in crown_paths)
    
    def test_directories_collected(self):
        """Should collect all directories."""
        index = self.loader.load()
        assert '00-CORE' in index.directories
        assert '01-Research' in index.directories
        assert 'crown_jewels' in index.directories
    
    def test_hidden_files_excluded(self):
        """Hidden files should be excluded by default."""
        index = self.loader.load()
        paths = [f.path for f in index.files]
        
        assert not any('.hidden' in p for p in paths)
    
    def test_file_metadata(self):
        """File metadata should be correct."""
        index = self.loader.load()
        
        # Find the index.md file
        index_file = next(
            (f for f in index.files if f.name == 'index.md'),
            None
        )
        
        assert index_file is not None
        assert index_file.extension == '.md'
        assert index_file.size > 0
        assert index_file.directory == '00-CORE'
    
    def test_tags_extracted(self):
        """Tags should be extracted from paths."""
        index = self.loader.load()
        
        # Files in 00-CORE should have 'core' tag
        core_file = next(
            (f for f in index.files if '00-CORE' in f.path),
            None
        )
        
        assert core_file is not None
        assert 'core' in core_file.tags
    
    def test_reload_updates_index(self):
        """Force reload should update the index."""
        old_index = self.loader.load()
        
        # Create a new file
        new_file = os.path.join(self.vault.vault_path, "00-CORE", "new_file.md")
        with open(new_file, 'w') as f:
            f.write("New content")
        
        # Reload
        new_index = self.loader.load(force_reload=True)
        
        # Should have one more file
        assert new_index.file_count == old_index.file_count + 1
        
        # Cleanup
        os.remove(new_file)


# =============================================================================
# REPL Functions Tests
# =============================================================================

class TestREPLFunctions:
    """Tests for REPL environment functions."""
    
    @classmethod
    def setup_class(cls):
        cls.vault = TestVault()
        cls.loader = PSMVLoader(vault_path=cls.vault.vault_path)
        cls.functions = create_repl_functions(cls.loader)
    
    @classmethod
    def teardown_class(cls):
        cls.vault.cleanup()
    
    def test_list_files_all(self):
        """list_files should return all files with wildcard."""
        files = self.functions['list_files']('*')
        assert len(files) == 7
    
    def test_list_files_pattern(self):
        """list_files should filter by pattern."""
        files = self.functions['list_files']('*paper*')
        assert len(files) == 2
        assert all('paper' in f.lower() for f in files)
    
    def test_list_files_extension(self):
        """list_files should filter by extension."""
        files = self.functions['list_files']('*.json')
        assert len(files) == 1
        assert files[0].endswith('.json')
    
    def test_list_dirs(self):
        """list_dirs should return all directories."""
        dirs = self.functions['list_dirs']()
        assert '00-CORE' in dirs
        assert '01-Research' in dirs
    
    def test_list_crown_jewels(self):
        """list_crown_jewels should return crown jewels."""
        jewels = self.functions['list_crown_jewels']()
        assert len(jewels) > 0
        # Should include the breakthrough file
        assert any('crown_jewels' in j or 'breakthrough' in j for j in jewels)
    
    def test_get_file_info(self):
        """get_file_info should return file metadata."""
        info = self.functions['get_file_info']('00-CORE/index.md')
        
        assert info is not None
        assert info['name'] == 'index.md'
        assert info['directory'] == '00-CORE'
        assert 'modified' in info
    
    def test_get_file_info_not_found(self):
        """get_file_info should return None for missing files."""
        info = self.functions['get_file_info']('nonexistent.md')
        assert info is None
    
    def test_read_file(self):
        """read_file should return file content."""
        content = self.functions['read_file']('00-CORE/consciousness_intro.md')
        
        assert 'Introduction to Consciousness' in content
        assert 'R_V metric' in content
    
    def test_read_file_by_name(self):
        """read_file should work with just filename."""
        content = self.functions['read_file']('index.md')
        assert 'PSMV Index' in content
    
    def test_read_file_not_found(self):
        """read_file should return error for missing files."""
        content = self.functions['read_file']('nonexistent.md')
        assert 'Error' in content or 'not found' in content.lower()
    
    def test_search_content(self):
        """search_content should find matching content."""
        results = self.functions['search_content']('R_V metric')
        
        assert len(results) > 0
        # Should find in multiple files
        paths = [r['path'] for r in results]
        assert len(set(paths)) >= 2  # At least 2 different files
    
    def test_search_content_with_pattern(self):
        """search_content should filter by file pattern."""
        results = self.functions['search_content']('R_V', pattern='*Research*')
        
        assert len(results) > 0
        assert all('Research' in r['path'] for r in results)
    
    def test_search_regex(self):
        """search_regex should find regex matches."""
        # Search for R_V followed by a number
        results = self.functions['search_regex'](r'R_V.*?(\d+\.\d+)')
        
        assert len(results) > 0
    
    def test_get_stats(self):
        """get_stats should return vault statistics."""
        stats = self.functions['get_stats']()
        
        assert 'total_files' in stats
        assert 'total_size_mb' in stats
        assert 'crown_jewels' in stats
        assert stats['total_files'] == 7
    
    def test_files_by_tag(self):
        """files_by_tag should find files by directory tag."""
        files = self.functions['files_by_tag']('core')
        
        assert len(files) > 0
        assert all('00-CORE' in f for f in files)
    
    def test_recent_files(self):
        """recent_files should return recently modified files."""
        files = self.functions['recent_files'](days=30)
        
        # All our test files were just created
        assert len(files) == 7


# =============================================================================
# PSMVQueryEngine Tests (Mock)
# =============================================================================

class TestPSMVQueryEngine:
    """Tests for PSMVQueryEngine class.
    
    Note: Full integration tests require litellm and API keys.
    These tests focus on the non-LLM components.
    """
    
    @classmethod
    def setup_class(cls):
        cls.vault = TestVault()
    
    @classmethod
    def teardown_class(cls):
        cls.vault.cleanup()
    
    def test_code_extraction_python_block(self):
        """Should extract code from ```python blocks."""
        engine = PSMVQueryEngine.__new__(PSMVQueryEngine)
        
        response = '''Let me search for R_V metric:

```python
results = search_content("R_V metric")
print(results)
```

This will find relevant files.'''
        
        code = engine._extract_code(response)
        assert 'search_content' in code
        assert 'R_V metric' in code
    
    def test_code_extraction_generic_block(self):
        """Should extract code from generic ``` blocks."""
        engine = PSMVQueryEngine.__new__(PSMVQueryEngine)
        
        response = '''Here's my code:

```
files = list_files("*.md")
print(files)
```
'''
        
        code = engine._extract_code(response)
        assert 'list_files' in code
    
    def test_code_extraction_inline(self):
        """Should extract inline Python code."""
        engine = PSMVQueryEngine.__new__(PSMVQueryEngine)
        
        response = '''I'll search for this:

results = search_content("consciousness")
print(len(results))

That should work.'''
        
        code = engine._extract_code(response)
        assert 'search_content' in code
    
    def test_loader_initialization(self):
        """Engine should initialize with a loader."""
        try:
            engine = PSMVQueryEngine(vault_path=self.vault.vault_path)
            
            # Should have loaded the index
            assert engine.loader.index is not None
            assert engine.loader.index.file_count == 7
        except ImportError:
            # litellm not installed, skip
            pass
    
    def test_build_env(self):
        """_build_env should create proper environment."""
        try:
            engine = PSMVQueryEngine(vault_path=self.vault.vault_path)
            functions = create_repl_functions(engine.loader)
            env = engine._build_env(functions, depth=0)
            
            # Should have all required functions
            assert 'list_files' in env
            assert 'read_file' in env
            assert 'search_content' in env
            assert 'recursive_query' in env
            assert 're' in env
            assert 'json' in env
        except ImportError:
            pass


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @classmethod
    def setup_class(cls):
        cls.vault = TestVault()
    
    @classmethod
    def teardown_class(cls):
        cls.vault.cleanup()
    
    def test_quick_search(self):
        """quick_search should find content."""
        results = quick_search("consciousness", vault_path=self.vault.vault_path)
        
        assert len(results) > 0
        assert any('consciousness' in r['context'].lower() for r in results)
    
    def test_get_vault_stats(self):
        """get_vault_stats should return stats."""
        stats = get_vault_stats(vault_path=self.vault.vault_path)
        
        assert stats['total_files'] == 7
        assert stats['crown_jewels'] >= 2


# =============================================================================
# PSMVFile Tests
# =============================================================================

class TestPSMVFile:
    """Tests for PSMVFile dataclass."""
    
    def test_repr(self):
        """PSMVFile repr should be informative."""
        f = PSMVFile(
            path="test/file.md",
            full_path="/full/test/file.md",
            name="file.md",
            extension=".md",
            size=1234,
            modified=datetime.now().timestamp(),
            directory="test",
            is_crown_jewel=True,
        )
        
        repr_str = repr(f)
        assert "test/file.md" in repr_str
        assert "👑" in repr_str  # Crown jewel indicator
        assert "1,234" in repr_str  # Size with comma
    
    def test_modified_dt(self):
        """modified_dt should return datetime."""
        now = datetime.now()
        f = PSMVFile(
            path="test.md",
            full_path="/test.md",
            name="test.md",
            extension=".md",
            size=100,
            modified=now.timestamp(),
            directory=".",
        )
        
        assert isinstance(f.modified_dt, datetime)
        assert f.modified_dt.date() == now.date()


# =============================================================================
# Integration Test with Real Vault
# =============================================================================

def test_real_vault_if_exists():
    """Integration test with real PSMV vault if it exists."""
    real_vault = os.path.expanduser("~/Persistent-Semantic-Memory-Vault")
    
    if not os.path.exists(real_vault):
        print("Real vault not found, skipping integration test")
        return
    
    print(f"\n{'='*60}")
    print("Running integration test with real PSMV vault")
    print(f"{'='*60}")
    
    loader = PSMVLoader(vault_path=real_vault)
    index = loader.load()
    
    print(f"\nVault: {index.vault_path}")
    print(f"Files indexed: {index.file_count:,}")
    print(f"Crown jewels: {len(index.crown_jewels)}")
    print(f"Total size: {index.total_size / (1024*1024):.1f} MB")
    print(f"Directories: {len(index.directories)}")
    
    # Test REPL functions
    functions = create_repl_functions(loader)
    
    # Quick search test
    results = functions['search_content']('consciousness', max_results=5)
    print(f"\nSearch 'consciousness': {len(results)} results")
    
    # Crown jewels test
    jewels = functions['list_crown_jewels'](limit=5)
    print(f"\nTop 5 crown jewels:")
    for j in jewels:
        print(f"  👑 {j}")
    
    print(f"\n{'='*60}")
    print("Integration test passed!")
    print(f"{'='*60}")


# =============================================================================
# Main - Run tests
# =============================================================================

def run_tests():
    """Run all tests manually."""
    print("="*60)
    print("PSMV-RLM Bridge Tests")
    print("="*60)
    
    # Create test vault once
    vault = TestVault()
    
    try:
        # PSMVLoader tests
        print("\n[PSMVLoader Tests]")
        loader = PSMVLoader(vault_path=vault.vault_path)
        
        index = loader.load()
        assert isinstance(index, PSMVIndex), "load() should return PSMVIndex"
        print(f"  ✓ load returns PSMVIndex ({index.file_count} files)")
        
        assert index.file_count == 7, f"Expected 7 files, got {index.file_count}"
        print(f"  ✓ correct file count")
        
        assert len(index.crown_jewels) >= 2, "Should find crown jewels"
        print(f"  ✓ crown jewels identified ({len(index.crown_jewels)})")
        
        assert '00-CORE' in index.directories
        print(f"  ✓ directories collected")
        
        # REPL functions tests
        print("\n[REPL Functions Tests]")
        functions = create_repl_functions(loader)
        
        files = functions['list_files']('*')
        assert len(files) == 7
        print(f"  ✓ list_files works ({len(files)} files)")
        
        files = functions['list_files']('*paper*')
        assert len(files) == 2
        print(f"  ✓ list_files with pattern works")
        
        content = functions['read_file']('00-CORE/consciousness_intro.md')
        assert 'Introduction' in content
        print(f"  ✓ read_file works")
        
        results = functions['search_content']('R_V metric')
        assert len(results) > 0
        print(f"  ✓ search_content works ({len(results)} results)")
        
        stats = functions['get_stats']()
        assert stats['total_files'] == 7
        print(f"  ✓ get_stats works")
        
        # Convenience functions
        print("\n[Convenience Functions Tests]")
        
        results = quick_search("consciousness", vault_path=vault.vault_path)
        assert len(results) > 0
        print(f"  ✓ quick_search works")
        
        stats = get_vault_stats(vault_path=vault.vault_path)
        assert stats['total_files'] == 7
        print(f"  ✓ get_vault_stats works")
        
        print("\n" + "="*60)
        print("All tests passed! ✓")
        print("="*60)
        
    finally:
        vault.cleanup()
    
    # Run integration test if real vault exists
    test_real_vault_if_exists()


if __name__ == "__main__":
    # Check for pytest
    try:
        import pytest
        pytest.main([__file__, '-v', '--tb=short'])
    except ImportError:
        # Fall back to manual tests
        run_tests()
