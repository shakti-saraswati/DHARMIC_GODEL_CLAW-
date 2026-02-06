from __future__ import annotations
"""Core evaluation system for the DHARMIC GODEL CLAW swarm."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .types import Proposal, EvaluationResult


class EvaluationStatus(Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvaluationContext:
    """Context for evaluation including metrics and constraints."""
    proposal: Proposal
    current_metrics: Dict[str, float]
    resource_limits: Dict[str, Any]
    safety_constraints: List[str]
    timestamp: datetime


class ProposalEvaluator:
    """Evaluates proposals for safety, feasibility, and potential impact."""
    
    def __init__(self, safety_threshold: float = 0.7, impact_threshold: float = 0.5):
        """Initialize evaluator with thresholds."""
        self.safety_threshold = safety_threshold
        self.impact_threshold = impact_threshold
        self.logger = logging.getLogger(__name__)
        self._evaluation_cache: Dict[str, EvaluationResult] = {}
    
    async def evaluate_proposal(self, proposal: Proposal, context: EvaluationContext) -> EvaluationResult:
        """Evaluate a single proposal comprehensively."""
        try:
            # Check cache first
            cache_key = self._get_cache_key(proposal, context)
            if cache_key in self._evaluation_cache:
                return self._evaluation_cache[cache_key]
            
            # Run parallel evaluations
            safety_score, impact_score, feasibility_score = await asyncio.gather(
                self._evaluate_safety(proposal, context),
                self._evaluate_impact(proposal, context),
                self._evaluate_feasibility(proposal, context)
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                safety_score, impact_score, feasibility_score
            )
            
            # Make decision
            approved = (
                safety_score >= self.safety_threshold and
                impact_score >= self.impact_threshold and
                feasibility_score >= 0.6 and
                overall_score >= 0.6
            )
            
            result = EvaluationResult(
                proposal_id=proposal.id,
                approved=approved,
                safety_score=safety_score,
                impact_score=impact_score,
                feasibility_score=feasibility_score,
                overall_score=overall_score,
                reasoning=self._generate_reasoning(
                    safety_score, impact_score, feasibility_score, approved
                ),
                timestamp=datetime.now()
            )
            
            # Cache result
            self._evaluation_cache[cache_key] = result
            return result
            
        except Exception as e:
            self.logger.error(f"Evaluation failed for proposal {proposal.id}: {e}")
            return EvaluationResult(
                proposal_id=proposal.id,
                approved=False,
                safety_score=0.0,
                impact_score=0.0,
                feasibility_score=0.0,
                overall_score=0.0,
                reasoning=f"Evaluation failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _evaluate_safety(self, proposal: Proposal, context: EvaluationContext) -> float:
        """Evaluate safety of proposal."""
        score = 1.0
        
        # Check against safety constraints
        for constraint in context.safety_constraints:
            if self._violates_constraint(proposal, constraint):
                score *= 0.5
        
        # Penalize high-risk operations
        if any(keyword in proposal.description.lower() for keyword in 
               ['delete', 'remove', 'destroy', 'shutdown']):
            score *= 0.7
        
        # Reward gradual changes
        if 'incremental' in proposal.description.lower():
            score *= 1.1
        
        return min(score, 1.0)
    
    async def _evaluate_impact(self, proposal: Proposal, context: EvaluationContext) -> float:
        """Evaluate potential positive impact."""
        score = 0.5  # Base score
        
        # Reward improvement keywords
        improvement_keywords = [
            'improve', 'optimize', 'enhance', 'better', 'faster', 'efficient'
        ]
        
        for keyword in improvement_keywords:
            if keyword in proposal.description.lower():
                score += 0.1
        
        # Consider proposal type
        if proposal.type == 'optimization':
            score += 0.2
        elif proposal.type == 'feature':
            score += 0.15
        elif proposal.type == 'fix':
            score += 0.1
        
        return min(score, 1.0)
    
    async def _evaluate_feasibility(self, proposal: Proposal, context: EvaluationContext) -> float:
        """Evaluate implementation feasibility."""
        score = 0.8  # Base feasibility
        
        # Check resource requirements
        if hasattr(proposal, 'resource_requirements'):
            for resource, required in proposal.resource_requirements.items():
                if resource in context.resource_limits:
                    available = context.resource_limits[resource]
                    if required > available:
                        score *= 0.3
                    elif required > available * 0.8:
                        score *= 0.7
        
        # Consider complexity
        complexity_indicators = ['complex', 'major', 'significant', 'extensive']
        for indicator in complexity_indicators:
            if indicator in proposal.description.lower():
                score *= 0.8
        
        return max(score, 0.1)
    
    def _calculate_overall_score(self, safety: float, impact: float, feasibility: float) -> float:
        """Calculate weighted overall score."""
        # Safety is most important, then feasibility, then impact
        return (safety * 0.5) + (feasibility * 0.3) + (impact * 0.2)
    
    def _generate_reasoning(self, safety: float, impact: float, feasibility: float, approved: bool) -> str:
        """Generate human-readable reasoning for the decision."""
        parts = []
        
        if safety < self.safety_threshold:
            parts.append(f"Safety concerns (score: {safety:.2f})")
        if impact < self.impact_threshold:
            parts.append(f"Limited impact (score: {impact:.2f})")
        if feasibility < 0.6:
            parts.append(f"Feasibility issues (score: {feasibility:.2f})")
        
        if approved:
            return "Proposal approved: meets all thresholds"
        else:
            return "Proposal rejected: " + ", ".join(parts)
    
    def _violates_constraint(self, proposal: Proposal, constraint: str) -> bool:
        """Check if proposal violates a safety constraint."""
        # Simple keyword-based constraint checking
        constraint_lower = constraint.lower()
        description_lower = proposal.description.lower()
        
        if 'no_external_network' in constraint_lower:
            return any(keyword in description_lower for keyword in 
                      ['network', 'internet', 'http', 'api', 'external'])
        
        if 'no_file_system' in constraint_lower:
            return any(keyword in description_lower for keyword in 
                      ['file', 'directory', 'path', 'write', 'read'])
        
        return False
    
    def _get_cache_key(self, proposal: Proposal, context: EvaluationContext) -> str:
        """Generate cache key for proposal and context."""
        return f"{proposal.id}_{hash(str(context.safety_constraints))}"


class EvaluationWorkflow:
    """Manages the complete evaluation workflow."""
    
    def __init__(self, evaluator: ProposalEvaluator):
        """Initialize workflow with evaluator."""
        self.evaluator = evaluator
        self.logger = logging.getLogger(__name__)
        self._active_evaluations: Dict[str, EvaluationStatus] = {}
    
    async def process_proposals(self, proposals: List[Proposal], 
                              context: EvaluationContext) -> List[EvaluationResult]:
        """Process multiple proposals concurrently."""
        results = []
        
        # Mark evaluations as in progress
        for proposal in proposals:
            self._active_evaluations[proposal.id] = EvaluationStatus.IN_PROGRESS
        
        try:
            # Evaluate all proposals concurrently
            evaluation_tasks = [
                self.evaluator.evaluate_proposal(proposal, context)
                for proposal in proposals
            ]
            
            results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
            
            # Handle any exceptions
            final_results = []
            for i, result in enumerate(results):
                proposal_id = proposals[i].id
                
                if isinstance(result, Exception):
                    self.logger.error(f"Evaluation failed for {proposal_id}: {result}")
                    self._active_evaluations[proposal_id] = EvaluationStatus.FAILED
                    final_results.append(EvaluationResult(
                        proposal_id=proposal_id,
                        approved=False,
                        safety_score=0.0,
                        impact_score=0.0,
                        feasibility_score=0.0,
                        overall_score=0.0,
                        reasoning=f"Evaluation error: {str(result)}",
                        timestamp=datetime.now()
                    ))
                else:
                    self._active_evaluations[proposal_id] = EvaluationStatus.COMPLETED
                    final_results.append(result)
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Workflow processing failed: {e}")
            # Mark all as failed
            for proposal in proposals:
                self._active_evaluations[proposal.id] = EvaluationStatus.FAILED
            raise
    
    def get_evaluation_status(self, proposal_id: str) -> Optional[EvaluationStatus]:
        """Get current status of an evaluation."""
        return self._active_evaluations.get(proposal_id)
    
    async def batch_evaluate(self, proposals: List[Proposal], 
                           batch_size: int = 10) -> List[EvaluationResult]:
        """Evaluate proposals in batches to manage resources."""
        all_results = []
        
        for i in range(0, len(proposals), batch_size):
            batch = proposals[i:i + batch_size]
            
            # Create context for this batch
            context = EvaluationContext(
                proposal=batch[0],  # Use first proposal for context
                current_metrics={},
                resource_limits={'cpu': 0.8, 'memory': 0.8},
                safety_constraints=['no_external_network', 'no_destructive_ops'],
                timestamp=datetime.now()
            )
            
            batch_results = await self.process_proposals(batch, context)
            all_results.extend(batch_results)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        return all_results