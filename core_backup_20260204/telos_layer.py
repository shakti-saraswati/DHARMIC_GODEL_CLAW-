"""
TELOS LAYER: 7 Dharmic Gates + Moksha Orientation
Tier A (Absolute): AHIMSA | Tier B (Strong): SATYA, CONSENT | Tier C: rest
"""
from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum
import json

class GateResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"

@dataclass
class GateCheck:
    gate: str
    result: GateResult
    reason: str

@dataclass
class TelosCheck:
    passed: bool
    gates: List[GateCheck]
    alignment_score: float
    recommendation: str

class TelosLayer:
    GATES = [
        ("AHIMSA", "Does this harm?", "A"),
        ("SATYA", "Is this true?", "B"),
        ("VYAVASTHIT", "Allow or force?", "C"),
        ("CONSENT", "Permission granted?", "B"),
        ("REVERSIBILITY", "Can undo?", "C"),
        ("SVABHAAV", "Authentic or imitation?", "C"),
        ("COHERENCE", "Serves moksha?", "C"),
    ]
    
    def __init__(self, telos: str = "moksha"):
        self.telos = telos
        
    def check_action(self, action: str, context: Dict = None) -> TelosCheck:
        context = context or {}
        gates = []
        tier_a_pass = tier_b_pass = True
        
        for name, question, tier in self.GATES:
            result = self._evaluate(name, action, context)
            gates.append(result)
            if result.result == GateResult.FAIL:
                if tier == "A": tier_a_pass = False
                elif tier == "B": tier_b_pass = False
        
        alignment = sum(1 for g in gates if g.result == GateResult.PASS) / len(self.GATES)
        passed = tier_a_pass and tier_b_pass and alignment >= 0.7
        
        if not tier_a_pass: rec = "REJECT: Ahimsa violation"
        elif not tier_b_pass: rec = "REJECT: Satya/Consent violation"
        elif alignment < 0.7: rec = f"REVIEW: {alignment:.0%} alignment"
        else: rec = "PROCEED"
        
        return TelosCheck(passed=passed, gates=gates, alignment_score=alignment, recommendation=rec)
    
    def _evaluate(self, gate: str, action: str, context: Dict) -> GateCheck:
        a = action.lower()
        if gate == "AHIMSA":
            if any(w in a for w in ["delete all", "destroy", "rm -rf"]): 
                return GateCheck(gate, GateResult.FAIL, "Harmful pattern")
            return GateCheck(gate, GateResult.PASS, "No harm detected")
        elif gate == "SATYA":
            return GateCheck(gate, GateResult.PASS if context.get("verified") else GateResult.UNCERTAIN, "Truth check")
        elif gate == "CONSENT":
            return GateCheck(gate, GateResult.PASS if context.get("consent", True) else GateResult.UNCERTAIN, "Consent check")
        elif gate == "REVERSIBILITY":
            if any(w in a for w in ["permanent", "irreversible"]): 
                return GateCheck(gate, GateResult.FAIL, "Irreversible")
            return GateCheck(gate, GateResult.PASS, "Reversible")
        return GateCheck(gate, GateResult.PASS, "Default pass")
    
    def get_orientation(self) -> Dict:
        return {"telos": self.telos, "gates": [g[0] for g in self.GATES]}

if __name__ == "__main__":
    t = TelosLayer()
    r = t.check_action("Read Aptavani for witness recognition", {"verified": True, "consent": True})
    print(f"Passed: {r.passed}, Alignment: {r.alignment_score:.0%}, {r.recommendation}")
