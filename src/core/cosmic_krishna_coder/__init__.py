"""
Cosmic Krishna Coder (CKC) — Autonomous Coding with Dharmic Security

Components:
- RiskDetector: 5-dimensional risk scoring
- YOLOWeaver: Intelligent YOLO-Gate integration
- Gates: Gate runner wrapper

Usage:
    from src.core.cosmic_krishna_coder import RiskDetector, YOLOWeaver
    
    detector = RiskDetector()
    risk = detector.analyze("Build payment system", files=["payment.py"])
    
    weaver = YOLOWeaver()
    result = weaver.execute("Build auth", code="...", files=["auth.py"])

JSCA! 🔥
"""

from .risk_detector import (
    RiskDetector,
    RiskResult,
    RiskTier,
    WeaveMode,
    RiskSignal,
    analyze_risk,
)

from .yolo_weaver import (
    YOLOWeaver,
    WeaveResult,
    GateResult,
    GateStatus,
)

from . import gates
from .gates import (
    run_gate,
    run_gates,
    run_all_gates,
    GATE_REGISTRY,
)

from .dgm_evolver import (
    DGMEvolver,
    get_evolver,
    evolve_from_failures,
    EvolutionProposal,
    FailurePattern,
    ProposalType,
)

__all__ = [
    # Risk Detection
    "RiskDetector",
    "RiskResult",
    "RiskTier",
    "WeaveMode",
    "RiskSignal",
    "analyze_risk",
    # YOLO Weaver
    "YOLOWeaver",
    "WeaveResult",
    "GateResult",
    "GateStatus",
    # Real Gates
    "gates",
    "run_gate",
    "run_gates",
    "run_all_gates",
    "GATE_REGISTRY",
    # DGM Evolution
    "DGMEvolver",
    "get_evolver",
    "evolve_from_failures",
    "EvolutionProposal",
    "FailurePattern",
    "ProposalType",
]
