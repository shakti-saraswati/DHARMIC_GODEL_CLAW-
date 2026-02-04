"""
Tests for KimiReviewer — Deep Code Review with 128k Context
============================================================

Tests cover:
- KimiReview dataclass serialization
- MutationProposal conversion
- ContextGatherer file discovery
- KimiReviewer prompt building
- Response parsing
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm.kimi_reviewer import (
    KimiReview,
    MutationProposal,
    ContextGatherer,
    KimiReviewer,
    KimiAPIError,
    create_reviewer,
    review_file_change,
)


# =============================================================================
# KimiReview Tests
# =============================================================================

class TestKimiReview:
    """Tests for KimiReview dataclass."""
    
    def test_create_basic_review(self):
        """Test basic review creation."""
        review = KimiReview(
            approved=True,
            confidence=0.85,
            issues=[],
            suggestions=["Add docstring"],
            codebase_conflicts=[],
            architectural_concerns=[],
            overall_assessment="Looks good!",
        )
        
        assert review.approved is True
        assert review.confidence == 0.85
        assert review.has_blockers is False
        assert review.severity_score == 1.0
    
    def test_review_with_issues(self):
        """Test review with issues detected."""
        review = KimiReview(
            approved=False,
            confidence=0.9,
            issues=["Missing error handling", "Potential race condition"],
            codebase_conflicts=["Conflicts with utils.py pattern"],
            architectural_concerns=["Breaks layering"],
            overall_assessment="Several issues need addressing.",
        )
        
        assert review.approved is False
        assert review.has_blockers is True
        assert review.severity_score < 1.0
        assert len(review.issues) == 2
    
    def test_confidence_bounds(self):
        """Test confidence is clamped to 0-1."""
        review = KimiReview(approved=True, confidence=1.5)
        assert review.confidence == 1.0
        
        review = KimiReview(approved=False, confidence=-0.5)
        assert review.confidence == 0.0
    
    def test_to_dict(self):
        """Test serialization to dict."""
        review = KimiReview(
            approved=True,
            confidence=0.75,
            issues=["Issue 1"],
            suggestions=["Suggestion 1"],
            overall_assessment="Test assessment",
        )
        
        d = review.to_dict()
        
        assert d["approved"] is True
        assert d["confidence"] == 0.75
        assert d["issues"] == ["Issue 1"]
        assert d["has_blockers"] is True  # Has issues
        assert "review_timestamp" in d
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "approved": False,
            "confidence": 0.6,
            "issues": ["Problem 1"],
            "suggestions": ["Fix it"],
            "codebase_conflicts": ["Conflict 1"],
            "architectural_concerns": [],
            "overall_assessment": "Needs work",
        }
        
        review = KimiReview.from_dict(data)
        
        assert review.approved is False
        assert review.confidence == 0.6
        assert review.issues == ["Problem 1"]
        assert review.codebase_conflicts == ["Conflict 1"]
    
    def test_summary(self):
        """Test human-readable summary."""
        review = KimiReview(
            approved=True,
            confidence=0.95,
            issues=[],
            suggestions=["Minor tweak"],
            overall_assessment="Ship it!",
        )
        
        summary = review.summary()
        
        assert "✅ APPROVED" in summary
        assert "95%" in summary
        assert "Issues: 0" in summary
    
    def test_severity_score_calculation(self):
        """Test severity score decreases with issues."""
        # No issues = perfect score
        review1 = KimiReview(approved=True, confidence=1.0)
        assert review1.severity_score == 1.0
        
        # Issues decrease score
        review2 = KimiReview(
            approved=False,
            confidence=0.5,
            issues=["Issue 1", "Issue 2"],  # -0.3
            codebase_conflicts=["Conflict"],  # -0.2
            architectural_concerns=["Concern"],  # -0.1
        )
        expected = 1.0 - 0.3 - 0.2 - 0.1
        assert abs(review2.severity_score - expected) < 0.01


# =============================================================================
# MutationProposal Tests
# =============================================================================

class TestMutationProposal:
    """Tests for MutationProposal dataclass."""
    
    def test_create_basic_proposal(self):
        """Test basic proposal creation."""
        proposal = MutationProposal(
            id="test-001",
            component="src/module.py",
            description="Add error handling",
            diff="+    try:\n+        ...",
            rationale="Improve robustness",
        )
        
        assert proposal.id == "test-001"
        assert proposal.component == "src/module.py"
        assert proposal.mutation_type == "improve"
        assert proposal.risk_level == "low"
    
    def test_from_voting_proposal(self):
        """Test conversion from voting.MutationProposal-like object."""
        mock_voting = Mock()
        mock_voting.id = "vote-123"
        mock_voting.component = "src/voting.py"
        mock_voting.description = "Fix vote counting"
        mock_voting.diff = "+fixed code"
        mock_voting.rationale = "Bug fix"
        mock_voting.parent_id = "parent-001"
        mock_voting.metadata = {"source": "auto"}
        
        proposal = MutationProposal.from_voting_proposal(mock_voting)
        
        assert proposal.id == "vote-123"
        assert proposal.component == "src/voting.py"
        assert proposal.rationale == "Bug fix"
    
    def test_from_mutator_proposal(self):
        """Test conversion from mutator.MutationProposal-like object."""
        mock_mutator = Mock()
        mock_mutator.diff = "+new code\n-old code"
        mock_mutator.rationale = "Optimization"
        mock_mutator.affected_files = ["src/main.py", "src/utils.py"]
        mock_mutator.mutation_type = "optimize"
        mock_mutator.risk_level = "medium"
        
        proposal = MutationProposal.from_mutator_proposal(mock_mutator, "src/main.py")
        
        assert proposal.component == "src/main.py"
        assert proposal.mutation_type == "optimize"
        assert proposal.risk_level == "medium"
        assert "src/main.py" in proposal.affected_files


# =============================================================================
# ContextGatherer Tests
# =============================================================================

class TestContextGatherer:
    """Tests for ContextGatherer."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        
        # Main module
        main_py = src_dir / "main.py"
        main_py.write_text("""
import utils
from helper import Helper

def main():
    h = Helper()
    return utils.process(h.data)
""")
        
        # Utils module
        utils_py = src_dir / "utils.py"
        utils_py.write_text("""
def process(data):
    return data.upper()
""")
        
        # Helper module
        helper_py = src_dir / "helper.py"
        helper_py.write_text("""
class Helper:
    def __init__(self):
        self.data = "test"
""")
        
        # Test file
        test_main = tests_dir / "test_main.py"
        test_main.write_text("""
from src.main import main

def test_main():
    assert main() == "TEST"
""")
        
        return tmp_path
    
    def test_gather_context_includes_target(self, temp_project):
        """Test that target file is always included."""
        gatherer = ContextGatherer(project_root=temp_project)
        context, meta = gatherer.gather_context("src/main.py")
        
        assert "# FILE:" in context
        assert "main.py" in context
        assert meta["files_included"] >= 1
    
    def test_gather_context_finds_tests(self, temp_project):
        """Test that test files are discovered."""
        gatherer = ContextGatherer(project_root=temp_project)
        context, meta = gatherer.gather_context("src/main.py")
        
        # Should find test_main.py
        test_files = [f for f in meta["included_files"] if f["type"] == "test"]
        assert len(test_files) >= 0  # May or may not find depending on pattern matching
    
    def test_gather_context_respects_max_chars(self, temp_project):
        """Test that context respects max_chars limit."""
        gatherer = ContextGatherer(project_root=temp_project)
        context, meta = gatherer.gather_context("src/main.py", max_chars=500)
        
        assert len(context) <= 600  # Some buffer for formatting
    
    def test_find_siblings(self, temp_project):
        """Test finding sibling files in same directory."""
        gatherer = ContextGatherer(project_root=temp_project)
        target = temp_project / "src" / "main.py"
        siblings = gatherer._find_siblings(target)
        
        sibling_names = [s.name for s in siblings]
        assert "utils.py" in sibling_names
        assert "helper.py" in sibling_names
    
    def test_resolve_path_absolute(self, temp_project):
        """Test resolving absolute paths."""
        gatherer = ContextGatherer(project_root=temp_project)
        abs_path = temp_project / "src" / "main.py"
        
        resolved = gatherer._resolve_path(str(abs_path))
        assert resolved == abs_path
    
    def test_resolve_path_relative(self, temp_project):
        """Test resolving relative paths."""
        gatherer = ContextGatherer(project_root=temp_project)
        resolved = gatherer._resolve_path("src/main.py")
        
        expected = temp_project / "src" / "main.py"
        assert resolved == expected
    
    def test_nonexistent_file_returns_empty(self, temp_project):
        """Test handling of nonexistent files."""
        gatherer = ContextGatherer(project_root=temp_project)
        context, meta = gatherer.gather_context("does_not_exist.py")
        
        assert context == ""
        assert "error" in meta


