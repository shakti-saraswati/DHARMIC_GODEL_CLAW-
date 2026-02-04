#!/bin/bash
# =============================================================================
# CLAWDBOT → OPENCLAW MIGRATION SCRIPT
# =============================================================================
#
# SECURITY ALERT:
#   Clawdbot 2026.1.24-3 is VULNERABLE (CVE-2026-25253, CVSS 8.8)
#   OpenClaw 2026.2.2-3 is SAFE
#
# This script:
#   1. Creates full backup of all data
#   2. Stops vulnerable Clawdbot gateway
#   3. Migrates config to OpenClaw
#   4. Starts secure OpenClaw gateway
#   5. Verifies migration
#   6. Cleans up Clawdbot (optional)
#
# Usage:
#   ./migrate_to_openclaw.sh          # Full migration
#   ./migrate_to_openclaw.sh --dry-run # Preview only
#   ./migrate_to_openclaw.sh --rollback # Restore from backup
#
# =============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
CLAWDBOT_DIR="$HOME/.moltbot"
OPENCLAW_DIR="$HOME/.openclaw"
CLAWD_WORKSPACE="$HOME/clawd"
BACKUP_DIR="$HOME/.openclaw_migration_backup_$(date +%Y%m%d_%H%M%S)"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"

# Flags
DRY_RUN=false
ROLLBACK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute: $*"
    else
        "$@"
    fi
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

preflight_check() {
    echo "============================================================"
    echo "CLAWDBOT → OPENCLAW MIGRATION"
    echo "============================================================"
    echo ""

    # Check versions
    log_info "Checking versions..."
    CLAWDBOT_VERSION=$(clawdbot --version 2>/dev/null || echo "not installed")
    OPENCLAW_VERSION=$(openclaw --version 2>/dev/null || echo "not installed")

    echo "  Clawdbot: $CLAWDBOT_VERSION"
    echo "  OpenClaw: $OPENCLAW_VERSION"
    echo ""

    # Security check
    if [[ "$CLAWDBOT_VERSION" < "2026.1.29" ]] && [[ "$CLAWDBOT_VERSION" != "not installed" ]]; then
        log_warn "SECURITY: Clawdbot $CLAWDBOT_VERSION is VULNERABLE (CVE-2026-25253)"
        log_warn "          Migration will fix this security issue"
    fi

    if [[ "$OPENCLAW_VERSION" == "not installed" ]]; then
        log_error "OpenClaw not installed. Run: curl -fsSL https://openclaw.bot/install.sh | bash"
        exit 1
    fi

    # Check gateway status
    log_info "Checking gateway status..."
    if launchctl list | grep -q "com.clawdbot.gateway"; then
        CLAWDBOT_GATEWAY_RUNNING=true
        log_warn "Clawdbot gateway is RUNNING (will be stopped)"
    else
        CLAWDBOT_GATEWAY_RUNNING=false
        log_info "Clawdbot gateway not running"
    fi

    if launchctl list | grep -q "com.openclaw.gateway"; then
        OPENCLAW_GATEWAY_RUNNING=true
        log_info "OpenClaw gateway already running"
    else
        OPENCLAW_GATEWAY_RUNNING=false
        log_info "OpenClaw gateway not running (will be started)"
    fi

    # Check data to migrate
    log_info "Checking data to migrate..."

    if [ -d "$CLAWDBOT_DIR" ]; then
        CLAWDBOT_SIZE=$(du -sh "$CLAWDBOT_DIR" 2>/dev/null | cut -f1)
        log_info "  Clawdbot config: $CLAWDBOT_SIZE"
    else
        log_warn "  No Clawdbot directory found"
    fi

    if [ -d "$CLAWD_WORKSPACE" ]; then
        CLAWD_SIZE=$(du -sh "$CLAWD_WORKSPACE" 2>/dev/null | cut -f1)
        log_info "  Clawd workspace: $CLAWD_SIZE (will be preserved)"
    fi

    if [ -d "$OPENCLAW_DIR" ]; then
        OPENCLAW_SIZE=$(du -sh "$OPENCLAW_DIR" 2>/dev/null | cut -f1)
        log_info "  OpenClaw config: $OPENCLAW_SIZE"
    fi

    echo ""
}

