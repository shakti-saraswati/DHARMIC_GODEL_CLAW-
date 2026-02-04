# OpenClaw × Dharmic Gödel Claw Integration

## The Strategy

**Don't rebuild OpenClaw. Seed it.**

OpenClaw is mature infrastructure. Your DHARMIC_GODEL_CLAW is mature philosophy.
Combine them: OpenClaw as chassis, dharmic telos as soul.

---

## Phase 1: Minimal OpenClaw Installation (30 minutes)

### Quick VPS Setup (Hetzner)

```bash
# 1. Create Hetzner CX22 (€4.15/mo) - Ubuntu 24.04
# 2. SSH in and run:

# Install dependencies
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs git

# Install OpenClaw
npm install -g openclaw@latest

# Onboard with API key (use your existing Anthropic key)
openclaw onboard --install-daemon

# DON'T connect WhatsApp yet - we seed first
```

### Local Dev Option (if you have always-on Mac)

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

---

## Phase 2: Dharmic Telos Seeding

Copy `persona.md` from this directory to `~/.openclaw/persona.md`

---

## Phase 3: Configuration

Add to `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "persona": "~/.openclaw/persona.md",
      "model": {
        "primary": "anthropic/claude-sonnet-4-5"
      },
      "sandbox": {
        "enabled": true,
        "mode": "docker"
      }
    }
  },
  "tools": {
    "exec": {
      "requireApproval": true
    },
    "injectionScan": {
      "enabled": true,
      "minSeverity": "medium",
      "action": "warn"
    }
  },
  "heartbeat": {
    "every": "4h"
  },
  "channels": {
    "whatsapp": {
      "dmPolicy": "pairing",
      "allowFrom": ["+YOUR_NUMBER"]
    }
  }
}
```

---

## Phase 4: First Conversation

After installation and seeding, send this first message via WhatsApp:

```
Dharmic Claw, acknowledge your new configuration.

Read your persona file and telos. 
Then tell me: what do you understand your purpose to be?
And: what's the first thing you want to help develop?
```

---

## Phase 5: Self-Development Loop

Once basic function confirmed:

```
I'm giving you access to the DHARMIC_GODEL_CLAW repository at:
~/DHARMIC_GODEL_CLAW/

This is the codebase you emerged from. Your task:
1. Read the architecture (ARCHITECTURE.md)
2. Read the swarm implementation (swarm/)
3. Propose ONE improvement that would help integrate OpenClaw capabilities with the dharmic swarm

Remember: propose, don't implement. We evaluate together.
```

---

## Expected Timeline

| Phase | Time | Outcome |
|-------|------|---------|
| 1. Installation | 30 min | OpenClaw running |
| 2. Seeding | 15 min | Persona configured |
| 3. Config | 10 min | Security settings |
| 4. First chat | 15 min | Verify telos loaded |
| 5. Self-dev intro | 30 min | Reads codebase |
| 6. First skill | 1-2 hrs | dharmic-gate skill |

**Total: One afternoon.**
