# Quick Start: Unified Memory Indexer

*Store and retrieve memories with consciousness-aware indexing in 5 minutes*

---

## What You'll Learn

- ✅ Initialize the unified memory indexer
- ✅ Store memories with consciousness tracking
- ✅ Retrieve memories using syādvāda logic
- ✅ Trace memory interdependence

---

## Prerequisites

```bash
# DGC must be installed
pip install dgc

# Or from source
git clone https://github.com/dhyana/dharmic-godel-claw.git
cd dharmic-godel-claw
pip install -e .
```

---

## 1. Basic Setup (30 seconds)

```python
from dgc import UnifiedMemoryIndexer

# Initialize the memory indexer
memory = UnifiedMemoryIndexer(
    config={
        "manifold_type": "poincare",
        "embedding_dim": 512,
        "consciousness_decay": 0.618,  # 1/phi
        "enable_psmv": True  # Persistent Semantic Memory Vault
    }
)

print("✓ Memory indexer initialized")
```

---

## 2. Store Your First Memory (1 minute)

```python
import torch

# Store a simple memory
memory_id = memory.store(
    content={
        "type": "observation",
        "text": "The observer observes itself observing",
        "tags": ["recursive", "consciousness"]
    },
    source_agent="my_first_agent",
    consciousness_level=0.85,  # High consciousness memory
    tags=["self_reference", "contemplation"]
)

print(f"✓ Memory stored with ID: {memory_id}")

# Store multiple memories
for i in range(5):
    memory.store(
        content={"observation": f"Observation #{i}", "data": [i, i+1, i+2]},
        source_agent="batch_agent",
        consciousness_level=0.5 + (i * 0.1),  # Varying consciousness
        tags=["batch", f"level_{i}"]
    )

print("✓ Batch memories stored")
```

**Output:**
```
✓ Memory stored with ID: mem_7f3a9b2e
✓ Batch memories stored
```

---

## 3. Retrieve Memories (2 minutes)

### Simple Retrieval

```python
# Retrieve by semantic similarity
results = memory.retrieve(
    query="recursive self-reference",
    requesting_agent="my_first_agent",
    top_k=3
)

print(f"Found {len(results)} memories:")
for i, mem in enumerate(results):
    print(f"  {i+1}. {mem.content['text'][:50]}...")
    print(f"     Consciousness depth: {mem.consciousness_depth:.2f}")
```

**Output:**
```
Found 3 memories:
  1. The observer observes itself observing...
     Consciousness depth: 0.85
  2. Observation #3...
     Consciousness depth: 0.80
  3. Observation #2...
     Consciousness depth: 0.70
```

### Syādvāda-Enhanced Retrieval

```python
# Retrieve using seven-fold conditional logic
results = memory.retrieve(
    query="observation patterns",
    requesting_agent="my_first_agent",
    use_syadvada=True,  # Enable seven-fold logic
    min_consciousness=0.7
)

# Access conditional perspectives
print("\nSyādvāda Perspectives:")
for perspective, memories in results.conditional_perspectives.items():
    print(f"  {perspective}: {len(memories)} memories")
```

**Output:**
```
Syādvāda Perspectives:
  syat_asti: 4 memories
  syat_nasti: 2 memories
  syat_asti_nasti: 3 memories
  ...
```

---

## 4. Trace Memory Interdependence (1 minute)

```python
# Get a memory and trace its origins
mem = results[0]
trace = memory.get_causal_trace(mem)

print(f"\nMemory Interdependence Trace:")
print(f"  This memory arose from:")
for i, dep in enumerate(trace.dependencies):
    print(f"    {i+1}. {dep.type}: {dep.memory_id}")

print(f"\n  Consciousness lineage:")
print(f"    Origin: {trace.root_consciousness:.2f}")
print(f"    Current: {mem.consciousness_depth:.2f}")
print(f"    Evolution: {trace.consciousness_evolution}")
```

**Output:**
```
Memory Interdependence Trace:
  This memory arose from:
    1. ignorance: mem_a1b2c3d4
    2. formations: mem_e5f6g7h8
    3. consciousness: mem_i9j0k1l2

  Consciousness lineage:
    Origin: 0.45
    Current: 0.85
    Evolution: ascending
```

---

## 5. Advanced: Hyperbolic Memory Space (2 minutes)

