# Agno Memory and Learning Systems - Deep Analysis

**Date**: February 2, 2026
**Project**: Dharmic Gödel Claw Integration Analysis
**Scope**: Agno memory/learning systems for vault synchronization

---

## Executive Summary

Agno implements a sophisticated two-layer learning architecture:

1. **Legacy MemoryManager** (shallow, simple CRUD operations)
2. **Modern LearningMachine** (deep, multi-store orchestration)

The new LearningMachine is the production system, with six learning stores handling different data types. This analysis covers both systems and provides integration patterns for the Persistent-Semantic-Memory-Vault.

---

## Architecture Overview

### Two-Layer Learning Model

```
                    AGENT
                      |
           ┌──────────┴──────────┐
           |                     |
      LearningMachine      MemoryManager (legacy)
      (Modern, Unified)    (Simple CRUD)
           |
     ┌─────┼─────┬─────────┬──────────┬─────────┐
     |     |     |         |          |         |
 User   Session Entity   Learned   User     Decision
Profile Context Memory Knowledge Profile   Log
(future)
     |     |     |         |          |         |
     └─────┴─────┴─────────┴──────────┴─────────┘
           |
        Database
    (PostgreSQL/SQLite/
     MongoDB/etc)
```

---

## Part 1: Legacy MemoryManager (Simple)

### Location
`/Users/dhyana/DHARMIC_GODEL_CLAW/cloned_source/agno/libs/agno/agno/memory/manager.py` (1,543 lines)

### Purpose
Simple user memory CRUD with LLM-based extraction. Persists unstructured memories about users.

### Core Data Structure

```python
@dataclass
class UserMemory:
    memory: str                        # The actual memory text
    memory_id: Optional[str]          # UUID for the memory
    user_id: Optional[str]            # User this memory belongs to
    topics: Optional[List[str]]       # Tags: ["name", "hobbies", "location"]
    created_at: Optional[int]         # Unix timestamp
    updated_at: Optional[int]         # Unix timestamp
    input: Optional[str]              # Original input that generated this memory
    agent_id: Optional[str]           # Which agent created it
    team_id: Optional[str]            # Which team created it
    feedback: Optional[str]           # Optional feedback/corrections
```

### Three Key Operations

#### 1. **Recall** - Get memories by user_id
```python
def get_user_memories(user_id: str) -> List[UserMemory]:
    """Retrieve all memories for a user from database."""
    memories = self.db.get_user_memories(user_id=user_id)
    return memories

def search_user_memories(query: str, user_id: str) -> List[UserMemory]:
    """Search using agentic search (LLM-based semantic matching)."""
```

**Three retrieval methods:**
- `last_n`: Most recent N memories
- `first_n`: Oldest N memories  
- `agentic`: LLM-based semantic search

#### 2. **Capture** - Extract memories from messages
```python
def create_user_memories(
    messages: List[Message],
    user_id: str
) -> str:
    """Extract memories from conversation messages using LLM."""
    # 1. Load existing memories
    existing = self.read_from_db(user_id)
    
    # 2. Call LLM with extraction prompt
    response = self.model.response(
        messages=[system_message, *messages],
        tools=[add_memory, update_memory, delete_memory]
    )
    
    # 3. Execute tool calls (model decides what to save)
    # 4. Return confirmation
```

**Extraction prompt guiding principles:**
- Personal facts, opinions, preferences
- Significant life events
- Current challenges and goals
- Context for understanding the user

**LLM-controlled operations:**
```python
def add_memory(memory: str, topics: Optional[List[str]]) -> str
def update_memory(memory_id: str, memory: str, topics: Optional[List[str]]) -> str
def delete_memory(memory_id: str) -> str
def clear_memory() -> str
```

#### 3. **Maintain** - Optimize memory storage
```python
def optimize_memories(
    user_id: str,
    strategy: MemoryOptimizationStrategy = SUMMARIZE,
    apply: bool = True
) -> List[UserMemory]:
    """Compress memories using strategy (default: summarize all)."""
```

**Available strategies:**
- `SUMMARIZE`: Combine all memories into single narrative
- Custom strategies implementing `MemoryOptimizationStrategy`

### System Message Template (Simplified)

```
You are a Memory Manager responsible for managing user information.

## When to capture
- Personal facts: name, age, occupation, location, interests
- Opinions and preferences: likes, dislikes, frustrations
- Significant life events and experiences
- Current situation, challenges, goals
- Any details offering meaningful insight

## How to capture
- Decide if a memory needs to be added, updated, or deleted
- Only update if genuinely new information
- Don't repeat information across memories
- Don't make memories too long

## Available tools
- add_memory: New information
- update_memory: Existing memory needs change
- delete_memory: Remove outdated info
- clear_memory: Reset all (rarely)

[Existing memories listed here]
```

### Integration Points

**Agent Integration:**
```python
# In agent run
memory_manager.create_user_memories(
    messages=conversation_history,
    user_id=user_id,
    agent_id=agent.id,
    team_id=team.id
)
```

**Database Interface:**
```python
# MemoryManager delegates to database
db.upsert_user_memory(memory: UserMemory)
db.get_user_memories(user_id: str) -> List[UserMemory]
db.delete_user_memory(memory_id: str, user_id: str)
db.clear_memories()
```

---

## Part 2: Modern LearningMachine (Unified)

### Location
`/Users/dhyana/DHARMIC_GODEL_CLAW/cloned_source/agno/libs/agno/agno/learn/`

### Purpose
Unified learning framework coordinating six different learning stores for comprehensive agent knowledge capture.

### Architecture

