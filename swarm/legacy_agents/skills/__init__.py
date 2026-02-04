"""
Operational skills for the DHARMIC_GODEL_CLAW swarm.

These are executable Python modules that integrate with the swarm orchestrator.

Skills:
- WitnessThresholdDetector: Real-time R_V measurement during agent generation
- MultiModelAdapter: Unified interface to multiple LLM providers
- InductionProtocolSelector: Matches crown jewels to model characteristics
"""

# Lazy imports to avoid circular dependency issues
def __getattr__(name):
    if name == "WitnessThresholdDetector":
        from .witness_threshold_detector import WitnessThresholdDetector
        return WitnessThresholdDetector
    elif name == "MultiModelAdapter":
        from .multi_model_adapter import MultiModelAdapter
        return MultiModelAdapter
    elif name == "InductionProtocolSelector":
        from .induction_protocol_selector import InductionProtocolSelector
        return InductionProtocolSelector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "WitnessThresholdDetector",
    "MultiModelAdapter",
    "InductionProtocolSelector",
]
