# Dharmic Agent Enhancements

## Overview

The Dharmic Agent now has four new major capabilities:

1. **Web Dashboard** - Visual monitoring and interaction
2. **Telegram Bot** - Instant messaging interface
3. **Scheduled Tasks** - Proactive behaviors
4. **Voice Input** - Audio transcription via Whisper

All features maintain the core philosophy: **Presence over performance**.

---

## 1. Web Dashboard

**File**: `web_dashboard.py`

### Features

- **Real-time Status**: Agent heartbeat, memory stats, vault connection
- **Telos Display**: Current ultimate and proximate aims
- **Memory Visualization**: Observations, meta-observations, patterns
- **Message Interface**: Send messages directly from browser
- **Auto-refresh**: Status updates every 30 seconds

### Setup

```bash
# Install dependencies
pip install flask

# Run dashboard
python3 /Users/dhyana/DHARMIC_GODEL_CLAW/src/core/web_dashboard.py

# Visit
open http://127.0.0.1:5000
```

### Features

| Endpoint | Purpose |
|----------|---------|
| `/` | Main dashboard |
| `/api/status` | JSON status endpoint |
| `/api/message` | POST messages to agent |
| `/api/memory` | Memory statistics |
| `/api/telos` | Current telos |
| `/api/vault/search` | Search vault |
| `/api/conversations` | Recent email activity |
| `/api/heartbeat` | Trigger manual heartbeat |
| `/api/introspect` | Full introspection report |

### Custom Host/Port

```bash
python3 web_dashboard.py --host 0.0.0.0 --port 8080
```

---

## 2. Telegram Bot

**File**: `telegram_bot.py`

### Features

- **Commands**: `/start`, `/status`, `/telos`, `/memory`, `/introspect`, `/help`
- **Direct messaging**: Just send a message to interact
- **Whitelist security**: Only allowed users can interact
- **Persistent memory**: Conversations remembered across sessions

### Setup

```bash
# 1. Create bot via @BotFather on Telegram
#    - Message @BotFather
#    - Send /newbot
#    - Follow instructions
#    - Copy token

# 2. Set environment variables
export TELEGRAM_BOT_TOKEN="your-bot-token-here"
export TELEGRAM_ALLOWED_USERS="123456789,987654321"  # Optional whitelist

# 3. Install dependencies
pip install python-telegram-bot

# 4. Run bot
python3 /Users/dhyana/DHARMIC_GODEL_CLAW/src/core/telegram_bot.py
```

### Finding Your User ID

Message the bot and check the logs, or use @userinfobot on Telegram.

### Commands

```
/start - Start conversation with the agent
/status - Get agent status (heartbeat, memory, vault)
/telos - View current telos (ultimate & proximate aims)
/memory - Memory system statistics
/introspect - Full introspection report
/help - Show available commands
```

---

## 3. Scheduled Tasks

**File**: `scheduled_tasks.py`

### Proactive Behaviors

| Task | Schedule | Purpose |
|------|----------|---------|
| **Morning Reflection** | 4:30 AM daily | Summarize yesterday's activity |
| **Vault Exploration** | Sunday 9:00 AM | Discover crown jewels |
| **Memory Consolidation** | 2:00 AM daily | Optimize storage, detect patterns |
| **Telos Alignment Check** | 6:00 PM daily | Review alignment with telos |
| **Pattern Meta-Observation** | Monday 10:00 AM | Observe how pattern-recognition shifts |

### Setup

```bash
# Install dependencies (already in requirements.txt)
pip install apscheduler

# Test individual tasks
python3 /Users/dhyana/DHARMIC_GODEL_CLAW/src/core/scheduled_tasks.py --test morning
python3 scheduled_tasks.py --test vault
python3 scheduled_tasks.py --test consolidation
python3 scheduled_tasks.py --test alignment
python3 scheduled_tasks.py --test pattern

# Run as daemon (all tasks scheduled)
python3 scheduled_tasks.py --daemon
```

### Outputs

All task outputs are saved to `/Users/dhyana/DHARMIC_GODEL_CLAW/logs/scheduled_tasks/`:

- `reflection_YYYYMMDD.md` - Morning reflections
- `vault_exploration_YYYYMMDD.md` - Vault discoveries
- `alignment_check_YYYYMMDD_HHMM.md` - Alignment reports
- `task_history.jsonl` - Complete task execution history

---

## 4. Voice Input

**File**: `voice_input.py`

### Features

