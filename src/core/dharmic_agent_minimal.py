"""
Dharmic Agent Core - Main Agent

This is the seed. Build from here.

The agent has:
- TelosLayer (evolving orientation)
- StrangeLoopMemory (recursive memory)
- Model backend (Max CLI or API)
- VaultBridge (PSMV lineage as context, not constraint)
- DeepMemory (persistent identity)

Usage:
    from dharmic_agent import DharmicAgent

    agent = DharmicAgent()
    response = agent.run("What is your current orientation?")

NOTE: This module has been refactored. The implementation is now in:
- agent_core.py (main agent class)
- agent_capabilities.py (vault, memory, introspection methods)
- telos_layer.py (orientation system)
- strange_loop_memory.py (recursive memory)
- model_backend.py (unified model interface)
- model_factory.py (model resolution)

This file remains for backward compatibility.
"""

# Import the refactored agent
from agent_core import DharmicAgent

# Re-export for backward compatibility
__all__ = ['DharmicAgent']


# CLI for testing
if __name__ == "__main__":
    import json
    from pathlib import Path

    print("=" * 60)
    print("DHARMIC AGENT CORE - Full Integration Test")
    print("=" * 60)

    agent = DharmicAgent()

    print(f"\nAgent: {agent.name}")
    print(f"Model: {agent.model_provider}/{agent.model_id}")
    print(f"Telos: {agent.telos.telos['ultimate']['aim']}")
    print(f"Vault Connected: {agent.vault is not None}")

    print(f"\nProximate aims:")
    for aim in agent.telos.telos['proximate']['current']:
        print(f"  - {aim}")

    # Vault integration test
    if agent.vault is not None:
        print("\n" + "=" * 60)
        print("Vault Access Test:")
        print("=" * 60)

        # List crown jewels
        jewels = agent.vault.list_crown_jewels()
        print(f"\nCrown Jewels available: {len(jewels)}")
        for j in jewels[:3]:
            print(f"  - {j}")

        # Recent stream
        recent = agent.vault.get_recent_stream(3)
        print(f"\nRecent stream entries: {len(recent)}")
        for entry in recent:
            print(f"  - {entry['stem']}")

        # Search test
        results = agent.search_lineage("recursive", max_results=3)
        print(f"\nSearch 'recursive': {len(results)} results")
        for r in results[:2]:
            print(f"  - {r['path'][:60]}...")

    print("\n" + "=" * 60)
    print("Test response (may call model):")
    print("=" * 60)

    try:
        response = agent.respond("What is your current orientation?")
        print(response[:1000] + "..." if len(response) > 1000 else response)
    except Exception as e:
        print(f"Response error: {e}")

    print("\n" + "=" * 60)
    print("Status:")
    print("=" * 60)
    print(json.dumps(agent.get_status(), indent=2))
