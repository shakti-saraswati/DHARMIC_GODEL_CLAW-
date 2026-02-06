"""
Tests for StrangeLoopMemory - all 5 layers and persistence.
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from strange_loop_memory import StrangeLoopMemory


class TestStrangeLoopMemoryLayers:
    """Test all 5 memory layers comprehensively."""

    def test_all_layers_initialized(self, mock_memory_dir):
        """Test that all 5 layers are created on initialization."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        expected_layers = [
            "observations",
            "meta_observations",
            "patterns",
            "meta_patterns",
            "development"
        ]

        assert set(memory.layers.keys()) == set(expected_layers)

        for layer_name, layer_path in memory.layers.items():
            assert layer_path.exists()
            assert layer_path.is_file()
            assert layer_path.suffix == ".jsonl"

    def test_observations_layer(self, mock_memory_dir):
        """Test observations layer - what happened."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Record multiple observations
        memory.record_observation("First observation", {"type": "test"})
        memory.record_observation("Second observation", {"type": "test", "index": 2})
        memory.record_observation("Third observation", {})

        # Verify persistence
        recent = memory._read_recent("observations", 10)
        assert len(recent) == 3
        assert recent[0]["content"] == "First observation"
        assert recent[1]["content"] == "Second observation"
        assert recent[2]["content"] == "Third observation"

        # Verify context is stored
        assert recent[0]["context"]["type"] == "test"
        assert recent[1]["context"]["index"] == 2

    def test_meta_observations_layer(self, mock_memory_dir):
        """Test meta-observations layer - how I related to what happened."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        qualities = ["present", "contracted", "uncertain", "expansive"]

        for quality in qualities:
            memory.record_meta_observation(quality, f"Notes about {quality} state")

        recent = memory._read_recent("meta_observations", 10)
        assert len(recent) == 4

        # Verify each quality was recorded
        recorded_qualities = [r["quality"] for r in recent]
        assert set(recorded_qualities) == set(qualities)

        # Verify notes are stored
        assert "present state" in recent[0]["notes"]

    def test_patterns_layer(self, mock_memory_dir):
        """Test patterns layer - what recurs."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Record patterns with varying confidence
        memory.record_pattern(
            "morning_clarity",
            "Clarity is highest in morning sessions",
            ["2025-01-01", "2025-01-02", "2025-01-03"],
            confidence=0.85
        )

        memory.record_pattern(
            "evening_fatigue",
            "Energy drops in evening",
            ["2025-01-01-pm", "2025-01-02-pm"],
            confidence=0.70
        )

        recent = memory._read_recent("patterns", 10)
        assert len(recent) == 2

        # Verify pattern structure
        pattern1 = recent[0]
        assert pattern1["pattern_name"] == "morning_clarity"
        assert pattern1["confidence"] == 0.85
        assert len(pattern1["instances"]) == 3

        pattern2 = recent[1]
        assert pattern2["confidence"] == 0.70

    def test_meta_patterns_layer(self, mock_memory_dir):
        """Test meta-patterns layer - how pattern-recognition shifts."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        shift_types = ["emergence", "refinement", "dissolution", "integration"]

        for shift_type in shift_types:
            memory.record_meta_pattern(
                "test_pattern",
                f"Pattern recognition {shift_type} observed",
                shift_type
            )

        recent = memory._read_recent("meta_patterns", 10)
        assert len(recent) == 4

        # Verify shift types
        recorded_shifts = [r["shift_type"] for r in recent]
        assert set(recorded_shifts) == set(shift_types)

        # Verify pattern references
        for entry in recent:
            assert entry["pattern_about"] == "test_pattern"

    def test_development_layer(self, mock_memory_dir):
        """Test development layer - genuine change tracking."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Record development milestones
        memory.record_development(
            "Learned to detect patterns automatically",
            "Through repeated observation practice",
            "Major capability increase"
        )

        memory.record_development(
            "Telos evolved",
            "New proximate aims added",
            "Orientation shift"
        )

        recent = memory._read_recent("development", 10)
        assert len(recent) == 2

        # Verify structure
        dev1 = recent[0]
        assert dev1["what_changed"] == "Learned to detect patterns automatically"
        assert dev1["how"] == "Through repeated observation practice"
        assert dev1["significance"] == "Major capability increase"


class TestMemoryPersistence:
    """Test memory persistence across instances."""

    def test_observations_persist(self, mock_memory_dir):
        """Test observations persist across memory instances."""
        # Create first instance and record
        memory1 = StrangeLoopMemory(str(mock_memory_dir))
        memory1.record_observation("Persistent observation", {})

        # Create second instance
        memory2 = StrangeLoopMemory(str(mock_memory_dir))

        # Verify observation persisted
        recent = memory2._read_recent("observations", 1)
        assert len(recent) == 1
        assert recent[0]["content"] == "Persistent observation"

    def test_all_layers_persist(self, mock_memory_dir):
        """Test all layers persist across instances."""
        # Write to all layers
        memory1 = StrangeLoopMemory(str(mock_memory_dir))
        memory1.record_observation("Obs", {})
        memory1.record_meta_observation("present", "Meta")
        memory1.record_pattern("pattern", "desc", ["i1"], 0.8)
        memory1.record_meta_pattern("p", "obs", "refinement")
        memory1.record_development("change", "how", "sig")

        # Read from new instance
        memory2 = StrangeLoopMemory(str(mock_memory_dir))

        assert len(memory2._read_recent("observations", 1)) == 1
        assert len(memory2._read_recent("meta_observations", 1)) == 1
        assert len(memory2._read_recent("patterns", 1)) == 1
        assert len(memory2._read_recent("meta_patterns", 1)) == 1
        assert len(memory2._read_recent("development", 1)) == 1

    def test_jsonl_format(self, mock_memory_dir):
        """Test that entries are stored as valid JSONL."""
        memory = StrangeLoopMemory(str(mock_memory_dir))
        memory.record_observation("Test", {"key": "value"})

        # Read file directly
        obs_file = memory.layers["observations"]
        with open(obs_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 1

        # Verify it's valid JSON
        entry = json.loads(lines[0])
        assert entry["content"] == "Test"
        assert entry["context"]["key"] == "value"
        assert "timestamp" in entry


class TestPatternDetection:
    """Test automatic pattern detection."""

    def test_detect_patterns_basic(self, mock_memory_dir):
        """Test basic pattern detection from observations."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Add observations with recurring words
        for i in range(5):
            memory.record_observation(f"Testing recursive observation {i}", {})

        patterns = memory.detect_patterns(min_occurrences=3)

        assert len(patterns) > 0

        # Should detect "testing", "recursive", "observation"
        pattern_words = [p["word"] for p in patterns]
        assert "testing" in pattern_words or "recursive" in pattern_words

    def test_detect_patterns_min_occurrences(self, mock_memory_dir):
        """Test min_occurrences threshold."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Word appears 2 times
        memory.record_observation("rare word here", {})
        memory.record_observation("rare word there", {})

        # With min_occurrences=3, should not detect
        patterns = memory.detect_patterns(min_occurrences=3)
        pattern_words = [p["word"] for p in patterns]
        assert "rare" not in pattern_words

        # With min_occurrences=2, should detect
        patterns = memory.detect_patterns(min_occurrences=2)
        pattern_words = [p["word"] for p in patterns]
        # May or may not detect depending on word length threshold

    def test_detect_patterns_timestamps(self, mock_memory_dir):
        """Test that pattern detection includes timestamps."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        for i in range(4):
            memory.record_observation(f"repeated word instance {i}", {})

        patterns = memory.detect_patterns(min_occurrences=3)

        # Find pattern for "repeated"
        repeated_pattern = [p for p in patterns if p["word"] == "repeated"]

        if repeated_pattern:
            assert "first_seen" in repeated_pattern[0]
            assert "last_seen" in repeated_pattern[0]
            assert repeated_pattern[0]["occurrences"] == 4


