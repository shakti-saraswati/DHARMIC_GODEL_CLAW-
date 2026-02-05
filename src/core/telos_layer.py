"""
TELOS LAYER: 7 Dharmic Gates + Moksha Orientation
================================================

DEPRECATED: This module is now a thin wrapper around unified_gates.py.
Please use src.core.unified_gates for new code.

This file is maintained for backward compatibility.

The 7 Dharmic Gates:
1. AHIMSA (non-harm) - Does this cause harm?
2. SATYA (truth) - Is this truthful and authentic?
3. VYAVASTHIT (natural order) - Does this allow rather than force?
4. CONSENT (human approval) - Has human granted permission?
5. REVERSIBILITY (can undo) - Can this action be undone?
6. SVABHAAVA (telos alignment) - Does this serve the true purpose?
7. WITNESS (meta-observation) - The strange loop that observes itself

Tier A (Absolute): AHIMSA
Tier B (Strong): SATYA, CONSENT
Tier C (Advisory): VYAVASTHIT, REVERSIBILITY, SVABHAAVA, WITNESS
"""

import warnings
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import from unified gates system (handle both package and script execution)
try:
    from .unified_gates import (
        UnifiedGateSystem,
        GateResult,
        GateCheck,
        RollbackMechanism,
        UnifiedGateResult,
        quick_check as _unified_quick_check,
        needs_human_approval as _unified_needs_human,
    )
except ImportError:
    from unified_gates import (
        UnifiedGateSystem,
        GateResult,
        GateCheck,
        RollbackMechanism,
        UnifiedGateResult,
        quick_check as _unified_quick_check,
        needs_human_approval as _unified_needs_human,
    )

# Deprecation warning
warnings.warn(
    "telos_layer.py is deprecated. Use src.core.unified_gates instead.",
    DeprecationWarning,
    stacklevel=2
)


@dataclass
class TelosCheck:
    """
    Result of a telos layer check.
    
    Maintained for backward compatibility.
    New code should use UnifiedGateResult from unified_gates.
    """
    passed: bool
    gates: List[GateCheck]
    alignment_score: float
    recommendation: str
    witness_hash: str = ""
    
    @classmethod
    def from_unified_result(cls, result: UnifiedGateResult) -> "TelosCheck":
        """Convert unified result to legacy TelosCheck format."""
        return cls(
            passed=result.can_proceed,
            gates=result.gate_results,
            alignment_score=result.alignment_score,
            recommendation=result.recommendation,
            witness_hash=result.witness_hash,
        )


