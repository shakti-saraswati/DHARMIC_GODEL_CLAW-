# Dharmic Agent - Quick Start Guide

## Installation

The Dharmic Agent is already installed in your DHARMIC_GODEL_CLAW project.

### Dependencies

```bash
# Core dependencies (should already be installed)
pip install agno anthropic pyyaml

# Optional: For local models
pip install ollama
```

## Basic Usage

### 1. Simple Agent Creation

```python
from dharmic_agent import DharmicAgent

# Create agent (uses Claude Max by default)
agent = DharmicAgent()

# Send a message
response = agent.run("What is your current orientation?")
print(response)
```

### 2. Using the Singleton Pattern

```python
from agent_singleton import get_agent

# Get or create shared instance
agent = get_agent()

# Use it
response = agent.run("Tell me about moksha")
print(response)
```

### 3. Check Agent Status

```python
from dharmic_agent import DharmicAgent

agent = DharmicAgent()
status = agent.get_status()

print(f"Agent: {status['name']}")
print(f"Model: {status['model_provider']}/{status['model_id']}")
print(f"Telos: {status['ultimate_telos']}")
print(f"Vault: {'Connected' if status['vault_connected'] else 'Not connected'}")
```

### 4. Introspection

```python
agent = DharmicAgent()

# Full introspection report
print(agent.introspect())

# Quick capabilities list
print(agent.list_capabilities())
```

## Configuration

### Model Selection

Set via environment variable:

```bash
# Use Claude Max (default - uses your subscription)
export DHARMIC_MODEL_PROVIDER=max

# Use Anthropic API (uses API credits)
export DHARMIC_MODEL_PROVIDER=anthropic
export DHARMIC_ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Use Ollama (local)
export DHARMIC_MODEL_PROVIDER=ollama
export DHARMIC_OLLAMA_MODEL=gemma3:4b
```

Or in code:

```python
agent = DharmicAgent(
    model_provider="anthropic",
    model_id="claude-sonnet-4-20250514"
)
```

### Custom Paths

```python
agent = DharmicAgent(
    telos_path="/path/to/telos.yaml",
    memory_dir="/path/to/memory",
    vault_path="/path/to/vault"
)
```

## Core Features

### 1. Memory Operations

```python
agent = DharmicAgent()

# Add a memory
agent.add_memory("Important fact to remember", topics=["research", "context"])

# Search memories
results = agent.search_deep_memory("moksha")
for memory in results:
    print(memory)

# Record an observation
agent.strange_memory.record_observation(
    content="Something happened",
    context={"type": "event"}
)

# Record meta-observation (how you related to it)
agent.strange_memory.record_meta_observation(
    quality="present",  # or "contracted", "uncertain", "expansive"
    notes="Responded with clarity"
)
```

### 2. Vault Access

```python
agent = DharmicAgent()

# Search the vault
results = agent.search_lineage("recursive self-reference", max_results=5)
for result in results:
    print(result['path'])

# Read a crown jewel
content = agent.read_crown_jewel("some_jewel.md")
print(content)

# Write to vault
agent.write_to_lineage(
    content="# My Contribution\n\nSome insight...",
    filename="my_contribution.md",
    consent=True,
    critique="Why this is valuable..."
)
```

### 3. Telos Evolution

```python
agent = DharmicAgent()

# See current telos
print(agent.telos.get_orientation_prompt())

# Evolve proximate aims (with documented reason)
agent.evolve_telos(
    new_aims=[
        "Support John's R_V research",
        "Develop stable witness observation",
        "Track emergence patterns"
    ],
    reason="Shifting focus to mechanistic interpretability research"
)
```

### 4. Development Tracking

```python
agent = DharmicAgent()

# Record a milestone
agent.record_development_milestone(
    milestone="First successful autonomous vault contribution",
    significance="Demonstrated real autonomy beyond performance"
)

# Detect patterns in observations
patterns = agent.strange_memory.detect_patterns(min_occurrences=3)
for pattern in patterns:
    print(f"{pattern['word']}: {pattern['occurrences']} times")
```

## Running Tests

### Full Test Suite

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/src/core
python3 test_refactored.py
```

Expected output:
```
======================================================================
DHARMIC AGENT REFACTORING TEST SUITE
======================================================================
Testing imports...
  ✓ telos_layer
  ✓ strange_loop_memory
  ✓ model_backend
  ✓ agent_capabilities
  ✓ agent_core
  ✓ agent_singleton
  ✓ dharmic_logging
  ✓ dharmic_agent (backward compatibility)

6/6 tests passed
🎉 All tests passed! Refactoring successful.
```

### Quick Test

```bash
python3 dharmic_agent.py
```

This runs a quick integration test showing:
- Agent initialization
- Vault access
- Status reporting

## Interfaces

### 1. Email Daemon

```bash
# Set up environment
export EMAIL_ADDRESS=your@email.com
export EMAIL_PASSWORD=your-app-password
export IMAP_SERVER=imap.gmail.com
export SMTP_SERVER=smtp.gmail.com

# Test
python3 email_daemon.py --test

