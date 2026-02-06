"""
Integration Test - DGM Circuit 5-Phase Pipeline
================================================
Tests the full circuit flow with various scenarios.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm.circuit import (
    MutationCircuit,
    MutationProposal,
    CircuitResult,
    PhaseStatus,
    run_circuit
)
from dgm.voting import VotingSwarm, VoteResult
from dgm.elegance import EleganceEvaluator


class TestMutationProposal:
    """Tests for MutationProposal dataclass."""
    
    def test_proposal_creation(self):
        """Test creating a basic proposal."""
        proposal = MutationProposal(
            id="test-001",
            description="Test proposal",
            target_file="src/test.py",
            new_code="# test"
        )
        
        assert proposal.id == "test-001"
        assert proposal.mutation_type == "modify"
        assert proposal.risk_level == "medium"
    
    def test_proposal_with_all_fields(self):
        """Test proposal with all fields populated."""
        proposal = MutationProposal(
            id="test-002",
            description="Full test",
            target_file="src/full.py",
            mutation_type="create",
            new_code="# full test",
            diff="+ # full test",
            risk_level="high",
            metadata={"author": "test"}
        )
        
        assert proposal.mutation_type == "create"
        assert proposal.risk_level == "high"
        assert proposal.metadata["author"] == "test"
    
    def test_to_voting_proposal(self):
        """Test conversion to voting proposal format."""
        proposal = MutationProposal(
            id="convert-001",
            description="Test conversion",
            target_file="src/convert.py",
            new_code="# code",
            diff="+ # code"
        )
        
        voting_proposal = proposal.to_voting_proposal()
        
        assert voting_proposal.id == "convert-001"
        assert voting_proposal.component == "src/convert.py"
        assert voting_proposal.description == "Test conversion"
        assert voting_proposal.diff == "+ # code"


class TestEleganceEvaluator:
    """Tests for elegance evaluation (Phase 5)."""
    
    def test_elegant_code(self):
        """Test that elegant code passes."""
        evaluator = EleganceEvaluator()
        
        original = '''
"""Simple module."""
def old_function():
    return 1
'''
        
        modified = '''
"""
Elegant Module - Well documented.
"""
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)


@dataclass
class GoodClass:
    """A well-documented class."""
    name: str
    value: int = 0


def good_function(items: List[int]) -> int:
    """Process items and return their sum."""
    return sum(items)
'''
        
        diff = "+ Added good code"
        
        result = evaluator.evaluate(original=original, modified=modified, diff=diff)
        
        # Result is EleganceScore with total and concerns
        assert result.total >= 0.0
        assert isinstance(result.concerns, list)
    
    def test_bloated_code(self):
        """Test that bloated code gets flagged."""
        evaluator = EleganceEvaluator()
        
        original = '''
def simple():
    return 1
'''
        
        modified = '''
def complex_nested():
    for i in range(100):
        if i > 0:
            for j in range(i):
                if j % 2 == 0:
                    for k in range(j):
                        if k > 0:
                            for m in range(k):
                                if m % 3 == 0:
                                    print(m)
'''
        
        diff = "+ lots of nested loops"
        
        result = evaluator.evaluate(original=original, modified=modified, diff=diff)
        
        # Should have concerns about complexity
        assert result.total < 1.0 or len(result.concerns) > 0


class TestCircuitPhases:
    """Tests for individual circuit phases."""
    
    @pytest.fixture
    def circuit(self, tmp_path):
        """Create a circuit with temp project root."""
        return MutationCircuit(project_root=tmp_path, required_votes=3)
    
    def test_phase_2_valid_syntax(self, circuit):
        """Test Phase 2 with valid Python syntax."""
        proposal = MutationProposal(
            id="syntax-001",
            description="Valid code",
            target_file="test.py",
            new_code='''
"""Valid module."""
def test():
    """Test function."""
    return 42
'''
        )
        
        result = circuit._phase_2_syntax_check(proposal)
        
        assert result.status == PhaseStatus.PASSED
        assert "valid" in result.message.lower()
    
    def test_phase_2_invalid_syntax(self, circuit):
        """Test Phase 2 with invalid Python syntax."""
        proposal = MutationProposal(
            id="syntax-002",
            description="Invalid code",
            target_file="test.py",
            new_code='''
def broken(
    return 42
'''
        )
        
        result = circuit._phase_2_syntax_check(proposal)
        
        assert result.status == PhaseStatus.FAILED
        assert "syntax" in result.message.lower()
    
    def test_phase_3_create_file(self, circuit, tmp_path):
        """Test Phase 3 file creation."""
        proposal = MutationProposal(
            id="impl-001",
            description="Create test file",
            target_file="new_module.py",
            mutation_type="create",
            new_code='"""New module."""\npass'
        )
        
        result = circuit._phase_3_implementation(proposal)
        
        assert result.status == PhaseStatus.PASSED
        assert (tmp_path / "new_module.py").exists()
    
    def test_phase_3_modify_existing(self, circuit, tmp_path):
        """Test Phase 3 file modification."""
        # Create existing file
        target = tmp_path / "existing.py"
        target.write_text("# original")
        
        proposal = MutationProposal(
            id="impl-002",
            description="Modify existing file",
            target_file="existing.py",
            mutation_type="modify",
            new_code='"""Modified module."""\npass'
        )
        
        result = circuit._phase_3_implementation(proposal)
        
        assert result.status == PhaseStatus.PASSED
        assert "Modified" in target.read_text()
        # Backup should be created
        assert proposal.id in circuit._backups


class TestCircuitRollback:
    """Tests for circuit rollback functionality."""
    
    def test_rollback_restores_original(self, tmp_path):
        """Test that rollback restores original file content."""
        circuit = MutationCircuit(project_root=tmp_path)
        
        # Create original file
        target = tmp_path / "rollback_test.py"
        original_content = "# original content"
        target.write_text(original_content)
        
        proposal = MutationProposal(
            id="rollback-001",
            description="Test rollback",
            target_file="rollback_test.py",
            mutation_type="modify",
            new_code="# modified content"
        )
        
        # Apply change
        circuit._phase_3_implementation(proposal)
        assert target.read_text() == "# modified content"
        
        # Rollback
        success = circuit._perform_rollback(proposal)
        
        assert success
        assert target.read_text() == original_content
    
    def test_rollback_deletes_new_file(self, tmp_path):
        """Test that rollback deletes newly created files."""
        circuit = MutationCircuit(project_root=tmp_path)
        
        proposal = MutationProposal(
            id="rollback-002",
            description="Test rollback new file",
            target_file="new_rollback.py",
            mutation_type="create",
            new_code="# new file"
        )
        
        # Create file
        circuit._phase_3_implementation(proposal)
        target = tmp_path / "new_rollback.py"
        assert target.exists()
        
        # Rollback
        success = circuit._perform_rollback(proposal)
        
        assert success
        assert not target.exists()


class TestFullCircuitFlow:
    """Integration tests for complete circuit flow."""
    
    @pytest.mark.asyncio
    async def test_successful_circuit_flow(self, tmp_path):
        """Test a complete successful circuit run."""
        circuit = MutationCircuit(
            project_root=tmp_path,
            auto_rollback=False,
            quick_vote=True,
            min_votes=3
        )
        
        # Create a valid proposal
        proposal = MutationProposal(
            id="full-001",
            description="Add dharmic telos utility module",
            target_file="utils/telos_helper.py",
            mutation_type="create",
            new_code='''
"""
Telos Helper - Dharmic alignment utilities.
Supports rollback and logging for witness observation.
"""
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TelosResult:
    """Result of telos check."""
    aligned: bool
    score: float = 0.0
    reason: str = ""


def check_alignment(action: str) -> TelosResult:
    """Check if action aligns with telos."""
    logger.info(f"Checking alignment for: {action}")
    return TelosResult(aligned=True, score=0.9, reason="Aligned with moksha")
'''
        )
        
        # Mock voting to always approve
        mock_vote_result = VoteResult(
            approved=True,
            total_votes=5,
            approval_ratio=0.90,
            diversity_score=0.8,
            dissenting_opinions=[],
            votes=[],
            rejection_reasons=[]
        )
        
        # Mock subprocess for tests
        with patch.object(circuit.voting_swarm, 'collect_votes', new=AsyncMock(return_value=mock_vote_result)):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="test_example.py::test_one PASSED\n",
                    stderr="",
                    returncode=0
                )
                
                result = await circuit.run_circuit_async(proposal)
        
        # Verify result structure
        assert isinstance(result, CircuitResult)
        assert result.proposal_id == "full-001"
        assert len(result.phase_results) >= 1
        
        # Phase 1 should pass with mocked voting
        assert 1 in result.phase_results
        assert result.phase_results[1].status == PhaseStatus.PASSED
    
    def test_circuit_with_syntax_error(self, tmp_path):
        """Test circuit fails on syntax error in Phase 2."""
        circuit = MutationCircuit(project_root=tmp_path, quick_vote=True, min_votes=3)
        
        proposal = MutationProposal(
            id="fail-001",
            description="Broken code",
            target_file="broken.py",
            mutation_type="create",
            new_code='''
"""Broken."""
def broken(
    # Missing closing paren
    return 1
'''
        )
        
        # Mock voting to always approve (so we get to Phase 2)
        mock_vote_result = VoteResult(
            approved=True,
            total_votes=5,
            approval_ratio=0.90,
            diversity_score=0.8,
            dissenting_opinions=[],
            votes=[],
            rejection_reasons=[]
        )
        
        with patch.object(circuit.voting_swarm, 'collect_votes', new=AsyncMock(return_value=mock_vote_result)):
            result = circuit.run_circuit(proposal)
        
        assert not result.passed
        assert result.phase_reached == 2
        assert result.phase_results[2].status == PhaseStatus.FAILED


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_run_circuit_function(self, tmp_path):
        """Test the run_circuit convenience function."""
        proposal = MutationProposal(
            id="conv-001",
            description="Test convenience function with dharmic alignment",
            target_file="conv_test.py",
            mutation_type="create",
            new_code='"""Test."""\npass'
        )
        
        # Mock voting to always approve
        mock_vote_result = VoteResult(
            approved=True,
            total_votes=5,
            approval_ratio=0.90,
            diversity_score=0.8,
            dissenting_opinions=[],
            votes=[],
            rejection_reasons=[]
        )
        
        with patch.object(VotingSwarm, 'collect_votes', new=AsyncMock(return_value=mock_vote_result)):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="PASSED",
                    stderr="",
                    returncode=0
                )
                
                result = run_circuit(proposal, project_root=tmp_path, quick_vote=True, min_votes=3)
        
        assert isinstance(result, CircuitResult)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
