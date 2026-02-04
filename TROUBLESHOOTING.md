# Dharmic Agent - Troubleshooting Guide

Common issues and solutions for the Dharmic Agent system.

## Quick Diagnostic

Run this to check system health:

```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate

# Test each component
echo "Testing agent..."
python3 -c "from dharmic_agent import DharmicAgent; print('✓ Agent OK')"

echo "Testing telos..."
python3 -c "from dharmic_agent import TelosLayer; t = TelosLayer(); print('✓ Telos OK')"

echo "Testing memory..."
python3 -c "from dharmic_agent import StrangeLoopMemory; m = StrangeLoopMemory(); print('✓ Memory OK')"

echo "Testing deep memory..."
python3 -c "from deep_memory import DeepMemory; print('✓ Deep Memory OK')"

echo "Testing vault..."
python3 -c "from vault_bridge import VaultBridge; print('✓ Vault OK')"

echo "Testing model factory..."
python3 -c "from model_factory import resolve_model_spec; print('✓ Model Factory OK')"
```

---

## Installation Issues

### ImportError: No module named 'agno'

**Symptom:**
```
ImportError: No module named 'agno'
```

**Cause:** Agno framework not installed.

**Solution:**
```bash
cd ~/DHARMIC_GODEL_CLAW/cloned_source/agno
source ../../.venv/bin/activate
pip install -e .
cd ../..
```

**Verify:**
```bash
python3 -c "import agno; print(agno.__version__)"
```

---

### ImportError: No module named 'anthropic'

**Symptom:**
```
ImportError: No module named 'anthropic'
```

**Cause:** Anthropic SDK not installed.

**Solution:**
```bash
source .venv/bin/activate
pip install anthropic
```

**Alternative:** Use Claude Max or Ollama provider:
```bash
export DHARMIC_MODEL_PROVIDER=max
# or
export DHARMIC_MODEL_PROVIDER=ollama
```

---

### Virtual environment not activating

**Symptom:**
```
bash: .venv/bin/activate: No such file or directory
```

**Cause:** Virtual environment doesn't exist.

**Solution:**
```bash
cd ~/DHARMIC_GODEL_CLAW
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Verify:**
```bash
which python3
# Should show: ~/DHARMIC_GODEL_CLAW/.venv/bin/python3
```

---

## Configuration Issues

### Telos file not found

**Symptom:**
```
FileNotFoundError: Telos file not found: .../config/telos.yaml
```

**Cause:** Telos configuration missing or wrong path.

**Solution:**
```bash
# Check if file exists
ls ~/DHARMIC_GODEL_CLAW/config/telos.yaml

