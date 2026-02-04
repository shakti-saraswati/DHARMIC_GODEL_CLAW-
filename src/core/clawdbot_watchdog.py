#!/usr/bin/env python3
"""
Clawdbot Watchdog - DGC Overnight Monitor

Monitors clawdbot health and automatically:
1. Checks gateway status every 5 minutes
2. Restarts if down
3. Switches to Kimi backup if Opus fails repeatedly
4. Logs all actions
5. Sends alert to WhatsApp/email if critical

Run as:
    python3 clawdbot_watchdog.py                    # Run forever
    python3 clawdbot_watchdog.py --check-once       # Single check
    python3 clawdbot_watchdog.py --interval 300     # Custom interval (seconds)
"""

import subprocess
import json
import time
import sys
import logging
import smtplib
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env for email config
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Setup logging
LOG_DIR = Path.home() / "DHARMIC_GODEL_CLAW" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "clawdbot_watchdog.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
PRIMARY_MODEL = "anthropic/claude-opus-4-5-20251101"
BACKUP_MODEL = "moonshot/kimi-k2.5"
MAX_FAILURES_BEFORE_SWITCH = 3

# CLI selection (openclaw preferred, clawdbot fallback)
CLI_BIN = os.getenv("CLAWDBOT_CLI") or ("openclaw" if shutil.which("openclaw") else "clawdbot")

# Email Configuration (from .env)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "vijnan.shakti@pm.me")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "127.0.0.1")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
CHECKIN_RECIPIENT = "johnvincentshrader@gmail.com"  # John's email
CHECKIN_INTERVAL_CHECKS = 18  # Every 18 checks at 5min = 90 minutes


