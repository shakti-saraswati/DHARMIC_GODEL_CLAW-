"""
Agent Singleton - Shared Agent Instance

Provides a singleton pattern for agent initialization to avoid
duplication across daemon and email interfaces.
"""

from typing import Optional
from dharmic_logging import get_logger

logger = get_logger("agent_singleton")

_agent_instance = None


def get_agent(
    model_provider: Optional[str] = None,
    model_id: Optional[str] = None,
    force_new: bool = False
):
    """
    Get or create the Dharmic Agent singleton instance.

    Args:
        model_provider: Override provider (max, anthropic, etc.)
        model_id: Override model ID
        force_new: Force create a new instance

    Returns:
        DharmicAgent instance
    """
    global _agent_instance

    if _agent_instance is None or force_new:
        logger.info("Creating new agent instance")
        from agent_core import DharmicAgent
        _agent_instance = DharmicAgent(
            model_provider=model_provider,
            model_id=model_id
        )
        logger.info(f"Agent initialized: {_agent_instance.model_provider}/{_agent_instance.model_id}")

    return _agent_instance


def reset_agent():
    """Reset the singleton (useful for testing)."""
    global _agent_instance
    _agent_instance = None
    logger.info("Agent instance reset")
