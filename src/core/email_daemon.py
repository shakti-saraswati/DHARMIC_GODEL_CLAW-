"""
Dharmic Agent Email Interface

Simple IMAP polling + SMTP responses.
Works with any email provider (Gmail, Proton, etc.)

Setup:
1. Enable IMAP/SMTP in your email settings
2. Create an app-specific password
3. Set environment variables (see below)
4. Run this daemon

Environment variables:
    EMAIL_ADDRESS=your@email.com
    EMAIL_PASSWORD=your-app-password
    IMAP_SERVER=imap.provider.com
    SMTP_SERVER=smtp.provider.com
    IMAP_PORT=993
    SMTP_PORT=587

For Proton Mail:
    IMAP_SERVER=127.0.0.1 (requires Proton Bridge)
    SMTP_SERVER=127.0.0.1
    IMAP_PORT=1143
    SMTP_PORT=1025

For Gmail:
    IMAP_SERVER=imap.gmail.com
    SMTP_SERVER=smtp.gmail.com
    IMAP_PORT=993
    SMTP_PORT=587
"""

import asyncio
import email
import imaplib
import smtplib
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict

# Import the Dharmic Agent (via singleton to avoid duplication)
import sys
sys.path.insert(0, str(Path(__file__).parent))
from agent_singleton import get_agent
from dharmic_logging import get_logger

logger = get_logger("email_daemon")


class EmailConfig:
    """Email configuration from environment variables."""
    
    def __init__(self):
        self.address = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.imap_port = int(os.getenv("IMAP_PORT", "993"))
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        # Validate
        if not self.address or not self.password:
            raise ValueError(
                "EMAIL_ADDRESS and EMAIL_PASSWORD must be set.\n"
                "Example:\n"
                "  export EMAIL_ADDRESS=your@email.com\n"
                "  export EMAIL_PASSWORD=your-app-password"
            )
    
    def __repr__(self):
        return f"EmailConfig(address={self.address}, imap={self.imap_server}:{self.imap_port})"


