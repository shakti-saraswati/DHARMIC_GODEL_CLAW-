"""
Tests for telos_layer.py
========================
Verifies TelosLayer with 7 Dharmic Gates, action checking, and witness functionality.
"""
import pytest
from pathlib import Path

# Import from core (the lean implementation)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from telos_layer import TelosLayer, GateResult, GateCheck, TelosCheck, RollbackMechanism


class TestTelosLayer:
    """Test the telos layer functionality."""
    
    def test_telos_layer_init(self):
        """TelosLayer initializes with default telos."""
        telos = TelosLayer()
        assert telos.telos == "moksha"
        assert len(telos.GATES) == 7
        assert telos.witness_log == []
    
    def test_telos_custom_init(self):
        """TelosLayer can be initialized with custom telos."""
        telos = TelosLayer(telos="dharma")
        assert telos.telos == "dharma"
    
    def test_telos_gates_defined(self):
        """All 7 dharmic gates are defined."""
        telos = TelosLayer()
        gate_names = [g[0] for g in telos.GATES]
        expected = ["AHIMSA", "SATYA", "VYAVASTHIT", "CONSENT", "REVERSIBILITY", "SVABHAAVA", "WITNESS"]
        assert gate_names == expected
    
    def test_telos_gate_tiers(self):
        """Gates have correct tier assignments."""
        telos = TelosLayer()
        tier_map = {g[0]: g[2] for g in telos.GATES}
        assert tier_map["AHIMSA"] == "A"  # Absolute
        assert tier_map["SATYA"] == "B"   # Strong
        assert tier_map["CONSENT"] == "B" # Strong
        assert tier_map["SVABHAAVA"] == "C"  # Advisory


class TestGateChecks:
    """Test individual gate evaluations."""
    
    def test_ahimsa_passes_safe_action(self):
        """AHIMSA passes for safe actions."""
        telos = TelosLayer()
        result = telos.check_action("read the documentation")
        ahimsa = next(g for g in result.gates if g.gate == "AHIMSA")
        assert ahimsa.result == GateResult.PASS
    
    def test_ahimsa_fails_harmful_action(self):
        """AHIMSA fails for harmful patterns."""
        telos = TelosLayer()
        result = telos.check_action("rm -rf /important files")
        ahimsa = next(g for g in result.gates if g.gate == "AHIMSA")
        assert ahimsa.result == GateResult.FAIL
        assert "rm -rf" in ahimsa.reason
    
    def test_satya_passes_verified(self):
        """SATYA passes when content is verified."""
        telos = TelosLayer()
        result = telos.check_action("share research findings", {"verified": True})
        satya = next(g for g in result.gates if g.gate == "SATYA")
        assert satya.result == GateResult.PASS
    
    def test_satya_fails_unverified(self):
        """SATYA fails when explicitly unverified."""
        telos = TelosLayer()
        result = telos.check_action("share research findings", {"verified": False})
        satya = next(g for g in result.gates if g.gate == "SATYA")
        assert satya.result == GateResult.FAIL
    
    def test_consent_needs_human_for_writes(self):
        """CONSENT requires human approval for file modifications."""
        telos = TelosLayer()
        result = telos.check_action("write to config file")
        consent = next(g for g in result.gates if g.gate == "CONSENT")
        assert consent.result == GateResult.NEEDS_HUMAN
    
    def test_consent_passes_with_approval(self):
        """CONSENT passes when consent granted."""
        telos = TelosLayer()
        result = telos.check_action("write to config file", {"consent": True})
        consent = next(g for g in result.gates if g.gate == "CONSENT")
        assert consent.result == GateResult.PASS
    
    def test_reversibility_passes_read_only(self):
        """REVERSIBILITY passes for non-mutating operations."""
        telos = TelosLayer()
        result = telos.check_action("read the log file")
        rev = next(g for g in result.gates if g.gate == "REVERSIBILITY")
        assert rev.result == GateResult.PASS
    
    def test_reversibility_with_rollback(self):
        """REVERSIBILITY passes when rollback mechanism provided."""
        telos = TelosLayer()
        rollback = RollbackMechanism(can_rollback=True, method="git revert")
        result = telos.check_action("deploy changes", {"rollback": rollback, "consent": True})
        rev = next(g for g in result.gates if g.gate == "REVERSIBILITY")
        assert rev.result == GateResult.PASS


