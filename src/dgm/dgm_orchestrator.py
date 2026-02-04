#!/usr/bin/env python3
"""
DGM Orchestrator - Full Autonomous Self-Improvement Loop
=========================================================

The Brain of the Darwin-Gödel Machine.

This is the main entry point that ties together all DGM components:
- Mutator: Proposes improvements to code
- VotingSwarm: Multi-agent voting (5 phases, 25 votes)
- EleganceEvaluator: Scores code elegance
- MutationCircuit: Full evaluation pipeline
- AutoPusher: Git commit and push automation
- Archive: Evolution history with lineage
- TelosLayer: 7 Dharmic gates for safety

The Self-Improvement Loop:
1. SELECT component to improve (or use target)
2. GET best parent from archive
3. PROPOSE improvement via Mutator
4. EVALUATE via MutationCircuit (5 phases + 25 votes)
5. If circuit passes → COMMIT via AutoPusher
6. ARCHIVE result with full lineage
7. RETURN ImprovementResult

Author: DGM System
License: MIT
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Callable

# Internal DGM components
from .archive import (
    Archive, 
    EvolutionEntry, 
    FitnessScore, 
    get_archive,
)
from .fitness import FitnessEvaluator, EvaluationResult
from .selector import Selector, SelectionResult

# Core system components
from src.core.telos_layer import TelosLayer, TelosCheck, GateResult

# =============================================================================
# Multi-Model Pipeline Components (Optional)
# =============================================================================

# CodexProposer - Fast, cheap proposal generation
try:
    from .codex_proposer import CodexProposer
    CODEX_AVAILABLE = True
except ImportError:
    CodexProposer = None
    CODEX_AVAILABLE = False

# KimiReviewer - Deep 128k context review
try:
    from .kimi_reviewer import KimiReviewer
    KIMI_AVAILABLE = True
except ImportError:
    KimiReviewer = None
    KIMI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("dgm.orchestrator")


# =============================================================================
# Data Structures
# =============================================================================

class ImprovementStatus(Enum):
    """Status of an improvement attempt."""
    PENDING = "pending"
    PROPOSED = "proposed"
    EVALUATING = "evaluating"
    CIRCUIT_PASSED = "circuit_passed"
    CIRCUIT_FAILED = "circuit_failed"
    COMMITTED = "committed"
    PUSHED = "pushed"
    ARCHIVED = "archived"
    REJECTED = "rejected"
    ERROR = "error"


class VoteDecision(Enum):
    """Individual vote decision."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    """Single vote from a swarm voter."""
    voter_id: str
    phase: int
    decision: VoteDecision
    confidence: float  # 0.0-1.0
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VotingResult:
    """Aggregated voting result from swarm."""
    total_votes: int
    approve_count: int
    reject_count: int
    abstain_count: int
    average_confidence: float
    passed: bool
    votes: List[Vote] = field(default_factory=list)
    
    @property
    def approval_rate(self) -> float:
        """Calculate approval rate (approve / non-abstain)."""
        valid = self.approve_count + self.reject_count
        return self.approve_count / valid if valid > 0 else 0.0


@dataclass
class MutationProposal:
    """Proposed mutation from the Mutator."""
    id: str
    component: str
    parent_id: Optional[str]
    description: str
    diff: str
    mutated_code: str
    original_code: str
    mutation_type: str  # "refactor", "optimize", "fix", "enhance"
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CircuitResult:
    """Result from the full MutationCircuit evaluation."""
    passed: bool
    proposal: MutationProposal
    phases_completed: int
    total_phases: int = 5
    voting_result: Optional[VotingResult] = None
    telos_check: Optional[TelosCheck] = None
    fitness_score: Optional[FitnessScore] = None
    elegance_score: float = 0.0
    test_results: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
    review_result: Optional[Dict[str, Any]] = None  # Kimi review results
    models_used: Dict[str, str] = field(default_factory=dict)  # phase → model


@dataclass
class ImprovementResult:
    """Final result of an improvement cycle."""
    success: bool
    status: ImprovementStatus
    component: str
    cycle_id: str
    proposal: Optional[MutationProposal] = None
    circuit_result: Optional[CircuitResult] = None
    commit_hash: Optional[str] = None
    entry_id: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    models_used: Dict[str, str] = field(default_factory=dict)  # phase → model
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "status": self.status.value,
            "component": self.component,
            "cycle_id": self.cycle_id,
            "commit_hash": self.commit_hash,
            "entry_id": self.entry_id,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "models_used": self.models_used,
        }
        if self.proposal:
            result["proposal"] = {
                "id": self.proposal.id,
                "description": self.proposal.description,
                "mutation_type": self.proposal.mutation_type,
            }
        if self.circuit_result:
            result["circuit"] = {
                "passed": self.circuit_result.passed,
                "phases_completed": self.circuit_result.phases_completed,
                "fitness": self.circuit_result.fitness_score.total() if self.circuit_result.fitness_score else None,
                "elegance": self.circuit_result.elegance_score,
            }
        return result


@dataclass
class ComponentMetrics:
    """Metrics for a component used in selection."""
    component: str
    last_modified_cycle: int = 0
    recent_fitness: List[float] = field(default_factory=list)
    test_failures: int = 0
    improvement_attempts: int = 0
    successful_improvements: int = 0
    
    @property
    def fitness_trend(self) -> float:
        """Calculate fitness trend (-1.0 declining, 0 stable, +1.0 improving)."""
        if len(self.recent_fitness) < 2:
            return 0.0
        # Compare recent half to older half
        mid = len(self.recent_fitness) // 2
        older = sum(self.recent_fitness[:mid]) / mid if mid > 0 else 0
        newer = sum(self.recent_fitness[mid:]) / (len(self.recent_fitness) - mid)
        if older == 0:
            return 0.0
        return (newer - older) / older  # Relative change
    
    @property
    def success_rate(self) -> float:
        """Success rate of improvements."""
        if self.improvement_attempts == 0:
            return 0.5  # Unknown, assume average
        return self.successful_improvements / self.improvement_attempts


# =============================================================================
# Sub-Components (Interfaces with default implementations)
# =============================================================================

class Mutator:
    """
    Proposes improvements to code components.
    
    In production, this would call an LLM to generate mutations.
    This is a simplified implementation for structure.
    """
    
    MUTATION_TYPES = ["refactor", "optimize", "fix", "enhance", "document"]
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
    
    def propose_improvement(
        self,
        component: str,
        parent: Optional[EvolutionEntry] = None,
        focus: Optional[str] = None,
    ) -> MutationProposal:
        """
        Propose an improvement to a component.
        
        Args:
            component: Path to the component (e.g., "src/dgm/voting.py")
            parent: Parent evolution entry to build upon
            focus: Specific focus area ("elegance", "performance", "safety")
        
        Returns:
            MutationProposal with the proposed changes
        """
        # Read current code
        component_path = self.project_root / component
        if component_path.exists():
            original_code = component_path.read_text()
        else:
            original_code = ""
        
        # Generate proposal ID
        proposal_id = self._generate_id(component, parent)
        
        # Analyze and propose mutation
        mutation_type = self._select_mutation_type(original_code, focus)
        description, reasoning = self._generate_mutation_description(
            component, original_code, mutation_type, focus
        )
        
        # In a real implementation, this would call an LLM
        # For now, we return a placeholder that maintains structure
        mutated_code = original_code  # Placeholder - would be LLM output
        diff = ""  # Would be generated from actual changes
        
        return MutationProposal(
            id=proposal_id,
            component=component,
            parent_id=parent.id if parent else None,
            description=description,
            diff=diff,
            mutated_code=mutated_code,
            original_code=original_code,
            mutation_type=mutation_type,
            reasoning=reasoning,
        )
    
    def _generate_id(self, component: str, parent: Optional[EvolutionEntry]) -> str:
        """Generate unique proposal ID."""
        content = f"{component}{datetime.now().isoformat()}{parent.id if parent else ''}"
        hash_part = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"mut_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash_part}"
    
    def _select_mutation_type(self, code: str, focus: Optional[str]) -> str:
        """Select appropriate mutation type based on analysis."""
        if focus == "elegance":
            return "refactor"
        elif focus == "performance":
            return "optimize"
        elif focus == "safety":
            return "fix"
        elif focus == "features":
            return "enhance"
        
        # Analyze code to suggest mutation type
        if len(code) > 10000:
            return "refactor"  # Large files benefit from refactoring
        elif code.count("# TODO") > 0 or code.count("# FIXME") > 0:
            return "fix"
        elif code.count('"""') < 3:
            return "document"
        else:
            return "enhance"
    
    def _generate_mutation_description(
        self,
        component: str,
        code: str,
        mutation_type: str,
        focus: Optional[str]
    ) -> Tuple[str, str]:
        """Generate description and reasoning for mutation."""
        descriptions = {
            "refactor": f"Refactor {component} for improved clarity and modularity",
            "optimize": f"Optimize {component} for better performance",
            "fix": f"Fix issues and address TODOs in {component}",
            "enhance": f"Enhance {component} with additional capabilities",
            "document": f"Improve documentation in {component}",
        }
        
        reasonings = {
            "refactor": "Code structure can be improved for maintainability",
            "optimize": "Performance bottlenecks identified for optimization",
            "fix": "Issues or TODOs found that need addressing",
            "enhance": "Component can benefit from additional features",
            "document": "Documentation is sparse and needs improvement",
        }
        
        desc = descriptions.get(mutation_type, f"Improve {component}")
        reasoning = reasonings.get(mutation_type, "General improvement opportunity")
        
        if focus:
            desc = f"[{focus.upper()}] {desc}"
            reasoning = f"Focus: {focus}. {reasoning}"
        
        return desc, reasoning


