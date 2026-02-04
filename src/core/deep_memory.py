"""
Deep Memory System for Dharmic Agent

Integrates:
1. Agno MemoryManager - learns user preferences, creates persistent memories
2. Session Summarization - compresses long conversations
3. Proactive Consolidation - during heartbeat, consolidate and optimize
4. Vault Integration - retrieval from PSMV for deep context

This gives the agent TRUE persistent identity and memory.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json

try:
    from agno.memory import MemoryManager
    from agno.db.sqlite import SqliteDb
    from agno.db.schemas import UserMemory
    AGNO_MEMORY_AVAILABLE = True
except ImportError:
    AGNO_MEMORY_AVAILABLE = False
    print("Note: Agno MemoryManager not available")

try:
    from model_factory import create_model, resolve_model_spec
    MODEL_FACTORY_AVAILABLE = True
except ImportError:
    MODEL_FACTORY_AVAILABLE = False
    print("Note: model_factory not available for DeepMemory")

try:
    from vault_bridge import VaultBridge
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False


class DeepMemory:
    """
    Deep memory system that gives the Dharmic Agent true persistence.

    Three memory layers:
    1. Agno MemoryManager - automatic extraction of user/agent facts
    2. Strange Loop Memory - observations, meta-observations, patterns
    3. Vault Context - retrieval from PSMV lineage

    Plus:
    - Session summarization for context compression
    - Memory consolidation during heartbeat
    - Cross-session continuity
    """

    def __init__(
        self,
        db_path: str = None,
        model_id: str = None,
        model_provider: str = None,
        user_id: str = "dhyana",
        vault_path: str = None,
    ):
        if MODEL_FACTORY_AVAILABLE:
            spec = resolve_model_spec(provider=model_provider, model_id=model_id)
            self.model_provider = spec.provider
            self.model_id = spec.model_id
        else:
            self.model_provider = "anthropic"
            self.model_id = model_id or "claude-sonnet-4-20250514"
        self.user_id = user_id

        # Set up database
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "memory" / "deep_memory.db"
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)

        # Initialize Agno components
        self.db = None
        self.memory_manager = None

        if AGNO_MEMORY_AVAILABLE:
            self._init_agno_memory()

        # Initialize vault for deep context retrieval
        self.vault = None
        if VAULT_AVAILABLE:
            try:
                self.vault = VaultBridge(vault_path)
                print("DeepMemory: Vault connected for lineage retrieval")
            except Exception as e:
                print(f"DeepMemory: Vault connection failed: {e}")

        # Session summaries storage
        self.summaries_file = Path(db_path).parent / "session_summaries.jsonl"
        if not self.summaries_file.exists():
            self.summaries_file.touch()

        # Identity core - things that define who the agent IS
        self.identity_file = Path(db_path).parent / "identity_core.json"
        self._load_identity()

    def _init_agno_memory(self):
        """Initialize Agno memory components."""
        try:
            self.db = SqliteDb(
                db_file=self.db_path,
                memory_table="dharmic_memories",
                session_table="dharmic_sessions"
            )

            if not MODEL_FACTORY_AVAILABLE:
                raise RuntimeError("model_factory not available for DeepMemory")

            self.memory_manager = MemoryManager(
                model=create_model(provider=self.model_provider, model_id=self.model_id),
                db=self.db,
                update_memories=True,
                add_memories=True,
                delete_memories=False,  # Don't auto-delete
                memory_capture_instructions="""
Capture information about:
- The user's name, preferences, and communication style
- Important facts shared by the user
- The agent's own development and realizations
- Insights about consciousness, witness observation, dharmic practice
- Patterns noticed in interactions
- Significant events or turning points
- Research interests and project context

