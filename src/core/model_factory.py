"""
Model factory for Dharmic Agent.

Selects provider/model from environment with safe defaults:
- DHARMIC_MODEL_PROVIDER: proxy | max | anthropic | ollama | moonshot
- Default is 'proxy' (claude-max-api-proxy on localhost:3456)

Proxy is most reliable - routes through Claude CLI using Max subscription.
"""

from dataclasses import dataclass
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelSpec:
    """Model specification with provider and model ID."""
    provider: str
    model_id: str


def resolve_model_spec(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
) -> ModelSpec:
    """
    Resolve provider/model from args + environment.

    Args:
        provider: Override provider (max, anthropic, ollama, moonshot)
        model_id: Override model ID

    Returns:
        ModelSpec with resolved provider and model_id
    """
    raw_provider = (provider or os.getenv("DHARMIC_MODEL_PROVIDER") or "").strip().lower()

    # DEFAULT TO PROXY (claude-max-api-proxy on localhost:3456)
    if not raw_provider:
        raw_provider = "proxy"

    if raw_provider in ("proxy", "claude-max-proxy"):
        resolved_provider = "proxy"
        resolved_model = model_id or "claude-opus-4"

    elif raw_provider in ("max", "claude-max", "subscription"):
        resolved_provider = "max"
        resolved_model = model_id or "claude-max"

    elif raw_provider in ("anthropic", "claude", "api"):
        resolved_provider = "anthropic"
        resolved_model = (
            model_id
            or os.getenv("DHARMIC_ANTHROPIC_MODEL")
            or os.getenv("ANTHROPIC_MODEL")
            or "claude-sonnet-4-20250514"
        )

    elif raw_provider in ("ollama", "local"):
        resolved_provider = "ollama"
        resolved_model = (
            model_id
            or os.getenv("DHARMIC_OLLAMA_MODEL")
            or "gemma3:4b"
        )

    elif raw_provider in ("moonshot", "kimi", "moon-shot"):
        resolved_provider = "moonshot"
        resolved_model = (
            model_id
            or os.getenv("DHARMIC_MOONSHOT_MODEL")
            or "kimi-k2.5"
        )

    else:
        raise ValueError(f"Unsupported provider: {raw_provider}")

    logger.info(f"Resolved model: {resolved_provider}/{resolved_model}")
    return ModelSpec(provider=resolved_provider, model_id=resolved_model)


def create_model(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
):
    """
    Create a model instance based on resolved spec.

    Note: For 'max' provider, this returns a ClaudeMax model that wraps
    the CLI. For other providers, returns Agno model instances.

    Args:
        provider: Model provider
        model_id: Model identifier

    Returns:
        Model instance compatible with Agno Agent

    Raises:
        RuntimeError: If required dependencies not available
        ValueError: If provider not supported
    """
    spec = resolve_model_spec(provider=provider, model_id=model_id)

    # Claude Max - uses subscription via CLI
    if spec.provider == "max":
        try:
            from claude_max_model import ClaudeMax
            return ClaudeMax(id=spec.model_id)
        except ImportError as exc:
            raise RuntimeError("ClaudeMax model not available") from exc

    # Anthropic API via Agno
    if spec.provider == "anthropic":
        try:
            from agno.models.anthropic import Claude
            return Claude(id=spec.model_id)
        except ImportError as exc:
            raise RuntimeError("Anthropic model not available - install agno") from exc

    # Ollama local models
    if spec.provider == "ollama":
        try:
            from agno.models.ollama import Ollama
            return Ollama(id=spec.model_id)
        except ImportError as exc:
            raise RuntimeError("Ollama model not available - install agno") from exc

    # Moonshot/Kimi
    if spec.provider == "moonshot":
        try:
            from agno.models.moonshot import MoonShot
            return MoonShot(id=spec.model_id)
        except ImportError as exc:
            raise RuntimeError("Moonshot model not available - install agno") from exc

    raise ValueError(f"Unsupported provider: {spec.provider}")