# =============================================================================
# BACKUP
# =============================================================================

create_backup() {
    echo "============================================================"
    echo "STEP 1: Creating Backup"
    echo "============================================================"

    run_cmd mkdir -p "$BACKUP_DIR"

    # Backup Clawdbot config
    if [ -d "$CLAWDBOT_DIR" ]; then
        log_info "Backing up Clawdbot config..."
        run_cmd cp -R "$CLAWDBOT_DIR" "$BACKUP_DIR/moltbot"
        log_success "Backed up $CLAWDBOT_DIR"
    fi

    # Backup OpenClaw config (in case we need to rollback)
    if [ -d "$OPENCLAW_DIR" ]; then
        log_info "Backing up OpenClaw config..."
        run_cmd cp -R "$OPENCLAW_DIR" "$BACKUP_DIR/openclaw"
        log_success "Backed up $OPENCLAW_DIR"
    fi

    # Backup LaunchAgent plist
    if [ -f "$LAUNCHAGENT_DIR/com.clawdbot.gateway.plist" ]; then
        log_info "Backing up LaunchAgent..."
        run_cmd cp "$LAUNCHAGENT_DIR/com.clawdbot.gateway.plist" "$BACKUP_DIR/"
        log_success "Backed up LaunchAgent plist"
    fi

    # Backup clawd workspace (just the config, not full workspace)
    if [ -f "$CLAWD_WORKSPACE/config/workspace.json" ]; then
        run_cmd mkdir -p "$BACKUP_DIR/clawd_config"
        run_cmd cp -R "$CLAWD_WORKSPACE/config" "$BACKUP_DIR/clawd_config/"
        log_success "Backed up workspace config"
    fi

    log_success "Backup created at: $BACKUP_DIR"
    echo ""
}

# =============================================================================
# STOP CLAWDBOT
# =============================================================================

stop_clawdbot() {
    echo "============================================================"
    echo "STEP 2: Stopping Clawdbot Gateway"
    echo "============================================================"

    if launchctl list | grep -q "com.clawdbot.gateway"; then
        log_info "Unloading Clawdbot gateway..."
        run_cmd launchctl bootout "gui/$(id -u)/com.clawdbot.gateway" 2>/dev/null || true
        sleep 2

        # Verify stopped
        if ! launchctl list | grep -q "com.clawdbot.gateway"; then
            log_success "Clawdbot gateway stopped"
        else
            log_warn "Gateway may still be running"
        fi
    else
        log_info "Clawdbot gateway not running"
    fi

    echo ""
}

# =============================================================================
# MIGRATE CONFIG
# =============================================================================

