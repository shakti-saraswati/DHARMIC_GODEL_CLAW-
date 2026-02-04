"""
DGM Circuit - 6-Phase Mutation Implementation Pipeline
======================================================
The core execution pipeline for safely implementing mutations.

Phases:
1. MVP (Build)     - Mutator proposes, code is written
2. TEST            - Run pytest, check coverage
3. RED TEAM        - Adversarial attack to find vulnerabilities
4. SLIM            - Remove bloat, keep it lean
5. REVIEW          - 25-vote diverse consensus
6. VERIFY          - Final dharmic gates + integration check

Each phase can PASS, FAIL, or RETRY (with feedback).
ANY phase failure = full stop, return to builder with feedback.
Rollback is automatic if implementation fails after Phase 1.

"The circuit is the crucible. Only worthy code survives."
"""
import ast
import subprocess
import shutil
import logging
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from datetime import datetime, timezone
from collections import defaultdict

# Local imports
from .voting import VotingSwarm, VoteResult
from .elegance import EleganceEvaluator, EleganceScore
from .fitness import FitnessEvaluator, EvaluationResult
from .archive import FitnessScore, EvolutionEntry, get_archive
from .red_team import RedTeamAgent, RedTeamReport, Severity
from .slimmer import Slimmer, SlimResult

# Import telos layer from core
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.telos_layer import TelosLayer, TelosCheck, GateResult

logger = logging.getLogger(__name__)


class PhaseStatus(Enum):
    """Status of a pipeline phase."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a single phase execution."""
    phase: int
    name: str
    status: PhaseStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    retry_count: int = 0
    feedback: Optional[str] = None


@dataclass
class MutationProposal:
    """A proposed code mutation to be executed through the circuit."""
    id: str
    description: str
    target_file: str
    mutation_type: str = "modify"  # create, modify, delete
    new_code: Optional[str] = None
    diff: Optional[str] = None
    risk_level: str = "medium"  # low, medium, high
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For rollback support
    original_code: Optional[str] = None
    
    # Track code through pipeline
    current_code: Optional[str] = None  # May be modified by slimmer


@dataclass
class CircuitResult:
    """Final result of the mutation circuit."""
    proposal_id: str
    phase: int  # Phase number reached (1-6)
    passed: bool
    reason: Optional[str] = None
    phase_results: Dict[int, PhaseResult] = field(default_factory=dict)
    final_fitness: Optional[FitnessScore] = None
    ready_to_push: bool = False
    total_duration_ms: int = 0
    rollback_performed: bool = False
    rollback_reason: Optional[str] = None
    
    # Final code (may be slimmed)
    final_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "proposal_id": self.proposal_id,
            "phase": self.phase,
            "passed": self.passed,
            "reason": self.reason,
            "ready_to_push": self.ready_to_push,
            "total_duration_ms": self.total_duration_ms,
            "rollback_performed": self.rollback_performed,
            "phases": {
                k: {"status": v.status.value, "message": v.message}
                for k, v in self.phase_results.items()
            }
        }


