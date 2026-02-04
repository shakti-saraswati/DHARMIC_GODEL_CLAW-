# FIX: Clawdbot Claude Max Integration

## The Problem
Clawdbot is trying to hit Anthropic API directly (requires credits)
Your Claude Max subscription doesn't include API access
You need a proxy to route through your subscription

## The Solution: claude-max-api-proxy

### Step 1: Install the Proxy

```bash
# Requires Claude Code CLI to be authenticated
# Check if Claude CLI is working:
claude --version

# If that works, install the proxy:
npm install -g claude-max-api-proxy
```

### Step 2: Start the Proxy

```bash
# Start it (runs on port 3456 by default)
claude-max-api-proxy

# Or run in background:
nohup claude-max-api-proxy > /tmp/claude-proxy.log 2>&1 &
```

### Step 3: Test the Proxy

```bash
# Health check
curl http://localhost:3456/health

# List available models
curl http://localhost:3456/v1/models

# Test a completion
curl http://localhost:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Step 4: Configure Clawdbot to Use the Proxy

Edit `~/.clawdbot/clawdbot.json` and add the model section:

```json
{
  "model": {
    "primary": "claude-sonnet-4",
    "provider": {
      "type": "openai-compatible",
      "baseURL": "http://localhost:3456/v1",
      "apiKey": "not-needed"
    }
  },
  ... rest of your existing config
}
```

### Step 5: Restart Clawdbot Gateway

```bash
clawdbot gateway restart
```

### Step 6: Test

```bash
clawdbot agent -m "Hello, are you working?" --agent main --local
```

---

## Alternative: Run Proxy as Launch Agent (Auto-Start)

Create `~/Library/LaunchAgents/com.claude-max-api.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude-max-api</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/dhyana/.npm-global/bin/claude-max-api-proxy</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/Users/dhyana/.npm-global/bin:/usr/bin:/bin</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/claude-proxy.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/claude-proxy-error.log</string>
</dict>
</plist>
```

Then load it:
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.claude-max-api.plist
```

---

## Quick Fix Commands (Run These)

```bash
# 1. Install proxy
npm install -g claude-max-api-proxy

# 2. Start proxy in background
nohup claude-max-api-proxy > /tmp/claude-proxy.log 2>&1 &

# 3. Test proxy
curl http://localhost:3456/health

# 4. Update clawdbot config (backup first)
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.backup

# 5. Add model config
cat ~/.clawdbot/clawdbot.json | jq '. + {"model": {"primary": "claude-sonnet-4", "provider": {"type": "openai-compatible", "baseURL": "http://localhost:3456/v1", "apiKey": "not-needed"}}}' > /tmp/clawdbot-new.json && mv /tmp/clawdbot-new.json ~/.clawdbot/clawdbot.json

# 6. Restart gateway
clawdbot gateway restart

# 7. Test
clawdbot agent -m "Hello from Claude Max!" --agent main --local
```
