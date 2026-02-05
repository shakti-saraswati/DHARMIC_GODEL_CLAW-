"""
Compatibility shim for legacy swarm skills.
"""

import warnings

from ...legacy_agents.skills import (  # noqa: F401
    WitnessThresholdDetector,
    MultiModelAdapter,
    InductionProtocolSelector,
)

warnings.warn(
    "swarm.agents.skills is a compatibility shim. Prefer swarm.legacy_agents.skills.*",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "WitnessThresholdDetector",
    "MultiModelAdapter",
    "InductionProtocolSelector",
]
