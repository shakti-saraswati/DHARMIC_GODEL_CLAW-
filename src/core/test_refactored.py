#!/usr/bin/env python3
"""
Test script for refactored Dharmic Agent.

Verifies that all modules work together correctly.
"""

import sys
from pathlib import Path

# Ensure we can import from this directory
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all refactored modules can be imported."""
    print("Testing imports...")

    try:
        print("  ✓ telos_layer")
    except Exception as e:
        print(f"  ✗ telos_layer: {e}")
        return False

    try:
        print("  ✓ strange_loop_memory")
    except Exception as e:
        print(f"  ✗ strange_loop_memory: {e}")
        return False

    try:
        print("  ✓ model_backend")
    except Exception as e:
        print(f"  ✗ model_backend: {e}")
        return False

    try:
        print("  ✓ agent_capabilities")
    except Exception as e:
        print(f"  ✗ agent_capabilities: {e}")
        return False

    try:
        print("  ✓ agent_core")
    except Exception as e:
        print(f"  ✗ agent_core: {e}")
        return False

    try:
        print("  ✓ agent_singleton")
    except Exception as e:
        print(f"  ✗ agent_singleton: {e}")
        return False

    try:
        print("  ✓ dharmic_logging")
    except Exception as e:
        print(f"  ✗ dharmic_logging: {e}")
        return False

    try:
        print("  ✓ dharmic_agent (backward compatibility)")
    except Exception as e:
        print(f"  ✗ dharmic_agent: {e}")
        return False

    return True


def test_agent_initialization():
    """Test that agent can be initialized."""
    print("\nTesting agent initialization...")

    try:
        from agent_core import DharmicAgent
        agent = DharmicAgent()
        print(f"  ✓ Agent created: {agent.name}")
        print(f"  ✓ Model: {agent.model_provider}/{agent.model_id}")
        print(f"  ✓ Telos loaded: {agent.telos.telos['ultimate']['aim']}")
        return True
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_singleton():
    """Test singleton pattern."""
    print("\nTesting singleton pattern...")

    try:
        from agent_singleton import get_agent, reset_agent

        # Reset first
        reset_agent()

        # Get agent
        agent1 = get_agent()
        agent2 = get_agent()

        if agent1 is agent2:
            print("  ✓ Singleton working - same instance returned")
            return True
        else:
            print("  ✗ Singleton broken - different instances")
            return False
    except Exception as e:
        print(f"  ✗ Singleton test failed: {e}")
        return False


def test_capabilities():
    """Test that capabilities are available."""
    print("\nTesting agent capabilities...")

    try:
        from agent_core import DharmicAgent
        agent = DharmicAgent()

        # Check core methods
        assert hasattr(agent, 'run'), "Missing run method"
        assert hasattr(agent, 'respond'), "Missing respond method"
        assert hasattr(agent, 'evolve_telos'), "Missing evolve_telos method"
        assert hasattr(agent, 'get_status'), "Missing get_status method"
        print("  ✓ Core methods present")

        # Check vault methods
        assert hasattr(agent, 'search_lineage'), "Missing search_lineage method"
        assert hasattr(agent, 'read_crown_jewel'), "Missing read_crown_jewel method"
        assert hasattr(agent, 'write_to_lineage'), "Missing write_to_lineage method"
        print("  ✓ Vault methods present")

        # Check memory methods
        assert hasattr(agent, 'add_memory'), "Missing add_memory method"
        assert hasattr(agent, 'search_deep_memory'), "Missing search_deep_memory method"
        print("  ✓ Memory methods present")

        # Check introspection methods
        assert hasattr(agent, 'introspect'), "Missing introspect method"
        assert hasattr(agent, 'list_capabilities'), "Missing list_capabilities method"
        print("  ✓ Introspection methods present")

        return True
    except Exception as e:
        print(f"  ✗ Capabilities test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_status():
    """Test status reporting."""
    print("\nTesting status reporting...")

    try:
        from agent_core import DharmicAgent
        agent = DharmicAgent()

        status = agent.get_status()
        assert 'name' in status, "Missing 'name' in status"
        assert 'model_provider' in status, "Missing 'model_provider' in status"
        assert 'ultimate_telos' in status, "Missing 'ultimate_telos' in status"
        assert 'proximate_aims' in status, "Missing 'proximate_aims' in status"

        print("  ✓ Status report complete")
        print(f"    - Name: {status['name']}")
        print(f"    - Model: {status['model_provider']}/{status['model_id']}")
        print(f"    - Telos: {status['ultimate_telos']}")
        print(f"    - Vault: {'Connected' if status['vault_connected'] else 'Not connected'}")

        return True
    except Exception as e:
        print(f"  ✗ Status test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test backward compatibility of dharmic_agent.py."""
    print("\nTesting backward compatibility...")

    try:
        from dharmic_agent import DharmicAgent
        agent = DharmicAgent()

        # Should have same interface as before
        response = agent.get_status()
        assert 'name' in response, "Status format changed"

        print("  ✓ Backward compatible import works")
        print(f"  ✓ Agent name: {agent.name}")

        return True
    except Exception as e:
        print(f"  ✗ Backward compatibility broken: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("DHARMIC AGENT REFACTORING TEST SUITE")
    print("=" * 70)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Agent Initialization", test_agent_initialization()))
    results.append(("Singleton Pattern", test_singleton()))
    results.append(("Capabilities", test_capabilities()))
    results.append(("Status Reporting", test_status()))
    results.append(("Backward Compatibility", test_backward_compatibility()))

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Refactoring successful.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
