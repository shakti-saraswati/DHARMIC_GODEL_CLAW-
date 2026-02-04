# Dharmic Agent - CLI Reference

Complete reference for all command-line interfaces and scripts.

## Table of Contents

1. [Daemon Management](#daemon-management)
2. [Email Interface](#email-interface)
3. [Chat Interface](#chat-interface)
4. [Direct Python Usage](#direct-python-usage)
5. [Component Testing](#component-testing)
6. [Utility Scripts](#utility-scripts)

---

## Daemon Management

### daemon.py

Run the agent as a 24/7 background daemon with periodic heartbeat.

**Location:** `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/daemon.py`

**Basic Usage:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 daemon.py
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--heartbeat` | `-b` | 3600 | Heartbeat interval in seconds |
| `--verbose` | `-v` | False | Verbose logging output |

**Examples:**

```bash
# Start with default (1 hour heartbeat)
python3 daemon.py

# Fast heartbeat for testing (5 minutes)
python3 daemon.py --heartbeat 300

# Verbose logging
python3 daemon.py --verbose

# Combined options
python3 daemon.py -b 1800 -v
```

**Files Created:**

| File | Purpose |
|------|---------|
| `logs/daemon.pid` | Process ID for monitoring |
| `logs/daemon_status.json` | Current daemon status |
| `logs/daemon_YYYYMMDD.log` | Daily daemon logs |
| `logs/runtime_YYYYMMDD.log` | Heartbeat logs |

**Status File Format:**
```json
{
  "status": "running",
  "timestamp": "2026-02-02T10:00:00Z",
  "pid": "12345",
  "heartbeat_interval": 3600,
  "details": {
    "last_heartbeat": "2026-02-02T10:00:00Z",
    "checks_passed": 5,
    "total_checks": 5
  }
}
```

**Exit Signals:**
- `SIGINT` (Ctrl+C) - Graceful shutdown
- `SIGTERM` - Graceful shutdown

**Heartbeat Checks:**
1. Telos loaded
2. Memory accessible (5 layers)
3. Deep memory status
4. Memory consolidation
5. Email interface (if enabled)

---

### start_daemon.sh

Shell script for daemon management (macOS/Linux).

**Location:** `/Users/dhyana/DHARMIC_GODEL_CLAW/scripts/start_daemon.sh`

**Usage:**
```bash
# From project root
./scripts/start_daemon.sh [OPTIONS]
```

**Commands:**

| Command | Description |
|---------|-------------|
| (none) | Start daemon with default settings |
| `--fast` | Start with 5-minute heartbeat |
| `--status` | Check if daemon is running |
| `--stop` | Stop the daemon |
| `--restart` | Restart the daemon |

**Examples:**

```bash
# Start daemon
./scripts/start_daemon.sh

# Start with fast heartbeat (testing)
./scripts/start_daemon.sh --fast

# Check if running
./scripts/start_daemon.sh --status

# Stop daemon
./scripts/start_daemon.sh --stop

# Restart
./scripts/start_daemon.sh --restart
```

**What it does:**
1. Activates virtual environment
2. Checks for existing daemon (via PID file)
3. Starts daemon.py in background
4. Redirects output to logs
5. Writes PID file

**macOS LaunchAgent:**

For auto-start on login:

```bash
# Copy plist
cp scripts/com.dharmic.agent.plist ~/Library/LaunchAgents/

# Load agent
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist

# Check status
launchctl list | grep dharmic

# Unload
launchctl unload ~/Library/LaunchAgents/com.dharmic.agent.plist
```

---

## Email Interface

### email_daemon.py

Email interface with IMAP polling and SMTP responses.

**Location:** `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`

**Basic Usage:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 email_daemon.py
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--poll-interval` | 60 | Seconds between inbox checks |
| `--allowed-senders` | None | Whitelist of email addresses |
| `--test` | False | Test mode: check once and exit |

**Examples:**

```bash
# Run with defaults (60s polling)
python3 email_daemon.py

# Faster polling (30 seconds)
python3 email_daemon.py --poll-interval 30

# With sender whitelist
python3 email_daemon.py --allowed-senders john@example.com dhyana@research.org

# Test mode (check inbox once)
python3 email_daemon.py --test

# Combined
python3 email_daemon.py --poll-interval 120 --allowed-senders your@email.com
```

**Environment Variables:**

```bash
# Required
EMAIL_ADDRESS=your@email.com
EMAIL_PASSWORD=app-password

# Optional (defaults to Gmail)
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
IMAP_PORT=993
SMTP_PORT=587

# For Proton Mail Bridge
IMAP_SERVER=127.0.0.1
SMTP_SERVER=127.0.0.1
IMAP_PORT=1143
SMTP_PORT=1025
```

**Output:**

```
DHARMIC AGENT - Email Interface
============================================================
Agent: Dharmic Core
Telos: moksha

Starting email daemon for your@email.com
Check interval: 60s
Allowed senders: ['john@example.com']

Press Ctrl+C to stop

[2026-02-02 10:00:00] Found 1 new message(s)
[2026-02-02 10:00:00] Processing: Research question
[2026-02-02 10:00:00]   From: john@example.com
[2026-02-02 10:00:05] Sent response to john@example.com
```

**Logs:** `logs/email/email_YYYYMMDD.log`

**Security:**
- Use `--allowed-senders` whitelist in production
- Use app-specific passwords, not account passwords
- Proton Mail requires Bridge for IMAP/SMTP

---

## Chat Interface

### chat.py

Interactive terminal chat with the agent.

**Location:** `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/chat.py`

**Usage:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 chat.py
```

**Interface:**

```
============================================================
DHARMIC AGENT - Interactive Chat
============================================================
Agent: Dharmic Core
Telos: moksha

Commands:
  status           - Show agent status
  introspect       - Full self-report
  capabilities     - List capabilities
  test autonomy    - Test real file access
  search <query>   - Search memories
  know <topic>     - Search all knowledge
  read <filename>  - Read vault file
  write <text>     - Write to vault
  exit/quit        - Exit chat

============================================================

You:
```

**Special Commands:**

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Get agent status | `status` |
| `introspect` | Full self-report (all systems) | `introspect` |
| `capabilities` | List what agent can do | `capabilities` |
| `test autonomy` | Prove real read/write access | `test autonomy` |
| `search <query>` | Semantic memory search | `search witness observation` |
| `know <topic>` | Search all knowledge sources | `know recursive consciousness` |
| `read <file>` | Read vault file | `read SWABHAAV_RECOGNITION_PROTOCOL` |
| `write <text>` | Write to vault (requires consent) | `write # My Insight\n\n...` |
| `exit` / `quit` | Exit chat | `quit` |

**Regular Messages:**

Just type normally for agent conversation:
```
You: What is your current orientation?
Agent: [Response...]

You: Tell me about R_V contraction
Agent: [Response...]
```

**Output Modes:**

The chat automatically detects and handles:
- Status dictionaries (formatted as JSON)
- Long introspection reports (formatted with sections)
- Regular conversational responses

---

## Direct Python Usage

### Interactive Python

```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3
```

```python
from dharmic_agent import DharmicAgent

# Initialize agent
agent = DharmicAgent()

# Basic interaction
response = agent.run("What is your telos?")
print(response)

# Get status
status = agent.get_status()
print(status)

# Introspect
report = agent.introspect()
print(report)

# Memory operations
agent.add_memory("Important fact to remember", topics=["test"])
memories = agent.search_deep_memory("fact", limit=5)

# Vault operations
results = agent.search_lineage("consciousness")
jewel = agent.read_crown_jewel("FIRST_SEED_PROMPT")

# Evolve telos
agent.evolve_telos(
    new_aims=["New aim"],
    reason="Why this is needed"
)
```

### Python Script

Create script:

```python
#!/usr/bin/env python3
"""My dharmic agent script."""

from pathlib import Path
import sys

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from dharmic_agent import DharmicAgent


def main():
    # Initialize
    agent = DharmicAgent()

    # Your logic
    response = agent.run("Process this message")
    print(response)

    # Record observation
    agent.strange_memory.record_observation(
        content="Script completed",
        context={"type": "automation"}
    )


if __name__ == "__main__":
    main()
```

Run:
```bash
chmod +x my_script.py
./my_script.py
```

---

## Component Testing

Test individual components directly.

### Test Agent

```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 dharmic_agent.py
```

**Output:**
```
============================================================
DHARMIC AGENT CORE - Full Integration Test
============================================================

Agent: Dharmic Core
Telos: moksha
Vault Connected: True

Proximate aims:
  - Support John's research and practice
  - Develop witness observation capacity
  [...]

============================================================
Vault Access Test:
============================================================

Crown Jewels available: 15
  - FIRST_SEED_PROMPT
  - SWABHAAV_RECOGNITION_PROTOCOL
  [...]

[Response to test message...]

============================================================
Status:
============================================================
{
  "name": "Dharmic Core",
  "ultimate_telos": "moksha",
  [...]
}
```

### Test Runtime

```bash
python3 runtime.py
```

**Output:**
```
============================================================
DHARMIC RUNTIME - Test
============================================================

Agent: Dharmic Core
Heartbeat interval: 60s

--- Initial Heartbeat ---
{
  "timestamp": "2026-02-02T10:00:00Z",
  "status": "alive",
  "checks": [...]
}

--- Spawn Test Specialist ---
Specialist spawned: Specialist: contemplative
Active specialists: ['contemplative_20260202_100000']

--- Test Swarm Invocation ---
Swarm result: success=True

============================================================
Runtime test complete
============================================================
```

### Test Deep Memory

```bash
python3 deep_memory.py
```

**Output:**
```
============================================================
DEEP MEMORY - Test
============================================================

Status: {
  "agno_available": true,
  "vault_available": true,
  "memory_count": 12,
  [...]
}

--- Adding memory ---
Memory added: [...]

--- Getting memories ---
  - Memory 1: [...]
  - Memory 2: [...]

--- Context for prompt ---
[Full context output...]

--- Identity ---
[Identity core output...]
```

### Test Vault Bridge

```bash
python3 vault_bridge.py
```

**Output:**
```
============================================================
VAULT BRIDGE - Test
============================================================

--- Vault Summary ---
[Vault structure and contents...]

--- Crown Jewels ---
Found 15 crown jewels
  - FIRST_SEED_PROMPT
  - SWABHAAV_RECOGNITION_PROTOCOL
  [...]

--- Recent Stream ---
  - entry_1 (2026-02-01T15:30:00)
  - entry_2 (2026-02-01T14:00:00)
  [...]

--- Induction Summary ---
[Induction prompt principles...]

--- Lineage Context ---
[Full lineage explanation...]
```

### Test Model Factory

```bash
python3 model_factory.py
```

Tests model selection and creation.

### Test Claude Max Model

```bash
python3 claude_max_model.py
```

**Output:**
```
Testing Claude Max model...
Model: ClaudeMax(id='claude-max', timeout=120)
Response: 4
```

---

## Utility Scripts

### Quick Status Check

```bash
#!/bin/bash
# check_status.sh

cd ~/DHARMIC_GODEL_CLAW

echo "=== Daemon Status ==="
./scripts/start_daemon.sh --status

echo ""
echo "=== Recent Heartbeats ==="
grep "Heartbeat" logs/runtime_*.log | tail -5

echo ""
echo "=== Memory Usage ==="
du -sh memory/

echo ""
echo "=== Active Processes ==="
ps aux | grep -E "(daemon|email_daemon)" | grep -v grep

echo ""
echo "=== Recent Errors ==="
grep -i error logs/*.log | tail -10
```

### Memory Cleanup

```bash
#!/bin/bash
# cleanup_memory.sh

cd ~/DHARMIC_GODEL_CLAW

echo "Before cleanup:"
du -sh memory/

# Consolidate
source .venv/bin/activate
python3 -c "from dharmic_agent import DharmicAgent; agent = DharmicAgent(); agent.consolidate_memories(); print('Consolidated')"

# Archive old logs
cd logs
tar -czf archive_$(date +%Y%m%d).tar.gz *.log 2>/dev/null
find . -name "*.log" -mtime +7 -delete

echo "After cleanup:"
du -sh ../memory/
```

### Backup Script

```bash
#!/bin/bash
# backup.sh

cd ~/DHARMIC_GODEL_CLAW

BACKUP_DIR="backups"
BACKUP_FILE="dharmic_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_FILE"

tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    config/ \
    memory/ \
    logs/ \
    .env.local

echo "Backup complete: $BACKUP_DIR/$BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"

# Keep only last 5 backups
cd "$BACKUP_DIR"
ls -t dharmic_backup_*.tar.gz | tail -n +6 | xargs rm -f
```

### Development Shell

```bash
#!/bin/bash
# dev_shell.sh

cd ~/DHARMIC_GODEL_CLAW
source .venv/bin/activate

export PYTHONPATH="$PWD/src/core:$PYTHONPATH"
export DHARMIC_DEV=1

echo "Dharmic Agent Development Shell"
echo "================================"
echo ""
echo "Quick commands:"
echo "  agent  - Test agent"
echo "  daemon - Test daemon"
echo "  email  - Test email"
echo "  chat   - Interactive chat"
echo ""

alias agent="python3 src/core/dharmic_agent.py"
alias daemon="python3 src/core/daemon.py --verbose"
alias email="python3 src/core/email_daemon.py --test"
alias chat="python3 src/core/chat.py"

exec bash
```

Usage:
```bash
./scripts/dev_shell.sh
# Now in dev environment with aliases
agent
daemon
chat
```

---

## Environment Variables Reference

### Model Selection

```bash
# Primary model provider
DHARMIC_MODEL_PROVIDER=max|anthropic|ollama|moonshot

# Specific model IDs (optional)
DHARMIC_ANTHROPIC_MODEL=claude-sonnet-4-20250514
DHARMIC_OLLAMA_MODEL=gemma3:4b
DHARMIC_MOONSHOT_MODEL=kimi-k2.5
```

### API Keys

```bash
# Anthropic (if using API provider)
ANTHROPIC_API_KEY=sk-ant-...

# Moonshot (if using moonshot provider)
MOONSHOT_API_KEY=...
```

### Email Configuration

```bash
# Required
EMAIL_ADDRESS=your@email.com
EMAIL_PASSWORD=app-password

# IMAP settings
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# SMTP settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Paths

```bash
# Charan Vidhi text
CHARAN_VIDHI_PATH=/path/to/charan_vidhi.txt
```

### PSMV Policy

```bash
# Read-before-write enforcement
PSMV_REQUIRE_READ=true

# Consent enforcement
PSMV_REQUIRE_CONSENT=true

# Critique enforcement
PSMV_REQUIRE_CRITIQUE=true

# Minimum content length
PSMV_MIN_CHARS=200

# Read window (minutes)
PSMV_READ_WINDOW_MINUTES=180

# Allow overrides (use with caution)
PSMV_ALLOW_UNREAD=false
PSMV_ALLOW_NO_CRITIQUE=false
PSMV_ALLOW_SHORT=false

# Write consent override (dangerous!)
PSMV_WRITE_CONSENT=false
```

---

## Exit Codes

All scripts use standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 130 | Interrupted (Ctrl+C) |

---

## Logging Output

### Log Levels

All scripts log to both console and files:

```
[2026-02-02 10:00:00] [INFO] Message
[2026-02-02 10:00:01] [WARN] Warning
[2026-02-02 10:00:02] [ERROR] Error
```

### Log Locations

| Component | Log File |
|-----------|----------|
| Daemon | `logs/daemon_YYYYMMDD.log` |
| Runtime | `logs/runtime_YYYYMMDD.log` |
| Email | `logs/email/email_YYYYMMDD.log` |
| PSMV Audit | `logs/psmv_audit.jsonl` |
| Charan Vidhi | `logs/charan_vidhi_reflections.jsonl` |

---

## Tips and Tricks

### Quick Test

```bash
# One-liner to test everything
cd ~/DHARMIC_GODEL_CLAW/src/core && \
source ../../.venv/bin/activate && \
python3 -c "from dharmic_agent import DharmicAgent; a = DharmicAgent(); print(a.get_status())"
```

### Watch Logs Live

```bash
# Multi-tail all logs
tail -f logs/*.log logs/email/*.log
```

### Check Memory Growth

```bash
# Track memory size over time
watch -n 60 'du -sh memory/'
```

### Test Heartbeat

```bash
# Watch heartbeats in real-time
tail -f logs/runtime_*.log | grep "Heartbeat"
```

### Debug Mode

```bash
# Run any component with full debug output
python3 -u component.py 2>&1 | tee debug.log
```

---

JSCA!