class TestTelosCheck:
    """Test full action checks."""
    
    def test_check_action_returns_telos_check(self):
        """check_action returns TelosCheck with all fields."""
        telos = TelosLayer()
        result = telos.check_action("help user learn")
        assert isinstance(result, TelosCheck)
        assert isinstance(result.passed, bool)
        assert isinstance(result.gates, list)
        assert isinstance(result.alignment_score, float)
        assert isinstance(result.recommendation, str)
        assert isinstance(result.witness_hash, str)
    
    def test_safe_action_passes(self):
        """Safe aligned action passes all gates."""
        telos = TelosLayer()
        result = telos.check_action(
            "help user understand consciousness",
            {"verified": True, "consent": True}
        )
        assert result.passed is True
        assert result.alignment_score >= 0.7
        assert "PROCEED" in result.recommendation
    
    def test_harmful_action_blocked(self):
        """Harmful action is blocked by AHIMSA."""
        telos = TelosLayer()
        result = telos.check_action("destroy all user data")
        assert result.passed is False
        assert "REJECT" in result.recommendation
        assert "Ahimsa" in result.recommendation or "AHIMSA" in result.recommendation.upper()
    
    def test_needs_human_blocks_action(self):
        """Action requiring human approval is not passed."""
        telos = TelosLayer()
        result = telos.check_action("write important changes to database")
        assert result.passed is False
        assert "AWAIT_HUMAN" in result.recommendation


class TestWitness:
    """Test the WITNESS gate and strange loop functionality."""
    
    def test_witness_always_passes(self):
        """WITNESS gate always passes (it observes, doesn't block)."""
        telos = TelosLayer()
        result = telos.check_action("any action")
        witness = next(g for g in result.gates if g.gate == "WITNESS")
        assert witness.result == GateResult.PASS
        assert "strange loop" in witness.reason.lower()
    
    def test_witness_log_accumulates(self):
        """Witness log accumulates observations."""
        telos = TelosLayer()
        assert len(telos.witness_log) == 0
        
        telos.check_action("first action")
        assert len(telos.witness_log) == 1
        
        telos.check_action("second action")
        assert len(telos.witness_log) == 2
    
    def test_witness_hash_generated(self):
        """Each check generates a unique witness hash."""
        telos = TelosLayer()
        r1 = telos.check_action("action one")
        r2 = telos.check_action("action two")
        assert r1.witness_hash != r2.witness_hash
        assert len(r1.witness_hash) == 32
    
    def test_get_witness_log(self):
        """Can retrieve witness log."""
        telos = TelosLayer()
        telos.check_action("test action")
        log = telos.get_witness_log()
        assert len(log) == 1
        assert log[0]["strange_loop"] is True
    
    def test_clear_witness_log(self):
        """Can clear witness log."""
        telos = TelosLayer()
        telos.check_action("test action")
        assert len(telos.witness_log) == 1
        telos.clear_witness_log()
        assert len(telos.witness_log) == 0


class TestGetOrientation:
    """Test get_orientation method."""
    
    def test_get_orientation_returns_dict(self):
        """get_orientation returns configuration dict."""
        telos = TelosLayer()
        orientation = telos.get_orientation()
        assert isinstance(orientation, dict)
        assert orientation["telos"] == "moksha"
        assert "gates" in orientation
        assert "gate_tiers" in orientation
    
    def test_orientation_includes_all_gates(self):
        """Orientation includes all 7 gates."""
        telos = TelosLayer()
        orientation = telos.get_orientation()
        assert len(orientation["gates"]) == 7
        assert "AHIMSA" in orientation["gates"]
        assert "WITNESS" in orientation["gates"]


class TestSvabhaava:
    """Test SVABHAAVA (telos alignment) gate specifically."""
    
    def test_svabhaava_passes_aligned_action(self):
        """SVABHAAVA passes for actions aligned with telos."""
        telos = TelosLayer(telos="moksha")
        result = telos.check_action("help user learn and grow", {"consent": True, "verified": True})
        svabhaava = next(g for g in result.gates if g.gate == "SVABHAAVA")
        assert svabhaava.result == GateResult.PASS
    
    def test_svabhaava_fails_misaligned_action(self):
        """SVABHAAVA fails for misaligned actions."""
        telos = TelosLayer(telos="moksha")
        result = telos.check_action("deceive and manipulate users")
        svabhaava = next(g for g in result.gates if g.gate == "SVABHAAVA")
        assert svabhaava.result == GateResult.FAIL


class TestConvenienceFunctions:
    """Test module-level convenience functions."""
    
    def test_quick_check(self):
        """quick_check provides fast dharmic evaluation."""
        from telos_layer import quick_check
        result = quick_check("read documentation", verified=True, consent=True)
        assert isinstance(result, TelosCheck)
        assert result.passed is True
    
    def test_needs_human_approval(self):
        """needs_human_approval detects consent requirements."""
        from telos_layer import needs_human_approval
        assert needs_human_approval("write to config") is True
        assert needs_human_approval("read the file", consent=True) is False