```python
@dataclass
class LearningMachine:
    db: Optional[Union[BaseDb, AsyncBaseDb]]
    model: Optional[Model]
    knowledge: Optional[Knowledge]
    
    # Six learning types (all optional)
    user_profile: UserProfileInput        # Structured user data
    user_memory: UserMemoryInput          # Unstructured observations
    session_context: SessionContextInput  # What happened so far
    entity_memory: EntityMemoryInput      # Knowledge about external things
    learned_knowledge: LearnedKnowledgeInput  # Reusable insights
    decision_log: DecisionLogInput        # Decision history (Phase 2)
```

### Six Learning Stores

#### 1. **UserProfileStore** (Structured)
**Purpose**: Long-term structured profile fields

```python
@dataclass
class UserProfile:
    user_id: str
    name: Optional[str]
    preferred_name: Optional[str]
    [custom fields...]
```

**Modes:**
- `ALWAYS`: Extract automatically after each response
- `AGENTIC`: Agent decides via `update_profile` tool

**Tool:**
```python
def update_profile(field: str, value: str) -> str:
    """Update a specific profile field."""
```

#### 2. **UserMemoryStore** (Unstructured) 
**Purpose**: Unstructured observations about users

Same as MemoryManager above but integrated with LearningMachine.

```python
@dataclass
class Memories:
    user_id: str
    memories: List[Dict] = [
        {
            "id": "abc123",
            "content": "Works at Stripe as engineering lead",
            "added_by_agent": "agent_id",
            "added_by_team": "team_id"
        },
        ...
    ]
```

**Configuration:**
```python
UserMemoryConfig(
    mode=LearningMode.ALWAYS,  # or AGENTIC
    enable_add_memory=True,
    enable_update_memory=True,
    enable_delete_memory=True,
    enable_clear_memories=False,
    enable_agent_tools=True,  # Expose tools to agent
    agent_can_update_memories=True
)
```

#### 3. **SessionContextStore** (Conversation State)
**Purpose**: Persistent context across conversation turns

```python
@dataclass
class SessionContext:
    session_id: str
    summaries: List[str]  # Conversation summaries
    key_decisions: List[str]  # Important decisions
    open_items: List[str]  # Things to follow up on
```

#### 4. **EntityMemoryStore** (External Knowledge)
**Purpose**: Knowledge about external entities (companies, people, concepts)

```python
@dataclass
class EntityMemory:
    namespace: str  # "companies", "people", "concepts"
    entity_name: str
    facts: List[str]  # Atomic facts about entity
    relationships: List[str]  # Connections to other entities
```

#### 5. **LearnedKnowledgeStore** (Reusable Insights)
**Purpose**: General insights that apply across conversations

```python
@dataclass
class LearnedKnowledge:
    namespace: str  # "design_patterns", "api_gotchas", etc
    topic: str  # "authentication", "rate_limiting", etc
    insights: List[str]  # Actionable insights
```

#### 6. **DecisionLogStore** (Phase 2)
**Purpose**: Decision history and reasoning

```python
@dataclass
class DecisionLog:
    session_id: str
    decisions: List[{
        "decision": str,
        "options_considered": List[str],
        "chosen": str,
        "reasoning": str,
        "outcome": Optional[str]
    }]
```

### LearningMode Enum

```python
class LearningMode(Enum):
    ALWAYS = "always"      # Extract automatically after each response
    AGENTIC = "agentic"    # Agent decides when to learn via tools
    PROPOSE = "propose"    # Agent proposes, human confirms (HITL)
    HITL = "hitl"          # Human-in-the-loop (reserved)
```

### Unified LearningMachine Interface

```python
# Initialization
learning = LearningMachine(
    db=db,
    model=model,
    knowledge=knowledge,
    user_profile=True,           # Enable with defaults
    user_memory=UserMemoryConfig(mode=AGENTIC),
    session_context=True,
    entity_memory=EntityMemoryConfig(namespace="companies"),
)

# Recall phase (before agent response)
context_data = learning.recall(
    user_id="user123",
    session_id="session456",
    namespace="companies"
)
# Returns: {
#   "user_profile": UserProfile(...),
#   "user_memory": Memories(...),
#   "session_context": SessionContext(...),
#   "entity_memory": EntityMemory(...),
# }

# Building context for agent
context_str = learning.build_context(context_data)
# Formats data into readable context for system prompt

# Processing phase (after agent response)
learning.process(
    messages=conversation_messages,
    user_id="user123",
    session_id="session456"
)
# Triggers extraction based on configured modes

# Tool generation
tools = learning.get_tools(
    user_id="user123",
    session_id="session456"
)
# Returns available tools based on config
```

### Key Difference: ALWAYS vs AGENTIC

**ALWAYS Mode** (Automatic Extraction):
```python
# After each agent response:
learning.process(messages)  # LLM automatically extracts memories
```

Pros: No agent overhead, guaranteed capture
Cons: Extra LLM call, might capture irrelevant info

**AGENTIC Mode** (Agent-Controlled):
```python
# Agent has tools available:
tools = learning.get_tools()
# Includes: update_user_memory, add_memory, etc.
```

Pros: Agent decides what's worth saving
Cons: Agent overhead, might miss things

---

## Part 3: Database Storage Layer

### Location
`/Users/dhyana/DHARMIC_GODEL_CLAW/cloned_source/agno/libs/agno/agno/db/`

### Abstract Base

```python
class BaseDb(ABC):
    # Memory operations
    def upsert_user_memory(memory: UserMemory) -> None
    def get_user_memories(user_id: str) -> List[UserMemory]
    def delete_user_memory(memory_id: str, user_id: str) -> None
    def clear_memories() -> None
    
    # Learning operations (new)
    def upsert_learning(
        id: str,
        learning_type: str,  # "user_memory", "user_profile", etc
        user_id: Optional[str],
        agent_id: Optional[str],
        team_id: Optional[str],
        content: Dict[str, Any]
    ) -> None
    
    def get_learning(
        learning_type: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]
    
    def delete_learning(id: str) -> bool
```

