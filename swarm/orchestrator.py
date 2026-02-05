"""Orchestrator for the self-improving agent swarm workflow.

This module coordinates the 5-phase improvement cycle:
1. ANALYZE - AnalyzerAgent scans codebase for issues
2. PROPOSE - ProposerAgent generates improvement proposals
3. EVALUATE - EvaluatorAgent checks proposals against dharmic gates
4. IMPLEMENT - WriterAgent writes approved changes to files
5. TEST - TesterAgent verifies changes don't break tests

Integrations:
- Mech-interp research for informed proposals (research-backed suggestions)
- DGM Archive for evolution tracking and lineage-based selection

Key Classes:
- SwarmOrchestrator: Main coordinator
- WorkflowResult: Result container with metrics
- WorkflowState: Enum tracking execution phase

Usage:
    orchestrator = SwarmOrchestrator()
    result = await orchestrator.execute_improvement_cycle("src/core/")
    
    # Or continuous improvement
    results = await orchestrator.continuous_improvement(max_iterations=5)
"""

import asyncio
import json
import logging
import time
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path

from .analyzer import AnalyzerAgent
from .proposer import ProposerAgent
from .evaluator import EvaluatorAgent
from .writer import WriterAgent
from .tester import TesterAgent

# Mech-interp bridge for research-informed proposals
try:
    from .mech_interp_bridge import MechInterpBridge
    MECH_INTERP_AVAILABLE = True
except ImportError:
    MECH_INTERP_AVAILABLE = False

# DGM Archive for evolution tracking
try:
    from src.dgm.archive import Archive, EvolutionEntry, FitnessScore, get_archive
    DGM_ARCHIVE_AVAILABLE = True
except ImportError:
    DGM_ARCHIVE_AVAILABLE = False

# Enforcement module for rate limits, cost tracking
try:
    from .enforcement import get_enforcer, can_propose, record_proposal, EnforcementResult
    ENFORCEMENT_AVAILABLE = True
except ImportError:
    ENFORCEMENT_AVAILABLE = False

# Interaction logging for systemic risk monitoring
INTERACTION_LOG = Path(__file__).parent.parent / "logs" / "interaction_events.jsonl"

# File locking for multi-agent safety
try:
    from .file_lock import FileLock, FileLockError
    FILE_LOCK_AVAILABLE = True
except ImportError:
    FILE_LOCK_AVAILABLE = False

# Gate runner (Cosmic Krishna Coder)
try:
    from .run_gates import GateRunner
    GATE_RUNNER_AVAILABLE = True
except ImportError:
    GATE_RUNNER_AVAILABLE = False


class WorkflowState(Enum):
    """Workflow execution states."""
    ANALYZING = "analyzing"
    PROPOSING = "proposing"
    EVALUATING = "evaluating"
    WRITING = "writing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    state: WorkflowState
    files_changed: List[str]
    tests_passed: bool
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    evolution_id: Optional[str] = None  # DGM archive entry ID


