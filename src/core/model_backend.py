"""
Model Backend Interface

Unified interface for different model backends:
- Claude Max (via CLI using subscription)
- Anthropic API (via Agno)
- Other providers (Ollama, etc.)

This abstracts away the differences between CLI and API approaches.
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

# Security integration
try:
    from dharmic_security import ExecGuard
    EXEC_GUARD = ExecGuard(allowed_bins=["claude"])
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    EXEC_GUARD = None

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """Unified response format."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None

    def __str__(self):
        return self.content


class ModelBackend:
    """
    Abstract base for model backends.

    Subclasses implement specific providers (Max CLI, API, etc.)
    """

    def invoke(self, message: str, system: Optional[str] = None, **kwargs) -> ModelResponse:
        """
        Invoke the model with a message.

        Args:
            message: User message
            system: Optional system prompt
            **kwargs: Provider-specific options

        Returns:
            ModelResponse with content
        """
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> ModelResponse:
        """
        Multi-turn chat conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            **kwargs: Provider-specific options

        Returns:
            ModelResponse with content
        """
        # Default: just take the last message
        last_msg = messages[-1] if messages else {"content": ""}
        return self.invoke(last_msg["content"], system=system, **kwargs)


class ClaudeMaxBackend(ModelBackend):
    """
    Claude Max backend using CLI.

    Uses your Claude Max subscription via the claude CLI.
    No API credits consumed.
    """

    def __init__(
        self,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None,  # None = no timeout
    ):
        self.working_dir = working_dir or str(Path.home() / "DHARMIC_GODEL_CLAW")
        self.timeout = timeout  # None means no timeout
        self._verify_cli()

    def _verify_cli(self):
        """Verify Claude CLI is available."""
        try:
            cmd = ["claude", "--version"]
            if SECURITY_AVAILABLE and EXEC_GUARD:
                result = EXEC_GUARD.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
            if result.returncode != 0:
                raise RuntimeError("Claude CLI not working")
            logger.info("Claude CLI verified")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

    def invoke(self, message: str, system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Invoke Claude Max via CLI."""
        # Build full prompt
        prompt_parts = []
        if system:
            prompt_parts.append(f"System: {system}\n")
        prompt_parts.append(f"User: {message}")

        full_prompt = "\n".join(prompt_parts)

        try:
            cmd = ["claude", "-p", full_prompt]
            if SECURITY_AVAILABLE and EXEC_GUARD:
                result = EXEC_GUARD.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.working_dir
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.working_dir
                )

            if result.returncode == 0:
                return ModelResponse(
                    content=result.stdout.strip(),
                    model="claude-max",
                    provider="max"
                )
            else:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude CLI timeout after {self.timeout}s")
        except Exception as e:
            raise RuntimeError(f"Claude CLI error: {e}")

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Multi-turn chat via CLI."""
        # Build conversation prompt
        prompt_parts = []
        if system:
            prompt_parts.append(f"System: {system}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"User: {content}")

        full_prompt = "\n\n".join(prompt_parts)

        try:
            cmd = ["claude", "-p", full_prompt]
            if SECURITY_AVAILABLE and EXEC_GUARD:
                result = EXEC_GUARD.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.working_dir
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.working_dir
                )

            if result.returncode == 0:
                return ModelResponse(
                    content=result.stdout.strip(),
                    model="claude-max",
                    provider="max"
                )
            else:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude CLI timeout after {self.timeout}s")


class DirectAnthropicBackend(ModelBackend):
    """
    Direct Anthropic API backend.

    Uses anthropic SDK directly - no Agno, no CLI.
    For use when Claude CLI is unavailable (e.g., launchd environment).
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        import os
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed: pip install anthropic")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # Try loading from .env
            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                        break

        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not found in environment or .env")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"Direct Anthropic backend initialized with model {model}")

    def invoke(self, message: str, system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Invoke via Anthropic API directly."""
        messages = [{"role": "user", "content": message}]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system or "You are a helpful assistant.",
                messages=messages
            )

            content = response.content[0].text if response.content else ""

            return ModelResponse(
                content=content,
                model=self.model,
                provider="anthropic-direct",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Multi-turn chat via Anthropic API."""
        api_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                continue  # System goes in system param
            api_messages.append({
                "role": role if role in ("user", "assistant") else "user",
                "content": msg.get("content", "")
            })

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system or "You are a helpful assistant.",
                messages=api_messages
            )

            content = response.content[0].text if response.content else ""

            return ModelResponse(
                content=content,
                model=self.model,
                provider="anthropic-direct",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")


class ProxyBackend(ModelBackend):
    """
    Claude Max Proxy backend using OpenAI-compatible API.

    Uses claude-max-api-proxy running on localhost:3456.
    This routes through Claude CLI which uses Max subscription auth.
    Most reliable method - recommended default.
    """

    def __init__(
        self,
        model: str = "claude-opus-4",
        base_url: str = "http://localhost:3456/v1",
        api_key: str = "not-needed",
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed: pip install openai")

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.base_url = base_url
        logger.info(f"Proxy backend initialized: {base_url} with model {model}")

    def invoke(self, message: str, system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Invoke via proxy."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                messages=messages
            )

            content = response.choices[0].message.content if response.choices else ""

            return ModelResponse(
                content=content,
                model=self.model,
                provider="proxy",
                usage={
                    "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(response.usage, "completion_tokens", 0)
                } if response.usage else None
            )
        except Exception as e:
            raise RuntimeError(f"Proxy backend error: {e}")

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Multi-turn chat via proxy."""
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                continue  # Already handled
            api_messages.append({
                "role": role if role in ("user", "assistant") else "user",
                "content": msg.get("content", "")
            })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                messages=api_messages
            )

            content = response.choices[0].message.content if response.choices else ""

            return ModelResponse(
                content=content,
                model=self.model,
                provider="proxy",
                usage={
                    "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(response.usage, "completion_tokens", 0)
                } if response.usage else None
            )
        except Exception as e:
            raise RuntimeError(f"Proxy backend error: {e}")


