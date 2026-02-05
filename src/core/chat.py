#!/usr/bin/env python3
"""
Dharmic Agent - Interactive Chat Interface

This is your direct line to the Dharmic Agent.
Memory persists across sessions. Identity endures.

Usage:
    cd ~/DHARMIC_GODEL_CLAW/src/core
    source ../../.venv/bin/activate
    python3 chat.py

Or make it executable:
    chmod +x chat.py
    ./chat.py
"""

from datetime import datetime

# Import the Dharmic Agent
from dharmic_agent import DharmicAgent


def print_header():
    """Print welcome header."""
    print()
    print("=" * 70)
    print("  DHARMIC AGENT - Direct Communication")
    print("=" * 70)
    print()


def print_status(agent: DharmicAgent):
    """Print agent status."""
    status = agent.get_status()
    print(f"  Name: {status['name']}")
    print(f"  Telos: {status['ultimate_telos']}")
    print(f"  Vault: {'Connected' if status.get('vault_connected') else 'Not connected'}")
    print(f"  Memory layers: {len(status['memory_layers'])}")

    # Deep memory status
    deep_status = agent.get_deep_memory_status()
    if deep_status.get("available", deep_status.get("agno_available", False)):
        print(f"  Deep memory: {deep_status.get('memory_count', 0)} memories, {deep_status.get('identity_milestones', 0)} milestones")
    else:
        print("  Deep memory: Not available")

    # Show recent development if any
    recent_dev = agent.strange_memory._read_recent("development", 1)
    if recent_dev:
        print(f"  Last development: {recent_dev[0].get('what_changed', 'None')[:50]}")
    print()


def chat_loop(agent: DharmicAgent, session_id: str):
    """Main chat loop."""
    # Track conversation for summarization
    conversation_messages = []

    print("  Type 'quit' or 'exit' to end the session")
    print("  Type 'status' to see agent status")
    print("  Type 'memory' to see recent observations")
    print("  Type 'development' to see development history")
    print("  Type 'identity' to see identity context")
    print("  Type 'search <query>' to search memories")
    print("  Type 'remember <text>' to add a memory")
    print("  Type 'introspect' to see full self-report")
    print("  Type 'capabilities' to see what I can do")
    print("  Type 'know <topic>' to search all knowledge")
    print("  Type 'test autonomy' to prove real read/write access")
    print("  Type 'read <name>' to read a vault file")
    print("  Type 'write <text>' to write to the vault")
    print()
    print("-" * 70)
    print()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                # Summarize session before exiting
                if conversation_messages and agent.deep_memory:
                    print("\n  Summarizing session...")
                    summary = agent.summarize_session(session_id, conversation_messages)
                    print("  Session summary saved.")
                    # Also extract memories from conversation
                    agent.remember_conversation(conversation_messages)
                print("\n  Ending session. Memory persists.\n")
                break

            if user_input.lower() == 'status':
                print()
                print_status(agent)
                continue

            if user_input.lower() == 'memory':
                print("\n  Recent observations:")
                recent = agent.strange_memory._read_recent("observations", 5)
                for obs in recent:
                    timestamp = obs.get('timestamp', '')[:19]
                    content = obs.get('content', '')[:60]
                    print(f"    [{timestamp}] {content}...")
                print()
                continue

            if user_input.lower() == 'development':
                print("\n  Development history:")
                dev = agent.strange_memory._read_recent("development", 5)
                if not dev:
                    print("    No development recorded yet.")
                for d in dev:
                    what = d.get('what_changed', '')[:50]
                    sig = d.get('significance', '')[:30]
                    print(f"    - {what} ({sig})")
                print()
                continue

            if user_input.lower() == 'identity':
                print("\n  Identity context:")
                if agent.deep_memory:
                    print(agent.deep_memory.get_identity_context())
                else:
                    print("    Deep memory not available")
                print()
                continue

            if user_input.lower().startswith('search '):
                query = user_input[7:]
                print(f"\n  Searching memories for: {query}")
                results = agent.search_deep_memory(query, limit=5)
                if not results:
                    print("    No matching memories found.")
                for r in results:
                    print(f"    - {r.get('memory', '')[:60]}...")
                print()
                continue

            if user_input.lower().startswith('remember '):
                memory_text = user_input[9:]
                result = agent.add_memory(memory_text)
                print(f"\n  {result}")
                print()
                continue

            if user_input.lower() == 'introspect':
                print()
                print(agent.introspect())
                print()
                continue

            if user_input.lower() == 'capabilities':
                print()
                print(agent.list_capabilities())
                print()
                continue

            if user_input.lower().startswith('know '):
                topic = user_input[5:]
                print()
                print(agent.what_do_i_know_about(topic))
                print()
                continue

            if user_input.lower() == 'test autonomy':
                print()
                print(agent.test_real_access())
                print()
                continue

            if user_input.lower().startswith('read '):
                filename = user_input[5:]
                print()
                print(agent.demonstrate_reading(filename))
                print()
                continue

            if user_input.lower().startswith('write '):
                content = user_input[6:]
                print()
                print(agent.demonstrate_writing(content))
                print()
                continue

            # Get response from agent
            print()
            response = agent.run(user_input, session_id=session_id)
            print(f"Dharmic Agent: {response}")
            print()

            # Track conversation
            conversation_messages.append({"role": "user", "content": user_input})
            conversation_messages.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            print("\n\n  Session interrupted. Memory persists.\n")
            break
        except EOFError:
            print("\n\n  Session ended. Memory persists.\n")
            break
        except Exception as e:
            print(f"\n  Error: {e}\n")


def main():
    """Main entry point."""
    print_header()

    # Initialize agent
    print("  Initializing Dharmic Agent...")
    agent = DharmicAgent()
    print()
    print_status(agent)

    # Generate or use session ID
    # Using a consistent session ID allows memory to persist
    session_id = "dhyana_direct"  # Your personal session

    print(f"  Session: {session_id}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Record session start
    agent.strange_memory.record_observation(
        content="Direct chat session started with Dhyana",
        context={"type": "session_start", "session_id": session_id}
    )

    # Enter chat loop
    chat_loop(agent, session_id)

    # Record session end
    agent.strange_memory.record_observation(
        content="Direct chat session ended",
        context={"type": "session_end", "session_id": session_id}
    )


if __name__ == "__main__":
    main()