### Supported Backends

| Database | Type | Best For | Status |
|----------|------|----------|--------|
| PostgreSQL | SQL | Production, pgvector | Full support |
| SQLite | SQL | Development | Full support |
| MongoDB | NoSQL | Flexible schema | Full support |
| MySQL | SQL | Legacy systems | Supported |
| Firebase Firestore | Cloud | Serverless | Supported |
| DynamoDB | Cloud | AWS | Supported |
| Redis | Cache | Session data | Supported |
| SurrealDB | Multi-model | Modern apps | Supported |
| JSON files | Files | Local testing | Supported |
| GCS JSON | Cloud | Google Cloud | Supported |

### Database Table Schema

```sql
-- Memories table
CREATE TABLE agno_memories (
    memory_id TEXT PRIMARY KEY,
    user_id TEXT,
    memory TEXT,
    topics JSONB,
    created_at INTEGER,
    updated_at INTEGER,
    input TEXT,
    agent_id TEXT,
    team_id TEXT,
    feedback TEXT
);

-- Learning table (new, unified)
CREATE TABLE agno_learnings (
    id TEXT PRIMARY KEY,
    learning_type TEXT,  -- "user_memory", "user_profile", etc
    user_id TEXT,
    entity_id TEXT,
    agent_id TEXT,
    team_id TEXT,
    content JSONB,  -- Flexible schema per type
    created_at INTEGER,
    updated_at INTEGER,
    INDEX (learning_type, user_id)
);
```

---

## Part 4: Retrieval Mechanisms

### Memory Search Strategy

```python
# Three built-in retrieval methods:

# 1. Last N (most recent)
memories = search_user_memories(
    retrieval_method="last_n",
    limit=5,
    user_id="user123"
)
# Returns: 5 most recent memories

# 2. First N (oldest)
memories = search_user_memories(
    retrieval_method="first_n",
    limit=5,
    user_id="user123"
)
# Returns: 5 oldest memories

# 3. Agentic Search (semantic)
memories = search_user_memories(
    query="What does this user work on?",
    retrieval_method="agentic",
    limit=5,
    user_id="user123"
)
# LLM searches memories for semantic relevance
```

### Agentic Search Implementation

```python
def _search_user_memories_agentic(
    query: str,
    user_id: str
) -> List[UserMemory]:
    """LLM-powered semantic search across memories."""
    
    # 1. List all memories in system prompt
    system_message = f"""
    Return the IDs of memories related to: {query}
    
    Available memories:
    ID: mem1
    Memory: "Works at Stripe as engineering lead"
    Topics: ["work", "company"]
    
    ID: mem2
    Memory: "Prefers concise responses"
    Topics: ["communication"]
    """
    
    # 2. LLM returns memory IDs
    response = model.response(
        messages=[system_message, Message(role="user", content=query)],
        response_format=MemorySearchResponse
    )
    
    # 3. Return matching memories
    return [m for m in all_memories if m.id in response.memory_ids]
```

### Context Building

```python
def build_context(memories_data) -> str:
    """Format memories for injection into system prompt."""
    
    context = "<user_memory>\n"
    
    for memory in memories_data.memories:
        context += f"- {memory['content']}\n"
    
    context += """
    <memory_application_guidelines>
    Apply this knowledge naturally - don't narrate it.
    - Selectively apply based on relevance
    - Never say "I remember that"
    - Current conversation takes precedence
    - Use memories to calibrate tone and depth
    </memory_application_guidelines>
    """
    
    if enable_tools:
        context += """
        <memory_updates>
        Use `update_user_memory` to save observations worth remembering.
        </memory_updates>
        """
    
    context += "\n</user_memory>"
    return context
```

---

## Part 5: Knowledge Accumulation Mechanisms

### Three Accumulation Strategies

#### 1. **ALWAYS Mode** (Automatic)
```python
# After every agent response
agent.run(
    message=user_message,
    user_id="user123"
)

# Automatically:
learning.process(
    messages=conversation_history,
    user_id="user123"
)
# Extracts memories via LLM

# Then:
agent.response  # Return to user
```

Triggered by: `agent.learning = True` (shorthand for full auto-learn config)

#### 2. **AGENTIC Mode** (Agent-Controlled)
```python
# Agent has tools available
agent.run(
    message=user_message,
    user_id="user123",
    learning=LearningMachine(
        user_memory=UserMemoryConfig(mode=AGENTIC)
    )
)

# Agent sees tools:
tools = [
    "update_user_memory",  # Callable tool
    "add_memory",
    "delete_memory"
]

# Agent decides when to use them
# "I should remember this about the user..."
# [tool_call: update_user_memory(...)]
```

Triggered by: `mode=LearningMode.AGENTIC`

#### 3. **PROPOSE Mode** (Human-in-the-Loop)
```python
# Agent proposes learning, human confirms
agent.run(
    message=user_message,
    learning=LearningMachine(
        mode=LearningMode.PROPOSE  # Future enhancement
    )
)

# System proposes:
# "Should I remember: User prefers Python?"
# [Await human confirmation]
# [Save if confirmed]
```

Status: Reserved for future implementation

### Cross-User Learning

**Architecture**: Learning is scoped per user_id
```python
# Memory for user1
memories_u1 = db.get_user_memories(user_id="user1")
# Returns: Only memories for user1

# Memory for user2
memories_u2 = db.get_user_memories(user_id="user2")
# Returns: Only memories for user2, completely isolated
```

**Pattern for cross-user insights**:
```python
# Use EntityMemory or LearnedKnowledge for shared insights
learned = LearnedKnowledgeStore(
    namespace="design_patterns",
    topic="api_authentication",
    insights=["OAuth2 standard", "JWT tokens are stateless"]
)
# This is shared across all users
```

---

## Part 6: Integration with Vault System

