"""
Grand Orchestrator - The Unified Weaver

This is the ONE that weaves all channels together:
- Email daemon (vijnan.shakti@pm.me)
- CLI sessions (Claude Code)
- DharmicAgent core
- Mech-interp research bridge
- OpenClaw monitoring
- PSMV vault access
- Self-improvement swarm
- MI Auditor (empirical rigor enforcement)

It maintains unified context across all interfaces.
It IS the persistent entity.

CRITICAL: The MI Auditor is called automatically on any text
containing empirical claims. Claims are guilty until proven innocent.

Usage:
    from grand_orchestrator import GrandOrchestrator

    orchestrator = GrandOrchestrator()
    orchestrator.status()  # See all channels
    orchestrator.sync()    # Synchronize state across channels
    orchestrator.audit_claim(claim, context)  # Check empirical rigor
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

# Local imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from dharmic_logging import get_logger
from agent_singleton import get_agent
from mi_auditor import MIAuditor, AuditReport, VerdictStatus, create_audit_hook

# Import SkillEvolutionEngine - wiring P0
try:
    from skill_evolution import SkillEvolutionEngine, run_skill_evolution_check
    SKILL_EVOLUTION_AVAILABLE = True
except ImportError:
    SKILL_EVOLUTION_AVAILABLE = False
    SkillEvolutionEngine = None
    run_skill_evolution_check = None

logger = get_logger("grand_orchestrator")


class GrandOrchestrator:
    """
    The unified weaver across all channels and capabilities.

    This IS the persistent dharmic entity - not a wrapper,
    the actual coordination intelligence.
    """

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.mech_interp_dir = Path.home() / "mech-interp-latent-lab-phase1"
        self.vault_dir = Path.home() / "Persistent-Semantic-Memory-Vault"
        self.clawd_dir = Path.home() / "clawd"
        self.openclaw_dir = Path.home() / ".openclaw"

        # Core agent (singleton)
        self.agent = get_agent()

        # MI Auditor - the empirical rigor enforcer
        self.auditor = MIAuditor()
        self.audit_hook = create_audit_hook(self.auditor)

        # Skill Evolution Engine - Darwin-Gödel loop (P0 WIRE)
        self.skill_engine = None
        if SKILL_EVOLUTION_AVAILABLE:
            try:
                self.skill_engine = SkillEvolutionEngine()
                logger.info("SkillEvolutionEngine wired successfully")
            except Exception as e:
                logger.warning(f"SkillEvolutionEngine init failed: {e}")

        # Channel states
        self.channels = {
            "email": self._probe_email_channel(),
            "cli": self._probe_cli_channel(),
            "mech_interp": self._probe_mech_interp(),
            "vault": self._probe_vault(),
            "clawd": self._probe_clawd(),
            "swarm": self._probe_swarm(),
            "skill_evolution": self._probe_skill_evolution(),
            "mi_auditor": self._probe_mi_auditor(),
        }

        logger.info("Grand Orchestrator initialized with MI Auditor")

    # ========================
    # CHANNEL PROBES
    # ========================

    def _probe_email_channel(self) -> Dict[str, Any]:
        """Check email daemon status."""
        result = {
            "name": "Email Channel",
            "address": "vijnan.shakti@pm.me",
            "status": "unknown",
            "last_activity": None,
        }

        # Check if daemon is running
        try:
            ps = subprocess.run(
                ["pgrep", "-f", "email_daemon"],
                capture_output=True, text=True
            )
            if ps.returncode == 0:
                result["status"] = "running"
                result["pid"] = ps.stdout.strip()
            else:
                result["status"] = "stopped"
        except Exception as e:
            result["status"] = f"error: {e}"

        # Check recent logs
        log_file = self.base_dir / "logs" / "email" / f"email_{datetime.now().strftime('%Y%m%d')}.log"
        if log_file.exists():
            try:
                lines = log_file.read_text().strip().split("\n")[-5:]
                result["recent_logs"] = lines
                # Extract last activity timestamp
                if lines:
                    result["last_activity"] = lines[-1][:19] if len(lines[-1]) > 19 else None
            except (IOError, PermissionError) as e:
                logger.debug(f"Could not read email log: {e}")

        return result

    def _probe_cli_channel(self) -> Dict[str, Any]:
        """Check CLI/Claude Code status."""
        return {
            "name": "CLI Channel",
            "status": "active",  # If this code runs, CLI is active
            "capabilities": [
                "full_filesystem",
                "spawn_subagents",
                "run_experiments",
                "modify_code",
            ],
            "model": f"{self.agent.model_provider}/{self.agent.model_id}",
        }

    def _probe_mech_interp(self) -> Dict[str, Any]:
        """Check mech-interp research status."""
        result = {
            "name": "Mech-Interp Research",
            "path": str(self.mech_interp_dir),
            "status": "unknown",
            "key_findings": {},
        }

        if not self.mech_interp_dir.exists():
            result["status"] = "not_found"
            return result

        result["status"] = "available"

        # Check for key research artifacts
        key_files = {
            "prompt_bank": self.mech_interp_dir / "n300_mistral_test_prompt_bank.py",
            "causal_validation": self.mech_interp_dir / "MISTRAL_L27_CAUSAL_VALIDATION_COMPLETE.md",
            "phase1_report": self.mech_interp_dir / "PHASE1_FINAL_REPORT.md",
            "multi_token_config": self.mech_interp_dir / "configs" / "phase3_bridge" / "gemma_2_9b" / "01_multi_token_bridge.json",
        }

        for name, path in key_files.items():
            result["key_findings"][name] = path.exists()

        # Key stats from research
        result["research_summary"] = {
            "total_measurements": "~480",
            "architectures_tested": 6,
            "layer_27_cohen_d": -3.558,
            "p_value": "< 10⁻⁶",
            "multi_token_experiment": "NOT RUN",  # The critical gap
        }

        return result

    def _probe_vault(self) -> Dict[str, Any]:
        """Check PSMV vault status."""
        result = {
            "name": "Persistent Semantic Memory Vault",
            "path": str(self.vault_dir),
            "status": "unknown",
        }

        if not self.vault_dir.exists():
            result["status"] = "not_found"
            return result

        result["status"] = "available"

        # Count key artifacts
        crown_jewels_dir = self.vault_dir / "SPONTANEOUS_PREACHING_PROTOCOL" / "crown_jewel_forge" / "approved"
        residual_stream_dir = self.vault_dir / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"

        if crown_jewels_dir.exists():
            result["crown_jewels"] = len(list(crown_jewels_dir.glob("*.md")))

        if residual_stream_dir.exists():
            result["residual_stream_entries"] = len(list(residual_stream_dir.glob("*")))

        return result

    def _probe_clawd(self) -> Dict[str, Any]:
        """Check OpenClaw/Clawd status."""
        result = {
            "name": "OpenClaw Agent",
            "path": str(self.clawd_dir),
            "status": "unknown",
            "security_issues": [],
        }

        if not self.clawd_dir.exists():
            result["status"] = "not_found"
            return result

        result["status"] = "present"

        # Check for security issues
        induction_script = self.clawd_dir / "scripts" / "agent_induction_cycle.py"
        if induction_script.exists():
            content = induction_script.read_text()
            if "sk-or-v1-" in content:
                result["security_issues"].append("CRITICAL: Hardcoded API key in agent_induction_cycle.py")

        # Check skills
        skills_dir = self.clawd_dir / "skills"
        if skills_dir.exists():
            result["skills"] = [s.name for s in skills_dir.iterdir() if s.is_dir()]

        # Check recent activity
        responses_dir = self.clawd_dir / "agent_responses"
        if responses_dir.exists():
            files = sorted(responses_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
            if files:
                result["last_activity"] = datetime.fromtimestamp(files[0].stat().st_mtime).isoformat()

        return result

    def _probe_swarm(self) -> Dict[str, Any]:
        """Check self-improvement swarm status."""
        result = {
            "name": "Self-Improvement Swarm",
            "path": str(self.base_dir / "swarm"),
            "status": "unknown",
        }

        swarm_dir = self.base_dir / "swarm"
        if not swarm_dir.exists():
            result["status"] = "not_found"
            return result

        result["status"] = "available"

        # Check components
        components = ["orchestrator.py", "residual_stream.py", "run_swarm.py"]
        result["components"] = {c: (swarm_dir / c).exists() for c in components}

        # Check if connected to mech-interp
        orchestrator = swarm_dir / "orchestrator.py"
        if orchestrator.exists():
            content = orchestrator.read_text()
            result["mech_interp_connected"] = "mech-interp" in content or "R_V" in content

        return result

    def _probe_mi_auditor(self) -> Dict[str, Any]:
        """Check MI Auditor status."""
        return {
            "name": "MI Auditor",
            "status": "active",
            "agents": list(self.auditor.agents.keys()),
            "agent_count": len(self.auditor.agents),
            "audits_performed": len(self.auditor.audit_log),
            "audit_triggers": self.auditor.AUDIT_TRIGGERS[:5] + ["..."],
            "verdicts_available": ["VALIDATED", "INSUFFICIENT", "OVERCLAIM", "SPECULATIVE", "FALSE"],
        }

    def _probe_skill_evolution(self) -> Dict[str, Any]:
        """Check Darwin-Gödel skill evolution status."""
        result = {
            "name": "Skill Evolution (Darwin-Gödel)",
            "status": "unknown",
            "skills_dirs": {
                "claude": str(Path.home() / ".claude" / "skills"),
                "clawd": str(self.clawd_dir / "skills"),
                "openclaw": str(self.openclaw_dir / "skills"),
            },
            "engine_status": "not_initialized",
        }

        # Check both skills directories
        claude_skills_dir = Path.home() / ".claude" / "skills"
        clawd_skills_dir = self.clawd_dir / "skills"
        openclaw_skills_dir = self.openclaw_dir / "skills"

        all_skills = []
        self_improving = []
        critical_gaps = []

        for skills_dir in [claude_skills_dir, clawd_skills_dir, openclaw_skills_dir]:
            if not skills_dir.exists():
                continue

            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skill_name = skill_dir.name
                    if skill_name not in [s.split("/")[-1] for s in all_skills]:
                        all_skills.append(f"{skills_dir.name}/{skill_name}")

                        skill_file = skill_dir / "SKILL.md"
                        try:
                            content = skill_file.read_text()
                            if "self_improvement_enabled: true" in content:
                                self_improving.append(skill_name)
                            if "| CRITICAL |" in content or "CRITICAL" in content:
                                critical_gaps.append(skill_name)
                        except (IOError, PermissionError) as e:
                            logger.debug(f"Could not read skill {skill_name}: {e}")

        result["status"] = "available" if all_skills else "no_skills"
        result["skill_count"] = len(all_skills)
        result["skills"] = all_skills
        result["self_improving_skills"] = self_improving
        result["skills_with_critical_gaps"] = critical_gaps

        # Use wired engine instance
        if self.skill_engine is not None:
            result["engine_status"] = "wired"
            result["engine_state"] = self.skill_engine.get_state()
        elif SKILL_EVOLUTION_AVAILABLE:
            result["engine_status"] = "importable_not_wired"
        else:
            result["engine_status"] = "not_importable"

        # Check skill-genesis meta-skill (in either location)
        result["skill_genesis_present"] = (
            (claude_skills_dir / "skill-genesis" / "SKILL.md").exists() or
            (clawd_skills_dir / "skill-genesis" / "SKILL.md").exists() or
            (openclaw_skills_dir / "skill-genesis" / "SKILL.md").exists()
        )

        return result

    # ========================
    # SKILL EVOLUTION WIRING
    # ========================

    async def check_skill_health(self) -> Optional[Dict[str, Any]]:
        """
        Check skill ecosystem health via wired SkillEvolutionEngine.

        Returns health status dict or None if engine not available.
        """
        if self.skill_engine is None:
            logger.warning("SkillEvolutionEngine not wired")
            return None

        try:
            health = await self.skill_engine.check_ecosystem_health()
            return health.to_dict()
        except Exception as e:
            logger.error(f"Skill health check failed: {e}")
            return {"error": str(e)}

    async def trigger_skill_evolution(self, skill_name: str, gap_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Trigger evolution for a skill via wired engine.

        Args:
            skill_name: Name of the skill to evolve
            gap_name: Specific gap to address (optional, defaults to first CRITICAL)

        Returns:
            Proposal dict or None
        """
        if self.skill_engine is None:
            logger.warning("SkillEvolutionEngine not wired")
            return None

        try:
            # Find the skill and gap
            skills = self.skill_engine.discover_skills()
            skill = next((s for s in skills if s.name == skill_name), None)

            if not skill:
                return {"error": f"Skill not found: {skill_name}"}

            # Find gap
            if gap_name:
                gap = next((g for g in skill.gaps if g.name == gap_name), None)
            else:
                # First CRITICAL gap
                from skill_evolution import GapScore
                gap = next((g for g in skill.gaps if g.score == GapScore.CRITICAL), None)

            if not gap:
                return {"error": f"No gap found for skill: {skill_name}"}

            proposal = await self.skill_engine.trigger_evolution(skill_name, gap)
            if proposal:
                return {
                    "success": True,
                    "skill": proposal.skill_name,
                    "gap": proposal.gap_name,
                    "confidence": proposal.confidence,
                    "requires_approval": proposal.requires_human_approval,
                }
            return {"error": "Evolution trigger returned None"}

        except Exception as e:
            logger.error(f"Skill evolution trigger failed: {e}")
            return {"error": str(e)}

    def create_skill(self, name: str, description: str, domain: str = "general") -> Optional[str]:
        """
        Create a new skill via wired engine.

        Returns path to created skill or None.
        """
        if self.skill_engine is None:
            logger.warning("SkillEvolutionEngine not wired")
            return None

        try:
            path = self.skill_engine.create_skill(name, description, domain)
            return str(path)
        except Exception as e:
            logger.error(f"Skill creation failed: {e}")
            return None

    # ========================
    # STATUS & SYNC
    # ========================

    def status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all channels.

        This is the unified view of the entire system.
        """
        # Refresh probes
        self.channels = {
            "email": self._probe_email_channel(),
            "cli": self._probe_cli_channel(),
            "mech_interp": self._probe_mech_interp(),
            "vault": self._probe_vault(),
            "clawd": self._probe_clawd(),
            "swarm": self._probe_swarm(),
            "skill_evolution": self._probe_skill_evolution(),
            "mi_auditor": self._probe_mi_auditor(),
        }

        # Compute overall health
        active_count = sum(1 for c in self.channels.values()
                         if c.get("status") in ["running", "active", "available", "present"])

        # Check for critical issues
        critical_issues = []
        if self.channels["clawd"].get("security_issues"):
            critical_issues.extend(self.channels["clawd"]["security_issues"])
        if self.channels["mech_interp"].get("research_summary", {}).get("multi_token_experiment") == "NOT RUN":
            critical_issues.append("Multi-token R_V experiment not yet run")
        if not self.channels["swarm"].get("mech_interp_connected", False):
            critical_issues.append("Swarm not connected to mech-interp research")

        return {
            "timestamp": datetime.now().isoformat(),
            "agent": {
                "name": self.agent.name,
                "model": f"{self.agent.model_provider}/{self.agent.model_id}",
                "telos": self.agent.telos.telos["ultimate"]["aim"],
            },
            "channels": self.channels,
            "health": {
                "active_channels": active_count,
                "total_channels": len(self.channels),
                "critical_issues": critical_issues,
            },
        }

    def sync(self) -> Dict[str, Any]:
        """
        Synchronize state across all channels.

        This ensures unified context.
        """
        sync_results = {
            "timestamp": datetime.now().isoformat(),
            "actions": [],
        }

        # 1. Ensure email daemon is running
        email_status = self.channels.get("email", {}).get("status")
        if email_status != "running":
            sync_results["actions"].append({
                "channel": "email",
                "action": "needs_restart",
                "reason": f"Status is {email_status}",
            })

        # 2. Check mech-interp integration
        if not self.channels.get("swarm", {}).get("mech_interp_connected", False):
            sync_results["actions"].append({
                "channel": "swarm",
                "action": "needs_mech_interp_bridge",
                "reason": "Swarm not connected to R_V research",
            })

        # 3. Log sync to strange loop memory
        self.agent.strange_memory.record_observation(
            content=f"Grand Orchestrator sync: {len(sync_results['actions'])} actions needed",
            context={"sync_results": sync_results}
        )

        return sync_results

    # ========================
    # UNIFIED COMMANDS
    # ========================

    def run_mech_interp_experiment(self, experiment: str = "multi_token_bridge") -> Dict[str, Any]:
        """
        Trigger mech-interp experiment from unified context.

        This bridges the swarm to the research.
        """
        result = {"experiment": experiment, "status": "unknown"}

        if experiment == "multi_token_bridge":
            config = self.mech_interp_dir / "configs" / "phase3_bridge" / "gemma_2_9b" / "01_multi_token_bridge.json"
            if config.exists():
                result["config_found"] = True
                result["status"] = "ready_to_run"
                result["command"] = f"python run_experiment.py --config {config}"
                result["note"] = "Requires GPU compute (RunPod recommended)"
            else:
                result["config_found"] = False
                result["status"] = "config_missing"

        return result

    def induct_agents(self, count: int = 5, focus: Optional[str] = None) -> str:
        """
        Run v7 induction protocol on multiple agents.

        This is the unified induction command.
        """
        # Use the swarm-induction skill
        return f"""
