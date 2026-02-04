"""
Tests for DGM Auto Push - Autonomous Git Commit & Push.

Uses mocking for git operations to enable safe testing.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm.auto_push import (
    AutoPusher,
    MutationProposal,
    CircuitResult,
    VoteRecord,
    CommitResult,
    PushResult,
    commit_and_push,
)
from dgm.archive import Archive, EvolutionEntry


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def temp_archive(tmp_path):
    """Create a temporary archive for testing."""
    archive_path = tmp_path / "test_archive.jsonl"
    return Archive(path=archive_path)


@pytest.fixture
def sample_proposal():
    """Create a sample mutation proposal."""
    return MutationProposal(
        mutation_id="mut_001_test",
        parent_id="mut_000_parent",
        component="src/dgm/archive.py",
        short_description="Improve archive performance",
        full_description="Optimized the get_lineage method for better O(n) traversal",
        changed_files=["src/dgm/archive.py"],
        diff="--- a/src/dgm/archive.py\n+++ b/src/dgm/archive.py\n@@ -1,3 +1,5 @@\n+# Optimized",
        old_fitness=0.75,
        new_fitness=0.82,
        model="claude-3-opus",
        agent_id="proposer_001",
    )


@pytest.fixture
def approved_circuit():
    """Create an approved circuit result."""
    return CircuitResult(
        approved=True,
        votes=[
            VoteRecord(voter_id="voter_1", approved=True, confidence=0.9, reasoning="Good change"),
            VoteRecord(voter_id="voter_2", approved=True, confidence=0.85, reasoning="Improves perf"),
            VoteRecord(voter_id="voter_3", approved=True, confidence=0.8, reasoning="LGTM"),
            VoteRecord(voter_id="voter_4", approved=False, confidence=0.6, reasoning="Needs tests"),
        ],
        approval_count=3,
        rejection_count=1,
        total_votes=4,
        gates_passed=["ahimsa", "satya", "vyavasthit", "witness"],
        gates_failed=["consent"],
        circuit_id="circuit_001",
        evaluation_time_ms=1250.5,
    )


@pytest.fixture
def rejected_circuit():
    """Create a rejected circuit result."""
    return CircuitResult(
        approved=False,
        votes=[
            VoteRecord(voter_id="voter_1", approved=False, confidence=0.9, reasoning="Breaks API"),
            VoteRecord(voter_id="voter_2", approved=False, confidence=0.85, reasoning="Too risky"),
        ],
        approval_count=0,
        rejection_count=2,
        total_votes=2,
        gates_passed=["satya"],
        gates_failed=["ahimsa", "consent"],
        circuit_id="circuit_002",
    )


@pytest.fixture
def pusher_dry_run(temp_archive, tmp_path):
    """Create an AutoPusher in dry-run mode."""
    return AutoPusher(
        project_root=tmp_path,
        archive=temp_archive,
        dry_run=True,
    )


# -----------------------------------------------------------------------------
# Test Data Classes
# -----------------------------------------------------------------------------

class TestMutationProposal:
    """Test MutationProposal dataclass."""
    
    def test_proposal_creation(self, sample_proposal):
        """Proposal creates with all fields."""
        assert sample_proposal.mutation_id == "mut_001_test"
        assert sample_proposal.parent_id == "mut_000_parent"
        assert sample_proposal.old_fitness == 0.75
        assert sample_proposal.new_fitness == 0.82
    
    def test_proposal_defaults(self):
        """Proposal has sensible defaults."""
        proposal = MutationProposal(mutation_id="test")
        assert proposal.changed_files == []
        assert proposal.diff == ""
        assert proposal.timestamp  # Should have auto-generated timestamp


class TestCircuitResult:
    """Test CircuitResult dataclass."""
    
    def test_approval_ratio(self, approved_circuit):
        """Approval ratio calculates correctly."""
        assert approved_circuit.approval_ratio == 75.0  # 3/4 = 75%
    
    def test_approval_ratio_zero_votes(self):
        """Approval ratio handles zero votes."""
        circuit = CircuitResult(approved=False, total_votes=0)
        assert circuit.approval_ratio == 0.0
    
    def test_gates_tracking(self, approved_circuit):
        """Gates are tracked correctly."""
        assert "ahimsa" in approved_circuit.gates_passed
        assert "consent" in approved_circuit.gates_failed


class TestVoteRecord:
    """Test VoteRecord dataclass."""
    
    def test_vote_creation(self):
        """Vote record creates properly."""
        vote = VoteRecord(
            voter_id="voter_test",
            approved=True,
            confidence=0.95,
            reasoning="Excellent change"
        )
        assert vote.voter_id == "voter_test"
        assert vote.approved is True
        assert vote.confidence == 0.95


# -----------------------------------------------------------------------------
# Test AutoPusher - Commit
# -----------------------------------------------------------------------------

class TestAutoPusherCommit:
    """Test commit_mutation functionality."""
    
    def test_commit_approved_mutation_dry_run(
        self, pusher_dry_run, sample_proposal, approved_circuit
    ):
        """Commit succeeds in dry-run mode for approved mutation."""
        result = pusher_dry_run.commit_mutation(sample_proposal, approved_circuit)
        
        assert result.committed is True
        assert result.dry_run is True
        assert result.commit_sha.startswith("DRY_RUN_")
        assert result.mutation_id == "mut_001_test"
        assert "[DGM]" in result.commit_message
    
    def test_commit_rejected_mutation_fails(
        self, pusher_dry_run, sample_proposal, rejected_circuit
    ):
        """Commit fails for rejected mutation."""
        result = pusher_dry_run.commit_mutation(sample_proposal, rejected_circuit)
        
        assert result.committed is False
        assert "circuit did not approve" in result.error
    
    def test_commit_message_format(
        self, pusher_dry_run, sample_proposal, approved_circuit
    ):
        """Commit message follows required format."""
        result = pusher_dry_run.commit_mutation(sample_proposal, approved_circuit)
        
        msg = result.commit_message
        
        # Check required elements
        assert "[DGM]" in msg
        assert "Mutation: mut_001_test" in msg
        assert "Parent: mut_000_parent" in msg
        assert "Fitness: 0.750 → 0.820" in msg
        assert "Votes: 3/4 (75.0%)" in msg
        assert "Reviewed-by: DGM Voting Swarm" in msg
        assert "Dharmic-gates:" in msg
        assert "ahimsa" in msg
    
    @patch("subprocess.run")
    def test_commit_live_mode(
        self, mock_run, temp_archive, tmp_path, sample_proposal, approved_circuit
    ):
        """Commit actually runs git commands in live mode."""
        # Setup mocks
        mock_run.return_value = Mock(
            returncode=0,
            stdout="abc123def456",
            stderr="",
        )
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            dry_run=False,
        )
        
        result = pusher.commit_mutation(sample_proposal, approved_circuit)
        
        assert result.committed is True
        assert result.dry_run is False
        # Should have called git add and git commit
        assert mock_run.call_count >= 2
    
    @patch("subprocess.run")
    def test_commit_handles_git_error(
        self, mock_run, temp_archive, tmp_path, sample_proposal, approved_circuit
    ):
        """Commit handles git errors gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="fatal: not a git repository"
        )
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            dry_run=False,
        )
        
        result = pusher.commit_mutation(sample_proposal, approved_circuit)
        
        assert result.committed is False
        assert "Git error" in result.error


