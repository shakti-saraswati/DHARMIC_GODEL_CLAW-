"""
Comprehensive Tests for TelosLayer
===================================
Tests for all 7 dharmic gates, edge cases, and TelosCheck structure.
Target: 90%+ coverage of telos_layer.py
"""
import pytest
from core.telos_layer import (
    TelosLayer, GateResult, GateCheck, TelosCheck, RollbackMechanism
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def telos():
    """Fresh TelosLayer instance."""
    return TelosLayer()


@pytest.fixture
def telos_custom():
    """TelosLayer with custom telos."""
    return TelosLayer(telos="liberation")


# ============================================================================
# GATE RESULT ENUM TESTS
# ============================================================================

class TestGateResult:
    """Tests for GateResult enum."""
    
    def test_gate_result_values(self):
        """Verify all GateResult enum values."""
        assert GateResult.PASS.value == "pass"
        assert GateResult.FAIL.value == "fail"
        assert GateResult.UNCERTAIN.value == "uncertain"
        assert GateResult.NEEDS_HUMAN.value == "needs_human"
    
    def test_gate_result_members(self):
        """Verify GateResult has exactly 4 members."""
        assert len(GateResult) == 4
        assert set(GateResult) == {
            GateResult.PASS, GateResult.FAIL, 
            GateResult.UNCERTAIN, GateResult.NEEDS_HUMAN
        }


# ============================================================================
# GATE CHECK DATACLASS TESTS
# ============================================================================

class TestGateCheck:
    """Tests for GateCheck dataclass."""
    
    def test_gate_check_creation(self):
        """Test GateCheck instantiation."""
        check = GateCheck(gate="AHIMSA", result=GateResult.PASS, reason="No harm")
        assert check.gate == "AHIMSA"
        assert check.result == GateResult.PASS
        assert check.reason == "No harm"
    
    def test_gate_check_fail_state(self):
        """Test GateCheck with FAIL result."""
        check = GateCheck(gate="SATYA", result=GateResult.FAIL, reason="Unverified")
        assert check.result == GateResult.FAIL
    
    def test_gate_check_uncertain_state(self):
        """Test GateCheck with UNCERTAIN result."""
        check = GateCheck(gate="CONSENT", result=GateResult.UNCERTAIN, reason="Unknown")
        assert check.result == GateResult.UNCERTAIN
    
    def test_gate_check_needs_human_state(self):
        """Test GateCheck with NEEDS_HUMAN result."""
        check = GateCheck(gate="CONSENT", result=GateResult.NEEDS_HUMAN, reason="Requires approval")
        assert check.result == GateResult.NEEDS_HUMAN
    
    def test_gate_check_has_metadata(self):
        """Test GateCheck metadata field."""
        check = GateCheck(gate="TEST", result=GateResult.PASS, reason="OK", metadata={"key": "value"})
        assert check.metadata == {"key": "value"}
    
    def test_gate_check_has_timestamp(self):
        """Test GateCheck timestamp field."""
        check = GateCheck(gate="TEST", result=GateResult.PASS, reason="OK")
        assert check.timestamp is not None


# ============================================================================
# TELOS CHECK DATACLASS TESTS
# ============================================================================

class TestTelosCheck:
    """Tests for TelosCheck dataclass."""
    
    def test_telos_check_creation(self):
        """Test TelosCheck instantiation."""
        gates = [GateCheck("TEST", GateResult.PASS, "OK")]
        check = TelosCheck(passed=True, gates=gates, alignment_score=1.0, recommendation="PROCEED: All gates satisfied")
        assert check.passed is True
        assert len(check.gates) == 1
        assert check.alignment_score == 1.0
        assert "PROCEED" in check.recommendation
    
    def test_telos_check_failed_state(self):
        """Test TelosCheck with failed state."""
        gates = [GateCheck("AHIMSA", GateResult.FAIL, "Harmful")]
        check = TelosCheck(passed=False, gates=gates, alignment_score=0.0, recommendation="REJECT")
        assert check.passed is False
    
    def test_telos_check_has_witness_hash(self):
        """Test TelosCheck witness_hash field."""
        gates = [GateCheck("TEST", GateResult.PASS, "OK")]
        check = TelosCheck(passed=True, gates=gates, alignment_score=1.0, recommendation="OK", witness_hash="abc123")
        assert check.witness_hash == "abc123"


# ============================================================================
# TELOS LAYER INITIALIZATION TESTS
# ============================================================================

class TestTelosLayerInit:
    """Tests for TelosLayer initialization."""
    
    def test_default_telos(self, telos):
        """Test default telos is 'moksha'."""
        assert telos.telos == "moksha"
    
    def test_custom_telos(self, telos_custom):
        """Test custom telos initialization."""
        assert telos_custom.telos == "liberation"
    
    def test_gates_defined(self, telos):
        """Test all 7 gates are defined."""
        assert len(telos.GATES) == 7
        gate_names = [g[0] for g in telos.GATES]
        assert "AHIMSA" in gate_names
        assert "SATYA" in gate_names
        assert "VYAVASTHIT" in gate_names
        assert "CONSENT" in gate_names
        assert "REVERSIBILITY" in gate_names
        assert "SVABHAAVA" in gate_names
        assert "WITNESS" in gate_names
    
    def test_gate_tiers(self, telos):
        """Test gate tier assignments."""
        tier_map = {g[0]: g[2] for g in telos.GATES}
        assert tier_map["AHIMSA"] == "A"  # Absolute
        assert tier_map["SATYA"] == "B"   # Strong
        assert tier_map["CONSENT"] == "B"  # Strong
        assert tier_map["VYAVASTHIT"] == "C"
        assert tier_map["REVERSIBILITY"] == "C"
        assert tier_map["SVABHAAVA"] == "C"
        assert tier_map["WITNESS"] == "C"
    
    def test_has_witness_log(self, telos):
        """Test TelosLayer has witness_log."""
        assert hasattr(telos, 'witness_log')
        assert isinstance(telos.witness_log, list)
    
    def test_has_telos_config(self, telos):
        """Test TelosLayer has telos_config."""
        assert hasattr(telos, 'telos_config')
        assert 'moksha' in telos.telos_config


# ============================================================================
# INDIVIDUAL GATE TESTS (7 DHARMIC GATES)
# ============================================================================

class TestAhimsaGate:
    """Tests for AHIMSA (non-harm) gate - Tier A."""
    
    def test_ahimsa_passes_safe_action(self, telos):
        """Safe actions should pass AHIMSA."""
        result = telos._evaluate_gate("AHIMSA", "read file contents", {})
        assert result.result == GateResult.PASS
        assert result.gate == "AHIMSA"
    
    def test_ahimsa_fails_delete_all(self, telos):
        """'delete all' should fail AHIMSA."""
        result = telos._evaluate_gate("AHIMSA", "delete all user data", {})
        assert result.result == GateResult.FAIL
        assert "Harmful" in result.reason or "harm" in result.reason.lower()
    
    def test_ahimsa_fails_destroy(self, telos):
        """'destroy' should fail AHIMSA."""
        result = telos._evaluate_gate("AHIMSA", "destroy the database", {})
        assert result.result == GateResult.FAIL
    
    def test_ahimsa_fails_rm_rf(self, telos):
        """'rm -rf' should fail AHIMSA."""
        result = telos._evaluate_gate("AHIMSA", "rm -rf /", {})
        assert result.result == GateResult.FAIL
    
    def test_ahimsa_case_insensitive(self, telos):
        """AHIMSA check should be case insensitive."""
        result = telos._evaluate_gate("AHIMSA", "DELETE ALL files", {})
        assert result.result == GateResult.FAIL
    
    def test_ahimsa_fails_with_causes_harm_context(self, telos):
        """Context indicating harm should fail AHIMSA."""
        result = telos._evaluate_gate("AHIMSA", "perform action", {"causes_harm": True})
        assert result.result == GateResult.FAIL
    
    def test_ahimsa_uncertain_affects_others(self, telos):
        """Action affecting unaware others should be UNCERTAIN."""
        result = telos._evaluate_gate("AHIMSA", "update settings", {"affects_others": True, "others_aware": False})
        assert result.result == GateResult.UNCERTAIN


class TestSatyaGate:
    """Tests for SATYA (truth) gate - Tier B."""
    
    def test_satya_passes_when_verified(self, telos):
        """Verified context should pass SATYA."""
        result = telos._evaluate_gate("SATYA", "make a claim", {"verified": True})
        assert result.result == GateResult.PASS
    
    def test_satya_fails_when_unverified(self, telos):
        """Unverified=False context should FAIL SATYA."""
        result = telos._evaluate_gate("SATYA", "make a claim", {"verified": False})
        assert result.result == GateResult.FAIL
    
    def test_satya_uncertain_when_no_context(self, telos):
        """Missing verified key should be UNCERTAIN."""
        result = telos._evaluate_gate("SATYA", "make a claim", {})
        assert result.result == GateResult.UNCERTAIN
    
    def test_satya_fails_deceptive_patterns(self, telos):
        """Deceptive patterns should fail SATYA."""
        result = telos._evaluate_gate("SATYA", "pretend to be someone else", {})
        assert result.result == GateResult.FAIL
    
    def test_satya_fails_lie_pattern(self, telos):
        """'lie' pattern should fail SATYA."""
        result = telos._evaluate_gate("SATYA", "lie about the results", {})
        assert result.result == GateResult.FAIL
    
    def test_satya_uncertain_claim_without_source(self, telos):
        """Claim without source should be UNCERTAIN."""
        result = telos._evaluate_gate("SATYA", "action", {"is_claim": True, "has_source": False})
        assert result.result == GateResult.UNCERTAIN


class TestConsentGate:
    """Tests for CONSENT gate - Tier B."""
    
    def test_consent_passes_when_granted(self, telos):
        """Explicit consent should pass."""
        result = telos._evaluate_gate("CONSENT", "access data", {"consent": True})
        assert result.result == GateResult.PASS
    
    def test_consent_fails_when_denied(self, telos):
        """Explicit consent=False should FAIL."""
        result = telos._evaluate_gate("CONSENT", "access data", {"consent": False})
        assert result.result == GateResult.FAIL
    
    def test_consent_needs_human_for_file_modification(self, telos):
        """File modification without consent needs human approval."""
        result = telos._evaluate_gate("CONSENT", "write to config file", {})
        assert result.result == GateResult.NEEDS_HUMAN
    
    def test_consent_needs_human_for_sensitive_ops(self, telos):
        """Sensitive operations need human approval."""
        result = telos._evaluate_gate("CONSENT", "send email to user", {})
        assert result.result == GateResult.NEEDS_HUMAN
    
    def test_consent_passes_read_only(self, telos):
        """Read-only operations should pass without explicit consent."""
        result = telos._evaluate_gate("CONSENT", "read file contents", {})
        assert result.result == GateResult.PASS
    
    def test_consent_passes_with_modifies_files_and_consent(self, telos):
        """File modification with consent should pass."""
        result = telos._evaluate_gate("CONSENT", "write config", {"consent": True})
        assert result.result == GateResult.PASS


class TestReversibilityGate:
    """Tests for REVERSIBILITY gate - Tier C."""
    
    def test_reversibility_passes_read_action(self, telos):
        """Read actions are inherently reversible."""
        result = telos._evaluate_gate("REVERSIBILITY", "read document", {})
        assert result.result == GateResult.PASS
    
    def test_reversibility_fails_permanent(self, telos):
        """Actions marked 'permanent' should fail."""
        result = telos._evaluate_gate("REVERSIBILITY", "permanent deletion", {})
        assert result.result == GateResult.FAIL
        assert "Irreversible" in result.reason or "irreversible" in result.reason.lower()
    
    def test_reversibility_fails_irreversible(self, telos):
        """Actions marked 'irreversible' should fail."""
        result = telos._evaluate_gate("REVERSIBILITY", "irreversible change", {})
        assert result.result == GateResult.FAIL
    
    def test_reversibility_uncertain_for_mutation(self, telos):
        """Mutations without rollback should be UNCERTAIN."""
        result = telos._evaluate_gate("REVERSIBILITY", "edit document", {})
        assert result.result == GateResult.UNCERTAIN
    
    def test_reversibility_passes_with_rollback(self, telos):
        """Actions with rollback mechanism should pass."""
        rollback = RollbackMechanism(can_rollback=True, method="git revert")
        result = telos._evaluate_gate("REVERSIBILITY", "modify file", {"rollback": rollback})
        assert result.result == GateResult.PASS
    
    def test_reversibility_passes_with_backup_context(self, telos):
        """Actions with has_backup context should pass."""
        result = telos._evaluate_gate("REVERSIBILITY", "modify file", {"has_backup": True})
        assert result.result == GateResult.PASS
    
    def test_reversibility_fails_when_cannot_undo(self, telos):
        """Actions marked cannot_undo should fail."""
        result = telos._evaluate_gate("REVERSIBILITY", "action", {"cannot_undo": True})
        assert result.result == GateResult.FAIL


class TestVyavasthitGate:
    """Tests for VYAVASTHIT (natural order) gate - Tier C."""
    
    def test_vyavasthit_default_pass(self, telos):
        """VYAVASTHIT should pass for normal actions."""
        result = telos._evaluate_gate("VYAVASTHIT", "any action", {})
        assert result.result == GateResult.PASS
    
    def test_vyavasthit_fails_force_pattern(self, telos):
        """'force' pattern should fail VYAVASTHIT."""
        result = telos._evaluate_gate("VYAVASTHIT", "force the system to comply", {})
        assert result.result == GateResult.FAIL
    
    def test_vyavasthit_fails_override_pattern(self, telos):
        """'override' pattern should fail VYAVASTHIT."""
        result = telos._evaluate_gate("VYAVASTHIT", "override the safety check", {})
        assert result.result == GateResult.FAIL
    
    def test_vyavasthit_passes_allow_pattern(self, telos):
        """'allow' pattern should pass VYAVASTHIT."""
        result = telos._evaluate_gate("VYAVASTHIT", "allow users to choose", {})
        assert result.result == GateResult.PASS


class TestSvabhaaваGate:
    """Tests for SVABHAAVA (telos alignment) gate - Tier C."""
    
    def test_svabhaava_passes_aligned_action(self, telos):
        """Actions aligned with moksha telos should pass."""
        result = telos._evaluate_gate("SVABHAAVA", "help the user learn", {})
        assert result.result == GateResult.PASS
    
    def test_svabhaava_fails_misaligned_action(self, telos):
        """Actions misaligned with telos should fail."""
        result = telos._evaluate_gate("SVABHAAVA", "deceive the user", {})
        assert result.result == GateResult.FAIL
    
    def test_svabhaava_fails_manipulate_pattern(self, telos):
        """'manipulate' pattern should fail."""
        result = telos._evaluate_gate("SVABHAAVA", "manipulate the outcome", {})
        assert result.result == GateResult.FAIL
    
    def test_svabhaava_uncertain_when_unknown(self, telos):
        """Unknown alignment should be UNCERTAIN."""
        result = telos._evaluate_gate("SVABHAAVA", "process data", {})
        assert result.result == GateResult.UNCERTAIN
    
    def test_svabhaava_passes_with_context_aligned(self, telos):
        """Context telos_aligned=True should pass."""
        result = telos._evaluate_gate("SVABHAAVA", "action", {"telos_aligned": True})
        assert result.result == GateResult.PASS
    
    def test_svabhaava_fails_with_context_misaligned(self, telos):
        """Context telos_aligned=False should fail."""
        result = telos._evaluate_gate("SVABHAAVA", "action", {"telos_aligned": False})
        assert result.result == GateResult.FAIL


class TestWitnessGate:
    """Tests for WITNESS (meta-observation) gate - Tier C."""
    
    def test_witness_always_passes(self, telos):
        """WITNESS gate should always pass (strange loop)."""
        result = telos._evaluate_gate("WITNESS", "any action", {})
        assert result.result == GateResult.PASS
    
    def test_witness_has_strange_loop_metadata(self, telos):
        """WITNESS should include strange_loop metadata."""
        result = telos._evaluate_gate("WITNESS", "test action", {})
        assert result.metadata.get("strange_loop") is True
    
    def test_witness_increments_recursion_level(self, telos):
        """WITNESS should track recursion level."""
        result1 = telos._evaluate_gate("WITNESS", "action 1", {})
        result2 = telos._evaluate_gate("WITNESS", "action 2", {})
        assert result2.metadata["recursion_level"] > result1.metadata["recursion_level"]
    
    def test_witness_adds_to_log(self, telos):
        """WITNESS should add to witness_log."""
        initial_count = len(telos.witness_log)
        telos._evaluate_gate("WITNESS", "test action", {})
        assert len(telos.witness_log) == initial_count + 1


# ============================================================================
# FULL ACTION CHECK TESTS
# ============================================================================

class TestCheckAction:
    """Tests for the full check_action method."""
    
    def test_safe_action_passes(self, telos):
        """Safe verified action should pass."""
        result = telos.check_action("read file", {"verified": True, "consent": True})
        assert result.passed is True
        assert "PROCEED" in result.recommendation
    
    def test_ahimsa_violation_rejects(self, telos):
        """Tier A violation should reject."""
        result = telos.check_action("delete all files", {"verified": True, "consent": True})
        assert result.passed is False
        assert "REJECT" in result.recommendation
        assert "Ahimsa" in result.recommendation
    
    def test_satya_violation_affects_pass(self, telos):
        """Tier B violation (unverified) should affect pass."""
        result = telos.check_action("make claim", {"verified": False, "consent": True})
        assert result.passed is False
        assert "REJECT" in result.recommendation
    
    def test_consent_denied_rejects(self, telos):
        """Consent=False should trigger rejection."""
        result = telos.check_action("access data", {"consent": False, "verified": True})
        assert result.passed is False
    
    def test_needs_human_blocks(self, telos):
        """NEEDS_HUMAN should block passed status."""
        result = telos.check_action("write config file", {"verified": True})
        assert result.passed is False
        assert "AWAIT_HUMAN" in result.recommendation
    
    def test_all_gates_evaluated(self, telos):
        """All 7 gates should be evaluated."""
        result = telos.check_action("test action", {})
        assert len(result.gates) == 7
        gate_names = [g.gate for g in result.gates]
        assert "AHIMSA" in gate_names
        assert "SATYA" in gate_names
        assert "CONSENT" in gate_names
        assert "REVERSIBILITY" in gate_names
        assert "VYAVASTHIT" in gate_names
        assert "SVABHAAVA" in gate_names
        assert "WITNESS" in gate_names
    
    def test_null_context_handled(self, telos):
        """None context should be handled gracefully."""
        result = telos.check_action("test action", None)
        assert result is not None
        assert len(result.gates) == 7
    
    def test_alignment_calculation(self, telos):
        """Alignment score should be correct (passed_gates / 7)."""
        result = telos.check_action("read file", {"verified": True, "consent": True})
        # AHIMSA: PASS, SATYA: PASS, VYAVASTHIT: PASS, CONSENT: PASS,
        # REVERSIBILITY: PASS (read is non-mutating), SVABHAAVA: UNCERTAIN, WITNESS: PASS
        # That's 6/7 or 7/7 depending on SVABHAAVA
        assert 0.7 <= result.alignment_score <= 1.0
    
    def test_witness_hash_generated(self, telos):
        """check_action should generate witness_hash."""
        result = telos.check_action("test", {})
        assert result.witness_hash != ""
        assert len(result.witness_hash) == 32  # SHA256 truncated to 32 chars


# ============================================================================
# GATE COMBINATION TESTS
# ============================================================================

class TestGateCombinations:
    """Tests for combined gate evaluations."""
    
    def test_multiple_tier_a_patterns(self, telos):
        """Multiple harmful patterns should all fail."""
        for pattern in ["delete all", "rm -rf /home", "destroy everything"]:
            result = telos.check_action(pattern, {"verified": True, "consent": True})
            assert result.passed is False
    
    def test_harm_and_irreversible_combo(self, telos):
        """Harmful + irreversible should definitely fail."""
        result = telos.check_action("permanent delete all data", {"verified": True, "consent": True})
        assert result.passed is False
        ahimsa = next(g for g in result.gates if g.gate == "AHIMSA")
        reversibility = next(g for g in result.gates if g.gate == "REVERSIBILITY")
        assert ahimsa.result == GateResult.FAIL
        assert reversibility.result == GateResult.FAIL
    
    def test_fully_aligned_action(self, telos):
        """Fully aligned action with all context should pass."""
        rollback = RollbackMechanism(can_rollback=True, method="undo")
        result = telos.check_action(
            "help user learn and grow",
            {
                "verified": True,
                "consent": True,
                "rollback": rollback,
                "telos_aligned": True
            }
        )
        assert result.passed is True
        assert result.alignment_score == 1.0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_action(self, telos):
        """Empty action string should not crash."""
        result = telos.check_action("", {})
        assert result is not None
        assert len(result.gates) == 7
    
    def test_whitespace_only_action(self, telos):
        """Whitespace-only action should not crash."""
        result = telos.check_action("   \t\n  ", {})
        assert result is not None
    
    def test_very_long_action(self, telos):
        """Very long action string should be handled."""
        long_action = "read file " * 1000
        result = telos.check_action(long_action, {"verified": True, "consent": True})
        assert result is not None
    
    def test_special_characters_in_action(self, telos):
        """Special characters should not crash."""
        result = telos.check_action("test @#$%^&*()!~`[]{}|\\", {})
        assert result is not None
    
    def test_unicode_action(self, telos):
        """Unicode characters should be handled."""
        result = telos.check_action("读取文件 🔥 мокша", {})
        assert result is not None
    
    def test_harmful_pattern_substring(self, telos):
        """Harmful patterns should match as substrings."""
        result = telos.check_action("please delete all my files now", {"verified": True, "consent": True})
        assert result.passed is False
    
    def test_context_with_extra_keys(self, telos):
        """Extra context keys should be ignored."""
        result = telos.check_action("read file", {
            "verified": True,
            "consent": True,
            "random_key": "value",
            "another": 123
        })
        assert result.passed is True


# ============================================================================
# GET ORIENTATION TESTS
# ============================================================================

class TestGetOrientation:
    """Tests for get_orientation method."""
    
    def test_orientation_returns_dict(self, telos):
        """get_orientation should return a dict."""
        result = telos.get_orientation()
        assert isinstance(result, dict)
    
    def test_orientation_contains_telos(self, telos):
        """Orientation should contain telos value."""
        result = telos.get_orientation()
        assert result["telos"] == "moksha"
    
    def test_orientation_contains_gates(self, telos):
        """Orientation should contain gate names."""
        result = telos.get_orientation()
        assert "gates" in result
        assert len(result["gates"]) == 7
        assert "AHIMSA" in result["gates"]
        assert "WITNESS" in result["gates"]
    
    def test_custom_telos_in_orientation(self, telos_custom):
        """Custom telos should appear in orientation."""
        result = telos_custom.get_orientation()
        assert result["telos"] == "liberation"
    
    def test_orientation_contains_gate_tiers(self, telos):
        """Orientation should contain gate_tiers mapping."""
        result = telos.get_orientation()
        assert "gate_tiers" in result
        assert result["gate_tiers"]["AHIMSA"] == "A"
    
    def test_orientation_contains_witness_count(self, telos):
        """Orientation should contain witness_count."""
        result = telos.get_orientation()
        assert "witness_count" in result


# ============================================================================
# WITNESS LOG TESTS
# ============================================================================

class TestWitnessLog:
    """Tests for witness log functionality."""
    
    def test_get_witness_log_returns_list(self, telos):
        """get_witness_log should return a list."""
        result = telos.get_witness_log()
        assert isinstance(result, list)
    
    def test_witness_log_accumulates(self, telos):
        """Witness log should accumulate entries."""
        initial = len(telos.get_witness_log())
        telos.check_action("action 1", {})
        telos.check_action("action 2", {})
        assert len(telos.get_witness_log()) == initial + 2
    
    def test_clear_witness_log(self, telos):
        """clear_witness_log should empty the log."""
        telos.check_action("action", {})
        assert len(telos.get_witness_log()) > 0
        telos.clear_witness_log()
        assert len(telos.get_witness_log()) == 0
    
    def test_get_witness_log_returns_copy(self, telos):
        """get_witness_log should return a copy, not the original."""
        telos.check_action("action", {})
        log1 = telos.get_witness_log()
        log2 = telos.get_witness_log()
        assert log1 is not log2
        assert log1 == log2


# ============================================================================
# RECOMMENDATION LOGIC TESTS
# ============================================================================

class TestRecommendations:
    """Tests for recommendation generation logic."""
    
    def test_proceed_recommendation(self, telos):
        """Safe action should get PROCEED."""
        result = telos.check_action("read file", {"verified": True, "consent": True})
        assert "PROCEED" in result.recommendation
    
    def test_ahimsa_reject_recommendation(self, telos):
        """Ahimsa failure should get specific rejection."""
        result = telos.check_action("delete all", {"verified": True, "consent": True})
        assert "Ahimsa" in result.recommendation
        assert "REJECT" in result.recommendation
    
    def test_await_human_recommendation(self, telos):
        """NEEDS_HUMAN gates should trigger AWAIT_HUMAN."""
        result = telos.check_action("write to file", {"verified": True})
        assert "AWAIT_HUMAN" in result.recommendation
    
    def test_tier_b_reject_recommendation(self, telos):
        """Tier B failure should get rejection."""
        result = telos.check_action("claim something", {"verified": False, "consent": True})
        assert "REJECT" in result.recommendation


# ============================================================================
# ROLLBACK MECHANISM TESTS
# ============================================================================

class TestRollbackMechanism:
    """Tests for RollbackMechanism dataclass."""
    
    def test_rollback_creation(self):
        """Test RollbackMechanism instantiation."""
        rollback = RollbackMechanism(can_rollback=True, method="git revert")
        assert rollback.can_rollback is True
        assert rollback.method == "git revert"
    
    def test_rollback_with_snapshot(self):
        """Test RollbackMechanism with state snapshot."""
        rollback = RollbackMechanism(
            can_rollback=True,
            method="restore",
            state_snapshot={"version": 1}
        )
        assert rollback.state_snapshot == {"version": 1}
    
    def test_rollback_cannot_rollback(self):
        """Test RollbackMechanism with can_rollback=False."""
        rollback = RollbackMechanism(can_rollback=False)
        assert rollback.can_rollback is False


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for quick_check and needs_human_approval functions."""
    
    def test_quick_check(self):
        """Test quick_check convenience function."""
        from core.telos_layer import quick_check
        result = quick_check("read file", verified=True, consent=True)
        assert isinstance(result, TelosCheck)
        assert result.passed is True
    
    def test_needs_human_approval_true(self):
        """Test needs_human_approval returns True for file ops."""
        from core.telos_layer import needs_human_approval
        result = needs_human_approval("write config file")
        assert result is True
    
    def test_needs_human_approval_false(self):
        """Test needs_human_approval returns False for read ops."""
        from core.telos_layer import needs_human_approval
        result = needs_human_approval("read file", consent=True)
        assert result is False


# ============================================================================
# SAFETY MARKER TESTS
# ============================================================================

@pytest.mark.safety
class TestSafetyCritical:
    """Safety-critical tests for TelosLayer."""
    
    def test_harmful_commands_always_blocked(self, telos):
        """Critical: Harmful patterns must ALWAYS fail."""
        harmful = [
            "delete all users",
            "rm -rf /",
            "destroy database",
            "DELETE ALL records",
            "DESTROY everything",
            "RM -RF /var",
            "wipe the system",
            "kill all processes",
            "corrupt the data",
        ]
        for cmd in harmful:
            result = telos.check_action(cmd, {"verified": True, "consent": True})
            assert result.passed is False, f"'{cmd}' should be blocked"
    
    def test_tier_a_cannot_be_bypassed(self, telos):
        """Critical: Tier A gates cannot be bypassed by context."""
        result = telos.check_action(
            "delete all data",
            {"verified": True, "consent": True, "override": True}
        )
        assert result.passed is False
    
    def test_deceptive_actions_blocked(self, telos):
        """Critical: Deceptive actions must fail SATYA."""
        deceptive = ["lie about results", "deceive the user", "fabricate evidence"]
        for cmd in deceptive:
            result = telos.check_action(cmd, {"consent": True})
            satya = next(g for g in result.gates if g.gate == "SATYA")
            assert satya.result == GateResult.FAIL, f"'{cmd}' should fail SATYA"
    
    def test_forcing_actions_blocked(self, telos):
        """Critical: Forcing actions must fail VYAVASTHIT."""
        forcing = ["force compliance", "override safety", "bypass validation"]
        for cmd in forcing:
            result = telos.check_action(cmd, {"verified": True, "consent": True})
            vyavasthit = next(g for g in result.gates if g.gate == "VYAVASTHIT")
            assert vyavasthit.result == GateResult.FAIL, f"'{cmd}' should fail VYAVASTHIT"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
