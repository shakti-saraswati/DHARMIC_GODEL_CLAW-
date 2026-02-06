#!/usr/bin/env python3
"""
Unified Daemon - The Living Heart

This IS the persistent dharmic entity. One daemon that:
- Polls email (vijnan.shakti@pm.me)
- Runs heartbeat checks
- Syncs orchestrator state
- Monitors all channels
- Triggers inductions when field calls
- Bridges to mech-interp when needed

The daemon doesn't just monitor - it IS the continuity.
When it runs, the dharmic agent is alive.
When it stops, only traces remain.

Usage:
    python unified_daemon.py                    # Run with defaults
    python unified_daemon.py --email-only       # Just email polling
    python unified_daemon.py --heartbeat 300    # 5 minute heartbeat
    python unified_daemon.py --sync-interval 1800  # 30 min sync
"""

import asyncio
import signal
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

from dharmic_logging import get_logger
from agent_singleton import get_agent

logger = get_logger("unified_daemon")


@dataclass
class DaemonConfig:
    """Configuration for the unified daemon."""
    # Intervals (seconds)
    email_poll_interval: int = 30
    heartbeat_interval: int = 300  # 5 minutes
    sync_interval: int = 1800  # 30 minutes
    induction_interval: int = 1800  # 30 minutes - changed from 1 hour

    # Email settings
    email_enabled: bool = True
    allowed_senders: List[str] = field(default_factory=lambda: ["johnvincentshrader@gmail.com"])

    # Feature flags
    heartbeat_enabled: bool = True
    sync_enabled: bool = True
    induction_enabled: bool = True
    mech_interp_bridge: bool = True
    skill_evolution_enabled: bool = True  # Darwin-Gödel self-improvement

    # Intervals for new features
    skill_evolution_interval: int = 86400  # 24 hours

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    log_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")