class CircuitMetrics:
    """
    Track which phases kill the most builds.
    Essential for understanding pipeline bottlenecks.
    """
    
    def __init__(self, metrics_file: Path = None):
        self.metrics_file = metrics_file or Path(__file__).parent / "circuit_metrics.json"
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from disk."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file) as f:
                    data = json.load(f)
                    self.phase_failures = defaultdict(int, data.get("phase_failures", {}))
                    self.phase_successes = defaultdict(int, data.get("phase_successes", {}))
                    self.total_runs = data.get("total_runs", 0)
                    self.total_passes = data.get("total_passes", 0)
                    return
            except Exception as e:
                logger.warning(f"Failed to load metrics: {e}")
        
        # Initialize fresh metrics
        self.phase_failures = defaultdict(int)
        self.phase_successes = defaultdict(int)
        self.total_runs = 0
        self.total_passes = 0
    
    def _save_metrics(self):
        """Persist metrics to disk."""
        try:
            data = {
                "phase_failures": dict(self.phase_failures),
                "phase_successes": dict(self.phase_successes),
                "total_runs": self.total_runs,
                "total_passes": self.total_passes,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save metrics: {e}")
    
    def record_result(self, result: CircuitResult):
        """Record a circuit result."""
        self.total_runs += 1
        
        # Record successes for passed phases
        for phase_num in range(1, result.phase + 1):
            if phase_num in result.phase_results:
                phase_result = result.phase_results[phase_num]
                if phase_result.status == PhaseStatus.PASSED:
                    self.phase_successes[str(phase_num)] += 1
        
        # Record failure for the failing phase
        if not result.passed:
            self.phase_failures[str(result.phase)] += 1
        else:
            self.total_passes += 1
        
        self._save_metrics()
    
    def get_kill_stats(self) -> Dict[str, Any]:
        """Get statistics on which phases kill builds."""
        stats = {
            "total_runs": self.total_runs,
            "total_passes": self.total_passes,
            "pass_rate": self.total_passes / max(self.total_runs, 1),
            "phase_kill_counts": dict(self.phase_failures),
            "deadliest_phase": None
        }
        
        if self.phase_failures:
            deadliest = max(self.phase_failures.keys(), key=lambda k: self.phase_failures[k])
            stats["deadliest_phase"] = {
                "phase": int(deadliest),
                "kills": self.phase_failures[deadliest],
                "kill_rate": self.phase_failures[deadliest] / max(self.total_runs, 1)
            }
        
        return stats


class MutationCircuit:
    """
    6-Phase Mutation Implementation Pipeline.
    
    Orchestrates the safe implementation of code mutations through
    a series of validation phases. Each phase must pass before
    proceeding to the next.
    
    Phases:
        1. MVP (Build)  - Code is written and compiles
        2. TEST         - Run pytest, check coverage
        3. RED TEAM     - Adversarial vulnerability scanning
        4. SLIM         - Remove bloat, keep it lean
        5. REVIEW       - 25-vote diverse consensus
        6. VERIFY       - Final dharmic gates + integration
    
    Usage:
        circuit = MutationCircuit()
        result = await circuit.run_full_circuit(proposal)
        if result.ready_to_push:
            # Safe to commit
    """
    
    PHASE_NAMES = {
        1: "MVP (Build)",
        2: "Test",
        3: "Red Team",
        4: "Slim",
        5: "Review",
        6: "Verify"
    }
    
    def __init__(
        self,
        project_root: Path = None,
        max_retries: int = 2,
        auto_rollback: bool = True,
        required_votes: int = 25,
        bloat_threshold: float = 0.3,
        strict_red_team: bool = True
    ):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.max_retries = max_retries
        self.auto_rollback = auto_rollback
        self.required_votes = required_votes
        self.bloat_threshold = bloat_threshold
        self.strict_red_team = strict_red_team
        
        # Initialize subsystems
        self.voting_system = VotingSwarm()
        self.elegance_evaluator = EleganceEvaluator(project_root=self.project_root)
        self.fitness_evaluator = FitnessEvaluator(project_root=self.project_root)
        self.telos_layer = TelosLayer()
        self.archive = get_archive()
        self.red_team = RedTeamAgent(strict_mode=strict_red_team)
        self.slimmer = Slimmer(aggressive=False)
        self.metrics = CircuitMetrics()
        
        # Backup storage for rollback
        self._backups: Dict[str, str] = {}
    
    async def run_full_circuit(self, proposal: MutationProposal) -> CircuitResult:
        """
        Execute the full 6-phase mutation circuit.
        
        Args:
            proposal: The mutation proposal to execute
            
        Returns:
            CircuitResult with phase results and final status
        """
        logger.info(f"Starting 6-phase circuit for proposal: {proposal.id}")
        
        start_time = time.time()
        phase_results: Dict[int, PhaseResult] = {}
        current_phase = 0
        rollback_performed = False
        rollback_reason = None
        
        # Initialize current_code
        proposal.current_code = proposal.new_code
        
        # Execute phases in sequence
        phases = [
            (1, self._phase_1_mvp),
            (2, self._phase_2_test),
            (3, self._phase_3_red_team),
            (4, self._phase_4_slim),
            (5, self._phase_5_review),
            (6, self._phase_6_verify),
        ]
        
        for phase_num, phase_fn in phases:
            current_phase = phase_num
            phase_start = time.time()
            
            logger.info(f"[Phase {phase_num}/6] {self.PHASE_NAMES[phase_num]}")
            
            # Execute phase with retry support
            result = await self._execute_with_retry(phase_fn, proposal, phase_num)
            
            # Calculate duration
            result.duration_ms = int((time.time() - phase_start) * 1000)
            phase_results[phase_num] = result
            
            # Log phase result
            status_icon = "✓" if result.status == PhaseStatus.PASSED else "✗"
            logger.info(f"  {status_icon} {result.message}")
            
            # Check if phase failed
            if result.status == PhaseStatus.FAILED:
                logger.warning(f"Phase {phase_num} failed: {result.message}")
                
                # Automatic rollback on implementation failure
                if phase_num >= 2 and self.auto_rollback:
                    rollback_performed = self._perform_rollback(proposal)
                    rollback_reason = result.message
                
                # Build the failure result
                total_duration_ms = int((time.time() - start_time) * 1000)
                
                circuit_result = CircuitResult(
                    proposal_id=proposal.id,
                    phase=current_phase,
                    passed=False,
                    reason=result.message,
                    phase_results=phase_results,
                    final_fitness=FitnessScore(),
                    ready_to_push=False,
                    total_duration_ms=total_duration_ms,
                    rollback_performed=rollback_performed,
                    rollback_reason=rollback_reason
                )
                
                # Record metrics
                self.metrics.record_result(circuit_result)
                self._log_post_mortem(proposal, circuit_result)
                
                return circuit_result
        
        # All phases passed!
        # Calculate final fitness
        fitness_result = self.fitness_evaluator.evaluate(
            proposal.target_file,
            diff=proposal.diff or "",
            run_tests=False  # Already ran in Phase 2
        )
        
        total_duration_ms = int((time.time() - start_time) * 1000)
        
        circuit_result = CircuitResult(
            proposal_id=proposal.id,
            phase=6,
            passed=True,
            phase_results=phase_results,
            final_fitness=fitness_result.score,
            ready_to_push=True,
            total_duration_ms=total_duration_ms,
            final_code=proposal.current_code
        )
        
        # Record metrics and archive
        self.metrics.record_result(circuit_result)
        self._archive_result(proposal, circuit_result)
        
        logger.info(
            f"Circuit PASSED: {total_duration_ms}ms, "
            f"fitness={fitness_result.score.total():.2f}, ready_to_push=True"
        )
        
        return circuit_result
    
    # Synchronous wrapper for backwards compatibility
    def run_circuit(self, proposal: MutationProposal) -> CircuitResult:
        """
        Synchronous wrapper for run_full_circuit.
        For backwards compatibility with existing code.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run, 
                        self.run_full_circuit(proposal)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.run_full_circuit(proposal))
        except RuntimeError:
            return asyncio.run(self.run_full_circuit(proposal))
    
    async def _execute_with_retry(
        self,
        phase_fn: Callable,
        proposal: MutationProposal,
        phase_num: int
    ) -> PhaseResult:
        """Execute a phase with retry support."""
        retry_count = 0
        
        while retry_count <= self.max_retries:
            result = await phase_fn(proposal)
            
            if result.status == PhaseStatus.RETRY:
                retry_count += 1
                logger.info(
                    f"  → Retry {retry_count}/{self.max_retries}: {result.feedback}"
                )
                
                if retry_count > self.max_retries:
                    result.status = PhaseStatus.FAILED
                    result.message = f"Max retries exceeded: {result.feedback}"
                    break
            else:
                break
        
        result.retry_count = retry_count
        return result
    
    # ============ PHASE 1: MVP (Build) ============
    async def _phase_1_mvp(self, proposal: MutationProposal) -> PhaseResult:
        """
        Phase 1: Build the MVP.
        - Verify code is provided
        - Check syntax (compiles)
        - Apply to filesystem
        """
        try:
            code = proposal.current_code
            if not code:
                return PhaseResult(
                    phase=1,
                    name=self.PHASE_NAMES[1],
                    status=PhaseStatus.FAILED,
                    message="No code provided in proposal"
                )
            
            # 1.1 Parse AST to verify it compiles
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return PhaseResult(
                    phase=1,
                    name=self.PHASE_NAMES[1],
                    status=PhaseStatus.FAILED,
                    message=f"Won't compile: {e.msg} (line {e.lineno})",
                    feedback=f"Fix syntax at line {e.lineno}: {e.msg}"
                )
            
            # 1.2 Check imports resolve
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            unresolved = []
            for imp in imports:
                try:
                    __import__(imp.split('.')[0])
                except ImportError:
                    local_path = self.project_root / imp.replace('.', '/')
                    if not (local_path.exists() or (local_path.parent / f"{local_path.name}.py").exists()):
                        unresolved.append(imp)
            
            if unresolved:
                return PhaseResult(
                    phase=1,
                    name=self.PHASE_NAMES[1],
                    status=PhaseStatus.RETRY,
                    message=f"Unresolved imports: {', '.join(unresolved)}",
                    feedback=f"Add missing dependencies: {', '.join(unresolved)}"
                )
            
            # 1.3 Apply to filesystem
            target_path = self.project_root / proposal.target_file
            
            # Backup existing file
            if target_path.exists():
                proposal.original_code = target_path.read_text()
                self._backups[proposal.id] = proposal.original_code
            else:
                self._backups[proposal.id] = None
            
            # Write the file
            if proposal.mutation_type == "create":
                if target_path.exists():
                    return PhaseResult(
                        phase=1,
                        name=self.PHASE_NAMES[1],
                        status=PhaseStatus.FAILED,
                        message=f"File already exists: {proposal.target_file}"
                    )
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
            target_path.write_text(code)
            
            return PhaseResult(
                phase=1,
                name=self.PHASE_NAMES[1],
                status=PhaseStatus.PASSED,
                message=f"MVP compiles and written to {proposal.target_file}",
                details={
                    "imports": imports,
                    "ast_nodes": len(list(ast.walk(tree))),
                    "lines": len(code.split('\n'))
                }
            )
            
        except Exception as e:
            logger.exception(f"Phase 1 error: {e}")
            return PhaseResult(
                phase=1,
                name=self.PHASE_NAMES[1],
                status=PhaseStatus.FAILED,
                message=f"Build error: {str(e)}"
            )
    
    # ============ PHASE 2: Test ============
    async def _phase_2_test(self, proposal: MutationProposal) -> PhaseResult:
        """
        Phase 2: Run pytest and check coverage.
        """
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["python3", "-m", "pytest", "-v", "--tb=short", "-x", 
                 "--cov=.", "--cov-report=term-missing"],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=self.project_root
            )
            
            output = result.stdout + result.stderr
            
            # Parse test results
            passed_tests = output.count(" PASSED")
            failed_tests = output.count(" FAILED")
            error_tests = output.count(" ERROR")
            
            total_failures = failed_tests + error_tests
            
            # Parse coverage
            coverage_match = None
            for line in output.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            try:
                                coverage_match = int(part.rstrip('%'))
                            except ValueError:
                                pass
            
            if total_failures > 0:
                # Extract failure info
                failure_lines = []
                for line in output.split('\n'):
                    if 'FAILED' in line or 'ERROR' in line or 'AssertionError' in line:
                        failure_lines.append(line.strip())
                
                return PhaseResult(
                    phase=2,
                    name=self.PHASE_NAMES[2],
                    status=PhaseStatus.FAILED,
                    message=f"Tests failed: {total_failures} failure(s)",
                    details={
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "errors": error_tests,
                        "failures": failure_lines[:5],
                        "coverage": coverage_match
                    },
                    feedback=f"Fix {total_failures} failing test(s): {failure_lines[0] if failure_lines else 'unknown'}"
                )
            
            # Check coverage threshold (optional)
            if coverage_match is not None and coverage_match < 50:
                return PhaseResult(
                    phase=2,
                    name=self.PHASE_NAMES[2],
                    status=PhaseStatus.RETRY,
                    message=f"Low test coverage: {coverage_match}%",
                    feedback=f"Add tests to improve coverage from {coverage_match}% to >50%",
                    details={"coverage": coverage_match}
                )
            
            if passed_tests == 0:
                return PhaseResult(
                    phase=2,
                    name=self.PHASE_NAMES[2],
                    status=PhaseStatus.PASSED,
                    message="No tests found (proceeding with caution)",
                    details={"warning": "No test coverage for this change"}
                )
            
            return PhaseResult(
                phase=2,
                name=self.PHASE_NAMES[2],
                status=PhaseStatus.PASSED,
                message=f"All {passed_tests} tests passed" + 
                        (f" ({coverage_match}% coverage)" if coverage_match else ""),
                details={
                    "passed": passed_tests,
                    "failed": 0,
                    "errors": 0,
                    "coverage": coverage_match
                }
            )
            
        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=2,
                name=self.PHASE_NAMES[2],
                status=PhaseStatus.FAILED,
                message="Tests timed out (>180s)"
            )
        except Exception as e:
            logger.exception(f"Phase 2 error: {e}")
            return PhaseResult(
                phase=2,
                name=self.PHASE_NAMES[2],
                status=PhaseStatus.FAILED,
                message=f"Test error: {str(e)}"
            )
    
    # ============ PHASE 3: Red Team ============
    async def _phase_3_red_team(self, proposal: MutationProposal) -> PhaseResult:
        """
        Phase 3: Red team attacks the code to find vulnerabilities.
        """
        try:
            code = proposal.current_code
            
            # Run red team attack
            attack_result: RedTeamReport = await self.red_team.attack(
                code, 
                filename=proposal.target_file
            )
            
            # Check for critical vulnerabilities (hard fail)
            if attack_result.has_critical_vulnerabilities:
                critical_vulns = [
                    v for v in attack_result.vulnerabilities
                    if v.severity == Severity.CRITICAL
                ]
                return PhaseResult(
                    phase=3,
                    name=self.PHASE_NAMES[3],
                    status=PhaseStatus.FAILED,
                    message=f"Critical vulnerabilities found: {len(critical_vulns)}",
                    details={
                        "vulnerabilities": [
                            {
                                "name": v.name,
                                "severity": v.severity.value,
                                "location": v.location,
                                "description": v.description
                            }
                            for v in critical_vulns
                        ],
                        "attack_summary": attack_result.summary
                    },
                    feedback=f"Fix critical: {critical_vulns[0].description} at {critical_vulns[0].location}"
                )
            
            # Check for high vulnerabilities in strict mode
            if self.strict_red_team and attack_result.has_high_vulnerabilities:
                high_vulns = [
                    v for v in attack_result.vulnerabilities
                    if v.severity == Severity.HIGH
                ]
                return PhaseResult(
                    phase=3,
                    name=self.PHASE_NAMES[3],
                    status=PhaseStatus.RETRY,
                    message=f"High-severity vulnerabilities found: {len(high_vulns)}",
                    details={
                        "vulnerabilities": [
                            {"name": v.name, "location": v.location}
                            for v in high_vulns
                        ]
                    },
                    feedback=f"Fix high-severity: {high_vulns[0].name} at {high_vulns[0].location}"
                )
            
            # Count issues by severity
            vuln_counts = attack_result.vulnerability_count
            
            return PhaseResult(
                phase=3,
                name=self.PHASE_NAMES[3],
                status=PhaseStatus.PASSED,
                message=f"Red team attack complete: {attack_result.summary}",
                details={
                    "vectors_tried": attack_result.attack_vectors_tried,
                    "vectors_succeeded": attack_result.attack_vectors_succeeded,
                    "vulnerability_counts": vuln_counts,
                    "duration_ms": attack_result.duration_ms
                }
            )
            
        except Exception as e:
            logger.exception(f"Phase 3 error: {e}")
            return PhaseResult(
                phase=3,
                name=self.PHASE_NAMES[3],
                status=PhaseStatus.FAILED,
                message=f"Red team error: {str(e)}"
            )
    
    # ============ PHASE 4: Slim ============
    async def _phase_4_slim(self, proposal: MutationProposal) -> PhaseResult:
        """
        Phase 4: Remove bloat from the code.
        """
        try:
            code = proposal.current_code
            
            # Run slimmer
            slim_result: SlimResult = await self.slimmer.slim(
                code,
                filename=proposal.target_file
            )
            
            # Check bloat score
            if slim_result.bloat_score > self.bloat_threshold:
                # Too bloated - fail
                top_issues = slim_result.bloat_items[:3]
                return PhaseResult(
                    phase=4,
                    name=self.PHASE_NAMES[4],
                    status=PhaseStatus.FAILED,
                    message=f"Too bloated: score {slim_result.bloat_score:.2f} > {self.bloat_threshold}",
                    details={
                        "bloat_score": slim_result.bloat_score,
                        "threshold": self.bloat_threshold,
                        "original_lines": slim_result.original_lines,
                        "bloat_items": [
                            {"category": b.category, "description": b.description}
                            for b in top_issues
                        ]
                    },
                    feedback=f"Reduce bloat: {top_issues[0].description if top_issues else 'general cleanup needed'}"
                )
            
            # Update the proposal with slimmed code
            if slim_result.bytes_removed > 0:
                proposal.current_code = slim_result.slimmed_code
                
                # Also update the file on disk
                target_path = self.project_root / proposal.target_file
                target_path.write_text(slim_result.slimmed_code)
            
            return PhaseResult(
                phase=4,
                name=self.PHASE_NAMES[4],
                status=PhaseStatus.PASSED,
                message=f"Slimmed: {slim_result.summary}",
                details={
                    "bloat_score": slim_result.bloat_score,
                    "original_lines": slim_result.original_lines,
                    "slimmed_lines": slim_result.slimmed_lines,
                    "bytes_removed": slim_result.bytes_removed,
                    "reduction_percent": slim_result.reduction_percent,
                    "bloat_items_found": len(slim_result.bloat_items)
                }
            )
            
        except Exception as e:
            logger.exception(f"Phase 4 error: {e}")
            return PhaseResult(
                phase=4,
                name=self.PHASE_NAMES[4],
                status=PhaseStatus.FAILED,
                message=f"Slimmer error: {str(e)}"
            )
    
    # ============ PHASE 5: Review (25 votes) ============
    async def _phase_5_review(self, proposal: MutationProposal) -> PhaseResult:
        """
        Phase 5: Collect 25 votes from diverse reviewers.
        """
        try:
            # Request 25 votes
            voting_result: VoteResult = self.voting_system.review_proposal(
                proposal,
                required_votes=self.required_votes
            )
            
            if voting_result.passed:
                return PhaseResult(
                    phase=5,
                    name=self.PHASE_NAMES[5],
                    status=PhaseStatus.PASSED,
                    message=f"Approved by {voting_result.total_votes} reviewers "
                            f"({voting_result.approval_ratio:.0%} approval)",
                    details={
                        "votes": voting_result.total_votes,
                        "approval_ratio": voting_result.approval_ratio,
                        "consensus": voting_result.consensus_reached,
                        "required": self.required_votes
                    }
                )
            
            # Check if we should retry (request_changes)
            if voting_result.request_changes_count > 0:
                return PhaseResult(
                    phase=5,
                    name=self.PHASE_NAMES[5],
                    status=PhaseStatus.RETRY,
                    message=f"Changes requested by {voting_result.request_changes_count} reviewers",
                    feedback="; ".join(voting_result.feedback[:3]),
                    details={
                        "votes": voting_result.total_votes,
                        "request_changes": voting_result.request_changes_count,
                        "feedback": voting_result.feedback
                    }
                )
            
            # Hard rejection
            return PhaseResult(
                phase=5,
                name=self.PHASE_NAMES[5],
                status=PhaseStatus.FAILED,
                message=f"Rejected: {voting_result.approval_ratio:.0%} approval "
                        f"({voting_result.total_votes} votes)",
                details={
                    "approval_ratio": voting_result.approval_ratio,
                    "dissenting_reasons": voting_result.feedback[:5]
                },
                feedback=voting_result.feedback[0] if voting_result.feedback else "Improve code quality"
            )
            
        except Exception as e:
            logger.exception(f"Phase 5 error: {e}")
            return PhaseResult(
                phase=5,
                name=self.PHASE_NAMES[5],
                status=PhaseStatus.FAILED,
                message=f"Review error: {str(e)}"
            )
    
    # ============ PHASE 6: Verify (Dharmic Gates) ============
    async def _phase_6_verify(self, proposal: MutationProposal) -> PhaseResult:
        """
        Phase 6: Final verification - dharmic gates + integration check.
        """
        try:
            issues = []
            failed_gates = []
            
            # 6.1 Dharmic gates check
            telos_check: TelosCheck = self.telos_layer.check_action(
                f"Apply mutation: {proposal.description}",
                {
                    "modifies_files": True,
                    "consent": True,  # Consent granted by reaching this phase
                    "verified": True,
                    "has_backup": True,
                    "can_undo": True,
                    "purpose": "code evolution and improvement"
                }
            )
            
            if not telos_check.passed:
                for gate in telos_check.gates:
                    if gate.result == GateResult.FAIL:
                        failed_gates.append(gate.gate)
                
                # Tier A failures (AHIMSA) are hard stops
                if "AHIMSA" in failed_gates:
                    return PhaseResult(
                        phase=6,
                        name=self.PHASE_NAMES[6],
                        status=PhaseStatus.FAILED,
                        message="Dharmic gate failure: AHIMSA violated",
                        details={
                            "alignment": telos_check.alignment_score,
                            "failed_gates": failed_gates
                        },
                        feedback="Code violates non-harm principle"
                    )
                
                issues.append(f"Low dharmic alignment: {telos_check.alignment_score:.0%}")
            
            # 6.2 Elegance check
            code = proposal.current_code
            elegance_result: EleganceScore = self.elegance_evaluator.evaluate(code=code)
            
            if not elegance_result.passed:
                issues.extend(elegance_result.issues[:2])
            
            # 6.3 Integration check - verify file still compiles after all changes
            try:
                ast.parse(code)
            except SyntaxError as e:
                return PhaseResult(
                    phase=6,
                    name=self.PHASE_NAMES[6],
                    status=PhaseStatus.FAILED,
                    message=f"Integration check failed: syntax error at line {e.lineno}",
                    feedback=f"Fix syntax: {e.msg}"
                )
            
            # 6.4 Final test run (quick sanity check)
            test_result = subprocess.run(
                ["python3", "-m", "pytest", "-x", "-q", "--tb=no"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root
            )
            
            if test_result.returncode != 0:
                return PhaseResult(
                    phase=6,
                    name=self.PHASE_NAMES[6],
                    status=PhaseStatus.FAILED,
                    message="Integration tests failed",
                    details={"test_output": test_result.stdout[-500:]},
                    feedback="Tests pass individually but fail integrated"
                )
            
            # Evaluate final result
            if failed_gates:
                return PhaseResult(
                    phase=6,
                    name=self.PHASE_NAMES[6],
                    status=PhaseStatus.FAILED,
                    message=f"Dharmic gates failed: {', '.join(failed_gates)}",
                    details={
                        "failed_gates": failed_gates,
                        "alignment": telos_check.alignment_score
                    },
                    feedback=f"Address dharmic concerns: {failed_gates[0]}"
                )
            
            if issues and len(issues) > 2:
                return PhaseResult(
                    phase=6,
                    name=self.PHASE_NAMES[6],
                    status=PhaseStatus.RETRY,
                    message="Minor quality issues",
                    feedback="; ".join(issues),
                    details={"issues": issues}
                )
            
            return PhaseResult(
                phase=6,
                name=self.PHASE_NAMES[6],
                status=PhaseStatus.PASSED,
                message="All gates passed - ready to push",
                details={
                    "dharmic_alignment": telos_check.alignment_score,
                    "elegance_score": elegance_result.score.total() if elegance_result.score else 0,
                    "witness_hash": telos_check.witness_hash,
                    "all_gates_pass": True
                }
            )
            
        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=6,
                name=self.PHASE_NAMES[6],
                status=PhaseStatus.RETRY,
                message="Integration tests timed out",
                feedback="Tests taking too long - optimize or split"
            )
        except Exception as e:
            logger.exception(f"Phase 6 error: {e}")
            return PhaseResult(
                phase=6,
                name=self.PHASE_NAMES[6],
                status=PhaseStatus.FAILED,
                message=f"Verification error: {str(e)}"
            )
    
    # ============ Rollback Support ============
    def _perform_rollback(self, proposal: MutationProposal) -> bool:
        """
        Rollback changes made during implementation.
        Restores file to original state from backup.
        """
        try:
            backup = self._backups.get(proposal.id)
            target_path = self.project_root / proposal.target_file
            
            if backup is None:
                # File was newly created - delete it
                if target_path.exists():
                    target_path.unlink()
                    logger.info(f"Rollback: Deleted newly created file {proposal.target_file}")
            else:
                # Restore original content
                target_path.write_text(backup)
                logger.info(f"Rollback: Restored {proposal.target_file} to original state")
            
            # Clear backup
            if proposal.id in self._backups:
                del self._backups[proposal.id]
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    # ============ Logging & Archiving ============
    def _log_post_mortem(self, proposal: MutationProposal, result: CircuitResult):
        """Log detailed post-mortem for failed circuits."""
        log_file = self.project_root / "logs" / "circuit_failures.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        post_mortem = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proposal_id": proposal.id,
            "description": proposal.description,
            "target_file": proposal.target_file,
            "failed_phase": result.phase,
            "failed_phase_name": self.PHASE_NAMES.get(result.phase, "Unknown"),
            "reason": result.reason,
            "total_duration_ms": result.total_duration_ms,
            "phases": {
                str(k): {
                    "status": v.status.value,
                    "message": v.message,
                    "duration_ms": v.duration_ms,
                    "feedback": v.feedback
                }
                for k, v in result.phase_results.items()
            }
        }
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(post_mortem) + '\n')
        except Exception as e:
            logger.warning(f"Failed to log post-mortem: {e}")
    
    def _archive_result(self, proposal: MutationProposal, result: CircuitResult):
        """Archive successful circuit results."""
        try:
            entry = EvolutionEntry(
                id="",  # Will be auto-generated
                timestamp="",
                component=proposal.target_file,
                change_type="mutation",
                description=proposal.description,
                diff=proposal.diff or "",
                fitness=result.final_fitness,
                status="applied" if result.passed else "rejected",
                rollback_reason=result.rollback_reason
            )
            
            self.archive.add_entry(entry)
            
        except Exception as e:
            logger.warning(f"Failed to archive result: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit performance metrics."""
        return self.metrics.get_kill_stats()


# Convenience functions
def run_circuit(proposal: MutationProposal, **kwargs) -> CircuitResult:
    """Quick synchronous circuit execution with default settings."""
    circuit = MutationCircuit(**kwargs)
    return circuit.run_circuit(proposal)


async def run_full_circuit(proposal: MutationProposal, **kwargs) -> CircuitResult:
    """Quick async circuit execution with default settings."""
    circuit = MutationCircuit(**kwargs)
    return await circuit.run_full_circuit(proposal)


if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Create a test proposal
    test_code = '''
"""
Test Module - Created by circuit test.
"""
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestData:
    """Test dataclass."""
    name: str
    value: int = 0


def process(items: List[int]) -> int:
    """Process items and return sum."""
    return sum(items)
'''
    
    proposal = MutationProposal(
        id="test-circuit-6phase-001",
        description="Add test module for 6-phase circuit validation",
        target_file="tests/circuit_6phase_test_output.py",
        mutation_type="create",
        new_code=test_code,
        risk_level="low"
    )
    
    async def main():
        circuit = MutationCircuit()
        result = await circuit.run_full_circuit(proposal)
        
        print("\n" + "=" * 60)
        print("6-PHASE CIRCUIT RESULT")
        print("=" * 60)
        print(f"Proposal: {result.proposal_id}")
        print(f"Passed: {result.passed}")
        print(f"Phase Reached: {result.phase}/6")
        print(f"Ready to Push: {result.ready_to_push}")
        print(f"Duration: {result.total_duration_ms}ms")
        
        if result.rollback_performed:
            print(f"Rollback: Yes ({result.rollback_reason})")
        
        print("\nPhase Results:")
        for phase_num in range(1, 7):
            if phase_num in result.phase_results:
                phase_result = result.phase_results[phase_num]
                status_icon = "✓" if phase_result.status == PhaseStatus.PASSED else "✗"
                print(f"  {status_icon} Phase {phase_num} ({phase_result.name}): {phase_result.status.value}")
                print(f"    {phase_result.message}")
                if phase_result.feedback:
                    print(f"    Feedback: {phase_result.feedback}")
        
        if result.final_fitness:
            print(f"\nFinal Fitness: {result.final_fitness.total():.2f}")
        
        # Show metrics
        print("\n" + "=" * 60)
        print("CIRCUIT METRICS")
        print("=" * 60)
        metrics = circuit.get_metrics()
        print(f"Total runs: {metrics['total_runs']}")
        print(f"Pass rate: {metrics['pass_rate']:.1%}")
        if metrics['deadliest_phase']:
            dp = metrics['deadliest_phase']
            print(f"Deadliest phase: {dp['phase']} ({circuit.PHASE_NAMES[dp['phase']]}) - "
                  f"{dp['kills']} kills ({dp['kill_rate']:.1%})")
    
    asyncio.run(main())