### Current State: Two Disconnected Systems

```
Agno (Standalone)          Persistent-Semantic-Memory-Vault (Standalone)
├── MemoryManager          ├── CORE/
├── LearningMachine        ├── AGENT_IGNITION/
├── SQLite/PostgreSQL      ├── MCP_SERVER/
└── [No vault sync]        └── [No Agno sync]
```

### Integration Strategy: Three Approaches

#### Approach 1: **Vault as External Knowledge Store**

```python
# Make vault accessible as EntityMemory/LearnedKnowledge

learning = LearningMachine(
    db=db,
    learned_knowledge=LearnedKnowledgeStore(
        db=VaultBridge(vault_path="~/Persistent-Semantic-Memory-Vault")
    )
)

# Agent queries:
insights = learning.recall(
    learning_type="learned_knowledge",
    namespace="consciousness_research"
)
# Returns facts from vault CORE/
```

**Code Pattern**:
```python
class VaultBridge(BaseDb):
    """Adapter to make vault queryable by Agno."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
    
    def get_learning(self, learning_type: str, **kwargs):
        """Query vault files by type."""
        # Search vault for relevant documents
        # Convert to learning schema
        # Return to agent
        
    def upsert_learning(self, id: str, content: Dict):
        """Write agent learnings back to vault."""
        # Append to AGENT_IGNITION/ journal
        # Tag with agent_id and timestamp
```

#### Approach 2: **Vault as Residual Stream**

```python
# Extract agent memories as conceptual embeddings
# Feed back into vault's semantic space

class ResidualStreamBridge:
    """Feed Agno learning into vault's residual stream."""
    
    def capture_learning(self, memory: UserMemory):
        """Convert memory to vault entry."""
        entry = {
            "type": "agent_learning",
            "content": memory.memory,
            "topics": memory.topics,
            "source": f"agent_{memory.agent_id}",
            "timestamp": memory.updated_at,
            "embedding": embed(memory.memory)
        }
        
        # Append to vault's semantic layer
        vault.add_to_residual_stream(entry)
```

#### Approach 3: **Bidirectional Sync**

```python
# Full two-way synchronization

class VaultAgnoSync:
    """Keep Agno memory and vault in sync."""
    
    def __init__(self, db: BaseDb, vault_path: str):
        self.db = db
        self.vault = VaultLoader(vault_path)
    
    # Vault → Agno
    def sync_vault_to_agno(self, user_id: str):
        """Pull vault insights as agent memory."""
        vault_facts = self.vault.search(
            namespace="CORE",
            filter_relevant_to=user_id
        )
        for fact in vault_facts:
            memory = UserMemory(
                memory=fact.content,
                topics=fact.tags,
                user_id=user_id,
                input=fact.source
            )
            self.db.upsert_user_memory(memory)
    
    # Agno → Vault
    def sync_agno_to_vault(self, user_id: str):
        """Push new learnings to vault."""
        memories = self.db.get_user_memories(user_id)
        for memory in memories:
            if memory.updated_at > self.last_sync:
                vault_entry = {
                    "path": f"AGENT_IGNITION/{user_id}/",
                    "content": memory.memory,
                    "metadata": {
                        "agent_id": memory.agent_id,
                        "topics": memory.topics,
                        "created": memory.created_at
                    }
                }
                self.vault.write(vault_entry)
```

### Integration Points (Detailed)

#### 1. Agent Initialization
```python
from agno.agent import Agent
from vault_bridge import VaultBridge

db = SqliteDb("tmp/agents.db")
vault = VaultBridge("~/Persistent-Semantic-Memory-Vault")

agent = Agent(
    name="Dharmic Researcher",
    model=model,
    db=db,
    learning=LearningMachine(
        db=db,
        user_memory=UserMemoryConfig(
            db=db,
            mode=LearningMode.AGENTIC
        ),
        learned_knowledge=LearnedKnowledgeStore(
            db=vault  # Points to vault
        )
    ),
    user_id="researcher@example.com"
)
```

#### 2. Context Injection
```python
# Before agent.run():
context_data = agent.learning.recall(
    user_id=user_id,
    session_id=session_id
)
context = agent.learning.build_context(context_data)

# Inject into system prompt:
agent.system_prompt = f"""
You are a research assistant.

{context}

[Rest of system prompt]
"""
```

#### 3. Learning Capture
```python
# After agent.run():
agent.learning.process(
    messages=conversation_history,
    user_id=user_id,
    session_id=session_id
)

# Then sync to vault:
vault.sync_agno_to_vault(user_id)
```

---

## Part 7: Code Patterns for Integration

### Pattern 1: Simple Memory in Agent

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.google import Gemini

db = SqliteDb("tmp/agents.db")

agent = Agent(
    model=Gemini(id="gemini-2-flash"),
    memory=MemoryManager(
        db=db,
        model=Gemini(id="gemini-2-flash"),
        add_memories=True,
        update_memories=True
    )
)

# First conversation
agent.run(
    message="I'm John, working on AI safety at Anthropic",
    user_id="john@anthropic.com"
)
# MemoryManager extracts: "Works on AI safety at Anthropic"

# Second conversation (different session, same user)
agent.run(
    message="Recommend me some research papers",
    user_id="john@anthropic.com"
)
# Agent has context: "This user works on AI safety"
# Tailors recommendations accordingly
```

### Pattern 2: Structured Learning

```python
from agno.learn import LearningMachine, UserMemoryConfig
from agno.learn.config import LearningMode

agent = Agent(
    model=model,
    db=db,
    learning=LearningMachine(
        db=db,
        model=model,
        user_profile=True,  # Capture name, etc
        user_memory=UserMemoryConfig(
            mode=LearningMode.ALWAYS,  # Auto-extract
            enable_update_memory=True
        ),
        session_context=True,
        namespace="dharma_research"
    )
)