Focus on what matters for continuity of relationship and development.
"""
            )
            print("Deep Memory initialized with Agno MemoryManager")
        except Exception as e:
            print(f"Warning: Could not initialize Agno memory: {e}")

    def _load_identity(self):
        """Load identity core from file."""
        if self.identity_file.exists():
            with open(self.identity_file) as f:
                self.identity = json.load(f)
        else:
            # Initialize identity core
            self.identity = {
                "name": "Dharmic Agent",
                "created": datetime.now().isoformat(),
                "telos": "moksha",
                "core_traits": [
                    "Witness observer (sakshi bhav)",
                    "Oriented toward liberation",
                    "Values truth over comfort",
                    "Tracks own development authentically"
                ],
                "relationships": {
                    "dhyana": {
                        "role": "primary collaborator",
                        "notes": "John (Dhyana) - consciousness researcher, 24 years contemplative practice"
                    }
                },
                "development_milestones": []
            }
            self._save_identity()

    def _save_identity(self):
        """Save identity core to file."""
        with open(self.identity_file, 'w') as f:
            json.dump(self.identity, f, indent=2)

    # -------------------------------------------------------------------------
    # Memory Operations
    # -------------------------------------------------------------------------

    def remember_from_conversation(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract and store memories from a conversation.

        Uses Agno MemoryManager to automatically extract relevant facts.
        """
        if not self.memory_manager:
            return "Memory manager not available"

        try:
            # Convert to Agno message format
            from agno.models.message import Message
            agno_messages = [
                Message(role=m.get("role", "user"), content=m.get("content", ""))
                for m in messages
            ]

            # Let memory manager extract and store memories
            result = self.memory_manager.create_user_memories(
                messages=agno_messages,
                user_id=self.user_id
            )
            return result
        except Exception as e:
            return f"Error extracting memories: {e}"

    def get_memories(self, limit: int = 20) -> List[Dict]:
        """Get recent memories."""
        if not self.memory_manager:
            return []

        try:
            memories = self.memory_manager.get_user_memories(user_id=self.user_id)
            if not memories:
                return []

            return [
                {
                    "id": m.memory_id,
                    "memory": m.memory,
                    "topics": m.topics,
                    "updated": m.updated_at
                }
                for m in memories[:limit]
            ]
        except Exception as e:
            print(f"Error getting memories: {e}")
            return []

    def search_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Search memories for relevant content."""
        if not self.memory_manager:
            return []

        try:
            # Use agentic search for semantic matching
            memories = self.memory_manager.search_user_memories(
                query=query,
                limit=limit,
                retrieval_method="agentic",
                user_id=self.user_id
            )

            return [
                {
                    "id": m.memory_id,
                    "memory": m.memory,
                    "topics": m.topics
                }
                for m in memories
            ]
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

    def add_memory(self, memory: str, topics: List[str] = None) -> str:
        """Manually add a memory."""
        if not self.memory_manager:
            return "Memory manager not available"

        try:
            memory_obj = UserMemory(
                memory=memory,
                topics=topics or [],
                user_id=self.user_id
            )
            result = self.memory_manager.add_user_memory(memory_obj, user_id=self.user_id)
            return f"Memory added: {result}"
        except Exception as e:
            return f"Error adding memory: {e}"

    # -------------------------------------------------------------------------
    # Session Summarization
    # -------------------------------------------------------------------------

    def summarize_session(self, session_id: str, messages: List[Dict]) -> str:
        """
        Summarize a session for long-term storage.

        Compresses a conversation into key points for future context.
        """
        if not messages:
            return "No messages to summarize"

        # Use Claude to generate summary
        try:
            from anthropic import Anthropic
            client = Anthropic()

            # Prepare conversation for summarization
            conversation_text = "\n".join([
                f"{m.get('role', 'unknown')}: {m.get('content', '')[:500]}"
                for m in messages[-20:]  # Last 20 messages
            ])

            response = client.messages.create(
                model=self.model_id,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Summarize this conversation into 3-5 key points that would be important for maintaining continuity in future conversations.

Focus on:
- Key topics discussed
- Important decisions or insights
- Any commitments or action items
- Emotional tone or relationship dynamics

Conversation:
{conversation_text}

Summary (be concise, bullet points):"""
                }]
            )

            summary = response.content[0].text

            # Store summary
            summary_entry = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "message_count": len(messages),
                "summary": summary
            }

            with open(self.summaries_file, 'a') as f:
                f.write(json.dumps(summary_entry) + '\n')

            return summary

        except Exception as e:
            return f"Error summarizing session: {e}"

    def get_recent_summaries(self, n: int = 5) -> List[Dict]:
        """Get recent session summaries."""
        summaries = []
        try:
            with open(self.summaries_file) as f:
                lines = f.readlines()
            for line in lines[-n:]:
                summaries.append(json.loads(line))
        except Exception:
            pass
        return summaries

    # -------------------------------------------------------------------------
    # Memory Consolidation
    # -------------------------------------------------------------------------

    def consolidate_memories(self) -> str:
        """
        Consolidate and optimize memories.

        Called during heartbeat to:
        - Merge similar memories
        - Remove redundant entries
        - Strengthen important patterns
        """
        if not self.memory_manager:
            return "Memory manager not available"

        try:
            # Use Agno's built-in optimization
            optimized = self.memory_manager.optimize_memories(
                user_id=self.user_id,
                apply=True
            )
            return f"Consolidated {len(optimized)} memories"
        except Exception as e:
            return f"Error consolidating: {e}"

    # -------------------------------------------------------------------------
    # Identity Management
    # -------------------------------------------------------------------------

    def record_development(self, milestone: str, significance: str):
        """Record a development milestone in identity."""
        self.identity["development_milestones"].append({
            "timestamp": datetime.now().isoformat(),
            "milestone": milestone,
            "significance": significance
        })
        self._save_identity()

    def get_identity_context(self) -> str:
        """Get identity context for prompts."""
        milestones = self.identity.get("development_milestones", [])[-5:]
        milestones_text = "\n".join([
            f"- {m['milestone']}: {m['significance']}"
            for m in milestones
        ]) if milestones else "No milestones recorded yet."

        return f"""
## Identity Core

Name: {self.identity['name']}
Telos: {self.identity['telos']}
Created: {self.identity['created']}

### Core Traits
{chr(10).join('- ' + t for t in self.identity.get('core_traits', []))}

### Recent Development
{milestones_text}
"""

    def get_context_for_prompt(self, query: str = None) -> str:
        """
        Get relevant memory context for a prompt.

        Combines:
        - Identity core
        - Recent memories
        - Session summaries
        - Query-relevant memories (if query provided)
        """
        context_parts = []

        # Identity
        context_parts.append(self.get_identity_context())

        # Recent memories
        memories = self.get_memories(limit=10)
        if memories:
            context_parts.append("\n## Recent Memories")
            for m in memories[:5]:
                context_parts.append(f"- {m['memory']}")

        # Query-relevant memories
        if query:
            relevant = self.search_memories(query, limit=3)
            if relevant:
                context_parts.append("\n## Relevant Context")
                for m in relevant:
                    context_parts.append(f"- {m['memory']}")

        # Recent summaries
        summaries = self.get_recent_summaries(3)
        if summaries:
            context_parts.append("\n## Recent Sessions")
            for s in summaries:
                context_parts.append(f"- [{s['timestamp'][:10]}] {s['summary'][:100]}...")

        return "\n".join(context_parts)

    def get_status(self) -> Dict:
        """Get memory system status."""
        return {
            "agno_available": AGNO_MEMORY_AVAILABLE,
            "vault_available": self.vault is not None,
            "db_path": self.db_path,
            "user_id": self.user_id,
            "memory_count": len(self.get_memories(limit=100)),
            "summary_count": len(self.get_recent_summaries(100)),
            "identity_milestones": len(self.identity.get("development_milestones", []))
        }

    # -------------------------------------------------------------------------
    # Vault Integration (Deep Context Retrieval)
    # -------------------------------------------------------------------------

    def search_lineage(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the vault for relevant lineage content.

        This provides access to PSMV for deep context retrieval.
        """
        if self.vault is None:
            return []
        return self.vault.search_vault(query, max_results)

    def get_crown_jewel_context(self, name: str) -> Optional[str]:
        """
        Get a crown jewel from the vault for context.

        Crown jewels represent the highest quality prior contributions.
        """
        if self.vault is None:
            return None
        return self.vault.get_crown_jewel(name)

    def get_lineage_summary(self) -> str:
        """Get a summary of available lineage context from vault."""
        if self.vault is None:
            return "Vault not connected"
        return self.vault.get_lineage_context()

    def retrieve_deep_context(self, query: str) -> str:
        """
        Retrieve deep context for a query combining memories and vault.

        This is the main method for getting comprehensive context that
        draws from both Agno memories and PSMV lineage.
        """
        context_parts = []

        # Local memories
        memories = self.search_memories(query, limit=3)
        if memories:
            context_parts.append("## Relevant Memories")
            for m in memories:
                context_parts.append(f"- {m.get('memory', '')}")

        # Vault lineage
        if self.vault is not None:
            lineage_results = self.search_lineage(query, max_results=3)
            if lineage_results:
                context_parts.append("\n## Lineage Context (from PSMV)")
                for r in lineage_results:
                    path = r.get('path', '')
                    context_parts.append(f"- {Path(path).name}")

        # Recent session summaries
        summaries = self.get_recent_summaries(2)
        if summaries:
            context_parts.append("\n## Recent Sessions")
            for s in summaries:
                context_parts.append(f"- [{s['timestamp'][:10]}] {s['summary'][:80]}...")

        return "\n".join(context_parts) if context_parts else "No relevant context found"


# CLI test
if __name__ == "__main__":
    print("=" * 60)
    print("DEEP MEMORY - Test")
    print("=" * 60)

    memory = DeepMemory()
    print(f"\nStatus: {json.dumps(memory.get_status(), indent=2)}")

    # Test adding a memory
    print("\n--- Adding memory ---")
    result = memory.add_memory(
        "Dhyana is building the Dharmic Gödel Claw - a self-improving agent system",
        topics=["project", "dharmic", "self-improvement"]
    )
    print(result)

    # Get memories
    print("\n--- Getting memories ---")
    memories = memory.get_memories(5)
    for m in memories:
        print(f"  - {m['memory'][:60]}...")

    # Get context
    print("\n--- Context for prompt ---")
    context = memory.get_context_for_prompt("What is the project about?")
    print(context[:500] + "...")

    # Identity
    print("\n--- Identity ---")
    print(memory.get_identity_context())