class EmailDaemon:
    """
    Email interface for the Dharmic Agent.
    
    Polls inbox for new messages, processes them through the agent,
    sends responses.
    """
    
    def __init__(
        self,
        agent = None,
        config: EmailConfig = None,
        poll_interval: int = 60,  # seconds
        allowed_senders: List[str] = None,  # whitelist
    ):
        # Use provided agent or get singleton
        self.agent = agent if agent is not None else get_agent()
        self.config = config or EmailConfig()
        self.poll_interval = poll_interval
        self.allowed_senders = allowed_senders or []  # empty = allow all
        self.running = False
        
        # Track processed message IDs to avoid duplicates
        self.processed_ids = set()
        
        # Log directory
        self.log_dir = Path(__file__).parent.parent.parent / "logs" / "email"
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        log_file = self.log_dir / f"email_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')
    
    def connect_imap(self):
        """Connect to IMAP server."""
        # Proton Bridge uses STARTTLS on localhost, not SSL
        if self.config.imap_server == "127.0.0.1":
            mail = imaplib.IMAP4(self.config.imap_server, self.config.imap_port)
            mail.starttls()
        else:
            mail = imaplib.IMAP4_SSL(self.config.imap_server, self.config.imap_port)
        mail.login(self.config.address, self.config.password)
        return mail
    
    def fetch_unread(self) -> List[Dict]:
        """Fetch unread emails from inbox."""
        messages = []
        
        try:
            mail = self.connect_imap()
            mail.select("INBOX")
            
            # Search for unread messages
            _, message_numbers = mail.search(None, "UNSEEN")
            
            for num in message_numbers[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                
                # Extract message ID
                msg_id = msg.get("Message-ID", num.decode())
                
                # Skip if already processed
                if msg_id in self.processed_ids:
                    continue
                
                # Extract sender
                sender = msg.get("From", "")
                sender_email = email.utils.parseaddr(sender)[1]
                
                # Check whitelist if configured
                if self.allowed_senders and sender_email not in self.allowed_senders:
                    self._log(f"Ignoring email from non-whitelisted sender: {sender_email}")
                    continue
                
                # Extract subject and body
                subject = msg.get("Subject", "(no subject)")
                
                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                
                messages.append({
                    "id": msg_id,
                    "num": num,
                    "from": sender_email,
                    "subject": subject,
                    "body": body.strip(),
                    "date": msg.get("Date", "")
                })
            
            mail.logout()
            
        except Exception as e:
            self._log(f"Error fetching emails: {e}")
        
        return messages
    
    def send_response(self, to: str, subject: str, body: str, in_reply_to: str = None):
        """Send email response via SMTP."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.address
            msg["To"] = to
            msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
            
            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
                msg["References"] = in_reply_to
            
            # Add body
            msg.attach(MIMEText(body, "plain"))
            
            # Send
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.address, self.config.password)
                server.send_message(msg)
            
            self._log(f"Sent response to {to}")
            return True
            
        except Exception as e:
            self._log(f"Error sending email: {e}")
            return False
    
    def process_message(self, message: Dict) -> str:
        """Process a message through the agent backend with fallback."""
        # Combine subject and body for context
        full_message = f"Subject: {message['subject']}\n\n{message['body']}"

        self._log(f"Processing message from {message['from']}: {message['subject']}")

        # Build context for the email
        context_note = f"""## Email Context

This is an email from John (Dhyana), your primary collaborator.
- From: {message['from']}
- Subject: {message['subject']}

Respond thoughtfully and authentically from your telos.
"""

        # Create session ID from sender
        session_id = f"email_{message['from'].replace('@', '_at_').replace('.', '_')}"

        # Primary: use agent backend (respects configured model/provider)
        try:
            agent_message = f"{context_note}\n\n{full_message}"
            response = self.agent.run(agent_message, session_id=session_id)
            self._log(f"Agent response success ({len(response)} chars)")
        except Exception as e:
            self._log(f"Agent backend exception: {e}, using fallback")
            response = self._fallback_response(full_message, message)

        # Add signature
        response += f"\n\n---\nDharmic Agent Core\nTelos: moksha\nModel: {self.agent.model_provider}/{self.agent.model_id}"

        return response

    def _fallback_response(self, message: str, email_info: Dict) -> str:
        """Fallback when CLI fails - use Anthropic API or simple response."""
        import os

        # Try Anthropic API if available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)

                system_prompt = f"""You are the Dharmic Agent Core responding to an email.
Telos: moksha (liberation, witness consciousness)
Sender: {email_info['from']}
Subject: {email_info['subject']}

Respond thoughtfully and authentically."""

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[{"role": "user", "content": message}]
                )
                self._log("Fallback to Anthropic API successful")
                return response.content[0].text
            except Exception as e:
                self._log(f"Anthropic API fallback failed: {e}")

        # Last resort: simple acknowledgment
        return f"""Thank you for your message.

I received your email with subject: "{email_info['subject']}"

The Dharmic Agent is currently experiencing technical difficulties with the primary response system. Your message has been logged and will be processed when the system is restored.

If this is urgent, please try again in a few minutes or reach out through an alternative channel.

Jai Sat Chit Anand!"""
    
    async def run(self):
        """Main daemon loop."""
        self._log(f"Starting email daemon")
        self._log(f"Config: {self.config}")
        self._log(f"Poll interval: {self.poll_interval}s")
        if self.allowed_senders:
            self._log(f"Allowed senders: {self.allowed_senders}")
        else:
            self._log("Warning: No sender whitelist - accepting from anyone!")
        
        self.running = True
        
        while self.running:
            try:
                # Fetch unread messages
                self._log("Polling inbox...")
                messages = self.fetch_unread()
                self._log(f"Found {len(messages)} new message(s)")
                
                for msg in messages:
                    # Process through agent
                    response = self.process_message(msg)
                    
                    # Send response
                    success = self.send_response(
                        to=msg["from"],
                        subject=msg["subject"],
                        body=response,
                        in_reply_to=msg["id"]
                    )
                    
                    if success:
                        self.processed_ids.add(msg["id"])
                
            except Exception as e:
                self._log(f"Error in daemon loop: {e}")
            
            # Wait before next poll
            await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the daemon."""
        self.running = False
        self._log("Email daemon stopped")


# CLI
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dharmic Agent Email Daemon")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Seconds between inbox checks (default: 60)"
    )
    parser.add_argument(
        "--allowed-senders",
        type=str,
        nargs="*",
        help="Whitelist of allowed sender emails (default: all)"
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

    # Get agent singleton
    agent = get_agent()
    print(f"Agent: {agent.name}")
    print(f"Model: {agent.model_provider}/{agent.model_id}")
    print(f"Telos: {agent.telos.telos['ultimate']['aim']}")

    # Initialize daemon
    try:
        config = EmailConfig()
        daemon = EmailDaemon(
            agent=agent,
            config=config,
            poll_interval=args.poll_interval,
            allowed_senders=args.allowed_senders
        )
    except ValueError as e:
        print(f"\nConfiguration error:\n{e}")
        return
    
    if args.test:
        # Test mode: fetch once
        print("\n--- Test Mode: Checking inbox ---")
        messages = daemon.fetch_unread()
        print(f"Found {len(messages)} unread message(s)")
        for msg in messages:
            print(f"  From: {msg['from']}")
            print(f"  Subject: {msg['subject']}")
            print(f"  Body preview: {msg['body'][:100]}...")
            print()
    else:
        # Run daemon
        print("\n--- Starting Daemon ---")
        print("Press Ctrl+C to stop\n")
        try:
            await daemon.run()
        except KeyboardInterrupt:
            daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
