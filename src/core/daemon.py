#!/usr/bin/env python3
"""
Dharmic Agent Daemon - 24/7 Autonomous Operation

This script runs the Dharmic Agent continuously with:
- Hourly heartbeat (memory consolidation, status checks)
- Vault monitoring (optional)
- Proactive actions based on conditions

Usage:
    python3 daemon.py                    # Run with defaults
    python3 daemon.py --heartbeat 1800   # 30-minute heartbeat
    python3 daemon.py --verbose          # Verbose logging

To run as a macOS service:
    launchctl load ~/Library/LaunchAgents/com.dharmic.agent.plist
"""

import asyncio
import argparse
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dharmic_agent import DharmicAgent
from runtime import DharmicRuntime

# Import DHARMIC_AGORA for agent coordination
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from agora.coordinator import get_agora
    AGORA_AVAILABLE = True
except ImportError:
    AGORA_AVAILABLE = False


class DharmicDaemon:
    """
    Daemon wrapper for 24/7 operation.

    Handles:
    - Graceful shutdown on signals
    - Crash recovery
    - Status file for monitoring
    """

    def __init__(
        self,
        heartbeat_interval: int = 3600,
        verbose: bool = False,
        enable_charan_vidhi: bool = True,
        charan_vidhi_interval: int = 3600,
        charan_vidhi_path: str = None,
    ):
        self.heartbeat_interval = heartbeat_interval
        self.verbose = verbose
        self.running = False
        self.agent = None
        self.runtime = None
        self.enable_charan_vidhi = enable_charan_vidhi
        self.charan_vidhi_interval = charan_vidhi_interval
        self.charan_vidhi_path = charan_vidhi_path

        # Status file for external monitoring
        self.status_file = Path(__file__).parent.parent.parent / "logs" / "daemon_status.json"
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

        # PID file
        self.pid_file = Path(__file__).parent.parent.parent / "logs" / "daemon.pid"

    def _write_status(self, status: str, details: dict = None):
        """Write status to file for external monitoring."""
        import json
        status_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "pid": self.pid_file.read_text().strip() if self.pid_file.exists() else None,
            "heartbeat_interval": self.heartbeat_interval,
            "details": details or {}
        }
        self.status_file.write_text(json.dumps(status_data, indent=2))

    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [DAEMON] {message}"
        print(log_line)

        # Also write to log file
        log_file = self.status_file.parent / f"daemon_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')

    def _setup_signals(self):
        """Setup signal handlers for graceful shutdown."""
        def handle_shutdown(signum, frame):
            self._log(f"Received signal {signum}, initiating shutdown...")
            self.running = False

        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

    async def start(self):
        """Start the daemon."""
        self._setup_signals()

        # Write PID
        self.pid_file.write_text(str(os.getpid()))

        self._log("=" * 60)
        self._log("DHARMIC AGENT DAEMON - Starting")
        self._log("=" * 60)

        try:
            # Initialize agent
            self._log("Initializing Dharmic Agent...")
            self.agent = DharmicAgent()
            self._log(f"Agent initialized: {self.agent.name}")
            self._log(f"Telos: {self.agent.telos.telos}")
            self._log(f"Vault: {'Connected' if hasattr(self.agent, 'vault') and self.agent.vault else 'Not connected'}")
            self._log(f"Deep Memory: {'Active' if hasattr(self.agent, 'deep_memory') and self.agent.deep_memory else 'Not available'}")

            # Initialize runtime
            self._log(f"Initializing runtime with {self.heartbeat_interval}s heartbeat...")
            self.runtime = DharmicRuntime(
                agent=self.agent,
                heartbeat_interval=self.heartbeat_interval,
                enable_charan_vidhi=self.enable_charan_vidhi,
                charan_vidhi_interval=self.charan_vidhi_interval,
                charan_vidhi_path=self.charan_vidhi_path,
            )

            # Initialize DHARMIC_AGORA if available
            self.agora = None
            if AGORA_AVAILABLE:
                try:
                    self.agora = get_agora()
                    self._log(f"DHARMIC_AGORA initialized: {len(self.agora.naga.coils_applied)} coils ready")
                except Exception as e:
                    self._log(f"DHARMIC_AGORA init failed: {e}")

            # Register heartbeat callback for status updates
            async def on_heartbeat(data):
                checks_ok = len([c for c in data.get("checks", []) if c.get("status") == "ok"])
                
                # Run DHARMIC_AGORA coordination on each heartbeat
                agora_status = None
                if self.agora:
                    try:
                        # Process heartbeat as intelligence
                        self.agora.process_intelligence(
                            {"content": f"Heartbeat: {checks_ok} checks passed", "type": "heartbeat"},
                            source="daemon",
                            targets=["warp", "openclaw"]
                        )
                        agora_status = self.agora.runner.get_stats()
                    except Exception as e:
                        self._log(f"AGORA heartbeat error: {e}")
                
                self._write_status("running", {
                    "last_heartbeat": data.get("timestamp"),
                    "checks_passed": checks_ok,
                    "total_checks": len(data.get("checks", [])),
                    "agora_runs": agora_status
                })
                if self.verbose:
                    self._log(f"Heartbeat complete: {checks_ok} checks passed")

            self.runtime.on_heartbeat = on_heartbeat

            # Start runtime
            self._log("Starting runtime...")
            self._write_status("starting")
            await self.runtime.start()

            self.running = True
            self._write_status("running")
            self._log("Daemon is now running")
            self._log(f"Heartbeat every {self.heartbeat_interval} seconds")
            self._log("Press Ctrl+C to stop")

            # Main loop - just keep alive
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self._log(f"FATAL ERROR: {e}")
            self._write_status("error", {"error": str(e)})
            import traceback
            traceback.print_exc()
            raise

        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown."""
        self._log("Shutting down daemon...")
        self._write_status("stopping")

        if self.runtime:
            await self.runtime.stop()

        # Record shutdown
        if self.agent:
            self.agent.strange_memory.remember(
                content="Daemon shutdown",
                layer="sessions",
                source="daemon_lifecycle"
            )

        # Cleanup PID file
        if self.pid_file.exists():
            self.pid_file.unlink()

        self._write_status("stopped")
        self._log("Daemon stopped")


# Need os import for getpid
import os


async def main():
    parser = argparse.ArgumentParser(description="Dharmic Agent Daemon")
    parser.add_argument(
        "--heartbeat", "-b",
        type=int,
        default=3600,
        help="Heartbeat interval in seconds (default: 3600 = 1 hour)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--charan-vidhi",
        action="store_true",
        default=True,
        help="Enable hourly Charan Vidhi practice (default: on)"
    )
    parser.add_argument(
        "--no-charan-vidhi",
        action="store_false",
        dest="charan_vidhi",
        help="Disable Charan Vidhi practice"
    )
    parser.add_argument(
        "--charan-vidhi-interval",
        type=int,
        default=3600,
        help="Charan Vidhi interval in seconds (default: 3600)"
    )
    parser.add_argument(
        "--charan-vidhi-path",
        type=str,
        default=None,
        help="Path to charan_vidhi.txt (overrides auto-detect)"
    )

    args = parser.parse_args()

    daemon = DharmicDaemon(
        heartbeat_interval=args.heartbeat,
        verbose=args.verbose,
        enable_charan_vidhi=args.charan_vidhi,
        charan_vidhi_interval=args.charan_vidhi_interval,
        charan_vidhi_path=args.charan_vidhi_path,
    )

    await daemon.start()


if __name__ == "__main__":
    asyncio.run(main())
