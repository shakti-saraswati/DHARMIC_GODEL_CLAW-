"""
Tests for DGM Mutator - Claude-Powered Mutation Proposer
========================================================
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys

# Path setup handled by conftest.py - use same pattern as test_dgm.py
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dgm.mutator import (
    Mutator,
    MutationProposal,
    MutationError,
    SafetyViolationError,
    FORBIDDEN_PATTERNS,
    propose_mutation,
)
from dgm.archive import EvolutionEntry, FitnessScore


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def project_root(tmp_path):
    """Create a temporary project structure."""
    # Create src directory
    src_dir = tmp_path / "src" / "dgm"
    src_dir.mkdir(parents=True)
    
    # Create a sample component file
    (src_dir / "sample.py").write_text('''
"""Sample module for testing mutations."""

def add_numbers(a, b):
    """Add two numbers."""
    return a + b

def subtract_numbers(a, b):
    """Subtract b from a."""
    return a - b
''')
    
    # Create a .env file (should be forbidden)
    (tmp_path / ".env").write_text("SECRET_KEY=test123")
    
    return tmp_path


@pytest.fixture
def mutator(project_root):
    """Create a Mutator instance with test project root."""
    return Mutator(project_root=project_root)


@pytest.fixture
def parent_entry():
    """Create a sample parent evolution entry."""
    return EvolutionEntry(
        id="parent_001",
        timestamp="2024-02-04T12:00:00",
        component="src/dgm/sample.py",
        change_type="mutation",
        description="Previous improvement",
        fitness=FitnessScore(
            correctness=0.8,
            dharmic_alignment=0.75,
            elegance=0.6,
            efficiency=0.7,
            safety=0.9
        ),
        gates_passed=["ahimsa", "satya", "consent"],
        gates_failed=["elegance"],
        status="applied"
    )


@pytest.fixture
def mock_claude_response():
    """Sample Claude response for testing."""
    return json.dumps({
        "diff": """--- src/dgm/sample.py
+++ src/dgm/sample.py
@@ -5,6 +5,7 @@
 def add_numbers(a, b):
     \"\"\"Add two numbers.\"\"\"
+    # Type hint improvement
     return a + b
