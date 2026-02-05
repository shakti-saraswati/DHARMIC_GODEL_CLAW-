"""
Compatibility shim for legacy swarm agent imports.

`swarm.agents` historically existed; the current canonical pipeline lives in `swarm/*`.
This module re-exports legacy agent classes to keep older imports working.
"""

import warnings

from ..legacy_agents import (  # noqa: F401
    BaseAgent,
    AgentResponse,
    ProposerAgent,
    WriterAgent,
    TesterAgent,
    RefinerAgent,
    EvolverAgent,
    DharmicGateAgent,
    DharmicAgent,
    AgentMode,
)

warnings.warn(
    "swarm.agents is a compatibility shim. Prefer swarm/* or swarm.legacy_agents.*",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "ProposerAgent",
    "WriterAgent",
    "TesterAgent",
    "RefinerAgent",
    "EvolverAgent",
    "DharmicGateAgent",
    "DharmicAgent",
    "AgentMode",
]
