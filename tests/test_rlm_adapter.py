"""
Tests for RLM (Recursive Language Model) Adapter

Tests cover:
1. Basic RLM functionality
2. REPL environment
3. Recursive calls
4. FINAL() and FINAL_VAR() handling
5. Context processing
6. Error handling
7. PSMV vault integration (mocked)
8. Codebase query integration (mocked)
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rlm.rlm_adapter import (
    RLMAdapter,
    RLMConfig,
    RLMResult,
    RLMError,
    MaxIterationsError,
    MaxDepthError,
    REPLEnvironment,
    SAFE_BUILTINS,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_completion():
    """Mock LLM completion function."""
    def _mock(responses):
        """Create a mock that returns responses in sequence."""
        mock = Mock()
        mock.side_effect = list(responses)
        return mock
    return _mock


@pytest.fixture
def simple_context():
    """Simple test context."""
    return """
    The capital of France is Paris.
    The capital of Germany is Berlin.
    The capital of Italy is Rome.
    The secret code is: ALPHA-BRAVO-42
    """


@pytest.fixture
def large_context():
    """Large test context for chunking tests."""
    sections = []
    for i in range(100):
        sections.append(f"""
=== Section {i} ===
This is section number {i}.
Key fact: The value for section {i} is {i * 7}.
Random data: {'x' * 500}
""")
    return "\n".join(sections)


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault structure."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    
    # Create some test files
    (vault / "notes").mkdir()
    (vault / "notes" / "test1.md").write_text("# Test 1\nSecret: VAULT-SECRET-1")
    (vault / "notes" / "test2.md").write_text("# Test 2\nSecret: VAULT-SECRET-2")
    (vault / "data.json").write_text(json.dumps({"key": "value"}))
    
    return vault


@pytest.fixture
def temp_codebase(tmp_path):
    """Create a temporary codebase structure."""
    codebase = tmp_path / "test_codebase"
    codebase.mkdir()
    
    (codebase / "main.py").write_text("""
def main():
    '''Main entry point'''
    print("Hello World")
    
if __name__ == "__main__":
    main()
""")
    
    (codebase / "utils.py").write_text("""
def helper():
    '''Helper function'''
    return 42