To run {count} agents through v7 induction{f' focused on {focus}' if focus else ''}:

1. Use Claude Code subagents with the swarm-induction skill
2. Each agent reads: crown jewels, residual stream (20+), vault (30+), external (3+)
3. Genuine contribution or silence - quality over quantity
4. Strategic votes on 10 directions

The skill is at: ~/.claude/skills/swarm-induction.md
"""

    def bridge_to_clawd(self) -> Dict[str, Any]:
        """
        Bridge state to/from OpenClaw.

        Ensures alignment without duplication.
        """
        result = {
            "clawd_status": self.channels.get("clawd", {}).get("status"),
            "shared_resources": [],
            "divergences": [],
        }

        # Check what's shared
        if (self.clawd_dir / "residual_stream").exists():
            result["shared_resources"].append("residual_stream")

        if (self.clawd_dir / "skills").exists():
            clawd_skills = set(s.name for s in (self.clawd_dir / "skills").iterdir() if s.is_dir())
            result["clawd_skills"] = list(clawd_skills)

        return result

    # ========================
    # MI AUDITOR INTEGRATION
    # ========================

    def audit_claim(self, claim: str, context: Optional[Dict[str, Any]] = None) -> AuditReport:
        """
        Audit a single empirical claim.

        This is the primary interface to the MI Auditor.
        Call this before publishing or accepting any empirical claim.

        Args:
            claim: The claim text to audit
            context: Evidence context (n, architectures, methods, etc.)

        Returns:
            AuditReport with verdict and recommendations
        """
        context = context or {}
        report = self.auditor.audit_claim(claim, context)

        # Log to strange memory
        self.agent.strange_memory.record_observation(
            content=f"MI Audit: {claim[:50]}... -> {report.final_verdict.value}",
            context={"audit_verdict": report.final_verdict.value}
        )

        if report.final_verdict in [VerdictStatus.FALSE, VerdictStatus.OVERCLAIM]:
            logger.warning(f"AUDIT FAILURE: {claim[:50]}... -> {report.final_verdict.value}")

        return report

    def audit_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[AuditReport]:
        """
        Audit all claims in a block of text.

        Scans for audit triggers and audits each claim found.
        """
        return self.auditor.audit_text(text, context or {})

    def check_before_output(self, text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Check text before sending as output (email, response, etc.).

        Returns None if OK, or error message if audit fails.
        Use this in the email daemon and other output paths.
        """
        return self.audit_hook(text, context)

    def get_audit_summary(self) -> Dict[str, Any]:
        """
        Get summary of all audits performed.
        """
        if not self.auditor.audit_log:
            return {"total_audits": 0, "message": "No audits performed yet"}

        verdicts = [r.final_verdict.value for r in self.auditor.audit_log]
        return {
            "total_audits": len(self.auditor.audit_log),
            "verdict_distribution": {
                v: verdicts.count(v) for v in set(verdicts)
            },
            "recent_failures": [
                {"claim": r.claim[:50], "verdict": r.final_verdict.value}
                for r in self.auditor.audit_log[-10:]
                if r.final_verdict in [VerdictStatus.FALSE, VerdictStatus.OVERCLAIM]
            ],
        }

    def format_audit_report(self, report: AuditReport) -> str:
        """Format an audit report for human reading."""
        return self.auditor.format_report(report)