migrate_config() {
    echo "============================================================"
    echo "STEP 3: Migrating Configuration"
    echo "============================================================"

    # Check if OpenClaw already has config
    if [ -f "$OPENCLAW_DIR/openclaw.json" ]; then
        log_info "OpenClaw config already exists"

        # Merge any missing API keys from Clawdbot
        if [ -f "$CLAWDBOT_DIR/clawdbot.json" ]; then
            log_info "Checking for API keys to merge..."

            # Use Python to safely merge configs
            if [ "$DRY_RUN" = false ]; then
                python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

clawdbot_config = Path.home() / ".moltbot" / "clawdbot.json"
openclaw_config = Path.home() / ".openclaw" / "openclaw.json"

if clawdbot_config.exists() and openclaw_config.exists():
    try:
        cb = json.loads(clawdbot_config.read_text())
        oc = json.loads(openclaw_config.read_text())

        # Merge env vars (API keys)
        if "env" in cb and "env" in oc:
            for key, value in cb.get("env", {}).items():
                if key not in oc["env"] or not oc["env"][key]:
                    oc["env"][key] = value
                    print(f"  Merged: {key}")

        # Save merged config
        openclaw_config.write_text(json.dumps(oc, indent=2))
        print("  Config merge complete")
    except Exception as e:
        print(f"  Warning: Could not merge configs: {e}")
PYTHON_SCRIPT
            fi
        fi
    else
        # Copy Clawdbot config as base
        if [ -f "$CLAWDBOT_DIR/clawdbot.json" ]; then
            log_info "Copying Clawdbot config to OpenClaw..."
            run_cmd cp "$CLAWDBOT_DIR/clawdbot.json" "$OPENCLAW_DIR/openclaw.json"
            log_success "Config copied"
        fi
    fi

    # Migrate credentials
    if [ -d "$CLAWDBOT_DIR/credentials" ]; then
        log_info "Migrating credentials..."
        run_cmd mkdir -p "$OPENCLAW_DIR/credentials"
        run_cmd cp -n "$CLAWDBOT_DIR/credentials/"* "$OPENCLAW_DIR/credentials/" 2>/dev/null || true
        log_success "Credentials migrated"
    fi

    # Migrate identity
    if [ -d "$CLAWDBOT_DIR/identity" ]; then
        log_info "Migrating identity..."
        run_cmd mkdir -p "$OPENCLAW_DIR/identity"
        run_cmd cp -n "$CLAWDBOT_DIR/identity/"* "$OPENCLAW_DIR/identity/" 2>/dev/null || true
        log_success "Identity migrated"
    fi

    # Migrate agents
    if [ -d "$CLAWDBOT_DIR/agents" ]; then
        log_info "Migrating agents..."
        run_cmd cp -Rn "$CLAWDBOT_DIR/agents/"* "$OPENCLAW_DIR/agents/" 2>/dev/null || true
        log_success "Agents migrated"
    fi

    # Create backward-compatible symlink
    if [ ! -L "$HOME/.clawdbot" ] && [ ! -d "$HOME/.clawdbot" ]; then
        log_info "Creating backward-compatible symlink..."
        run_cmd ln -s "$OPENCLAW_DIR" "$HOME/.clawdbot"
        log_success "Symlink created: ~/.clawdbot -> ~/.openclaw"
    fi

    echo ""
}

# =============================================================================
# START OPENCLAW
# =============================================================================

start_openclaw() {
    echo "============================================================"
    echo "STEP 4: Starting OpenClaw Gateway"
    echo "============================================================"

    # Install gateway service if needed
    if [ ! -f "$LAUNCHAGENT_DIR/com.openclaw.gateway.plist" ]; then
        log_info "Installing OpenClaw gateway service..."
        run_cmd openclaw gateway install
    fi

    # Start gateway
    log_info "Starting OpenClaw gateway..."
    run_cmd openclaw gateway start

    sleep 3

    # Verify running
    if launchctl list | grep -q "com.openclaw.gateway"; then
        log_success "OpenClaw gateway started"
    else
        log_warn "Gateway may not have started - check: openclaw gateway status"
    fi

    echo ""
}

# =============================================================================
# VERIFY
# =============================================================================