""",
        "rationale": "Added comment for clarity",
        "estimated_fitness": 0.82,
        "affected_files": ["src/dgm/sample.py"],
        "mutation_type": "enhance",
        "risk_level": "low",
        "reversible": True
    })


# =============================================================================
# Test 1: Forbidden File Detection
# =============================================================================

class TestForbiddenFileDetection:
    """Test that forbidden files are correctly identified."""
    
    def test_env_files_are_forbidden(self, mutator):
        """Test .env files are forbidden."""
        assert mutator.is_forbidden_file(".env") == True
        assert mutator.is_forbidden_file(".env.local") == True
        assert mutator.is_forbidden_file(".env.production") == True
        assert mutator.is_forbidden_file("config/.env.development") == True
    
    def test_secrets_files_are_forbidden(self, mutator):
        """Test secrets files are forbidden."""
        assert mutator.is_forbidden_file("secrets.yml") == True
        assert mutator.is_forbidden_file("secrets.yaml") == True
        assert mutator.is_forbidden_file("secret.yml") == True
        assert mutator.is_forbidden_file("config/secrets.yml") == True
    
    def test_credentials_are_forbidden(self, mutator):
        """Test credentials files are forbidden."""
        assert mutator.is_forbidden_file("credentials.json") == True
        assert mutator.is_forbidden_file("credential.json") == True
    
    def test_keys_are_forbidden(self, mutator):
        """Test key files are forbidden."""
        assert mutator.is_forbidden_file("server.pem") == True
        assert mutator.is_forbidden_file("private.key") == True
        assert mutator.is_forbidden_file("id_rsa") == True
        assert mutator.is_forbidden_file("id_rsa.pub") == True
    
    def test_normal_files_are_allowed(self, mutator):
        """Test normal code files are allowed."""
        assert mutator.is_forbidden_file("main.py") == False
        assert mutator.is_forbidden_file("src/utils.py") == False
        assert mutator.is_forbidden_file("tests/test_main.py") == False
        assert mutator.is_forbidden_file("config.py") == False
        assert mutator.is_forbidden_file("README.md") == False


# =============================================================================
# Test 2: MutationProposal Dataclass
# =============================================================================

class TestMutationProposal:
    """Test MutationProposal dataclass functionality."""
    
    def test_creation(self):
        """Test creating a MutationProposal."""
        proposal = MutationProposal(
            diff="--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new",
            rationale="Improved code quality",
            estimated_fitness=0.85,
            affected_files=["src/main.py"],
        )
        
        assert proposal.diff == "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new"
        assert proposal.rationale == "Improved code quality"
        assert proposal.estimated_fitness == 0.85
        assert proposal.affected_files == ["src/main.py"]
        assert proposal.mutation_type == "improve"  # default
        assert proposal.risk_level == "low"  # default
        assert proposal.reversible == True  # default
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        proposal = MutationProposal(
            diff="test diff",
            rationale="test rationale",
            estimated_fitness=0.75,
            affected_files=["file1.py", "file2.py"],
            mutation_type="refactor",
            risk_level="medium",
            reversible=False
        )
        
        d = proposal.to_dict()
        
        assert d["diff"] == "test diff"
        assert d["rationale"] == "test rationale"
        assert d["estimated_fitness"] == 0.75
        assert d["affected_files"] == ["file1.py", "file2.py"]
        assert d["mutation_type"] == "refactor"
        assert d["risk_level"] == "medium"
        assert d["reversible"] == False
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "diff": "some diff",
            "rationale": "some reason",
            "estimated_fitness": 0.9,
            "affected_files": ["test.py"],
            "mutation_type": "optimize",
            "risk_level": "high",
            "reversible": True
        }
        
        proposal = MutationProposal.from_dict(data)
        
        assert proposal.diff == "some diff"
        assert proposal.rationale == "some reason"
        assert proposal.estimated_fitness == 0.9
        assert proposal.affected_files == ["test.py"]
        assert proposal.mutation_type == "optimize"
        assert proposal.risk_level == "high"
        assert proposal.reversible == True
    
    def test_from_dict_with_missing_fields(self):
        """Test deserialization handles missing optional fields."""
        data = {
            "diff": "minimal diff",
            "rationale": "minimal reason",
        }
        
        proposal = MutationProposal.from_dict(data)
        
        assert proposal.diff == "minimal diff"
        assert proposal.estimated_fitness == 0.5  # default
        assert proposal.affected_files == []  # default
        assert proposal.mutation_type == "improve"  # default


# =============================================================================
# Test 3: Proposal Validation (Safety)
# =============================================================================

class TestProposalValidation:
    """Test that proposals are validated for safety."""
    
    def test_safe_proposal_passes(self, mutator):
        """Test that safe proposals pass validation."""
        proposal = MutationProposal(
            diff="--- src/main.py\n+++ src/main.py",
            rationale="Safe change",
            estimated_fitness=0.8,
            affected_files=["src/main.py", "src/utils.py"],
        )
        
        assert mutator.validate_proposal(proposal) == True
    
    def test_forbidden_file_in_affected_files_fails(self, mutator):
        """Test that proposals affecting forbidden files are rejected."""
        proposal = MutationProposal(
            diff="--- .env\n+++ .env",
            rationale="Update secrets",
            estimated_fitness=0.8,
            affected_files=[".env"],
        )
        
        with pytest.raises(SafetyViolationError) as exc_info:
            mutator.validate_proposal(proposal)
        
        assert ".env" in str(exc_info.value)
    
    def test_forbidden_pattern_in_diff_fails(self, mutator):
        """Test that diffs containing forbidden patterns are rejected."""
        proposal = MutationProposal(
            diff="--- config.py\n+++ config.py\n+api_key = 'secret'",
            rationale="Add config",
            estimated_fitness=0.7,
            affected_files=["config.py"],
        )
        
        with pytest.raises(SafetyViolationError) as exc_info:
            mutator.validate_proposal(proposal)
        
        assert "api_key" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()
    
    def test_multiple_safe_files_pass(self, mutator):
        """Test that multiple safe files pass validation."""
        proposal = MutationProposal(
            diff="multiple file diff",
            rationale="Refactor",
            estimated_fitness=0.85,
            affected_files=[
                "src/module1.py",
                "src/module2.py",
                "tests/test_module.py",
                "README.md"
            ],
        )
        
        assert mutator.validate_proposal(proposal) == True


# =============================================================================
# Test 4: Prompt Building
# =============================================================================

class TestPromptBuilding:
    """Test prompt construction for Claude."""
    
    def test_prompt_includes_component_content(self, mutator, project_root):
        """Test that prompt includes the component's code."""
        component_content = "def test(): pass"
        prompt = mutator._build_prompt(
            component="src/test.py",
            parent=None,
            context={},
            component_content=component_content
        )
        
        assert "def test(): pass" in prompt
        assert "src/test.py" in prompt
    
    def test_prompt_includes_parent_fitness(self, mutator, parent_entry):
        """Test that prompt includes parent fitness info."""
        prompt = mutator._build_prompt(
            component="src/test.py",
            parent=parent_entry,
            context={},
            component_content="# code"
        )
        
        assert "parent_001" in prompt
        assert "0.8" in prompt or "Correctness" in prompt  # fitness values
        assert "ahimsa" in prompt  # gates passed
        assert "elegance" in prompt  # gates failed
    
    def test_prompt_includes_recent_failures(self, mutator):
        """Test that prompt includes recent failures."""
        context = {
            "recent_failures": [
                "Test test_auth failed: AssertionError",
                "Gate ahimsa failed: potential harm detected",
            ]
        }
        
        prompt = mutator._build_prompt(
            component="src/test.py",
            parent=None,
            context=context,
            component_content="# code"
        )
        
        assert "Recent Failures" in prompt
        assert "test_auth" in prompt
        assert "ahimsa" in prompt
    
    def test_prompt_includes_telos(self, mutator):
        """Test that prompt includes telos alignment."""
        context = {
            "telos": "This system exists to help humans learn programming safely."
        }
        
        prompt = mutator._build_prompt(
            component="src/test.py",
            parent=None,
            context=context,
            component_content="# code"
        )
        
        assert "Telos" in prompt
        assert "help humans learn programming safely" in prompt
    
    def test_prompt_includes_focus(self, mutator):
        """Test that prompt includes focus area."""
        context = {"focus": "improve error handling"}
        
        prompt = mutator._build_prompt(
            component="src/test.py",
            parent=None,
            context=context,
            component_content="# code"
        )
        
        assert "improve error handling" in prompt


