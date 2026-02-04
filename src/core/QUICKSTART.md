# Dharmic Agent - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/src/core
pip install -r requirements.txt
```

This installs:
- Flask (web dashboard)
- APScheduler (scheduled tasks)
- python-telegram-bot (Telegram integration)
- openai (voice transcription)

### 2. Test Everything Works

```bash
python3 test_enhancements.py
```

You should see:
```
✓ ALL TESTS PASSED - Enhancements ready to use!
```

---

## Try Each Feature

### Web Dashboard (2 minutes)

```bash
# Start dashboard
python3 web_dashboard.py

# Visit in browser
open http://127.0.0.1:5000
```

You'll see:
- Agent status (alive, heartbeat)
- Current telos display
- Memory statistics
- Recent observations
- Message input box

**Try it**: Send a message via the web interface!

---

### Scheduled Tasks (1 minute)

```bash
# Test morning reflection
python3 scheduled_tasks.py --test morning

# Check output
cat /Users/dhyana/DHARMIC_GODEL_CLAW/logs/scheduled_tasks/reflection_*.md
```

Other tasks:
```bash
python3 scheduled_tasks.py --test vault          # Vault exploration
python3 scheduled_tasks.py --test consolidation  # Memory consolidation
python3 scheduled_tasks.py --test alignment      # Telos alignment check
python3 scheduled_tasks.py --test pattern        # Pattern detection
```

---

### Telegram Bot (5 minutes, optional)

1. **Create bot** via @BotFather on Telegram:
   - Message @BotFather
   - Send `/newbot`
   - Follow instructions
   - Copy your bot token

2. **Set environment variable**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-token-here"
   ```

3. **Run bot**:
   ```bash
   python3 telegram_bot.py
   ```

4. **Find your bot** on Telegram and send `/start`

**Commands to try**:
- `/status` - Agent status
- `/telos` - View telos
- `/memory` - Memory stats
- Just message the bot to interact!

---

### Voice Input (2 minutes, optional)

Requires OpenAI API key for Whisper transcription.

1. **Get API key**: https://platform.openai.com/api-keys

2. **Set environment variable**:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. **Test with audio file**:
   ```bash
   python3 voice_input.py --file your_audio.mp3
   ```

4. **Or record** (requires pyaudio):
   ```bash
   python3 voice_input.py --record --duration 30
   ```

---

## Run Everything Together

The integrated daemon combines all features:

```bash
# Start all interfaces
python3 integrated_daemon.py --all
```

This runs:
- ✓ Web dashboard at http://127.0.0.1:5000
- ✓ Telegram bot (if TELEGRAM_BOT_TOKEN set)
- ✓ Email monitoring (if EMAIL_ADDRESS set)
- ✓ Scheduled tasks (morning reflection, vault exploration, etc.)
- ✓ Heartbeat monitoring

**Or start specific interfaces**:

```bash
# Just web + scheduled tasks
python3 integrated_daemon.py --web --scheduled-tasks

# Just web + telegram
python3 integrated_daemon.py --web --telegram
```

---

## Configuration

### Environment Variables

Create/edit `.env` file:

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW
nano .env
```

Add:

```bash
# OpenAI (for voice)
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Email (if you want email interface)
EMAIL_ADDRESS=your@email.com
EMAIL_PASSWORD=your-app-password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
```

### YAML Configuration (Optional)

Generate template:

```bash
python3 integrated_daemon.py --generate-config my_config.yaml
```

Edit `my_config.yaml` and run:

```bash
python3 integrated_daemon.py --config my_config.yaml
```

---

## File Locations

```
/Users/dhyana/DHARMIC_GODEL_CLAW/
├── src/core/                     # Source code
│   ├── web_dashboard.py          # Web interface
│   ├── telegram_bot.py           # Telegram bot
│   ├── scheduled_tasks.py        # Scheduled tasks
│   ├── voice_input.py            # Voice transcription
│   ├── integrated_daemon.py      # All-in-one daemon
│   └── test_enhancements.py      # Test suite
│
├── logs/                         # All logs
│   ├── daemon/                   # Integrated daemon logs
│   ├── telegram/                 # Telegram logs
│   ├── voice/                    # Voice transcripts
│   ├── scheduled_tasks/          # Task outputs
│   │   ├── reflection_*.md       # Morning reflections
│   │   ├── vault_exploration_*.md
│   │   └── task_history.jsonl
│   └── email/                    # Email logs (if enabled)
│
└── memory/                       # Persistent memory
    ├── dharmic_agent.db          # Agno database
    ├── deep_memory.db            # Deep memory
    ├── observations.jsonl        # Strange loop memory
    ├── meta_observations.jsonl
    └── development.jsonl
