#!/usr/bin/env python3
"""
Interactive chat with the Agno-native Dharmic Agent.

Usage:
    python3 agno_chat.py
"""

from agno_agent import AgnoDharmicAgent
from datetime import datetime

def main():
    print("=" * 60)
    print("DHARMIC_CLAW - Agno Native Agent")
    print("=" * 60)
    print()

    print("Initializing agent...")
    agent = AgnoDharmicAgent()

    print(f"Agent: {agent.name}")
    print(f"Model: {agent.model_id}")
    print("Telos: moksha (liberation through witness consciousness)")
    print()
    print("Type 'quit' or 'exit' to end. Type 'witness' to record an observation.")
    print("-" * 60)
    print()

    session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nNamaste.")
                break

            if user_input.lower().startswith('witness '):
                obs = user_input[8:]
                agent.witness(obs)
                print(f"[Witness observation recorded: {obs[:50]}...]")
                print()
                continue

            response = agent.run(user_input, session_id=session_id)
            print(f"\n{agent.name}: {response}\n")

        except KeyboardInterrupt:
            print("\n\nNamaste.")
            break
        except Exception as e:
            print(f"\n[Error: {e}]\n")

if __name__ == "__main__":
    main()
