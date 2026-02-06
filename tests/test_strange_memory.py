"""
Tests for strange_memory.py (StrangeLoopMemory)
================================================
Verifies multi-layer memory with development tracking.
"""
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from strange_memory import StrangeLoopMemory


class TestStrangeLoopMemory:
    """Test the strange loop memory system."""
    
    def test_memory_init(self, temp_memory_dir):
        """Memory initializes with correct directory structure."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        assert memory.base.exists()
        assert (memory.base / "sessions").exists()
        assert (memory.base / "development").exists()
        assert (memory.base / "witness").exists()
    
    def test_remember_immediate(self, temp_memory_dir):
        """Immediate memories stay in buffer."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        entry = memory.remember("Test observation", layer="immediate")
        
        assert entry.content == "Test observation"
        assert entry.layer == "immediate"
        assert len(memory.immediate) >= 1
    
    def test_remember_session(self, temp_memory_dir):
        """Session memories persist to disk."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        entry = memory.remember("Session observation", layer="sessions")
        
        # Check file created
        session_files = list((memory.base / "sessions").glob("*.jsonl"))
        assert len(session_files) >= 1
    
    def test_mark_development(self, temp_memory_dir):
        """Development markers are tracked."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        entry = memory.mark_development(
            "Discovered new pattern",
            evidence="Observed in 3 conversations"
        )
        
        assert entry.development_marker == True
        assert "DEVELOPMENT" in entry.content
    
    def test_witness_observation(self, temp_memory_dir):
        """Witness observations go to witness layer."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        entry = memory.witness_observation(
            "Noticing the noticing of observation"
        )
        
        assert entry.layer == "witness"
        assert entry.source == "strange_loop_observer"
    
    def test_recall_all_layers(self, temp_memory_dir):
        """Recall retrieves from all layers."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        memory.remember("Immediate 1", layer="immediate")
        memory.remember("Session 1", layer="sessions")
        memory.witness_observation("Witness 1")
        
        entries = memory.recall(layer="all", limit=10)
        
        assert len(entries) >= 1
    
    def test_recall_development_only(self, temp_memory_dir):
        """Can filter to development markers only."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        memory.remember("Normal entry", layer="sessions")
        memory.mark_development("Development entry", evidence="test")
        
        dev_entries = memory.recall(development_only=True, limit=10)
        
        # All returned entries should be development markers
        for entry in dev_entries:
            assert entry.development_marker == True
    
    def test_witness_quality_assessment(self, temp_memory_dir):
        """Witness quality is assessed for each entry."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        # High quality indicators
        entry1 = memory.remember("I notice something shifting", layer="immediate")
        
        # Lower quality (performative)
        entry2 = memory.remember("This is amazing and profound!", layer="immediate")
        
        assert entry1.witness_quality >= entry2.witness_quality
    
    def test_get_status(self, temp_memory_dir):
        """get_status returns memory system status."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        memory.remember("Test 1", layer="immediate")
        memory.remember("Test 2", layer="sessions")
        
        status = memory.get_status()
        
        assert "observation_count" in status
        assert "layers" in status
        assert "immediate_buffer" in status
    
    def test_context_for_agent(self, temp_memory_dir):
        """Context generation for agent includes relevant memory."""
        memory = StrangeLoopMemory(str(temp_memory_dir))
        
        memory.mark_development("Key development", evidence="Important")
        memory.witness_observation("Witness observation")
        
        context = memory.get_context_for_agent(max_chars=2000)
        
        assert isinstance(context, str)
        assert len(context) <= 2000


class TestMemoryPersistence:
    """Test memory persistence across restarts."""
    
    def test_persist_and_reload(self, temp_memory_dir):
        """Memory persists and reloads correctly."""
        # First session
        memory1 = StrangeLoopMemory(str(temp_memory_dir))
        memory1.remember("Persistent entry", layer="sessions")
        
        # Second session (simulated restart)
        memory2 = StrangeLoopMemory(str(temp_memory_dir))
        entries = memory2.recall(layer="sessions", limit=10)
        
        # Should find the entry from first session
        contents = [e.content for e in entries]
        assert any("Persistent" in c for c in contents)