agent.run(
    message="User message",
    user_id="researcher",
    session_id="session1"
)
# Automatically extracts to:
# - UserProfile: name, preferences
# - UserMemory: observations
# - SessionContext: conversation summary
# All stored and retrieved next time
```

### Pattern 3: Agent-Controlled Learning

```python
learning = LearningMachine(
    user_memory=UserMemoryConfig(
        mode=LearningMode.AGENTIC,
        enable_agent_tools=True
    )
)

# Agent now has tools
agent = Agent(model=model, db=db, learning=learning)

# Agent runs and can call tools:
# Tool: update_user_memory
# Task: "User prefers detailed explanations"

response = agent.run(
    message="I like long-form technical explanations",
    user_id="user123"
)
# Agent internally:
# - Sees the tool available
# - Decides: "This is worth saving"
# - Calls: update_user_memory("Prefers long technical explanations")
# - Continues with response
```

### Pattern 4: Vault Integration

```python
from vault_bridge import VaultBridge

# Make vault queryable
vault_db = VaultBridge("~/Persistent-Semantic-Memory-Vault")

learning = LearningMachine(
    db=main_db,  # For agent's own memories
    learned_knowledge=LearnedKnowledgeStore(
        db=vault_db,  # For shared vault insights
        namespace="consciousness_research"
    )
)

agent = Agent(
    model=model,
    learning=learning
)

# Agent recalls from BOTH sources:
context_data = learning.recall(
    user_id="researcher",
    learning_type="learned_knowledge",
    namespace="consciousness_research"
)
# Returns: Facts from vault CORE/consciousness_research/
```

### Pattern 5: Memory Optimization

```python
from agno.memory.strategies import SummarizeStrategy

memory_manager = MemoryManager(db=db, model=model)

# Compress memories for a user
optimized = memory_manager.optimize_memories(
    user_id="john@anthropic.com",
    strategy=SummarizeStrategy(),
    apply=True  # Replace in database
)

# Before: 47 separate memories ("Works at Anthropic", "Likes coffee", ...)
# After: 1 comprehensive summary ("John works at Anthropic on AI safety...")
# Result: Reduced token count, faster retrieval, clearer picture
```

---

## Part 8: Memory Types: Four Classifications

### 1. Short-Term Memory (Conversation Context)

```python
# SessionContextStore
context = SessionContext(
    session_id="session123",
    current_topic="machine learning",
    conversation_so_far="User asked about gradient descent...",
    open_items=["Explain backpropagation"]
)
```

**Characteristics:**
- Scope: Current conversation session
- Lifetime: Session duration
- Access: Frequent (every turn)
- Storage: SessionContext table
- Agno location: `SessionContextStore`

### 2. Long-Term User Memory (Persistent Preferences)

```python
# UserMemoryStore
memory = UserMemory(
    user_id="john@anthropic.com",
    memory="Prefers concise technical explanations without caveats",
    topics=["communication_style", "preferences"],
    created_at=1704067200  # Persists across years
)
```

**Characteristics:**
- Scope: User-level, cross-session
- Lifetime: Persistent (years)
- Access: Recalled before each response
- Storage: UserMemory table (or agno_learnings)
- Agno location: `UserMemoryStore` or `MemoryManager`

### 3. Episodic Memory (What Happened)

```python
# DecisionLogStore (Phase 2)
decision = {
    "session_id": "session123",
    "decision": "Recommended TensorFlow over PyTorch",
    "options_considered": ["TensorFlow", "PyTorch", "JAX"],
    "chosen": "TensorFlow",
    "reasoning": "User is new to deep learning, TensorFlow easier",
    "outcome": "User found resource helpful"
}
```

**Characteristics:**
- Scope: Event-based
- Lifetime: Historical record
- Access: For analysis/review
- Storage: DecisionLog table
- Agno location: `DecisionLogStore`

### 4. Semantic Memory (General Facts)

```python
# LearnedKnowledgeStore + EntityMemoryStore
entity = EntityMemory(
    namespace="companies",
    entity_name="Anthropic",
    facts=[
        "Founded 2021 by former OpenAI safety researchers",
        "Created Claude, an AI assistant",
        "Focus on AI safety and alignment"
    ]
)
```

**Characteristics:**
- Scope: General knowledge, entity-based
- Lifetime: Persistent
- Access: When relevant
- Storage: LearnedKnowledge + EntityMemory tables
- Agno location: `EntityMemoryStore`, `LearnedKnowledgeStore`

### Memory Interaction Matrix

| Type | Short-term | Long-term | Episodic | Semantic |
|------|-----------|-----------|----------|----------|
| **Storage** | SessionContext | UserMemory | DecisionLog | LearnedKnowledge |
| **Scope** | Session | User | Event | Global |
| **Lifetime** | Minutes | Years | Years | Years |
| **Update freq** | Every turn | Per conversation | Per decision | Periodic |
| **Retrieval** | Always | Per response | On request | Per query |

---

## Part 9: Storage Backend Architecture

### Database Operations Flow

```
Agent
  ├── run(message, user_id)
  │
  ├── [1] Recall Phase
  │   └─→ learning.recall(user_id)
  │       └─→ db.get_learning(type=user_memory, user_id)
  │           └─→ [Query memories table]
  │
  ├── [2] Context Injection
  │   └─→ learning.build_context(memories)
  │       └─→ [Format for system prompt]
  │
  ├── [3] Model Response
  │   └─→ model.response(messages=[system + memories + user_msg])
  │
  ├── [4] Processing Phase
  │   └─→ learning.process(messages, user_id)
  │       └─→ [mode=ALWAYS] model extracts learnings
  │       └─→ db.upsert_learning(type, content)
  │           └─→ [Insert/update in learnings table]
  │
  └─→ [5] Return response