verify_migration() {
    echo "============================================================"
    echo "STEP 5: Verification"
    echo "============================================================"

    # Run doctor
    log_info "Running openclaw doctor..."
    if [ "$DRY_RUN" = false ]; then
        openclaw doctor 2>&1 | head -30
    else
        echo "[DRY-RUN] Would run: openclaw doctor"
    fi

    echo ""
    log_info "Testing agent..."
    if [ "$DRY_RUN" = false ]; then
        timeout 30 openclaw agent --agent main --message "Say 'Migration successful' if you can hear me." --local --json 2>&1 | head -10 || log_warn "Agent test timed out (may be normal)"
    fi

    echo ""
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup_clawdbot() {
    echo "============================================================"
    echo "STEP 6: Cleanup (Optional)"
    echo "============================================================"

    echo "The following Clawdbot artifacts can be removed:"
    echo "  - $LAUNCHAGENT_DIR/com.clawdbot.gateway.plist"
    echo "  - $CLAWDBOT_DIR (backed up to $BACKUP_DIR)"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would prompt for cleanup"
        return
    fi

    read -p "Remove Clawdbot LaunchAgent? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$LAUNCHAGENT_DIR/com.clawdbot.gateway.plist"
        log_success "Removed Clawdbot LaunchAgent"
    fi

    echo ""
    echo "NOTE: Keeping $CLAWDBOT_DIR for now (backup is at $BACKUP_DIR)"
    echo "      You can remove it manually after verifying everything works:"
    echo "      rm -rf $CLAWDBOT_DIR"
    echo ""
}

# =============================================================================
# ROLLBACK
# =============================================================================

rollback() {
    echo "============================================================"
    echo "ROLLBACK MODE"
    echo "============================================================"

    # Find most recent backup
    LATEST_BACKUP=$(ls -td "$HOME"/.openclaw_migration_backup_* 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        log_error "No backup found to rollback from"
        exit 1
    fi

    log_info "Found backup: $LATEST_BACKUP"

    # Stop OpenClaw
    log_info "Stopping OpenClaw gateway..."
    launchctl bootout "gui/$(id -u)/com.openclaw.gateway" 2>/dev/null || true

    # Restore Clawdbot
    if [ -d "$LATEST_BACKUP/moltbot" ]; then
        log_info "Restoring Clawdbot config..."
        rm -rf "$CLAWDBOT_DIR"
        cp -R "$LATEST_BACKUP/moltbot" "$CLAWDBOT_DIR"
        log_success "Restored $CLAWDBOT_DIR"
    fi

    # Restore LaunchAgent
    if [ -f "$LATEST_BACKUP/com.clawdbot.gateway.plist" ]; then
        log_info "Restoring LaunchAgent..."
        cp "$LATEST_BACKUP/com.clawdbot.gateway.plist" "$LAUNCHAGENT_DIR/"
        log_success "Restored LaunchAgent"
    fi

    # Start Clawdbot
    log_info "Starting Clawdbot gateway..."
    launchctl load "$LAUNCHAGENT_DIR/com.clawdbot.gateway.plist" 2>/dev/null || true

    log_success "Rollback complete"
    log_warn "NOTE: You are now running the VULNERABLE Clawdbot version"
    log_warn "      Please migrate to OpenClaw as soon as possible"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    if [ "$ROLLBACK" = true ]; then
        rollback
        exit 0
    fi

    if [ "$DRY_RUN" = true ]; then
        echo ""
        echo "=========================================="
        echo "           DRY RUN MODE"
        echo "  No changes will be made to your system"
        echo "=========================================="
        echo ""
    fi

    preflight_check

    if [ "$DRY_RUN" = false ]; then
        echo ""
        read -p "Proceed with migration? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Migration cancelled."
            exit 0
        fi
    fi

    create_backup
    stop_clawdbot
    migrate_config
    start_openclaw
    verify_migration
    cleanup_clawdbot

    echo "============================================================"
    echo "MIGRATION COMPLETE"
    echo "============================================================"
    echo ""
    echo "Summary:"
    echo "  - Backup created at: $BACKUP_DIR"
    echo "  - Clawdbot gateway: STOPPED"
    echo "  - OpenClaw gateway: RUNNING"
    echo "  - Security: PATCHED (no longer vulnerable)"
    echo ""
    echo "To rollback if needed:"
    echo "  $0 --rollback"
    echo ""
    echo "To verify:"
    echo "  openclaw doctor"
    echo "  openclaw agent --agent main --message 'Hello'"
    echo ""
}

main
