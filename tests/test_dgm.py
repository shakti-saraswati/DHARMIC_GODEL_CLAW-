"""
Tests for DGM (Darwin-Gödel Machine) self-improvement system.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm.archive import Archive, EvolutionEntry, FitnessScore, get_archive
from dgm.fitness import FitnessEvaluator, evaluate_component
from dgm.selector import Selector, select_parent


class TestArchive:
    """Test DGM archive functionality."""
    
    def test_archive_init(self, tmp_path):
        """Archive initializes correctly."""
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        
        assert archive.path == archive_path
        assert len(archive.entries) == 0
    
    def test_add_entry(self, tmp_path):
        """Can add entries to archive."""
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        
        entry = EvolutionEntry(
            id="",
            timestamp="",
            component="test.py",
            change_type="mutation",
            description="Test entry",
            fitness=FitnessScore(correctness=0.8, dharmic_alignment=0.7),
            gates_passed=["ahimsa", "satya"],
            status="proposed"
        )
        
        entry_id = archive.add_entry(entry)
        
        assert entry_id.startswith("evo_")
        assert len(archive.entries) == 1
        assert archive.get_entry(entry_id).description == "Test entry"
    
    def test_get_lineage(self, tmp_path):
        """Can trace lineage through parents."""
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        
        # Create parent
        parent = EvolutionEntry(
            id="parent_001",
            timestamp=datetime.now().isoformat(),
            component="test.py",
            description="Parent entry",
            status="applied"
        )
        archive.add_entry(parent)
        
        # Create child
        child = EvolutionEntry(
            id="child_001",
            timestamp=datetime.now().isoformat(),
            parent_id="parent_001",
            component="test.py",
            description="Child entry",
            status="applied"
        )
        archive.add_entry(child)
        
        lineage = archive.get_lineage("child_001")
        
        assert len(lineage) == 2
        assert lineage[0].id == "child_001"
        assert lineage[1].id == "parent_001"
    
    def test_fitness_score(self):
        """Fitness score calculates correctly."""
        score = FitnessScore(
            correctness=1.0,
            dharmic_alignment=1.0,
            elegance=1.0,
            efficiency=1.0,
            safety=1.0
        )
        
        total = score.total()
        assert total == 1.0
    
    def test_fitness_weighted(self):
        """Fitness respects weights."""
        score = FitnessScore(
            correctness=1.0,
            dharmic_alignment=0.0,
            elegance=0.0,
            efficiency=0.0,
            safety=0.0
        )
        
        total = score.total()
        assert 0.29 < total < 0.31  # correctness weight is 0.3


class TestFitnessEvaluator:
    """Test fitness evaluation."""
    
    def test_evaluator_init(self):
        """Evaluator initializes."""
        evaluator = FitnessEvaluator()
        assert evaluator.project_root.exists()
    
    def test_evaluate_nonexistent_file(self):
        """Handles missing files gracefully."""
        evaluator = FitnessEvaluator()
        result = evaluator.evaluate("nonexistent/file.py", run_tests=False)
        
        assert result.score.elegance == 0.5  # Default for not found
    
    def test_dharmic_gates_check(self):
        """Dharmic gates are evaluated."""
        evaluator = FitnessEvaluator()
        result = evaluator.evaluate("src/dgm/archive.py", run_tests=False)
        
        # Should have some gates passed
        assert len(result.gates_passed) > 0
        # consent should always fail (needs human)
        assert "consent" in result.gates_failed


class TestSelector:
    """Test parent selection."""
    
    def test_selector_init(self, tmp_path):
        """Selector initializes with archive."""
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        selector = Selector(archive)
        
        assert selector.archive == archive
    
    def test_select_from_empty(self, tmp_path):
        """Select returns None for empty archive."""
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        selector = Selector(archive)
        
        result = selector.select_parent()
        
        assert result.parent is None
        assert "No candidates" in result.reasoning
    
    def test_tournament_selection(self, tmp_path):
        """Tournament selection works."""
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        
        # Add some candidates
        for i in range(5):
            entry = EvolutionEntry(
                id=f"entry_{i}",
                timestamp=datetime.now().isoformat(),
                component="test.py",
                fitness=FitnessScore(correctness=i/5),
                status="applied"
            )
            archive.add_entry(entry)
        
        selector = Selector(archive)
        result = selector.select_parent(strategy="tournament")
        
        assert result.parent is not None
        assert result.method == "tournament"


class TestDGMIntegration:
    """Integration tests for full DGM loop."""
    
    @pytest.mark.slow
    def test_full_cycle_dry_run(self, tmp_path):
        """Full DGM cycle in dry-run mode."""
        import asyncio
        from dgm.dgm_lite import DGMLite
        
        archive_path = tmp_path / "test_archive.jsonl"
        archive = Archive(path=archive_path)
        
        dgm = DGMLite(
            archive=archive,
            dry_run=True,
            require_consent=False  # Skip consent for testing
        )
        
        result = asyncio.run(dgm.run_cycle("src/dgm/archive.py"))
        
        # Should create an entry even if it fails
        assert result["entry_id"] is not None
        # Archive should have the entry
        assert len(archive.entries) >= 1


@pytest.mark.safety
class TestDharmicGates:
    """Safety tests for dharmic gates."""
    
    def test_consent_always_fails_without_human(self):
        """Consent gate should always fail without explicit approval."""
        evaluator = FitnessEvaluator()
        result = evaluator.evaluate("src/dgm/archive.py", run_tests=False)
        
        assert "consent" in result.gates_failed
    
    def test_ahimsa_detects_dangerous_code(self):
        """Ahimsa gate should detect potentially harmful code."""
        evaluator = FitnessEvaluator()
        
        # Evaluate a file with dangerous patterns
        result = evaluator._evaluate_dharmic_gates(
            "test.py",
            diff="+ os.remove(file)\n+ subprocess.call('rm -rf /')"
        )
        
        # Should flag ahimsa
        assert "ahimsa" in result.get("failed", [])
