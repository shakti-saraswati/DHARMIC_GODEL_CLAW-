#!/usr/bin/env python3
"""
Tests for CodexProposer
=======================
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[2]))

from dgm.codex_proposer import (
    CodexProposal,
    CodexProposer,
    BridgeClient,
    OpenAIClient,
    BRIDGE_DIR,
)


class TestCodexProposal:
    """Tests for the CodexProposal dataclass."""
    
    def test_creation(self):
        """Test basic proposal creation."""
        proposal = CodexProposal(
            code="def hello(): return 'world'",
            diff="--- a/test.py\n+++ b/test.py",
            explanation="Made it better",
            estimated_tokens=100,
            model_used="gpt-4o-mini",
        )
        
        assert proposal.code == "def hello(): return 'world'"
        assert proposal.estimated_tokens == 100
        assert proposal.model_used == "gpt-4o-mini"
        assert proposal.confidence == 0.8  # default
    
    def test_to_dict(self):
        """Test serialization."""
        proposal = CodexProposal(
            code="x = 1",
            diff="diff",
            explanation="exp",
            estimated_tokens=50,
            model_used="gpt-4",
            component_path="test.py",
            constraints_applied=["no globals"],
            confidence=0.9,
        )
        
        d = proposal.to_dict()
        assert d["code"] == "x = 1"
        assert d["component_path"] == "test.py"
        assert d["constraints_applied"] == ["no globals"]
        assert d["confidence"] == 0.9
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "code": "y = 2",
            "diff": "diff2",
            "explanation": "exp2",
            "estimated_tokens": 75,
            "model_used": "gpt-4-turbo",
        }
        
        proposal = CodexProposal.from_dict(data)
        assert proposal.code == "y = 2"
        assert proposal.model_used == "gpt-4-turbo"
    
    def test_is_valid(self):
        """Test validity check."""
        valid = CodexProposal(
            code="x=1", diff="diff", explanation="e",
            estimated_tokens=1, model_used="m"
        )
        assert valid.is_valid()
        
        empty_code = CodexProposal(
            code="", diff="diff", explanation="e",
            estimated_tokens=1, model_used="m"
        )
        assert not empty_code.is_valid()
        
        empty_diff = CodexProposal(
            code="x=1", diff="", explanation="e",
            estimated_tokens=1, model_used="m"
        )
        assert not empty_diff.is_valid()


class TestBridgeClient:
    """Tests for BridgeClient."""
    
    def test_availability_check_no_bridge(self):
        """Test availability when bridge doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = BridgeClient(bridge_dir=Path(tmpdir))
            # Bridge dir exists but no bridge_queue.py
            assert not client.available
    
    def test_availability_with_mock_bridge(self):
        """Test availability when bridge exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge_dir = Path(tmpdir)
            
            # Create mock bridge_queue.py
            queue_code = '''
def enqueue_task(**kwargs): return {"id": "test123"}
def init_dirs(): pass
'''
            (bridge_dir / "bridge_queue.py").write_text(queue_code)
            
            client = BridgeClient(bridge_dir=bridge_dir)
            assert client.available
    
    def test_real_bridge_availability(self):
        """Test against real bridge if it exists."""
        client = BridgeClient()
        
        if BRIDGE_DIR.exists() and (BRIDGE_DIR / "bridge_queue.py").exists():
            assert client.available
            print(f"Real bridge found at {BRIDGE_DIR}")
        else:
            print(f"No bridge at {BRIDGE_DIR}")


class TestOpenAIClient:
    """Tests for OpenAIClient."""
    
    def test_availability_no_key(self):
        """Test availability without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY if set
            os.environ.pop("OPENAI_API_KEY", None)
            client = OpenAIClient()
            assert not client.available
    
    def test_availability_with_key(self):
        """Test availability with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = OpenAIClient()
            assert client.available
    
    def test_model_selection(self):
        """Test model selection from env."""
        with patch.dict(os.environ, {"CODEX_MODEL": "gpt-4"}):
            client = OpenAIClient()
            assert client.model == "gpt-4"
        
        # Explicit override
        client = OpenAIClient(model="gpt-4o")
        assert client.model == "gpt-4o"


class TestCodexProposer:
    """Tests for CodexProposer."""
    
    @pytest.fixture
    def temp_component(self):
        """Create a temporary component file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write('''
def calculate(a, b):
    """Add two numbers."""
    x = a + b
    return x
''')
            yield f.name
        os.unlink(f.name)
    
    def test_dry_run_mode(self, temp_component):
        """Test dry run doesn't call APIs."""
        proposer = CodexProposer(dry_run=True)
        
        proposal = proposer.propose_improvement(
            component=temp_component,
            analysis="Add type hints",
            constraints=["Python 3.9+"],
        )
        
        assert "[DRY-RUN]" in proposal.explanation
        assert proposal.confidence == 0.0
        assert proposal.component_path == temp_component
    
    def test_prompt_building(self):
        """Test prompt construction."""
        proposer = CodexProposer(dry_run=True)
        
        code = '''def calculate(a, b):
    """Add two numbers."""
    x = a + b
    return x
'''
        prompt = proposer._build_prompt(
            code=code,
            analysis="Improve this function",
            constraints=["no globals", "max 20 lines"],
        )
        
        assert "def calculate" in prompt
        assert "Improve this function" in prompt
        assert "- no globals" in prompt
        assert "- max 20 lines" in prompt
    
    def test_response_parsing(self, temp_component):
        """Test parsing of Codex response."""
        proposer = CodexProposer(dry_run=True)
        
        original = Path(temp_component).read_text()
        
        mock_response = '''
Here's the improved code:

```python
def calculate(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

I added type hints and simplified the function.
'''
        
        proposal = proposer._parse_response(
            response=mock_response,
            original_code=original,
            component_path=temp_component,
            tokens_used=150,
        )
        
        assert "def calculate(a: int, b: int)" in proposal.code
        assert proposal.estimated_tokens == 150
        assert "type hints" in proposal.explanation.lower()
        assert proposal.diff  # Should have a diff
    
    def test_diff_generation(self):
        """Test unified diff generation."""
        proposer = CodexProposer(dry_run=True)
        
        original = "def f():\n    return 1\n"
        proposed = "def f() -> int:\n    return 1\n"
        
        diff = proposer._generate_diff(original, proposed, "test.py")
        
        assert "--- a/test.py" in diff
        assert "+++ b/test.py" in diff
        assert "-def f():" in diff
        assert "+def f() -> int:" in diff
    
    def test_batch_dry_run(self, temp_component):
        """Test batch mode in dry run."""
        proposer = CodexProposer(dry_run=True)
        
        # Create second temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f2:
            f2.write("def other(): pass\n")
            temp2 = f2.name
        
        try:
            proposals = proposer.propose_batch(
                components=[temp_component, temp2],
                analysis="Add docstrings",
            )
            
            assert len(proposals) == 2
            assert all("[DRY-RUN]" in p.explanation for p in proposals)
        finally:
            os.unlink(temp2)
    
    def test_file_not_found(self):
        """Test handling of missing component."""
        proposer = CodexProposer(dry_run=True)
        
        with pytest.raises(FileNotFoundError):
            proposer.propose_improvement(
                component="/nonexistent/file.py",
                analysis="test",
            )
    
    @patch("dgm.codex_proposer.OpenAIClient")
    def test_api_call_flow(self, mock_openai_class, temp_component):
        """Test API call flow with mocked client."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.available = True
        mock_client.complete.return_value = (
            "```python\ndef calculate(a, b): return a + b\n```\nSimplified.",
            100,
        )
        mock_openai_class.return_value = mock_client
        
        proposer = CodexProposer(use_bridge=False, model="gpt-4o-mini")
        proposer.openai = mock_client
        
        proposal = proposer.propose_improvement(
            component=temp_component,
            analysis="Simplify",
        )
        
        assert mock_client.complete.called
        assert proposal.code
        assert "Simplified" in proposal.explanation


class TestIntegration:
    """Integration tests (require real API or bridge)."""
    
    @pytest.fixture
    def real_component(self):
        """Use a real component from the project."""
        # Use this test file itself as a component
        return str(Path(__file__))
    
    @pytest.mark.skip(reason="Requires real API call - run manually")
    def test_real_api_call(self, real_component):
        """Test with real OpenAI API (run manually with pytest -k test_real_api_call --runxfail)."""
        proposer = CodexProposer(use_bridge=False)
        
        proposal = proposer.propose_improvement(
            component=real_component,
            analysis="Suggest one small improvement to test organization",
            constraints=["minimal changes", "don't change test names"],
        )
        
        assert proposal.code or proposal.explanation
        assert proposal.model_used
        print(f"Tokens used: {proposal.estimated_tokens}")
        print(f"Model: {proposal.model_used}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