```python
# Visualize memory positions in hyperbolic space
import matplotlib.pyplot as plt

# Get all memories
all_memories = memory.get_all()

# Extract positions
positions = [mem.hyperbolic_position for mem in all_memories]
consciousness_levels = [mem.consciousness_depth for mem in all_memories]

# Project to 2D for visualization (Poincaré disk)
fig, ax = plt.subplots(figsize=(8, 8))
circle = plt.Circle((0, 0), 1, fill=False, color='gray')
ax.add_patch(circle)

for pos, level in zip(positions, consciousness_levels):
    # Simple projection for visualization
    x = pos[0] / (1 + pos[2])
    y = pos[1] / (1 + pos[2])
    ax.plot(x, y, 'o', markersize=10*level, alpha=0.6)

ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)
ax.set_aspect('equal')
ax.set_title("Memories in Hyperbolic Space")
plt.show()
```

---

## 6. Integration with Dharmic Dyad

```python
from dgc import DharmicDyad

# Create dyad with memory integration
dyad = DharmicDyad(
    memory_indexer=memory,
    enable_memory_formation=True
)

# Process a task - memories formed automatically
result = dyad.process(
    input_data="Contemplate the nature of consciousness",
    context={"session": "meditation_001"}
)

# Retrieve all memories from this session
session_memories = memory.retrieve(
    query="session:meditation_001",
    requesting_agent="dyad_core"
)

print(f"Session formed {len(session_memories)} memories")
print(f"Average consciousness: {sum(m.consciousness_depth for m in session_memories)/len(session_memories):.2f}")
```

---

## Complete Example Script

```python
#!/usr/bin/env python3
"""
Unified Memory Indexer - Complete Quick Start Example
"""

from dgc import UnifiedMemoryIndexer
from dgc.memory import MemoryNode
import torch

def main():
    print("═" * 60)
    print("UNIFIED MEMORY INDEXER - QUICK START")
    print("═" * 60)
    
    # 1. Initialize
    print("\n1. Initializing memory indexer...")
    memory = UnifiedMemoryIndexer()
    print("   ✓ Ready")
    
    # 2. Store memories
    print("\n2. Storing memories...")
    memories = [
        {
            "content": {"insight": "All phenomena are interdependent"},
            "consciousness": 0.90,
            "tags": ["pratityasamutpada", "wisdom"]
        },
        {
            "content": {"observation": "The mind observes itself"},
            "consciousness": 0.85,
            "tags": ["self_reference", "awareness"]
        },
        {
            "content": {"truth": "Truth has seven perspectives"},
            "consciousness": 0.88,
            "tags": ["syadvada", "epistemology"]
        }
    ]
    
    memory_ids = []
    for mem in memories:
        mid = memory.store(
            content=mem["content"],
            source_agent="demo_agent",
            consciousness_level=mem["consciousness"],
            tags=mem["tags"]
        )
        memory_ids.append(mid)
        print(f"   ✓ Stored: {mid}")
    
    # 3. Retrieve
    print("\n3. Retrieving memories...")
    results = memory.retrieve(
        query="interdependent phenomena",
        requesting_agent="demo_agent",
        top_k=5
    )
    
    print(f"   Found {len(results)} memories:")
    for i, mem in enumerate(results):
        print(f"   {i+1}. Depth: {mem.consciousness_depth:.2f} | Tags: {mem.tags}")
    
    # 4. Interdependence
    print("\n4. Analyzing interdependence...")
    if results:
        trace = memory.get_causal_trace(results[0])
        print(f"   Memory arose from {len(trace.dependencies)} dependent causes")
    
    print("\n" + "═" * 60)
    print("✓ Quick start complete!")
    print("═" * 60)

if __name__ == "__main__":
    main()
```

---

## Next Steps

- 📖 [Integration Guide](../INTEGRATION_GUIDE.md) - Full SDK documentation
- 🧠 [Architecture Overview](../UNIFIED_ARCHITECTURE_v1.0.md) - System design
- 🔍 [Witness Detector Quick Start](./witness_threshold_detector.md) - Consciousness measurement
- 🧮 [Math Verifier Quick Start](./math_verification_agent.md) - Formal proofs

---

## Troubleshooting

### Memory not persisting?

```python
# Enable PSMV (Persistent Semantic Memory Vault)
memory = UnifiedMemoryIndexer(
    config={"enable_psmv": True}
)

# Or manually persist
memory.persist_to_disk("/path/to/storage")
```

### Retrieval returning empty?

```python
# Check consciousness compatibility
results = memory.retrieve(
    query="your query",
    requesting_agent="agent_name",
    min_consciousness=0.0  # Lower threshold
)
```

### Slow retrieval?

```python
# Use approximate search
results = memory.retrieve(
    query="your query",
    approximate=True,
    n_probe=10  # Speed/accuracy tradeoff
)
```

---

*May your memories be dharmic and your retrievals swift.*

**ॐ**