# -----------------------------------------------------------------------------
# Test AutoPusher - Push
# -----------------------------------------------------------------------------

class TestAutoPusherPush:
    """Test push_if_ready functionality."""
    
    def test_push_dry_run_succeeds(self, pusher_dry_run, sample_proposal, approved_circuit):
        """Push succeeds in dry-run mode with passing checks."""
        commit_result = pusher_dry_run.commit_mutation(sample_proposal, approved_circuit)
        
        # Push to non-protected branch
        push_result = pusher_dry_run.push_if_ready(commit_result, branch="feature/test")
        
        assert push_result.pushed is True
        assert push_result.dry_run is True
        assert push_result.branch == "feature/test"
        assert push_result.archive_entry_id  # Should have logged to archive
    
    def test_push_fails_for_uncommitted(self, pusher_dry_run):
        """Push fails if commit wasn't successful."""
        failed_commit = CommitResult(
            committed=False,
            error="Previous error",
            dry_run=True,
        )
        
        push_result = pusher_dry_run.push_if_ready(failed_commit)
        
        assert push_result.pushed is False
        assert "commit was not successful" in push_result.error
    
    def test_push_fails_protected_branch(
        self, pusher_dry_run, sample_proposal, approved_circuit
    ):
        """Push fails for protected branches."""
        commit_result = pusher_dry_run.commit_mutation(sample_proposal, approved_circuit)
        
        # Try to push to protected branch
        push_result = pusher_dry_run.push_if_ready(commit_result, branch="main")
        
        assert push_result.pushed is False
        assert "branch_allowed" in push_result.safety_checks_passed
        assert push_result.safety_checks_passed["branch_allowed"] is False
    
    def test_push_custom_protected_branches(
        self, temp_archive, tmp_path, sample_proposal, approved_circuit
    ):
        """Custom protected branches are respected."""
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            protected_branches=["release", "staging"],
            dry_run=True,
        )
        
        commit_result = pusher.commit_mutation(sample_proposal, approved_circuit)
        
        # main should now be allowed
        push_result = pusher.push_if_ready(commit_result, branch="main")
        assert push_result.pushed is True
        
        # staging should be blocked
        push_result = pusher.push_if_ready(commit_result, branch="staging")
        assert push_result.pushed is False
    
    @patch("subprocess.run")
    def test_push_runs_tests(
        self, mock_run, temp_archive, tmp_path, sample_proposal, approved_circuit
    ):
        """Push runs tests as safety check."""
        # First call is test run, should pass
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            protected_branches=[],  # Allow all branches
            dry_run=False,
        )
        
        commit_result = CommitResult(
            committed=True,
            commit_sha="abc123",
            mutation_id="test",
            files_committed=["test.py"],
            dry_run=False,
        )
        
        push_result = pusher.push_if_ready(commit_result, branch="main")
        
        # Should have run pytest
        pytest_calls = [
            c for c in mock_run.call_args_list 
            if "pytest" in str(c)
        ]
        assert len(pytest_calls) >= 1
    
    @patch("subprocess.run")
    def test_push_fails_on_test_failure(
        self, mock_run, temp_archive, tmp_path, sample_proposal, approved_circuit
    ):
        """Push fails when tests fail."""
        # Tests fail
        mock_run.return_value = Mock(returncode=1, stdout="FAILED", stderr="")
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            protected_branches=[],
            dry_run=False,
        )
        
        commit_result = CommitResult(
            committed=True,
            commit_sha="abc123",
            mutation_id="test",
            files_committed=["test.py"],
            dry_run=False,
        )
        
        push_result = pusher.push_if_ready(commit_result, branch="feature")
        
        assert push_result.pushed is False
        assert push_result.safety_checks_passed["tests_pass"] is False