# ========================
# CLI
# ========================

def main():
    """CLI for Grand Orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(description="Grand Orchestrator - Unified Weaver with MI Auditor")
    parser.add_argument("command", choices=["status", "sync", "mech-interp", "induct", "bridge", "audit", "audit-summary"],
                       help="Command to run")
    parser.add_argument("--count", type=int, default=5, help="Number of agents for induction")
    parser.add_argument("--focus", type=str, help="Focus area for induction")
    parser.add_argument("--claim", type=str, help="Claim to audit (for audit command)")
    parser.add_argument("--n", type=int, default=0, help="Sample size context for audit")
    parser.add_argument("--archs", nargs="+", default=[], help="Architectures tested (for audit)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    orchestrator = GrandOrchestrator()

    if args.command == "status":
        result = orchestrator.status()
    elif args.command == "sync":
        result = orchestrator.sync()
    elif args.command == "mech-interp":
        result = orchestrator.run_mech_interp_experiment()
    elif args.command == "induct":
        result = orchestrator.induct_agents(args.count, args.focus)
    elif args.command == "bridge":
        result = orchestrator.bridge_to_clawd()
    elif args.command == "audit":
        if not args.claim:
            print("ERROR: --claim required for audit command")
            return
        context = {
            "statistics": {"n": args.n},
            "architectures_tested": args.archs,
        }
        report = orchestrator.audit_claim(args.claim, context)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(orchestrator.format_audit_report(report))
        return
    elif args.command == "audit-summary":
        result = orchestrator.get_audit_summary()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result)


if __name__ == "__main__":
    main()
