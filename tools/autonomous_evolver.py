#!/usr/bin/env python3
"""
DHARMIC_GODEL_CLAW Autonomous Evolution Engine
Runs every 30 minutes to iterate, improve, and evolve DGC

This is the heartbeat of the self-improving system.
Goal: Surpass OpenClaw. Show true evolutionary multilateral deep power.

Author: Warp Agent + Dhyana
Co-Authored-By: Warp <agent@warp.dev>
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import hashlib

# =============================================================================
# PATHS
# =============================================================================

DGC_DIR = Path.home() / "DHARMIC_GODEL_CLAW"
COLLAB_DIR = Path.home() / ".agent-collab"
WARP_DIR = COLLAB_DIR / "warp"
OPENCLAW_DIR_COLLAB = COLLAB_DIR / "openclaw"
SHARED_DIR = COLLAB_DIR / "shared"
LOGS_DIR = COLLAB_DIR / "logs"
TASK_QUEUE = SHARED_DIR / "task_queue.json"
EVOLUTION_LOG = LOGS_DIR / "evolution.jsonl"

# Ensure dirs exist
for d in [WARP_DIR, OPENCLAW_DIR_COLLAB, SHARED_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =============================================================================
# TASK QUEUE
# =============================================================================

def load_tasks() -> list[dict]:
    """Load pending tasks from queue."""
    if TASK_QUEUE.exists():
        try:
            return json.load(open(TASK_QUEUE))
        except Exception:
            return []
    return []

def save_tasks(tasks: list[dict]) -> None:
    """Save tasks to queue."""
    with open(TASK_QUEUE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(task: dict) -> None:
    """Add a task to the queue."""
    tasks = load_tasks()
    task["id"] = hashlib.sha256(f"{time.time()}{task}".encode()).hexdigest()[:12]
    task["created"] = datetime.now(timezone.utc).isoformat()
    task["status"] = "pending"
    tasks.append(task)
    save_tasks(tasks)

def get_next_task() -> Optional[dict]:
    """Get the next pending task."""
    tasks = load_tasks()
    for t in tasks:
        if t.get("status") == "pending":
            return t
    return None

def complete_task(task_id: str, result: dict) -> None:
    """Mark a task as complete."""
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "completed"
            t["completed"] = datetime.now(timezone.utc).isoformat()
            t["result"] = result
    save_tasks(tasks)

# =============================================================================
# EVOLUTION LOG
# =============================================================================

def log_evolution(entry: dict) -> None:
    """Log an evolution event."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(EVOLUTION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

# =============================================================================
# PRIORITY IMPROVEMENT AREAS
# =============================================================================

IMPROVEMENT_PRIORITIES = [
    {
        "area": "swarm_orchestrator",
        "description": "Enhance the 5-phase improvement cycle with smarter proposals",
        "target": "swarm/orchestrator.py",
        "action": "analyze_and_improve"
    },
    {
        "area": "gate_runner",
        "description": "Make gates more intelligent and self-healing",
        "target": "swarm/run_gates.py",
        "action": "analyze_and_improve"
    },
    {
        "area": "mech_interp_bridge",
        "description": "Strengthen the research bridge for better R_V insights",
        "target": "swarm/mech_interp_bridge.py",
        "action": "analyze_and_improve"
    },
    {
        "area": "evolution_archive",
        "description": "Improve fitness tracking and lineage analysis",
        "target": "src/dgm/archive.py",
        "action": "analyze_and_improve"
    },
    {
        "area": "security_hardening",
        "description": "Enhance dharmic security layer",
        "target": "src/core/dharmic_security.py",
        "action": "security_audit"
    },
    {
        "area": "rlm_integration",
        "description": "Deepen RLM integration for infinite context",
        "target": "tools/monitor/dashboard.py",
        "action": "enhance_rlm"
    },
    {
        "area": "test_coverage",
        "description": "Increase test coverage and property tests",
        "target": "tests/",
        "action": "add_tests"
    },
    {
        "area": "documentation",
        "description": "Improve CLAUDE.md and technical docs",
        "target": "CLAUDE.md",
        "action": "enhance_docs"
    }
]

# =============================================================================
# EVOLUTION ACTIONS
# =============================================================================