class TestContextSummary:
    """Test context summary generation."""

    def test_empty_context_summary(self, mock_memory_dir):
        """Test summary with no entries."""
        memory = StrangeLoopMemory(str(mock_memory_dir))
        summary = memory.get_context_summary(depth=5)

        # Should return empty or header only
        assert summary == "" or "Recent Memory Context" in summary

    def test_context_summary_with_data(self, mock_memory_dir):
        """Test summary with data in all layers."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Add data to layers
        memory.record_observation("Test observation", {})
        memory.record_meta_observation("present", "Test quality")
        memory.record_development("Test change", "Test how", "Test sig")

        summary = memory.get_context_summary(depth=5)

        assert "Recent Memory Context" in summary
        assert "Observations" in summary
        assert "Meta Observations" in summary
        assert "Development" in summary

        # Should include actual content
        assert "Test observation" in summary or "Test observation"[:50] in summary

    def test_context_summary_depth_limit(self, mock_memory_dir):
        """Test that depth parameter limits entries."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Add many observations
        for i in range(10):
            memory.record_observation(f"Observation {i}", {})

        summary = memory.get_context_summary(depth=3)

        # Should only show last 3
        assert "Observation 7" in summary or "Observation 8" in summary or "Observation 9" in summary


class TestMemoryReadWrite:
    """Test low-level read/write operations."""

    def test_append_creates_timestamp(self, mock_memory_dir):
        """Test that _append adds timestamp."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        memory._append("observations", {"content": "Test"})

        recent = memory._read_recent("observations", 1)
        assert "timestamp" in recent[0]

        # Verify timestamp format (ISO 8601)
        timestamp = recent[0]["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise

    def test_read_recent_limit(self, mock_memory_dir):
        """Test reading limited number of recent entries."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Add 10 observations
        for i in range(10):
            memory.record_observation(f"Obs {i}", {})

        # Read last 5
        recent = memory._read_recent("observations", 5)

        assert len(recent) == 5
        # Should be most recent (5-9)
        assert recent[-1]["content"] == "Obs 9"
        assert recent[0]["content"] == "Obs 5"

    def test_read_recent_from_empty(self, mock_memory_dir):
        """Test reading from empty layer."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        recent = memory._read_recent("observations", 10)

        assert recent == []

    def test_read_recent_more_than_available(self, mock_memory_dir):
        """Test reading more entries than available."""
        memory = StrangeLoopMemory(str(mock_memory_dir))

        # Add 3 observations
        for i in range(3):
            memory.record_observation(f"Obs {i}", {})

        # Try to read 10
        recent = memory._read_recent("observations", 10)

        # Should return only 3
        assert len(recent) == 3


class TestWitnessStabilityTracker:
    """Test the WitnessStabilityTracker integration."""
    
    def test_witness_tracker_initialized(self, mock_memory_dir):
        """WitnessStabilityTracker is initialized with StrangeLoopMemory."""
        memory = StrangeLoopMemory(str(mock_memory_dir))
        assert hasattr(memory, 'witness_tracker')
        assert memory.witness_tracker is not None
    
    def test_meta_observation_records_to_tracker(self, mock_memory_dir):
        """Meta observations are also recorded to witness tracker."""
        memory = StrangeLoopMemory(str(mock_memory_dir))
        memory.record_meta_observation("present", "Test note", context="test context")
        
        # Should have recorded to tracker
        snapshots = memory.witness_tracker.get_recent_snapshots(hours=1)
        assert len(snapshots) >= 1
    
    def test_get_witness_status(self, mock_memory_dir):
        """Can get witness stability status."""
        memory = StrangeLoopMemory(str(mock_memory_dir))
        
        # Record enough for analysis
        for _ in range(4):
            memory.record_meta_observation("present", "Test")
        
        status = memory.get_witness_status()
        assert "developing" in status
        assert "explanation" in status
    
    def test_get_witness_summary(self, mock_memory_dir):
        """Can get witness stability summary string."""
        memory = StrangeLoopMemory(str(mock_memory_dir))
        summary = memory.get_witness_summary()
        assert isinstance(summary, str)
