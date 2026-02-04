# Hyper-Secure OpenClaw Configuration

**Status**: Ready to Deploy
**Security Level**: Maximum (Paranoid Mode Available)

---

## Security Threat Model

### What We're Protecting Against

| Threat | Attack Vector | Mitigation |
|--------|---------------|------------|
| **CVE-2026-25253** | Gateway token theft via malicious link | Token auth + loopback binding |
| **Prompt Injection** | Malicious skills/content | Sandbox + tool denylists |
| **Credential Theft** | Config file exposure | 600 permissions + redaction |
| **Lateral Movement** | Agent escapes sandbox | Docker sandbox + scope isolation |
| **Remote Access** | Network exposure | Loopback-only binding |
| **Session Hijacking** | Shared DM context | Per-channel-peer isolation |

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NETWORK LAYER                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Gateway bound to 127.0.0.1:18789 ONLY               │   │
│  │ No external network exposure                         │   │
│  │ mDNS discovery: OFF or MINIMAL                      │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                   AUTH LAYER                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Token authentication required                        │   │
│  │ DM policy: PAIRING (approval required)              │   │
│  │ Groups: MENTION required                            │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  SANDBOX LAYER                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ All agents sandboxed by default                     │   │
│  │ Workspace: READ-ONLY (or NONE in paranoid)          │   │
│  │ Denied: exec, process, apply_patch                  │   │
│  │ Paranoid: +browser, +write, +edit, +web_fetch       │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 SESSION LAYER                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Session scope: per-channel-peer                     │   │
│  │ Each sender gets isolated context                   │   │
│  │ No cross-contamination between conversations        │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 LOGGING LAYER                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Sensitive data redacted from logs                   │   │
│  │ API keys, tokens, passwords masked                  │   │
│  │ Tool outputs sanitized                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Comparison

### Default vs Hardened vs Paranoid

| Setting | Default | Hardened | Paranoid |
|---------|---------|----------|----------|
| Gateway bind | loopback | loopback | loopback |
| Auth mode | token | token | token |
| mDNS | minimal | minimal | **off** |
| DM policy | open | **pairing** | **pairing** |
| Group mentions | false | **true** | **true** |
| Session scope | main | **per-channel-peer** | **per-channel-peer** |
| Sandbox mode | off | **all** | **all** |
| Workspace access | rw | **ro** | **none** |
| exec tool | allowed | **denied** | **denied** |
| process tool | allowed | **denied** | **denied** |
| browser tool | allowed | allowed | **denied** |
| write tool | allowed | allowed | **denied** |
| edit tool | allowed | allowed | **denied** |
| web_fetch | allowed | allowed | **denied** |
| Log redaction | off | **tools** | **tools** |

---

## Quick Deploy Commands

```bash
# 1. Migrate from Clawdbot (stop vulnerable version)
~/DHARMIC_GODEL_CLAW/scripts/migrate_to_openclaw.sh

# 2. Apply hardening (standard mode)
~/DHARMIC_GODEL_CLAW/scripts/harden_openclaw.sh

# 3. OR: Apply maximum paranoia
~/DHARMIC_GODEL_CLAW/scripts/harden_openclaw.sh --paranoid

# 4. Restart gateway
openclaw gateway restart

# 5. Verify
openclaw security audit --deep
openclaw doctor
```

---

## Hardened Configuration Template

```json
{
  "gateway": {
    "bind": "loopback",
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "YOUR_64_CHAR_SECURE_TOKEN"
    },
    "controlUi": {
      "allowInsecureAuth": false,
      "dangerouslyDisableDeviceAuth": false
    }
  },

  "discovery": {
    "mdns": { "mode": "minimal" }
  },

  "session": {
    "dmScope": "per-channel-peer"
  },

  "channels": {
    "whatsapp": {
      "dmPolicy": "pairing",
      "groups": { "*": { "requireMention": true } }
    },
    "telegram": {
      "dmPolicy": "pairing",
      "groups": { "*": { "requireMention": true } }
    }
  },

  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "all",
        "scope": "agent",
        "workspaceAccess": "ro"
      },
      "tools": {
        "deny": ["exec", "process", "apply_patch"]
      }
    }
  },

  "logging": {
    "redactSensitive": "tools",
    "redactPatterns": [
      "sk-ant-[a-zA-Z0-9-]+",
      "sk-or-[a-zA-Z0-9-]+",
      "password[=:][^\\s]+"
    ]
  },

  "rateLimit": {
    "enabled": true,
    "maxRequestsPerMinute": 30
  }
}
```

---

## File Permission Requirements

```bash
# Directory permissions
chmod 700 ~/.openclaw
chmod 700 ~/.openclaw/credentials
chmod 700 ~/.openclaw/agents

# File permissions
chmod 600 ~/.openclaw/openclaw.json
chmod 600 ~/.openclaw/credentials/*
chmod 600 ~/.openclaw/agents/*/agent/auth-profiles.json

# Verify
ls -la ~/.openclaw/
```

---

## API Key Security

### Problem
API keys in config file can be exposed if file permissions are wrong.

### Solution: Environment Variables

```bash
# In ~/.openclaw/env.sh (chmod 600)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="sk-or-..."
export MOONSHOT_API_KEY="sk-..."

# Source before running
source ~/.openclaw/env.sh
```

### Better: Use macOS Keychain

```bash
# Store in Keychain
security add-generic-password -s "openclaw-anthropic" -a "$USER" -w "sk-ant-..."

# Retrieve
security find-generic-password -s "openclaw-anthropic" -w
```

---

## Incident Response Playbook

### If Compromised

```bash
# 1. IMMEDIATE: Stop gateway
openclaw gateway stop

# 2. Isolate network
# (gateway already loopback-only, but verify)

# 3. Rotate ALL credentials
openclaw doctor --generate-gateway-token

# 4. Revoke API keys
# - Anthropic: console.anthropic.com
# - OpenRouter: openrouter.ai/settings
# - Moonshot: platform.moonshot.ai

# 5. Review logs
cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i "error\|fail\|denied"

# 6. Clear sessions
rm -rf ~/.openclaw/agents/*/sessions/*

# 7. Audit
openclaw security audit --deep

# 8. Restart with fresh config
openclaw gateway start
```

---

## Monitoring Commands

```bash
# Health check
openclaw doctor

# Security audit
openclaw security audit --deep

# View active sessions
openclaw sessions list

# Check gateway status
openclaw gateway status

# View recent logs
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

---

## The Dharmic Security Principle

> "The best security is making the system unattractive to bad actors while irresistible to aligned ones."

Our hyper-secure setup:
1. **Denies by default** - nothing allowed without explicit permission
2. **Isolates by default** - each session/agent sandboxed
3. **Redacts by default** - sensitive data never logged
4. **Requires proof** - pairing codes, mentions, tokens
5. **Fails closed** - if unsure, deny access

---

## Sources

- [OpenClaw Security Docs](https://docs.openclaw.ai/gateway/security)
- [DefectDojo Hardening Checklist](https://defectdojo.com/blog/the-openclaw-hardening-checklist-in-depth-edition)
- [CVE-2026-25253 Details](https://www.securityweek.com/vulnerability-allows-hackers-to-hijack-openclaw-ai-assistant/)
- [SecurityWeek Analysis](https://www.securityweek.com/vulnerability-allows-hackers-to-hijack-openclaw-ai-assistant/)