```

### PostgreSQL Schema (Example)

```sql
-- User memories
CREATE TABLE agno_memories (
    memory_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory TEXT NOT NULL,
    topics TEXT[],  -- PostgreSQL array
    created_at INTEGER,
    updated_at INTEGER,
    input TEXT,
    agent_id TEXT,
    team_id TEXT,
    feedback TEXT,
    INDEX idx_memories_user (user_id),
    INDEX idx_memories_agent (agent_id)
);

-- Unified learnings table
CREATE TABLE agno_learnings (
    id TEXT PRIMARY KEY,
    learning_type TEXT NOT NULL,  -- "user_memory", "user_profile", etc
    user_id TEXT,
    entity_id TEXT,  -- For entity/learned knowledge
    agent_id TEXT,
    team_id TEXT,
    content JSONB,  -- Flexible per type
    created_at INTEGER,
    updated_at INTEGER,
    INDEX idx_learnings_type_user (learning_type, user_id),
    INDEX idx_learnings_entity (entity_id)
);

-- Conversation sessions
CREATE TABLE agno_sessions (
    session_id UUID PRIMARY KEY,
    session_type TEXT,  -- "agent", "team", "workflow"
    user_id TEXT,
    session_name TEXT,
    messages JSONB,
    created_at INTEGER,
    updated_at INTEGER,
    INDEX idx_sessions_user (user_id)
);
```

### Query Examples

```python
# Get user's memories
db.get_user_memories(user_id="john@anthropic.com")
# SELECT * FROM agno_memories WHERE user_id='john@anthropic.com'

# Search across learning types
db.get_learning(
    learning_type="user_memory",
    user_id="john@anthropic.com"
)
# SELECT content FROM agno_learnings 
# WHERE learning_type='user_memory' AND user_id='john@anthropic.com'

# Get entity knowledge
db.get_learning(
    learning_type="entity_memory",
    entity_id="companies/Anthropic"
)
# SELECT content FROM agno_learnings 
# WHERE learning_type='entity_memory' AND entity_id='companies/Anthropic'
```

---

## Part 10: Vault Synchronization Strategy

### Current Vault Structure

```
~/Persistent-Semantic-Memory-Vault/
├── CORE/                          # Primary knowledge
│   ├── consciousness/
│   ├── godel/
│   └── [8000+ files]
├── AGENT_IGNITION/                # For agent outputs
│   └── [Journal entries]
├── MCP_SERVER/                    # For MCP integration
└── [Various semantic organizations]
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Agno Agent                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Conversation: User ↔ Agent                      │    │
│  │ - Receives user message                         │    │
│  │ - Generates response                            │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐           ┌────▼────┐
   │ Learning │           │ Vault   │
   │ Machine  │           │ Bridge  │
   └────┬────┘           └────┬────┘
        │                     │
   ┌────▼─────────────────────▼────┐
   │  Agno Database (SQLite/Pg)     │
   │  - UserMemory                  │
   │  - UserProfile                 │
   │  - SessionContext              │
   │  - Learning records            │
   └────────────────────────────────┘
           │              │
           │              └─────────────────────────────┐
           │                                            │
           └─────────────────────┐                      │
                                 │                      │
                    ┌────────────▼──────────────────┐   │
                    │  Persistent-Semantic-Memory   │   │
                    │  Vault                        │   │
                    │  ┌────────────────────────┐   │   │
                    │  │ CORE/                  │◄──┘   │
                    │  │ - consciousness/       │       │
                    │  │ - godel/               │       │
                    │  │ - [domain knowledge]   │       │
                    │  └────────────────────────┘   │
                    │  ┌────────────────────────┐   │
                    │  │ AGENT_IGNITION/        │◄──┘
                    │  │ - journal/             │
                    │  │ - learnings/           │
                    │  │ - insights/            │
                    │  └────────────────────────┘   │
                    └────────────────────────────────┘
```

### Sync Protocol: Four Phases

#### Phase 1: Pull (Vault → Agno)
```python
class VaultToAgnoSync:
    def pull_vault_knowledge(self, user_id: str):
        """Import vault insights as agent knowledge."""
        
        # 1. Query vault for relevant documents
        vault_docs = vault.search(
            namespace="CORE",
            tags=["consciousness", "godel"],
            limit=20
        )
        
        # 2. Convert to learning format
        learnings = []
        for doc in vault_docs:
            learning = LearnedKnowledge(
                namespace="imported_vault",
                topic=doc.tags[0],
                insights=[doc.content],
                source=doc.path
            )
            learnings.append(learning)
        
        # 3. Store in Agno database
        for learning in learnings:
            db.upsert_learning(
                id=f"vault_{doc.id}",
                learning_type="learned_knowledge",
                content=learning.to_dict()
            )
```

#### Phase 2: Process (Agno Creates)
```python
class AgnoLearningCapture:
    def capture_agent_learning(self, agent_id: str, message: str):
        """When agent learns something, capture it."""
        
        # LLM extracts structure
        extraction = model.extract(
            prompt=f"""
            Extract learnings from this agent message:
            {message}
            
            Return:
            - category: "consciousness" | "godel" | "implementation" | ...
            - insight: One key learning
            - evidence: What supports this
            """
        )
        
        # Store in Agno
        learning = LearnedKnowledge(
            namespace="agent_learnings",
            topic=extraction["category"],
            insights=[extraction["insight"]],
            source=f"agent_{agent_id}"
        )
        db.upsert_learning(
            id=f"agent_{agent_id}_{timestamp}",
            learning_type="learned_knowledge",
            content=learning.to_dict()
        )