class SwarmOrchestrator:
    """Orchestrates the self-improving agent swarm workflow.
    
    Integrates with DGM Archive for:
    - Tracking all evolution attempts
    - Lineage-based agent config selection
    - Fitness trend analysis
    """

    def __init__(self, config: Optional[Any] = None) -> None:
        """Initialize the orchestrator with agent instances.

        Args:
            config: Optional SwarmConfig for configuration settings.
                   If None, uses default settings.
        """
        self.config = config
        self.analyzer = AnalyzerAgent()
        self.proposer = ProposerAgent()
        self.evaluator = EvaluatorAgent()
        self.writer = WriterAgent()
        self.tester = TesterAgent()
        self.logger = logging.getLogger(__name__)

        # Store config values for access
        self.model = config.model if config else "claude-sonnet-4-20250514"
        self.max_cycles = config.max_cycles if config else 10
        self.fitness_threshold = config.fitness_threshold if config else 0.8

        # Initialize mech-interp bridge for research-informed proposals
        self.mech_interp = None
        if MECH_INTERP_AVAILABLE:
            try:
                self.mech_interp = MechInterpBridge()
                if self.mech_interp.available:
                    self.logger.info("Mech-interp bridge connected - research informs proposals")
                else:
                    self.logger.warning("Mech-interp directory not found")
            except Exception as e:
                self.logger.warning(f"Mech-interp bridge init failed: {e}")

        # Initialize DGM Archive for evolution tracking
        self.archive: Optional[Archive] = None
        self._last_evolution_id: Optional[str] = None
        if DGM_ARCHIVE_AVAILABLE:
            try:
                self.archive = get_archive()
                self.logger.info(f"DGM Archive connected - {len(self.archive.entries)} entries loaded")
            except Exception as e:
                self.logger.warning(f"DGM Archive init failed: {e}")

        # Initialize enforcement for rate limits and cost tracking
        self.enforcer = None
        if ENFORCEMENT_AVAILABLE:
            try:
                self.enforcer = get_enforcer()
                status = self.enforcer.get_status()
                self.logger.info(f"Enforcement enabled - {status['daily_proposals']}/{status['daily_limit']} proposals today, ${status['daily_cost_usd']:.2f} spent")
            except Exception as e:
                self.logger.warning(f"Enforcement init failed: {e}")

    def _run_cosmic_gates(self, proposal_id: str, dry_run: bool = False):
        """Run the Cosmic Krishna Coder gate runner."""
        if not GATE_RUNNER_AVAILABLE:
            self.logger.warning("Gate runner unavailable; skipping Cosmic Krishna Coder gates")
            return None
        try:
            runner = GateRunner()
            return runner.run_all_gates(proposal_id=proposal_id, dry_run=dry_run)
        except Exception as e:
            self.logger.error(f"Gate runner failed: {e}")
            return None

    def get_research_context(self) -> str:
        """Get mech-interp research context for proposals."""
        if self.mech_interp and self.mech_interp.available:
            return self.mech_interp.get_swarm_context()
        return ""

    def validate_against_research(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a proposal against research findings."""
        if self.mech_interp and self.mech_interp.available:
            return self.mech_interp.validate_proposal(proposal)
        return {"research_aligned": True, "concerns": [], "suggestions": []}

    def _create_evolution_entry(
        self,
        result: 'WorkflowResult',
        component: str = "swarm",
        change_type: str = "mutation",
        description: str = ""
    ) -> Optional[str]:
        """Create and archive an evolution entry from a workflow result.
        
        Args:
            result: The WorkflowResult from the improvement cycle
            component: Component that was modified
            change_type: Type of change (mutation, crossover, ablation)
            description: Human-readable description of changes
            
        Returns:
            Entry ID if archived successfully, None otherwise
        """
        if not self.archive:
            return None
        
        try:
            # Calculate fitness from metrics
            metrics = result.metrics or {}
            
            fitness = FitnessScore(
                correctness=1.0 if result.tests_passed else 0.3,
                dharmic_alignment=metrics.get("evaluation_score", 0.5),
                elegance=min(1.0, 1.0 - (len(result.files_changed) * 0.1)),  # Smaller changes = more elegant
                efficiency=0.7,  # Default; could be measured
                safety=1.0 if result.tests_passed else 0.5
            )
            
            # Determine gates passed based on results
            gates_passed = []
            gates_failed = []
            
            if result.tests_passed:
                gates_passed.extend(["ahimsa", "vyavasthit"])  # Non-harm, order
            else:
                gates_failed.append("vyavasthit")
            
            if metrics.get("evaluation_score", 0) >= 0.7:
                gates_passed.append("satya")  # Truth/correctness
            else:
                gates_failed.append("satya")
            
            # Create the entry
            entry = EvolutionEntry(
                id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                parent_id=self._last_evolution_id,
                component=component,
                change_type=change_type,
                description=description or f"Modified {len(result.files_changed)} files",
                diff="",  # Could capture actual diff here
                fitness=fitness,
                test_results={
                    "passed": result.tests_passed,
                    "tests_run": metrics.get("tests_run", 0),
                    "files_changed": result.files_changed
                },
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                agent_id="swarm_orchestrator",
                model=self.model,
                status="applied" if result.state == WorkflowState.COMPLETED else "proposed"
            )
            
            entry_id = self.archive.add_entry(entry)
            self._last_evolution_id = entry_id
            self.logger.info(f"Archived evolution entry: {entry_id} (fitness: {fitness.total():.2f})")
            
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Failed to create evolution entry: {e}")
            return None

    def get_fitness_trend(
        self, 
        component: Optional[str] = None,
        n_recent: int = 20
    ) -> Dict[str, Any]:
        """Query archive for fitness trends over time.
        
        Args:
            component: Optional component filter
            n_recent: Number of recent entries to analyze
            
        Returns:
            Dict with trend analysis including:
            - timeline: List of (timestamp, fitness) tuples
            - trend: 'improving', 'stable', or 'declining'
            - average_fitness: Mean fitness score
            - best_fitness: Maximum fitness achieved
            - improvement_rate: Fitness delta per entry
        """
        if not self.archive:
            return {
                "available": False,
                "message": "DGM Archive not available"
            }
        
        # Get fitness over time from archive
        timeline = self.archive.fitness_over_time(component)
        
        if not timeline:
            return {
                "available": True,
                "timeline": [],
                "trend": "unknown",
                "average_fitness": 0.0,
                "best_fitness": 0.0,
                "entries_analyzed": 0
            }
        
        # Limit to recent entries
        timeline = timeline[-n_recent:]
        fitness_values = [f for _, f in timeline]
        
        # Calculate trend
        if len(fitness_values) >= 2:
            first_half = sum(fitness_values[:len(fitness_values)//2]) / (len(fitness_values)//2)
            second_half = sum(fitness_values[len(fitness_values)//2:]) / (len(fitness_values) - len(fitness_values)//2)
            
            delta = second_half - first_half
            if delta > 0.05:
                trend = "improving"
            elif delta < -0.05:
                trend = "declining"
            else:
                trend = "stable"
            
            improvement_rate = delta / (len(fitness_values) // 2)
        else:
            trend = "unknown"
            improvement_rate = 0.0
        
        return {
            "available": True,
            "timeline": timeline,
            "trend": trend,
            "average_fitness": sum(fitness_values) / len(fitness_values),
            "best_fitness": max(fitness_values),
            "worst_fitness": min(fitness_values),
            "entries_analyzed": len(fitness_values),
            "improvement_rate": improvement_rate,
            "component": component
        }

    def select_best_agent_config(
        self,
        component: Optional[str] = None,
        min_fitness: float = 0.6
    ) -> Dict[str, Any]:
        """Select the best agent configuration using archive lineage.
        
        Analyzes successful evolution entries to determine optimal
        configuration for future runs.
        
        Args:
            component: Optional component to focus on
            min_fitness: Minimum fitness threshold for consideration
            
        Returns:
            Dict with recommended configuration including:
            - model: Recommended model based on successful runs
            - change_types: Most successful change types
            - lineage_depth: Optimal ancestry chain length
            - config_source: Entry ID this config derives from
        """
        if not self.archive:
            return {
                "available": False,
                "message": "DGM Archive not available",
                "config": self._default_config()
            }
        
        # Get best entries
        best_entries = self.archive.get_best(n=10, component=component)
        
        if not best_entries:
            return {
                "available": True,
                "message": "No successful entries in archive",
                "config": self._default_config()
            }
        
        # Filter by minimum fitness
        qualifying = [e for e in best_entries if e.fitness.total() >= min_fitness]
        
        if not qualifying:
            return {
                "available": True,
                "message": f"No entries meet fitness threshold {min_fitness}",
                "config": self._default_config(),
                "best_available_fitness": best_entries[0].fitness.total() if best_entries else 0
            }
        
        # Analyze successful patterns
        top_entry = qualifying[0]
        
        # Count successful change types
        change_type_scores: Dict[str, List[float]] = {}
        model_scores: Dict[str, List[float]] = {}
        
        for entry in qualifying:
            ct = entry.change_type or "unknown"
            if ct not in change_type_scores:
                change_type_scores[ct] = []
            change_type_scores[ct].append(entry.fitness.total())
            
            model = entry.model or "unknown"
            if model not in model_scores:
                model_scores[model] = []
            model_scores[model].append(entry.fitness.total())
        
        # Find best change type and model
        best_change_type = max(
            change_type_scores.keys(),
            key=lambda k: sum(change_type_scores[k]) / len(change_type_scores[k])
        )
        
        best_model = max(
            model_scores.keys(),
            key=lambda k: sum(model_scores[k]) / len(model_scores[k])
        )
        
        # Analyze lineage depth for top entry
        lineage = self.archive.get_lineage(top_entry.id)
        lineage_depth = len(lineage)
        
        # Calculate gates success rate
        gates_success = {}
        for entry in qualifying:
            for gate in entry.gates_passed:
                gates_success[gate] = gates_success.get(gate, 0) + 1
        
        total_qualifying = len(qualifying)
        gates_rate = {k: v / total_qualifying for k, v in gates_success.items()}
        
        return {
            "available": True,
            "config": {
                "model": best_model if best_model != "unknown" else self.model,
                "preferred_change_type": best_change_type,
                "fitness_threshold": min_fitness,
                "max_cycles": self.max_cycles
            },
            "config_source": top_entry.id,
            "source_fitness": top_entry.fitness.total(),
            "lineage_depth": lineage_depth,
            "change_type_effectiveness": {
                k: sum(v) / len(v) for k, v in change_type_scores.items()
            },
            "model_effectiveness": {
                k: sum(v) / len(v) for k, v in model_scores.items()
            },
            "gates_success_rate": gates_rate,
            "entries_analyzed": len(qualifying),
            "recommendation": f"Use {best_change_type} changes with {best_model} (avg fitness: {sum(change_type_scores[best_change_type])/len(change_type_scores[best_change_type]):.2f})"
        }
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration when archive unavailable."""
        return {
            "model": self.model,
            "preferred_change_type": "mutation",
            "fitness_threshold": self.fitness_threshold,
            "max_cycles": self.max_cycles
        }

    def _log_interaction(
        self,
        sender: str,
        recipient: str,
        event_type: str,
        size: int = 0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a lightweight interaction event for systemic monitoring."""
        try:
            INTERACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": time.time(),
                "sender": sender,
                "recipient": recipient,
                "event_type": event_type,
                "size": size,
            }
            if meta:
                entry["meta"] = meta
            with open(INTERACTION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            self.logger.debug(f"Interaction log write failed: {e}")

    async def execute_improvement_cycle(
        self, 
        target_area: Optional[str] = None
    ) -> WorkflowResult:
        """Execute a complete improvement cycle."""
        try:
            # Phase 1: Analysis
            self.logger.info("Starting analysis phase")
            self._log_interaction("orchestrator", "analyzer", "analysis_start")
            analysis = await self.analyzer.analyze_codebase(target_area)
            self._log_interaction(
                "analyzer",
                "orchestrator",
                "analysis_complete",
                size=len(analysis.issues) if analysis else 0,
            )
            if not analysis.issues:
                return WorkflowResult(
                    state=WorkflowState.COMPLETED,
                    files_changed=[],
                    tests_passed=True,
                    metrics={"issues_found": 0}
                )

            # Phase 2: Proposal generation (with enforcement check)
            self.logger.info("Starting proposal phase")
            self._log_interaction("orchestrator", "proposer", "proposal_start")

            # Check enforcement limits before proposing
            proposal_id = f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            if self.enforcer:
                check = self.enforcer.can_propose()
                if not check.allowed:
                    self.logger.warning(f"Proposal blocked by enforcement: {check.reason}")
                    return WorkflowResult(
                        state=WorkflowState.FAILED,
                        files_changed=[],
                        tests_passed=False,
                        error_message=f"Rate limit: {check.reason}"
                    )
                self.logger.info(f"Enforcement check passed - ${check.budget_remaining_usd:.2f} budget remaining")

            proposals = await self.proposer.generate_proposals(analysis)
            self._log_interaction(
                "proposer",
                "orchestrator",
                "proposal_complete",
                size=len(proposals) if proposals else 0,
            )
            if not proposals:
                # Record failed proposal attempt
                if self.enforcer:
                    self.enforcer.record_proposal(proposal_id, success=False)
                return WorkflowResult(
                    state=WorkflowState.FAILED,
                    files_changed=[],
                    tests_passed=False,
                    error_message="No viable proposals generated"
                )

            # Phase 3: Evaluation (17-gate protocol)
            self.logger.info("Starting evaluation phase - running 17 gates")
            self._log_interaction("orchestrator", "evaluator", "evaluation_start")
            evaluation = await self.evaluator.evaluate_proposals(
                proposals,
                proposal_id=proposal_id,
                dry_run=False
            )
            self._log_interaction(
                "evaluator",
                "orchestrator",
                "evaluation_complete",
                meta={
                    "passed": evaluation.gates_passed,
                    "failed": evaluation.gates_failed,
                    "warned": evaluation.gates_warned,
                },
            )
            
            # Log gate results
            self.logger.info(
                f"Gate results: {evaluation.gates_passed} passed, "
                f"{evaluation.gates_failed} failed, "
                f"{evaluation.gates_warned} warned"
            )
            if evaluation.evidence_bundle_hash:
                self.logger.info(f"Evidence bundle: {evaluation.evidence_bundle_hash[:16]}...")
            
            approved_proposals = [p for p in evaluation.proposals if p.approved]
            
            if not approved_proposals:
                self.logger.error("All proposals failed gate evaluation")
                # Record failed proposal
                if self.enforcer:
                    self.enforcer.record_proposal(proposal_id, success=False)
                return WorkflowResult(
                    state=WorkflowState.FAILED,
                    files_changed=[],
                    tests_passed=False,
                    error_message="No proposals passed evaluation"
                )

            # Phase 4: Implementation (with file locking)
            self.logger.info("Starting implementation phase")
            self._log_interaction("orchestrator", "writer", "implementation_start")

            # If file locking available, lock target files
            locked_files = []
            if FILE_LOCK_AVAILABLE:
                for proposal in approved_proposals:
                    for file_path in getattr(proposal, 'target_files', []):
                        try:
                            lock = FileLock(file_path, agent_id="CODING_AGENT", ttl=300)
                            lock.acquire()
                            locked_files.append(lock)
                        except FileLockError as e:
                            self.logger.warning(f"Could not lock {file_path}: {e}")

            try:
                implementation = await self.writer.implement_proposals(approved_proposals)
            finally:
                # Release all locks
                for lock in locked_files:
                    try:
                        lock.release()
                    except Exception as e:
                        self.logger.warning(f"Error releasing lock: {e}")
            self._log_interaction(
                "writer",
                "orchestrator",
                "implementation_complete",
                size=len(implementation.files_changed) if implementation else 0,
            )
            
            # Phase 5: Testing
            self.logger.info("Starting testing phase")
            self._log_interaction("orchestrator", "tester", "testing_start")
            test_result = await self.tester.run_tests(implementation.files_changed)
            self._log_interaction(
                "tester",
                "orchestrator",
                "testing_complete",
                meta={
                    "tests_run": test_result.tests_run,
                    "passed": test_result.passed,
                },
            )

            # Phase 6: Cosmic Krishna Coder gates (run even if tests fail)
            gate_result = None
            live_allowed = os.getenv("DGC_ALLOW_LIVE") == "1"
            force_gates = os.getenv("DGC_FORCE_GATES") == "1"
            if live_allowed or force_gates:
                self.logger.info("Starting Cosmic Krishna Coder gate runner")
                gate_result = self._run_cosmic_gates(
                    proposal_id=proposal_id,
                    dry_run=not live_allowed
                )
                if gate_result is None:
                    if self.enforcer:
                        self.enforcer.record_proposal(proposal_id, success=False)
                    return WorkflowResult(
                        state=WorkflowState.FAILED,
                        files_changed=implementation.files_changed,
                        tests_passed=test_result.passed,
                        error_message="Gate runner failed or unavailable",
                    )
                if gate_result.overall_result == "FAIL":
                    if self.enforcer:
                        self.enforcer.record_proposal(proposal_id, success=False)
                    return WorkflowResult(
                        state=WorkflowState.FAILED,
                        files_changed=implementation.files_changed,
                        tests_passed=test_result.passed,
                        error_message="Gate runner reported FAIL",
                        metrics={
                            "tests_failed_pre_gate": not test_result.passed,
                            "gate_overall": gate_result.overall_result,
                            "gate_evidence_hash": gate_result.evidence_bundle_hash,
                            "gates_failed": gate_result.gates_failed,
                            "gates_warned": gate_result.gates_warned,
                        }
                    )

            result = WorkflowResult(
                state=WorkflowState.COMPLETED if test_result.passed else WorkflowState.FAILED,
                files_changed=implementation.files_changed,
                tests_passed=test_result.passed,
                metrics={
                    "issues_found": len(analysis.issues),
                    "proposals_generated": len(proposals),
                    "proposals_approved": len(approved_proposals),
                    "files_modified": len(implementation.files_changed),
                    "tests_run": test_result.tests_run,
                    "evaluation_score": evaluation.overall_score,
                    "tests_failed_pre_gate": not test_result.passed,
                    "gate_overall": gate_result.overall_result if gate_result else "skipped",
                    "gate_evidence_hash": gate_result.evidence_bundle_hash if gate_result else "",
                    "gates_failed": gate_result.gates_failed if gate_result else 0,
                    "gates_warned": gate_result.gates_warned if gate_result else 0,
                }
            )
            
            # Archive successful run to DGM
            if result.state == WorkflowState.COMPLETED:
                evolution_id = self._create_evolution_entry(
                    result,
                    component=target_area or "swarm",
                    change_type="mutation",
                    description=f"Addressed {len(analysis.issues)} issues"
                )
                result.evolution_id = evolution_id
                self._log_interaction(
                    "orchestrator",
                    "archive",
                    "evolution_archived",
                    meta={"evolution_id": evolution_id},
                )

                # Record successful proposal to enforcement
                if self.enforcer:
                    self.enforcer.record_proposal(
                        proposal_id,
                        success=True,
                        cost_usd=0.01 * len(approved_proposals)  # Estimate
                    )
            else:
                # Record failed proposal
                if self.enforcer:
                    self.enforcer.record_proposal(proposal_id, success=False)

            return result

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return WorkflowResult(
                state=WorkflowState.FAILED,
                files_changed=[],
                tests_passed=False,
                error_message=str(e)
            )

    async def continuous_improvement(
        self, 
        max_iterations: int = 10,
        improvement_threshold: float = 0.1
    ) -> List[WorkflowResult]:
        """Run continuous improvement cycles until convergence."""
        results = []
        
        for iteration in range(max_iterations):
            self.logger.info(f"Starting improvement iteration {iteration + 1}")
            
            result = await self.execute_improvement_cycle()
            results.append(result)
            
            if result.state == WorkflowState.FAILED:
                self.logger.warning(f"Iteration {iteration + 1} failed: {result.error_message}")
                break
                
            if not result.files_changed:
                self.logger.info("No improvements needed, stopping")
                break
                
            # Check if improvements are diminishing
            if (len(results) >= 2 and 
                result.metrics and results[-2].metrics and
                result.metrics.get("issues_found", 0) > 
                results[-2].metrics.get("issues_found", 0) * (1 - improvement_threshold)):
                self.logger.info("Improvements below threshold, stopping")
                break
                
            # Brief pause between iterations
            await asyncio.sleep(1)
        
        return results

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status and metrics."""
        status = {
            "agents_active": 5,
            "workflow_phases": len(WorkflowState),
            "evaluation_enabled": True,
            "dgm_archive_available": self.archive is not None,
        }
        
        # Add archive stats if available
        if self.archive:
            status["archive_entries"] = len(self.archive.entries)
            trend = self.get_fitness_trend(n_recent=10)
            status["fitness_trend"] = trend.get("trend", "unknown")
            status["average_fitness"] = trend.get("average_fitness", 0.0)
        
        return status

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status for run_swarm.py compatibility."""
        return {
            "current_state": "ready",
            "cycles_completed": 0,
            "baseline_fitness": 0.5,
            "model": self.model,
            "max_cycles": self.max_cycles,
            **self.get_workflow_status()
        }

    async def run_cycles(
        self,
        n: int = 1,
        dry_run: bool = False,
        target_area: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Run n improvement cycles.
        
        Args:
            n: Number of cycles to run
            dry_run: If True, don't actually modify files
            
        Returns:
            List of result dicts compatible with run_swarm.py
        """
        results = []
        
        # Get recommended config from archive before starting
        if self.archive and not dry_run:
            best_config = self.select_best_agent_config()
            if best_config.get("available"):
                self.logger.info(f"Using archive-optimized config: {best_config.get('recommendation', 'default')}")
        
        for i in range(n):
            self.logger.info(f"Starting cycle {i+1}/{n} (dry_run={dry_run})")
            
            if dry_run:
                # In dry run, just analyze but don't modify
                analysis = await self.analyzer.analyze_codebase(target_area)
                issues_found = len(analysis.issues) if analysis else 0
                results.append({
                    "cycle": i + 1,
                    "result": "success",
                    "files_changed": [],
                    "tests_passed": True,
                    "metrics": {
                        "issues_found": issues_found,
                        "dry_run": True
                    },
                    "fitness": 0.5 + (0.1 * (i + 1)),  # Simulated improvement
                    "evolution_id": None
                })
            else:
                workflow_result = await self.execute_improvement_cycle(target_area)
                
                # Map WorkflowState to result string
                result_map = {
                    WorkflowState.COMPLETED: "success",
                    WorkflowState.FAILED: "error",
                }
                
                # Calculate actual fitness from archive entry if available
                fitness = 0.5
                if workflow_result.evolution_id and self.archive:
                    entry = self.archive.get_entry(workflow_result.evolution_id)
                    if entry:
                        fitness = entry.fitness.total()
                
                results.append({
                    "cycle": i + 1,
                    "result": result_map.get(workflow_result.state, "refined"),
                    "files_changed": workflow_result.files_changed,
                    "tests_passed": workflow_result.tests_passed,
                    "metrics": workflow_result.metrics or {},
                    "fitness": fitness,
                    "evolution_id": workflow_result.evolution_id
                })
                
                if workflow_result.state == WorkflowState.FAILED:
                    break
        
        # Log fitness trend after cycles complete
        if results and self.archive:
            trend = self.get_fitness_trend(n_recent=len(results))
            self.logger.info(f"Fitness trend after {len(results)} cycles: {trend.get('trend', 'unknown')}")
        
        return results


# Aliases for backward compatibility with __init__.py
Orchestrator = SwarmOrchestrator
CycleResult = WorkflowResult
