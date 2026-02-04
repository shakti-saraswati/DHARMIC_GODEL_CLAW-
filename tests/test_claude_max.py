"""
Tests for ClaudeMax - CLI model wrapper for Max subscription.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from claude_max_model import ClaudeMax, ModelResponse, Message


class TestMessage:
    """Test Message dataclass."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Test content")

        assert msg.role == "user"
        assert msg.content == "Test content"


class TestModelResponse:
    """Test ModelResponse dataclass."""

    def test_response_creation(self):
        """Test creating a response."""
        response = ModelResponse(content="Test response")

        assert response.content == "Test response"
        assert response.model == "claude-max"
        assert response.usage["input_tokens"] == 0
        assert response.usage["output_tokens"] == 0

    def test_response_with_custom_model(self):
        """Test response with custom model name."""
        response = ModelResponse(
            content="Test",
            model="claude-sonnet-4",
            usage={"input_tokens": 100, "output_tokens": 50}
        )

        assert response.model == "claude-sonnet-4"
        assert response.usage["input_tokens"] == 100


class TestClaudeMax:
    """Test ClaudeMax class."""

    @patch('subprocess.run')
    def test_initialization_success(self, mock_run):
        """Test successful initialization with CLI available."""
        # Mock successful version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        model = ClaudeMax(id="test-claude-max", timeout=60)

        assert model.id == "test-claude-max"
        assert model.timeout == 60
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_initialization_cli_not_found(self, mock_run):
        """Test initialization fails when CLI not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="Claude CLI not found"):
            ClaudeMax()

    @patch('subprocess.run')
    def test_initialization_cli_not_working(self, mock_run):
        """Test initialization fails when CLI not working."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Claude CLI not working"):
            ClaudeMax()

    @patch('subprocess.run')
    def test_invoke_simple_message(self, mock_run):
        """Test invoking with simple message."""
        # Mock version check
        version_result = Mock()
        version_result.returncode = 0

        # Mock invoke call
        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Test response from Claude"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        messages = [{"role": "user", "content": "Test message"}]

        response = model.invoke(messages)

        assert response.content == "Test response from Claude"
        assert response.model == "claude-max"
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_invoke_with_system_prompt(self, mock_run):
        """Test invoking with system prompt."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Response with system"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        messages = [{"role": "user", "content": "Test"}]
        system = "You are a helpful assistant"

        response = model.invoke(messages, system=system)

        # Verify system prompt was included
        call_args = mock_run.call_args_list[1]
        assert "System: You are a helpful assistant" in call_args[0][0][2]

    @patch('subprocess.run')
    def test_invoke_with_conversation_history(self, mock_run):
        """Test invoking with multi-turn conversation."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Continued response"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"}
        ]

        response = model.invoke(messages)

        # Verify all messages were included
        call_args = mock_run.call_args_list[1]
        prompt = call_args[0][0][2]
        assert "First message" in prompt
        assert "First response" in prompt
        assert "Second message" in prompt

    @patch('subprocess.run')
    def test_invoke_cli_error(self, mock_run):
        """Test handling of CLI errors."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 1
        invoke_result.stderr = "CLI error message"

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(RuntimeError, match="Claude CLI error"):
            model.invoke(messages)

    @patch('subprocess.run')
    def test_invoke_timeout(self, mock_run):
        """Test handling of CLI timeout."""
        version_result = Mock()
        version_result.returncode = 0

        mock_run.side_effect = [
            version_result,
            subprocess.TimeoutExpired("claude", 30)
        ]

        model = ClaudeMax(timeout=30)
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(RuntimeError, match="Claude CLI timeout"):
            model.invoke(messages)

    @patch('subprocess.run')
    def test_response_method_alias(self, mock_run):
        """Test that response() is an alias for invoke()."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Test response"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        messages = [{"role": "user", "content": "Test"}]

        response = model.response(messages)

        assert response.content == "Test response"

    @patch('subprocess.run')
    def test_chat_simple(self, mock_run):
        """Test simple chat interface."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Chat response"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        response = model.chat("Hello")

        assert response == "Chat response"

    @patch('subprocess.run')
    def test_chat_with_history(self, mock_run):
        """Test chat with conversation history."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Continued chat"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        history = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "First response"}
        ]

        response = model.chat("Second message", history=history)

        assert response == "Continued chat"
        # Verify history was included
        call_args = mock_run.call_args_list[1]
        prompt = call_args[0][0][2]
        assert "First" in prompt

    @patch('subprocess.run')
    def test_chat_with_system_prompt(self, mock_run):
        """Test chat with system prompt."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "System-aware response"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        model = ClaudeMax()
        response = model.chat(
            "Test message",
            system="Be concise"
        )

        # Verify system prompt was included
        call_args = mock_run.call_args_list[1]
        prompt = call_args[0][0][2]
        assert "System: Be concise" in prompt

    @patch('subprocess.run')
    def test_working_directory(self, mock_run):
        """Test that working directory is used in CLI calls."""
        version_result = Mock()
        version_result.returncode = 0

        invoke_result = Mock()
        invoke_result.returncode = 0
        invoke_result.stdout = "Response"
        invoke_result.stderr = ""

        mock_run.side_effect = [version_result, invoke_result]

        custom_dir = "/tmp/test_dir"
        model = ClaudeMax(working_dir=custom_dir)
        messages = [{"role": "user", "content": "Test"}]

        model.invoke(messages)

        # Check that cwd was set
        call_kwargs = mock_run.call_args_list[1][1]
        assert call_kwargs["cwd"] == custom_dir

    @patch('subprocess.run')
    def test_repr(self, mock_run):
        """Test string representation."""
        version_result = Mock()
        version_result.returncode = 0
        mock_run.return_value = version_result

        model = ClaudeMax(id="test-id", timeout=90)
        repr_str = repr(model)

        assert "test-id" in repr_str
        assert "90" in repr_str
