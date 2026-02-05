"""
YOLO-Gate Weaver Integration for Swarm Orchestrator

This module integrates the YOLO-Gate Weaver into the DGC orchestration pipeline,
enabling intelligent routing between YOLO fast-iteration and full gate enforcement.

Usage:
    from yolo_gate_integration import YOLOGateIntegration
    
    integration = YOLOGateIntegration()
    result = await integration.execute_with_weaver(
        task="Build auth system",
        files=["src/auth.py"],
        target_area="src/auth"
    )
"""

import asyncio
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

# Add cosmic_krishna_coder to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "clawd" / "skills" / "cosmic-krishna-coder"))

from proactive_risk_detector import ProactiveRiskDetector, RiskLevel
from yolo_gate_weaver import YOLOGateWeaver, YOLOMode

# Gate runner integration
sys.path.insert(0, str(Path(__file__).parent))
from run_gates import GateRunner

@dataclass
class WeaverResult:
    """Result from YOLO-Gate Weaver execution."""
    status: str  # "committed", "escalated", "needs_revision", "failed"
    files_changed: List[str]
    risk_score: int
    yolo_confidence: float
    overseer_approved: bool
    gate_violations: List[str]
    evidence_bundle: Dict[str, Any]
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None

class YOLOGateIntegration:
    """
    Integrates YOLO-Gate Weaver into the DGC orchestration pipeline.
    
    This is the "hardwire" implementation that makes Cosmic Krishna Coder
    the enforcement layer for all live changes.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.detector = ProactiveRiskDetector()
        self.weaver = YOLOGateWeaver(mode=YOLOMode.WEAVED)
        self.gate_runner = GateRunner()
        self.logger = logging.getLogger(__name__)
        
    async def execute_with_weaver(
        self,
        task: str,
        files: List[str],
        target_area: Optional[str] = None,
        force_mode: Optional[str] = None
    ) -> WeaverResult:
        """
        Execute a task with YOLO-Gate Weaver routing.
        
        This is the main entry point that:
        1. Detects risk level
        2. Routes to appropriate pipeline (YOLO_NAVIGATE / YOLO_OVERSEER / FULL_GATES)
        3. Executes with oversight
        4. Returns structured result
        """
        self.logger.info(f"🔥 YOLO-Gate Weaver: Starting execution")
        self.logger.info(f"   Task: {task}")
        self.logger.info(f"   Files: {files}")
        
        # Phase 1: Risk Detection
        assessment = self.detector.analyze(files, task)
        self.logger.info(f"   Risk Level: {assessment.level.value.upper()}")
        self.logger.info(f"   Risk Score: {assessment.score.total}/100")
        
        # Phase 2: Route based on risk
        if assessment.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            # HIGH/CRITICAL: Full 22-gate enforcement
            return await self._execute_full_gates(task, files, assessment)
        
        elif assessment.level == RiskLevel.MEDIUM:
            # MEDIUM: YOLO_OVERSEER mode
            return await self._execute_yolo_overseer(task, files, assessment)
        
        else:
            # LOW/YOLO: YOLO_NAVIGATE mode
            return await self._execute_yolo_navigate(task, files, assessment)
    
    async def _execute_yolo_navigate(
        self,
        task: str,
        files: List[str],
        assessment: Any
    ) -> WeaverResult:
        """
        YOLO navigates gates in advisory mode.
        Fast iteration with awareness.
        """
        self.logger.info("🚀 Executing YOLO_NAVIGATE mode")
        
        # Run gates in advisory mode
        gate_result = self.gate_runner.run_all_gates(
            proposal_id=f"YOLO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            dry_run=self.dry_run
        )
        
        # YOLO makes navigation decisions
        yolo_confidence = assessment.confidence
        
        # Check if YOLO can self-approve
        if yolo_confidence > 0.85 and gate_result.overall_result == "PASS":
            self.logger.info("✅ YOLO self-approval granted")
            
            # Simulate code generation (in real implementation, call actual generator)
            files_changed = files  # Placeholder
            
            return WeaverResult(
                status="committed",
                files_changed=files_changed,
                risk_score=assessment.score.total,
                yolo_confidence=yolo_confidence,
                overseer_approved=True,  # Self-approved
                gate_violations=[],
                evidence_bundle={
                    "mode": "YOLO_NAVIGATE",
                    "gates_passed": gate_result.gates_passed,
                    "self_approved": True,
                    "timestamp": datetime.now().isoformat()
                },
                commit_hash="dry-run-hash" if self.dry_run else None
            )
        else:
            # Escalate to overseer
            self.logger.info("⏸️  YOLO confidence insufficient, escalating to overseer")
            return await self._execute_yolo_overseer(task, files, assessment)
    
    async def _execute_yolo_overseer(
        self,
        task: str,
        files: List[str],
        assessment: Any
    ) -> WeaverResult:
        """
        YOLO produces, overseer reviews.
        """
        self.logger.info("👁️  Executing YOLO_OVERSEER mode")
        
        # Run full gates
        gate_result = self.gate_runner.run_all_gates(
            proposal_id=f"OVERSEER-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            dry_run=self.dry_run
        )
        
        # Overseer review
        violations = []
        if gate_result.gates_failed > 0:
            violations.append(f"{gate_result.gates_failed} gates failed")
        
        if assessment.score.total > 60 and assessment.yolo_confidence < 0.7:
            violations.append("High risk with low YOLO confidence")
        
        # Determine outcome
        if not violations and gate_result.overall_result == "PASS":
            self.logger.info("✅ Overseer approval granted")
            return WeaverResult(
                status="committed",
                files_changed=files,
                risk_score=assessment.score.total,
                yolo_confidence=assessment.confidence,
                overseer_approved=True,
                gate_violations=[],
                evidence_bundle={
                    "mode": "YOLO_OVERSEER",
                    "gates_passed": gate_result.gates_passed,
                    "gates_failed": gate_result.gates_failed,
                    "overseer_approved": True,
                    "timestamp": datetime.now().isoformat()
                },
                commit_hash="dry-run-hash" if self.dry_run else None
            )
        
        elif violations:
            self.logger.warning("⚠️  Gate violations detected, escalating")
            return await self._execute_full_gates(task, files, assessment)
        
        else:
            self.logger.info("📝 Overseer requesting revision")
            return WeaverResult(
                status="needs_revision",
                files_changed=[],
                risk_score=assessment.score.total,
                yolo_confidence=assessment.confidence,
                overseer_approved=False,
                gate_violations=violations,
                evidence_bundle={
                    "mode": "YOLO_OVERSEER",
                    "gates_passed": gate_result.gates_passed,
                    "gates_failed": gate_result.gates_failed,
                    "overseer_approved": False,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _execute_full_gates(
        self,
        task: str,
        files: List[str],
        assessment: Any
    ) -> WeaverResult:
        """
        Full 22-gate enforcement.
        Human approval required.
        """
        self.logger.info("🔒 Executing FULL_GATES mode (22 gates)")
        self.logger.warning("   Human approval required for this change")
        
        # Run full gate suite
        gate_result = self.gate_runner.run_all_gates(
            proposal_id=f"FULL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            dry_run=True  # Always dry-run first for high-risk
        )
        
        # For high-risk, always require human approval
        # Return pending status
        return WeaverResult(
            status="pending_approval",  # Waiting for human
            files_changed=[],
            risk_score=assessment.score.total,
            yolo_confidence=0.0,  # YOLO not used
            overseer_approved=False,
            gate_violations=[],
            evidence_bundle={
                "mode": "FULL_GATES",
                "gates_passed": gate_result.gates_passed,
                "gates_failed": gate_result.gates_failed,
                "requires_human_approval": True,
                "risk_level": assessment.level.value,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_recommended_mode(self, task: str, files: List[str]) -> str:
        """
        Get the recommended execution mode for a task.
        """
        assessment = self.detector.analyze(files, task)
        
        if assessment.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return "FULL_GATES (Human approval required)"
        elif assessment.level == RiskLevel.MEDIUM:
            return "YOLO_OVERSEER (Review before commit)"
        else:
            return "YOLO_NAVIGATE (Fast iteration with awareness)"


# Integration hook for existing orchestrator
class OrchestratorWeaverMixin:
    """
    Mixin to add YOLO-Gate Weaver to SwarmOrchestrator.
    
    Usage:
        class EnhancedOrchestrator(SwarmOrchestrator, OrchestratorWeaverMixin):
            pass
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.yolo_integration = YOLOGateIntegration(
            dry_run=not os.environ.get("DGC_ALLOW_LIVE", "0") == "1"
        )
    
    async def execute_with_yolo_weaver(
        self,
        target_area: Optional[str] = None,
        task_description: Optional[str] = None
    ) -> Any:
        """
        Execute improvement cycle with YOLO-Gate Weaver.
        
        This replaces or enhances the standard execute_improvement_cycle.
        """
        # Detect files that would be modified
        files = self._get_target_files(target_area)
        
        # Use weaver for intelligent execution
        result = await self.yolo_integration.execute_with_weaver(
            task=task_description or f"Improve {target_area}",
            files=files,
            target_area=target_area
        )
        
        # Convert WeaverResult to WorkflowResult
        from .orchestrator import WorkflowResult, WorkflowState
        
        state_map = {
            "committed": WorkflowState.COMPLETED,
            "escalated": WorkflowState.FAILED,
            "needs_revision": WorkflowState.FAILED,
            "pending_approval": WorkflowState.EVALUATING,
            "failed": WorkflowState.FAILED
        }
        
        return WorkflowResult(
            state=state_map.get(result.status, WorkflowState.FAILED),
            files_changed=result.files_changed,
            tests_passed=(result.status == "committed"),
            error_message=result.error_message,
            metrics={
                "risk_score": result.risk_score,
                "yolo_confidence": result.yolo_confidence,
                "overseer_approved": result.overseer_approved,
                "gate_violations": result.gate_violations
            }
        )
    
    def _get_target_files(self, target_area: Optional[str]) -> List[str]:
        """Get list of files in target area."""
        if not target_area:
            return []
        
        target_path = Path(target_area)
        if target_path.is_file():
            return [str(target_path)]
        elif target_path.is_dir():
            return [str(f) for f in target_path.rglob("*.py")]
        return []


# CLI for testing
if __name__ == "__main__":
    import sys
    
    async def demo():
        integration = YOLOGateIntegration(dry_run=True)
        
        demo_tasks = [
            ("Learn asyncio basics", ["examples/async_demo.py"]),
            ("Fix typo in README", ["README.md"]),
            ("Build authentication system", ["src/auth/login.py", "src/auth/jwt.py"]),
            ("Payment gateway integration", ["src/payments/stripe.py"]),
        ]
        
        print("🔥 YOLO-Gate Weaver Integration Demo")
        print("=" * 60)
        
        for task, files in demo_tasks:
            print(f"\n📋 Task: {task}")
            print(f"   Files: {', '.join(files)}")
            
            # Get recommended mode
            mode = integration.get_recommended_mode(task, files)
            print(f"   Recommended: {mode}")
            
            # Simulate execution
            result = await integration.execute_with_weaver(task, files)
            print(f"   Result: {result.status}")
            print(f"   Risk Score: {result.risk_score}/100")
    
    asyncio.run(demo())