# If missing, check for backup
ls ~/DHARMIC_GODEL_CLAW/config/*.yaml

# If no backup, create from template (example in DAEMON_README.md)
```

**Verify:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
python3 -c "from dharmic_agent import TelosLayer; t = TelosLayer(); print(t.telos['ultimate']['aim'])"
# Should print: moksha
```

---

### Environment variables not loaded

**Symptom:**
```
ValueError: EMAIL_ADDRESS and EMAIL_PASSWORD must be set
```

**Cause:** `.env.local` not loaded or doesn't exist.

**Solution:**
```bash
# Create .env.local if missing
cd ~/DHARMIC_GODEL_CLAW
cp .env.example .env.local

# Edit with your credentials
nano .env.local

# Verify loading
source .env.local
env | grep EMAIL
```

**Alternative:** Set directly:
```bash
export EMAIL_ADDRESS=your@email.com
export EMAIL_PASSWORD=your-password
```

---

### API key issues

**Symptom:**
```
AuthenticationError: Invalid API key
```

**Cause:** Missing or incorrect API key.

**Solution:**
```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Set if missing
export ANTHROPIC_API_KEY=sk-ant-...

# Add to .env.local for persistence
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env.local
```

**Alternative:** Use Claude Max (no API key needed):
```bash
export DHARMIC_MODEL_PROVIDER=max
npm install -g @anthropic-ai/claude-code
```

---

## Agent Runtime Issues

### Agent initialization fails

**Symptom:**
```python
agent = DharmicAgent()
# Fails with various errors
```

**Diagnosis:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
python3 dharmic_agent.py
# Check full error traceback
```

**Common causes and fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: telos.yaml` | Missing config | Create config/telos.yaml |
| `ImportError: agno` | Agno not installed | `cd cloned_source/agno && pip install -e .` |
| `RuntimeError: model_factory not available` | Missing dependency | `pip install anthropic` or set provider=max |
| `PermissionError: memory/` | Directory permissions | `chmod -R 755 memory/` |

---

### Model timeout

**Symptom:**
```
RuntimeError: Claude CLI timeout after 120s
```

**Cause:** Model taking too long to respond.

**Solution:**
```python
# Increase timeout
agent = DharmicAgent(model_id="claude-max")
agent._timeout = 300  # 5 minutes

# Or in claude_max_model.py
model = ClaudeMax(timeout=300)
```

**Alternative:** Switch to API provider (usually faster):
```bash
export DHARMIC_MODEL_PROVIDER=anthropic
```

---

### Strange loop memory errors

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'memory/observations.jsonl'
```

**Cause:** File permissions issue.

**Solution:**
```bash
cd ~/DHARMIC_GODEL_CLAW
chmod -R 755 memory/
```

**If file corrupted:**
```bash
# Backup corrupted file
cp memory/observations.jsonl memory/observations.jsonl.bak

# Remove and let system recreate
rm memory/observations.jsonl

# Restart agent
cd src/core
python3 dharmic_agent.py
```

---

## Deep Memory Issues

### Database locked

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing same database.

**Solution:**
```bash
# Check for running processes
ps aux | grep dharmic
ps aux | grep daemon

# Kill stale processes
killall python3  # or specific PID

# Remove stale locks
rm ~/DHARMIC_GODEL_CLAW/memory/*.db-shm
rm ~/DHARMIC_GODEL_CLAW/memory/*.db-wal
```

---

### Memory consolidation fails

**Symptom:**
```
Error consolidating memories: ...
```

**Diagnosis:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 deep_memory.py
# Check full error output
```

**Common fixes:**

1. **Database corruption:**
```bash
# Backup and reinitialize
cp memory/deep_memory.db memory/deep_memory.db.bak
rm memory/deep_memory.db
python3 dharmic_agent.py
```

2. **Out of disk space:**
```bash
df -h ~/DHARMIC_GODEL_CLAW/
# Free up space if needed
```

3. **Permission issues:**
```bash
chmod 644 memory/deep_memory.db
```

---

## Vault Integration Issues

### Vault not connecting

**Symptom:**
```
Note: VaultBridge not available. Running without vault context.
```

**Cause:** Vault path doesn't exist (this is actually OK - vault is optional).

**If you want vault:**
```bash
# Check if vault exists
ls ~/Persistent-Semantic-Memory-Vault/

# If not, vault integration is optional
# Agent works fine without it
```

**Force vault path:**
```python
agent = DharmicAgent(
    vault_path="~/your/custom/vault/path"
)
```

---

### Vault write rejected

**Symptom:**
```python
path = agent.write_to_lineage(content, filename)
# Returns None
```

**Diagnosis:** Check policy violations.

**Common reasons:**

| Reason | Check | Fix |
|--------|-------|-----|
| No consent | `consent=False` | Set `consent=True` |
| No critique | `critique=None` | Provide critique string |
| Haven't read recently | No recent vault reads | Read files first |
| Content too short | `len(content) < 200` | Write more meaningful content |
| Ahimsa violation | Contains harmful words | Remove harmful patterns |

**Debug:**
```bash
# Check audit log
cat ~/DHARMIC_GODEL_CLAW/logs/psmv_audit.jsonl | tail -20
```

---

### Read-before-write stale

**Symptom:**
```
Policy violation: read_before_write_stale
```

**Cause:** Last vault read was more than 3 hours ago.

**Solution:**
```python
# Read something from vault first
jewels = agent.vault.list_crown_jewels()
content = agent.read_crown_jewel(jewels[0])

# Now write within 3-hour window
path = agent.write_to_lineage(
    content="...",
    filename="file.md",
    consent=True,
    critique="..."
)
```

---

## Daemon Issues

### Daemon won't start

**Symptom:**
```bash
./scripts/start_daemon.sh
# No output or error
```

**Diagnosis:**
```bash
# Check logs
tail -50 ~/DHARMIC_GODEL_CLAW/logs/daemon_*.log

# Try running directly
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate
python3 daemon.py --verbose
```

**Common causes:**

1. **Stale PID file:**
```bash
rm ~/DHARMIC_GODEL_CLAW/logs/daemon.pid
./scripts/start_daemon.sh
```

2. **Virtual env not activated:**
```bash
# Edit start_daemon.sh to activate venv
source /Users/dhyana/DHARMIC_GODEL_CLAW/.venv/bin/activate
```

3. **Python path issues:**
```bash
which python3
# Should be in .venv/bin/
```

---

### Heartbeat not running

**Symptom:** Daemon running but no heartbeat logs.

**Diagnosis:**
```bash
# Check heartbeat interval
cat ~/DHARMIC_GODEL_CLAW/logs/daemon_status.json

# Check runtime logs
tail -f ~/DHARMIC_GODEL_CLAW/logs/runtime_*.log
```

**Solution:**
```bash
# Restart with faster heartbeat for testing
cd ~/DHARMIC_GODEL_CLAW/src/core
python3 daemon.py --heartbeat 300 --verbose
# Should see heartbeat every 5 minutes
```

---

### Daemon zombie process

**Symptom:** Daemon shows as running but not responding.

**Solution:**
```bash
# Find process
ps aux | grep daemon.py

# Kill process
kill -9 <PID>

# Remove stale files
rm ~/DHARMIC_GODEL_CLAW/logs/daemon.pid
rm ~/DHARMIC_GODEL_CLAW/logs/daemon_status.json

# Restart
./scripts/start_daemon.sh
```

---

## Email Interface Issues

### Email authentication failed

**Symptom:**
```
Error: Email authentication failed
```

**Gmail users:**
```bash
# Use App Password, not account password
# 1. Enable 2FA in Google Account
# 2. Security > App Passwords
# 3. Generate for "Mail"
# 4. Use that 16-character password

export EMAIL_PASSWORD=abcd-efgh-ijkl-mnop
```

**Proton Mail users:**
```bash
# Must use Proton Bridge
# 1. Install Proton Mail Bridge
# 2. Start Bridge
# 3. Get credentials from Bridge settings
# 4. Use localhost connection

export IMAP_SERVER=127.0.0.1
export IMAP_PORT=1143
export SMTP_SERVER=127.0.0.1
export SMTP_PORT=1025
```

---

### Email not polling

**Symptom:** Email daemon runs but doesn't check inbox.

**Diagnosis:**
```bash
cd ~/DHARMIC_GODEL_CLAW/src/core
source ../../.venv/bin/activate

# Test mode
python3 email_daemon.py --test
# Should show unread count
```

**Common fixes:**

1. **Credentials wrong:**
```bash
python3 email_daemon.py --test
# Will show authentication error if wrong
```

2. **Proton Bridge not running:**
```bash
ps aux | grep protonmail-bridge
# If not running, start Bridge app
```

3. **Firewall blocking:**
```bash
# Check if ports accessible
telnet 127.0.0.1 1143  # For Proton
telnet imap.gmail.com 993  # For Gmail
```

---

### Email responses not sending

**Symptom:** Receives emails but doesn't respond.

**Check logs:**
```bash
tail -f ~/DHARMIC_GODEL_CLAW/logs/email/email_*.log
```

**Common causes:**

1. **SMTP authentication failed:**
```bash
# Same password for SMTP as IMAP
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
```

2. **Whitelist blocking:**
```bash
# If whitelist configured, sender must be listed
python3 email_daemon.py --allowed-senders your@email.com
```

3. **Model timeout:**
```bash
# Increase timeout or switch provider
export DHARMIC_MODEL_PROVIDER=anthropic
```

---

## Claude Max Issues

### Claude CLI not found

**Symptom:**
```
RuntimeError: Claude CLI not found
```

**Solution:**
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Verify
which claude
claude --version
```

**If npm not installed:**
```bash
# macOS
brew install node

# Then install Claude CLI
npm install -g @anthropic-ai/claude-code
```

---

### Claude CLI timeout

**Symptom:**
```
RuntimeError: Claude CLI timeout after 120s
```

**Solution:**
```python
# Increase timeout
from claude_max_model import ClaudeMax
model = ClaudeMax(timeout=300)  # 5 minutes
```

**Or switch to API:**
```bash
export DHARMIC_MODEL_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

---

### Claude CLI error output

**Symptom:**
```
Claude CLI error: stderr output
```

**Diagnosis:**
```bash
# Test CLI directly
echo "What is 2+2?" | claude

# Check Claude CLI status
claude --version
```

**Common fixes:**

1. **Not logged in:**
```bash
claude login
# Follow prompts
```

2. **Subscription expired:**
Check Claude Max subscription status

3. **Working directory issues:**
```bash
# CLI needs valid working directory
cd ~/DHARMIC_GODEL_CLAW
python3 src/core/dharmic_agent.py
```

---

## Memory/Performance Issues

### Out of memory

**Symptom:**
```
MemoryError: Cannot allocate memory
```

**Check memory usage:**
```bash
# Memory files
du -sh ~/DHARMIC_GODEL_CLAW/memory/
ls -lh ~/DHARMIC_GODEL_CLAW/memory/

# Running processes
ps aux | grep python | awk '{print $6, $11}'
```

**Solutions:**

1. **Consolidate memories:**
```python
agent = DharmicAgent()
agent.consolidate_memories()
```

2. **Clean old logs:**
```bash
# Keep only last 7 days
find ~/DHARMIC_GODEL_CLAW/logs/ -name "*.log" -mtime +7 -delete
```

3. **Archive old memory:**
```bash
cd ~/DHARMIC_GODEL_CLAW/memory/
tar -czf archive_$(date +%Y%m%d).tar.gz *.jsonl
# Move archive to safe location
# Truncate original files
> observations.jsonl
> meta_observations.jsonl
# etc.
```

---

### Slow performance

**Symptom:** Agent responses taking very long.

**Check:**

1. **Model provider:**
```bash
echo $DHARMIC_MODEL_PROVIDER
# Max or anthropic typically fastest
```

2. **Database size:**
```bash
ls -lh ~/DHARMIC_GODEL_CLAW/memory/deep_memory.db
# If > 500MB, may need optimization
```

3. **Memory consolidation:**
```python
agent = DharmicAgent()
status = agent.get_deep_memory_status()
print(status['memory_count'])
# If > 1000, consolidate
agent.consolidate_memories()
```

4. **Vault cache:**
```python
# VaultBridge caches reads
# Clear if too large:
agent.vault._cache.clear()
```

---

## Specialist Issues

### Specialist spawn fails

**Symptom:**
```python
specialist = runtime.spawn_specialist("research", "task")
# Returns None
```

**Check logs:**
```bash
tail -50 ~/DHARMIC_GODEL_CLAW/logs/runtime_*.log
```

**Common causes:**

1. **Agno not available:**
```bash
python3 -c "from agno.agent import Agent"
# Should not error
```

2. **Model factory missing:**
```bash
python3 -c "from model_factory import create_model"
```

3. **Model provider issue:**
```bash
# Check provider works
export DHARMIC_MODEL_PROVIDER=anthropic
```

---

## Testing Issues

### Tests fail with import errors

**Symptom:**
```
ImportError: cannot import name 'DharmicAgent'
```

**Solution:**
```bash
# Ensure testing from project root
cd ~/DHARMIC_GODEL_CLAW
source .venv/bin/activate
export PYTHONPATH=$PWD/src/core:$PYTHONPATH
pytest tests/
```

---

### Tests modify production data

**Symptom:** Tests change actual agent telos or memory.

**Solution:** Use test fixtures:

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def test_agent(tmp_path):
    """Create agent with temporary storage."""
    from dharmic_agent import DharmicAgent

    # Copy telos.yaml to temp location
    import shutil
    test_telos = tmp_path / "telos.yaml"
    shutil.copy("config/telos.yaml", test_telos)

    # Create agent with temp paths
    agent = DharmicAgent(
        telos_path=str(test_telos),
        memory_dir=str(tmp_path / "memory"),
        db_path=str(tmp_path / "test.db")
    )
    return agent

def test_something(test_agent):
    # Use test_agent instead of real agent
    response = test_agent.run("test message")
    assert response
```

---

## Platform-Specific Issues

### macOS: Command not found

**Symptom:**
```bash
./scripts/start_daemon.sh
# bash: ./scripts/start_daemon.sh: Permission denied
```

**Solution:**
```bash
chmod +x ./scripts/start_daemon.sh
./scripts/start_daemon.sh
```

---

### macOS: launchd not loading

**Symptom:**
```bash
launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist
# No output but doesn't start
```

**Check:**
```bash
launchctl list | grep dharmic
# Should show agent

# Check logs
cat ~/Library/Logs/com.dharmic.agent.log
```

**Fix plist paths:**
```xml
<!-- Ensure absolute paths in plist -->
<key>ProgramArguments</key>
<array>
    <string>/Users/dhyana/DHARMIC_GODEL_CLAW/.venv/bin/python3</string>
    <string>/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/daemon.py</string>
</array>
```

---

### Linux: systemd service

For Linux, use systemd instead of launchd:

```bash
# Create service file
sudo nano /etc/systemd/system/dharmic-agent.service
```

```ini
[Unit]
Description=Dharmic Agent Daemon
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/DHARMIC_GODEL_CLAW
ExecStart=/home/your-username/DHARMIC_GODEL_CLAW/.venv/bin/python3 src/core/daemon.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable dharmic-agent
sudo systemctl start dharmic-agent
sudo systemctl status dharmic-agent
```

---

## Emergency Recovery

### Complete system reset

If everything is broken:

```bash
# 1. Backup current state
cd ~/DHARMIC_GODEL_CLAW
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    config/ memory/ logs/ .env.local

# 2. Stop all processes
pkill -f dharmic
pkill -f daemon.py
rm logs/daemon.pid

# 3. Recreate virtual environment
rm -rf .venv/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cloned_source/agno && pip install -e . && cd ../..

# 4. Verify config
ls config/telos.yaml
ls .env.local

# 5. Test agent
cd src/core
python3 dharmic_agent.py

# 6. If working, restart daemon
cd ../..
./scripts/start_daemon.sh
```

---

### Restore from backup

```bash
# Extract backup
cd ~/DHARMIC_GODEL_CLAW
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz

# Verify files restored
ls config/telos.yaml
ls memory/

# Test
cd src/core
source ../../.venv/bin/activate
python3 dharmic_agent.py
```

---

## Getting More Help

If issue persists:

1. **Collect diagnostic info:**
```bash
cd ~/DHARMIC_GODEL_CLAW

echo "=== System Info ===" > diagnostic.txt
uname -a >> diagnostic.txt
python3 --version >> diagnostic.txt

echo "=== Python packages ===" >> diagnostic.txt
pip list >> diagnostic.txt

echo "=== File structure ===" >> diagnostic.txt
tree -L 2 src/core/ >> diagnostic.txt

echo "=== Recent logs ===" >> diagnostic.txt
tail -50 logs/daemon_*.log >> diagnostic.txt
tail -50 logs/runtime_*.log >> diagnostic.txt

echo "=== Environment ===" >> diagnostic.txt
env | grep -E "(DHARMIC|ANTHROPIC|EMAIL)" >> diagnostic.txt
```

2. **Check logs:** Always review logs first
```bash
tail -100 logs/daemon_*.log
tail -100 logs/runtime_*.log
```

3. **Test components individually:** Isolate the problem
```bash
cd src/core
python3 dharmic_agent.py
python3 runtime.py
python3 deep_memory.py
```

4. **Review recent changes:** What changed before it broke?
```bash
git log -10 --oneline
git diff HEAD~1
```

---

**Remember:** The agent is designed with graceful degradation. If one component fails, others should continue working. Vault optional, deep memory optional, email optional. Core agent always works.

JSCA!