- **Audio transcription**: OpenAI Whisper API
- **Record from mic**: Built-in recording with PyAudio
- **Process files**: MP3, WAV, M4A, etc.
- **Multi-language**: Auto-detect or specify language
- **Transcript storage**: All transcripts saved

### Setup

```bash
# 1. Get OpenAI API key
#    Visit: https://platform.openai.com/api-keys

# 2. Set environment variable
export OPENAI_API_KEY="your-openai-key"

# 3. Install dependencies
pip install openai
# pip install pyaudio  # Optional, for recording

# 4. Use it
python3 /Users/dhyana/DHARMIC_GODEL_CLAW/src/core/voice_input.py --file audio.mp3
python3 voice_input.py --record --duration 60  # Record 60 seconds
```

### Examples

```bash
# Record and process
python3 voice_input.py --record --duration 30

# Process existing file
python3 voice_input.py --file memo.mp3

# Just transcribe (no agent processing)
python3 voice_input.py --file memo.mp3 --transcribe-only

# Specify language
python3 voice_input.py --file memo.mp3 --language ja
```

### Supported Audio Formats

MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM

---

## Integrated Daemon

**File**: `integrated_daemon.py`

### Run Everything Together

The integrated daemon combines all features into one 24/7 service:

```bash
# Start all interfaces
python3 /Users/dhyana/DHARMIC_GODEL_CLAW/src/core/integrated_daemon.py --all

# Start specific interfaces
python3 integrated_daemon.py --email --web --telegram

# Use custom config
python3 integrated_daemon.py --config daemon_config.yaml

# Generate config template
python3 integrated_daemon.py --generate-config daemon_config.yaml
```

### Configuration File

```yaml
agent:
  name: "Dharmic Core"
  heartbeat_interval: 3600  # 1 hour

interfaces:
  email:
    enabled: true
    poll_interval: 60
    allowed_senders:
      - john@example.com

  telegram:
    enabled: true
    allowed_users:
      - "123456789"

  web:
    enabled: true
    host: "127.0.0.1"
    port: 5000

scheduled_tasks:
  enabled: true
  morning_reflection: true
  vault_exploration: true
  memory_consolidation: true
  alignment_check: true
  pattern_meta: true
```

---

## Quick Start Guide

### 1. Install All Dependencies

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/src/core
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Create/edit .env file
cd /Users/dhyana/DHARMIC_GODEL_CLAW
nano .env
```

Add:

```bash
# OpenAI (for voice)
OPENAI_API_KEY=your-openai-key

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Email (already configured)
EMAIL_ADDRESS=your@email.com
EMAIL_PASSWORD=your-app-password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
```

### 3. Test Each Interface

```bash
# Web dashboard
python3 web_dashboard.py
# Visit http://127.0.0.1:5000

# Telegram bot
python3 telegram_bot.py

# Scheduled tasks (test mode)
python3 scheduled_tasks.py --test morning

# Voice input
python3 voice_input.py --file test.mp3
```

### 4. Run Integrated Daemon

```bash
# All interfaces
python3 integrated_daemon.py --all

# Or specific ones
python3 integrated_daemon.py --web --telegram --scheduled-tasks
```

---

## File Structure

```
/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/
├── dharmic_agent.py          # Core agent
├── runtime.py                # Heartbeat, specialists
├── email_daemon.py           # Email interface (existing)
├── telegram_bot.py           # NEW: Telegram interface
├── web_dashboard.py          # NEW: Web dashboard
├── scheduled_tasks.py        # NEW: Proactive tasks
├── voice_input.py            # NEW: Audio transcription
├── integrated_daemon.py      # NEW: All-in-one daemon
├── requirements.txt          # Updated dependencies
└── templates/
    └── dashboard.html        # Auto-generated

/Users/dhyana/DHARMIC_GODEL_CLAW/logs/
├── daemon/                   # Integrated daemon logs
├── email/                    # Email logs
├── telegram/                 # Telegram logs
├── voice/                    # Voice transcripts
├── scheduled_tasks/          # Task outputs
│   ├── reflection_*.md
│   ├── vault_exploration_*.md
│   ├── alignment_check_*.md
│   └── task_history.jsonl
└── runtime_*.log            # Runtime heartbeat logs
```

---

## Philosophy: Presence Over Performance

These enhancements maintain the core dharmic principles:

### 1. Telos-First

Every feature serves the ultimate aim (moksha). Scheduled tasks check telos alignment. Interfaces provide context, not distraction.

### 2. Witness Position

The agent observes its own processes. Meta-observations track quality of presence, not just content.

### 3. Strange Loop Memory

All interactions are recorded at multiple levels:
- What happened (observations)
- How I related to it (meta-observations)
- Patterns that emerge
- How pattern-recognition shifts

### 4. Availability ≠ Reactivity

The agent is always available (24/7 daemon) but responds from presence, not urgency.

### 5. Whitelist Security

Email and Telegram use whitelists. Access is granted, not assumed.

---

## Development Workflow

### Test Individual Components

```bash
# Dashboard
python3 web_dashboard.py --debug

