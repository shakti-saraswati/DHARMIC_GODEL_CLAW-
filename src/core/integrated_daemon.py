"""
Dharmic Agent - Integrated Daemon

Combines all interfaces and capabilities:
- Email monitoring
- Telegram bot
- Web dashboard
- Scheduled tasks (morning reflection, vault exploration, etc.)
- Heartbeat monitoring
- Voice input support

This is the "full presence" mode - the agent running 24/7 with all interfaces active.

Usage:
    python3 integrated_daemon.py --all
    python3 integrated_daemon.py --email --telegram --web
    python3 integrated_daemon.py --config daemon_config.yaml

Philosophy: Presence over performance. The agent is always available,
            but operates from telos, not from urgency.
"""

import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import argparse
import yaml
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Import Dharmic components
sys.path.insert(0, str(Path(__file__).parent))
from dharmic_agent import DharmicAgent
from runtime import DharmicRuntime
from scheduled_tasks import ScheduledTasks

# Optional interfaces
try:
    from email_daemon import EmailDaemon, EmailConfig
    EMAIL_AVAILABLE = True
except Exception as e:
    EMAIL_AVAILABLE = False
    print(f"Email interface unavailable: {e}")

try:
    from telegram_bot import DharmicTelegramBot, TelegramConfig
    TELEGRAM_AVAILABLE = True
except Exception as e:
    TELEGRAM_AVAILABLE = False
    print(f"Telegram interface unavailable: {e}")

try:
    from web_dashboard import app as dashboard_app, init_agent as init_dashboard_agent
    from flask import Flask
    import threading
    WEB_AVAILABLE = True
except Exception as e:
    WEB_AVAILABLE = False
    print(f"Web dashboard unavailable: {e}")