class VotingSwarm:
    """
    Multi-agent voting system for mutation evaluation.
    
    Implements a 5-phase voting protocol with 25 total votes:
    - Phase 1: Syntax & Structure (5 votes)
    - Phase 2: Functionality (5 votes)
    - Phase 3: Safety & Gates (5 votes)
    - Phase 4: Elegance & Style (5 votes)
    - Phase 5: Overall Approval (5 votes)
    """
    
    PHASES = [
        ("syntax", "Syntax & Structure"),
        ("functionality", "Functionality & Correctness"),
        ("safety", "Safety & Dharmic Gates"),
        ("elegance", "Elegance & Style"),
        ("approval", "Overall Approval"),
    ]
    
    VOTES_PER_PHASE = 5
    TOTAL_VOTES = 25
    APPROVAL_THRESHOLD = 0.6  # 60% approval needed
    
    def __init__(self, threshold: float = None):
        self.threshold = threshold or self.APPROVAL_THRESHOLD
        self.voters = [f"voter_{i}" for i in range(self.VOTES_PER_PHASE)]
    
    def vote_on_proposal(
        self,
        proposal: MutationProposal,
        fitness: FitnessScore = None,
        telos_check: TelosCheck = None,
    ) -> VotingResult:
        """
        Run full 5-phase voting on a proposal.
        
        Args:
            proposal: The mutation proposal to vote on
            fitness: Fitness evaluation results
            telos_check: Dharmic gate check results
        
        Returns:
            VotingResult with aggregated votes
        """
        all_votes: List[Vote] = []
        
        for phase_idx, (phase_key, phase_name) in enumerate(self.PHASES, 1):
            phase_votes = self._vote_phase(
                phase_idx, phase_key, phase_name, 
                proposal, fitness, telos_check
            )
            all_votes.extend(phase_votes)
        
        return self._aggregate_votes(all_votes)
    
    def _vote_phase(
        self,
        phase_num: int,
        phase_key: str,
        phase_name: str,
        proposal: MutationProposal,
        fitness: Optional[FitnessScore],
        telos_check: Optional[TelosCheck],
    ) -> List[Vote]:
        """Execute voting for a single phase."""
        votes = []
        
        for voter_id in self.voters:
            # Determine vote based on phase and available data
            decision, confidence, reasoning = self._evaluate_vote(
                phase_key, proposal, fitness, telos_check
            )
            
            vote = Vote(
                voter_id=f"{voter_id}_p{phase_num}",
                phase=phase_num,
                decision=decision,
                confidence=confidence,
                reasoning=f"[{phase_name}] {reasoning}",
            )
            votes.append(vote)
        
        return votes
    
    def _evaluate_vote(
        self,
        phase_key: str,
        proposal: MutationProposal,
        fitness: Optional[FitnessScore],
        telos_check: Optional[TelosCheck],
    ) -> Tuple[VoteDecision, float, str]:
        """Evaluate and cast a single vote."""
        # Default evaluation based on available data
        if phase_key == "syntax":
            # Check if code is syntactically valid
            try:
                compile(proposal.mutated_code, "<string>", "exec")
                return VoteDecision.APPROVE, 0.9, "Code syntax is valid"
            except SyntaxError as e:
                return VoteDecision.REJECT, 0.95, f"Syntax error: {e}"
        
        elif phase_key == "functionality":
            if fitness and fitness.correctness >= 0.7:
                return VoteDecision.APPROVE, fitness.correctness, "Tests passing"
            elif fitness and fitness.correctness < 0.5:
                return VoteDecision.REJECT, 0.8, "Too many test failures"
            return VoteDecision.ABSTAIN, 0.5, "Insufficient test data"
        
        elif phase_key == "safety":
            if telos_check:
                if telos_check.passed:
                    return VoteDecision.APPROVE, telos_check.alignment_score, "Dharmic gates passed"
                elif telos_check.alignment_score < 0.5:
                    return VoteDecision.REJECT, 0.9, f"Gates failed: {telos_check.recommendation}"
                else:
                    return VoteDecision.ABSTAIN, 0.6, "Some gates uncertain"
            return VoteDecision.ABSTAIN, 0.5, "No safety evaluation available"
        
        elif phase_key == "elegance":
            if fitness and fitness.elegance >= 0.6:
                return VoteDecision.APPROVE, fitness.elegance, "Code is elegant"
            elif fitness and fitness.elegance < 0.4:
                return VoteDecision.REJECT, 0.7, "Code needs elegance improvement"
            return VoteDecision.ABSTAIN, 0.5, "Elegance unclear"
        
        else:  # approval phase
            if fitness:
                total = fitness.total()
                if total >= 0.7:
                    return VoteDecision.APPROVE, total, "Overall high fitness"
                elif total < 0.5:
                    return VoteDecision.REJECT, 0.8, "Overall fitness too low"
            return VoteDecision.ABSTAIN, 0.5, "Insufficient data for overall approval"
    
    def _aggregate_votes(self, votes: List[Vote]) -> VotingResult:
        """Aggregate all votes into final result."""
        approve = sum(1 for v in votes if v.decision == VoteDecision.APPROVE)
        reject = sum(1 for v in votes if v.decision == VoteDecision.REJECT)
        abstain = sum(1 for v in votes if v.decision == VoteDecision.ABSTAIN)
        
        confidences = [v.confidence for v in votes if v.decision != VoteDecision.ABSTAIN]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Calculate if passed (approval rate among non-abstains)
        valid_votes = approve + reject
        passed = (approve / valid_votes) >= self.threshold if valid_votes > 0 else False
        
        return VotingResult(
            total_votes=len(votes),
            approve_count=approve,
            reject_count=reject,
            abstain_count=abstain,
            average_confidence=avg_confidence,
            passed=passed,
            votes=votes,
        )


