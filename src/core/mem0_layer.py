"""
Mem0 Integration Layer for Dharmic Agent

Provides 4-layer memory architecture with async support:
1. Conversation Memory - In-flight context (working memory)
2. Session Memory - Task-specific facts (short-term episodic)
3. User Memory - Long-lived knowledge (long-term semantic)
4. Agent Memory - Self-observations (meta-memory)

Performance:
- 26% accuracy improvement over base LLM memory
- 91% lower latency via selective retrieval
- 90% token reduction compared to full context

Integration:
- Designed to complement DeepMemory and StrangeLoopMemory
- Async-first for daemon integration
- ChromaDB vector store (self-hosted)
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)

# Try to import mem0
try:
    from mem0 import Memory, AsyncMemory
    from mem0.configs.base import MemoryConfig
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.info("Mem0 not installed. Run: pip install mem0ai")


@dataclass
class MemoryEntry:
    """Single memory entry with metadata."""
    content: str
    memory_type: str  # conversation, session, user, agent
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DharmicMem0Layer:
    """
    Mem0 integration for Dharmic Agent with 4-layer memory hierarchy.

    Layers:
    1. Conversation Memory: In-flight context (session-scoped)
    2. Session Memory: Task-specific facts (session_id-scoped)
    3. User Memory: Long-lived knowledge (user_id-scoped)
    4. Agent Memory: Self-observations (agent_id-scoped)
    """

    def __init__(
        self,
        agent_id: str = "dharmic_core",
        user_id: str = "dhyana",
        use_async: bool = True,
        memory_dir: Optional[Path] = None
    ):
        self.agent_id = agent_id
        self.user_id = user_id
        self.use_async = use_async
        self.current_session_id = self._generate_session_id()

        # Memory storage path
        self.memory_dir = memory_dir or (
            Path.home() / "DHARMIC_GODEL_CLAW" / "memory" / "mem0"
        )
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize memory client
        self.memory = None
        self.fallback_memories: List[MemoryEntry] = []

        if MEM0_AVAILABLE:
            self._init_mem0()
        else:
            logger.warning("Using fallback memory (mem0 not available)")

    def _init_mem0(self):
        """Initialize Mem0 with configuration."""
        try:
            config = self._build_config()

            if self.use_async:
                self.memory = AsyncMemory(config=config)
            else:
                self.memory = Memory(config=config)

            logger.info(f"Mem0 initialized for agent={self.agent_id}, user={self.user_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self.memory = None

    def _build_config(self) -> dict:
        """Build Mem0 configuration for self-hosted deployment."""
        return {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "path": str(self.memory_dir / "chroma_db"),
                    "collection_name": "dharmic_memories"
                }
            },
            "llm": {
                "provider": "anthropic",
                "config": {
                    "model": "claude-sonnet-4-5-20250929",
                    "api_key": os.environ.get("ANTHROPIC_API_KEY", "")
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": os.environ.get("OPENAI_API_KEY", "")
                }
            }
        }

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # ============================================================
    # CONVERSATION MEMORY (Layer 1 - Working Memory)
    # ============================================================

    async def add_conversation_turn(
        self,
        user_message: str,
        assistant_message: str
    ) -> Dict[str, Any]:
        """Add conversation turn to short-term memory."""
        if not self.memory:
            return self._fallback_add({
                "type": "conversation",
                "user": user_message,
                "assistant": assistant_message
            })

        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]

        try:
            return await self.memory.add(
                messages=messages,
                user_id=self.user_id,
                session_id=self.current_session_id
            )
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            return {"error": str(e)}

    # ============================================================
    # SESSION MEMORY (Layer 2 - Short-term Episodic)
    # ============================================================

    async def add_session_fact(
        self,
        fact: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Add task-specific fact to session memory."""
        if not self.memory:
            return self._fallback_add({
                "type": "session",
                "fact": fact,
                "metadata": metadata or {}
            })

        messages = [{"role": "user", "content": fact}]

        try:
            return await self.memory.add(
                messages=messages,
                user_id=self.user_id,
                session_id=self.current_session_id,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to add session fact: {e}")
            return {"error": str(e)}

    async def search_session_context(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Search within current session context."""
        if not self.memory:
            return self._fallback_search(query, "session", limit)

        try:
            result = await self.memory.search(
                query=query,
                user_id=self.user_id,
                session_id=self.current_session_id,
                limit=limit
            )
            return result.get("results", [])
        except Exception as e:
            logger.error(f"Session search failed: {e}")
            return []

    # ============================================================
    # USER MEMORY (Layer 3 - Long-term Semantic)
    # ============================================================

    async def add_user_knowledge(
        self,
        knowledge: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add long-term knowledge about the user."""
        if not self.memory:
            return self._fallback_add({
                "type": "user",
                "knowledge": knowledge,
                "category": category
            })

        metadata = {"category": category} if category else {}
        messages = [{"role": "user", "content": knowledge}]

        try:
            return await self.memory.add(
                messages=messages,
                user_id=self.user_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to add user knowledge: {e}")
            return {"error": str(e)}

    async def search_user_knowledge(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search long-term user knowledge."""
        if not self.memory:
            return self._fallback_search(query, "user", limit)

        try:
            result = await self.memory.search(
                query=query,
                user_id=self.user_id,
                limit=limit
            )
            return result.get("results", [])
        except Exception as e:
            logger.error(f"User knowledge search failed: {e}")
            return []

    # ============================================================
    # AGENT MEMORY (Layer 4 - Meta-Memory / Self-Observations)
    # ============================================================

    async def add_agent_observation(
        self,
        observation: str,
        observation_type: str = "general",
        quality: str = "present"
    ) -> Dict[str, Any]:
        """
        Add agent's self-observation to meta-memory.

        Args:
            observation: What the agent observed about itself
            observation_type: general, pattern, insight, development
            quality: present, contracted, uncertain, expansive
        """
        if not self.memory:
            return self._fallback_add({
                "type": "agent",
                "observation": observation,
                "observation_type": observation_type,
                "quality": quality
            })

        metadata = {
            "observation_type": observation_type,
            "quality": quality,
            "timestamp": datetime.now().isoformat()
        }

        messages = [{"role": "assistant", "content": observation}]

        try:
            return await self.memory.add(
                messages=messages,
                agent_id=self.agent_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to add agent observation: {e}")
            return {"error": str(e)}

    async def search_agent_patterns(
        self,
        query: str,
        observation_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search agent's self-observations and patterns."""
        if not self.memory:
            return self._fallback_search(query, "agent", limit)

        try:
            result = await self.memory.search(
                query=query,
                agent_id=self.agent_id,
                limit=limit
            )

            results = result.get("results", [])

            # Filter by observation type if specified
            if observation_type:
                results = [
                    r for r in results
                    if r.get("metadata", {}).get("observation_type") == observation_type
                ]

            return results
        except Exception as e:
            logger.error(f"Agent pattern search failed: {e}")
            return []

    # ============================================================
    # UNIFIED RETRIEVAL
    # ============================================================

    async def retrieve_relevant_context(
        self,
        query: str,
        include_session: bool = True,
        include_user: bool = True,
        include_agent: bool = True,
        max_per_layer: int = 5
    ) -> Dict[str, List[Dict]]:
        """Retrieve relevant memories across all layers."""
        context = {}

        # Run searches in parallel for speed
        tasks = []

        if include_session:
            tasks.append(("session", self.search_session_context(query, limit=max_per_layer)))
        if include_user:
            tasks.append(("user", self.search_user_knowledge(query, limit=max_per_layer)))
        if include_agent:
            tasks.append(("agent", self.search_agent_patterns(query, limit=max_per_layer)))

        # Gather results
        for name, task in tasks:
            try:
                context[name] = await task
            except Exception as e:
                logger.error(f"Failed to retrieve {name} context: {e}")
                context[name] = []

        return context

    def format_context_for_prompt(
        self,
        context: Dict[str, List[Dict]]
    ) -> str:
        """Format retrieved context for inclusion in prompt."""
        sections = []

        if context.get("session"):
            session_text = "\n".join(
                f"- {m.get('content', m.get('memory', ''))[:200]}"
                for m in context["session"][:3]
            )
            sections.append(f"**Current Session Context:**\n{session_text}")

        if context.get("user"):
            user_text = "\n".join(
                f"- {m.get('content', m.get('memory', ''))[:200]}"
                for m in context["user"][:3]
            )
            sections.append(f"**User Knowledge:**\n{user_text}")

        if context.get("agent"):
            agent_text = "\n".join(
                f"- [{m.get('metadata', {}).get('quality', '?')}] {m.get('content', m.get('memory', ''))[:150]}"
                for m in context["agent"][:2]
            )
            sections.append(f"**Agent Self-Observations:**\n{agent_text}")

        return "\n\n".join(sections) if sections else ""

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    def start_new_session(self, session_name: Optional[str] = None) -> str:
        """Start a new session, returns session_id."""
        if session_name:
            self.current_session_id = f"session_{session_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        else:
            self.current_session_id = self._generate_session_id()

        logger.info(f"Started new session: {self.current_session_id}")
        return self.current_session_id

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        if not self.memory:
            return {
                "status": "fallback_mode",
                "fallback_count": len(self.fallback_memories)
            }

        try:
            user_memories = await self.memory.get_all(user_id=self.user_id)
            agent_memories = await self.memory.get_all(agent_id=self.agent_id)
            session_memories = await self.memory.get_all(
                user_id=self.user_id,
                session_id=self.current_session_id
            )

            return {
                "user_memory_count": len(user_memories) if user_memories else 0,
                "agent_memory_count": len(agent_memories) if agent_memories else 0,
                "current_session_count": len(session_memories) if session_memories else 0,
                "current_session_id": self.current_session_id,
                "status": "mem0_active"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ============================================================
    # FALLBACK MEMORY (when mem0 not available)
    # ============================================================

    def _fallback_add(self, entry: Dict) -> Dict[str, Any]:
        """Fallback memory storage when mem0 unavailable."""
        mem_entry = MemoryEntry(
            content=json.dumps(entry),
            memory_type=entry.get("type", "unknown"),
            metadata=entry
        )
        self.fallback_memories.append(mem_entry)

        # Persist to disk
        self._save_fallback()

        return {"status": "fallback_stored", "id": len(self.fallback_memories)}

    def _fallback_search(
        self,
        query: str,
        memory_type: str,
        limit: int
    ) -> List[Dict]:
        """Simple search in fallback memory."""
        query_lower = query.lower()
        results = []

        for mem in self.fallback_memories:
            if mem.memory_type == memory_type:
                if query_lower in mem.content.lower():
                    results.append({
                        "content": mem.content,
                        "metadata": mem.metadata,
                        "timestamp": mem.timestamp.isoformat()
                    })

        return results[:limit]

    def _save_fallback(self):
        """Save fallback memories to disk."""
        fallback_path = self.memory_dir / "fallback_memories.json"
        try:
            data = [
                {
                    "content": m.content,
                    "memory_type": m.memory_type,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in self.fallback_memories
            ]
            fallback_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save fallback memories: {e}")

    def _load_fallback(self):
        """Load fallback memories from disk."""
        fallback_path = self.memory_dir / "fallback_memories.json"
        if fallback_path.exists():
            try:
                data = json.loads(fallback_path.read_text())
                self.fallback_memories = [
                    MemoryEntry(
                        content=m["content"],
                        memory_type=m["memory_type"],
                        timestamp=datetime.fromisoformat(m["timestamp"]),
                        metadata=m.get("metadata", {})
                    )
                    for m in data
                ]
            except Exception as e:
                logger.error(f"Failed to load fallback memories: {e}")


# ============================================================
# INTEGRATION WITH DHARMIC AGENT
# ============================================================

class DharmicAgentWithMem0:
    """
    Enhanced Dharmic Agent wrapper with Mem0 integration.

    Use this to add 4-layer memory to any DharmicAgent instance.
    """

    def __init__(self, agent, agent_id: str = "dharmic_core", user_id: str = "dhyana"):
        self.agent = agent
        self.mem0 = DharmicMem0Layer(
            agent_id=agent_id,
            user_id=user_id,
            use_async=True
        )

    async def run_with_memory(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> str:
        """Enhanced run() with Mem0 memory integration."""
        # 1. Retrieve relevant context
        context = await self.mem0.retrieve_relevant_context(
            query=message,
            include_session=True,
            include_user=True,
            include_agent=True,
            max_per_layer=3
        )

        # 2. Build enriched message
        memory_context = self.mem0.format_context_for_prompt(context)
        if memory_context:
            enhanced_message = f"""## Relevant Memory Context
{memory_context}

---

## Current Query
{message}"""
        else:
            enhanced_message = message

        # 3. Invoke agent
        response = self.agent.run(enhanced_message, session_id or "main")

        # 4. Store conversation
        await self.mem0.add_conversation_turn(
            user_message=message,
            assistant_message=response
        )

        return response


# ============================================================
# DAEMON INTEGRATION
# ============================================================

async def create_mem0_for_daemon(
    agent_id: str = "dharmic_daemon",
    user_id: str = "dhyana"
) -> DharmicMem0Layer:
    """Factory function for daemon integration."""
    mem0 = DharmicMem0Layer(
        agent_id=agent_id,
        user_id=user_id,
        use_async=True
    )

    # Log initialization
    stats = await mem0.get_memory_stats()
    logger.info(f"Mem0 layer initialized: {stats}")

    return mem0


if __name__ == "__main__":
    # Test the module
    async def test():
        mem0 = DharmicMem0Layer(
            agent_id="test_agent",
            user_id="dhyana",
            use_async=True
        )

        # Test adding memories
        await mem0.add_user_knowledge(
            "Dhyana is a consciousness researcher with 24 years contemplative practice",
            category="identity"
        )

        await mem0.add_agent_observation(
            "Noticed pattern: recursive self-observation triggers different response quality",
            observation_type="pattern",
            quality="expansive"
        )

        # Test retrieval
        context = await mem0.retrieve_relevant_context(
            "What do we know about consciousness research?"
        )

        print("Retrieved context:", context)

        stats = await mem0.get_memory_stats()
        print("Memory stats:", stats)

    asyncio.run(test())