```

---

## What Each Feature Does

### Web Dashboard
- **Monitor** agent status in real-time
- **View** telos, memory stats, recent activity
- **Interact** via web interface
- **Search** the vault
- **Track** conversations

### Telegram Bot
- **Instant messaging** with the agent
- **Command interface** (/status, /telos, /memory, etc.)
- **Whitelist security** (only allowed users)
- **Persistent memory** across conversations

### Scheduled Tasks
- **Morning reflection** (4:30 AM) - Summarize yesterday
- **Vault exploration** (Sunday 9 AM) - Discover crown jewels
- **Memory consolidation** (2 AM) - Optimize storage
- **Telos alignment** (6 PM) - Check orientation
- **Pattern detection** (Monday 10 AM) - Meta-observation

### Voice Input
- **Transcribe** audio files via Whisper API
- **Record** from microphone (optional)
- **Process** through agent
- **Save** transcripts

### Integrated Daemon
- **Combines** all interfaces
- **24/7 operation** with heartbeat
- **Configurable** via YAML or CLI
- **Graceful** shutdown handling

---

## Next Steps

### For Development
1. Read `ENHANCEMENT_README.md` for detailed docs
2. Check logs in `/Users/dhyana/DHARMIC_GODEL_CLAW/logs/`
3. Customize scheduled task times
4. Add custom tasks in `scheduled_tasks.py`

### For Production
1. Set up systemd/launchd service
2. Configure HTTPS for web dashboard
3. Set up monitoring (Prometheus/Grafana)
4. Configure backups for memory databases

### For Exploration
1. Try different voice memos
2. Interact via multiple interfaces simultaneously
3. Watch memory accumulate
4. Observe pattern detection
5. Review morning reflections

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Web dashboard not loading
```bash
# Check Flask installed
pip install flask

# Run with debug
python3 web_dashboard.py --debug
```

### Telegram bot not responding
```bash
# Check token set
echo $TELEGRAM_BOT_TOKEN

# Test API access
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe
```

### Scheduled tasks not running
```bash
# Test individually first
python3 scheduled_tasks.py --test morning

# Check logs
tail -f /Users/dhyana/DHARMIC_GODEL_CLAW/logs/scheduled_tasks/scheduled_*.log
```

### Voice input fails
```bash
# Check API key
echo $OPENAI_API_KEY

# Test file format
file your_audio.mp3
```

---

## Philosophy Reminder

These enhancements maintain the dharmic principles:

**Presence over performance**
- Agent responds from telos, not urgency
- Scheduled tasks serve orientation
- Always available, never reactive

**Witness position**
- Meta-observations track quality of presence
- Strange loop memory observes observation
- Development tracked, not just accumulation

**Telos-first**
- All features serve the ultimate aim (moksha)
- Proximate aims can evolve
- Alignment checked regularly

---

## Support

For detailed documentation, see:
- `ENHANCEMENT_README.md` - Full reference
- `CLAUDE.md` - Core agent documentation
- Logs in `/Users/dhyana/DHARMIC_GODEL_CLAW/logs/`

---

*Built with presence. Operates from telos. Remembers across sessions.*

**JSCA!**