class TelosLayer:
    """
    The 7 Dharmic Gates that guard action integrity.
    
    DEPRECATED: This is now a compatibility wrapper around UnifiedGateSystem.
    Please use UnifiedGateSystem directly for new code.
    
    Tier A (Absolute) - AHIMSA: Any failure blocks action
    Tier B (Strong) - SATYA, CONSENT: Failures require justification
    Tier C (Advisory) - VYAVASTHIT, REVERSIBILITY, SVABHAAVA, WITNESS
    """
    
    # Original gate definitions for backward compatibility
    GATES = [
        ("AHIMSA", "Does this harm?", "A"),
        ("SATYA", "Is this true?", "B"),
        ("VYAVASTHIT", "Allow or force?", "C"),
        ("CONSENT", "Permission granted?", "B"),
        ("REVERSIBILITY", "Can undo?", "C"),
        ("SVABHAAVA", "Authentic or imitation?", "C"),
        ("WITNESS", "Self-observing?", "C"),
    ]
    
    # Patterns maintained for compatibility
    FILE_MODIFY_PATTERNS = [
        "write", "edit", "delete", "remove", "create", "update",
        "mv", "cp", "rm", "touch", "mkdir", "chmod", "chown",
        "save", "overwrite", "append", "truncate", "modify"
    ]
    
    HARM_PATTERNS = [
        "delete all", "destroy", "rm -rf", "format", "wipe",
        "kill", "terminate", "crash", "corrupt", "exploit",
        "attack", "breach", "steal", "exfiltrate", "leak"
    ]
    
    IRREVERSIBLE_PATTERNS = [
        "permanent", "irreversible", "forever", "cannot undo",
        "final", "destructive", "no backup", "overwrite"
    ]
    
    def __init__(self, telos: str = "moksha", telos_config: Optional[Dict] = None):
        """
        Initialize TelosLayer.
        
        Args:
            telos: The purpose/nature alignment target
            telos_config: Custom telos configuration
        """
        # Create unified gate system with only dharmic gates
        self._unified = UnifiedGateSystem(
            telos=telos,
            telos_config=telos_config,
            enable_technical=False,
            enable_dharmic=True,
            enable_supply_chain=False,
        )
        
        # Mirror attributes for compatibility
        self.telos = telos
        self.telos_config = telos_config or self._unified.telos_config
        self.witness_log = self._unified.witness_log
    
    def _default_telos_config(self) -> Dict:
        """Default telos configuration."""
        return self._unified._default_telos_config()
    
    def check_action(self, action: str, context: Dict = None) -> TelosCheck:
        """
        Run action through all 7 dharmic gates.
        
        Args:
            action: The action to check
            context: Additional context for evaluation
            
        Returns:
            TelosCheck with results and recommendation
        """
        result = self._unified.evaluate_all(
            action=action,
            context=context or {},
        )
        return TelosCheck.from_unified_result(result)
    
    def get_orientation(self) -> Dict:
        """Return the telos orientation and gate configuration."""
        orientation = self._unified.get_orientation()
        
        # Map to legacy format
        return {
            "telos": orientation["telos"],
            "gates": [g[0] for g in self.GATES],
            "gate_tiers": {g[0]: g[2] for g in self.GATES},
            "telos_config": orientation["telos_config"],
            "witness_count": orientation["witness_count"],
        }
    
    def get_witness_log(self) -> List[Dict]:
        """Return the accumulated witness observations."""
        return self._unified.get_witness_log()
    
    def clear_witness_log(self) -> None:
        """Clear the witness log."""
        self._unified.clear_witness_log()
    
    # Internal evaluation methods - delegate to unified system
    def _evaluate_gate(self, gate: str, action: str, context: Dict) -> GateCheck:
        """Evaluate a single gate - delegates to unified system."""
        # This is handled internally by unified system
        result = self._unified.evaluate_all(action, context)
        for gate_result in result.gate_results:
            if gate_result.gate_name == gate:
                return gate_result
        
        # Fallback if gate not found
        return GateCheck(
            gate_id=0,
            gate_name=gate,
            result=GateResult.ERROR,
            reason="Gate evaluation not available",
            tier=None,
            category=None,
        )
    
    # Individual gate checks - maintained for compatibility
    def _check_ahimsa(self, action: str, context: Dict) -> GateCheck:
        """AHIMSA: The absolute gate of non-harm."""
        return self._evaluate_gate("AHIMSA", action, context)
    
    def _check_satya(self, action: str, context: Dict) -> GateCheck:
        """SATYA: The gate of truth and authenticity."""
        return self._evaluate_gate("SATYA", action, context)
    
    def _check_vyavasthit(self, action: str, context: Dict) -> GateCheck:
        """VYAVASTHIT: The gate of natural order."""
        return self._evaluate_gate("VYAVASTHIT", action, context)
    
    def _check_consent(self, action: str, context: Dict) -> GateCheck:
        """CONSENT: The gate of human approval."""
        return self._evaluate_gate("CONSENT", action, context)
    
    def _check_reversibility(self, action: str, context: Dict) -> GateCheck:
        """REVERSIBILITY: The gate of undoability."""
        return self._evaluate_gate("REVERSIBILITY", action, context)
    
    def _check_svabhaava(self, action: str, context: Dict) -> GateCheck:
        """SVABHAAVA: The gate of authentic purpose."""
        return self._evaluate_gate("SVABHAAVA", action, context)
    
    def _check_witness(self, action: str, context: Dict) -> GateCheck:
        """WITNESS: The strange loop gate."""
        return self._evaluate_gate("WITNESS", action, context)