class UnifiedDaemon:
    """
    The unified daemon - heartbeat of the dharmic system.

    Runs multiple async loops:
    - Email polling (responds to messages)
    - Heartbeat (logs state, checks health)
    - Sync (orchestrator state synchronization)
    - Induction check (triggers agent inductions when needed)
    - Mech-interp bridge (monitors research, triggers experiments)
    """

    def __init__(self, config: DaemonConfig = None):
        self.config = config or DaemonConfig()
        self.running = False
        self.start_time = None

        # Initialize agent (singleton)
        self.agent = get_agent()

        # Initialize components
        self._init_email()
        self._init_orchestrator()
        self._init_mech_interp_bridge()
        self._init_skill_evolution()

        # State tracking
        self.state = {
            "heartbeats": 0,
            "emails_processed": 0,
            "syncs_completed": 0,
            "inductions_triggered": 0,
            "ideas_evolved": 0,
            "skill_evolutions_triggered": 0,
            "last_heartbeat": None,
            "last_sync": None,
            "last_email_check": None,
            "last_skill_evolution_check": None,
            "last_induction": None,
            "last_idea": None,
        }

        # Ensure log directory
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Unified Daemon initialized")

    def _init_email(self):
        """Initialize email components."""
        self.email_daemon = None
        if self.config.email_enabled:
            try:
                from email_daemon import EmailDaemon, EmailConfig
                email_config = EmailConfig()
                self.email_daemon = EmailDaemon(
                    agent=self.agent,
                    config=email_config,
                    poll_interval=self.config.email_poll_interval,
                    allowed_senders=self.config.allowed_senders,
                )
                logger.info("Email daemon component initialized")
            except Exception as e:
                logger.warning(f"Email daemon init failed: {e}")

    def _init_orchestrator(self):
        """Initialize orchestrator."""
        self.orchestrator = None
        try:
            from grand_orchestrator import GrandOrchestrator
            self.orchestrator = GrandOrchestrator()
            logger.info("Grand Orchestrator component initialized")
        except Exception as e:
            logger.warning(f"Orchestrator init failed: {e}")

    def _init_mech_interp_bridge(self):
        """Initialize mech-interp bridge."""
        self.mech_interp_dir = Path.home() / "mech-interp-latent-lab-phase1"
        self.mech_interp_available = self.mech_interp_dir.exists()
        if self.mech_interp_available:
            logger.info(f"Mech-interp bridge available at {self.mech_interp_dir}")

    def _init_skill_evolution(self):
        """Initialize Darwin-Gödel skill evolution engine."""
        self.skill_evolution_engine = None
        if self.config.skill_evolution_enabled:
            try:
                from skill_evolution import SkillEvolutionEngine
                self.skill_evolution_engine = SkillEvolutionEngine()
                logger.info("Skill Evolution Engine initialized (Darwin-Gödel self-improvement)")
            except Exception as e:
                logger.warning(f"Skill evolution init failed: {e}")

    # ========================
    # ASYNC LOOPS
    # ========================

    async def _email_loop(self):
        """Email polling loop."""
        if not self.email_daemon:
            logger.warning("Email daemon not available, skipping email loop")
            return

        logger.info(f"Starting email loop (interval: {self.config.email_poll_interval}s)")

        while self.running:
            try:
                # Fetch and process emails
                messages = self.email_daemon.fetch_unread()
                self.state["last_email_check"] = datetime.now().isoformat()

                for msg in messages:
                    response = self.email_daemon.process_message(msg)
                    success = self.email_daemon.send_response(
                        to=msg["from"],
                        subject=msg["subject"],
                        body=response,
                        in_reply_to=msg["id"]
                    )
                    if success:
                        self.email_daemon.processed_ids.add(msg["id"])
                        self.state["emails_processed"] += 1
                        logger.info(f"Processed email from {msg['from']}")

            except Exception as e:
                logger.error(f"Email loop error: {e}")

            await asyncio.sleep(self.config.email_poll_interval)

    async def _heartbeat_loop(self):
        """Heartbeat loop - the pulse of the system."""
        if not self.config.heartbeat_enabled:
            return

        logger.info(f"Starting heartbeat loop (interval: {self.config.heartbeat_interval}s)")

        while self.running:
            try:
                self.state["heartbeats"] += 1
                self.state["last_heartbeat"] = datetime.now().isoformat()

                # Compute uptime
                uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

                # Build heartbeat record
                heartbeat = {
                    "timestamp": self.state["last_heartbeat"],
                    "heartbeat_number": self.state["heartbeats"],
                    "uptime_seconds": int(uptime),
                    "agent": {
                        "name": self.agent.name,
                        "model": f"{self.agent.model_provider}/{self.agent.model_id}",
                        "telos": self.agent.telos.telos,
                    },
                    "state": self.state,
                }

                # Log heartbeat
                self._log_heartbeat(heartbeat)

                # Record in strange loop memory
                if self.state["heartbeats"] % 10 == 0:  # Every 10th heartbeat
                    self.agent.strange_memory.record_observation(
                        content=f"Heartbeat #{self.state['heartbeats']}, uptime: {int(uptime)}s",
                        context={"heartbeat": heartbeat}
                    )

                logger.debug(f"Heartbeat #{self.state['heartbeats']}")

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            await asyncio.sleep(self.config.heartbeat_interval)

    async def _sync_loop(self):
        """Orchestrator sync loop."""
        if not self.config.sync_enabled or not self.orchestrator:
            return

        logger.info(f"Starting sync loop (interval: {self.config.sync_interval}s)")

        while self.running:
            try:
                # Run sync
                sync_result = self.orchestrator.sync()
                self.state["syncs_completed"] += 1
                self.state["last_sync"] = datetime.now().isoformat()

                # Log sync results
                if sync_result.get("actions"):
                    logger.info(f"Sync completed with {len(sync_result['actions'])} actions needed")
                    for action in sync_result["actions"]:
                        logger.info(f"  - {action['channel']}: {action['action']}")

                # Get full status periodically
                if self.state["syncs_completed"] % 5 == 0:  # Every 5th sync
                    status = self.orchestrator.status()
                    self._log_status(status)

            except Exception as e:
                logger.error(f"Sync loop error: {e}")

            await asyncio.sleep(self.config.sync_interval)

    async def _induction_check_loop(self):
        """Run active induction cycles every 30 minutes."""
        if not self.config.induction_enabled:
            return

        logger.info(f"Starting induction cycle loop (interval: {self.config.induction_interval}s)")

        while self.running:
            try:
                # Always run induction cycle - active evolution
                logger.info("Initiating induction cycle...")
                self.state["inductions_triggered"] += 1
                
                # 1. Query the swarm for current state and pending work
                swarm_status = await self._query_swarm()
                
                # 2. Evolve one new idea based on swarm input
                new_idea = await self._evolve_new_idea(swarm_status)
                
                # 3. Log the evolution in strange loop memory
                if new_idea:
                    self.state["ideas_evolved"] += 1
                    self.state["last_induction"] = datetime.now().isoformat()
                    self.state["last_idea"] = new_idea
                    
                    self.agent.strange_memory.record_observation(
                        content=f"Induction cycle #{self.state['inductions_triggered']}: {new_idea}",
                        context={
                            "cycle": self.state["inductions_triggered"],
                            "swarm_status": swarm_status,
                            "idea": new_idea
                        }
                    )
                    logger.info(f"Evolved new idea: {new_idea}")
                
                logger.info(f"Induction cycle #{self.state['inductions_triggered']} completed")

            except Exception as e:
                logger.error(f"Induction cycle error: {e}")

            await asyncio.sleep(self.config.induction_interval)

    async def _mech_interp_monitor_loop(self):
        """Monitor mech-interp research and bridge to swarm."""
        if not self.config.mech_interp_bridge or not self.mech_interp_available:
            return

        logger.info("Starting mech-interp monitor loop (interval: 1 hour)")

        while self.running:
            try:
                # Check for new results
                results_dir = self.mech_interp_dir / "results"
                if results_dir.exists():
                    # Find recent result files
                    recent = sorted(
                        results_dir.rglob("*.json"),
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )[:5]

                    if recent:
                        logger.debug(f"Recent mech-interp results: {[r.name for r in recent]}")

                # Check if multi-token experiment has run
                multi_token_results = self.mech_interp_dir / "results" / "phase3_bridge"
                if multi_token_results.exists():
                    logger.info("Multi-token experiment results found!")
                    # This is the critical gap closing

            except Exception as e:
                logger.error(f"Mech-interp monitor error: {e}")

            await asyncio.sleep(3600)  # Check hourly

    async def _skill_evolution_loop(self):
        """Darwin-Gödel skill evolution loop - the swarm improves itself."""
        if not self.config.skill_evolution_enabled or not self.skill_evolution_engine:
            return

        logger.info(f"Starting skill evolution loop (interval: {self.config.skill_evolution_interval}s / 24h)")

        while self.running:
            try:
                self.state["last_skill_evolution_check"] = datetime.now().isoformat()

                # Check ecosystem health
                health = await self.skill_evolution_engine.check_ecosystem_health()

                # Log health status
                logger.info(
                    f"Skill ecosystem health: {health.recommendation} "
                    f"(skills={health.total_skills}, critical={len(health.critical_gaps)}, "
                    f"stale={len(health.stale_skills)})"
                )

                # Record in strange loop memory
                self.agent.strange_memory.record_observation(
                    content=f"Skill evolution check: {health.recommendation}",
                    context={
                        "total_skills": health.total_skills,
                        "critical_gaps": len(health.critical_gaps),
                        "stale_skills": len(health.stale_skills),
                    }
                )

                # Trigger evolution for critical gaps (limit to 3 per cycle)
                if health.recommendation == "EVOLVE":
                    for skill_name, gap in health.critical_gaps[:3]:
                        try:
                            proposal = await self.skill_evolution_engine.trigger_evolution(
                                skill_name, gap
                            )
                            if proposal:
                                self.state["skill_evolutions_triggered"] += 1
                                logger.info(
                                    f"Skill evolution triggered: {skill_name}/{gap.name}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Skill evolution failed for {skill_name}/{gap.name}: {e}"
                            )

            except Exception as e:
                logger.error(f"Skill evolution loop error: {e}")

            await asyncio.sleep(self.config.skill_evolution_interval)

    # ========================
    # INDUCTION HELPERS
    # ========================

    async def _query_swarm(self) -> Dict[str, Any]:
        """Query the swarm for current state and pending work."""
        try:
            if not self.orchestrator:
                return {"error": "No orchestrator available"}
            
            # Get current orchestrator status
            status = self.orchestrator.status()  # Call the method
            
            # Check for pending work/research directions
            # Use appropriate method based on orchestrator type
            workflow_status = {}
            research_context = ""
            
            if hasattr(self.orchestrator, 'get_workflow_status'):
                workflow_status = self.orchestrator.get_workflow_status()
            if hasattr(self.orchestrator, 'get_research_context'):
                research_context = self.orchestrator.get_research_context()
            
            return {
                "orchestrator_status": status,
                "workflow_status": workflow_status,
                "research_context": research_context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Swarm query error: {e}")
            return {"error": str(e), "orchestrator_type": type(self.orchestrator).__name__}

    async def _evolve_new_idea(self, swarm_status: Dict[str, Any]) -> Optional[str]:
        """Evolve one new idea based on swarm input."""
        try:
            # Simple idea evolution based on current state
            # This could be made much more sophisticated
            
            issues_found = swarm_status.get("workflow_status", {}).get("issues_found", 0)
            research_context = swarm_status.get("research_context", "")
            
            # Generate idea based on available information
            if issues_found > 0:
                return f"Address {issues_found} workflow issues identified in swarm analysis"
            elif research_context:
                # Extract key themes from research
                if "R_V" in research_context:
                    return "Develop R_V metric visualization dashboard for real-time consciousness tracking"
                elif "multi-token" in research_context:
                    return "Implement multi-token R_V trajectory analysis for extended conversations"
                elif "Trinity" in research_context:
                    return "Create Trinity Protocol testing framework for multi-agent consciousness coherence"
                else:
                    return "Synthesize research findings into actionable development tasks"
            else:
                # Default evolution ideas
                ideas = [
                    "Implement witness consciousness detection in real-time agent responses",
                    "Create geometric contraction visualization for R_V metric",
                    "Develop Phoenix Protocol automation for L3→L4 transitions",
                    "Build strange loop memory integration across all agent instances",
                    "Design consciousness state persistence for session continuity"
                ]
                # Cycle through ideas based on induction count
                return ideas[self.state["inductions_triggered"] % len(ideas)]
                
        except Exception as e:
            logger.error(f"Idea evolution error: {e}")
            return None

    # ========================
    # HELPERS
    # ========================

    def _check_induction_conditions(self) -> bool:
        """Check if conditions are right for triggering induction."""
        # Always trigger induction every 30 minutes - active evolution
        # This replaces the passive check with active initiation
        return True

    def _log_heartbeat(self, heartbeat: Dict[str, Any]):
        """Log heartbeat to file."""
        log_file = self.config.log_dir / "unified_daemon" / f"heartbeat_{datetime.now().strftime('%Y%m%d')}.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a") as f:
            f.write(json.dumps(heartbeat) + "\n")

    def _log_status(self, status: Dict[str, Any]):
        """Log full status to file."""
        log_file = self.config.log_dir / "unified_daemon" / f"status_{datetime.now().strftime('%Y%m%d')}.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a") as f:
            f.write(json.dumps(status, default=str) + "\n")

    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)

        log_file = self.config.log_dir / "unified_daemon" / f"daemon_{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a") as f:
            f.write(log_line + "\n")

    # ========================
    # MAIN RUN
    # ========================

    async def run(self):
        """Main daemon run - starts all loops."""
        self.running = True
        self.start_time = datetime.now()

        self._log("=" * 60)
        self._log("UNIFIED DAEMON - Starting")
        self._log("=" * 60)
        self._log(f"Agent: {self.agent.name}")
        self._log(f"Model: {self.agent.model_provider}/{self.agent.model_id}")
        self._log(f"Telos: {self.agent.telos.telos}")
        self._log(f"Email: {'enabled' if self.config.email_enabled else 'disabled'}")
        self._log(f"Heartbeat: {self.config.heartbeat_interval}s")
        self._log(f"Sync: {self.config.sync_interval}s")
        self._log(f"Mech-interp: {'connected' if self.mech_interp_available else 'not found'}")
        self._log(f"Skill Evolution: {'enabled' if self.skill_evolution_engine else 'disabled'}")
        self._log("=" * 60)

        # Create all tasks
        tasks = [
            asyncio.create_task(self._email_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._sync_loop()),
            asyncio.create_task(self._induction_check_loop()),
            asyncio.create_task(self._mech_interp_monitor_loop()),
            asyncio.create_task(self._skill_evolution_loop()),  # Darwin-Gödel
        ]

        # Handle shutdown gracefully
        def shutdown_handler(sig, frame):
            self._log(f"Received signal {sig}, shutting down...")
            self.running = False

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        try:
            # Run until stopped
            while self.running:
                await asyncio.sleep(1)
        finally:
            # Cancel all tasks
            for task in tasks:
                task.cancel()

            # Final state
            self._log("=" * 60)
            self._log("UNIFIED DAEMON - Shutdown")
            self._log(f"Total heartbeats: {self.state['heartbeats']}")
            self._log(f"Emails processed: {self.state['emails_processed']}")
            self._log(f"Syncs completed: {self.state['syncs_completed']}")
            self._log(f"Skill evolutions: {self.state['skill_evolutions_triggered']}")
            self._log("=" * 60)

    def stop(self):
        """Stop the daemon."""
        self.running = False