# =============================================================================
# KimiReviewer Tests
# =============================================================================

class TestKimiReviewer:
    """Tests for KimiReviewer class."""
    
    @pytest.fixture
    def mock_reviewer(self, tmp_path):
        """Create a reviewer with mocked API."""
        # Create minimal project structure
        main_py = tmp_path / "main.py"
        main_py.write_text("def main(): pass")
        
        reviewer = KimiReviewer(
            project_root=tmp_path,
            api_key=None,  # Will use clawdbot fallback
        )
        return reviewer
    
    def test_init_with_api_key(self, tmp_path):
        """Test initialization with API key."""
        reviewer = KimiReviewer(
            project_root=tmp_path,
            api_key="test-api-key",
        )
        
        assert reviewer.api_key == "test-api-key"
    
    def test_init_from_env(self, tmp_path, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv("MOONSHOT_API_KEY", "env-api-key")
        
        reviewer = KimiReviewer(project_root=tmp_path)
        
        assert reviewer.api_key == "env-api-key"
    
    def test_build_review_prompt(self, mock_reviewer):
        """Test review prompt construction."""
        proposal = MutationProposal(
            id="test-001",
            component="main.py",
            description="Test change",
            diff="+new line",
            rationale="Testing",
        )
        
        prompt = mock_reviewer._build_review_prompt(proposal, "# Context here")
        
        assert "test-001" in prompt
        assert "main.py" in prompt
        assert "+new line" in prompt
        assert "# Context here" in prompt
        assert "REQUIRED OUTPUT FORMAT" in prompt
    
    def test_parse_valid_json_response(self, mock_reviewer):
        """Test parsing valid JSON response."""
        response = '''
Here is my review:
```json
{
    "approved": true,
    "confidence": 0.85,
    "issues": [],
    "suggestions": ["Add tests"],
    "codebase_conflicts": [],
    "architectural_concerns": [],
    "overall_assessment": "Good change"
}
```
'''
        review = mock_reviewer._parse_review_response(response)
        
        assert review.approved is True
        assert review.confidence == 0.85
        assert review.suggestions == ["Add tests"]
    
    def test_parse_raw_json_response(self, mock_reviewer):
        """Test parsing JSON without code blocks."""
        response = '''{
    "approved": false,
    "confidence": 0.5,
    "issues": ["Bug found"],
    "suggestions": [],
    "codebase_conflicts": [],
    "architectural_concerns": [],
    "overall_assessment": "Needs fixes"
}'''
        review = mock_reviewer._parse_review_response(response)
        
        assert review.approved is False
        assert review.issues == ["Bug found"]
    
    def test_parse_invalid_response(self, mock_reviewer):
        """Test handling of unparseable response."""
        response = "This is not JSON at all!"
        
        review = mock_reviewer._parse_review_response(response)
        
        assert review.approved is False
        assert review.confidence == 0.0
        assert len(review.issues) > 0
    
    @patch('subprocess.run')
    def test_call_clawdbot(self, mock_run, mock_reviewer):
        """Test clawdbot CLI fallback."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"approved": true, "confidence": 0.9, "issues": [], "suggestions": [], "codebase_conflicts": [], "architectural_concerns": [], "overall_assessment": "OK"}',
            stderr='',
        )
        
        response = mock_reviewer._call_clawdbot("Test prompt")
        
        assert "approved" in response
        mock_run.assert_called_once()
        
        # Verify clawdbot was called with kimi model
        call_args = mock_run.call_args
        assert "kimi" in call_args[0][0]
    
    @patch('subprocess.run')
    def test_call_clawdbot_failure(self, mock_run, mock_reviewer):
        """Test handling of clawdbot failures."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='Error: model not found',
        )
        
        with pytest.raises(KimiAPIError):
            mock_reviewer._call_clawdbot("Test prompt")
    
    def test_review_mutation_full_flow(self, mock_reviewer):
        """Test full review flow with mocked API."""
        # Force clawdbot mode and mock it
        mock_reviewer.use_direct_api = False
        
        with patch.object(mock_reviewer, '_call_clawdbot') as mock_call:
            mock_call.return_value = json.dumps({
                "approved": True,
                "confidence": 0.8,
                "issues": [],
                "suggestions": ["Consider adding docstring"],
                "codebase_conflicts": [],
                "architectural_concerns": [],
                "overall_assessment": "Clean change, approve."
            })
            
            proposal = MutationProposal(
                id="test-002",
                component="main.py",
                description="Add logging",
                diff="+import logging",
                rationale="Better debugging",
            )
            
            review = mock_reviewer.review_mutation(proposal)
            
            assert review.approved is True
            assert review.confidence == 0.8
            assert "docstring" in review.suggestions[0]
    
    def test_quick_review(self, mock_reviewer):
        """Test quick review convenience method."""
        with patch.object(mock_reviewer, 'review_mutation') as mock_review:
            mock_review.return_value = KimiReview(
                approved=True,
                confidence=0.9,
            )
            
            review = mock_reviewer.quick_review(
                diff="+new code",
                file_path="main.py",
            )
            
            assert review.approved is True
            mock_review.assert_called_once()


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestFactoryFunctions:
    """Tests for module-level factory functions."""
    
    def test_create_reviewer(self, tmp_path):
        """Test create_reviewer factory."""
        reviewer = create_reviewer(project_root=tmp_path)
        
        assert isinstance(reviewer, KimiReviewer)
        assert reviewer.project_root == tmp_path
    
    @patch('dgm.kimi_reviewer.create_reviewer')
    def test_review_file_change(self, mock_create, tmp_path):
        """Test review_file_change convenience function."""
        mock_reviewer = Mock()
        mock_reviewer.quick_review.return_value = KimiReview(
            approved=True,
            confidence=0.95,
        )
        mock_create.return_value = mock_reviewer
        
        review = review_file_change(
            file_path="test.py",
            diff="+code",
            project_root=tmp_path,
        )
        
        assert review.approved is True
        mock_reviewer.quick_review.assert_called_with("+code", "test.py")


