"""
Claude Max Model - Uses Claude Code CLI for Max subscription.

This provides an Agno-compatible model interface that routes all
inference through the Claude Code CLI, using your Max subscription
instead of API credits.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass


@dataclass
class Message:
    """Simple message container."""
    role: str
    content: str


@dataclass
class ModelResponse:
    """Response from Claude Max."""
    content: str
    model: str = "claude-max"
    usage: Dict[str, int] = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {"input_tokens": 0, "output_tokens": 0}


class ClaudeMax:
    """
    Claude Max model that uses Claude Code CLI.

    Compatible with Agno's model interface for drop-in replacement.
    Uses your Max subscription instead of API credits.
    """

    def __init__(
        self,
        id: str = "claude-max",
        working_dir: Optional[str] = None,
        timeout: int = 120,
    ):
        self.id = id
        self.working_dir = working_dir or str(Path.home() / "DHARMIC_GODEL_CLAW")
        self.timeout = timeout
        self._verify_cli()

    def _verify_cli(self):
        """Verify Claude CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("Claude CLI not working")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

    def invoke(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Invoke Claude via CLI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            **kwargs: Additional args (ignored for CLI)

        Returns:
            ModelResponse with content
        """
        # Build the prompt from messages
        prompt_parts = []

        if system:
            prompt_parts.append(f"System: {system}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
            else:
                prompt_parts.append(f"User: {content}\n")

        full_prompt = "\n".join(prompt_parts)

        # Call Claude CLI
        try:
            result = subprocess.run(
                ["claude", "-p", full_prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_dir
            )

            if result.returncode == 0:
                return ModelResponse(content=result.stdout.strip())
            else:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude CLI timeout after {self.timeout}s")

    def response(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """Alias for invoke() - Agno compatibility."""
        return self.invoke(messages, system, **kwargs)

    def chat(
        self,
        message: str,
        system: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        Simple chat interface.

        Args:
            message: User message
            system: Optional system prompt
            history: Optional conversation history

        Returns:
            Response string
        """
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = self.invoke(messages, system, **kwargs)
        return response.content

    def __repr__(self):
        return f"ClaudeMax(id='{self.id}', timeout={self.timeout})"


# Convenience function
def create_claude_max(**kwargs) -> ClaudeMax:
    """Create a Claude Max model instance."""
    return ClaudeMax(**kwargs)


# Test
if __name__ == "__main__":
    print("Testing Claude Max model...")

    model = ClaudeMax()
    print(f"Model: {model}")

    response = model.chat(
        "What is 2 + 2? Reply with just the number.",
        system="You are a helpful assistant. Be brief."
    )
    print(f"Response: {response}")