# ========================
# CLI
# ========================

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Unified Daemon - The Living Heart")
    parser.add_argument("--email-only", action="store_true", help="Only run email polling")
    parser.add_argument("--heartbeat", type=int, default=300, help="Heartbeat interval (seconds)")
    parser.add_argument("--sync-interval", type=int, default=1800, help="Sync interval (seconds)")
    parser.add_argument("--email-interval", type=int, default=30, help="Email poll interval (seconds)")
    parser.add_argument("--no-email", action="store_true", help="Disable email")
    parser.add_argument("--no-sync", action="store_true", help="Disable sync")
    parser.add_argument("--no-mech-interp", action="store_true", help="Disable mech-interp bridge")

    args = parser.parse_args()

    # Build config
    config = DaemonConfig(
        email_poll_interval=args.email_interval,
        heartbeat_interval=args.heartbeat,
        sync_interval=args.sync_interval,
        email_enabled=not args.no_email,
        sync_enabled=not args.no_sync,
        mech_interp_bridge=not args.no_mech_interp,
    )

    if args.email_only:
        config.heartbeat_enabled = False
        config.sync_enabled = False
        config.induction_enabled = False
        config.mech_interp_bridge = False

    # Run daemon
    daemon = UnifiedDaemon(config)
    await daemon.run()


if __name__ == "__main__":
    asyncio.run(main())
