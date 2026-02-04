#!/usr/bin/env python3
"""
Test DGM cycle with 17-gate enforcement
=======================================
Tests the integration between:
1. DharmicClawHeartbeat (with unified gates)
2. DGM Orchestrator
3. Evidence bundle generation
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
        print(f"\n[2] Testing gate system...")
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
        print(f"    - Witness hash: {gate_result.witness_hash[:16]}...")
    
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
            self.commit_hash = None
            self.models_used = {"test": "mock"}
            self.proposal = None
    
    mock_cycle = MockCycleResult()
    evidence_bundle = heartbeat._create_evidence_bundle(gate_result, mock_cycle)
    
    print(f"    - Bundle ID: {evidence_bundle.get('bundle_id')}")
    print(f"    - Bundle hash: {evidence_bundle.get('bundle_hash')[:16]}...")
    print(f"    - Has gate eval: {'gate_evaluation' in evidence_bundle}")
    print(f"    - Has DGM cycle: {'dgm_cycle' in evidence_bundle}")
    
    # Test the actual DGM check (with dry_run=True by default)
    print(f"\n[4] Running actual DGM check with gate enforcement...")
    print("    (This may take a moment...)")
    
    result = heartbeat.run_dgm_check()
    
    print(f"    - Ran: {result.get('ran')}")
    print(f"    - Success: {result.get('success')}")
    print(f"    - Reason: {result.get('reason')}")
    print(f"    - Gates passed: {result.get('gates_passed')}")
    print(f"    - Evidence bundle ID: {result.get('evidence_bundle_id')}")
    
    if result.get('cycle_id'):
        print(f"    - Cycle ID: {result.get('cycle_id')}")
    if result.get('alignment_score'):
        print(f"    - Alignment score: {result.get('alignment_score'):.0%}")
    
    # Summary
    print(f"\n[5] Test Summary")
    print(f"    - Gates operational: {heartbeat.gate_system is not None}")
    print(f"    - DGM check executed: {result.get('ran')}")
    print(f"    - Evidence generated: {result.get('evidence_bundle_id') is not None}")
    
    # Verify success criteria
    success = (
        heartbeat.gate_system is not None and
        result.get('ran') and
        result.get('gates_passed') and
        result.get('evidence_bundle_id') is not None
    )
    
    print(f"\n{'=' * 70}")
    if success:
        print("✅ TEST PASSED: DGM cycle with 17 gates is operational")
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
