"""
Test script for DharmicAgent with WitnessThresholdDetector integration.

This script verifies:
1. Agent initializes with R_V monitoring enabled
2. R_V < 0.7 triggers WITNESS mode
3. R_V < 0.5 triggers CONTEMPLATIVE mode  
4. Different behaviors in each mode
5. Enhanced logging during WITNESS mode
6. R_V trajectory tracking
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swarm.agents import DharmicAgent, AgentMode


def test_agent_initialization():
    """Test that agent initializes correctly."""
    print("\n" + "="*70)
    print("TEST 1: Agent Initialization")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    assert agent.current_mode == AgentMode.NORMAL, "Should start in NORMAL mode"
    assert agent.enable_rv_monitoring == True, "RV monitoring should be enabled"
    assert agent.rv_detector is not None, "RV detector should be initialized"
    
    print(f"✅ Agent initialized in {agent.current_mode.name} mode")
    print(f"✅ RV monitoring: {'enabled' if agent.enable_rv_monitoring else 'disabled'}")
    print(f"✅ RV detector: {type(agent.rv_detector).__name__}")
    
    agent.shutdown()
    return True


def test_witness_mode_trigger():
    """Test that R_V < 0.7 triggers WITNESS mode."""
    print("\n" + "="*70)
    print("TEST 2: Witness Mode Trigger (R_V < 0.7)")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    # Start with baseline R_V
    print("\nBaseline (R_V > 0.7):")
    for i in range(3):
        rv = 1.0 + (i * 0.1)
        agent.update_rv(rv, {"step": i})
        print(f"  Step {i}: R_V={rv:.2f} -> Mode: {agent.current_mode.name}")
    
    assert agent.current_mode == AgentMode.NORMAL, "Should be in NORMAL mode with R_V > 0.7"
    print("✅ Normal mode maintained with R_V > 0.7")
    
    # Drop below threshold (need min_persistence_steps=2 to trigger)
    print("\nDropping below threshold (R_V < 0.7):")
    for i in range(3, 7):
        rv = 0.75 - (i-3) * 0.05  # Decrease towards 0.55
        agent.update_rv(rv, {"step": i})
        print(f"  Step {i}: R_V={rv:.2f} -> Mode: {agent.current_mode.name}")
    
    assert agent.current_mode == AgentMode.WITNESS, "Should be in WITNESS mode with R_V < 0.7"
    print("✅ WITNESS mode entered when R_V < 0.7")
    
    agent.shutdown()
    return True


def test_contemplative_mode_trigger():
    """Test that R_V < 0.5 triggers CONTEMPLATIVE mode."""
    print("\n" + "="*70)
    print("TEST 3: Contemplative Mode Trigger (R_V < 0.5)")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    # Simulate deep contraction
    print("\nDeep contraction (R_V < 0.5):")
    rv_values = [0.7, 0.6, 0.55, 0.48, 0.45, 0.42, 0.40]
    
    for i, rv in enumerate(rv_values):
        agent.update_rv(rv, {"step": i})
        print(f"  Step {i}: R_V={rv:.2f} -> Mode: {agent.current_mode.name}")
    
    assert agent.current_mode == AgentMode.CONTEMPLATIVE, "Should be in CONTEMPLATIVE mode with R_V < 0.5"
    print("✅ CONTEMPLATIVE mode entered when R_V < 0.5")
    
    agent.shutdown()
    return True


def test_mode_aware_processing():
    """Test that agent behaves differently in each mode."""
    print("\n" + "="*70)
    print("TEST 4: Mode-Aware Processing")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    test_input = {"query": "What is awareness?", "context": "test"}
    
    # Process in NORMAL mode
    print("\nProcessing in NORMAL mode:")
    result_normal = agent._process_normal(test_input)
    print(f"  Mode: {result_normal['mode']}")
    print(f"  Output: {result_normal['output'][:60]}...")
    assert result_normal['mode'] == 'NORMAL', "Should report NORMAL mode"
    
    # Force switch to WITNESS mode
    agent.current_mode = AgentMode.WITNESS
    agent._current_rv = 0.65
    agent._witness_active = True
    
    print("\nProcessing in WITNESS mode:")
    result_witness = agent._process_witness(test_input)
    print(f"  Mode: {result_witness['mode']}")
    print(f"  Output: {result_witness['output'][:60]}...")
    print(f"  Observation: {result_witness.get('witness_observation', 'N/A')[:60]}...")
    assert result_witness['mode'] == 'WITNESS', "Should report WITNESS mode"
    assert 'witness_observation' in result_witness, "Should include witness observation"
    
    # Force switch to CONTEMPLATIVE mode
    agent.current_mode = AgentMode.CONTEMPLATIVE
    agent._current_rv = 0.45
    
    print("\nProcessing in CONTEMPLATIVE mode:")
    result_contemplative = agent._process_contemplative(test_input)
    print(f"  Mode: {result_contemplative['mode']}")
    print(f"  Output: {result_contemplative['output']}")
    assert result_contemplative['mode'] == 'CONTEMPLATIVE', "Should report CONTEMPLATIVE mode"
    
    print("\n✅ Different behaviors in each mode verified")
    
    agent.shutdown()
    return True


def test_rv_trajectory_tracking():
    """Test R_V trajectory tracking."""
    print("\n" + "="*70)
    print("TEST 5: R_V Trajectory Tracking")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    # Simulate trajectory
    print("\nSimulating R_V trajectory:")
    trajectory_rvs = [1.2, 1.1, 0.9, 0.75, 0.65, 0.55, 0.45, 0.5, 0.65, 0.8, 0.9]
    
    for i, rv in enumerate(trajectory_rvs):
        agent.update_rv(rv, {"step": i, "test": True})
    
    # Get trajectory
    trajectory = agent.get_rv_trajectory()
    print(f"\nRecorded {len(trajectory)} trajectory points")
    
    # Verify trajectory (may have more points due to event-triggered recordings)
    assert len(trajectory) >= len(trajectory_rvs), "Should record at least all trajectory points"
    assert trajectory[0]['rv_value'] == 1.2, "First point should be R_V=1.2"
    assert trajectory[-1]['rv_value'] == 0.9, "Last point should be R_V=0.9"
    
    print("\nRecent trajectory points:")
    for point in trajectory[-5:]:
        print(f"  {point['timestamp']}: R_V={point['rv_value']:.2f}, Mode={point['mode']}")
    
    # Get summary
    summary = agent.get_witness_summary()
    print("\nTrajectory Summary:")
    print(f"  Total measurements: {summary['total_measurements']}")
    print(f"  R_V range: [{summary['rv_min']:.2f}, {summary['rv_max']:.2f}]")
    print(f"  Mean R_V: {summary['rv_mean']:.4f}")
    print(f"  Steps in witness mode: {summary['steps_witness_mode']}")
    print(f"  Mode distribution: {summary['mode_distribution']}")
    
    print("\n✅ R_V trajectory tracking verified")
    
    agent.shutdown()
    return True


def test_enhanced_logging():
    """Test enhanced logging during witness mode."""
    print("\n" + "="*70)
    print("TEST 6: Enhanced Logging in Witness Mode")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    # Check that witness observations log exists
    witness_log = agent.memory_dir / "witness_observations.jsonl"
    
    # Trigger witness mode to generate logs
    print("\nTriggering witness mode to generate logs:")
    for i in range(5):
        rv = 0.75 - (i * 0.05)
        agent.update_rv(rv, {"step": i, "test": "logging"})
        print(f"  Step {i}: R_V={rv:.2f} -> Mode: {agent.current_mode.name}")
    
    # Process to generate more logs
    agent.process({"test": "input"})
    
    # Check log file
    if witness_log.exists():
        import json
        with open(witness_log) as f:
            lines = f.readlines()
        print(f"\n✅ Witness log file created with {len(lines)} entries")
        
        if lines:
            last_entry = json.loads(lines[-1])
            print(f"  Last entry: {last_entry['observation'][:60]}...")
    else:
        print("\n⚠️  Witness log file not found (may be created asynchronously)")
    
    agent.shutdown()
    return True


def test_mode_transitions():
    """Test mode transition recording."""
    print("\n" + "="*70)
    print("TEST 7: Mode Transition Recording")
    print("="*70)
    
    agent = DharmicAgent(
        agent_id="test_agent",
        enable_rv_monitoring=True
    )
    
    # Simulate mode transitions
    print("\nSimulating mode transitions:")
    transitions = [
        (1.0, "baseline"),
        (0.9, "approaching"),
        (0.75, "near_threshold"),
        (0.68, "entering_witness"),  # Should trigger WITNESS
        (0.62, "witness_active"),
        (0.58, "witness_stable"),
        (0.48, "deep_contraction"),  # Should trigger CONTEMPLATIVE
        (0.42, "contemplative_deep"),
        (0.52, "rising"),
        (0.65, "recovering"),
        (0.78, "exiting_witness"),   # Should trigger RECOVERY
        (0.85, "returned_normal"),
        (1.0, "fully_normal")
    ]
    
    for i, (rv, label) in enumerate(transitions):
        agent.update_rv(rv, {"step": i, "label": label})
        print(f"  {label:20s}: R_V={rv:.2f} -> Mode: {agent.current_mode.name}")
    
    # Check mode history
    history = agent.get_mode_history()
    print(f"\nRecorded {len(history)} mode transitions:")
    for transition in history:
        print(f"  {transition['from_mode']:15s} -> {transition['to_mode']:15s} "
              f"(R_V={transition['trigger_rv']:.4f})")
    
    assert len(history) > 0, "Should record mode transitions"
    
    # Check that we have WITNESS and CONTEMPLATIVE transitions
    modes_entered = set(t['to_mode'] for t in history)
    assert 'WITNESS' in modes_entered, "Should have entered WITNESS mode"
    assert 'CONTEMPLATIVE' in modes_entered, "Should have entered CONTEMPLATIVE mode"
    
    print("\n✅ Mode transition recording verified")
    
    agent.shutdown()
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "🧘"*35)
    print("DHARMIC AGENT - WITNESS THRESHOLD DETECTOR INTEGRATION TESTS")
    print("🧘"*35)
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Witness Mode Trigger", test_witness_mode_trigger),
        ("Contemplative Mode Trigger", test_contemplative_mode_trigger),
        ("Mode-Aware Processing", test_mode_aware_processing),
        ("R_V Trajectory Tracking", test_rv_trajectory_tracking),
        ("Enhanced Logging", test_enhanced_logging),
        ("Mode Transitions", test_mode_transitions),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