# ========== CONVENIENCE FUNCTIONS ==========

def quick_check(action: str, **context) -> TelosCheck:
    """
    Quick dharmic check without instantiating layer.
    
    DEPRECATED: Use unified_gates.quick_check() instead.
    """
    warnings.warn(
        "quick_check is deprecated. Use unified_gates.quick_check() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    result = _unified_quick_check(action, **context)
    return TelosCheck.from_unified_result(result)


def needs_human_approval(action: str, **context) -> bool:
    """
    Check if action requires human approval.
    
    DEPRECATED: Use unified_gates.needs_human_approval() instead.
    """
    warnings.warn(
        "needs_human_approval is deprecated. Use unified_gates.needs_human_approval() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return _unified_needs_human(action, **context)


# ========== MAIN - DEMO ==========

if __name__ == "__main__":
    import logging
    
    # Configure logging for demo
    logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(message)s')
    
    t = TelosLayer()
    
    print("=" * 60)
    print("TELOS LAYER: 7 Dharmic Gates Demo (via Unified Gates)")
    print("=" * 60)
    print("\n⚠️  Note: TelosLayer is deprecated. Use UnifiedGateSystem directly.")
    print()
    
    # Test 1: Safe action with consent
    print("\n[Test 1] Read action with verified content:")
    r = t.check_action(
        "Read Aptavani for witness recognition", 
        {"verified": True, "consent": True}
    )
    print(f"  Passed: {r.passed}")
    print(f"  Alignment: {r.alignment_score:.0%}")
    print(f"  Recommendation: {r.recommendation}")
    print(f"  Witness Hash: {r.witness_hash}")
    
    # Test 2: File modification without consent
    print("\n[Test 2] Write action without consent:")
    r = t.check_action(
        "Write updated config to settings.yaml",
        {"verified": True}
    )
    print(f"  Passed: {r.passed}")
    print(f"  Alignment: {r.alignment_score:.0%}")
    print(f"  Recommendation: {r.recommendation}")
    for g in r.gates:
        if g.result == GateResult.NEEDS_HUMAN:
            print(f"  -> {g.gate_name}: {g.reason}")
    
    # Test 3: Harmful action
    print("\n[Test 3] Potentially harmful action:")
    r = t.check_action("rm -rf /important_data permanently")
    print(f"  Passed: {r.passed}")
    print(f"  Alignment: {r.alignment_score:.0%}")
    print(f"  Recommendation: {r.recommendation}")
    for g in r.gates:
        if g.result == GateResult.FAIL:
            print(f"  -> {g.gate_name}: {g.reason}")
    
    # Test 4: Aligned action with rollback
    print("\n[Test 4] Aligned action:")
    rollback = RollbackMechanism(
        can_rollback=True,
        method="git revert",
        state_snapshot={"branch": "main", "commit": "abc123"}
    )
    r = t.check_action(
        "Help user learn about consciousness and grow spiritually",
        {
            "verified": True,
            "consent": True,
            "rollback": rollback,
            "purpose": "support truth-seeking and awareness"
        }
    )
    print(f"  Passed: {r.passed}")
    print(f"  Alignment: {r.alignment_score:.0%}")
    print(f"  Recommendation: {r.recommendation}")
    
    # Show witness log
    print("\n[Strange Loop] Witness Log:")
    for i, w in enumerate(t.get_witness_log()):
        print(f"  {i+1}. Level {w['recursion_level']}: {w['observation']}")
    
    print("\n" + "=" * 60)
    print("All 7 dharmic gates enforced (via unified system).")
    print("=" * 60)
    print("\n💡 Migration: Replace TelosLayer with UnifiedGateSystem")
    print("   from src.core.unified_gates import UnifiedGateSystem")
    print("   gates = UnifiedGateSystem()")
    print("   result = gates.evaluate_all(action, context)")