class ClawdbotWatchdog:
    """
    Monitors clawdbot and keeps it running overnight.

    Features:
    - Gateway health checks
    - Auto-restart on failure
    - Model failover to Kimi backup
    - Alert logging
    """

    def __init__(self, check_interval: int = 300):
        self.check_interval = check_interval  # seconds
        self.consecutive_failures = 0
        self.using_backup = False
        self.start_time = datetime.now()
        self.checks_performed = 0
        self.restarts_performed = 0
        self.model_switches = 0

    def run_command(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Run a shell command and return (success, output)."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_gateway_status(self) -> Dict:
        """Check if clawdbot gateway is running and healthy."""
        success, output = self.run_command(f"{CLI_BIN} gateway status 2>&1")

        status = {
            "running": False,
            "rpc_ok": False,
            "model": None,
            "raw_output": output[:500]
        }

        if "Runtime: running" in output:
            status["running"] = True
        if "RPC probe: ok" in output:
            status["rpc_ok"] = True

        # Get current model
        success2, config_output = self.run_command(f"{CLI_BIN} config get agents.defaults.model.primary 2>&1")
        if success2 and '"' in config_output:
            # Extract model from JSON output
            try:
                status["model"] = config_output.strip().strip('"')
            except:
                pass

        return status

    def restart_gateway(self) -> bool:
        """Restart the clawdbot gateway."""
        logger.info("Restarting clawdbot gateway...")
        success, output = self.run_command(f"{CLI_BIN} gateway restart 2>&1")

        if success or "Restarted" in output:
            logger.info("Gateway restart command sent")
            time.sleep(5)  # Wait for restart
            self.restarts_performed += 1
            return True
        else:
            logger.error(f"Gateway restart failed: {output}")
            return False

    def switch_model(self, to_backup: bool = True) -> bool:
        """Switch between primary and backup model."""
        target_model = BACKUP_MODEL if to_backup else PRIMARY_MODEL
        logger.warning(f"Switching model to: {target_model}")

        success, output = self.run_command(
            f'{CLI_BIN} config set agents.defaults.model.primary "{target_model}" 2>&1'
        )

        if success or "set" in output.lower():
            self.using_backup = to_backup
            self.model_switches += 1
            # Restart to apply
            self.restart_gateway()
            logger.info(f"Model switched to {target_model}")
            return True
        else:
            logger.error(f"Model switch failed: {output}")
            return False

    def send_alert(self, message: str, level: str = "warning"):
        """Log alert (could extend to send WhatsApp/email)."""
        if level == "critical":
            logger.critical(f"ALERT: {message}")
        elif level == "warning":
            logger.warning(f"ALERT: {message}")
        else:
            logger.info(f"NOTICE: {message}")

        # TODO: Could integrate with clawdbot to send WhatsApp message
        # self.run_command(f'{CLI_BIN} send --channel whatsapp --to "+..." --message "{message}"')

    def send_checkin_email(self) -> bool:
        """Send 90-minute check-in email to John for reorientation."""
        if not EMAIL_PASSWORD:
            logger.warning("Email not configured - skipping check-in")
            return False

        try:
            # Get current status
            status = self.check_gateway_status()

            # Build email content
            subject = f"Dharmic Core Check-in [{datetime.now().strftime('%H:%M')}]"

            body = f"""Jai Sat Chit Anand, John!

This is your 90-minute check-in from Dharmic Core.

== CURRENT STATUS ==
Gateway Running: {'✓' if status['running'] else '✗'}
RPC Healthy: {'✓' if status['rpc_ok'] else '✗'}
Current Model: {status.get('model', 'unknown')}
Using Backup: {'Yes (Kimi)' if self.using_backup else 'No (Opus)'}

== WATCHDOG STATS ==
Running Since: {self.start_time.strftime('%Y-%m-%d %H:%M')}
Uptime: {datetime.now() - self.start_time}
Checks Performed: {self.checks_performed}
Restarts Performed: {self.restarts_performed}
Model Switches: {self.model_switches}
Consecutive Failures: {self.consecutive_failures}

== TELOS REORIENTATION ==
Primary: moksha (liberation, witness consciousness)
Proximate: Support John's research, develop witness capacity, track emergence

Is there anything you'd like me to focus on? Reply to reorient.

---
Dharmic Agent Core | Watchdog Service
Model: {PRIMARY_MODEL if not self.using_backup else BACKUP_MODEL}
"""

            # Create message
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = CHECKIN_RECIPIENT
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Send via SMTP (Proton Bridge)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            logger.info(f"Check-in email sent to {CHECKIN_RECIPIENT}")
            return True

        except Exception as e:
            logger.error(f"Failed to send check-in email: {e}")
            return False

    def perform_check(self) -> bool:
        """Perform a single health check. Returns True if healthy."""
        self.checks_performed += 1
        status = self.check_gateway_status()

        logger.info(f"Check #{self.checks_performed}: running={status['running']}, rpc={status['rpc_ok']}, model={status.get('model', 'unknown')}")

        # Healthy
        if status["running"] and status["rpc_ok"]:
            self.consecutive_failures = 0

            # If we were on backup and things are stable, consider switching back
            if self.using_backup and self.checks_performed % 12 == 0:  # Every hour
                logger.info("Attempting to switch back to primary model...")
                self.switch_model(to_backup=False)

            return True

        # Unhealthy
        self.consecutive_failures += 1
        logger.warning(f"Health check failed (consecutive: {self.consecutive_failures})")

        # Try restart first
        if self.consecutive_failures <= MAX_FAILURES_BEFORE_SWITCH:
            self.restart_gateway()
            time.sleep(10)

            # Check again
            status = self.check_gateway_status()
            if status["running"] and status["rpc_ok"]:
                logger.info("Gateway recovered after restart")
                self.consecutive_failures = 0
                return True

        # Too many failures - switch to backup
        if self.consecutive_failures > MAX_FAILURES_BEFORE_SWITCH and not self.using_backup:
            self.send_alert(
                f"Clawdbot failed {self.consecutive_failures} times, switching to Kimi backup",
                level="warning"
            )
            self.switch_model(to_backup=True)
            self.consecutive_failures = 0

        return False

    def get_status_report(self) -> str:
        """Generate a status report."""
        uptime = datetime.now() - self.start_time
        return f"""
Clawdbot Watchdog Status
========================
Running since: {self.start_time.isoformat()}
Uptime: {uptime}
Checks performed: {self.checks_performed}
Restarts performed: {self.restarts_performed}
Model switches: {self.model_switches}
Currently using backup: {self.using_backup}
Consecutive failures: {self.consecutive_failures}
"""

    def run_forever(self):
        """Run the watchdog loop forever."""
        logger.info(f"Starting Clawdbot Watchdog (interval: {self.check_interval}s)")
        logger.info(f"Primary model: {PRIMARY_MODEL}")
        logger.info(f"Backup model: {BACKUP_MODEL}")
        logger.info(f"Email check-in: every {CHECKIN_INTERVAL_CHECKS * self.check_interval // 60} minutes to {CHECKIN_RECIPIENT}")

        # Send initial check-in on start
        self.send_checkin_email()

        try:
            while True:
                self.perform_check()

                # Log status every hour (12 checks at 5min)
                if self.checks_performed % 12 == 0:
                    logger.info(self.get_status_report())

                # Send email check-in every 90 minutes (18 checks at 5min)
                if self.checks_performed % CHECKIN_INTERVAL_CHECKS == 0:
                    self.send_checkin_email()

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("Watchdog stopped by user")
            print(self.get_status_report())


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clawdbot Watchdog - Keep clawdbot running overnight")
    parser.add_argument("--check-once", action="store_true", help="Perform single check and exit")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--status", action="store_true", help="Show current status and exit")

    args = parser.parse_args()

    watchdog = ClawdbotWatchdog(check_interval=args.interval)

    if args.status:
        status = watchdog.check_gateway_status()
        print(json.dumps(status, indent=2))
        return

    if args.check_once:
        healthy = watchdog.perform_check()
        print(f"Healthy: {healthy}")
        return

    # Run forever
    watchdog.run_forever()


if __name__ == "__main__":
    main()