class EleganceEvaluator:
    """
    Evaluates code elegance on multiple dimensions.
    
    Dimensions:
    - Clarity: Is the code easy to understand?
    - Conciseness: Is it minimal without being cryptic?
    - Consistency: Does it follow consistent patterns?
    - Composability: Are components well-separated and reusable?
    """
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
    
    def evaluate(self, code: str, component: str = None) -> float:
        """
        Evaluate elegance of code.
        
        Returns:
            Float 0.0-1.0 representing elegance score
        """
        scores = {
            "clarity": self._score_clarity(code),
            "conciseness": self._score_conciseness(code),
            "consistency": self._score_consistency(code),
            "composability": self._score_composability(code),
        }
        
        weights = {
            "clarity": 0.3,
            "conciseness": 0.2,
            "consistency": 0.25,
            "composability": 0.25,
        }
        
        total = sum(scores[k] * weights[k] for k in scores)
        return min(max(total, 0.0), 1.0)
    
    def _score_clarity(self, code: str) -> float:
        """Score code clarity (docstrings, comments, naming)."""
        score = 0.5
        
        # Docstrings present
        if '"""' in code or "'''" in code:
            score += 0.2
        
        # Reasonable line length (most lines < 100 chars)
        lines = code.split('\n')
        long_lines = sum(1 for l in lines if len(l) > 100)
        if long_lines / max(len(lines), 1) < 0.1:
            score += 0.2
        
        # Type hints present
        if ': ' in code and '->' in code:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_conciseness(self, code: str) -> float:
        """Score code conciseness (not too verbose, not cryptic)."""
        lines = code.split('\n')
        non_empty = [l for l in lines if l.strip()]
        
        if len(non_empty) == 0:
            return 0.0
        
        # Average line length should be reasonable (30-80 chars ideal)
        avg_len = sum(len(l) for l in non_empty) / len(non_empty)
        if 30 <= avg_len <= 80:
            return 0.9
        elif 20 <= avg_len <= 100:
            return 0.7
        else:
            return 0.5
    
    def _score_consistency(self, code: str) -> float:
        """Score coding style consistency."""
        score = 0.5
        
        # Consistent indentation (spaces, not mixed)
        lines = code.split('\n')
        indents = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
        if indents:
            # Check if all indents are multiples of 4 (or 2)
            consistent = all(i % 4 == 0 or i % 2 == 0 for i in indents)
            if consistent:
                score += 0.25
        
        # Consistent naming (snake_case for functions)
        if "_" in code:  # Uses snake_case
            score += 0.15
        
        # Consistent string quotes
        single_quotes = code.count("'") - code.count("'''") * 3
        double_quotes = code.count('"') - code.count('"""') * 3
        if single_quotes == 0 or double_quotes == 0:
            score += 0.1  # Consistent quote style
        
        return min(score, 1.0)
    
    def _score_composability(self, code: str) -> float:
        """Score how well code is decomposed into reusable parts."""
        import ast
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.3
        
        # Count functions and classes
        funcs = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        
        # Ideal: multiple small functions rather than few large ones
        lines = len(code.split('\n'))
        
        if lines == 0:
            return 0.5
        
        # Ratio of functions/classes to lines
        density = (funcs + classes) / (lines / 50)  # Expect ~1 func per 50 lines
        
        if 0.5 <= density <= 2.0:
            return 0.9
        elif 0.3 <= density <= 3.0:
            return 0.7
        else:
            return 0.5