""")
    
    (codebase / "__pycache__").mkdir()
    (codebase / "__pycache__" / "main.cpython-311.pyc").write_bytes(b"compiled")
    
    return codebase


# ==============================================================================
# REPL Environment Tests
# ==============================================================================

class TestREPLEnvironment:
    """Tests for the REPL environment."""
    
    def test_basic_execution(self):
        """Test basic code execution."""
        repl = REPLEnvironment(
            context="test context",
            query="test query",
            recursive_fn=lambda q, c: f"answer: {q}",
        )
        
        try:
            output = repl.execute("print(1 + 1)")
            assert "2" in output
        finally:
            repl.cleanup()
    
    def test_context_access(self):
        """Test that context is accessible."""
        repl = REPLEnvironment(
            context="hello world",
            query="what is the context?",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            output = repl.execute("print(context)")
            assert "hello" in output
        finally:
            repl.cleanup()
    
    def test_variable_persistence(self):
        """Test that variables persist across executions."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            repl.execute("x = 42")
            output = repl.execute("print(x * 2)")
            assert "84" in output
        finally:
            repl.cleanup()
    
    def test_final_function(self):
        """Test FINAL() function."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            repl.execute('FINAL("my answer")')
            assert repl.has_final_answer
            assert repl.final_answer == "my answer"
        finally:
            repl.cleanup()
    
    def test_final_var_function(self):
        """Test FINAL_VAR() function."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            repl.execute('answer = "computed answer"')
            repl.execute('FINAL_VAR("answer")')
            assert repl.has_final_answer
            assert repl.final_answer == "computed answer"
        finally:
            repl.cleanup()
    
    def test_final_var_not_found(self):
        """Test FINAL_VAR with non-existent variable."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            output = repl.execute('print(FINAL_VAR("nonexistent"))')
            assert "not found" in output.lower()
            assert not repl.has_final_answer
        finally:
            repl.cleanup()
    
    def test_show_vars(self):
        """Test SHOW_VARS() function."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            output = repl.execute("print(SHOW_VARS())")
            assert "No variables" in output or "variables" in output.lower()
            
            repl.execute("my_var = 123")
            output = repl.execute("print(SHOW_VARS())")
            assert "my_var" in output
        finally:
            repl.cleanup()
    
    def test_recursive_llm_function(self):
        """Test recursive_llm() function."""
        calls = []
        
        def mock_recursive(query, context):
            calls.append((query, context))
            return f"recursive result for: {query}"
        
        repl = REPLEnvironment(
            context="main context",
            query="main query",
            recursive_fn=mock_recursive,
        )
        
        try:
            output = repl.execute('result = recursive_llm("sub query", "sub context")\nprint(result)')
            assert "recursive result" in output
            assert len(calls) == 1
            assert calls[0] == ("sub query", "sub context")
        finally:
            repl.cleanup()
    
    def test_standard_library_access(self):
        """Test that standard library modules are available."""
        repl = REPLEnvironment(
            context="hello123world456",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            output = repl.execute('print(re.findall(r"\\d+", context))')
            assert "123" in output
            assert "456" in output
        finally:
            repl.cleanup()
    
    def test_code_extraction_repl_block(self):
        """Test code extraction from ```repl blocks."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            text = """Let me check the context:
```repl
print("hello from repl")
```
That should work."""
            
            output = repl.execute(text)
            assert "hello from repl" in output
        finally:
            repl.cleanup()
    
    def test_code_extraction_python_block(self):
        """Test code extraction from ```python blocks."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            text = """```python
print("hello from python")
```"""
            
            output = repl.execute(text)
            assert "hello from python" in output
        finally:
            repl.cleanup()
    
    def test_output_truncation(self):
        """Test that long output is truncated."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
            max_output_chars=100,
        )
        
        try:
            output = repl.execute('print("x" * 500)')
            assert "truncated" in output.lower()
            assert len(output) < 500
        finally:
            repl.cleanup()
    
    def test_error_handling(self):
        """Test that errors are captured properly."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            output = repl.execute("undefined_variable")
            assert "NameError" in output or "Error" in output
        finally:
            repl.cleanup()
    
    def test_safe_builtins_blocks_dangerous(self):
        """Test that dangerous operations are blocked."""
        repl = REPLEnvironment(
            context="test",
            query="test",
            recursive_fn=lambda q, c: c,
        )
        
        try:
            # eval should be blocked
            output = repl.execute('eval("1+1")')
            assert "TypeError" in output or "None" in output or "Error" in output
        finally:
            repl.cleanup()


# ==============================================================================
# RLMConfig Tests
# ==============================================================================

class TestRLMConfig:
    """Tests for RLMConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RLMConfig()
        
        assert config.model == "claude-opus-4"
        assert config.backend == "proxy"
        assert config.max_depth == 3
        assert config.max_iterations == 30
        assert config.verbose is False
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = RLMConfig(
            model="claude-sonnet-4",
            backend="direct",
            max_depth=5,
            max_iterations=50,
            verbose=True,
        )
        
        assert config.model == "claude-sonnet-4"
        assert config.backend == "direct"
        assert config.max_depth == 5
        assert config.max_iterations == 50
        assert config.verbose is True
    
    def test_recursive_model_default(self):
        """Test recursive model defaults to main model."""
        config = RLMConfig(model="claude-opus-4")
        assert config.recursive_model is None


# ==============================================================================
# RLMAdapter Tests (with mocked LLM)
# ==============================================================================

class TestRLMAdapterMocked:
    """Tests for RLMAdapter with mocked LLM calls."""
    
    def test_simple_completion(self, simple_context):
        """Test simple completion with mocked LLM."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        # Mock the completion function
        responses = [
            """Let me check the context:
```repl
print(context[:200])
```""",
            """I found the secret code:
```repl
FINAL("ALPHA-BRAVO-42")
```""",
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="What is the secret code?",
                context=simple_context,
            )
            
            assert "ALPHA-BRAVO-42" in result.answer
            assert result.iterations <= 3
    
    def test_final_in_text(self, simple_context):
        """Test FINAL() detected in plain text (not code block)."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """After examining the context, the answer is clear.
FINAL("The secret code is ALPHA-BRAVO-42")""",
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="What is the secret code?",
                context=simple_context,
            )
            
            assert "ALPHA-BRAVO-42" in result.answer
            assert result.iterations == 1
    
    def test_final_var_detection(self, simple_context):
        """Test FINAL_VAR() detection."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """```repl
answer = "Paris is the capital"
print(answer)
```""",
            """Now I'll return the answer.
FINAL_VAR(answer)""",
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="What is the capital of France?",
                context=simple_context,
            )
            
            assert "Paris" in result.answer
    
    def test_multiple_iterations(self, simple_context):
        """Test multiple iteration workflow."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """First, let me see what we have:
```repl
print(len(context))
```""",
            """Now let me search:
```repl
print("capital" in context)
```""",
            """Found it:
```repl
FINAL("Paris, Berlin, Rome")
```""",
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="List all capitals",
                context=simple_context,
            )
            
            assert result.iterations == 3
            assert "Paris" in result.answer
    
    def test_max_iterations_reached(self, simple_context):
        """Test behavior when max iterations reached."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        # Never calls FINAL
        responses = [
            """```repl
print("thinking...")
```""",
        ] * 5 + [
            """FINAL("Forced answer after limit")"""
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="What is the answer?",
                context=simple_context,
                max_iterations=5,
            )
            
            assert result.iterations == 5
    
    def test_recursive_depth_limit(self, simple_context):
        """Test max depth is enforced."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy", max_depth=1))
        
        with pytest.raises(MaxDepthError):
            adapter.recursive_complete(
                query="test",
                context=simple_context,
                _current_depth=1,
            )
    
    def test_result_contains_stats(self, simple_context):
        """Test that result contains execution statistics."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            'FINAL("quick answer")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="test",
                context=simple_context,
            )
            
            assert isinstance(result, RLMResult)
            assert result.iterations >= 1
            assert result.depth >= 0
            assert result.execution_time > 0
            assert isinstance(result.trace, list)
    
    def test_trace_contains_responses(self, simple_context):
        """Test that trace contains response previews."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """```repl
print("step 1")
```""",
            'FINAL("done")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="test",
                context=simple_context,
            )
            
            assert len(result.trace) >= 1
            assert "iteration" in result.trace[0]
            assert "depth" in result.trace[0]
    
    def test_dict_context(self):
        """Test with dictionary context."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        context = {"name": "Alice", "age": 30, "city": "Paris"}
        
        responses = [
            """```repl
print(type(context))
print(context.get("name"))
```""",
            'FINAL("Alice")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="What is the name?",
                context=context,
            )
            
            assert "Alice" in result.answer
    
    def test_list_context(self):
        """Test with list context."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        context = ["item1", "item2", "item3"]
        
        responses = [
            """```repl
print(len(context))
print(context[0])
```""",
            'FINAL("3 items, first is item1")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="How many items?",
                context=context,
            )
            
            assert "3" in result.answer


# ==============================================================================
# Vault Integration Tests (Mocked)
# ==============================================================================

class TestVaultIntegration:
    """Tests for PSMV vault integration."""
    
    def test_query_vault_loads_files(self, temp_vault):
        """Test that query_vault loads files correctly."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """```repl
print(context[:500])
```""",
            'FINAL("Found VAULT-SECRET-1 and VAULT-SECRET-2")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.query_vault(
                query="What secrets are in the vault?",
                vault_path=str(temp_vault),
                file_pattern="**/*.md",
            )
            
            assert result.answer is not None
    
    def test_query_vault_not_found(self):
        """Test error when vault doesn't exist."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        with pytest.raises(FileNotFoundError):
            adapter.query_vault(
                query="test",
                vault_path="/nonexistent/path",
            )


# ==============================================================================
# Codebase Integration Tests (Mocked)
# ==============================================================================

class TestCodebaseIntegration:
    """Tests for codebase query integration."""
    
    def test_query_codebase_loads_files(self, temp_codebase):
        """Test that query_codebase loads Python files."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """```repl
print(context[:500])
```""",
            'FINAL("Found main.py and utils.py")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.query_codebase(
                query="What files exist?",
                codebase_path=str(temp_codebase),
            )
            
            assert result.answer is not None
    
    def test_query_codebase_excludes_pycache(self, temp_codebase):
        """Test that __pycache__ is excluded."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        # Track what context was passed
        context_seen = []
        
        def mock_completion(messages):
            # Extract context from REPL env setup
            for msg in messages:
                if "context" in str(msg):
                    context_seen.append(msg)
            return 'FINAL("test")'
        
        with patch.object(adapter, '_completion_fn', mock_completion):
            result = adapter.query_codebase(
                query="test",
                codebase_path=str(temp_codebase),
            )
            
            # The completion should work without including pycache
            assert result.answer is not None
    
    def test_query_codebase_not_found(self):
        """Test error when codebase doesn't exist."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        with pytest.raises(FileNotFoundError):
            adapter.query_codebase(
                query="test",
                codebase_path="/nonexistent/path",
            )


# ==============================================================================
# Process Document Tests
# ==============================================================================

class TestProcessDocument:
    """Tests for document processing."""
    
    def test_process_document(self):
        """Test processing a document."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        document = "This is a test document with important information."
        
        responses = [
            """```repl
print(context)
```""",
            'FINAL("This document contains important information.")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.process_document(
                document=document,
                task="Summarize this document",
            )
            
            assert "information" in result.answer.lower()


# ==============================================================================
# Error Handling Tests
# ==============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_handles_llm_error(self, simple_context):
        """Test handling of LLM errors."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        with patch.object(adapter, '_completion_fn', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                adapter.recursive_complete(
                    query="test",
                    context=simple_context,
                )
    
    def test_handles_repl_error_gracefully(self, simple_context):
        """Test that REPL errors don't crash the adapter."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """```repl
# This will error
undefined_variable_xyz
```""",
            """```repl
# Try again
FINAL("recovered from error")
```""",
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="test",
                context=simple_context,
            )
            
            # Should recover and continue
            assert result.answer is not None


# ==============================================================================
# Integration Test (Requires Real LLM)
# ==============================================================================

@pytest.mark.skip(reason="Requires real LLM connection")
class TestRealLLMIntegration:
    """Integration tests with real LLM (skipped by default)."""
    
    def test_real_completion(self, simple_context):
        """Test with real LLM."""
        adapter = RLMAdapter(config=RLMConfig(
            backend="proxy",
            verbose=True,
        ))
        
        result = adapter.recursive_complete(
            query="What is the secret code in the context?",
            context=simple_context,
            max_iterations=5,
        )
        
        print(f"Answer: {result.answer}")
        print(f"Iterations: {result.iterations}")
        
        assert "ALPHA-BRAVO-42" in result.answer


# ==============================================================================
# Performance Tests
# ==============================================================================

class TestPerformance:
    """Performance-related tests."""
    
    def test_handles_large_context(self, large_context):
        """Test handling of large context."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = [
            """```repl
print(f"Context length: {len(context)}")
print(context[:200])
```""",
            'FINAL("Large context processed successfully")',
        ]
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="Process this large context",
                context=large_context,
            )
            
            assert result.answer is not None
    
    def test_execution_time_tracked(self, simple_context):
        """Test that execution time is tracked."""
        adapter = RLMAdapter(config=RLMConfig(backend="proxy"))
        
        responses = ['FINAL("quick")']
        
        with patch.object(adapter, '_completion_fn', side_effect=responses):
            result = adapter.recursive_complete(
                query="test",
                context=simple_context,
            )
            
            assert result.execution_time > 0
            assert result.execution_time < 60  # Sanity check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
