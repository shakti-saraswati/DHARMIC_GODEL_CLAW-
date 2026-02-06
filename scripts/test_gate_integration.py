#!/usr/bin/env python3
"""Quick verification that gate integration is working."""

import sys
import asyncio
from pathlib import Path

# Add swarm to path
sys.path.insert(0, str(Path(__file__).parent.parent / "swarm"))

from evaluator import EvaluatorAgent

async def test_gate_integration():
    """Test that gates are actually being invoked."""
    print("="*60)
    print("DHARMIC_CLAW Gate Integration Test")
    print("="*60)
    
    # Create evaluator
    evaluator = EvaluatorAgent()
    
    # Check gate status
    status = evaluator.get_gate_status()
    print("\nGate Configuration:")
    print(f"  Total gates: {status['total_gates']}")
    print(f"  Version: {status['version']}")
    print(f"  Enforcement: {status['enforcement_mode']}")
    print(f"  Evidence dir: {status['evidence_dir']}")
    
    # Test with a dummy proposal
    dummy_proposals = [{"id": "test", "description": "Test proposal"}]
    
    print("\nRunning gates on test proposal...")
    print("(This will take a moment as it runs all 17 gates)")
    
    result = await evaluator.evaluate_proposals(
        dummy_proposals,
        proposal_id="TEST-001",
        dry_run=True  # Use dry-run to avoid actual execution
    )
    
    print("\nResults:")
    print(f"  Overall score: {result.overall_score:.2f}")
    print(f"  Gates passed: {result.gates_passed}")
    print(f"  Gates failed: {result.gates_failed}")
    print(f"  Gates warned: {result.gates_warned}")
    print(f"  Evidence hash: {result.evidence_bundle_hash[:16] if result.evidence_bundle_hash else 'N/A'}...")
    
    if result.proposals:
        print(f"\nProposal status: {'APPROVED' if result.proposals[0].approved else 'REJECTED'}")
        print(f"Feedback:\n{result.proposals[0].feedback}")
    
    print("\n" + "="*60)
    print("Integration test complete!")
    print("="*60)
    
    return result

if __name__ == "__main__":
    asyncio.run(test_gate_integration())
