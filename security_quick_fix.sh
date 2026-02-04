#!/bin/bash
# Security Quick Fix Script
# Addresses CRITICAL and HIGH severity issues from security audit
# Run with: bash security_quick_fix.sh

set -e

echo "=========================================="
echo "Dharmic Agent - Security Quick Fix"
echo "=========================================="
echo ""

DHARMIC_ROOT="/Users/dhyana/DHARMIC_GODEL_CLAW"

# Check if running from correct directory
if [ ! -d "$DHARMIC_ROOT" ]; then
    echo "ERROR: $DHARMIC_ROOT not found"
    exit 1
fi

cd "$DHARMIC_ROOT"

echo "[1/6] Fixing .env file permissions..."
if [ -f ".env" ]; then
    chmod 600 .env
    echo "  ✓ .env now: $(ls -l .env | awk '{print $1, $3, $4}')"
else
    echo "  ! .env not found (may not be an issue)"
fi

echo ""
echo "[2/6] Fixing database file permissions..."
if [ -d "memory" ]; then
    chmod 700 memory
    chmod 600 memory/*.db 2>/dev/null || true
    chmod 600 memory/*.jsonl 2>/dev/null || true
    chmod 600 memory/*.json 2>/dev/null || true
    echo "  ✓ Database files secured"
    ls -la memory/*.db 2>/dev/null | awk '{print "    " $1, $9}'
else
    echo "  ! memory/ directory not found"
fi

echo ""
echo "[3/6] Fixing log file permissions..."
if [ -d "logs" ]; then
    chmod 700 logs
    find logs -type f -name "*.log" -exec chmod 600 {} \;
    find logs -type f -name "*.json" -exec chmod 600 {} \;
    echo "  ✓ Log files secured"
    echo "  $(find logs -type f | wc -l | tr -d ' ') log files updated"
else
    echo "  ! logs/ directory not found"
fi

echo ""
echo "[4/6] Backing up current files..."
BACKUP_DIR="security_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp src/core/email_daemon.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/core/vault_bridge.py "$BACKUP_DIR/" 2>/dev/null || true
echo "  ✓ Backups saved to $BACKUP_DIR/"

echo ""
echo "[5/6] Checking for hardcoded credentials in git history..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    CREDENTIAL_FILES=$(git log --all --full-history --source -- '*.env' 2>/dev/null | grep -c "^commit" || echo "0")
    if [ "$CREDENTIAL_FILES" -gt 0 ]; then
        echo "  ⚠ WARNING: Found $CREDENTIAL_FILES commits with .env files"
        echo "  Consider using git-filter-repo to remove sensitive history"
    else
        echo "  ✓ No .env files found in git history"
    fi
else
    echo "  ! Not a git repository"
fi

echo ""
echo "[6/6] Verification..."

# Check permissions
echo "  Checking critical file permissions:"
if [ -f ".env" ]; then
    PERM=$(stat -f "%Lp" .env)
    if [ "$PERM" = "600" ]; then
        echo "    ✓ .env: 600 (correct)"
    else
        echo "    ✗ .env: $PERM (should be 600)"
    fi
fi

if [ -d "memory" ]; then
    DB_COUNT=$(find memory -name "*.db" -perm 600 | wc -l | tr -d ' ')
    echo "    ✓ $DB_COUNT database files with 600 permissions"
fi

if [ -d "logs" ]; then
    LOG_COUNT=$(find logs -name "*.log" -perm 600 | wc -l | tr -d ' ')
    echo "    ✓ $LOG_COUNT log files with 600 permissions"
fi

echo ""
echo "=========================================="
echo "Quick Fix Complete!"
echo "=========================================="
echo ""
echo "⚠ IMPORTANT: This script only fixed file permissions."
echo ""
echo "Still required (see SECURITY_AUDIT_REPORT.md):"
echo "  1. Migrate credentials from .env to macOS Keychain"
echo "  2. Add input sanitization to email_daemon.py"
echo "  3. Add path traversal protection to vault_bridge.py"
echo "  4. Enable email sender whitelist enforcement"
echo "  5. Review and test all subprocess calls"
echo ""
echo "Next steps:"
echo "  1. Read: cat SECURITY_AUDIT_REPORT.md"
echo "  2. Review backups in: $BACKUP_DIR/"
echo "  3. Apply code-level fixes from audit report"
echo "  4. Test security with: python3 scripts/security_test.py"
echo ""
