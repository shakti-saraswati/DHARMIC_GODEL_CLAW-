"""
Dharmic Agent - Email Interface

Simple IMAP/SMTP integration for email-based interaction.
The agent checks for new emails, processes them, and responds.

Setup:
1. Set environment variables:
   - DHARMIC_EMAIL_ADDRESS=your-email@gmail.com
   - DHARMIC_EMAIL_PASSWORD=your-app-password
   - DHARMIC_EMAIL_IMAP=imap.gmail.com
   - DHARMIC_EMAIL_SMTP=smtp.gmail.com

2. For Gmail, create an App Password:
   - Go to Google Account → Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"

3. Run: python3 email_interface.py
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import os
import asyncio
from pathlib import Path
from typing import List, Dict

# Import the dharmic agent
import sys
sys.path.insert(0, str(Path(__file__).parent))
from dharmic_agent import DharmicAgent


class EmailInterface:
    """
    Email interface for the Dharmic Agent.
    
    Polls inbox for new messages, processes them through the agent,
    and sends responses.
    """
    
    def __init__(
        self,
        agent: DharmicAgent,
        email_address: str = None,
        email_password: str = None,
        imap_server: str = None,
        smtp_server: str = None,
        check_interval: int = 60,  # seconds
        allowed_senders: List[str] = None,  # Whitelist (security)
    ):
        self.agent = agent
        
        # Email config from env or params
        self.email_address = email_address or os.getenv("DHARMIC_EMAIL_ADDRESS")
        self.email_password = email_password or os.getenv("DHARMIC_EMAIL_PASSWORD")
        self.imap_server = imap_server or os.getenv("DHARMIC_EMAIL_IMAP", "imap.gmail.com")
        self.smtp_server = smtp_server or os.getenv("DHARMIC_EMAIL_SMTP", "smtp.gmail.com")
        
        self.check_interval = check_interval
        self.allowed_senders = allowed_senders or []
        
        # Track processed emails
        self.processed_ids: set = set()
        
        # Validate config
        if not self.email_address or not self.email_password:
            raise ValueError(
                "Email credentials required. Set DHARMIC_EMAIL_ADDRESS and DHARMIC_EMAIL_PASSWORD"
            )
    
    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server."""
        imap = imaplib.IMAP4_SSL(self.imap_server)
        imap.login(self.email_address, self.email_password)
        return imap
    
    def _connect_smtp(self) -> smtplib.SMTP_SSL:
        """Connect to SMTP server."""
        smtp = smtplib.SMTP_SSL(self.smtp_server, 465)
        smtp.login(self.email_address, self.email_password)
        return smtp
    
    def _decode_subject(self, subject) -> str:
        """Decode email subject."""
        if subject is None:
            return ""
        decoded = decode_header(subject)
        result = ""
        for part, encoding in decoded:
            if isinstance(part, bytes):
                result += part.decode(encoding or 'utf-8', errors='replace')
            else:
                result += part
        return result
    
    def _get_email_body(self, msg) -> str:
        """Extract plain text body from email."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
        
        return body.strip()
    
    def check_inbox(self) -> List[Dict]:
        """
        Check inbox for new unread emails.
        
        Returns list of email dicts with: id, from, subject, body, date
        """
        new_emails = []
        
        try:
            imap = self._connect_imap()
            imap.select("INBOX")
            
            # Search for unread emails
            status, messages = imap.search(None, "UNSEEN")
            
            if status != "OK":
                return new_emails
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                # Skip if already processed
                if email_id in self.processed_ids:
                    continue
                
                # Fetch email
                status, msg_data = imap.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract fields
                from_addr = msg.get("From", "")
                subject = self._decode_subject(msg.get("Subject", ""))
                body = self._get_email_body(msg)
                date = msg.get("Date", "")
                
                # Extract just the email address from "Name <email>" format
                if "<" in from_addr and ">" in from_addr:
                    sender_email = from_addr.split("<")[1].split(">")[0]
                else:
                    sender_email = from_addr
                
                # Security: Check whitelist if configured
                if self.allowed_senders:
                    if sender_email.lower() not in [s.lower() for s in self.allowed_senders]:
                        print(f"Ignoring email from non-whitelisted sender: {sender_email}")
                        self.processed_ids.add(email_id)
                        continue
                
                new_emails.append({
                    "id": email_id,
                    "from": from_addr,
                    "sender_email": sender_email,
                    "subject": subject,
                    "body": body,
                    "date": date
                })
                
                self.processed_ids.add(email_id)
            
            imap.close()
            imap.logout()
            
        except Exception as e:
            print(f"Error checking inbox: {e}")
        
        return new_emails
    
    def send_response(self, to_addr: str, subject: str, body: str):
        """Send email response."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_addr
            msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
            
            # Add body
            msg.attach(MIMEText(body, "plain"))
            
            # Send
            smtp = self._connect_smtp()
            smtp.send_message(msg)
            smtp.quit()
            
            print(f"Sent response to {to_addr}")
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def process_email(self, email_data: Dict) -> str:
        """
        Process an email through the Dharmic Agent.
        
        Returns the response text.
        """
        # Build the message for the agent
        message = f"""
[EMAIL FROM: {email_data['from']}]
[SUBJECT: {email_data['subject']}]
[DATE: {email_data['date']}]

{email_data['body']}
"""
        
        # Record as observation
        self.agent.strange_memory.record_observation(
            content=f"Email from {email_data['sender_email']}: {email_data['subject'][:100]}",
            context={"type": "email", "from": email_data['sender_email']}
        )
        
        # Get response from agent
        response = self.agent.run(
            message,
            session_id=f"email_{email_data['sender_email']}"
        )
        
        # Add signature
        response += "\n\n---\nDharmic Agent Core\nTelos: moksha"
        
        return response
    
    async def run_loop(self):
        """
        Main loop: check inbox, process emails, send responses.
        """
        print(f"Starting email interface for {self.email_address}")
        print(f"Check interval: {self.check_interval}s")
        if self.allowed_senders:
            print(f"Allowed senders: {self.allowed_senders}")
        print()
        
        while True:
            try:
                # Check for new emails
                new_emails = self.check_inbox()
                
                if new_emails:
                    print(f"Found {len(new_emails)} new email(s)")
                
                for email_data in new_emails:
                    print(f"\nProcessing: {email_data['subject']}")
                    print(f"  From: {email_data['from']}")
                    
                    # Process through agent
                    response = self.process_email(email_data)
                    
                    # Send response
                    self.send_response(
                        to_addr=email_data['sender_email'],
                        subject=email_data['subject'],
                        body=response
                    )
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\nStopping email interface...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                await asyncio.sleep(self.check_interval)


