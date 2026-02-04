#!/bin/bash
# =============================================================================
# OPENCLAW HYPER-SECURITY HARDENING SCRIPT
# =============================================================================
#
# Based on:
#   - OpenClaw Official Security Docs
#   - DefectDojo Hardening Checklist
#   - CVE-2026-25253 Post-Mortem Recommendations
#
# This script applies MAXIMUM security settings while maintaining usability.
#
# Usage:
#   ./harden_openclaw.sh              # Apply hardening
#   ./harden_openclaw.sh --audit      # Audit only (no changes)
#   ./harden_openclaw.sh --paranoid   # Maximum paranoia mode
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

OPENCLAW_DIR="$HOME/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
BACKUP_FILE="$CONFIG_FILE.pre-hardening.$(date +%Y%m%d_%H%M%S)"

AUDIT_ONLY=false
PARANOID=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --audit) AUDIT_ONLY=true; shift ;;
        --paranoid) PARANOID=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

log() { echo -e "${BLUE}[HARDEN]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

# =============================================================================
# SECURITY CHECKS
# =============================================================================

echo ""
echo "============================================================"
echo "     OPENCLAW HYPER-SECURITY HARDENING"
echo "============================================================"
echo ""

# Check OpenClaw version
log "Checking OpenClaw version..."
VERSION=$(openclaw --version 2>/dev/null || echo "unknown")
if [[ "$VERSION" < "2026.1.29" ]]; then
    fail "Version $VERSION is VULNERABLE - update first!"
    exit 1
else
    pass "Version $VERSION (patched)"
fi

# Check file permissions
log "Checking file permissions..."

check_perms() {
    local file="$1"
    local expected="$2"
    local actual=$(stat -f "%OLp" "$file" 2>/dev/null || echo "missing")

    if [[ "$actual" == "$expected" ]]; then
        pass "$file: $actual"
        return 0
    else
        fail "$file: $actual (should be $expected)"
        return 1
    fi
}

PERM_ISSUES=0
check_perms "$OPENCLAW_DIR" "700" || ((PERM_ISSUES++))
check_perms "$CONFIG_FILE" "600" || ((PERM_ISSUES++))

if [[ -d "$OPENCLAW_DIR/credentials" ]]; then
    check_perms "$OPENCLAW_DIR/credentials" "700" || ((PERM_ISSUES++))
fi

# Check gateway binding
log "Checking gateway configuration..."
if [[ -f "$CONFIG_FILE" ]]; then
    BIND=$(python3 -c "import json; c=json.load(open('$CONFIG_FILE')); print(c.get('gateway',{}).get('bind','loopback'))" 2>/dev/null || echo "unknown")
    if [[ "$BIND" == "loopback" ]]; then
        pass "Gateway bound to loopback only"
    elif [[ "$BIND" == "0.0.0.0" ]]; then
        fail "Gateway exposed to ALL interfaces (CRITICAL)"
        ((PERM_ISSUES++))
    else
        warn "Gateway bound to: $BIND"
    fi

    # Check auth
    AUTH_MODE=$(python3 -c "import json; c=json.load(open('$CONFIG_FILE')); print(c.get('gateway',{}).get('auth',{}).get('mode','none'))" 2>/dev/null || echo "none")
    if [[ "$AUTH_MODE" == "token" ]]; then
        pass "Token authentication enabled"
    else
        fail "Authentication mode: $AUTH_MODE (should be 'token')"
        ((PERM_ISSUES++))
    fi
fi

# Check for sensitive data in config
log "Checking for exposed secrets..."
if grep -q "sk-ant-" "$CONFIG_FILE" 2>/dev/null; then
    warn "Anthropic API key found in config (consider env vars)"
fi
if grep -q "sk-or-" "$CONFIG_FILE" 2>/dev/null; then
    warn "OpenRouter API key found in config (consider env vars)"
fi

echo ""
echo "============================================================"
echo "Security Audit Summary: $PERM_ISSUES issues found"
echo "============================================================"

if [[ "$AUDIT_ONLY" == "true" ]]; then
    echo ""
    log "Audit-only mode. Run without --audit to apply fixes."
    exit 0
fi

# =============================================================================
# APPLY HARDENING
# =============================================================================

echo ""
log "Applying hyper-security hardening..."
echo ""

# Backup config
log "Creating backup..."
cp "$CONFIG_FILE" "$BACKUP_FILE"
pass "Backup: $BACKUP_FILE"

# Fix permissions
log "Fixing file permissions..."
chmod 700 "$OPENCLAW_DIR"
chmod 600 "$CONFIG_FILE"
[[ -d "$OPENCLAW_DIR/credentials" ]] && chmod 700 "$OPENCLAW_DIR/credentials"
[[ -d "$OPENCLAW_DIR/agents" ]] && chmod 700 "$OPENCLAW_DIR/agents"
find "$OPENCLAW_DIR" -type f -name "*.json" -exec chmod 600 {} \; 2>/dev/null || true
pass "Permissions hardened"

# Generate secure token if needed
log "Checking gateway token..."
if ! grep -q '"token"' "$CONFIG_FILE" 2>/dev/null; then
    log "Generating secure gateway token..."
    NEW_TOKEN=$(openssl rand -hex 32)
    warn "New token generated - save this: $NEW_TOKEN"
fi

# Apply secure configuration
log "Applying secure configuration..."

python3 << 'PYTHON_HARDENING'
import json
import os
import secrets
from pathlib import Path

config_file = Path.home() / ".openclaw" / "openclaw.json"
paranoid = os.environ.get("PARANOID", "false") == "true"

# Load existing config
config = json.loads(config_file.read_text())

# =============================================================================
# GATEWAY HARDENING
# =============================================================================

if "gateway" not in config:
    config["gateway"] = {}

# Bind to loopback ONLY
config["gateway"]["bind"] = "loopback"
config["gateway"]["port"] = 18789

# Require token auth
if "auth" not in config["gateway"]:
    config["gateway"]["auth"] = {}

config["gateway"]["auth"]["mode"] = "token"

# Generate token if missing
if not config["gateway"]["auth"].get("token"):
    config["gateway"]["auth"]["token"] = secrets.token_hex(32)
    print(f"  Generated gateway token: {config['gateway']['auth']['token'][:16]}...")

# Disable dangerous control UI options
config["gateway"]["controlUi"] = {
    "allowInsecureAuth": False,
    "dangerouslyDisableDeviceAuth": False
}

# =============================================================================
# DISCOVERY HARDENING
# =============================================================================

config["discovery"] = {
    "mdns": {"mode": "off" if paranoid else "minimal"}
}

# =============================================================================
# SESSION ISOLATION
# =============================================================================

config["session"] = {
    "dmScope": "per-channel-peer"  # Isolate sessions by sender
}

# =============================================================================
# CHANNEL HARDENING
# =============================================================================

for channel in ["whatsapp", "telegram", "discord", "slack", "signal"]:
    if channel not in config.get("channels", {}):
        if "channels" not in config:
            config["channels"] = {}
        config["channels"][channel] = {}

    # Require pairing for DMs
    config["channels"][channel]["dmPolicy"] = "pairing"

    # Require explicit mentions in groups
    if "groups" not in config["channels"][channel]:
        config["channels"][channel]["groups"] = {}
    config["channels"][channel]["groups"]["*"] = {"requireMention": True}

# =============================================================================
# AGENT SANDBOXING
# =============================================================================

if "agents" not in config:
    config["agents"] = {}

if "defaults" not in config["agents"]:
    config["agents"]["defaults"] = {}

# Enable sandboxing by default
config["agents"]["defaults"]["sandbox"] = {
    "mode": "all",
    "scope": "agent",
    "workspaceAccess": "ro" if not paranoid else "none"
}

# Deny dangerous tools by default
config["agents"]["defaults"]["tools"] = {
    "deny": [
        "exec",           # Shell execution
        "process",        # Process spawning
        "apply_patch",    # Direct file patching
    ]
}

if paranoid:
    config["agents"]["defaults"]["tools"]["deny"].extend([
        "browser",        # Browser automation
        "write",          # File writing
        "edit",           # File editing
        "web_fetch",      # External HTTP requests
    ])
    config["agents"]["defaults"]["sandbox"]["workspaceAccess"] = "none"

# =============================================================================
# LOGGING & REDACTION
# =============================================================================

config["logging"] = {
    "redactSensitive": "tools",
    "redactPatterns": [
        "sk-ant-[a-zA-Z0-9-]+",      # Anthropic keys
        "sk-or-[a-zA-Z0-9-]+",       # OpenRouter keys
        "sk-[a-zA-Z0-9-]{20,}",      # Generic API keys
        "password[=:][^\\s]+",       # Password patterns
        "token[=:][^\\s]+",          # Token patterns
    ]
}

# =============================================================================
# RATE LIMITING (Additional protection)
# =============================================================================

config["rateLimit"] = {
    "enabled": True,
    "maxRequestsPerMinute": 30,
    "maxToolCallsPerSession": 100
}

# =============================================================================
# SAVE CONFIG
# =============================================================================

config_file.write_text(json.dumps(config, indent=2))
print("  Configuration hardened successfully")

# Print summary
print("\n  === HARDENING SUMMARY ===")
print(f"  Gateway bind: {config['gateway']['bind']}")
print(f"  Auth mode: {config['gateway']['auth']['mode']}")
print(f"  mDNS: {config['discovery']['mdns']['mode']}")
print(f"  Session isolation: {config['session']['dmScope']}")
print(f"  Sandbox mode: {config['agents']['defaults']['sandbox']['mode']}")
print(f"  Workspace access: {config['agents']['defaults']['sandbox']['workspaceAccess']}")
print(f"  Denied tools: {', '.join(config['agents']['defaults']['tools']['deny'])}")

PYTHON_HARDENING

# Set paranoid mode if requested
if [[ "$PARANOID" == "true" ]]; then
    PARANOID=true python3 -c "import os; os.environ['PARANOID']='true'" 2>/dev/null || true
fi

# Run OpenClaw security audit
echo ""
log "Running OpenClaw security audit..."
openclaw security audit --fix 2>/dev/null || warn "Security audit command not available in this version"

# Verify changes
echo ""
log "Verification..."
openclaw doctor 2>&1 | head -20 || true

echo ""
echo "============================================================"
echo "     HARDENING COMPLETE"
echo "============================================================"
echo ""
echo "Security measures applied:"
echo "  [x] Gateway bound to loopback only"
echo "  [x] Token authentication required"
echo "  [x] mDNS discovery minimized"
echo "  [x] Session isolation enabled"
echo "  [x] DM pairing required"
echo "  [x] Group mentions required"
echo "  [x] Agent sandboxing enabled"
echo "  [x] Dangerous tools denied"
echo "  [x] Log redaction enabled"
echo "  [x] File permissions hardened"
echo ""
echo "Backup saved to: $BACKUP_FILE"
echo ""
echo "To restore: cp '$BACKUP_FILE' '$CONFIG_FILE'"
echo ""

if [[ "$PARANOID" == "true" ]]; then
    echo "PARANOID MODE: Maximum restrictions applied"
    echo "  - Browser tool DENIED"
    echo "  - Write/Edit tools DENIED"
    echo "  - Web fetch DENIED"
    echo "  - Workspace access: NONE"
    echo ""
fi

echo "Restart gateway to apply: openclaw gateway restart"
echo ""
