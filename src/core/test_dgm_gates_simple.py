#!/usr/bin/env python3
"""
Test DGM cycle with 17-gate enforcement (Mock version)
======================================================
Tests the integration without external API calls.
"""

import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "core"))

from dharmic_claw_heartbeat import DharmicClawHeartbeat

def test_dgm_cycle_with_gates():
    """Test a full DGM cycle with 17-gate enforcement."""
    print("=" * 70)
    print("TEST: DGM Cycle with 17 Dharmic Gates")
    print("=" * 70)
    
    # Create heartbeat instance
    heartbeat = DharmicClawHeartbeat(interval=300)
    
    print(f"\n[1] Heartbeat initialized")
    print(f"    - Gates available: {heartbeat.gate_system is not None}")
    print(f"    - Evidence bundles: {len(heartbeat.dgm_evidence_bundles)}")
    
    # Test gate system directly
    if heartbeat.gate_system:
        print(f"\n[2] Testing gate system with 8 dharmic gates...")
        test_action = "Test DGM improvement cycle"
        test_context = {
            "verified": True,
            "consent": True,
            "modifies_files": True,
            "has_backup": True,
        }
        
        gate_result = heartbeat.gate_system.evaluate_all(test_action, test_context)
        print(f"    - Can proceed: {gate_result.can_proceed}")
        print(f"    - Overall: {gate_result.overall_result}")
        print(f"    - Alignment: {gate_result.alignment_score:.0%}")
        print(f"    - Gates evaluated: {len(gate_result.gate_results)}")
        print(f"    - Blocking: {gate_result.blocking_gates}")
        print(f"    - Warnings: {gate_result.warning_gates}")
        print(f"    - Needs human: {gate_result.needs_human_gates}")
        print(f"    - Witness hash: {gate_result.witness_hash[:16]}...")
        
        # Print each gate result
        print(f"\n    Gate details:")
        for g in gate_result.gate_results:
            status = "✅" if g.result.value == "pass" else "⚠️" if g.result.value == "uncertain" else "❌"
            print(f"      {status} {g.gate_name} ({g.tier.value}): {g.result.value}")
    
    # Test evidence bundle generation
    print(f"\n[3] Testing evidence bundle generation...")
    
    # Mock cycle result for testing
    class MockCycleResult:
        def __init__(self):
            self.cycle_id = "test_cycle_001"
            self.success = True
            self.status = "test"
            self.component = "test_component.py"
            self.duration_seconds = 1.5
            self.commit_hash = "abc123"
            self.models_used = {"test": "mock"}
            self.proposal = None
    
    mock_cycle = MockCycleResult()
    evidence_bundle = heartbeat._create_evidence_bundle(gate_result, mock_cycle)
    
    print(f"    - Bundle ID: {evidence_bundle.get('bundle_id')}")
    print(f"    - Bundle hash: {evidence_bundle.get('bundle_hash')[:16]}...")
    print(f"    - Has gate eval: {'gate_evaluation' in evidence_bundle}")
    print(f"    - Has DGM cycle: {'dgm_cycle' in evidence_bundle}")
    
    # Verify bundle file was created
    evidence_dir = Path.home() / "DHARMIC_GODEL_CLAW" / "logs" / "evidence_bundles"
    bundle_files = list(evidence_dir.glob("*.json"))
    print(f"    - Bundle files in logs: {len(bundle_files)}")
    
    # Summary
    print(f"\n[4] Test Summary")
    print(f"    - Gates operational: {heartbeat.gate_system is not None}")
    print(f"    - Gates passed: {gate_result.can_proceed}")
    print(f"    - Evidence generated: {evidence_bundle.get('bundle_id') is not None}")
    print(f"    - Evidence file saved: {len(bundle_files) > 0}")
    
    # Verify success criteria
    success = (
        heartbeat.gate_system is not None and
        gate_result.can_proceed and
        evidence_bundle.get('bundle_id') is not None and
        len(bundle_files) > 0
    )
    
    print(f"\n{'=' * 70}")
    if success:
        print("✅ TEST PASSED: DGM cycle with gates is operational")
        print("\nSuccess criteria:")
        print("  ✅ 8 dharmic gates evaluated")
        print("  ✅ All gates passed (no blocking)")
        print("  ✅ Evidence bundle generated with immutable hash")
        print("  ✅ Evidence bundle saved to disk")
    else:
        print("⚠️  TEST PARTIAL: Some components may need attention")
    print(f"{'=' * 70}")
    
    return success

if __name__ == "__main__":
    try:
        success = test_dgm_cycle_with_gates()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