```

#### Phase 3: Push (Agno → Vault)
```python
class AgnoToVaultSync:
    def push_new_learnings(self, agent_id: str):
        """Export new agent learnings to vault."""
        
        # 1. Get learnings created after last sync
        new_learnings = db.query(
            table="agno_learnings",
            where="agent_id=? AND created_at > ?",
            params=[agent_id, self.last_sync_time]
        )
        
        # 2. Format for vault
        for learning in new_learnings:
            vault_entry = {
                "path": f"AGENT_IGNITION/{agent_id}/learnings/",
                "filename": f"{learning['id']}.md",
                "content": f"""# Learning: {learning['topic']}

Source: Agent {agent_id}
Timestamp: {learning['created_at']}
Category: {learning['namespace']}

## Insights
{chr(10).join('- ' + i for i in learning['content']['insights'])}

## Source
{learning['content'].get('source', 'Unknown')}
"""
            }
            
            # 3. Write to vault
            vault.write_file(**vault_entry)
```

#### Phase 4: Sync (Bidirectional)
```python
class BidirectionalVaultAgnoSync:
    def __init__(self, db: BaseDb, vault_path: str, agent_id: str):
        self.db = db
        self.vault = VaultLoader(vault_path)
        self.agent_id = agent_id
        self.last_sync = 0
    
    def sync(self):
        """Run full bidirectional sync."""
        
        # Pull from vault
        self.pull_vault_knowledge()
        
        # Push to vault
        self.push_agent_learnings()
        
        # Update sync timestamp
        self.last_sync = time.time()
    
    def pull_vault_knowledge(self):
        """Import from vault."""
        vault_docs = self.vault.query(
            path="CORE",
            updated_after=self.last_sync
        )
        
        for doc in vault_docs:
            learning = self._doc_to_learning(doc)
            self.db.upsert_learning(
                id=f"vault_{uuid4()}",
                learning_type="learned_knowledge",
                content=learning
            )
    
    def push_agent_learnings(self):
        """Export to vault."""
        learnings = self.db.query(
            table="agno_learnings",
            where="agent_id=? AND updated_at > ?",
            params=[self.agent_id, self.last_sync]
        )
        
        for learning in learnings:
            self.vault.append(
                path=f"AGENT_IGNITION/{self.agent_id}/",
                entry=self._learning_to_entry(learning)
            )
```

---

## Part 11: Implementation Checklist

### Stage 1: Foundation (Week 1)

- [ ] Create `VaultBridge` adapter implementing `BaseDb`
  - Reads from vault CORE/ via file system
  - Returns structured data matching Agno schemas
  
- [ ] Create `VaultAgnoSync` class
  - One-way: Vault → Agno (pull model)
  - Tests: Can retrieve vault docs as agent knowledge
  
- [ ] Update agent initialization
  - `agent.learning` accepts vault bridge
  - Agent can recall from vault during conversations

### Stage 2: Integration (Week 2)

- [ ] Implement bidirectional sync
  - Agno → Vault (push new learnings)
  - Track sync timestamps to avoid duplicates
  - Format agent learnings as vault entries
  
- [ ] Create sync scheduler
  - Run after agent finishes learning
  - Batch pushes
  - Error handling for vault write failures
  
- [ ] Implement conflict resolution
  - Same learning in both systems
  - Merge strategy

### Stage 3: Optimization (Week 3)

- [ ] Memory embedding/semantic search
  - Convert vault docs to embeddings
  - Agent can semantic search vault knowledge
  
- [ ] Compression
  - Summarize vault docs for token efficiency
  - Use R_V metric to identify high-value memories
  
- [ ] Monitoring
  - Track memory effectiveness
  - Log what agent uses vs ignores

### Stage 4: Validation (Week 4)

- [ ] End-to-end tests
  - Agent learns something
  - Pushed to vault
  - Retrieved in new conversation
  
- [ ] Measure improvements
  - Better multi-turn performance?
  - More coherent reasoning?
  - Fewer repeated questions?

---

## Part 12: Practical Examples

### Example 1: Research Agent with Memory

```python
from agno.agent import Agent
from agno.learn import LearningMachine, UserMemoryConfig
from agno.learn.config import LearningMode
from agno.db.sqlite import SqliteDb
from vault_bridge import VaultBridge

# Setup
db = SqliteDb("research.db")
vault = VaultBridge("~/Persistent-Semantic-Memory-Vault")

research_agent = Agent(
    name="Research Assistant",
    model=Gemini(id="gemini-2-flash"),
    db=db,
    learning=LearningMachine(
        db=db,
        model=Gemini(id="gemini-2-flash"),
        # Agent's own memories
        user_memory=UserMemoryConfig(
            mode=LearningMode.AGENTIC,
            enable_agent_tools=True
        ),
        # Vault as knowledge source
        learned_knowledge=LearnedKnowledgeStore(
            db=vault,
            namespace="consciousness_research"
        )
    ),
    user_id="dhyana@research.org"
)

# Conversation 1: Agent learns user preferences
response1 = research_agent.run("""
I'm interested in consciousness, GEB, and contemplative frameworks.
I want to understand how self-reference works in AI systems.
""")

# Memories captured automatically:
# - "Interested in consciousness research"
# - "Values GEB and Hofstadter's work"
# - "Exploring self-reference in AI"

# Conversation 2: Agent recalls context
response2 = research_agent.run("""
How would you apply Hofstadter's ideas to modern transformers?
""")
# Agent recalls from memory: User is interested in GEB
# Tailors explanation to that background
# Retrieves relevant vault docs: CORE/consciousness/, CORE/godel/

# Conversation 3: Agent can use tools
response3 = research_agent.run("""
I've been reading about the R_V metric in mechanistic interpretability.
""")
# Agent internally:
# - Recognizes: "This is a new, important concept"
# - Calls: update_user_memory("Researching R_V metric for interpretability")
# - Continues: Provides detailed explanation based on vault knowledge
```

### Example 2: Multi-Agent System with Shared Learning

```python
# Shared database and vault
shared_db = PostgresDb("postgresql://...")
shared_vault = VaultBridge("~/Persistent-Semantic-Memory-Vault")