# CLI
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dharmic Agent Email Interface")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--whitelist",
        type=str,
        nargs="+",
        help="Allowed sender emails (security whitelist)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: check inbox once and exit"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DHARMIC AGENT - Email Interface")
    print("=" * 60)
    
    # Check env vars
    if not os.getenv("DHARMIC_EMAIL_ADDRESS"):
        print("\nERROR: Set environment variables:")
        print("  export DHARMIC_EMAIL_ADDRESS=your-email@gmail.com")
        print("  export DHARMIC_EMAIL_PASSWORD=your-app-password")
        print("  export ANTHROPIC_API_KEY=your-api-key")
        return
    
    # Create agent
    agent = DharmicAgent()
    print(f"Agent: {agent.name}")
    print(f"Telos: {agent.telos.telos['ultimate']['aim']}")
    
    # Create email interface
    interface = EmailInterface(
        agent=agent,
        check_interval=args.interval,
        allowed_senders=args.whitelist
    )
    
    if args.test:
        # Test mode
        print("\n--- Test Mode: Checking inbox ---")
        emails = interface.check_inbox()
        print(f"Found {len(emails)} unread emails")
        for e in emails:
            print(f"  - From: {e['from']}")
            print(f"    Subject: {e['subject']}")
        return
    
    # Run main loop
    await interface.run_loop()


if __name__ == "__main__":
    asyncio.run(main())
