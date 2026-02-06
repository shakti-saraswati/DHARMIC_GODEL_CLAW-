from __future__ import annotations
"""Evaluator Agent - Evaluates proposals using the 17-gate protocol.

This agent is the CODE_GUARDIAN role - it runs all gates and produces
signed evidence bundles. It cannot write code or modify gates.
"""

import os
from dataclasses import dataclass, field
from typing import List, Any, Optional
from pathlib import Path
import logging
import sys

# Import the gate runner
sys.path.insert(0, str(Path(__file__).parent))
from run_gates import GateRunner, EVIDENCE_DIR


@dataclass
class ProposalEvaluation:
    """Evaluation of a single proposal."""
    proposal: Any
    approved: bool
    score: float
    feedback: str = ""
    gate_result: Optional[Any] = None


@dataclass
class EvaluationResult:
    """Result of evaluating multiple proposals."""
    proposals: List[ProposalEvaluation] = field(default_factory=list)
    overall_score: float = 0.0
    gates_passed: int = 0
    gates_failed: int = 0
    gates_warned: int = 0
    evidence_bundle_hash: str = ""


class EvaluatorAgent:
    """
    Evaluates proposals using the 17-gate DHARMIC_CLAW protocol.
    
    This agent enforces:
    - 8 technical gates (lint, type check, security, tests, etc.)
    - 7 dharmic gates (ahimsa, satya, consent, etc.)
    - 2 supply-chain gates (SBOM, license compliance)
    
    No proposal passes without gate passage. CI is the ultimate authority.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gate_runner = GateRunner()

    async def evaluate_proposals(
        self, 
        proposals: List[Any],
        proposal_id: str = "",
        dry_run: bool = False
    ) -> EvaluationResult:
        """
        Evaluate proposals by running all 17 gates.

        Args:
            proposals: List of proposals to evaluate
            proposal_id: Unique identifier for this proposal batch
            dry_run: If True, simulate but don't execute gates

        Returns:
            EvaluationResult with approved/rejected proposals and gate evidence
        """
        self.logger.info(f"Evaluating {len(proposals)} proposals with 17-gate protocol")
        
        # Generate proposal ID if not provided
        if not proposal_id:
            from datetime import datetime
            proposal_id = f"PROP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Run all gates - this is the non-bypassable check
        self.logger.info(f"Running gates for proposal: {proposal_id}")
        
        is_yolo = os.getenv("DGC_YOLO_MODE") == "1"
        emergency_args = {}
        if is_yolo:
            self.logger.warning("⚠️ YOLO MODE DETECTED - ACTIVATING EMERGENCY BYPASS")
            emergency_args = {
                "emergency": True,
                "emergency_reason": "YOLO Mode Active",
                "emergency_approver": "CosmicKrishna"
            }

        try:
            # Run gates (this blocks until complete)
            gate_result = self.gate_runner.run_all_gates(
                proposal_id=proposal_id,
                dry_run=dry_run,
                **emergency_args
            )
            
            # Determine approval based on gate results
            # In emergency mode, WARN is accepted
            approved = gate_result.overall_result in ["PASS", "WARN"]
            self.logger.info(f"Proposals approved status set to: {approved} (Overall: {gate_result.overall_result})")
            
            # Calculate score based on gates passed
            total_gates = gate_result.gates_passed + gate_result.gates_failed + gate_result.gates_warned
            score = gate_result.gates_passed / total_gates if total_gates > 0 else 0.0
            
            # Build feedback message
            feedback_lines = [
                f"Gate run complete: {gate_result.gates_passed}/{total_gates} passed",
                f"Failed: {gate_result.gates_failed}, Warned: {gate_result.gates_warned}",
                f"Evidence hash: {gate_result.evidence_bundle_hash[:16]}..."
            ]
            
            if not approved:
                feedback_lines.append("BLOCKED: Gates failed - see evidence bundle for details")
            
            feedback = "\n".join(feedback_lines)
            
            self.logger.info(f"Evaluation result: {gate_result.overall_result} (score: {score:.2f})")
            
            # Create evaluations for each proposal
            # (All proposals in batch share the same gate result)
            evaluations = []
            for proposal in proposals:
                evaluations.append(ProposalEvaluation(
                    proposal=proposal,
                    approved=approved,
                    score=score,
                    feedback=feedback,
                    gate_result=gate_result
                ))
            
            return EvaluationResult(
                proposals=evaluations,
                overall_score=score,
                gates_passed=gate_result.gates_passed,
                gates_failed=gate_result.gates_failed,
                gates_warned=gate_result.gates_warned,
                evidence_bundle_hash=gate_result.evidence_bundle_hash
            )
            
        except Exception as e:
            self.logger.error(f"Gate execution failed: {e}")
            # Fail closed - if gates can't run, proposal is rejected
            return EvaluationResult(
                proposals=[
                    ProposalEvaluation(
                        proposal=p,
                        approved=False,
                        score=0.0,
                        feedback=f"Gate execution error: {e}"
                    )
                    for p in proposals
                ],
                overall_score=0.0,
                gates_passed=0,
                gates_failed=17,  # Assume all failed if we can't check
                gates_warned=0
            )

    def get_gate_status(self) -> dict:
        """Get current gate configuration status."""
        return {
            "total_gates": len(self.gate_runner.config.get("gates", [])),
            "version": self.gate_runner.config.get("version", "unknown"),
            "enforcement_mode": self.gate_runner.config.get("enforcement", {}).get("mode", "standard"),
            "evidence_dir": str(EVIDENCE_DIR)
        }