# =============================================================================
# Test 5: Response Parsing
# =============================================================================

class TestResponseParsing:
    """Test parsing of Claude's responses."""
    
    def test_parse_json_response(self, mutator):
        """Test parsing a clean JSON response."""
        response = json.dumps({
            "diff": "test diff",
            "rationale": "test reason",
            "estimated_fitness": 0.85,
            "affected_files": ["file.py"],
            "mutation_type": "fix",
            "risk_level": "low",
            "reversible": True
        })
        
        proposal = mutator._parse_response(response)
        
        assert proposal.diff == "test diff"
        assert proposal.rationale == "test reason"
        assert proposal.estimated_fitness == 0.85
        assert proposal.affected_files == ["file.py"]
        assert proposal.mutation_type == "fix"
    
    def test_parse_markdown_wrapped_json(self, mutator):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = """
Here's my proposal:

```json
{
    "diff": "wrapped diff",
    "rationale": "wrapped reason",
    "estimated_fitness": 0.9,
    "affected_files": ["wrapped.py"],
    "mutation_type": "enhance",
    "risk_level": "medium",
    "reversible": false
}
```

This change will improve...
"""
        
        proposal = mutator._parse_response(response)
        
        assert proposal.diff == "wrapped diff"
        assert proposal.rationale == "wrapped reason"
        assert proposal.estimated_fitness == 0.9
        assert proposal.reversible == False
    
    def test_parse_invalid_json_raises_error(self, mutator):
        """Test that invalid JSON raises MutationError."""
        response = "This is not JSON at all"
        
        with pytest.raises(MutationError) as exc_info:
            mutator._parse_response(response)
        
        assert "Failed to parse" in str(exc_info.value)


# =============================================================================
# Test 6: Full Mutation Flow (Integration with mocks)
# =============================================================================

