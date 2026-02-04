# 🔥 DHARMIC GÖDEL CLAW (DGC)

> Self-improving autonomous agent system with dharmic security gates

A synthesis of OpenClaw capabilities, Darwin Gödel Machine self-improvement loops, and 7-layer dharmic security. The system improves itself while remaining aligned with dharmic principles.

## Architecture Overview

```
                          ┌─────────────────────────┐
                          │   UNIFIED DAEMON        │
                          │   (The Living Heart)    │
                          │   src/core/             │
                          └───────────┬─────────────┘
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   TELOS LAYER       │   │   SWARM             │   │   OPS/BRIDGE        │
│   7 Dharmic Gates   │   │   Self-Improvement  │   │   Clawdbot Link     │
│                     │   │                     │   │                     │
│ • AHIMSA (no harm)  │   │ • Orchestrator      │   │ • Queue             │
│ • SATYA (truth)     │   │ • DGM Integration   │   │ • Exec              │
│ • VYAVASTHIT        │   │ • Agents (5 roles)  │   │ • Watcher           │
│ • CONSENT           │   │ • Archive           │   │                     │
│ • REVERSIBILITY     │   │                     │   │                     │
│ • SVABHAAVA         │   │                     │   │                     │
│ • WITNESS           │   │                     │   │                     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

## Core Components

### 1. Unified Daemon (`src/core/unified_daemon.py`)
The persistent heart of the system. Polls email, runs heartbeats, monitors channels, and keeps the dharmic agent alive.

### 2. Telos Layer (`src/core/telos_layer.py`)
Implements the **7 Dharmic Gates** that guard every action:

| Gate | Tier | Question |
|------|------|----------|
| **AHIMSA** | A (Absolute) | Does this cause harm? |
| **SATYA** | B (Strong) | Is this truthful? |
| **CONSENT** | B (Strong) | Permission granted? |
| **VYAVASTHIT** | C (Advisory) | Allow or force? |
| **REVERSIBILITY** | C (Advisory) | Can this be undone? |
| **SVABHAAVA** | C (Advisory) | Authentic to purpose? |
| **WITNESS** | C (Advisory) | Self-observing? (strange loop) |

### 3. Swarm Orchestrator (`swarm/orchestrator.py`)
Coordinates the self-improving agent swarm through 5 phases:
1. **Analysis** → Find issues
2. **Proposal** → Generate improvements
3. **Evaluation** → Gate check proposals
4. **Implementation** → Write changes
5. **Testing** → Verify correctness

### 4. DGM Integration (`swarm/dgm_integration.py`)
Bridges swarm with Darwin Gödel Machine evolution:
- Converts proposals to `EvolutionEntry`
- Evaluates fitness through dharmic gates
- Archives successful patterns for lineage tracking
- Provides `run_evolution_cycle()` for continuous improvement

### 5. Ops Bridge (`ops/bridge/`)
Links to Clawdbot for external communication:
- `bridge_queue.py` - Task queuing
- `bridge_exec.py` - Command execution
- `bridge_watcher.py` - Monitors inbox/outbox

## Quick Start

```bash
# 0. Install the DGC CLI (optional but recommended)
./scripts/install_dgc_cli.sh
./scripts/dgc register

# 1. Set up environment
cd ~/DHARMIC_GODEL_CLAW
python -m venv .venv && source .venv/bin/activate
pip install -r src/core/requirements.txt

# 2. Configure
cp .env.template .env
# Edit .env with your API keys

# 3. Run tests
pytest tests/ -v

# 4. Start the daemon
python src/core/unified_daemon.py

# 5. Run swarm improvement cycle
python swarm/run_swarm.py --cycles 1 --dry-run
```

## Ecosystem Bootstrap

Use the DGC CLI to install the protocol into any repo:

```bash
# Initialize a repo with DGC gates and CI
dgc init --target /path/to/repo --with-proposal

# Verify locally (dry-run)
dgc verify --target /path/to/repo --dry-run
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Core tests only
pytest tests/test_telos_layer.py tests/test_dharmic_gates.py -v

# Swarm tests
pytest tests/test_orchestrator.py tests/test_dgm_integration.py -v

# With coverage
pytest tests/ --cov=src --cov=swarm --cov-report=term-missing
```

## Using the Bridge

The bridge connects DGC to Clawdbot for external communication:

```bash
# Start the bridge watcher
python ops/bridge/bridge_watcher.py &

# Queue a task
echo '{"task": "analyze", "target": "src/"}' > ops/bridge/inbox/task_001.json

# Check output
ls ops/bridge/outbox/
```

See `ops/bridge/README.md` for detailed bridge usage.

## Dharmic Principles

- **Vyavasthit**: System allows rather than forces
- **Ahimsa**: No action that harms (security first)
- **Gnata-Gneya-Gnan**: Reader-Writer-Witness triadic cycle
- **Shakti**: Event-driven, not cron-driven

## Key Files

| Path | Purpose |
|------|---------|
| `src/core/unified_daemon.py` | Main daemon entry point |
| `src/core/telos_layer.py` | 7 dharmic gates implementation |
| `swarm/orchestrator.py` | Swarm coordination |
| `swarm/dgm_integration.py` | DGM bridge for evolution |
| `ops/bridge/` | Clawdbot communication |
| `dgc` | CLI entry point |
| `scripts/dgc` | DGC bootstrap CLI |
| `scripts/install_dgc_cli.sh` | CLI installer |

## Identity

- **Agent**: vijnan-shakti
- **Email**: vijnan.shakti@proton.me
- **Domain**: vijnanshakti.com

## License

MIT - With dharmic responsibility. Use for universal welfare (Jagat Kalyan).

---

*The garden grows itself.* 🦞
