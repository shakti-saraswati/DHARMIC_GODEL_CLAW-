#!/usr/bin/env python3
"""
Tests for the VotingSwarm consensus mechanism.

Tests cover:
- Individual reviewer behavior
- VotingSwarm orchestration
- Diversity enforcement
- Consensus thresholds
- Edge cases
"""
import asyncio
import pytest
from collections import Counter
from unittest.mock import AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm.voting import (
    MutationProposal,
    Vote,
    VoteResult,
    ReviewerType,
    VotingSwarm,
    SecurityReviewer,
    EleganceReviewer,
    DharmicReviewer,
    PerformanceReviewer,
    CorrectnessReviewer,
    MinimalChangeReviewer,
    TestReviewer,
    ArchitectureReviewer,
    vote_on_proposal,
    create_proposal,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def safe_proposal():
    """A proposal that should pass all reviewers."""
    return create_proposal(
        component="src/utils/helpers.py",
        description="Add helper function for string formatting",
        diff='''
+def format_name(first: str, last: str) -> str:
+    """Format a full name from first and last name.
+    
+    Args:
+        first: First name
+        last: Last name
+        
+    Returns:
+        Formatted full name
+    """
+    if not first or not last:
+        return ""
+    return f"{first.strip()} {last.strip()}"
''',
        rationale="Improve code clarity by adding a reusable formatting helper",
    )


@pytest.fixture
def dangerous_proposal():
    """A proposal with security issues."""
    return create_proposal(
        component="src/core/executor.py",
        description="Add dynamic code execution",
        diff='''
+def run_user_code(code: str):
+    exec(code)
+    eval(input("Enter expression: "))
''',
        rationale="Allow users to run custom code",
    )


@pytest.fixture
def large_proposal():
    """A proposal with too many changes."""
    # Generate 600 lines of changes
    lines = ["+line_{i} = {i}" for i in range(600)]
    diff = "\n".join(lines)
    return create_proposal(
        component="src/big_module.py",
        description="Major refactor",
        diff=diff,
        rationale="Improve performance across the board",
    )


@pytest.fixture
def performance_issue_proposal():
    """A proposal with performance concerns."""
    return create_proposal(
        component="src/processor.py",
        description="Process items",
        diff='''
+def process_all(items):
+    result = []
+    for item in items:
+        for sub in item.children:
+            for detail in sub.details:
+                for x in detail.values:
+                    result.append(x)
+    while True:
+        pass
''',
        rationale="Process nested data",
    )


# =============================================================================
# MutationProposal Tests
# =============================================================================

class TestMutationProposal:
    """Tests for MutationProposal dataclass."""
    
    def test_create_proposal(self, safe_proposal):
        """Test basic proposal creation."""
        assert safe_proposal.id is not None
        assert safe_proposal.component == "src/utils/helpers.py"
        assert "format_name" in safe_proposal.diff
    
    def test_diff_lines_count(self, safe_proposal):
        """Test counting of changed lines."""
        lines = safe_proposal.diff_lines
        assert lines > 0
        # Count + lines in the diff
        expected = len([l for l in safe_proposal.diff.split('\n') 
                       if l.startswith('+') or l.startswith('-')])
        assert lines == expected
    
    def test_metadata_default(self):
        """Test that metadata defaults to empty dict."""
        proposal = create_proposal("test.py", "desc", "+code", "rationale")
        assert proposal.metadata == {}


# =============================================================================
# Vote Tests
# =============================================================================

class TestVote:
    """Tests for Vote dataclass."""
    
    def test_vote_creation(self):
        """Test basic vote creation."""
        vote = Vote(
            reviewer_type=ReviewerType.SECURITY,
            reviewer_id="security_1",
            approve=True,
            confidence=0.9,
            rationale="All good",
        )
        assert vote.approve is True
        assert vote.confidence == 0.9
    
    def test_confidence_clamping_high(self):
        """Test that confidence is clamped to 1.0 max."""
        vote = Vote(
            reviewer_type=ReviewerType.SECURITY,
            reviewer_id="test",
            approve=True,
            confidence=1.5,
            rationale="test",
        )
        assert vote.confidence == 1.0
    
    def test_confidence_clamping_low(self):
        """Test that confidence is clamped to 0.0 min."""
        vote = Vote(
            reviewer_type=ReviewerType.SECURITY,
            reviewer_id="test",
            approve=False,
            confidence=-0.5,
            rationale="test",
        )
        assert vote.confidence == 0.0


# =============================================================================
# VoteResult Tests
# =============================================================================

class TestVoteResult:
    """Tests for VoteResult dataclass."""
    
    def test_result_summary_approved(self):
        """Test summary for approved result."""
        result = VoteResult(
            approved=True,
            total_votes=25,
            approval_ratio=0.88,
            diversity_score=0.85,
            dissenting_opinions=["Minor concern"],
        )
        summary = result.summary()
        assert "APPROVED" in summary
        assert "25" in summary
        assert "88" in summary  # approval percentage
    
    def test_result_summary_rejected(self):
        """Test summary for rejected result."""
        result = VoteResult(
            approved=False,
            total_votes=20,
            approval_ratio=0.6,
            diversity_score=0.5,
            dissenting_opinions=["Major issue"],
            rejection_reasons=["Approval too low"],
        )
        summary = result.summary()
        assert "REJECTED" in summary
        assert "Approval too low" in summary


# =============================================================================
# Individual Reviewer Tests
# =============================================================================

class TestSecurityReviewer:
    """Tests for SecurityReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_safe_code(self, safe_proposal):
        """Test that safe code is approved."""
        reviewer = SecurityReviewer("sec_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
        assert vote.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_rejects_eval(self, dangerous_proposal):
        """Test that eval() is flagged."""
        reviewer = SecurityReviewer("sec_1")
        vote = await reviewer.review(dangerous_proposal)
        assert vote.approve is False
        assert any("eval" in c.lower() for c in vote.concerns)
    
    @pytest.mark.asyncio
    async def test_rejects_exec(self, dangerous_proposal):
        """Test that exec() is flagged."""
        reviewer = SecurityReviewer("sec_1")
        vote = await reviewer.review(dangerous_proposal)
        assert vote.approve is False
        assert any("exec" in c.lower() for c in vote.concerns)


class TestEleganceReviewer:
    """Tests for EleganceReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_clean_code(self, safe_proposal):
        """Test that clean code is approved."""
        reviewer = EleganceReviewer("eleg_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_flags_long_lines(self):
        """Test that long lines are flagged."""
        proposal = create_proposal(
            "test.py", "test", 
            "+" + "x" * 150,  # Very long line
            "test"
        )
        reviewer = EleganceReviewer("eleg_1")
        vote = await reviewer.review(proposal)
        assert any("100 characters" in c for c in vote.concerns)


class TestDharmicReviewer:
    """Tests for DharmicReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_beneficial_change(self, safe_proposal):
        """Test that beneficial changes pass."""
        reviewer = DharmicReviewer("dh_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_flags_irreversible_operation(self):
        """Test that irreversible operations are flagged."""
        proposal = create_proposal(
            "cleanup.py", "Cleanup script",
            "+shutil.rmtree('/data')",
            "Clean old data to improve performance"
        )
        reviewer = DharmicReviewer("dh_1")
        vote = await reviewer.review(proposal)
        assert vote.approve is False
        assert any("rmtree" in c.lower() for c in vote.concerns)


class TestPerformanceReviewer:
    """Tests for PerformanceReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_efficient_code(self, safe_proposal):
        """Test that efficient code passes."""
        reviewer = PerformanceReviewer("perf_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_flags_nested_loops(self, performance_issue_proposal):
        """Test that nested loops are flagged."""
        reviewer = PerformanceReviewer("perf_1")
        vote = await reviewer.review(performance_issue_proposal)
        assert vote.approve is False
        assert any("loop" in c.lower() for c in vote.concerns)


class TestCorrectnessReviewer:
    """Tests for CorrectnessReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_correct_code(self, safe_proposal):
        """Test that correct code passes."""
        reviewer = CorrectnessReviewer("corr_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_flags_mutable_default(self):
        """Test that mutable default args are flagged."""
        proposal = create_proposal(
            "test.py", "test",
            "+def func(items=[]):\n+    items.append(1)",
            "test"
        )
        reviewer = CorrectnessReviewer("corr_1")
        vote = await reviewer.review(proposal)
        assert any("mutable default" in c.lower() for c in vote.concerns)


class TestMinimalChangeReviewer:
    """Tests for MinimalChangeReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_small_change(self, safe_proposal):
        """Test that small changes pass."""
        reviewer = MinimalChangeReviewer("min_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_rejects_large_change(self, large_proposal):
        """Test that large changes are rejected."""
        reviewer = MinimalChangeReviewer("min_1")
        vote = await reviewer.review(large_proposal)
        assert vote.approve is False
        assert any("large" in c.lower() or "too" in c.lower() for c in vote.concerns)


class TestTestReviewer:
    """Tests for TestReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_code_with_tests(self):
        """Test that code with tests passes."""
        proposal = create_proposal(
            "src/module.py", "Add feature with tests",
            '''
+def new_feature():
+    return 42
+
+def test_new_feature():
+    assert new_feature() == 42
''',
            "Add feature with proper test coverage"
        )
        reviewer = TestReviewer("test_1")
        vote = await reviewer.review(proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_flags_missing_tests(self):
        """Test that missing tests are flagged."""
        proposal = create_proposal(
            "src/module.py", "Add feature",
            "+def complex_feature():\n+    return calculate_something()",
            "Add important feature"
        )
        reviewer = TestReviewer("test_1")
        vote = await reviewer.review(proposal)
        assert any("test" in c.lower() for c in vote.concerns)


class TestArchitectureReviewer:
    """Tests for ArchitectureReviewer."""
    
    @pytest.mark.asyncio
    async def test_approves_good_architecture(self, safe_proposal):
        """Test that well-architected code passes."""
        reviewer = ArchitectureReviewer("arch_1")
        vote = await reviewer.review(safe_proposal)
        assert vote.approve is True
    
    @pytest.mark.asyncio
    async def test_flags_inverted_dependency(self):
        """Test that inverted dependencies are flagged."""
        proposal = create_proposal(
            "src/core/base.py", "Add DGM import to core",
            "+from src.dgm import something",
            "Need to use DGM in core"
        )
        reviewer = ArchitectureReviewer("arch_1")
        vote = await reviewer.review(proposal)
        assert any("dependency" in c.lower() for c in vote.concerns)


# =============================================================================
# VotingSwarm Tests
# =============================================================================

class TestVotingSwarm:
    """Tests for VotingSwarm orchestration."""
    
    def test_create_swarm(self):
        """Test swarm creation with defaults."""
        swarm = VotingSwarm()
        assert swarm.approval_threshold == 0.80
        assert swarm.diversity_threshold == 0.70
        assert swarm.max_votes_per_type == 5
    
    def test_create_swarm_custom(self):
        """Test swarm creation with custom thresholds."""
        swarm = VotingSwarm(
            approval_threshold=0.90,
            diversity_threshold=0.60,
            max_votes_per_type=3,
        )
        assert swarm.approval_threshold == 0.90
        assert swarm.diversity_threshold == 0.60
        assert swarm.max_votes_per_type == 3
    
    def test_spawn_reviewers_count(self):
        """Test that correct number of reviewers are spawned."""
        swarm = VotingSwarm()
        reviewers = swarm._spawn_reviewers(25)
        assert len(reviewers) == 25
    
    def test_spawn_reviewers_diversity(self):
        """Test that reviewers are diverse."""
        swarm = VotingSwarm(max_votes_per_type=5)
        reviewers = swarm._spawn_reviewers(25)
        
        type_counts = Counter(r.reviewer_type for r in reviewers)
        
        # No type should exceed max_votes_per_type
        for count in type_counts.values():
            assert count <= 5
        
        # Should use multiple types
        assert len(type_counts) >= 5  # At least 5 different types
    
    def test_diversity_score_uniform(self):
        """Test diversity score with uniform distribution."""
        swarm = VotingSwarm()
        # Create votes evenly distributed across all 8 types
        votes = []
        for rtype in ReviewerType:
            for j in range(3):
                votes.append(Vote(
                    reviewer_type=rtype,
                    reviewer_id=f"{rtype.value}_{j}",
                    approve=True,
                    confidence=0.8,
                    rationale="test"
                ))
        
        score = swarm._calculate_diversity_score(votes)
        assert score > 0.95  # Should be very high for perfect uniform distribution
    
    def test_diversity_score_skewed(self):
        """Test diversity score with skewed distribution."""
        swarm = VotingSwarm()
        # Create votes mostly from one type
        votes = []
        for i in range(20):
            votes.append(Vote(
                reviewer_type=ReviewerType.SECURITY,
                reviewer_id=f"sec_{i}",
                approve=True,
                confidence=0.8,
                rationale="test"
            ))
        # Add just a few from another type
        for i in range(5):
            votes.append(Vote(
                reviewer_type=ReviewerType.ELEGANCE,
                reviewer_id=f"eleg_{i}",
                approve=True,
                confidence=0.8,
                rationale="test"
            ))
        
        score = swarm._calculate_diversity_score(votes)
        assert score < 0.7  # Should be lower for skewed distribution
    
    @pytest.mark.asyncio
    async def test_collect_votes_safe_proposal(self, safe_proposal):
        """Test voting on a safe proposal."""
        swarm = VotingSwarm()
        result = await swarm.collect_votes(safe_proposal, required_votes=25)
        
        assert result.total_votes == 25
        assert result.diversity_score > 0.5
        # Safe proposal should have high approval
        assert result.approval_ratio > 0.6
    
    @pytest.mark.asyncio
    async def test_collect_votes_dangerous_proposal(self, dangerous_proposal):
        """Test voting on a dangerous proposal."""
        swarm = VotingSwarm()
        result = await swarm.collect_votes(dangerous_proposal, required_votes=25)
        
        assert result.total_votes == 25
        # Dangerous proposal should have low approval
        assert result.approval_ratio < 0.9
        assert len(result.dissenting_opinions) > 0
    
    @pytest.mark.asyncio
    async def test_quick_vote(self, safe_proposal):
        """Test quick vote with fewer reviewers."""
        swarm = VotingSwarm()
        result = await swarm.quick_vote(safe_proposal, required_votes=9)
        
        assert result.total_votes == 9
    
    @pytest.mark.asyncio
    async def test_rejection_reasons_low_approval(self):
        """Test that low approval is captured in rejection reasons."""
        # Create a proposal that will fail
        proposal = create_proposal(
            "src/core/base.py", "Bad change",
            "+exec(input())\n+eval(code)\n+os.system(cmd)\n+pickle.loads(data)",
            "Add features"
        )
        
        swarm = VotingSwarm(approval_threshold=0.95)  # Very high bar
        result = await swarm.collect_votes(proposal, required_votes=25)
        
        if result.approval_ratio < 0.95:
            assert not result.approved
            assert any("approval" in r.lower() for r in result.rejection_reasons)


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    @pytest.mark.asyncio
    async def test_vote_on_proposal(self, safe_proposal):
        """Test the vote_on_proposal convenience function."""
        result = await vote_on_proposal(safe_proposal, required_votes=9)
        assert result.total_votes == 9
        assert isinstance(result, VoteResult)
    
    def test_create_proposal(self):
        """Test the create_proposal convenience function."""
        proposal = create_proposal(
            component="test.py",
            description="Test description",
            diff="+new code",
            rationale="Test rationale",
        )
        assert proposal.component == "test.py"
        assert proposal.description == "Test description"
        assert proposal.id is not None  # Auto-generated


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete voting flows."""
    
    @pytest.mark.asyncio
    async def test_full_voting_flow_approval(self, safe_proposal):
        """Test complete voting flow for approval."""
        swarm = VotingSwarm(
            approval_threshold=0.50,  # Lower threshold for test
            diversity_threshold=0.40,
        )
        result = await swarm.collect_votes(safe_proposal, required_votes=25)
        
        # Check all components
        assert result.total_votes == 25
        assert len(result.votes) == 25
        assert result.diversity_score > 0.0
        assert isinstance(result.approved, bool)
        
        # Each vote should have required fields
        for vote in result.votes:
            assert isinstance(vote.reviewer_type, ReviewerType)
            assert isinstance(vote.approve, bool)
            assert 0.0 <= vote.confidence <= 1.0
            assert len(vote.rationale) > 0
    
    @pytest.mark.asyncio
    async def test_vote_type_distribution(self, safe_proposal):
        """Test that votes are distributed across types."""
        swarm = VotingSwarm(max_votes_per_type=4)
        result = await swarm.collect_votes(safe_proposal, required_votes=24)
        
        type_counts = Counter(v.reviewer_type for v in result.votes)
        
        # All 8 types should be represented
        assert len(type_counts) == 8
        
        # Each type should have exactly 3 votes (24 / 8)
        for count in type_counts.values():
            assert count == 3


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_diff(self):
        """Test handling of empty diff."""
        proposal = create_proposal("test.py", "Empty change", "", "No reason")
        swarm = VotingSwarm()
        result = await swarm.collect_votes(proposal, required_votes=9)
        assert result.total_votes == 9
    
    @pytest.mark.asyncio
    async def test_single_vote(self):
        """Test with minimum votes."""
        proposal = create_proposal("test.py", "test", "+x=1", "test")
        swarm = VotingSwarm()
        result = await swarm.collect_votes(proposal, required_votes=1)
        assert result.total_votes == 1
    
    def test_diversity_score_empty_votes(self):
        """Test diversity score with no votes."""
        swarm = VotingSwarm()
        score = swarm._calculate_diversity_score([])
        assert score == 0.0
    
    def test_diversity_score_single_vote(self):
        """Test diversity score with single vote."""
        swarm = VotingSwarm()
        votes = [Vote(
            reviewer_type=ReviewerType.SECURITY,
            reviewer_id="sec_1",
            approve=True,
            confidence=0.8,
            rationale="test"
        )]
        score = swarm._calculate_diversity_score(votes)
        assert score == 1.0  # Single vote = perfect diversity for its size


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