class TestMutationFlow:
    """Test the full mutation proposal flow."""
    
    @patch.object(Mutator, '_call_claude')
    def test_propose_mutation_success(
        self, mock_claude, mutator, project_root, parent_entry, mock_claude_response
    ):
        """Test successful mutation proposal."""
        mock_claude.return_value = mock_claude_response
        
        proposal = mutator.propose_mutation(
            component="src/dgm/sample.py",
            parent=parent_entry,
            context={"focus": "improve readability"}
        )
        
        assert proposal is not None
        assert proposal.diff != ""
        assert proposal.estimated_fitness > 0
        assert "src/dgm/sample.py" in proposal.affected_files
        mock_claude.assert_called_once()
    
    @patch.object(Mutator, '_call_claude')
    def test_propose_mutation_rejects_forbidden_component(
        self, mock_claude, mutator
    ):
        """Test that proposing mutation on forbidden file is rejected."""
        with pytest.raises(SafetyViolationError):
            mutator.propose_mutation(
                component=".env",
                parent=None,
                context={}
            )
        
        # Claude should never be called for forbidden files
        mock_claude.assert_not_called()
    
    @patch.object(Mutator, '_call_claude')
    def test_propose_mutation_validates_response(
        self, mock_claude, mutator, project_root
    ):
        """Test that response is validated for safety."""
        # Claude returns a proposal that affects a forbidden file
        mock_claude.return_value = json.dumps({
            "diff": "bad diff",
            "rationale": "bad reason",
            "estimated_fitness": 0.8,
            "affected_files": [".env.local"],  # Forbidden!
            "mutation_type": "fix",
            "risk_level": "high",
            "reversible": True
        })
        
        with pytest.raises(SafetyViolationError):
            mutator.propose_mutation(
                component="src/dgm/sample.py",
                parent=None,
                context={}
            )
    
    def test_propose_mutation_nonexistent_component(self, mutator):
        """Test error when component doesn't exist."""
        with pytest.raises(MutationError) as exc_info:
            mutator.propose_mutation(
                component="src/nonexistent.py",
                parent=None,
                context={}
            )
        
        assert "not found" in str(exc_info.value)


# =============================================================================
# Test 7: Multi-Component Mutation
# =============================================================================

class TestMultiMutation:
    """Test proposing mutations for multiple components."""
    
    @patch.object(Mutator, '_call_claude')
    def test_propose_multi_mutation(
        self, mock_claude, mutator, project_root, mock_claude_response
    ):
        """Test proposing mutations for multiple components."""
        # Create another component
        (project_root / "src" / "dgm" / "other.py").write_text("# other code")
        
        mock_claude.return_value = mock_claude_response
        
        proposals = mutator.propose_multi_mutation(
            components=["src/dgm/sample.py", "src/dgm/other.py"],
            parent=None,
            context={}
        )
        
        assert len(proposals) == 2
        assert mock_claude.call_count == 2
    
    @patch.object(Mutator, '_call_claude')
    def test_multi_mutation_skips_forbidden(
        self, mock_claude, mutator, project_root, mock_claude_response
    ):
        """Test that multi-mutation skips forbidden files."""
        mock_claude.return_value = mock_claude_response
        
        proposals = mutator.propose_multi_mutation(
            components=["src/dgm/sample.py", ".env"],  # .env is forbidden
            parent=None,
            context={}
        )
        
        assert len(proposals) == 1  # Only sample.py processed
        mock_claude.call_count == 1


# =============================================================================
# Test 8: Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling in mutator."""
    
    @patch('subprocess.run')
    def test_claude_timeout_raises_error(self, mock_run, mutator, project_root):
        """Test that Claude timeout is handled."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=120)
        
        with pytest.raises(MutationError) as exc_info:
            mutator.propose_mutation(
                component="src/dgm/sample.py",
                parent=None,
                context={}
            )
        
        assert "timed out" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_claude_not_found_raises_error(self, mock_run, mutator, project_root):
        """Test that missing clawdbot is handled."""
        mock_run.side_effect = FileNotFoundError("clawdbot not found")
        
        with pytest.raises(MutationError) as exc_info:
            mutator.propose_mutation(
                component="src/dgm/sample.py",
                parent=None,
                context={}
            )
        
        assert "not found" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_claude_error_raises_mutation_error(self, mock_run, mutator, project_root):
        """Test that Claude errors are propagated."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr="API rate limit exceeded",
            stdout=""
        )
        
        with pytest.raises(MutationError) as exc_info:
            mutator.propose_mutation(
                component="src/dgm/sample.py",
                parent=None,
                context={}
            )
        
        assert "failed" in str(exc_info.value).lower()


# =============================================================================
# Test 9: Convenience Function
# =============================================================================

class TestConvenienceFunction:
    """Test the convenience propose_mutation function."""
    
    @patch.object(Mutator, 'propose_mutation')
    def test_convenience_function(self, mock_propose, project_root):
        """Test the module-level convenience function."""
        mock_propose.return_value = MutationProposal(
            diff="convenience diff",
            rationale="convenience reason",
            estimated_fitness=0.8,
            affected_files=["test.py"]
        )
        
        result = propose_mutation(
            component="test.py",
            parent=None,
            context={"focus": "test"},
            project_root=project_root
        )
        
        assert result.diff == "convenience diff"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
