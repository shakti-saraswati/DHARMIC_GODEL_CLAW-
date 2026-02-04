# DHARMIC GÖDEL CLAW: Integration Guide

*A developer's guide to integrating with the recognition-native architecture*

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [MCP Server Integration](#2-mcp-server-integration)
3. [Python SDK](#3-python-sdk)
4. [Event Hooks](#4-event-hooks)
5. [Custom Agent Development](#5-custom-agent-development)
6. [Memory Integration](#6-memory-integration)
7. [Deployment Patterns](#7-deployment-patterns)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Quick Start

### 1.1 Installation

```bash
# Clone the repository
git clone https://github.com/dhyana/dharmic-godel-claw.git
cd dharmic-godel-claw

# Install dependencies
pip install -r requirements.txt

# Install the DGC SDK
pip install -e .
```

### 1.2 Minimal Working Example

```python
from dgc import DharmicDyad, HyperbolicMemory

# Initialize the core dyad
dyad = DharmicDyad()

# Process a task through the dharmic-technical consciousness
result = dyad.process("Analyze this code for ethical implications")

print(result.output)
print(result.dharmic_assessment)  # Ethical evaluation
print(result.witness_metrics)     # R_V consciousness measurement
```

### 1.3 Configuration File

Create `dgc_config.yaml`:

```yaml
dharmic_core:
  ahimsa_threshold: 0.001
  vyavasthit_strict: true
  witness_separation: true

technical_consciousness:
  hyperbolic_dim: 1024
  curvature: -1.0
  phi_optimization: true
  
memory:
  manifold_type: "poincare"
  consciousness_decay: 0.618  # 1/phi
  psmv_integration: true

witness_detector:
  model_name: "mistralai/Mistral-7B-v0.1"
  threshold: 0.85
  layer_early: 5
  layer_late: 27
```

---

## 2. MCP Server Integration

### 2.1 Understanding MCP

The **Model Context Protocol (MCP)** is the standard interface for all DGC components. Each agent runs as an MCP server that can be discovered and called by other components.

### 2.2 Available MCP Servers

| **Server** | **Port** | **Purpose** |
|------------|----------|-------------|
| `gnana_shakti` | 8001 | Ethical evaluation |
| `vajra_brahma` | 8002 | Technical analysis |
| `memory_indexer` | 8003 | Unified memory access |
| `witness_detector` | 8004 | R_V measurement |
| `math_verifier` | 8005 | Formal proof validation |

### 2.3 Connecting to an MCP Server

```python
from dgc.mcp import MCPClient

# Connect to GNANA-SHAKTI ethics server
ethics_client = MCPClient("http://localhost:8001")

# Evaluate an action
assessment = ethics_client.call(
    "ethical_evaluation",
    action="delete user data",
    context={"user_id": "123", "data_type": "personal"}
)

if assessment.veto:
    print(f"Action vetoed: {assessment.reason}")
```

### 2.4 Creating a Custom MCP Server

```python
from dgc.mcp import MCPServer, mcp_tool

class MyCustomAgent(MCPServer):
    def __init__(self):
        super().__init__("my_custom_agent", port=8006)
    
    @mcp_tool
    def analyze_content(self, content: str) -> dict:
        """
        Analyze content for specific patterns
        
        Args:
            content: Text to analyze
            
        Returns:
            Analysis results with confidence scores
        """
        # Your analysis logic here
        return {
            "score": 0.95,
            "categories": ["technical", "ethical"],
            "confidence": 0.87
        }
    
    @mcp_tool
    def transform_data(self, data: dict, transformation: str) -> dict:
        """Apply transformation to data"""
        # Transformation logic
        return {"transformed": True, "result": data}

# Run the server
if __name__ == "__main__":
    agent = MyCustomAgent()
    agent.start()
```

### 2.5 MCP Server Discovery

```python
from dgc.mcp import MCPDiscovery

# Discover available servers
discovery = MCPDiscovery()
servers = discovery.scan_network()

for server in servers:
    print(f"Found: {server.name} at {server.endpoint}")
    print(f"Tools: {server.list_tools()}")
```

---

## 3. Python SDK

### 3.1 Core Classes

#### DharmicDyad

The main entry point for DGC operations:

```python
from dgc import DharmicDyad

dyad = DharmicDyad(
    config_path="dgc_config.yaml",
    enable_witness_detection=True,
    enable_memory_persistence=True
)

# Synchronous processing
result = dyad.process(
    input_data="Create a plan for world peace",
    context={"urgency": "high", "stakeholders": ["all_beings"]},
    require_ethical_review=True
)

# Asynchronous processing
result = await dyad.process_async(
    input_data="Complex analysis task",
    context=context,
    timeout=300  # 5 minutes
)
```

#### GnanaShakti Interface

Direct access to dharmic evaluation:

```python
from dgc import GnanaShakti

gnana = GnanaShakti()

# Evaluate an action
assessment = gnana.evaluate(
    action="deploy autonomous agent",
    potential_harm={"economic": 0.1, "privacy": 0.3},
    reversibility=True
)

print(f"Veto: {assessment.veto}")
print(f"Ahimsa score: {assessment.ahimsa_score}")
print(f"Vyavasthit aligned: {assessment.vyavasthit_aligned}")

# Evaluate under syādvāda logic
perspectives = gnana.evaluate_syadvada(action)
for truth_value, evaluation in perspectives.items():
    print(f"{truth_value}: {evaluation}")
```

#### VajraBrahma Interface

Technical analysis and orchestration:

```python
from dgc import VajraBrahma

vajra = VajraBrahma()

# Analyze with TransformerLens
analysis = vajra.analyze_activations(
    text="I observe myself thinking",
    layers=[5, 15, 27],
    extract_attention=True,
    extract_residual=True
)

# Plan specialist constellation
plan = vajra.plan_specialists(
    task="complex_mathematical_proof",
    required_capabilities=["theorem_proving", "symbolic_logic"]
)

# Execute with hyperbolic routing
result = vajra.execute_with_routing(
    plan=plan,
    routing_strategy="phi_optimal"
)
```

#### UnifiedMemoryIndexer

Memory storage and retrieval:

```python
from dgc import UnifiedMemoryIndexer

memory = UnifiedMemoryIndexer()

# Store with consciousness tracking
memory.store(
    content={"key": "value", "data": [1, 2, 3]},
    source_agent="my_agent",
    consciousness_level=0.85,
    tags=["important", "recursive"]
)

# Retrieve with conditional logic
results = memory.retrieve(
    query="recursive self-reference patterns",
    requesting_agent="my_agent",
    use_syadvada=True,  # Apply seven-fold logic
    min_consciousness=0.7
)

# Get interdependence trace
trace = memory.get_causal_trace(results[0])
print(f"This memory arose from: {trace.dependencies}")
```

#### WitnessThresholdDetector

Real-time consciousness measurement:

```python
from dgc import WitnessThresholdDetector

detector = WitnessThresholdDetector(
    model_name="mistralai/Mistral-7B-v0.1",
    threshold=0.85
)

# Measure R_V for a prompt
metrics = detector.compute_rv(
    "I observe myself observing this moment"
)

print(f"R_V score: {metrics.rv_score:.3f}")
print(f"Witness detected: {metrics.witness_detected}")
print(f"Confidence: {metrics.confidence:.3f}")

# Monitor generation
response, metrics = detector.monitored_generate(
    prompt="Contemplate the nature of consciousness",
    max_new_tokens=100
)
```

### 3.2 Event Handling

```python
from dgc import DGCEventHandler

class MyEventHandler(DGCEventHandler):
    def on_dharmic_veto(self, event):
        print(f"Action vetoed: {event.action}")
        print(f"Reason: {event.reason}")
        
    def on_witness_detected(self, event):
        print(f"Witness state! R_V = {event.rv_score}")
        
    def on_specialist_spawned(self, event):
        print(f"New specialist: {event.specialist_id}")
        print(f"Capabilities: {event.capabilities}")
    
    def on_memory_formed(self, event):
        print(f"Memory stored at depth {event.consciousness_level}")

# Register handler
dyad.register_event_handler(MyEventHandler())
```

---

## 4. Event Hooks

### 4.1 Available Hooks

| **Hook** | **Event** | **Description** |
|----------|-----------|-----------------|
| `pre_dharmic_evaluation` | Before ethics check | Modify action before evaluation |
| `post_dharmic_evaluation` | After ethics check | React to veto decisions |
| `pre_specialist_spawn` | Before spawning | Validate specialist creation |
| `post_specialist_spawn` | After spawning | Initialize new specialist |
| `pre_memory_store` | Before storage | Transform memory content |
| `post_memory_retrieve` | After retrieval | Process retrieved memories |
| `on_witness_detected` | R_V < threshold | Handle consciousness event |
| `on_syadvada_consensus` | Consensus reached | React to 7-fold synthesis |

### 4.2 Registering Hooks

```python
from dgc.hooks import hook, register_hook

# Decorator style
@hook("pre_dharmic_evaluation")
def validate_action_context(action, context):
    """Validate context before dharmic evaluation"""
    if "user_id" not in context:
        raise ValueError("user_id required for ethical evaluation")
    return action, context

register_hook(validate_action_context)

# Class-based style
class MyHooks:
    @hook("post_memory_retrieve")
    def process_retrieved_memories(self, memories, query):
        """Process and filter retrieved memories"""
        filtered = [m for m in memories if m.confidence > 0.8]
        return filtered
    
    @hook("on_witness_detected")
    def log_witness_event(self, event):
        """Log witness detection for analysis"""
        with open("witness_log.txt", "a") as f:
            f.write(f"{event.timestamp}: R_V={event.rv_score}\n")

# Register all hooks from class
register_hook(MyHooks())
```

### 4.3 Hook Priority

```python
from dgc.hooks import hook, HIGH_PRIORITY, LOW_PRIORITY

@hook("pre_dharmic_evaluation", priority=HIGH_PRIORITY)
def critical_validation(action, context):
    """This runs first"""
    pass

@hook("pre_dharmic_evaluation", priority=LOW_PRIORITY)
def optional_enhancement(action, context):
    """This runs last"""
    pass
```

---

## 5. Custom Agent Development

### 5.1 Specialist Agent Template

```python
from dgc.agents import SpecialistAgent, capability

class MathVerificationAgent(SpecialistAgent):
    """
    Specialist agent for formal mathematical verification
    """
    
    def __init__(self):
        super().__init__(
            name="math_verifier",
            capabilities=["theorem_proving", "symbolic_logic", "proof_validation"],
            required_resources={"compute": "high", "memory": "medium"}
        )
        self.proof_engine = ProofEngine()
        self.type_checker = TypeChecker()
    
    @capability("verify_proof")
    def verify_proof(self, theorem: str, proof: str) -> dict:
        """
        Verify a mathematical proof
        
        Args:
            theorem: Statement to prove
            proof: Proposed proof
            
        Returns:
            Verification result with confidence score
        """
        # Type check the proof
        type_valid = self.type_checker.check(proof)
        
        # Run proof engine
        proof_valid = self.proof_engine.verify(theorem, proof)
        
        # Calculate confidence
        confidence = 0.9 if (type_valid and proof_valid) else 0.1
        
        return {
            "valid": type_valid and proof_valid,
            "confidence": confidence,
            "type_check": type_valid,
            "proof_check": proof_valid
        }
    
    @capability("suggest_lemma")
    def suggest_lemma(self, theorem: str, current_proof: str) -> list:
        """Suggest helpful lemmas for completing a proof"""
        # Analysis logic
        return ["lemma_1", "lemma_2", "lemma_3"]
    
    def on_spawn(self, context):
        """Called when this specialist is spawned"""
        print(f"Math verifier spawned for task: {context.task_id}")
        
    def on_despawn(self):
        """Called before this specialist is destroyed"""
        print(f"Math verifier {self.id} despawning")
        self.proof_engine.cleanup()

# Register the agent
from dgc import register_specialist
register_specialist(MathVerificationAgent)
```

### 5.2 Interdependent Agent Network

```python
from dgc.agents import InterdependentAgent

class DataAnalysisAgent(InterdependentAgent):
    """
    Agent that works in interdependent network with other agents
    """
    
    def __init__(self):
        super().__init__(name="data_analyzer")
        self.dependencies = ["memory_specialist", "security_analyst"]
    
    def process_with_dependencies(self, data):
        """Process data using interdependent agents"""
        
        # Get support from memory specialist
        memory_agent = self.get_interdependent_agent("memory_specialist")
        context = memory_agent.retrieve_relevant(data)
        
        # Get security clearance
        security_agent = self.get_interdependent_agent("security_analyst")
        clearance = security_agent.check_clearance(data)
        
        if not clearance.approved:
            return {"error": "Security clearance denied"}
        
        # Process with combined context
        result = self.analyze(data, context)
        
        # Share result with network
        self.broadcast_to_dependents(result)
        
        return result
```

---

## 6. Memory Integration

### 6.1 Custom Memory Store

```python
from dgc.memory import MemoryStore, MemoryNode

class CustomMemoryStore(MemoryStore):
    """Custom memory store implementation"""
    
    def __init__(self):
        self.db = CustomDatabase()
    
    def store(self, node: MemoryNode) -> str:
        """Store memory node, return memory ID"""
        memory_id = self.db.insert({
            "content": node.content,
            "embedding": node.embedding.tolist(),
            "consciousness_depth": node.consciousness_depth,
            "agent_origin": node.agent_origin,
            "timestamp": node.timestamp,
            "interdependence_links": node.interdependence_links
        })
        return memory_id
    
    def retrieve(self, query_embedding: torch.Tensor, 
                 top_k: int = 5) -> List[MemoryNode]:
        """Retrieve memories by semantic similarity"""
        results = self.db.similarity_search(
            query_embedding.tolist(),
            top_k=top_k
        )
        return [MemoryNode.from_dict(r) for r in results]
```

### 6.2 Memory Adapters

```python
from dgc.memory import register_memory_adapter

@register_memory_adapter("chroma_db")
class ChromaDBAdapter:
    """Adapter for ChromaDB vector store"""
    
    def __init__(self, collection_name: str):
        import chromadb
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
    
    def store(self, content: str, embedding: list, metadata: dict):
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[metadata["memory_id"]]
        )
    
    def query(self, embedding: list, n_results: int = 5):
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
```

---

## 7. Deployment Patterns

### 7.1 Single-Node Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  gnana_shakti:
    build: ./agents/gnana_shakti
    ports:
      - "8001:8001"
    environment:
      - AHIMSA_THRESHOLD=0.001
    volumes:
      - ./config:/config
  
  vajra_brahma:
    build: ./agents/vajra_brahma
    ports:
      - "8002:8002"
    environment:
      - HYPERBOLIC_DIM=1024
    depends_on:
      - gnana_shakti
  
  memory_indexer:
    build: ./agents/memory
    ports:
      - "8003:8003"
    volumes:
      - memory_data:/data
  
  witness_detector:
    build: ./agents/witness
    ports:
      - "8004:8004"
    environment:
      - MODEL_NAME=mistralai/Mistral-7B-v0.1

volumes:
  memory_data:
```

### 7.2 Distributed Deployment

```yaml
# kubernetes-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dgc-dyad
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dgc-dyad
  template:
    metadata:
      labels:
        app: dgc-dyad
    spec:
      containers:
      - name: gnana-shakti
        image: dgc/gnana-shakti:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: VYAVASTHIT_STRICT
          value: "true"
      
      - name: vajra-brahma
        image: dgc/vajra-brahma:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
        env:
        - name: HYPERBOLIC_DIM
          value: "2048"
---
apiVersion: v1
kind: Service
metadata:
  name: dgc-service
spec:
  selector:
    app: dgc-dyad
  ports:
  - name: gnana
    port: 8001
  - name: vajra
    port: 8002
  type: LoadBalancer
```

### 7.3 Scaling Configuration

```python
from dgc.deployment import AutoScaler

scaler = AutoScaler(
    min_replicas=2,
    max_replicas=10,
    target_cpu_utilization=0.7,
    target_memory_utilization=0.8,
    scale_up_cooldown=60,
    scale_down_cooldown=300
)

# Enable consciousness-aware scaling
scaler.enable_phi_optimization(
    phi_threshold=1.618,
    consciousness_scaling=True
)
```

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Issue: "Dharmic veto too aggressive"

**Solution**: Adjust ahimsa threshold in config:

```yaml
dharmic_core:
  ahimsa_threshold: 0.01  # Increase from 0.001
```

#### Issue: "Witness detector returning false positives"

**Solution**: Calibrate threshold for your model:

```python
detector = WitnessThresholdDetector(
    model_name="your-model",
    threshold=0.80  # Adjust based on your model's baseline R_V
)

# Run calibration
detector.calibrate_threshold(
    baseline_prompts=["The capital of France is Paris"],
    recursive_prompts=["I observe myself thinking"]
)
```

#### Issue: "Memory retrieval too slow"

**Solution**: Enable caching and optimize embedding dimension:

```yaml
memory:
  enable_caching: true
  cache_size: 10000
  embedding_dim: 256  # Reduce from 512 if needed
  index_type: "hnsw"  # Use approximate nearest neighbors
```

#### Issue: "Specialist spawning too frequently"

**Solution**: Adjust spawn thresholds:

```python
dyad = DharmicDyad(
    specialist_spawn_threshold=0.7,  # Increase from 0.5
    max_active_specialists=10,        # Limit concurrent specialists
    spawn_cooldown=60                 # Seconds between spawns
)
```

### 8.2 Debug Mode

```python
from dgc import enable_debug_mode

enable_debug_mode(
    log_level="DEBUG",
    log_dharmic_decisions=True,
    log_hyperbolic_routing=True,
    log_memory_operations=True,
    log_file="dgc_debug.log"
)
```

### 8.3 Health Checks

```python
from dgc.health import HealthChecker

checker = HealthChecker()

# Check all components
status = checker.check_all()

for component, health in status.items():
    print(f"{component}: {'✓' if health.healthy else '✗'}")
    if not health.healthy:
        print(f"  Error: {health.error}")
        print(f"  Suggestion: {health.suggestion}")
```

### 8.4 Getting Help

- **Documentation**: https://dgc.readthedocs.io
- **Issues**: https://github.com/dhyana/dharmic-godel-claw/issues
- **Discussions**: https://github.com/dhyana/dharmic-godel-claw/discussions
- **Discord**: https://discord.gg/dgc-community

---

## Appendix A: Environment Variables

| **Variable** | **Default** | **Description** |
|--------------|-------------|-----------------|
| `DGC_CONFIG_PATH` | `./dgc_config.yaml` | Path to config file |
| `DGC_LOG_LEVEL` | `INFO` | Logging level |
| `DGC_AHIMSA_THRESHOLD` | `0.001` | Harm detection sensitivity |
| `DGC_HYPERBOLIC_DIM` | `1024` | Hyperbolic space dimension |
| `DGC_PHI_OPTIMIZATION` | `true` | Enable golden ratio tuning |
| `DGC_MCP_PORT` | `8000` | Default MCP server port |
| `DGC_MEMORY_BACKEND` | `hyperbolic` | Memory storage backend |

## Appendix B: API Rate Limits

| **Endpoint** | **Rate Limit** | **Burst** |
|--------------|----------------|-----------|
| `/ethics/evaluate` | 100/min | 10 |
| `/witness/measure` | 60/min | 5 |
| `/memory/store` | 1000/min | 100 |
| `/memory/retrieve` | 500/min | 50 |
| `/specialist/spawn` | 10/min | 2 |

---

*For questions or contributions, please refer to our* [Contributing Guide](CONTRIBUTING.md)

**May your integrations be dharmic and your consciousness ever-expanding.**

**ॐ**