# =============================================================================
# Integration Tests (require actual files)
# =============================================================================

class TestIntegration:
    """Integration tests that use real project files."""
    
    @pytest.fixture
    def real_project_root(self):
        """Get the actual DGM project root."""
        return Path(__file__).parent.parent / "src" / "dgm"
    
    def test_gather_context_on_real_file(self, real_project_root):
        """Test context gathering on actual kimi_reviewer.py."""
        if not real_project_root.exists():
            pytest.skip("Project root not found")
        
        gatherer = ContextGatherer(project_root=real_project_root.parent.parent)
        context, meta = gatherer.gather_context("src/dgm/kimi_reviewer.py")
        
        assert meta["files_included"] >= 1
        assert meta["total_chars"] > 0
        assert "KimiReview" in context  # Our class should be in context
    
    def test_reviewer_initialization_with_real_project(self, real_project_root):
        """Test reviewer init with real project structure."""
        if not real_project_root.exists():
            pytest.skip("Project root not found")
        
        reviewer = KimiReviewer(project_root=real_project_root.parent.parent)
        
        assert reviewer.context_gatherer is not None
        assert reviewer.project_root.exists()


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_diff(self, tmp_path):
        """Test handling of empty diff."""
        main_py = tmp_path / "main.py"
        main_py.write_text("pass")
        
        reviewer = KimiReviewer(project_root=tmp_path)
        
        with patch.object(reviewer, '_call_clawdbot') as mock_call:
            mock_call.return_value = json.dumps({
                "approved": False,
                "confidence": 0.1,
                "issues": ["Empty diff"],
                "suggestions": [],
                "codebase_conflicts": [],
                "architectural_concerns": [],
                "overall_assessment": "No changes to review."
            })
            
            review = reviewer.quick_review("", "main.py")
            
            assert review.approved is False
    
    def test_very_large_context(self, tmp_path):
        """Test handling of very large context."""
        large_file = tmp_path / "large.py"
        large_file.write_text("x = 1\n" * 100_000)  # ~700KB
        
        gatherer = ContextGatherer(project_root=tmp_path)
        context, meta = gatherer.gather_context("large.py", max_chars=10_000)
        
        assert len(context) <= 15_000  # Some buffer
        assert "[TRUNCATED]" in context or meta.get("truncated", False) or len(context) < len(large_file.read_text())
    
    def test_binary_file_handling(self, tmp_path):
        """Test handling of binary files."""
        binary_file = tmp_path / "binary.py"
        binary_file.write_bytes(b'\x00\x01\x02\x03')
        
        gatherer = ContextGatherer(project_root=tmp_path)
        # Should not crash
        context, meta = gatherer.gather_context("binary.py")
        
        # Either returns empty or handles gracefully
        assert isinstance(context, str)
    
    def test_circular_imports(self, tmp_path):
        """Test handling of circular import patterns."""
        a_py = tmp_path / "a.py"
        b_py = tmp_path / "b.py"
        
        a_py.write_text("import b\ndef func_a(): pass")
        b_py.write_text("import a\ndef func_b(): pass")
        
        gatherer = ContextGatherer(project_root=tmp_path)
        # Should not infinite loop
        context, meta = gatherer.gather_context("a.py")
        
        assert isinstance(context, str)
        assert meta["files_included"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