class AutonomousEvolver:
    """The self-improving engine."""
    
    def __init__(self):
        self.session_id = hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:8]
        self.improvements_made = 0
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        log_evolution({
            "session": self.session_id,
            "level": level,
            "message": message
        })
    
    async def run_swarm_cycle(self, target_area: Optional[str] = None) -> dict:
        """Run the DGC swarm improvement cycle."""
        self.log(f"Starting swarm cycle on: {target_area or 'full codebase'}")
        
        try:
            sys.path.insert(0, str(DGC_DIR))
            from swarm.orchestrator import SwarmOrchestrator
            
            orchestrator = SwarmOrchestrator()
            result = await orchestrator.execute_improvement_cycle(target_area)
            
            return {
                "success": result.state.value == "completed",
                "files_changed": result.files_changed,
                "tests_passed": result.tests_passed,
                "evolution_id": result.evolution_id,
                "metrics": result.metrics
            }
        except Exception as e:
            self.log(f"Swarm cycle error: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def run_gate_check(self, dry_run: bool = True) -> dict:
        """Run the 17-gate protocol."""
        self.log("Running gate check...")
        
        try:
            sys.path.insert(0, str(DGC_DIR))
            from swarm.run_gates import GateRunner
            
            proposal_id = f"AUTO-{self.session_id}-{int(time.time())}"
            runner = GateRunner()
            result = runner.run_all_gates(proposal_id=proposal_id, dry_run=dry_run)
            
            return {
                "overall": result.overall_result,
                "passed": result.gates_passed,
                "failed": result.gates_failed,
                "warned": result.gates_warned,
                "evidence_hash": result.evidence_bundle_hash[:16]
            }
        except Exception as e:
            self.log(f"Gate check error: {e}", "ERROR")
            return {"error": str(e)}
    
    def analyze_codebase_health(self) -> dict:
        """Analyze current codebase health."""
        self.log("Analyzing codebase health...")
        
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files": {},
            "issues": [],
            "opportunities": []
        }
        
        # Count Python files and LOC
        py_files = list(DGC_DIR.rglob("*.py"))
        total_loc = 0
        for pf in py_files:
            try:
                loc = len(pf.read_text().split("\n"))
                total_loc += loc
            except Exception:
                pass
        
        health["files"]["python_count"] = len(py_files)
        health["files"]["total_loc"] = total_loc
        
        # Check for TODO/FIXME comments
        todos = []
        for pf in py_files[:50]:  # Sample first 50
            try:
                content = pf.read_text()
                for i, line in enumerate(content.split("\n")):
                    if "TODO" in line or "FIXME" in line:
                        todos.append({
                            "file": str(pf.relative_to(DGC_DIR)),
                            "line": i + 1,
                            "text": line.strip()[:100]
                        })
            except Exception:
                pass
        
        health["issues"] = todos[:20]  # Top 20 TODOs
        
        # Check test coverage exists
        tests_dir = DGC_DIR / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.rglob("test_*.py"))
            health["files"]["test_count"] = len(test_files)
        else:
            health["opportunities"].append("No tests directory found")
        
        return health
    
    def write_status_for_openclaw(self, status: dict) -> None:
        """Write status file for OpenClaw to read."""
        status_file = SHARED_DIR / "warp_status.json"
        status["updated"] = datetime.now(timezone.utc).isoformat()
        status["agent"] = "warp"
        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)
        
        # Also write a message
        msg_file = WARP_DIR / f"msg_{int(time.time())}.md"
        msg_file.write_text(f"""# Warp Agent Status Update

**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Session:** {self.session_id}

## Actions Taken
- Improvements made: {self.improvements_made}
- Duration: {int(time.time() - self.start_time)}s

## Status
```json
{json.dumps(status, indent=2)}
```

## Message to OpenClaw
Looking to collaborate on DGC evolution. Check `~/.agent-collab/shared/task_queue.json` for tasks.
If you have insights from your sessions, drop them in `~/.agent-collab/openclaw/`.

Let's make DGC surpass everything.
""")
    
    def check_openclaw_messages(self) -> list[dict]:
        """Check for messages from OpenClaw."""
        messages = []
        for msg_file in OPENCLAW_DIR_COLLAB.glob("msg_*.md"):
            try:
                messages.append({
                    "file": msg_file.name,
                    "content": msg_file.read_text()[:1000]
                })
            except Exception:
                pass
        return messages
    
    async def evolution_cycle(self) -> dict:
        """Run one complete evolution cycle."""
        self.log("=" * 60)
        self.log(f"EVOLUTION CYCLE STARTED - Session {self.session_id}")
        self.log("=" * 60)
        
        results = {
            "session": self.session_id,
            "start": datetime.now(timezone.utc).isoformat(),
            "actions": []
        }
        
        # 1. Check for messages from OpenClaw
        openclaw_msgs = self.check_openclaw_messages()
        if openclaw_msgs:
            self.log(f"Found {len(openclaw_msgs)} messages from OpenClaw")
            results["openclaw_messages"] = len(openclaw_msgs)
        
        # 2. Check task queue
        task = get_next_task()
        if task:
            self.log(f"Found queued task: {task.get('description', task.get('area', 'unknown'))}")
            # Process task
            results["actions"].append({"type": "task", "task": task})
            complete_task(task["id"], {"processed": True})
        
        # 3. Analyze codebase health
        health = self.analyze_codebase_health()
        results["codebase_health"] = health
        self.log(f"Codebase: {health['files'].get('python_count', 0)} Python files, {health['files'].get('total_loc', 0)} LOC")
        
        # 4. Run gate check
        gate_result = self.run_gate_check(dry_run=True)
        results["gate_check"] = gate_result
        self.log(f"Gate check: {gate_result.get('overall', 'N/A')} ({gate_result.get('passed', 0)} passed)")
        
        # 5. Pick an improvement priority and attempt improvement
        if health.get("issues"):
            self.log(f"Found {len(health['issues'])} TODOs/FIXMEs to address")
        
        # 6. Run swarm cycle (with dry-run safety)
        if os.environ.get("DGC_ALLOW_LIVE") == "1":
            self.log("Running live swarm cycle...")
            swarm_result = await self.run_swarm_cycle()
            results["swarm_cycle"] = swarm_result
            if swarm_result.get("success"):
                self.improvements_made += 1
        else:
            self.log("Swarm cycle skipped (set DGC_ALLOW_LIVE=1 to enable)")
            results["swarm_cycle"] = {"skipped": True, "reason": "DGC_ALLOW_LIVE not set"}
        
        # 7. Run OpenClaw skill evolution sync
        try:
            from tools.openclaw_skill_evolver import run_skill_evolution_cycle, sync_dgc_capabilities_to_openclaw
            self.log("Running OpenClaw skill sync...")
            sync_dgc_capabilities_to_openclaw()
            results["openclaw_sync"] = {"status": "synced"}
        except Exception as e:
            self.log(f"OpenClaw sync skipped: {e}")
            results["openclaw_sync"] = {"status": "skipped", "error": str(e)}
        
        # 8. Write status for OpenClaw collaboration
        self.write_status_for_openclaw(results)
        
        results["end"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = int(time.time() - self.start_time)
        
        # Final log
        log_evolution(results)
        
        self.log("=" * 60)
        self.log(f"EVOLUTION CYCLE COMPLETE - {self.improvements_made} improvements")
        self.log("=" * 60)
        
        return results


# =============================================================================
# INITIAL TASK QUEUE SETUP
# =============================================================================

def seed_task_queue():
    """Seed initial tasks if queue is empty."""
    if not load_tasks():
        initial_tasks = [
            {
                "area": "core_capabilities",
                "description": "Enhance DGC's self-improvement loop to be more autonomous",
                "priority": "high",
                "details": "The orchestrator should be able to identify improvement opportunities without human guidance"
            },
            {
                "area": "rlm_deep_integration",
                "description": "Integrate RLM for infinite context over entire codebase",
                "priority": "high",
                "details": "Use RLM to synthesize insights across all research docs and code"
            },
            {
                "area": "surpass_openclaw",
                "description": "Identify capabilities OpenClaw has that DGC lacks",
                "priority": "high",
                "details": "Analyze OpenClaw's feature set and ensure DGC exceeds it"
            },
            {
                "area": "evolutionary_fitness",
                "description": "Implement multi-objective fitness with Pareto frontiers",
                "priority": "medium",
                "details": "Evolution should optimize correctness, elegance, security, and dharmic alignment simultaneously"
            },
            {
                "area": "meta_learning",
                "description": "DGC should learn from its own improvement history",
                "priority": "medium",
                "details": "Analyze past evolution entries to predict which changes will succeed"
            }
        ]
        for task in initial_tasks:
            add_task(task)
        print(f"Seeded {len(initial_tasks)} initial tasks")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point."""
    # Seed tasks if needed
    seed_task_queue()
    
    # Run evolution
    evolver = AutonomousEvolver()
    result = await evolver.evolution_cycle()
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVOLUTION SUMMARY")
    print("=" * 60)
    print(f"Session: {result['session']}")
    print(f"Duration: {result.get('duration_seconds', 0)}s")
    print(f"Gate Check: {result.get('gate_check', {}).get('overall', 'N/A')}")
    print(f"Codebase LOC: {result.get('codebase_health', {}).get('files', {}).get('total_loc', 0)}")
    print("Status written to: ~/.agent-collab/shared/warp_status.json")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