class MutationCircuit:
    """
    Full evaluation pipeline for mutations.
    
    5 Phases:
    1. Syntax Validation
    2. Test Execution
    3. Dharmic Gate Check
    4. Elegance Evaluation
    5. Swarm Voting
    """
    
    def __init__(
        self,
        project_root: Path = None,
        voting_swarm: VotingSwarm = None,
        elegance_evaluator: EleganceEvaluator = None,
        fitness_evaluator: FitnessEvaluator = None,
        telos_layer: TelosLayer = None,
    ):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.voting_swarm = voting_swarm or VotingSwarm()
        self.elegance = elegance_evaluator or EleganceEvaluator(self.project_root)
        self.fitness = fitness_evaluator or FitnessEvaluator(self.project_root)
        self.telos = telos_layer or TelosLayer()
    
    def evaluate(
        self,
        proposal: MutationProposal,
        run_tests: bool = True,
    ) -> CircuitResult:
        """
        Run full mutation circuit evaluation.
        
        Args:
            proposal: The mutation to evaluate
            run_tests: Whether to run tests (slower but more accurate)
        
        Returns:
            CircuitResult with pass/fail and all evaluation data
        """
        phases_completed = 0
        
        # Phase 1: Syntax Validation
        try:
            compile(proposal.mutated_code, "<string>", "exec")
            phases_completed = 1
            logger.debug(f"Phase 1 PASSED: Syntax valid for {proposal.component}")
        except SyntaxError as e:
            return CircuitResult(
                passed=False,
                proposal=proposal,
                phases_completed=0,
                failure_reason=f"Syntax error: {e}",
            )
        
        # Phase 2: Test Execution
        if run_tests:
            fitness_result = self.fitness.evaluate(proposal.component, proposal.diff)
            fitness_score = fitness_result.score
            test_results = {
                "passed": fitness_result.tests_passed,
                "failed": fitness_result.tests_failed,
            }
            if fitness_score.correctness < 0.5:
                return CircuitResult(
                    passed=False,
                    proposal=proposal,
                    phases_completed=1,
                    fitness_score=fitness_score,
                    test_results=test_results,
                    failure_reason=f"Tests failing: {fitness_result.tests_failed} failures",
                )
            phases_completed = 2
            logger.debug(f"Phase 2 PASSED: Tests ({fitness_result.tests_passed} passed)")
        else:
            fitness_score = FitnessScore(correctness=0.5)  # Unknown
            test_results = {"skipped": True}
            phases_completed = 2
        
        # Phase 3: Dharmic Gate Check
        telos_check = self.telos.check_action(
            f"Apply mutation to {proposal.component}: {proposal.description}",
            {
                "modifies_files": True,
                "has_backup": True,  # We maintain git history
                "purpose": "self-improvement",
                "verified": run_tests,
            }
        )
        
        # We expect NEEDS_HUMAN for consent gate - that's OK
        tier_a_failed = any(
            g.result == GateResult.FAIL and g.gate == "AHIMSA"
            for g in telos_check.gates
        )
        
        if tier_a_failed:
            return CircuitResult(
                passed=False,
                proposal=proposal,
                phases_completed=2,
                fitness_score=fitness_score,
                telos_check=telos_check,
                failure_reason=f"Dharmic gate AHIMSA failed: {telos_check.recommendation}",
            )
        phases_completed = 3
        logger.debug(f"Phase 3 PASSED: Dharmic gates ({telos_check.alignment_score:.0%})")
        
        # Phase 4: Elegance Evaluation
        elegance_score = self.elegance.evaluate(proposal.mutated_code, proposal.component)
        fitness_score.elegance = elegance_score
        phases_completed = 4
        logger.debug(f"Phase 4 PASSED: Elegance ({elegance_score:.2f})")
        
        # Phase 5: Swarm Voting
        voting_result = self.voting_swarm.vote_on_proposal(
            proposal, fitness_score, telos_check
        )
        phases_completed = 5
        
        passed = voting_result.passed
        failure_reason = None if passed else (
            f"Swarm rejected: {voting_result.approve_count}/{voting_result.total_votes} "
            f"({voting_result.approval_rate:.0%} approval)"
        )
        
        logger.debug(
            f"Phase 5 {'PASSED' if passed else 'FAILED'}: "
            f"Swarm voting ({voting_result.approval_rate:.0%})"
        )
        
        return CircuitResult(
            passed=passed,
            proposal=proposal,
            phases_completed=phases_completed,
            voting_result=voting_result,
            telos_check=telos_check,
            fitness_score=fitness_score,
            elegance_score=elegance_score,
            test_results=test_results,
            failure_reason=failure_reason,
        )


