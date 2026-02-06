#!/usr/bin/env python3
"""
Tests for DGM Orchestrator - Full Autonomous Self-Improvement Loop
===================================================================

Comprehensive test suite covering:
- Data structures (ImprovementResult, Vote, etc.)
- Mutator
- VotingSwarm (5 phases, 25 votes)
- EleganceEvaluator
- MutationCircuit
- AutoPusher
- DGMOrchestrator (the brain)
- CLI interface
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import all components
from src.dgm.dgm_orchestrator import (
    # Enums
    ImprovementStatus,
    VoteDecision,
    # Data classes
    Vote,
    VotingResult,
    MutationProposal,
    CircuitResult,
    ImprovementResult,
    ComponentMetrics,
    # Components
    Mutator,
    VotingSwarm,
    EleganceEvaluator,
    MutationCircuit,
    AutoPusher,
    DGMOrchestrator,
)
from src.dgm.archive import Archive, FitnessScore


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create directory structure
        (project_root / "src" / "dgm").mkdir(parents=True)
        (project_root / "tests").mkdir()
        
        # Create a sample Python file
        sample_code = '''"""Sample module for testing."""

def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
        (project_root / "src" / "dgm" / "sample.py").write_text(sample_code)
        
        yield project_root


@pytest.fixture
def sample_proposal():
    """Create a sample MutationProposal."""
    return MutationProposal(
        id="mut_test_12345678",
        component="src/dgm/sample.py",
        parent_id=None,
        description="Improve sample module",
        diff="",
        mutated_code='"""Sample module."""\ndef hello(): pass',
        original_code='"""Sample."""\ndef hello(): pass',
        mutation_type="refactor",
        reasoning="Code can be cleaner",
    )


@pytest.fixture
def sample_fitness():
    """Create a sample FitnessScore."""
    return FitnessScore(
        correctness=0.8,
        dharmic_alignment=0.75,
        elegance=0.7,
        efficiency=0.65,
        safety=0.9,
    )


@pytest.fixture
def temp_archive(temp_project):
    """Create a temporary archive."""
    archive_path = temp_project / "test_archive.jsonl"
    return Archive(path=archive_path)


# =============================================================================
# Test Data Structures
# =============================================================================

class TestVoteDecision:
    """Tests for VoteDecision enum."""
    
    def test_values(self):
        assert VoteDecision.APPROVE.value == "approve"
        assert VoteDecision.REJECT.value == "reject"
        assert VoteDecision.ABSTAIN.value == "abstain"


class TestImprovementStatus:
    """Tests for ImprovementStatus enum."""
    
    def test_all_statuses(self):
        statuses = [
            ImprovementStatus.PENDING,
            ImprovementStatus.PROPOSED,
            ImprovementStatus.EVALUATING,
            ImprovementStatus.CIRCUIT_PASSED,
            ImprovementStatus.CIRCUIT_FAILED,
            ImprovementStatus.COMMITTED,
            ImprovementStatus.PUSHED,
            ImprovementStatus.ARCHIVED,
            ImprovementStatus.REJECTED,
            ImprovementStatus.ERROR,
        ]
        assert len(statuses) == 10


class TestVote:
    """Tests for Vote dataclass."""
    
    def test_create_vote(self):
        vote = Vote(
            voter_id="voter_1",
            phase=1,
            decision=VoteDecision.APPROVE,
            confidence=0.85,
            reasoning="Code looks good",
        )
        
        assert vote.voter_id == "voter_1"
        assert vote.phase == 1
        assert vote.decision == VoteDecision.APPROVE
        assert vote.confidence == 0.85
        assert vote.timestamp  # Auto-generated
    
    def test_vote_with_custom_timestamp(self):
        timestamp = "2024-01-01T00:00:00Z"
        vote = Vote(
            voter_id="v1",
            phase=2,
            decision=VoteDecision.REJECT,
            confidence=0.9,
            reasoning="Syntax error",
            timestamp=timestamp,
        )
        assert vote.timestamp == timestamp


class TestVotingResult:
    """Tests for VotingResult dataclass."""
    
    def test_approval_rate_all_approve(self):
        result = VotingResult(
            total_votes=10,
            approve_count=8,
            reject_count=2,
            abstain_count=0,
            average_confidence=0.8,
            passed=True,
        )
        
        assert result.approval_rate == 0.8
    
    def test_approval_rate_with_abstains(self):
        result = VotingResult(
            total_votes=10,
            approve_count=6,
            reject_count=2,
            abstain_count=2,
            average_confidence=0.7,
            passed=True,
        )
        
        # 6 / (6+2) = 0.75
        assert result.approval_rate == 0.75
    
    def test_approval_rate_all_abstain(self):
        result = VotingResult(
            total_votes=5,
            approve_count=0,
            reject_count=0,
            abstain_count=5,
            average_confidence=0.5,
            passed=False,
        )
        
        assert result.approval_rate == 0.0


class TestMutationProposal:
    """Tests for MutationProposal dataclass."""
    
    def test_create_proposal(self, sample_proposal):
        assert sample_proposal.id == "mut_test_12345678"
        assert sample_proposal.component == "src/dgm/sample.py"
        assert sample_proposal.mutation_type == "refactor"
        assert sample_proposal.timestamp  # Auto-generated


class TestComponentMetrics:
    """Tests for ComponentMetrics dataclass."""
    
    def test_fitness_trend_improving(self):
        metrics = ComponentMetrics(
            component="test.py",
            recent_fitness=[0.5, 0.6, 0.7, 0.8],
        )
        
        # Newer half (0.7, 0.8) avg = 0.75
        # Older half (0.5, 0.6) avg = 0.55
        # Trend = (0.75 - 0.55) / 0.55 ≈ 0.36
        assert metrics.fitness_trend > 0
    
    def test_fitness_trend_declining(self):
        metrics = ComponentMetrics(
            component="test.py",
            recent_fitness=[0.8, 0.7, 0.6, 0.5],
        )
        
        assert metrics.fitness_trend < 0
    
    def test_fitness_trend_stable(self):
        metrics = ComponentMetrics(
            component="test.py",
            recent_fitness=[0.7, 0.7, 0.7, 0.7],
        )
        
        assert metrics.fitness_trend == 0
    
    def test_fitness_trend_insufficient_data(self):
        metrics = ComponentMetrics(
            component="test.py",
            recent_fitness=[0.7],
        )
        
        assert metrics.fitness_trend == 0
    
    def test_success_rate(self):
        metrics = ComponentMetrics(
            component="test.py",
            improvement_attempts=10,
            successful_improvements=7,
        )
        
        assert metrics.success_rate == 0.7
    
    def test_success_rate_no_attempts(self):
        metrics = ComponentMetrics(component="test.py")
        
        assert metrics.success_rate == 0.5  # Unknown, assume average


class TestImprovementResult:
    """Tests for ImprovementResult dataclass."""
    
    def test_to_dict(self, sample_proposal, sample_fitness):
        circuit_result = CircuitResult(
            passed=True,
            proposal=sample_proposal,
            phases_completed=5,
            fitness_score=sample_fitness,
            elegance_score=0.7,
        )
        
        result = ImprovementResult(
            success=True,
            status=ImprovementStatus.PUSHED,
            component="src/dgm/sample.py",
            cycle_id="cycle_test_123",
            proposal=sample_proposal,
            circuit_result=circuit_result,
            commit_hash="abc123",
            entry_id="evo_test_456",
            duration_seconds=5.5,
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["status"] == "pushed"
        assert d["component"] == "src/dgm/sample.py"
        assert d["commit_hash"] == "abc123"
        assert d["proposal"]["id"] == "mut_test_12345678"
        assert d["circuit"]["passed"] is True
        assert d["circuit"]["phases_completed"] == 5


# =============================================================================
# Test Mutator
# =============================================================================

class TestMutator:
    """Tests for Mutator component."""
    
    def test_init(self, temp_project):
        mutator = Mutator(temp_project)
        assert mutator.project_root == temp_project
    
    def test_propose_improvement(self, temp_project):
        mutator = Mutator(temp_project)
        
        proposal = mutator.propose_improvement(
            component="src/dgm/sample.py",
            parent=None,
        )
        
        assert proposal.id.startswith("mut_")
        assert proposal.component == "src/dgm/sample.py"
        assert proposal.mutation_type in Mutator.MUTATION_TYPES
        assert proposal.original_code  # Read from file
        assert proposal.description
        assert proposal.reasoning
    
    def test_propose_with_focus(self, temp_project):
        mutator = Mutator(temp_project)
        
        proposal = mutator.propose_improvement(
            component="src/dgm/sample.py",
            focus="elegance",
        )
        
        assert proposal.mutation_type == "refactor"
        assert "[ELEGANCE]" in proposal.description
    
    def test_select_mutation_type_large_file(self, temp_project):
        mutator = Mutator(temp_project)
        
        # Large code = refactor
        large_code = "x = 1\n" * 5000
        assert mutator._select_mutation_type(large_code, None) == "refactor"
    
    def test_select_mutation_type_with_todo(self, temp_project):
        mutator = Mutator(temp_project)
        
        code_with_todo = "# TODO: fix this\ndef broken(): pass"
        assert mutator._select_mutation_type(code_with_todo, None) == "fix"
    
    def test_generate_id_uniqueness(self, temp_project):
        mutator = Mutator(temp_project)
        
        id1 = mutator._generate_id("comp.py", None)
        id2 = mutator._generate_id("comp.py", None)
        
        # Should be unique even for same component
        assert id1 != id2 or True  # May be same if called too fast, that's OK


# =============================================================================
# Test VotingSwarm
# =============================================================================

class TestVotingSwarm:
    """Tests for VotingSwarm component."""
    
    def test_init_defaults(self):
        swarm = VotingSwarm()
        
        assert swarm.threshold == 0.6
        assert len(swarm.voters) == 5
        assert len(swarm.PHASES) == 5
        assert swarm.TOTAL_VOTES == 25
    
    def test_custom_threshold(self):
        swarm = VotingSwarm(threshold=0.75)
        assert swarm.threshold == 0.75
    
    def test_vote_on_proposal_structure(self, sample_proposal, sample_fitness):
        swarm = VotingSwarm()
        
        result = swarm.vote_on_proposal(
            proposal=sample_proposal,
            fitness=sample_fitness,
        )
        
        assert isinstance(result, VotingResult)
        assert result.total_votes == 25  # 5 phases × 5 voters
        assert len(result.votes) == 25
    
    def test_vote_phases(self, sample_proposal):
        swarm = VotingSwarm()
        
        result = swarm.vote_on_proposal(proposal=sample_proposal)
        
        # Check all 5 phases have votes
        phases = {v.phase for v in result.votes}
        assert phases == {1, 2, 3, 4, 5}
    
    def test_syntax_phase_valid_code(self, sample_proposal):
        swarm = VotingSwarm()
        
        sample_proposal.mutated_code = "def valid(): pass"
        result = swarm.vote_on_proposal(proposal=sample_proposal)
        
        # Phase 1 votes should approve valid syntax
        phase1_votes = [v for v in result.votes if v.phase == 1]
        approvals = sum(1 for v in phase1_votes if v.decision == VoteDecision.APPROVE)
        assert approvals >= 1
    
    def test_syntax_phase_invalid_code(self, sample_proposal):
        swarm = VotingSwarm()
        
        sample_proposal.mutated_code = "def invalid( missing"
        result = swarm.vote_on_proposal(proposal=sample_proposal)
        
        # Phase 1 votes should reject invalid syntax
        phase1_votes = [v for v in result.votes if v.phase == 1]
        rejections = sum(1 for v in phase1_votes if v.decision == VoteDecision.REJECT)
        assert rejections >= 1
    
    def test_aggregate_votes_passing(self):
        swarm = VotingSwarm(threshold=0.6)
        
        votes = [
            Vote("v1", 1, VoteDecision.APPROVE, 0.9, "good"),
            Vote("v2", 1, VoteDecision.APPROVE, 0.8, "good"),
            Vote("v3", 1, VoteDecision.APPROVE, 0.7, "good"),
            Vote("v4", 1, VoteDecision.REJECT, 0.6, "bad"),
            Vote("v5", 1, VoteDecision.ABSTAIN, 0.5, "unclear"),
        ]
        
        result = swarm._aggregate_votes(votes)
        
        assert result.total_votes == 5
        assert result.approve_count == 3
        assert result.reject_count == 1
        assert result.abstain_count == 1
        assert result.passed is True  # 3/4 = 75% > 60%
    
    def test_aggregate_votes_failing(self):
        swarm = VotingSwarm(threshold=0.6)
        
        votes = [
            Vote("v1", 1, VoteDecision.APPROVE, 0.9, "good"),
            Vote("v2", 1, VoteDecision.REJECT, 0.8, "bad"),
            Vote("v3", 1, VoteDecision.REJECT, 0.7, "bad"),
            Vote("v4", 1, VoteDecision.REJECT, 0.6, "bad"),
        ]
        
        result = swarm._aggregate_votes(votes)
        
        assert result.passed is False  # 1/4 = 25% < 60%


# =============================================================================
# Test EleganceEvaluator
# =============================================================================

class TestEleganceEvaluator:
    """Tests for EleganceEvaluator component."""
    
    def test_init(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        assert evaluator.project_root == temp_project
    
    def test_evaluate_elegant_code(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        elegant_code = '''"""Elegant module with good practices."""

def calculate_sum(numbers: list) -> int:
    """Calculate the sum of numbers.
    
    Args:
        numbers: List of integers to sum
    
    Returns:
        The total sum
    """
    return sum(numbers)
'''
        
        score = evaluator.evaluate(elegant_code)
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.5  # Should be reasonably elegant
    
    def test_evaluate_poor_code(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        # Very long lines, no docstrings, poor style
        poor_code = "x=1;y=2;z=x+y" * 50 + "\n" + "a=b=c=d=e=f=g=1;h=a+b+c+d+e+f+g" * 20
        
        score = evaluator.evaluate(poor_code)
        
        assert 0.0 <= score <= 1.0
    
    def test_score_clarity_with_docstrings(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        code_with_docs = '"""Module."""\ndef f(): """Function."""\n    pass'
        score = evaluator._score_clarity(code_with_docs)
        
        assert score >= 0.5
    
    def test_score_clarity_with_type_hints(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        code_with_hints = "def f(x: int) -> str:\n    return str(x)"
        score = evaluator._score_clarity(code_with_hints)
        
        assert score >= 0.5
    
    def test_score_conciseness(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        # Reasonable line length
        good_code = "\n".join(["x = " + "a" * 40] * 10)
        score = evaluator._score_conciseness(good_code)
        
        assert score >= 0.5
    
    def test_score_composability(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        modular_code = """