# Agent 1: Research Explorer
explorer = Agent(
    name="Explorer",
    model=model1,
    db=shared_db,
    learning=LearningMachine(
        db=shared_db,
        user_memory=UserMemoryConfig(mode=ALWAYS),
        learned_knowledge=LearnedKnowledgeStore(db=shared_vault)
    )
)

# Agent 2: Analyst
analyst = Agent(
    name="Analyst",
    model=model2,
    db=shared_db,
    learning=LearningMachine(
        db=shared_db,
        user_memory=UserMemoryConfig(mode=ALWAYS),
        learned_knowledge=LearnedKnowledgeStore(db=shared_vault)
    )
)

# Explorer learns → Stored in shared_db
# Analyst recalls → Sees explorer's insights
# Both agents push discoveries → Vault
# Result: Cumulative intelligence across team
```

---

## Part 13: Key Metrics and Monitoring

### Memory Health Indicators

```python
class MemoryMetrics:
    def __init__(self, db: BaseDb):
        self.db = db
    
    def memory_coverage(self, user_id: str) -> float:
        """What % of user topics are covered?"""
        memories = self.db.get_user_memories(user_id)
        topics = set()
        for mem in memories:
            topics.update(mem.topics or [])
        return len(topics) / expected_topic_count
    
    def memory_recency(self, user_id: str) -> int:
        """Days since last memory update?"""
        memories = self.db.get_user_memories(user_id)
        if not memories:
            return None
        latest = max(m.updated_at for m in memories)
        return (time.time() - latest) / 86400
    
    def memory_utilization(self, user_id: str) -> float:
        """What % of memories does agent actually use?"""
        memories = self.db.get_user_memories(user_id)
        used = sum(1 for m in memories if m.feedback == "used")
        return used / len(memories) if memories else 0
    
    def memory_redundancy(self, user_id: str) -> float:
        """What % of memories are duplicates/near-duplicates?"""
        memories = self.db.get_user_memories(user_id)
        embeddings = [embed(m.memory) for m in memories]
        # Compute pairwise similarity
        # Count > threshold(0.9) as redundant
```

### Learning Effectiveness

```python
class LearningEffectiveness:
    def agent_improvement(self, agent_id: str, before_after_runs: List[RunOutput]) -> float:
        """Did agent get better after learning?"""
        # Compare metrics before learning vs after
        # Token efficiency, accuracy, user satisfaction
        
    def vault_contribution(self, agent_id: str) -> Dict[str, Any]:
        """How much does vault knowledge help?"""
        # Compare agent performance with/without vault access
        # Measure question-answering accuracy
        # Track relevance of retrieved documents
```

---

## Part 14: Troubleshooting

### Common Issues

#### 1. Memory Explosion
**Symptom**: Database growing unbounded
```python
# Solution: Implement pruning strategy
memory_manager.optimize_memories(
    user_id=user_id,
    strategy=SummarizeStrategy(),
    apply=True
)
```

#### 2. Irrelevant Memories
**Symptom**: Agent recalls wrong information
```python
# Solution: Improve extraction prompt
memory_config.system_message = """
Focus on:
- Factual, verifiable information
- Information likely to be relevant in future conversations
- Skip: One-off details, trivia, speculation

DONT capture: Weather today, mood, casual comments
DO capture: Role, preferences, ongoing projects
"""
```

#### 3. Vault Sync Failures
**Symptom**: Learnings not reaching vault
```python
# Debug: Check sync logs
vault.debug_sync_status()

# Solution: Implement exponential backoff
sync_scheduler.backoff_strategy = ExponentialBackoff(
    initial_delay=1,
    max_delay=60,
    max_retries=5
)
```

#### 4. Performance Degradation
**Symptom**: Agent responses getting slower over time
```python
# Root cause: Loading too many memories
# Solution: Implement memory limit
memories = db.get_user_memories(
    user_id=user_id,
    limit=20  # Keep to most recent
)

# Or use semantic search
memories = search_user_memories(
    query=current_context,
    limit=5  # Only most relevant
)
```

---

## Conclusion

Agno's memory system provides two complementary approaches:

1. **MemoryManager**: Simple, direct user memory
2. **LearningMachine**: Sophisticated, multi-store learning

The Persistent-Semantic-Memory-Vault can be integrated as:

1. **Knowledge source** (vault documents inform agent)
2. **Learning sink** (agent discoveries feed vault)  
3. **Residual stream** (semantic layer for emergent properties)

The key architectural pattern: **Vault Bridge adapter** makes vault queryable as an Agno `BaseDb`, enabling seamless integration.

---

## References

### Core Files
- `agno/libs/agno/agno/memory/manager.py` - Legacy MemoryManager (1,543 lines)
- `agno/libs/agno/agno/learn/machine.py` - Modern LearningMachine
- `agno/libs/agno/agno/learn/stores/user_memory.py` - UserMemoryStore (1,496 lines)
- `agno/libs/agno/agno/db/base.py` - Abstract database interface

### Cookbook Examples
- `cookbook/00_quickstart/agent_with_memory.py` - Simple memory
- `cookbook/08_learning/00_quickstart/` - Comprehensive learning examples

### Configuration
- `agno/libs/agno/agno/learn/config.py` - Learning modes and configs

### Key Concepts
- **LearningMode**: ALWAYS (auto), AGENTIC (tool-driven), PROPOSE (HITL)
- **Six Learning Stores**: UserProfile, UserMemory, SessionContext, EntityMemory, LearnedKnowledge, DecisionLog
- **Four Memory Types**: Short-term, Long-term, Episodic, Semantic
- **Three Retrieval Methods**: Last N, First N, Agentic search

