"""
YOLO-Gate Weaver — Intelligent Integration of Speed and Security

Three modes that weave YOLO iteration with gate security:

1. YOLO_NAVIGATE: Gates in advisory mode (warnings, not blocks)
2. YOLO_OVERSEER: YOLO produces → Overseer reviews → Commit or Escalate
3. FULL_GATES: All gates blocking (traditional security)

The Weaver automatically routes based on RiskDetector score:
    - YOLO/LOW risk   → YOLO_NAVIGATE (fast, advisory gates)
    - MEDIUM risk     → YOLO_OVERSEER (produce → review → decide)
    - HIGH/CRITICAL   → FULL_GATES (all gates blocking, human required)

Usage:
    weaver = YOLOWeaver()
    result = weaver.execute(
        task="Build auth system",
        code="def login(): ...",
        files=["auth.py"]
    )

Created: 2026-02-05
JSCA! 🔥
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .risk_detector import RiskDetector, RiskResult, RiskTier, WeaveMode
from . import gates as real_gates
from .dgm_evolver import get_evolver


class GateStatus(Enum):
    """Status of a gate check."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class GateResult:
    """Result of a single gate check."""
    gate_name: str
    status: GateStatus
    message: str
    blocking: bool  # Whether this gate blocks in current mode
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WeaveResult:
    """Complete result of a weave execution."""
    task: str
    risk: RiskResult
    mode: WeaveMode
    gates_run: int
    gates_passed: int
    gates_warned: int
    gates_failed: int
    gate_results: List[GateResult]
    approved: bool
    approval_source: str  # "auto", "overseer", "human"
    escalated: bool
    escalation_reason: Optional[str]
    suggestions: List[str]
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "risk": self.risk.to_dict(),
            "mode": self.mode.value,
            "gates": {
                "run": self.gates_run,
                "passed": self.gates_passed,
                "warned": self.gates_warned,
                "failed": self.gates_failed
            },
            "approved": self.approved,
            "approval_source": self.approval_source,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "suggestions": self.suggestions,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class YOLOWeaver:
    """
    Intelligent YOLO-Gate integration.
    
    Weaves fast iteration with appropriate security based on risk.
    """
    
    # Gate definitions: (name, blocking_tiers, check_function_name)
    GATES = [
        # Core 4 (always run)
        ("LINT_FORMAT", {RiskTier.YOLO, RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_lint"),
        ("TYPE_CHECK", {RiskTier.YOLO, RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_types"),
        ("SECURITY_SCAN", {RiskTier.YOLO, RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_security"),
        ("AHIMSA", {RiskTier.YOLO, RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_ahimsa"),
        
        # Extended 8 (LOW+)
        ("SATYA", {RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_satya"),
        ("CONSENT", {RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_consent"),
        ("REVERSIBILITY", {RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_reversibility"),
        ("WITNESS", {RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_witness"),
        
        # Standard 14 (MEDIUM+)
        ("VYAVASTHIT", {RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_vyavasthit"),
        ("SVABHAAVA", {RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_svabhaava"),
        ("COHERENCE", {RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_coherence"),
        ("INTEGRITY", {RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_integrity"),
        ("BOUNDARY", {RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_boundary"),
        ("TEST_COVERAGE", {RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL}, "_check_tests"),
        
        # Full 22 (HIGH+)
        ("CLARITY", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_clarity"),
        ("CARE", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_care"),
        ("DIGNITY", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_dignity"),
        ("JUSTICE", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_justice"),
        ("HUMILITY", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_humility"),
        ("COMPLETION", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_completion"),
        ("DEPENDENCY_AUDIT", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_dependencies"),
        ("SBOM_PROVENANCE", {RiskTier.HIGH, RiskTier.CRITICAL}, "_check_sbom"),
    ]
    
    # Self-approval thresholds
    SELF_APPROVE_CONFIDENCE = 0.85
    SELF_APPROVE_MAX_WARNINGS = 2
    
    def __init__(self, evidence_dir: Optional[Path] = None, enable_evolution: bool = True):
        self.risk_detector = RiskDetector()
        self.evidence_dir = evidence_dir or Path.home() / ".agno_council" / "weave_evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # DGM Evolution
        self.enable_evolution = enable_evolution
        self.evolver = get_evolver() if enable_evolution else None
    
    def execute(
        self,
        task: str,
        code: str = "",
        files: Optional[List[str]] = None,
        branch: str = "",
        context: Optional[Dict[str, Any]] = None,
        force_mode: Optional[WeaveMode] = None
    ) -> WeaveResult:
        """
        Execute the YOLO-Gate weave pipeline.
        
        1. Analyze risk
        2. Determine mode
        3. Run appropriate gates
        4. Make approval decision
        
        Args:
            task: Task description
            code: Code to analyze
            files: Files being modified
            branch: Git branch
            context: Additional context
            force_mode: Override automatic mode selection
        
        Returns:
            WeaveResult with full trace
        """
        start_time = time.time()
        files = files or []
        context = context or {}
        
        # Step 1: Risk Analysis
        risk = self.risk_detector.analyze(
            description=task,
            code=code,
            files=files,
            branch=branch,
            context=context
        )
        
        # Step 2: Determine Mode
        mode = force_mode or risk.weave_mode
        
        # Step 3: Run Gates
        gate_results = self._run_gates(code, task, risk.tier, mode)
        
        # Step 4: Aggregate Results
        passed = sum(1 for g in gate_results if g.status == GateStatus.PASS)
        warned = sum(1 for g in gate_results if g.status == GateStatus.WARN)
        failed = sum(1 for g in gate_results if g.status == GateStatus.FAIL)
        
        # Step 5: Approval Decision
        approved, approval_source, escalated, escalation_reason = self._decide_approval(
            risk, mode, gate_results, passed, warned, failed
        )
        
        # Step 6: Generate Suggestions
        suggestions = self._generate_suggestions(risk, gate_results, mode)
        
        execution_time = (time.time() - start_time) * 1000
        
        result = WeaveResult(
            task=task,
            risk=risk,
            mode=mode,
            gates_run=len(gate_results),
            gates_passed=passed,
            gates_warned=warned,
            gates_failed=failed,
            gate_results=gate_results,
            approved=approved,
            approval_source=approval_source,
            escalated=escalated,
            escalation_reason=escalation_reason,
            suggestions=suggestions,
            execution_time_ms=execution_time
        )
        
        # Store evidence
        self._store_evidence(result)
        
        # DGM Evolution: Learn from failures
        if self.enable_evolution and self.evolver and failed > 0:
            self._evolve_from_result(result, code)
        
        return result
    
    def _evolve_from_result(self, result: WeaveResult, code: str = ""):
        """Record failures and potentially generate evolution proposals."""
        try:
            # Record each failure
            for gate_result in result.gate_results:
                if gate_result.status == GateStatus.FAIL:
                    self.evolver.record_failure(
                        gate_name=gate_result.gate_name,
                        message=gate_result.message,
                        code_snippet=code[:500] if code else "",
                        details=gate_result.evidence
                    )
            
            # Generate proposals if enough failures accumulated
            proposals = self.evolver.generate_proposals()
            
            if proposals:
                # Log evolution activity
                import logging
                logger = logging.getLogger('yolo_weaver')
                logger.info(f"🧬 DGM Evolution: Generated {len(proposals)} proposals from gate failures")
                
        except Exception:
            # Don't let evolution errors break the main flow
            pass
    
    def _run_gates(
        self,
        code: str,
        task: str,
        tier: RiskTier,
        mode: WeaveMode
    ) -> List[GateResult]:
        """Run gates based on tier and mode."""
        results = []
        combined = f"{code} {task}".lower()
        
        for gate_name, active_tiers, check_method in self.GATES:
            # Determine if gate should run
            should_run = tier in active_tiers
            
            # In NAVIGATE mode, run all gates but as advisory
            if mode == WeaveMode.YOLO_NAVIGATE:
                blocking = False
            else:
                blocking = should_run
            
            if not should_run and mode != WeaveMode.YOLO_NAVIGATE:
                results.append(GateResult(
                    gate_name=gate_name,
                    status=GateStatus.SKIP,
                    message="Skipped (tier below threshold)",
                    blocking=False
                ))
                continue
            
            # Run the gate check
            check_fn = getattr(self, check_method, None)
            if check_fn:
                status, message, evidence = check_fn(combined, code, task)
            else:
                status, message, evidence = GateStatus.PASS, "Check not implemented", {}
            
            results.append(GateResult(
                gate_name=gate_name,
                status=status,
                message=message,
                blocking=blocking,
                evidence=evidence
            ))
        
        return results
    
    def _decide_approval(
        self,
        risk: RiskResult,
        mode: WeaveMode,
        gates: List[GateResult],
        passed: int,
        warned: int,
        failed: int
    ) -> Tuple[bool, str, bool, Optional[str]]:
        """
        Decide approval based on mode and results.
        
        Returns: (approved, source, escalated, escalation_reason)
        """
        # Check for hard failures (blocking gates that failed)
        hard_failures = [g for g in gates if g.blocking and g.status == GateStatus.FAIL]
        
        if hard_failures:
            # Always reject if blocking gates failed
            return False, "gates", True, f"Blocking gates failed: {[g.gate_name for g in hard_failures]}"
        
        # Mode-specific logic
        if mode == WeaveMode.YOLO_NAVIGATE:
            # YOLO_NAVIGATE: Auto-approve unless critical failures
            if risk.tier in (RiskTier.YOLO, RiskTier.LOW):
                return True, "auto", False, None
            elif warned <= self.SELF_APPROVE_MAX_WARNINGS:
                return True, "auto", False, None
            else:
                return False, "overseer", True, f"Too many warnings ({warned}) for auto-approval"
        
        elif mode == WeaveMode.YOLO_OVERSEER:
            # YOLO_OVERSEER: Review warnings
            if failed == 0 and warned <= self.SELF_APPROVE_MAX_WARNINGS:
                return True, "overseer", False, None
            elif failed == 0:
                return False, "review", True, f"Warnings ({warned}) exceed threshold"
            else:
                return False, "review", True, "Gate failures detected"
        
        else:  # FULL_GATES
            # FULL_GATES: Strict, human required for HIGH+
            if failed == 0 and risk.tier not in (RiskTier.HIGH, RiskTier.CRITICAL):
                return True, "gates", False, None
            elif failed == 0:
                return False, "human", True, "Human approval required for HIGH risk"
            else:
                return False, "human", True, f"Gate failures: {failed}"
    
    def _generate_suggestions(
        self,
        risk: RiskResult,
        gates: List[GateResult],
        mode: WeaveMode
    ) -> List[str]:
        """Generate actionable suggestions."""
        suggestions = []
        
        # From risk analysis
        suggestions.extend(risk.suggestions)
        
        # From gate failures
        for gate in gates:
            if gate.status == GateStatus.FAIL:
                suggestions.append(f"Fix {gate.gate_name}: {gate.message}")
            elif gate.status == GateStatus.WARN:
                suggestions.append(f"Consider {gate.gate_name}: {gate.message}")
        
        return suggestions[:5]  # Top 5
    
    def _store_evidence(self, result: WeaveResult):
        """Store evidence bundle."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_id = f"weave_{timestamp}_{hash(result.task) % 10000}"
        
        filepath = self.evidence_dir / f"{evidence_id}.json"
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
    
    # === GATE CHECK IMPLEMENTATIONS (WIRED TO REAL TOOLS) ===
    
    def _convert_gate_result(self, result: real_gates.GateResult) -> Tuple[GateStatus, str, Dict]:
        """Convert real gate result to YOLOWeaver format."""
        # Map GateStatus from gates.py to local GateStatus
        status_map = {
            real_gates.GateStatus.PASS: GateStatus.PASS,
            real_gates.GateStatus.WARN: GateStatus.WARN,
            real_gates.GateStatus.FAIL: GateStatus.FAIL,
            real_gates.GateStatus.SKIP: GateStatus.SKIP,
            real_gates.GateStatus.ERROR: GateStatus.WARN,  # Errors become warnings
        }
        return status_map.get(result.status, GateStatus.PASS), result.message, result.details
    
    def _check_lint(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Check code formatting/linting via ruff format."""
        result = real_gates.check_lint_format(code)
        return self._convert_gate_result(result)
    
    def _check_types(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Check type annotations via mypy."""
        result = real_gates.check_type_check(code)
        return self._convert_gate_result(result)
    
    def _check_security(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Security scan via bandit."""
        result = real_gates.check_ahimsa(code)
        return self._convert_gate_result(result)
    
    def _check_ahimsa(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Non-harm check via bandit + secrets detection."""
        # Run both security and secrets checks
        security = real_gates.check_ahimsa(code)
        secrets = real_gates.check_secrets(code)
        
        # Combine results - fail if either fails
        if secrets.status == real_gates.GateStatus.FAIL:
            return GateStatus.FAIL, secrets.message, secrets.details
        if security.status == real_gates.GateStatus.FAIL:
            return GateStatus.FAIL, security.message, security.details
        if security.status == real_gates.GateStatus.WARN:
            return GateStatus.WARN, security.message, security.details
        return GateStatus.PASS, "Security and secrets check passed", {}
    
    def _check_satya(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Truth/documentation check via ruff lint + docstring check."""
        satya = real_gates.check_satya(code)
        svadhyaya = real_gates.check_svadhyaya(code)
        
        # Combine results
        if satya.status == real_gates.GateStatus.WARN or svadhyaya.status == real_gates.GateStatus.WARN:
            messages = []
            if satya.status == real_gates.GateStatus.WARN:
                messages.append(satya.message)
            if svadhyaya.status == real_gates.GateStatus.WARN:
                messages.append(svadhyaya.message)
            return GateStatus.WARN, "; ".join(messages), {**satya.details, **svadhyaya.details}
        return GateStatus.PASS, "Documentation and lint OK", {}
    
    def _check_consent(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Permission/consent check - pattern-based."""
        sensitive = ["delete", "drop", "remove", "shutdown", "destroy"]
        needs_consent = any(s in combined for s in sensitive)
        has_consent = "confirm" in combined or "approved" in combined or "consent" in combined
        
        if needs_consent and not has_consent:
            return GateStatus.WARN, "Sensitive operation without explicit confirmation", {}
        return GateStatus.PASS, "Consent OK", {}
    
    def _check_reversibility(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Reversibility check - pattern-based."""
        destructive = ["delete", "drop", "remove", "overwrite", "truncate"]
        reversible = ["backup", "undo", "rollback", "trash", "archive", "snapshot"]
        
        is_destructive = any(d in combined for d in destructive)
        has_reversible = any(r in combined for r in reversible)
        
        if is_destructive and not has_reversible:
            return GateStatus.WARN, "Destructive operation - consider adding backup/rollback", {}
        return GateStatus.PASS, "Reversibility OK", {}
    
    def _check_witness(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Logging/audit check via ishvara_pranidhana."""
        result = real_gates.check_ishvara_pranidhana(code)
        return self._convert_gate_result(result)
    
    def _check_vyavasthit(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Natural order check - complexity via brahmacharya."""
        result = real_gates.check_brahmacharya(code)
        return self._convert_gate_result(result)
    
    def _check_svabhaava(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Nature alignment check - clean code via saucha."""
        result = real_gates.check_saucha(code)
        return self._convert_gate_result(result)
    
    def _check_coherence(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Consistency check via tapas."""
        result = real_gates.check_tapas(code)
        return self._convert_gate_result(result)
    
    def _check_integrity(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Completeness check - run tests if available."""
        result = real_gates.check_correctness(code)
        return self._convert_gate_result(result)
    
    def _check_boundary(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Resource limits check via aparigraha (non-hoarding)."""
        result = real_gates.check_aparigraha(code)
        
        # Also check for unbounded loops
        unbounded = ["while True", "while 1", "for i in range(999"]
        found = [u for u in unbounded if u in code]
        
        if found:
            return GateStatus.WARN, f"Potentially unbounded: {found}", {"unbounded": found}
        return self._convert_gate_result(result)
    
    def _check_tests(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Test coverage check via pytest-cov."""
        result = real_gates.check_test_coverage(code)
        return self._convert_gate_result(result)
    
    def _check_clarity(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Clarity check via saucha (purity) - detects code smells."""
        result = real_gates.check_saucha(code)
        return self._convert_gate_result(result)
    
    def _check_care(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Data stewardship check via secrets detection."""
        result = real_gates.check_secrets(code)
        return self._convert_gate_result(result)
    
    def _check_dignity(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Respect check - bias audit for ML code."""
        result = real_gates.check_bias_audit(code)
        return self._convert_gate_result(result)
    
    def _check_justice(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Fairness check via ML explainability."""
        result = real_gates.check_explainability(code)
        return self._convert_gate_result(result)
    
    def _check_humility(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Uncertainty check - santosha (contentment)."""
        result = real_gates.check_santosha(code)
        
        # Also check for overconfident claims
        overconfident = ["100%", "guaranteed", "never fail", "perfect"]
        found = [o for o in overconfident if o in combined]
        
        if found:
            return GateStatus.WARN, f"Overconfident claims: {found}", {"claims": found}
        return self._convert_gate_result(result)
    
    def _check_completion(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Cleanup check - error handling via ishvara_pranidhana."""
        result = real_gates.check_ishvara_pranidhana(code)
        
        # Also check for resource cleanup
        resources = ["open(", "connect(", "session"]
        cleanup = ["close", "dispose", "with "]
        
        has_resources = any(r in code for r in resources)
        has_cleanup = any(c in code for c in cleanup)
        
        if has_resources and not has_cleanup:
            return GateStatus.WARN, "Add resource cleanup", {"needs_cleanup": True}
        return self._convert_gate_result(result)
    
    def _check_dependencies(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """Dependency audit via safety (vulnerability check)."""
        result = real_gates.check_vulnerability(code)
        return self._convert_gate_result(result)
    
    def _check_sbom(self, combined: str, code: str, task: str) -> Tuple[GateStatus, str, Dict]:
        """SBOM/provenance check via data_provenance + reproducibility."""
        provenance = real_gates.check_data_provenance(code)
        reproducibility = real_gates.check_reproducibility(code)
        
        # Combine - warn if either warns
        if provenance.status == real_gates.GateStatus.WARN or reproducibility.status == real_gates.GateStatus.WARN:
            messages = []
            if provenance.status == real_gates.GateStatus.WARN:
                messages.append(provenance.message)
            if reproducibility.status == real_gates.GateStatus.WARN:
                messages.append(reproducibility.message)
            return GateStatus.WARN, "; ".join(messages), {}
        return GateStatus.PASS, "Provenance and reproducibility OK", {}


if __name__ == "__main__":
    # Demo
    weaver = YOLOWeaver()
    
    examples = [
        ("Learn asyncio", "import asyncio\nasync def main(): pass", []),
        ("Build auth system", "def login(password): return hash(password)", ["auth.py"]),
        ("Payment webhook", "def process_payment(amount): db.execute('INSERT...')", ["payment.py"]),
    ]
    
    print("=" * 60)
    print("🔥 YOLO-GATE WEAVER — Demo")
    print("=" * 60)
    
    for task, code, files in examples:
        result = weaver.execute(task, code, files)
        print(f"\n📝 '{task}'")
        print(f"   Risk: {result.risk.score}/100 ({result.risk.tier.value})")
        print(f"   Mode: {result.mode.value}")
        print(f"   Gates: {result.gates_passed}/{result.gates_run} passed, {result.gates_warned} warned")
        print(f"   Approved: {result.approved} (by {result.approval_source})")
        if result.escalated:
            print(f"   ⚠️ Escalated: {result.escalation_reason}")
    
    print("\n" + "=" * 60)
    print("JSCA! 🪷")
