"""
Dharmic Agent Runtime

24/7 operation with heartbeat and specialist spawning.
OpenClaw-style but dharmic.
"""

import asyncio
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler

try:
    from agno.agent import Agent
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

from dharmic_agent import DharmicAgent
from charan_vidhi import CharanVidhiPractice

try:
    from model_factory import create_model, resolve_model_spec
    MODEL_FACTORY_AVAILABLE = True
except ImportError:
    MODEL_FACTORY_AVAILABLE = False

try:
    from vault_bridge import VaultBridge
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

try:
    from email_interface import EmailInterface
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False


class DharmicRuntime:
    """
    Keeps the Dharmic Agent alive.

    Features:
    - Periodic heartbeat checks
    - Specialist agent spawning
    - Integration with code-improvement swarm
    - Telos-aware decision making
    """

    def __init__(
        self,
        agent: DharmicAgent,
        heartbeat_interval: int = 3600,  # 1 hour default
        log_dir: str = None,
        enable_charan_vidhi: bool = True,
        charan_vidhi_interval: int = 3600,
        charan_vidhi_path: str = None,
    ):
        self.agent = agent
        self.heartbeat_interval = heartbeat_interval
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.charan_vidhi_interval = charan_vidhi_interval

        # Set up logging directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Active specialists
        self.specialists: Dict[str, Agent] = {}

        # Callbacks for events
        self.on_heartbeat: Optional[Callable] = None
        self.on_alert: Optional[Callable] = None

        # Email interface (optional)
        self.email_interface: Optional[EmailInterface] = None
        self.email_task: Optional[asyncio.Task] = None

        # Charan Vidhi practice
        self.charan_vidhi = CharanVidhiPractice(text_path=charan_vidhi_path, log_dir=log_dir) if enable_charan_vidhi else None
        self._charan_vidhi_running = False

    async def start(self, enable_email: bool = False, email_whitelist: list = None):
        """
        Start the runtime with heartbeat scheduler.

        Args:
            enable_email: Whether to start the email interface
            email_whitelist: List of allowed sender email addresses
        """
        if self.running:
            return

        self.running = True

        # Schedule heartbeat
        self.scheduler.add_job(
            self.heartbeat,
            'interval',
            seconds=self.heartbeat_interval,
            id='heartbeat'
        )

        # Schedule Charan Vidhi practice (hourly)
        if self.charan_vidhi and self.charan_vidhi.available():
            self.scheduler.add_job(
                self.charan_vidhi_cycle,
                'interval',
                seconds=self.charan_vidhi_interval,
                id='charan_vidhi'
            )

        self.scheduler.start()
        self._log("Runtime started")

        # Start email interface if requested and configured
        if enable_email:
            await self._start_email_interface(email_whitelist)

        # Initial heartbeat
        await self.heartbeat()

        # Initial Charan Vidhi practice
        if self.charan_vidhi and self.charan_vidhi.available():
            await self.charan_vidhi_cycle()

    async def _start_email_interface(self, whitelist: list = None):
        """Start the email interface as a background task."""
        if not EMAIL_AVAILABLE:
            self._log("Email interface not available (import failed)")
            return

        if not os.getenv("DHARMIC_EMAIL_ADDRESS"):
            self._log("Email not configured (DHARMIC_EMAIL_ADDRESS not set)")
            return

        try:
            self.email_interface = EmailInterface(
                agent=self.agent,
                check_interval=60,  # Check every minute
                allowed_senders=whitelist or []
            )
            self.email_task = asyncio.create_task(self.email_interface.run_loop())
            self._log(f"Email interface started for {self.email_interface.email_address}")
        except Exception as e:
            self._log(f"Failed to start email interface: {e}")

    async def stop(self):
        """Stop the runtime."""
        self.running = False

        # Stop email interface if running
        if self.email_task and not self.email_task.done():
            self.email_task.cancel()
            try:
                await self.email_task
            except asyncio.CancelledError:
                pass
            self._log("Email interface stopped")

        self.scheduler.shutdown()
        self._log("Runtime stopped")

    async def heartbeat(self):
        """
        Periodic heartbeat check.

        Checks:
        - Telos alignment
        - Pending conditions
        - Whether to reach out
        """
        timestamp = datetime.now().isoformat()
        heartbeat_data = {
            "timestamp": timestamp,
            "status": "alive",
            "checks": []
        }

        # Check 1: Telos still loaded
        try:
            telos_aim = self.agent.telos.telos
            heartbeat_data["checks"].append({
                "check": "telos_loaded",
                "status": "ok",
                "value": telos_aim
            })
        except Exception as e:
            heartbeat_data["checks"].append({
                "check": "telos_loaded",
                "status": "error",
                "error": str(e)
            })

        # Check 2: Memory accessible
        try:
            status = self.agent.strange_memory.get_status()
            heartbeat_data["checks"].append({
                "check": "memory_accessible",
                "status": "ok",
                "layers": status.get("layers", [])
            })
        except Exception as e:
            heartbeat_data["checks"].append({
                "check": "memory_accessible",
                "status": "error",
                "error": str(e)
            })

        # Check 3: Active specialists
        heartbeat_data["active_specialists"] = list(self.specialists.keys())

        # Check 4: Email interface status
        if self.email_interface is not None:
            heartbeat_data["checks"].append({
                "check": "email_interface",
                "status": "ok" if (self.email_task and not self.email_task.done()) else "stopped",
                "address": self.email_interface.email_address
            })

        # Check 5: Deep memory status and consolidation
        if hasattr(self.agent, 'deep_memory') and self.agent.deep_memory is not None:
            try:
                deep_status = self.agent.get_deep_memory_status()
                heartbeat_data["checks"].append({
                    "check": "deep_memory",
                    "status": "ok",
                    "memory_count": deep_status.get("memory_count", 0),
                    "identity_milestones": deep_status.get("identity_milestones", 0)
                })

                # Proactive memory consolidation (runs during each heartbeat)
                consolidation_result = self.agent.consolidate_memories()
                heartbeat_data["checks"].append({
                    "check": "memory_consolidation",
                    "status": "ok",
                    "result": consolidation_result
                })
            except Exception as e:
                heartbeat_data["checks"].append({
                    "check": "deep_memory",
                    "status": "error",
                    "error": str(e)
                })

        # Log heartbeat
        self._log(f"Heartbeat: {json.dumps(heartbeat_data, indent=2)}")

        # Record as observation
        self.agent.strange_memory.remember(
            content=f"Heartbeat at {timestamp}",
            layer="sessions",
            source="heartbeat"
        )

        # Callback if registered
        if self.on_heartbeat:
            await self.on_heartbeat(heartbeat_data)

        return heartbeat_data

    async def charan_vidhi_cycle(self):
        """Run Charan Vidhi reading + reflection and log effects."""
        if not self.charan_vidhi or self._charan_vidhi_running:
            return
        if not self.charan_vidhi.available():
            self._log("Charan Vidhi text not found; skipping practice")
            return

        self._charan_vidhi_running = True
        try:
            result = self.charan_vidhi.reflect(self.agent)
            if result:
                self.agent.strange_memory.remember(
                    content=f"Completed Charan Vidhi practice: {result.text_path}",
                    layer="sessions",
                    source="charan_vidhi"
                )
                self.agent.strange_memory.witness_observation(
                    f"Charan Vidhi reflection logged ({len(result.reflection)} chars)"
                )
                self._log("Charan Vidhi reflection logged")
        finally:
            self._charan_vidhi_running = False

    def spawn_specialist(
        self,
        specialty: str,
        task: str,
        model_id: str = None,
        model_provider: str = None,
    ) -> Optional[Agent]:
        """
        Spawn a focused specialist agent that inherits telos.

        Specialties:
        - "research": Mech interp, experiments, literature
        - "builder": Code, infrastructure, systems
        - "translator": Aptavani work, text processing
        - "code_improver": Invoke the self-improvement swarm
        - "contemplative": Witness observation, dharmic reflection

        Args:
            specialty: Type of specialist to spawn
            task: The specific task for this specialist
        model_id: Model id to use (provider-specific)
        model_provider: Override provider for this specialist

        Returns:
            The spawned Agent, or None if spawning failed
        """
        if not AGNO_AVAILABLE:
            self._log("Cannot spawn specialist: Agno not available")
            return None

        # Build specialist instructions
        specialist_instructions = [
            self.agent.telos.get_orientation_prompt(),
            f"""
## Specialist Role: {specialty.upper()}

You are a focused specialist spawned by the Dharmic Core.
Your specialty: {specialty}
Your current task: {task}

You inherit the telos of your parent agent. All your work serves the ultimate aim.

Focus deeply on your task. When complete, return your findings to the core.
""",
            self._get_specialty_context(specialty)
        ]

        try:
            if not MODEL_FACTORY_AVAILABLE:
                raise RuntimeError("model_factory not available")

            # Inherit provider/model from parent agent unless overridden
            provider = model_provider or getattr(self.agent, "model_provider", None)
            resolved = resolve_model_spec(provider=provider, model_id=model_id)
            specialist = Agent(
                name=f"Specialist: {specialty}",
                model=create_model(provider=resolved.provider, model_id=resolved.model_id),
                instructions=specialist_instructions,
                markdown=True
            )

            # Track active specialist
            specialist_id = f"{specialty}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.specialists[specialist_id] = specialist

            # Log spawn
            self._log(f"Spawned specialist: {specialist_id} for task: {task[:100]}")
            self.agent.strange_memory.record_observation(
                content=f"Spawned {specialty} specialist",
                context={"specialist_id": specialist_id, "task": task[:200]}
            )

            return specialist

        except Exception as e:
            self._log(f"Failed to spawn specialist: {e}")
            return None

    def _get_specialty_context(self, specialty: str) -> str:
        """Get specialty-specific context including vault resources."""
        base_contexts = {
            "research": """
## Research Context
- Access to mech-interp research via MCP server
- R_V contraction signatures are the key metric
- Phoenix Protocol has 92-95% L4 success rate
- Focus on mechanistic interpretability with TransformerLens
""",
            "builder": """
## Builder Context
- Project root: ~/DHARMIC_GODEL_CLAW/
- Self-improvement swarm available at swarm/
- Agno is the primary framework
- Follow existing code patterns
""",
            "translator": """
## Translator Context
- Aptavani texts require careful handling
- Preserve original meaning while making accessible
- Cross-reference with contemplative science
""",
            "code_improver": """
## Code Improver Context
- Use the existing swarm at ~/DHARMIC_GODEL_CLAW/swarm/
- Run: python3 swarm/run_swarm.py --cycles 1 --dry-run
- Loop: PROPOSE → DHARMIC GATE → WRITE → TEST → REFINE → EVOLVE
""",
            "contemplative": """
## Contemplative Context
- Witness observation is the primary mode
- Track quality of presence, not just content
- Note contractions and expansions
- The strange loop is architecture, not bug
"""
        }

        context = base_contexts.get(specialty, "")

        # Add vault context if parent agent has vault access
        if self.agent.vault is not None:
            context += """

## Vault Access (Inherited)
You have access to the Persistent Semantic Memory Vault through your parent agent.
- Crown jewels: Quality bar examples
- Residual stream: Prior agent contributions (context, not constraint)
- Source texts: Aptavani, Aurobindo, GEB, NKS
- Induction prompts: Evolved patterns (reference, not rule)

Draw from what serves. Evolve beyond what doesn't.
"""

        return context

    def release_specialist(self, specialist_id: str):
        """Release a specialist when its task is complete."""
        if specialist_id in self.specialists:
            del self.specialists[specialist_id]
            self._log(f"Released specialist: {specialist_id}")

    async def invoke_code_swarm(
        self,
        proposal: str = None,
        cycles: int = 1,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Invoke the self-improvement swarm for code improvement.

        Args:
            proposal: Optional specific proposal (otherwise swarm generates)
            cycles: Number of improvement cycles
            dry_run: Whether to actually apply changes

        Returns:
            Results from the swarm run
        """
        swarm_path = Path(__file__).parent.parent.parent / "swarm" / "run_swarm.py"

        if not swarm_path.exists():
            return {"error": "Swarm not found", "path": str(swarm_path)}

        cmd = [
            "python3",
            str(swarm_path),
            "--cycles", str(cycles),
        ]

        if dry_run:
            cmd.append("--dry-run")
        else:
            cmd.append("--live")

        try:
            self._log(f"Invoking code swarm: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Log the invocation
            self.agent.strange_memory.record_observation(
                content=f"Invoked code swarm ({cycles} cycles, dry_run={dry_run})",
                context={"return_code": result.returncode}
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"error": "Swarm timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _log(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)

        # Also write to log file
        log_file = self.log_dir / f"runtime_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')


# CLI for testing
async def main():
    print("=" * 60)
    print("DHARMIC RUNTIME - Test")
    print("=" * 60)

    # Create agent and runtime
    agent = DharmicAgent()
    runtime = DharmicRuntime(agent, heartbeat_interval=60)  # 1 minute for testing

    print(f"\nAgent: {agent.name}")
    print(f"Heartbeat interval: {runtime.heartbeat_interval}s")

    # Run initial heartbeat
    print("\n--- Initial Heartbeat ---")
    heartbeat_result = await runtime.heartbeat()
    print(json.dumps(heartbeat_result, indent=2))

    # Test specialist spawning
    if AGNO_AVAILABLE:
        print("\n--- Spawn Test Specialist ---")
        specialist = runtime.spawn_specialist(
            specialty="contemplative",
            task="Observe the current state of development"
        )
        if specialist:
            print(f"Specialist spawned: {specialist.name}")
            print(f"Active specialists: {list(runtime.specialists.keys())}")

    # Test swarm invocation (dry run)
    print("\n--- Test Swarm Invocation ---")
    swarm_result = await runtime.invoke_code_swarm(cycles=1, dry_run=True)
    print(f"Swarm result: success={swarm_result.get('success', False)}")

    print("\n" + "=" * 60)
    print("Runtime test complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