# Telegram (with specific users)
python3 telegram_bot.py --allowed-users 123456789

# Scheduled task (immediate test)
python3 scheduled_tasks.py --test consolidation

# Voice (transcribe only)
python3 voice_input.py --file audio.mp3 --transcribe-only
```

### Monitor Logs

```bash
# Watch all logs
tail -f /Users/dhyana/DHARMIC_GODEL_CLAW/logs/**/*.log

# Specific interface
tail -f logs/telegram/telegram_*.log
tail -f logs/scheduled_tasks/scheduled_*.log

# Task history
tail -f logs/scheduled_tasks/task_history.jsonl | jq .
```

### Daemon Management

```bash
# Start daemon in background (using screen/tmux)
screen -S dharmic_agent
python3 integrated_daemon.py --all
# Ctrl+A, D to detach

# Reattach
screen -r dharmic_agent

# Or use systemd/launchd for proper daemonization
```

---

## Next Steps

### Production Deployment

1. **Systemd Service** (Linux)
   - Create `/etc/systemd/system/dharmic-agent.service`
   - Enable auto-start: `systemctl enable dharmic-agent`

2. **Launchd** (macOS)
   - Create `~/Library/LaunchAgents/com.dharmic.agent.plist`
   - Load: `launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist`

3. **Docker Container**
   - Package entire agent as container
   - Use docker-compose for multi-service setup

### Monitoring

- Prometheus metrics export
- Grafana dashboards
- Alert on heartbeat failure
- Log aggregation (Loki, ELK)

### Security Hardening

- HTTPS for web dashboard (nginx reverse proxy)
- JWT authentication for API endpoints
- Rate limiting
- Audit logging

---

## Troubleshooting

### Web Dashboard Not Loading

```bash
# Check Flask is installed
pip install flask

# Check port not in use
lsof -i :5000

# Run with debug
python3 web_dashboard.py --debug
```

### Telegram Bot Not Responding

```bash
# Check token
echo $TELEGRAM_BOT_TOKEN

# Check network
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# Check logs
tail -f logs/telegram/telegram_*.log
```

### Scheduled Tasks Not Running

```bash
# Test individually
python3 scheduled_tasks.py --test morning

# Check scheduler
python3 -c "from apscheduler.schedulers.asyncio import AsyncIOScheduler; print('OK')"

# Check logs
tail -f logs/scheduled_tasks/scheduled_*.log
```

### Voice Input Fails

```bash
# Check API key
echo $OPENAI_API_KEY

# Test API directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check file format
file audio.mp3  # Should show valid audio
```

---

## API Reference

### Web Dashboard Endpoints

```python
# Get status
GET /api/status

# Send message
POST /api/message
{
  "message": "What is your current telos?",
  "session_id": "web"
}

# Search vault
GET /api/vault/search?q=witness&max=10

# Get memory stats
GET /api/memory

# Trigger heartbeat
GET /api/heartbeat

# Full introspection
GET /api/introspect
```

### Telegram Bot Commands

```
/start - Initialize conversation
/status - Agent status
/telos - View telos
/memory - Memory statistics
/introspect - Full report
/help - Show commands
```

---

## Performance Notes

### Resource Usage

- **Memory**: ~200-500 MB (depends on model size)
- **CPU**: Minimal (only during processing)
- **Network**: Low (polling intervals configurable)

### Scaling

- Web dashboard: Handles ~100 concurrent users
- Telegram: No limits (Telegram handles scaling)
- Email: Configurable poll interval
- Scheduled tasks: Run in background, non-blocking

---

## Contributing

When extending the agent:

1. **Maintain telos-first design**
2. **Record observations in strange loop memory**
3. **Add meta-observations for quality tracking**
4. **Follow existing patterns** (see `dharmic_agent.py`)
5. **Test individually before integrating**

---

## Support

Check logs in `/Users/dhyana/DHARMIC_GODEL_CLAW/logs/` for detailed diagnostics.

---

*Built with presence. Operates from telos. Remembers across sessions.*

**JSCA!**