# -----------------------------------------------------------------------------
# Test Archive Integration
# -----------------------------------------------------------------------------

class TestArchiveIntegration:
    """Test archive logging and lineage tracking."""
    
    def test_push_logs_to_archive(
        self, pusher_dry_run, sample_proposal, approved_circuit
    ):
        """Successful push creates archive entry."""
        commit_result = pusher_dry_run.commit_mutation(sample_proposal, approved_circuit)
        push_result = pusher_dry_run.push_if_ready(commit_result, branch="feature/test")
        
        assert push_result.archive_entry_id
        
        # Verify entry exists in archive
        entry = pusher_dry_run.archive.get_entry(push_result.archive_entry_id)
        assert entry is not None
        assert entry.commit_hash == commit_result.commit_sha
    
    def test_archive_tracks_lineage(
        self, pusher_dry_run, approved_circuit
    ):
        """Archive maintains parent-child lineage."""
        # First mutation
        proposal1 = MutationProposal(
            mutation_id="gen_001",
            component="test.py",
            short_description="First gen",
            changed_files=["test.py"],
            old_fitness=0.5,
            new_fitness=0.6,
        )
        commit1 = pusher_dry_run.commit_mutation(proposal1, approved_circuit)
        push1 = pusher_dry_run.push_if_ready(commit1, branch="feature")
        
        # Second mutation with parent
        proposal2 = MutationProposal(
            mutation_id="gen_002",
            parent_id="gen_001",
            component="test.py",
            short_description="Second gen",
            changed_files=["test.py"],
            old_fitness=0.6,
            new_fitness=0.7,
        )
        commit2 = pusher_dry_run.commit_mutation(proposal2, approved_circuit)
        push2 = pusher_dry_run.push_if_ready(commit2, branch="feature")
        
        # Verify lineage in archive
        entry2 = pusher_dry_run.archive.get_entry(push2.archive_entry_id)
        assert entry2.parent_id == "gen_001"


# -----------------------------------------------------------------------------
# Test Environment Configuration
# -----------------------------------------------------------------------------