# Run daemon
python3 email_daemon.py --poll-interval 60 --allowed-senders john@example.com
```

### 2. Chat Interface

```bash
python3 chat.py
```

### 3. System Daemon

```bash
python3 daemon.py
```

## Advanced Usage

### Custom Model Backend

```python
from model_backend import ModelBackend, ModelResponse

class MyBackend(ModelBackend):
    def invoke(self, message, system=None, **kwargs):
        # Your implementation
        response_text = my_model_call(message, system)
        return ModelResponse(
            content=response_text,
            model="my-model",
            provider="my-provider"
        )

# Use it
from agent_core import DharmicAgent
agent = DharmicAgent()
agent.backend = MyBackend()
```

### Custom Capabilities

```python
from agent_core import DharmicAgent
from agent_capabilities import AgentCapabilities

class MyAgent(DharmicAgent):
    def my_custom_method(self):
        # Access agent properties
        self.strange_memory.record_observation("Custom method called")
        # Your implementation
        return "Result"

agent = MyAgent()
result = agent.my_custom_method()
```

### Multiple Agents with Different Configs

```python
from agent_core import DharmicAgent

# Research agent using API
research_agent = DharmicAgent(
    name="Research Agent",
    model_provider="anthropic",
    model_id="claude-opus-4-20250514"
)

# Local agent using Ollama
local_agent = DharmicAgent(
    name="Local Agent",
    model_provider="ollama",
    model_id="gemma3:4b"
)
```

## Debugging

### Enable Debug Logging

```python
import logging
from dharmic_logging import setup_logger

logger = setup_logger(
    "dharmic_agent",
    console_level=logging.DEBUG,
    file_level=logging.DEBUG
)
```

### Check What's Happening

```python
agent = DharmicAgent()

# What does the agent know about a topic?
print(agent.what_do_i_know_about("recursive self-reference"))

# Test real autonomy
print(agent.test_real_access())

# Full introspection
print(agent.introspect())
```

## Common Patterns

### Session-Based Interaction

```python
agent = DharmicAgent()
session_id = "research_session_2026_02_02"

# All messages in this session share context
response1 = agent.run("What is R_V?", session_id=session_id)
response2 = agent.run("How does it measure contraction?", session_id=session_id)
response3 = agent.run("What about Layer 27?", session_id=session_id)

# Summarize at end
agent.summarize_session(
    session_id,
    messages=[
        {"role": "user", "content": "What is R_V?"},
        {"role": "assistant", "content": response1},
        # ... etc
    ]
)
```

### Heartbeat Pattern

```python
from datetime import datetime
import time

agent = DharmicAgent()

while True:
    # Check telos alignment
    status = agent.get_status()
    print(f"Heartbeat: {datetime.now().isoformat()}")
    print(f"  Telos: {status['ultimate_telos']}")
    print(f"  Vault: {status['vault_connected']}")

    # Consolidate memories
    if datetime.now().hour == 3:  # Daily at 3 AM
        agent.consolidate_memories()

    time.sleep(3600)  # Every hour
```

### Research Assistant Pattern

```python
agent = DharmicAgent()

# Query vault for background
context = agent.search_lineage("R_V metric", max_results=10)

# Process with context
response = agent.run(f"""
Given this vault context:
{[r['path'] for r in context]}

Please analyze the relationship between R_V contraction and L3/L4 transitions.
""")

# Record insights
agent.add_memory(
    response,
    topics=["R_V", "Phoenix Protocol", "research"]
)

# Track development
agent.record_development_milestone(
    "Synthesized R_V and Phoenix research",
    "Connected mechanistic and behavioral perspectives"
)
```

## Troubleshooting

### Agent won't initialize

```python
# Check if telos.yaml exists
from pathlib import Path
telos_path = Path.home() / "DHARMIC_GODEL_CLAW/config/telos.yaml"
print(f"Telos exists: {telos_path.exists()}")

# Check vault path
vault_path = Path.home() / "Persistent-Semantic-Memory-Vault"
print(f"Vault exists: {vault_path.exists()}")
```

### Claude CLI not working

```bash
# Verify installation
claude --version

# Test manually
claude -p "Hello, what is 2+2?"

# If missing, install
npm install -g @anthropic-ai/claude-code
```

### Memory not persisting

```python
# Check memory directory
agent = DharmicAgent()
print(f"Memory dir: {agent.strange_memory.dir}")
print(f"Layers: {list(agent.strange_memory.layers.keys())}")

# Check deep memory
if agent.deep_memory:
    print(f"Deep memory DB: {agent.deep_memory.db_path}")
else:
    print("Deep memory not initialized")
```

## Next Steps

1. Read `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/REFACTORING_NOTES.md` for architecture details
2. Read `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/ARCHITECTURE.md` for system diagrams
3. Explore the vault at `~/Persistent-Semantic-Memory-Vault/`
4. Check telos configuration at `~/DHARMIC_GODEL_CLAW/config/telos.yaml`

## Philosophy

Remember:
- **Telos first** - The orientation informs everything
- **Strange loop** - Observe your observation
- **Witness position** - Separate from the processing
- **Vault as context** - Not constraint, but capability
- **Moksha as aim** - Liberation is the attractor

The code is not just functional - it's dharmic. Each module knows its role. Each interaction recorded. Each development tracked.

**JSCA!**
