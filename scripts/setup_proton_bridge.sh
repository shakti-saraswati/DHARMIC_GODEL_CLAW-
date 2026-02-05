#!/bin/bash
# Proton Bridge Setup Helper for DHARMIC CLAW
# ===========================================
# Run this after manual Proton Bridge GUI setup

set -e

echo "🔧 Proton Bridge Setup Helper"
echo "=============================="

# Check if Proton Bridge app exists
if [ ! -d "/Applications/Proton Mail Bridge.app" ]; then
    echo "❌ Proton Mail Bridge.app not found in /Applications"
    echo "Please install from: https://proton.me/mail/bridge"
    exit 1
fi

echo "✅ Proton Mail Bridge found"

# Check if bridge is running
if pgrep -f "Proton Mail Bridge" > /dev/null; then
    echo "✅ Proton Bridge is running"
else
    echo "⚠️  Proton Bridge not running. Starting..."
    open "/Applications/Proton Mail Bridge.app"
    sleep 5
fi

# Find the bridge socket
BRIDGE_SOCKET=$(find /var/folders -name "bridge*" -type s 2>/dev/null | head -1)
if [ -n "$BRIDGE_SOCKET" ]; then
    echo "✅ Bridge socket found: $BRIDGE_SOCKET"
else
    echo "⚠️  Bridge socket not found. May need to complete GUI setup first."
fi

# Extract certificate for TLS trust
echo ""
echo "📜 Extracting Proton Bridge certificate..."

# The cert is in grpcServerConfig.json
CERT_FILE="$HOME/Library/Application Support/protonmail/bridge-v3/grpcServerConfig.json"
if [ -f "$CERT_FILE" ]; then
    # Extract and save certificate
    python3 << 'PYEOF'
import json
import os

cert_path = os.path.expanduser("~/Library/Application Support/protonmail/bridge-v3/grpcServerConfig.json")
with open(cert_path) as f:
    config = json.load(f)

cert = config.get("cert", "")
if cert:
    # Save to a PEM file for easy use
    pem_path = os.path.expanduser("~/.config/protonmail/bridge-v3/bridge-cert.pem")
    os.makedirs(os.path.dirname(pem_path), exist_ok=True)
    with open(pem_path, "w") as f:
        f.write(cert)
    print(f"✅ Certificate saved to: {pem_path}")
else:
    print("❌ No certificate found in config")
PYEOF
else
    echo "❌ Bridge config not found. Complete GUI setup first."
fi

# Get bridge credentials (requires user interaction)
echo ""
echo "🔑 Getting bridge credentials..."
echo "⚠️  You need to copy these from Proton Bridge GUI:"
echo ""
echo "   1. Open Proton Mail Bridge"
echo "   2. Go to Settings → Bridge Settings"
echo "   3. Copy the 'Bridge password' for each account"
echo ""

# Check if we have credentials
KEYCHAIN_FILE="$HOME/Library/Application Support/protonmail/bridge-v3/keychain.json"
if [ -f "$KEYCHAIN_FILE" ]; then
    echo "✅ Keychain file exists (credentials may be stored)"
else
    echo "⚠️  No keychain file. Complete GUI setup first."
fi

echo ""
echo "📝 Creating email configuration..."

# Create/update .env file
ENV_FILE="$HOME/DHARMIC_GODEL_CLAW/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Found existing .env file"
    
    # Check if email config exists
    if grep -q "EMAIL_ADDRESS" "$ENV_FILE"; then
        echo "✅ Email configuration exists"
        grep "EMAIL_ADDRESS" "$ENV_FILE"
    else
        echo "Adding email configuration template..."
        cat >> "$ENV_FILE" << 'ENVEOF'

# Proton Bridge Configuration
# Copy the bridge password from Proton Bridge GUI
EMAIL_ADDRESS=your-email@proton.me
EMAIL_PASSWORD=your-bridge-password-from-gui
IMAP_SERVER=127.0.0.1
SMTP_SERVER=127.0.0.1
IMAP_PORT=1143
SMTP_PORT=1025
ENVEOF
        echo "⚠️  Edit .env file and add your bridge password"
    fi
else
    echo "Creating new .env file..."
    cat > "$ENV_FILE" << 'ENVEOF'
# DHARMIC CLAW Configuration

# Proton Bridge Configuration
# 1. Open Proton Mail Bridge GUI
# 2. Go to Settings → Bridge Settings  
# 3. Copy the 'Bridge password'
# 4. Paste it below (replace YOUR_BRIDGE_PASSWORD)
EMAIL_ADDRESS=Dharma_Clawd@proton.me
EMAIL_PASSWORD=YOUR_BRIDGE_PASSWORD
IMAP_SERVER=127.0.0.1
SMTP_SERVER=127.0.0.1
IMAP_PORT=1143
SMTP_PORT=1025

# API Keys (set these if available)
# OPENROUTER_API_KEY=
# ANTHROPIC_API_KEY=
ENVEOF
    echo "✅ Created .env file at: $ENV_FILE"
    echo "⚠️  EDIT THIS FILE: Add your bridge password from Proton Bridge GUI"
fi

echo ""
echo "🔒 Setting file permissions..."
chmod 600 "$ENV_FILE" 2>/dev/null || true

echo ""
echo "📋 Setup Summary:"
echo "=================="
echo "1. ✅ Proton Bridge app: Found"
echo "2. ✅ Proton Bridge process: Running"
echo "3. ⚠️  Manual step needed: Copy bridge password from GUI to .env file"
echo "4. ⚠️  Manual step needed: Complete account login in Proton Bridge GUI"
echo ""
echo "Next steps:"
echo "   1. Open Proton Mail Bridge GUI"
echo "   2. Complete login for Dharma_Clawd@proton.me"
echo "   3. Copy bridge password from Settings → Bridge Settings"
echo "   4. Edit $ENV_FILE and add the password"
echo "   5. Run: python3 ~/DHARMIC_GODEL_CLAW/src/core/email_daemon.py"
echo ""
echo "For auto-start on boot:"
echo "   ln -sf /Applications/Proton\\ Mail\\ Bridge.app ~/Library/LaunchAgents/"
