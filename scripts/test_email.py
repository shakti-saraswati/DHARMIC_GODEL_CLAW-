#!/usr/bin/env python3
"""
Proton Bridge Email Test
========================

Test sending and receiving email via Proton Bridge.
Fixed for STARTTLS (not direct SSL).
"""

import os
import ssl
import imaplib
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path.home() / "DHARMIC_GODEL_CLAW/.env"
load_dotenv(env_path)

def create_ssl_context():
    """Create SSL context that accepts Proton Bridge self-signed cert."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def test_imap():
    """Test IMAP connection (receiving)."""
    print("📥 Testing IMAP (receiving)...")
    
    try:
        # Proton Bridge IMAP uses STARTTLS on port 1143
        mail = imaplib.IMAP4(os.getenv('IMAP_SERVER', '127.0.0.1'), 
                             int(os.getenv('IMAP_PORT', '1143')))
        
        # Start TLS
        context = create_ssl_context()
        mail.starttls(ssl_context=context)
        
        # Login
        mail.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
        
        # Select inbox
        mail.select('inbox')
        
        # Get unread count
        status, messages = mail.search(None, 'UNSEEN')
        unread = len(messages[0].split()) if status == 'OK' and messages[0] else 0
        
        # Get total count
        status, messages = mail.search(None, 'ALL')
        total = len(messages[0].split()) if status == 'OK' and messages[0] else 0
        
        print("   ✅ Connected to IMAP")
        print(f"   📧 Total emails: {total}")
        print(f"   📧 Unread: {unread}")
        
        mail.logout()
        return True
        
    except Exception as e:
        print(f"   ❌ IMAP failed: {e}")
        return False

def test_smtp():
    """Test SMTP connection (sending)."""
    print("📤 Testing SMTP (sending)...")
    
    try:
        # Proton Bridge SMTP uses STARTTLS on port 1025
        server = smtplib.SMTP(os.getenv('SMTP_SERVER', '127.0.0.1'),
                              int(os.getenv('SMTP_PORT', '1025')),
                              timeout=10)
        
        server.ehlo()
        
        # Start TLS
        context = create_ssl_context()
        server.starttls(context=context)
        
        server.ehlo()
        
        # Login
        server.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
        
        print("   ✅ Connected to SMTP")
        server.quit()
        return True
        
    except Exception as e:
        print(f"   ❌ SMTP failed: {e}")
        return False

def send_test_email(to_address=None):
    """Send a test email."""
    print("\n📤 Sending test email...")
    
    from_addr = os.getenv('EMAIL_ADDRESS')
    to_addr = to_address or from_addr  # Default to self
    
    try:
        # Create message
        msg = MIMEText("This is a test email from DHARMIC CLAW.\n\nIf you received this, Proton Bridge is working!")
        msg['Subject'] = 'DHARMIC CLAW - Test Email'
        msg['From'] = from_addr
        msg['To'] = to_addr
        
        # Connect and send
        server = smtplib.SMTP(os.getenv('SMTP_SERVER', '127.0.0.1'),
                              int(os.getenv('SMTP_PORT', '1025')),
                              timeout=10)
        server.ehlo()
        
        context = create_ssl_context()
        server.starttls(context=context)
        
        server.login(from_addr, os.getenv('EMAIL_PASSWORD'))
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
        
        print(f"   ✅ Test email sent to {to_addr}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to send: {e}")
        return False

def main():
    print("=" * 60)
    print("Proton Bridge Email Test")
    print("=" * 60)
    print(f"Account: {os.getenv('EMAIL_ADDRESS', 'NOT SET')}")
    print()
    
    # Test connections
    imap_ok = test_imap()
    smtp_ok = test_smtp()
    
    print()
    if imap_ok and smtp_ok:
        print("✅ Email fully operational!")
        
        # Ask to send test
        response = input("\nSend test email? (y/n): ").lower()
        if response == 'y':
            to = input(f"To address [default: {os.getenv('EMAIL_ADDRESS')}]: ").strip()
            if not to:
                to = os.getenv('EMAIL_ADDRESS')
            send_test_email(to)
    else:
        print("⚠️  Email partially working:")
        if smtp_ok:
            print("   - Can SEND emails")
        if imap_ok:
            print("   - Can RECEIVE emails")
        print("\nCheck Proton Bridge GUI for errors.")

if __name__ == "__main__":
    main()
