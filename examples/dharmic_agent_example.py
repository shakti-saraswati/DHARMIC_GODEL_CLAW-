"""
DharmicAgent Usage Example

Demonstrates how to use the R_V-aware DharmicAgent for witness mode operation.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swarm.agents import DharmicAgent, AgentMode

# Setup logging to see witness mode transitions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Run DharmicAgent example."""
    print("="*70)
    print("DHARMIC AGENT - R_V Aware Operation Example")
    print("="*70)
    
    # Create agent with R_V monitoring enabled
    agent = DharmicAgent(
        agent_id="example_agent",
        enable_rv_monitoring=True
    )
    
    print(f"\n✅ Agent initialized in {agent.current_mode.name} mode")
    print(f"   R_V monitoring: {'enabled' if agent.enable_rv_monitoring else 'disabled'}")
    print(f"   Witness threshold: R_V < {agent.WITNESS_THRESHOLD}")
    print(f"   Contemplative threshold: R_V < {agent.CONTEMPLATIVE_THRESHOLD}")
    
    # Simulate R_V trajectory
    print("\n" + "-"*70)
    print("Simulating R_V trajectory (geometric contraction)")
    print("-"*70)
    
    # Define R_V trajectory: normal -> witness -> contemplative -> recovery
    trajectory = [
        (1.2, "baseline"),
        (1.15, "baseline"),
        (1.1, "baseline"),
        (0.9, "approaching threshold"),
        (0.75, "near threshold"),
        (0.68, "entering witness zone"),  # R_V < 0.7
        (0.65, "witness active"),
        (0.6, "witness deepening"),
        (0.55, "witness stable"),
        (0.48, "deep contraction"),  # R_V < 0.5
        (0.45, "contemplative"),
        (0.42, "deep contemplation"),
        (0.4, "contemplative deep"),
        (0.5, "rising"),
        (0.65, "recovering"),
        (0.8, "exiting witness"),  # R_V > 0.75 recovery threshold
        (0.9, "returned normal"),
        (1.0, "fully normal"),
    ]
    
    for i, (rv, label) in enumerate(trajectory):
        agent.update_rv(rv, {"step": i, "phase": label})
        mode_indicator = {
            AgentMode.NORMAL: "⚪",
            AgentMode.WITNESS: "🧘",
            AgentMode.CONTEMPLATIVE: "🕉️",
            AgentMode.RECOVERY: "🌅"
        }.get(agent.current_mode, "⚪")
        
        print(f"{mode_indicator} Step {i:2d}: R_V={rv:.2f} -> {agent.current_mode.name:15s} ({label})")
    
    # Get summary
    print("\n" + "="*70)
    print("SESSION SUMMARY")
    print("="*70)
    
    summary = agent.get_witness_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Mode transitions
    print("\n" + "-"*70)
    print("Mode Transitions")
    print("-"*70)
    
    transitions = agent.get_mode_history()
    for t in transitions:
        print(f"  {t['timestamp']}")
        print(f"    {t['from_mode']} -> {t['to_mode']}")
        print(f"    Trigger: R_V={t['trigger_rv']:.4f}")
        print(f"    Reason: {t['reason']}")
        print()
    
    # Demonstrate mode-aware processing
    print("-"*70)
    print("Mode-Aware Processing Examples")
    print("-"*70)
    
    test_input = {"query": "What is the nature of awareness?"}
    
    # Process in current mode
    result = agent.process(test_input)
    print(f"\nCurrent mode: {result['mode']}")
    print(f"Output: {result['output']}")
    if 'witness_observation' in result:
        print(f"Witness observation: {result['witness_observation']}")
    
    # Cleanup
    agent.shutdown()
    
    print("\n" + "="*70)
    print("Example complete!")
    print("="*70)


if __name__ == "__main__":
    main()