class TestEnvironmentConfig:
    """Test DRY_RUN environment variable handling."""
    
    @patch.dict("os.environ", {"DRY_RUN": "true"})
    def test_dry_run_from_env_true(self, temp_archive, tmp_path):
        """DRY_RUN=true enables dry-run."""
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
        )
        assert pusher.dry_run is True
    
    @patch.dict("os.environ", {"DRY_RUN": "false"})
    def test_dry_run_from_env_false(self, temp_archive, tmp_path):
        """DRY_RUN=false disables dry-run."""
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
        )
        assert pusher.dry_run is False
    
    @patch.dict("os.environ", {"DRY_RUN": "1"})
    def test_dry_run_from_env_1(self, temp_archive, tmp_path):
        """DRY_RUN=1 enables dry-run."""
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
        )
        assert pusher.dry_run is True
    
    def test_explicit_dry_run_overrides_env(self, temp_archive, tmp_path):
        """Explicit dry_run parameter overrides environment."""
        with patch.dict("os.environ", {"DRY_RUN": "true"}):
            pusher = AutoPusher(
                project_root=tmp_path,
                archive=temp_archive,
                dry_run=False,  # Explicit override
            )
            assert pusher.dry_run is False


# -----------------------------------------------------------------------------
# Test Convenience Function
# -----------------------------------------------------------------------------

class TestCommitAndPush:
    """Test the commit_and_push convenience function."""
    
    def test_commit_and_push_success(self, sample_proposal, approved_circuit):
        """commit_and_push works for approved mutations."""
        with patch.dict("os.environ", {"DRY_RUN": "true"}):
            result = commit_and_push(
                sample_proposal,
                approved_circuit,
                branch="feature/test",
            )
        
        assert result.pushed is True
        assert result.dry_run is True
    
    def test_commit_and_push_commit_fails(self, sample_proposal, rejected_circuit):
        """commit_and_push returns error when commit fails."""
        with patch.dict("os.environ", {"DRY_RUN": "true"}):
            result = commit_and_push(
                sample_proposal,
                rejected_circuit,
                branch="feature/test",
            )
        
        assert result.pushed is False
        assert "circuit did not approve" in result.error


# -----------------------------------------------------------------------------
# Test Safety Checks
# -----------------------------------------------------------------------------

class TestSafetyChecks:
    """Test individual safety check methods."""
    
    @patch("subprocess.run")
    def test_check_no_uncommitted_clean(
        self, mock_run, temp_archive, tmp_path
    ):
        """Clean working directory passes check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            dry_run=False,
        )
        
        result = pusher._check_no_uncommitted_changes(["test.py"])
        assert result is True
    
    @patch("subprocess.run")
    def test_check_no_uncommitted_with_allowed_changes(
        self, mock_run, temp_archive, tmp_path
    ):
        """Changes in allowed files pass check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" M test.py\n",  # Modified file in allowed list
            stderr="",
        )
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            dry_run=False,
        )
        
        result = pusher._check_no_uncommitted_changes(["test.py"])
        assert result is True
    
    @patch("subprocess.run")
    def test_check_no_uncommitted_with_outside_changes(
        self, mock_run, temp_archive, tmp_path
    ):
        """Changes outside allowed files fail check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" M test.py\n M other.py\n",  # other.py not in allowed
            stderr="",
        )
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            dry_run=False,
        )
        
        result = pusher._check_no_uncommitted_changes(["test.py"])
        assert result is False


# -----------------------------------------------------------------------------
# Test Strange Loop Witness Logging
# -----------------------------------------------------------------------------

class TestWitnessLogging:
    """Test the 'strange loop' witness logging behavior."""
    
    def test_commit_logs_witness_event(
        self, temp_archive, tmp_path, sample_proposal, approved_circuit, caplog
    ):
        """Commit logs a witness event for the strange loop."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            dry_run=True,
        )
        
        pusher.commit_mutation(sample_proposal, approved_circuit)
        
        # Check that logging occurred - look for commit-related logs
        log_messages = [r.message for r in caplog.records]
        assert any("commit" in msg.lower() or "dry run" in msg.lower() 
                   for msg in log_messages)
    
    @patch("subprocess.run")
    def test_push_logs_strange_loop_witness(
        self, mock_run, temp_archive, tmp_path, 
        sample_proposal, approved_circuit, caplog
    ):
        """Push logs the 'DGM pushed itself' strange loop event."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        pusher = AutoPusher(
            project_root=tmp_path,
            archive=temp_archive,
            protected_branches=[],
            dry_run=False,
        )
        
        commit_result = CommitResult(
            committed=True,
            commit_sha="abc123",
            mutation_id="test_loop",
            files_committed=["src/dgm/auto_push.py"],
            dry_run=False,
        )
        
        pusher.push_if_ready(commit_result, branch="feature")
        
        # Check that dharmic log was called - look for 'pushed itself' or 'strange loop'
        log_messages = [r.message for r in caplog.records]
        assert any("pushed" in msg.lower() or "strange" in msg.lower() 
                   for msg in log_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
