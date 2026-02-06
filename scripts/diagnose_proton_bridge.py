#!/usr/bin/env python3
"""
Proton Bridge Diagnostic Tool
=============================

Check if Proton Bridge is properly configured for email.
Run this after GUI setup to verify everything works.
"""

import os
import ssl
import imaplib
import smtplib
from pathlib import Path

def check_bridge_process():
    """Check if Proton Bridge is running."""
    import subprocess
    result = subprocess.run(
        ["pgrep", "-f", "Proton Mail Bridge"],
        capture_output=True
    )
    if result.returncode == 0:
        pids = result.stdout.decode().strip().split('\n')
        print(f"✅ Proton Bridge running ({len(pids)} processes)")
        return True
    else:
        print("❌ Proton Bridge not running")
        return False

def check_bridge_config():
    """Check bridge configuration files."""
    config_path = Path.home() / "Library/Application Support/protonmail/bridge-v3"
    
    files_to_check = [
        "grpcServerConfig.json",
        "keychain.json",
        "vault.enc"
    ]
    
    print("\n📁 Bridge Configuration:")
    all_exist = True
    for f in files_to_check:
        path = config_path / f
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {f}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_env_config():
    """Check environment configuration."""
    env_path = Path.home() / "DHARMIC_GODEL_CLAW/.env"
    
    print("\n🔐 Environment Configuration:")
    if not env_path.exists():
        print("   ❌ .env file not found")
        return False
    
    # Load and check
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    required = ['EMAIL_ADDRESS', 'EMAIL_PASSWORD', 'IMAP_SERVER', 'SMTP_SERVER']
    all_set = True
    
    for var in required:
        value = os.getenv(var)
        if value and value not in ['your@email.com', 'your-bridge-password', 'YOUR_BRIDGE_PASSWORD']:
            # Mask password
            display = value[:10] + "..." if len(value) > 10 else value
            if 'PASSWORD' in var:
                display = "********"
            print(f"   ✅ {var}={display}")
        else:
            print(f"   ❌ {var} not set or default value")
            all_set = False
    
    return all_set

def test_imap_connection():
    """Test IMAP connection."""
    print("\n📥 IMAP Connection Test:")
    
    imap_server = os.getenv('IMAP_SERVER', '127.0.0.1')
    imap_port = int(os.getenv('IMAP_PORT', '1143'))
    email_addr = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not email_addr or not password:
        print("   ⚠️  Skip: No credentials in .env")
        return False
    
    try:
        # Create SSL context that accepts self-signed cert
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        mail = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
        mail.login(email_addr, password)
        mail.select('inbox')
        
        # Check unread count
        status, messages = mail.search(None, 'UNSEEN')
        unread = len(messages[0].split()) if messages[0] else 0
        
        print(f"   ✅ Connected to {imap_server}:{imap_port}")
        print(f"   📧 Unread emails: {unread}")
        mail.logout()
        return True
        
    except Exception as e:
        print(f"   ❌ IMAP failed: {e}")
        return False

def test_smtp_connection():
    """Test SMTP connection."""
    print("\n📤 SMTP Connection Test:")
    
    smtp_server = os.getenv('SMTP_SERVER', '127.0.0.1')
    smtp_port = int(os.getenv('SMTP_PORT', '1025'))
    email_addr = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not email_addr or not password:
        print("   ⚠️  Skip: No credentials in .env")
        return False
    
    try:
        # Proton Bridge SMTP uses STARTTLS, not SSL
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.ehlo()
        
        # Start TLS with bypass
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        server.starttls(context=context)
        
        server.login(email_addr, password)
        print(f"   ✅ Connected to {smtp_server}:{smtp_port}")
        server.quit()
        return True
        
    except Exception as e:
        print(f"   ❌ SMTP failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Proton Bridge Diagnostic Tool")
    print("=" * 60)
    
    results = {
        'process': check_bridge_process(),
        'config': check_bridge_config(),
        'env': check_env_config(),
    }
    
    if results['env']:
        results['imap'] = test_imap_connection()
        results['smtp'] = test_smtp_connection()
    else:
        print("\n⚠️  Skipping connection tests (no credentials)")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ Proton Bridge fully operational!")
        print("   You can now send/receive emails.")
    elif results['process'] and results['config']:
        print("\n⚠️  Bridge is running but needs configuration.")
        print("   Run: ~/DHARMIC_GODEL_CLAW/scripts/setup_proton_bridge.sh")
    else:
        print("\n❌ Bridge needs setup.")
        print("   1. Open Proton Mail Bridge GUI")
        print("   2. Complete login")
        print("   3. Run the setup script")

if __name__ == "__main__":
    main()