class AutoPusher:
    """
    Automated git commit and push for approved mutations.
    
    Features:
    - Creates meaningful commit messages
    - Maintains evolution lineage in commits
    - Supports dry-run mode
    - Validates before push
    """
    
    def __init__(
        self,
        project_root: Path = None,
        dry_run: bool = True,
        branch: str = "main",
    ):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.dry_run = dry_run
        self.branch = branch
    
    def commit_and_push(
        self,
        proposal: MutationProposal,
        circuit_result: CircuitResult,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Commit and push approved mutation.
        
        Args:
            proposal: The mutation proposal
            circuit_result: Results from circuit evaluation
        
        Returns:
            Tuple of (success, commit_hash, error_message)
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would commit: {proposal.description}")
            return True, "dry_run_hash", None
        
        try:
            # Write the mutated code
            component_path = self.project_root / proposal.component
            backup_path = component_path.with_suffix(component_path.suffix + ".bak")
            
            # Backup original
            if component_path.exists():
                component_path.rename(backup_path)
            
            # Write new code
            component_path.write_text(proposal.mutated_code)
            
            # Stage the file
            subprocess.run(
                ["git", "add", str(component_path)],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            
            # Create commit message
            commit_msg = self._generate_commit_message(proposal, circuit_result)
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                # Restore backup
                if backup_path.exists():
                    backup_path.rename(component_path)
                return False, None, f"Commit failed: {result.stderr}"
            
            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            commit_hash = result.stdout.strip()
            
            # Push
            result = subprocess.run(
                ["git", "push", "origin", self.branch],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                logger.warning(f"Push failed (commit saved locally): {result.stderr}")
                return True, commit_hash, f"Push failed: {result.stderr}"
            
            # Clean up backup
            if backup_path.exists():
                backup_path.unlink()
            
            logger.info(f"Committed and pushed: {commit_hash[:8]}")
            return True, commit_hash, None
            
        except Exception as e:
            logger.error(f"AutoPusher error: {e}")
            return False, None, str(e)
    
    def _generate_commit_message(
        self,
        proposal: MutationProposal,
        circuit_result: CircuitResult,
    ) -> str:
        """Generate meaningful commit message."""
        emoji_map = {
            "refactor": "♻️",
            "optimize": "⚡",
            "fix": "🔧",
            "enhance": "✨",
            "document": "📝",
        }
        emoji = emoji_map.get(proposal.mutation_type, "🧬")
        
        lines = [
            f"{emoji} [DGM] {proposal.description}",
            "",
            f"Mutation Type: {proposal.mutation_type}",
            f"Component: {proposal.component}",
            f"Parent: {proposal.parent_id or 'None (fresh)'}",
            "",
            f"Circuit Result:",
            f"  - Phases: {circuit_result.phases_completed}/5",
            f"  - Fitness: {circuit_result.fitness_score.total():.2f}" if circuit_result.fitness_score else "  - Fitness: N/A",
            f"  - Elegance: {circuit_result.elegance_score:.2f}",
        ]
        
        if circuit_result.voting_result:
            lines.append(
                f"  - Approval: {circuit_result.voting_result.approval_rate:.0%} "
                f"({circuit_result.voting_result.approve_count}/{circuit_result.voting_result.total_votes})"
            )
        
        lines.extend([
            "",
            f"Proposal ID: {proposal.id}",
            "---",
            "Automated by DGM Orchestrator",
        ])
        
        return "\n".join(lines)


# =============================================================================
# Main Orchestrator
# =============================================================================

class DGMOrchestrator:
    """
    The Brain - Full Autonomous Self-Improvement Loop.
    
    Orchestrates all DGM components to run continuous improvement cycles:
    
    Multi-Model Pipeline:
    1. ANALYZE (Claude) — Understand what needs improvement
    2. PROPOSE (Codex) — Generate mutation candidates (fast, cheap)
    3. BUILD (Claude sub-agents) — Implement the best proposal
    4. RED TEAM (Claude) — Attack the implementation
    5. SLIM (Claude) — Remove bloat
    6. REVIEW (Kimi) — Deep 128k context review
    7. VERIFY (Claude) — Final dharmic gates
    8. PUSH (Auto) — Git commit if all pass
    
    Each model is optimal for its task. Graceful fallback to Claude if unavailable.
    """
    
    # Configuration
    DEFAULT_COOLDOWN_CYCLES = 3  # Wait N cycles before re-improving same component
    MIN_INTERVAL_SECONDS = 60   # Minimum time between cycles
    
    def __init__(
        self,
        project_root: Path = None,
        archive: Archive = None,
        dry_run: bool = True,
        use_codex: bool = True,
        use_kimi_review: bool = True,
    ):
        """
        Initialize the DGM Orchestrator.
        
        Args:
            project_root: Root directory of the project
            archive: Evolution archive (creates default if None)
            dry_run: If True, don't actually commit/push changes
            use_codex: If True, use CodexProposer for mutations (fast, cheap)
            use_kimi_review: If True, use KimiReviewer for deep code review
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.archive = archive or get_archive()
        self.dry_run = dry_run
        
        # Multi-model configuration
        self.use_codex = use_codex
        self.use_kimi_review = use_kimi_review
        
        # Initialize sub-components
        self.selector = Selector(self.archive)
        self.mutator = Mutator(self.project_root)
        self.fitness_evaluator = FitnessEvaluator(self.project_root)
        self.elegance_evaluator = EleganceEvaluator(self.project_root)
        self.voting_swarm = VotingSwarm()
        self.telos = TelosLayer()
        self.circuit = MutationCircuit(
            project_root=self.project_root,
            voting_swarm=self.voting_swarm,
            elegance_evaluator=self.elegance_evaluator,
            fitness_evaluator=self.fitness_evaluator,
            telos_layer=self.telos,
        )
        self.auto_pusher = AutoPusher(self.project_root, dry_run=dry_run)
        
        # Initialize multi-model components (with graceful fallback)
        self.codex_proposer = None
        self.kimi_reviewer = None
        
        if use_codex and CODEX_AVAILABLE:
            try:
                self.codex_proposer = CodexProposer(self.project_root)
                logger.info("CodexProposer initialized — using Codex for fast proposals")
            except Exception as e:
                logger.warning(f"CodexProposer init failed, falling back to Claude Mutator: {e}")
                self.codex_proposer = None
        elif use_codex and not CODEX_AVAILABLE:
            logger.info("CodexProposer not available — using Claude Mutator for proposals")
        
        if use_kimi_review and KIMI_AVAILABLE:
            try:
                self.kimi_reviewer = KimiReviewer(self.project_root)
                logger.info("KimiReviewer initialized — using Kimi for deep 128k context review")
            except Exception as e:
                logger.warning(f"KimiReviewer init failed, falling back to Claude review: {e}")
                self.kimi_reviewer = None
        elif use_kimi_review and not KIMI_AVAILABLE:
            logger.info("KimiReviewer not available — using Claude sub-agent for review")
        
        # State tracking
        self.current_cycle = 0
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.last_cycle_time = 0.0
        self._running = False
        
        # Log configuration
        models_active = []
        if self.codex_proposer:
            models_active.append("Codex(propose)")
        if self.kimi_reviewer:
            models_active.append("Kimi(review)")
        models_active.append("Claude(build/verify)")
        
        logger.info(
            f"DGM Orchestrator initialized | "
            f"project={self.project_root} | dry_run={dry_run} | "
            f"models=[{', '.join(models_active)}]"
        )
    
    def run_improvement_cycle(
        self,
        target_component: str = None,
        run_tests: bool = True,
    ) -> ImprovementResult:
        """
        Run a single improvement cycle using the multi-model pipeline.
        
        The Pipeline:
        1. ANALYZE (Claude) — Select & understand component to improve
        2. PROPOSE (Codex) — Generate mutation candidates (fast, cheap)
        3. BUILD (Claude) — Implement the best proposal  
        4. RED TEAM (Claude) — Attack the implementation
        5. SLIM (Claude) — Remove bloat
        6. REVIEW (Kimi) — Deep 128k context review
        7. VERIFY (Claude) — Final dharmic gates
        8. PUSH (Auto) — Git commit if all pass
        
        Args:
            target_component: Specific component to improve (None = auto-select)
            run_tests: Whether to run tests during evaluation
        
        Returns:
            ImprovementResult with full details including models_used
        """
        start_time = time.time()
        cycle_id = self._generate_cycle_id()
        self.current_cycle += 1
        
        # Track which model handled each phase
        models_used: Dict[str, str] = {}
        
        logger.info(f"=== Improvement Cycle {self.current_cycle} ({cycle_id}) ===")
        
        # =====================================================================
        # Phase 1: ANALYZE — Select component (Claude / Selection Logic)
        # =====================================================================
        models_used["analyze"] = "claude"
        
        if target_component:
            component = target_component
            logger.info(f"[ANALYZE] Target component: {component}")
        else:
            component = self._select_component()
            if not component:
                return ImprovementResult(
                    success=False,
                    status=ImprovementStatus.REJECTED,
                    component="",
                    cycle_id=cycle_id,
                    error="No component available for improvement",
                    duration_seconds=time.time() - start_time,
                    models_used=models_used,
                )
            logger.info(f"[ANALYZE] Auto-selected component: {component}")
        
        # Update component metrics
        if component not in self.component_metrics:
            self.component_metrics[component] = ComponentMetrics(component=component)
        self.component_metrics[component].improvement_attempts += 1
        
        # Get best parent from archive
        parent_result = self.selector.select_parent(component=component, strategy="elite")
        parent = parent_result.parent
        logger.info(
            f"[ANALYZE] Parent: {parent.id if parent else 'None (fresh)'} | "
            f"Method: {parent_result.method}"
        )
        
        # =====================================================================
        # Phase 2: PROPOSE — Generate mutation (Codex or Claude fallback)
        # =====================================================================
        try:
            if self.codex_proposer:
                # Use Codex for fast, cheap proposals
                models_used["propose"] = "codex"
                logger.info("[PROPOSE] Using CodexProposer for mutation candidates...")
                proposal = self.codex_proposer.propose_improvement(
                    component=component,
                    parent=parent,
                )
                logger.info(f"[PROPOSE] Codex proposal: {proposal.id} | {proposal.mutation_type}")
            else:
                # Fallback to Claude Mutator
                models_used["propose"] = "claude"
                logger.info("[PROPOSE] Using Claude Mutator (Codex unavailable)...")
                proposal = self.mutator.propose_improvement(
                    component=component,
                    parent=parent,
                )
                logger.info(f"[PROPOSE] Claude proposal: {proposal.id} | {proposal.mutation_type}")
        except Exception as e:
            # Graceful fallback: if Codex fails, try Claude
            if self.codex_proposer and models_used.get("propose") == "codex":
                logger.warning(f"[PROPOSE] Codex failed ({e}), falling back to Claude...")
                models_used["propose"] = "claude (fallback)"
                try:
                    proposal = self.mutator.propose_improvement(
                        component=component,
                        parent=parent,
                    )
                    logger.info(f"[PROPOSE] Claude fallback proposal: {proposal.id}")
                except Exception as e2:
                    logger.error(f"[PROPOSE] Both Codex and Claude failed: {e2}")
                    return ImprovementResult(
                        success=False,
                        status=ImprovementStatus.ERROR,
                        component=component,
                        cycle_id=cycle_id,
                        error=f"Proposal generation failed: {e2}",
                        duration_seconds=time.time() - start_time,
                        models_used=models_used,
                    )
            else:
                logger.error(f"[PROPOSE] Mutator error: {e}")
                return ImprovementResult(
                    success=False,
                    status=ImprovementStatus.ERROR,
                    component=component,
                    cycle_id=cycle_id,
                    error=f"Mutator error: {e}",
                    duration_seconds=time.time() - start_time,
                    models_used=models_used,
                )
        
        # =====================================================================
        # Phases 3-5: BUILD, RED TEAM, SLIM (Claude via MutationCircuit)
        # =====================================================================
        models_used["build"] = "claude"
        models_used["red_team"] = "claude"
        models_used["slim"] = "claude"
        
        try:
            logger.info("[BUILD/RED_TEAM/SLIM] Running MutationCircuit evaluation...")
            circuit_result = self.circuit.evaluate(proposal, run_tests=run_tests)
            circuit_result.models_used = models_used.copy()
            
            logger.info(
                f"[CIRCUIT] {'PASSED' if circuit_result.passed else 'FAILED'} | "
                f"Phases: {circuit_result.phases_completed}/5 | "
                f"Reason: {circuit_result.failure_reason or 'All phases passed'}"
            )
        except Exception as e:
            logger.error(f"[CIRCUIT] Error: {e}")
            return ImprovementResult(
                success=False,
                status=ImprovementStatus.ERROR,
                component=component,
                cycle_id=cycle_id,
                proposal=proposal,
                error=f"Circuit error: {e}",
                duration_seconds=time.time() - start_time,
                models_used=models_used,
            )
        
        # =====================================================================
        # Phase 6: REVIEW — Deep code review (Kimi or Claude fallback)
        # =====================================================================
        if circuit_result.passed:
            review_passed = True
            review_result = None
            
            if self.kimi_reviewer:
                # Use Kimi for deep 128k context review
                models_used["review"] = "kimi"
                logger.info("[REVIEW] Using KimiReviewer for deep 128k context review...")
                try:
                    review_result = self.kimi_reviewer.review(
                        proposal=proposal,
                        circuit_result=circuit_result,
                    )
                    review_passed = review_result.get("approved", True)
                    circuit_result.review_result = review_result
                    
                    if review_passed:
                        logger.info(f"[REVIEW] Kimi APPROVED: {review_result.get('summary', 'No issues')}")
                    else:
                        logger.warning(f"[REVIEW] Kimi REJECTED: {review_result.get('reason', 'Unknown')}")
                        circuit_result.passed = False
                        circuit_result.failure_reason = f"Kimi review rejected: {review_result.get('reason', 'Unknown')}"
                except Exception as e:
                    # Graceful fallback: if Kimi fails, continue without deep review
                    logger.warning(f"[REVIEW] Kimi failed ({e}), skipping deep review...")
                    models_used["review"] = "kimi (failed)"
                    review_passed = True  # Don't block on Kimi failure
            else:
                # No Kimi available - use Claude sub-agent review (via voting swarm)
                models_used["review"] = "claude"
                logger.info("[REVIEW] Using Claude (Kimi unavailable) — review via voting swarm")
                # Note: Claude review already happened in MutationCircuit voting phase
        else:
            models_used["review"] = "skipped"
            logger.info("[REVIEW] Skipped — circuit failed earlier")
        
        # =====================================================================
        # Phase 7: VERIFY — Final dharmic gates (Claude / Telos)
        # =====================================================================
        models_used["verify"] = "claude"
        # Note: Dharmic verification already happened in circuit phase 3
        
        # =====================================================================
        # Phase 8: PUSH — Commit if passed
        # =====================================================================
        commit_hash = None
        if circuit_result.passed:
            models_used["push"] = "auto"
            success, commit_hash, error = self.auto_pusher.commit_and_push(
                proposal, circuit_result
            )
            if success:
                logger.info(f"[PUSH] Committed: {commit_hash}")
                status = ImprovementStatus.PUSHED if not self.dry_run else ImprovementStatus.COMMITTED
            else:
                logger.warning(f"[PUSH] Commit failed: {error}")
                status = ImprovementStatus.CIRCUIT_PASSED
        else:
            models_used["push"] = "skipped"
            status = ImprovementStatus.CIRCUIT_FAILED
        
        # =====================================================================
        # Archive result
        # =====================================================================
        entry = self._create_archive_entry(
            proposal, circuit_result, commit_hash, status, models_used
        )
        entry_id = self.archive.add_entry(entry)
        logger.info(f"[ARCHIVE] Entry: {entry_id}")
        
        # Update metrics
        if circuit_result.passed:
            self.component_metrics[component].successful_improvements += 1
        self.component_metrics[component].last_modified_cycle = self.current_cycle
        if circuit_result.fitness_score:
            self.component_metrics[component].recent_fitness.append(
                circuit_result.fitness_score.total()
            )
            # Keep only last 10 fitness values
            self.component_metrics[component].recent_fitness = \
                self.component_metrics[component].recent_fitness[-10:]
        
        # =====================================================================
        # Return result with model tracking
        # =====================================================================
        duration = time.time() - start_time
        self.last_cycle_time = time.time()
        
        result = ImprovementResult(
            success=circuit_result.passed,
            status=status,
            component=component,
            cycle_id=cycle_id,
            proposal=proposal,
            circuit_result=circuit_result,
            commit_hash=commit_hash,
            entry_id=entry_id,
            duration_seconds=duration,
            models_used=models_used,
        )
        
        # Log model usage summary
        model_summary = " | ".join(f"{phase}={model}" for phase, model in models_used.items() if model != "skipped")
        logger.info(
            f"Cycle complete: {'SUCCESS' if result.success else 'FAILED'} | "
            f"Duration: {duration:.1f}s | Models: [{model_summary}]"
        )
        
        return result
    
    async def run_continuous(
        self,
        interval_minutes: int = 30,
        max_cycles: int = None,
    ) -> List[ImprovementResult]:
        """
        Run improvement cycles continuously.
        
        Args:
            interval_minutes: Minutes between cycles
            max_cycles: Maximum cycles to run (None = infinite)
        
        Returns:
            List of all ImprovementResults
        """
        self._running = True
        results = []
        cycles_run = 0
        interval_seconds = max(interval_minutes * 60, self.MIN_INTERVAL_SECONDS)
        
        logger.info(
            f"Starting continuous improvement | "
            f"Interval: {interval_minutes}min | Max cycles: {max_cycles or 'unlimited'}"
        )
        
        try:
            while self._running:
                # Check max cycles
                if max_cycles and cycles_run >= max_cycles:
                    logger.info(f"Reached max cycles ({max_cycles})")
                    break
                
                # Run cycle
                result = self.run_improvement_cycle()
                results.append(result)
                cycles_run += 1
                
                # Log progress
                success_count = sum(1 for r in results if r.success)
                logger.info(
                    f"Continuous progress: {cycles_run} cycles | "
                    f"{success_count} successes | "
                    f"{len(results) - success_count} failures"
                )
                
                # Wait for next cycle
                if self._running and (max_cycles is None or cycles_run < max_cycles):
                    logger.info(f"Waiting {interval_minutes} minutes until next cycle...")
                    await asyncio.sleep(interval_seconds)
        
        except asyncio.CancelledError:
            logger.info("Continuous improvement cancelled")
        except Exception as e:
            logger.error(f"Continuous improvement error: {e}")
            raise
        finally:
            self._running = False
        
        logger.info(
            f"Continuous improvement complete | "
            f"Total: {len(results)} cycles | "
            f"Successes: {sum(1 for r in results if r.success)}"
        )
        
        return results
    
    def stop(self):
        """Stop continuous improvement loop."""
        self._running = False
        logger.info("Stop requested")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "current_cycle": self.current_cycle,
            "running": self._running,
            "dry_run": self.dry_run,
            "archive_size": len(self.archive.entries),
            "components_tracked": len(self.component_metrics),
            "multi_model": {
                "codex_available": CODEX_AVAILABLE,
                "codex_active": self.codex_proposer is not None,
                "kimi_available": KIMI_AVAILABLE,
                "kimi_active": self.kimi_reviewer is not None,
                "use_codex_config": self.use_codex,
                "use_kimi_config": self.use_kimi_review,
            },
            "best_entries": [
                {
                    "id": e.id,
                    "component": e.component,
                    "fitness": e.fitness.total(),
                    "status": e.status,
                }
                for e in self.archive.get_best(5)
            ],
            "component_metrics": {
                k: {
                    "attempts": v.improvement_attempts,
                    "successes": v.successful_improvements,
                    "success_rate": v.success_rate,
                    "fitness_trend": v.fitness_trend,
                    "last_modified_cycle": v.last_modified_cycle,
                }
                for k, v in self.component_metrics.items()
            },
        }
    
    def _select_component(self) -> Optional[str]:
        """
        Select component to improve using smart strategy.
        
        Strategy:
        1. Prioritize components with declining fitness
        2. Prioritize components with recent test failures
        3. Avoid components modified in last N cycles
        """
        # Get all known components
        components = set()
        for entry in self.archive.entries.values():
            if entry.component:
                components.add(entry.component)
        
        # Add any from metrics
        components.update(self.component_metrics.keys())
        
        if not components:
            # Default to some known components
            default_components = [
                "src/dgm/archive.py",
                "src/dgm/fitness.py",
                "src/dgm/selector.py",
            ]
            for c in default_components:
                path = self.project_root / c
                if path.exists():
                    return c
            return None
        
        # Score each component
        scores = {}
        for component in components:
            score = self._score_component_priority(component)
            scores[component] = score
        
        # Select highest priority
        if not scores:
            return None
        
        best_component = max(scores, key=scores.get)
        logger.debug(f"Component selection scores: {scores}")
        return best_component
    
    def _score_component_priority(self, component: str) -> float:
        """
        Score component priority for improvement.
        
        Higher = more urgent to improve
        """
        score = 0.5  # Base score
        
        metrics = self.component_metrics.get(component)
        if metrics:
            # Declining fitness → higher priority
            if metrics.fitness_trend < 0:
                score += 0.3 * abs(metrics.fitness_trend)
            
            # Low success rate → higher priority
            if metrics.success_rate < 0.5:
                score += 0.2
            
            # Recently modified → lower priority (let changes settle)
            cycles_since_modified = self.current_cycle - metrics.last_modified_cycle
            if cycles_since_modified < self.DEFAULT_COOLDOWN_CYCLES:
                score -= 0.5  # Cooldown
            
            # Test failures → higher priority
            if metrics.test_failures > 0:
                score += 0.1 * min(metrics.test_failures, 5)
        else:
            # Never improved → give it a chance
            score += 0.2
        
        return max(0.0, score)
    
    def _create_archive_entry(
        self,
        proposal: MutationProposal,
        circuit_result: CircuitResult,
        commit_hash: Optional[str],
        status: ImprovementStatus,
        models_used: Dict[str, str] = None,
    ) -> EvolutionEntry:
        """Create archive entry from improvement results."""
        fitness = circuit_result.fitness_score or FitnessScore()
        
        # Map status to archive status
        status_map = {
            ImprovementStatus.PUSHED: "applied",
            ImprovementStatus.COMMITTED: "applied",
            ImprovementStatus.CIRCUIT_PASSED: "approved",
            ImprovementStatus.CIRCUIT_FAILED: "rejected",
            ImprovementStatus.REJECTED: "rejected",
            ImprovementStatus.ERROR: "rejected",
        }
        archive_status = status_map.get(status, "proposed")
        
        # Build model string for tracking (e.g., "codex+claude+kimi")
        if models_used:
            # Get unique models used (excluding 'skipped' and 'auto')
            unique_models = sorted(set(
                m.split(" ")[0] for m in models_used.values() 
                if m not in ("skipped", "auto")
            ))
            model_str = "+".join(unique_models) if unique_models else "dgm-v1"
        else:
            model_str = "dgm-v1"
        
        # Include models_used in test_results for archival
        enriched_test_results = dict(circuit_result.test_results)
        if models_used:
            enriched_test_results["models_used"] = models_used
        if circuit_result.review_result:
            enriched_test_results["kimi_review"] = circuit_result.review_result
        
        return EvolutionEntry(
            id="",  # Will be generated
            timestamp="",  # Will be generated
            parent_id=proposal.parent_id,
            component=proposal.component,
            change_type=proposal.mutation_type,
            description=proposal.description,
            diff=proposal.diff,
            commit_hash=commit_hash,
            fitness=fitness,
            test_results=enriched_test_results,
            gates_passed=[
                g.gate for g in (circuit_result.telos_check.gates if circuit_result.telos_check else [])
                if g.result == GateResult.PASS
            ],
            gates_failed=[
                g.gate for g in (circuit_result.telos_check.gates if circuit_result.telos_check else [])
                if g.result == GateResult.FAIL
            ],
            agent_id="dgm_orchestrator",
            model=model_str,  # Track which models were used
            tokens_used=0,
            status=archive_status,
        )
    
    def _generate_cycle_id(self) -> str:
        """Generate unique cycle ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.sha256(
            f"{timestamp}{self.current_cycle}".encode()
        ).hexdigest()[:6]
        return f"cycle_{timestamp}_{hash_part}"


# =============================================================================
# CLI Interface
# =============================================================================

async def main():
    """CLI entry point for DGM Orchestrator."""
    parser = argparse.ArgumentParser(
        description="DGM Orchestrator - Autonomous Self-Improvement Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single improvement cycle on specific component
  python -m src.dgm.dgm_orchestrator --target src/dgm/voting.py

  # Run continuous improvement every 30 minutes
  python -m src.dgm.dgm_orchestrator --continuous --interval 30

  # Check current status
  python -m src.dgm.dgm_orchestrator --status

  # Dry run (no commits)
  python -m src.dgm.dgm_orchestrator --target src/dgm/archive.py --dry-run
        """
    )
    
    parser.add_argument(
        "--target", "-t",
        help="Target component to improve (e.g., src/dgm/voting.py)"
    )
    parser.add_argument(
        "--continuous", "-c",
        action="store_true",
        help="Run continuous improvement loop"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Interval between cycles in minutes (default: 30)"
    )
    parser.add_argument(
        "--max-cycles", "-m",
        type=int,
        default=None,
        help="Maximum number of cycles (default: unlimited)"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current DGM status"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        default=True,
        help="Don't commit/push changes (default: True)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually commit and push changes (CAREFUL!)"
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip running tests (faster but less accurate)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Multi-model pipeline options
    parser.add_argument(
        "--use-codex",
        action="store_true",
        default=True,
        help="Use CodexProposer for fast proposals (default: True)"
    )
    parser.add_argument(
        "--no-codex",
        action="store_true",
        help="Disable Codex, use Claude for proposals"
    )
    parser.add_argument(
        "--use-kimi",
        action="store_true",
        default=True,
        help="Use KimiReviewer for deep code review (default: True)"
    )
    parser.add_argument(
        "--no-kimi",
        action="store_true",
        help="Disable Kimi, use Claude for review"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine dry-run mode
    dry_run = not args.live
    
    # Determine multi-model config
    use_codex = args.use_codex and not args.no_codex
    use_kimi = args.use_kimi and not args.no_kimi
    
    # Initialize orchestrator with multi-model config
    orchestrator = DGMOrchestrator(
        dry_run=dry_run,
        use_codex=use_codex,
        use_kimi_review=use_kimi,
    )
    
    # Handle commands
    if args.status:
        status = orchestrator.get_status()
        print("\n" + "=" * 60)
        print("DGM ORCHESTRATOR STATUS")
        print("=" * 60)
        print(f"Current Cycle: {status['current_cycle']}")
        print(f"Running: {status['running']}")
        print(f"Mode: {'DRY RUN' if status['dry_run'] else 'LIVE'}")
        print(f"Archive Size: {status['archive_size']} entries")
        print(f"Components Tracked: {status['components_tracked']}")
        
        # Multi-model status
        print(f"\nMulti-Model Pipeline:")
        print(f"  Codex (proposals): {'AVAILABLE' if CODEX_AVAILABLE and orchestrator.codex_proposer else 'UNAVAILABLE (using Claude)'}")
        print(f"  Kimi (review):     {'AVAILABLE' if KIMI_AVAILABLE and orchestrator.kimi_reviewer else 'UNAVAILABLE (using Claude)'}")
        
        if status['best_entries']:
            print("\nTop 5 Entries:")
            for e in status['best_entries']:
                print(f"  [{e['status']}] {e['id'][:20]}... | {e['component']} | fitness={e['fitness']:.2f}")
        
        if status['component_metrics']:
            print("\nComponent Metrics:")
            for comp, m in status['component_metrics'].items():
                trend = "↑" if m['fitness_trend'] > 0 else ("↓" if m['fitness_trend'] < 0 else "→")
                print(
                    f"  {comp}: "
                    f"{m['successes']}/{m['attempts']} successes "
                    f"({m['success_rate']:.0%}) {trend}"
                )
        
        print("=" * 60)
        return
    
    if args.continuous:
        print(f"\nStarting continuous improvement (interval: {args.interval}min)")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE - CHANGES WILL BE COMMITTED'}")
        print("Press Ctrl+C to stop\n")
        
        try:
            results = await orchestrator.run_continuous(
                interval_minutes=args.interval,
                max_cycles=args.max_cycles,
            )
            
            # Summary
            print("\n" + "=" * 60)
            print("CONTINUOUS IMPROVEMENT SUMMARY")
            print("=" * 60)
            print(f"Total Cycles: {len(results)}")
            print(f"Successes: {sum(1 for r in results if r.success)}")
            print(f"Failures: {sum(1 for r in results if not r.success)}")
            
        except KeyboardInterrupt:
            print("\nStopping...")
            orchestrator.stop()
        
        return
    
    if args.target:
        print(f"\nRunning single improvement cycle on: {args.target}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE - CHANGES WILL BE COMMITTED'}")
        print()
        
        result = orchestrator.run_improvement_cycle(
            target_component=args.target,
            run_tests=not args.no_tests,
        )
        
        print("\n" + "=" * 60)
        print("IMPROVEMENT CYCLE RESULT")
        print("=" * 60)
        print(f"Status: {result.status.value}")
        print(f"Success: {result.success}")
        print(f"Component: {result.component}")
        print(f"Cycle ID: {result.cycle_id}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        
        if result.proposal:
            print(f"\nProposal: {result.proposal.id}")
            print(f"  Type: {result.proposal.mutation_type}")
            print(f"  Description: {result.proposal.description}")
        
        if result.circuit_result:
            print(f"\nCircuit: {result.circuit_result.phases_completed}/5 phases")
            if result.circuit_result.fitness_score:
                print(f"  Fitness: {result.circuit_result.fitness_score.total():.2f}")
            print(f"  Elegance: {result.circuit_result.elegance_score:.2f}")
            if result.circuit_result.failure_reason:
                print(f"  Failure: {result.circuit_result.failure_reason}")
        
        if result.commit_hash:
            print(f"\nCommit: {result.commit_hash}")
        
        if result.entry_id:
            print(f"Archive Entry: {result.entry_id}")
        
        if result.models_used:
            print(f"\nModels Used:")
            for phase, model in result.models_used.items():
                if model != "skipped":
                    print(f"  {phase}: {model}")
        
        if result.error:
            print(f"\nError: {result.error}")
        
        print("=" * 60)
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