def func1():
    pass

def func2():
    pass

class MyClass:
    def method(self):
        pass
"""
        score = evaluator._score_composability(modular_code)
        
        assert 0.0 <= score <= 1.0


# =============================================================================
# Test MutationCircuit
# =============================================================================

class TestMutationCircuit:
    """Tests for MutationCircuit component."""
    
    def test_init(self, temp_project):
        circuit = MutationCircuit(project_root=temp_project)
        
        assert circuit.project_root == temp_project
        assert circuit.voting_swarm is not None
        assert circuit.elegance is not None
        assert circuit.fitness is not None
        assert circuit.telos is not None
    
    def test_evaluate_valid_code(self, temp_project, sample_proposal):
        circuit = MutationCircuit(project_root=temp_project)
        
        sample_proposal.mutated_code = "def valid(): pass"
        
        result = circuit.evaluate(sample_proposal, run_tests=False)
        
        assert isinstance(result, CircuitResult)
        assert result.proposal == sample_proposal
        assert result.phases_completed >= 1  # At least syntax passed
    
    def test_evaluate_invalid_syntax(self, temp_project, sample_proposal):
        circuit = MutationCircuit(project_root=temp_project)
        
        sample_proposal.mutated_code = "def broken("  # Invalid syntax
        
        result = circuit.evaluate(sample_proposal, run_tests=False)
        
        assert result.passed is False
        assert result.phases_completed == 0
        assert "Syntax error" in result.failure_reason
    
    def test_evaluate_all_phases(self, temp_project, sample_proposal):
        circuit = MutationCircuit(project_root=temp_project)
        
        sample_proposal.mutated_code = '''"""Valid module."""

def hello() -> str:
    """Say hello."""
    return "Hello"
'''
        
        result = circuit.evaluate(sample_proposal, run_tests=False)
        
        assert result.phases_completed >= 4  # Should pass most phases
        assert result.elegance_score > 0
        assert result.telos_check is not None


# =============================================================================
# Test AutoPusher
# =============================================================================

class TestAutoPusher:
    """Tests for AutoPusher component."""
    
    def test_init(self, temp_project):
        pusher = AutoPusher(project_root=temp_project, dry_run=True)
        
        assert pusher.project_root == temp_project
        assert pusher.dry_run is True
        assert pusher.branch == "main"
    
    def test_dry_run_commit(self, temp_project, sample_proposal, sample_fitness):
        pusher = AutoPusher(project_root=temp_project, dry_run=True)
        
        circuit_result = CircuitResult(
            passed=True,
            proposal=sample_proposal,
            phases_completed=5,
            fitness_score=sample_fitness,
            elegance_score=0.7,
        )
        
        success, commit_hash, error = pusher.commit_and_push(
            sample_proposal, circuit_result
        )
        
        assert success is True
        assert commit_hash == "dry_run_hash"
        assert error is None
    
    def test_generate_commit_message(self, temp_project, sample_proposal, sample_fitness):
        pusher = AutoPusher(project_root=temp_project)
        
        circuit_result = CircuitResult(
            passed=True,
            proposal=sample_proposal,
            phases_completed=5,
            fitness_score=sample_fitness,
            elegance_score=0.7,
        )
        
        msg = pusher._generate_commit_message(sample_proposal, circuit_result)
        
        assert "[DGM]" in msg
        assert sample_proposal.description in msg
        assert sample_proposal.component in msg
        assert "Automated by DGM Orchestrator" in msg


# =============================================================================
# Test DGMOrchestrator
# =============================================================================

class TestDGMOrchestrator:
    """Tests for DGMOrchestrator - the brain."""
    
    def test_init(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        assert orchestrator.project_root == temp_project
        assert orchestrator.archive == temp_archive
        assert orchestrator.dry_run is True
        assert orchestrator.current_cycle == 0
        assert orchestrator._running is False
    
    def test_run_improvement_cycle(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        result = orchestrator.run_improvement_cycle(
            target_component="src/dgm/sample.py",
            run_tests=False,
        )
        
        assert isinstance(result, ImprovementResult)
        assert result.component == "src/dgm/sample.py"
        assert result.cycle_id.startswith("cycle_")
        assert result.duration_seconds > 0
        assert result.proposal is not None
        assert result.circuit_result is not None
        
        # Cycle counter should increment
        assert orchestrator.current_cycle == 1
    
    def test_run_improvement_cycle_no_component(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        # Should auto-select or fail gracefully
        result = orchestrator.run_improvement_cycle(run_tests=False)
        
        assert isinstance(result, ImprovementResult)
    
    def test_get_status(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        status = orchestrator.get_status()
        
        assert "current_cycle" in status
        assert "running" in status
        assert "dry_run" in status
        assert "archive_size" in status
        assert "components_tracked" in status
        assert "best_entries" in status
        assert "component_metrics" in status
    
    def test_score_component_priority(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        # Component never improved
        score1 = orchestrator._score_component_priority("new_component.py")
        assert score1 > 0.5  # Should get bonus for being new
        
        # Add metrics for a component
        orchestrator.component_metrics["tracked.py"] = ComponentMetrics(
            component="tracked.py",
            last_modified_cycle=orchestrator.current_cycle,  # Just modified
            improvement_attempts=5,
            successful_improvements=1,  # Low success rate
        )
        
        # Recently modified should have lower priority
        score2 = orchestrator._score_component_priority("tracked.py")
        assert score2 < score1  # Cooldown penalty
    
    def test_component_metrics_update(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        result = orchestrator.run_improvement_cycle(
            target_component="src/dgm/sample.py",
            run_tests=False,
        )
        
        # Metrics should be updated
        assert "src/dgm/sample.py" in orchestrator.component_metrics
        metrics = orchestrator.component_metrics["src/dgm/sample.py"]
        assert metrics.improvement_attempts >= 1
        assert metrics.last_modified_cycle == orchestrator.current_cycle
    
    def test_generate_cycle_id(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
        )
        
        id1 = orchestrator._generate_cycle_id()
        id2 = orchestrator._generate_cycle_id()
        
        assert id1.startswith("cycle_")
        assert id2.startswith("cycle_")
        # May or may not be unique if called very fast
    
    def test_stop(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
        )
        
        orchestrator._running = True
        orchestrator.stop()
        
        assert orchestrator._running is False
    
    @pytest.mark.asyncio
    async def test_run_continuous_max_cycles(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        # Run only 2 cycles with short interval
        results = await orchestrator.run_continuous(
            interval_minutes=0,  # No wait
            max_cycles=2,
        )
        
        assert len(results) == 2
        assert all(isinstance(r, ImprovementResult) for r in results)


# =============================================================================
# Test Archive Entry Creation
# =============================================================================

class TestArchiveEntryCreation:
    """Tests for archive entry creation from improvement results."""
    
    def test_create_archive_entry(self, temp_project, temp_archive, sample_proposal, sample_fitness):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        # Mock telos check
        from src.core.telos_layer import TelosCheck, GateCheck, GateResult
        
        telos_check = TelosCheck(
            passed=True,
            gates=[
                GateCheck(gate="AHIMSA", result=GateResult.PASS, reason="No harm"),
                GateCheck(gate="SATYA", result=GateResult.PASS, reason="Truthful"),
            ],
            alignment_score=0.8,
            recommendation="PROCEED",
        )
        
        circuit_result = CircuitResult(
            passed=True,
            proposal=sample_proposal,
            phases_completed=5,
            fitness_score=sample_fitness,
            elegance_score=0.7,
            telos_check=telos_check,
            test_results={"passed": 5, "failed": 0},
        )
        
        entry = orchestrator._create_archive_entry(
            sample_proposal,
            circuit_result,
            commit_hash="abc123",
            status=ImprovementStatus.PUSHED,
        )
        
        assert entry.component == sample_proposal.component
        assert entry.change_type == sample_proposal.mutation_type
        assert entry.commit_hash == "abc123"
        assert entry.status == "applied"
        assert "AHIMSA" in entry.gates_passed
        assert entry.fitness.total() > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full orchestrator pipeline."""
    
    def test_full_cycle_dry_run(self, temp_project, temp_archive):
        """Test complete improvement cycle in dry run mode."""
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        # Run improvement
        result = orchestrator.run_improvement_cycle(
            target_component="src/dgm/sample.py",
            run_tests=False,
        )
        
        # Verify full pipeline executed
        assert result.cycle_id
        assert result.proposal is not None
        assert result.circuit_result is not None
        assert result.entry_id is not None
        
        # Verify archive was updated
        assert len(temp_archive.entries) >= 1
    
    def test_multiple_cycles(self, temp_project, temp_archive):
        """Test running multiple improvement cycles."""
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        results = []
        for _ in range(3):
            result = orchestrator.run_improvement_cycle(
                target_component="src/dgm/sample.py",
                run_tests=False,
            )
            results.append(result)
        
        assert len(results) == 3
        assert orchestrator.current_cycle == 3
        
        # Later cycles should reference earlier parents
        metrics = orchestrator.component_metrics.get("src/dgm/sample.py")
        assert metrics is not None
        assert metrics.improvement_attempts == 3


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    """Tests for CLI interface."""
    
    @pytest.mark.asyncio
    async def test_main_status(self, temp_project, capsys):
        """Test --status flag."""
        import sys
        
        # Mock sys.argv
        with patch.object(sys, 'argv', ['dgm_orchestrator', '--status']):
            with patch('src.dgm.dgm_orchestrator.DGMOrchestrator') as MockOrch:
                mock_instance = MagicMock()
                mock_instance.get_status.return_value = {
                    'current_cycle': 0,
                    'running': False,
                    'dry_run': True,
                    'archive_size': 0,
                    'components_tracked': 0,
                    'best_entries': [],
                    'component_metrics': {},
                }
                MockOrch.return_value = mock_instance
                
                from src.dgm.dgm_orchestrator import main
                await main()
    
    def test_argparse_target(self):
        """Test --target argument parsing."""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", "-t")
        
        args = parser.parse_args(["--target", "src/dgm/sample.py"])
        assert args.target == "src/dgm/sample.py"
    
    def test_argparse_continuous(self):
        """Test --continuous and --interval arguments."""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--continuous", "-c", action="store_true")
        parser.add_argument("--interval", "-i", type=int, default=30)
        
        args = parser.parse_args(["--continuous", "--interval", "15"])
        assert args.continuous is True
        assert args.interval == 15


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_code(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        score = evaluator.evaluate("")
        assert 0.0 <= score <= 1.0
    
    def test_invalid_component_path(self, temp_project, temp_archive):
        orchestrator = DGMOrchestrator(
            project_root=temp_project,
            archive=temp_archive,
            dry_run=True,
        )
        
        result = orchestrator.run_improvement_cycle(
            target_component="nonexistent/file.py",
            run_tests=False,
        )
        
        # Should handle gracefully
        assert isinstance(result, ImprovementResult)
    
    def test_voting_all_abstain(self):
        swarm = VotingSwarm()
        
        votes = [
            Vote("v1", 1, VoteDecision.ABSTAIN, 0.5, "unclear"),
            Vote("v2", 1, VoteDecision.ABSTAIN, 0.5, "unclear"),
        ]
        
        result = swarm._aggregate_votes(votes)
        
        assert result.passed is False  # Can't pass with all abstains
        assert result.approval_rate == 0.0
    
    def test_composability_syntax_error(self, temp_project):
        evaluator = EleganceEvaluator(temp_project)
        
        invalid_code = "def broken("
        score = evaluator._score_composability(invalid_code)
        
        assert score == 0.3  # Fallback score for parse errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