class AgnoBackend(ModelBackend):
    """
    Agno-based backend for API providers.

    Supports Anthropic, Ollama, and other Agno-compatible providers.
    """

    def __init__(self, agent):
        """
        Initialize with an Agno Agent.

        Args:
            agent: Agno Agent instance with configured model
        """
        self.agent = agent
        self.provider = getattr(agent.model, 'id', 'unknown')

    def invoke(self, message: str, system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Invoke via Agno agent."""
        # Agno agents handle system prompts in instructions
        response = self.agent.run(message, stream=False)
        content = response.content if hasattr(response, 'content') else str(response)

        return ModelResponse(
            content=content,
            model=self.provider,
            provider="agno"
        )

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> ModelResponse:
        """Multi-turn chat via Agno agent."""
        # For multi-turn, just use the last message (Agno handles history internally)
        last_msg = messages[-1] if messages else {"content": ""}
        return self.invoke(last_msg["content"], system=system, **kwargs)


def create_backend(
    provider: str = "proxy",
    agent = None,
    **kwargs
) -> ModelBackend:
    """
    Create appropriate model backend.

    Args:
        provider: "proxy" (default) | "max" | "agno" | "api" | "direct" | "moonshot" | "ollama"
        agent: Agno agent (required for agno backends only)
        **kwargs: Backend-specific options

    Returns:
        ModelBackend instance
    """
    provider = provider.lower().strip()

    if provider in ("proxy", "claude-max-proxy"):
        # Proxy backend - uses claude-max-api-proxy on localhost:3456
        # Most reliable method - recommended default
        try:
            return ProxyBackend(**kwargs)
        except RuntimeError as e:
            logger.warning(f"Proxy backend unavailable ({e}), falling back to direct Anthropic API")
            provider = "direct"

    if provider in ("max", "claude-max", "subscription"):
        # Try Claude Max CLI, fall back to direct API if CLI unavailable
        try:
            return ClaudeMaxBackend(**kwargs)
        except (RuntimeError, FileNotFoundError) as e:
            logger.warning(f"Claude Max CLI unavailable ({e}), falling back to direct Anthropic API")
            # Fall through to direct backend
            provider = "direct"

    if provider in ("direct", "anthropic-direct"):
        # Direct Anthropic API - no CLI, no Agno needed
        try:
            return DirectAnthropicBackend(**kwargs)
        except RuntimeError as e:
            logger.error(f"Direct Anthropic backend failed: {e}")
            raise

    if provider in ("agno", "api", "anthropic"):
        if agent is None:
            # Try direct backend instead
            logger.warning("No Agno agent provided, trying direct Anthropic backend")
            try:
                return DirectAnthropicBackend(**kwargs)
            except RuntimeError:
                raise ValueError("Agno agent required for API backend and direct API unavailable")
        return AgnoBackend(agent)

    if provider in ("moonshot", "kimi", "ollama", "local"):
        if agent is None:
            raise ValueError(f"Agno agent required for provider: {provider}")
        return AgnoBackend(agent)

    else:
        raise ValueError(f"Unknown provider: {provider}")


# Convenience function for backward compatibility
def get_model_backend(model_provider: str, agent = None) -> ModelBackend:
    """Get appropriate backend for a provider."""
    return create_backend(provider=model_provider, agent=agent)