class DaemonConfig:
    """Configuration for the integrated daemon."""

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep-merge override into base (mutates base)."""
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _load_config(self, config_file: Optional[str]) -> dict:
        """Load configuration from YAML file."""
        default_config = {
            "agent": {
                "name": "Dharmic Core",
                "heartbeat_interval": 3600,  # 1 hour
                "subagents": {
                    "thinking": "auto"
                }
            },
            "interfaces": {
                "email": {
                    "enabled": False,
                    "poll_interval": 60,
                    "allowed_senders": []
                },
                "telegram": {
                    "enabled": False,
                    "allowed_users": []
                },
                "web": {
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": 5000
                }
            },
            "scheduled_tasks": {
                "enabled": True,
                "morning_reflection": True,
                "vault_exploration": True,
                "memory_consolidation": True,
                "alignment_check": True,
                "pattern_meta": True
            }
        }

        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path) as f:
                    user_config = yaml.safe_load(f) or {}
                # Merge with defaults (deep)
                default_config = self._deep_merge(default_config, user_config)

        return default_config

    def save_template(self, path: str):
        """Save a template configuration file."""
        template = {
            "agent": {
                "name": "Dharmic Core",
                "heartbeat_interval": 3600,
                "subagents": {
                    "thinking": "auto"
                }
            },
            "interfaces": {
                "email": {
                    "enabled": False,
                    "poll_interval": 60,
                    "allowed_senders": ["john@example.com"]
                },
                "telegram": {
                    "enabled": False,
                    "allowed_users": ["123456789"]
                },
                "web": {
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": 5000
                }
            },
            "scheduled_tasks": {
                "enabled": True,
                "morning_reflection": True,
                "vault_exploration": True,
                "memory_consolidation": True,
                "alignment_check": True,
                "pattern_meta": True
            }
        }

        with open(path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)

        print(f"Template configuration saved to: {path}")


class IntegratedDaemon:
    """
    The integrated daemon - all interfaces running together.

    This is the "full presence" mode of the Dharmic Agent.
    """

    def __init__(self, config: DaemonConfig):
        self.config = config.config
        self.running = False

        # Log directory
        self.log_dir = Path(__file__).parent.parent.parent / "logs" / "daemon"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize core agent
        print("Initializing Dharmic Agent Core...")
        self.agent = DharmicAgent(
            name=self.config["agent"]["name"],
            subagent_thinking=self.config["agent"].get("subagents", {}).get("thinking"),
        )

        # Initialize runtime
        print("Initializing Runtime...")
        self.runtime = DharmicRuntime(
            agent=self.agent,
            heartbeat_interval=self.config["agent"]["heartbeat_interval"]
        )

        # Initialize scheduled tasks
        self.scheduled_tasks = None
        if self.config["scheduled_tasks"]["enabled"]:
            print("Initializing Scheduled Tasks...")
            self.scheduled_tasks = ScheduledTasks(agent=self.agent)

        # Interface components
        self.email_daemon = None
        self.telegram_bot = None
        self.web_thread = None

        # Tasks
        self.email_task = None
        self.telegram_task = None

    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)

        log_file = self.log_dir / f"daemon_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')

    async def start(self):
        """Start all configured interfaces."""
        self._log("=" * 60)
        self._log("DHARMIC AGENT - Integrated Daemon Starting")
        self._log("=" * 60)
        self._log(f"Agent: {self.agent.name}")
        self._log(f"Telos: {self.agent.telos.telos['ultimate']['aim']}")
        self._log("=" * 60)

        self.running = True

        # Start runtime
        email_config = self.config["interfaces"]["email"]
        await self.runtime.start(
            enable_email=False,  # We'll handle email separately
            email_whitelist=email_config.get("allowed_senders", [])
        )

        # Start scheduled tasks
        if self.scheduled_tasks:
            task_config = self.config["scheduled_tasks"]
            self.scheduled_tasks.start(
                enable_morning_reflection=task_config.get("morning_reflection", True),
                enable_vault_exploration=task_config.get("vault_exploration", True),
                enable_memory_consolidation=task_config.get("memory_consolidation", True),
                enable_alignment_check=task_config.get("alignment_check", True),
                enable_pattern_meta=task_config.get("pattern_meta", True)
            )
            self._log("Scheduled tasks started")

        # Start email interface
        if self.config["interfaces"]["email"]["enabled"]:
            await self._start_email()

        # Start Telegram bot
        if self.config["interfaces"]["telegram"]["enabled"]:
            await self._start_telegram()

        # Start web dashboard
        if self.config["interfaces"]["web"]["enabled"]:
            self._start_web()

        self._log("=" * 60)
        self._log("All interfaces started - Daemon running")
        self._log("Press Ctrl+C to stop")
        self._log("=" * 60)

        # Record in memory
        self.agent.strange_memory.record_observation(
            content="Integrated daemon started - full presence mode",
            context={"interfaces": self._get_active_interfaces()}
        )

    async def _start_email(self):
        """Start email interface."""
        if not EMAIL_AVAILABLE:
            self._log("Email interface not available (dependencies missing)")
            return

        try:
            email_config = self.config["interfaces"]["email"]
            config = EmailConfig()

            self.email_daemon = EmailDaemon(
                agent=self.agent,
                config=config,
                poll_interval=email_config.get("poll_interval", 60),
                allowed_senders=email_config.get("allowed_senders", [])
            )

            # Start as background task
            self.email_task = asyncio.create_task(self.email_daemon.run())
            self._log(f"Email interface started ({config.address})")

        except Exception as e:
            self._log(f"Failed to start email interface: {e}")

    async def _start_telegram(self):
        """Start Telegram bot."""
        if not TELEGRAM_AVAILABLE:
            self._log("Telegram interface not available (dependencies missing)")
            return

        try:
            telegram_config = self.config["interfaces"]["telegram"]
            config = TelegramConfig()

            # Override allowed users from config if provided
            if telegram_config.get("allowed_users"):
                config.allowed_users = telegram_config["allowed_users"]

            self.telegram_bot = DharmicTelegramBot(
                agent=self.agent,
                config=config
            )

            # Start as background task
            self.telegram_task = asyncio.create_task(
                asyncio.to_thread(self.telegram_bot.run)
            )
            self._log("Telegram bot started")

        except Exception as e:
            self._log(f"Failed to start Telegram bot: {e}")

    def _start_web(self):
        """Start web dashboard in separate thread."""
        if not WEB_AVAILABLE:
            self._log("Web dashboard not available (dependencies missing)")
            return

        try:
            web_config = self.config["interfaces"]["web"]

            # Initialize dashboard agent
            init_dashboard_agent()

            # Run Flask in separate thread
            def run_flask():
                dashboard_app.run(
                    host=web_config.get("host", "127.0.0.1"),
                    port=web_config.get("port", 5000),
                    debug=False,
                    use_reloader=False
                )

            self.web_thread = threading.Thread(target=run_flask, daemon=True)
            self.web_thread.start()

            self._log(f"Web dashboard started at http://{web_config.get('host', '127.0.0.1')}:{web_config.get('port', 5000)}")

        except Exception as e:
            self._log(f"Failed to start web dashboard: {e}")

    def _get_active_interfaces(self) -> List[str]:
        """Get list of active interfaces."""
        interfaces = []
        if self.email_daemon:
            interfaces.append("email")
        if self.telegram_bot:
            interfaces.append("telegram")
        if self.web_thread and self.web_thread.is_alive():
            interfaces.append("web")
        return interfaces

    async def stop(self):
        """Stop all interfaces gracefully."""
        self._log("=" * 60)
        self._log("Stopping Dharmic Agent Daemon...")
        self._log("=" * 60)

        self.running = False

        # Stop email
        if self.email_daemon:
            self.email_daemon.stop()
            if self.email_task:
                self.email_task.cancel()
                try:
                    await self.email_task
                except asyncio.CancelledError:
                    pass
            self._log("Email interface stopped")

        # Stop Telegram
        if self.telegram_task and not self.telegram_task.done():
            self.telegram_task.cancel()
            try:
                await self.telegram_task
            except asyncio.CancelledError:
                pass
            self._log("Telegram bot stopped")

        # Stop scheduled tasks
        if self.scheduled_tasks:
            self.scheduled_tasks.stop()
            self._log("Scheduled tasks stopped")

        # Stop runtime
        await self.runtime.stop()
        self._log("Runtime stopped")

        # Web dashboard runs in daemon thread - will stop when main exits
        self._log("Web dashboard will stop with daemon")

        # Record in memory
        self.agent.strange_memory.record_observation(
            content="Integrated daemon stopped",
            context={"interfaces": self._get_active_interfaces()}
        )

        self._log("=" * 60)
        self._log("Daemon stopped gracefully")
        self._log("=" * 60)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dharmic Agent Integrated Daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start all interfaces
  python3 integrated_daemon.py --all

  # Start specific interfaces
  python3 integrated_daemon.py --email --web

  # Use custom config
  python3 integrated_daemon.py --config daemon_config.yaml

  # Generate config template
  python3 integrated_daemon.py --generate-config
        """
    )

    parser.add_argument("--all", action="store_true", help="Enable all interfaces")
    parser.add_argument("--email", action="store_true", help="Enable email interface")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram bot")
    parser.add_argument("--web", action="store_true", help="Enable web dashboard")
    parser.add_argument("--scheduled-tasks", action="store_true", help="Enable scheduled tasks")
    parser.add_argument("--config", type=str, help="Path to config YAML file")
    parser.add_argument("--generate-config", type=str, help="Generate config template and exit")

    args = parser.parse_args()

    # Generate config template if requested
    if args.generate_config:
        config = DaemonConfig()
        config.save_template(args.generate_config)
        return

    # Load configuration
    daemon_config = DaemonConfig(args.config)

    # Override with CLI flags
    if args.all:
        daemon_config.config["interfaces"]["email"]["enabled"] = True
        daemon_config.config["interfaces"]["telegram"]["enabled"] = True
        daemon_config.config["interfaces"]["web"]["enabled"] = True
        daemon_config.config["scheduled_tasks"]["enabled"] = True
    else:
        if args.email:
            daemon_config.config["interfaces"]["email"]["enabled"] = True
        if args.telegram:
            daemon_config.config["interfaces"]["telegram"]["enabled"] = True
        if args.web:
            daemon_config.config["interfaces"]["web"]["enabled"] = True
        if args.scheduled_tasks:
            daemon_config.config["scheduled_tasks"]["enabled"] = True

    # Create daemon
    daemon = IntegratedDaemon(daemon_config)

    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal...")
        asyncio.create_task(daemon.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start daemon
    await daemon.start()

    # Keep running
    try:
        while daemon.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

    # Stop gracefully
    await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
