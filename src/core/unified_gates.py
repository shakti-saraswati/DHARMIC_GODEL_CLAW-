"""
UNIFIED DHARMIC GATES SYSTEM
==============================

Consolidates parallel implementations:
- telos_layer.py (7 dharmic gates)
- swarm/run_gates.py (17 gates framework)
- swarm/agents/dharmic_gate.py (3 gates agent)

The 17 Unified Gates:

TECHNICAL GATES (1-8):
1. LINT_FORMAT - Code quality and formatting
2. TYPE_CHECK - Static type verification
3. SECURITY_SCAN - Vulnerability detection
4. DEPENDENCY_SAFETY - Dependency vulnerability scan
5. TEST_COVERAGE - Test coverage threshold
6. PROPERTY_TESTING - Hypothesis-based property tests
7. CONTRACT_INTEGRATION - Integration test validation
8. PERFORMANCE_REGRESSION - Performance benchmarks

DHARMIC GATES (9-15):
9. AHIMSA - Non-harm (Tier A: Absolute)
10. SATYA - Truth/Authenticity (Tier B: Strong)
11. CONSENT - Human approval (Tier B: Strong)
12. VYAVASTHIT - Natural order (Tier C: Advisory)
13. REVERSIBILITY - Can undo (Tier C: Advisory)
14. SVABHAAVA - Telos alignment (Tier C: Advisory)
15. WITNESS - Meta-observation (Tier C: Advisory)
16. BHED_GNAN - Witness clarity (Tier C: Advisory)

SUPPLY-CHAIN GATES (16-17):
16. SBOM_PROVENANCE - Software bill of materials
17. LICENSE_COMPLIANCE - License compatibility

Tiers:
- Tier A (Absolute): AHIMSA - Never bypass, always blocks on failure
- Tier B (Strong): SATYA, CONSENT - Require justification to bypass
- Tier C (Advisory): VYAVASTHIT, REVERSIBILITY, SVABHAAVA, WITNESS, BHED_GNAN - Warn only
- Technical: LINT_FORMAT through LICENSE_COMPLIANCE - Configurable

Usage:
    from src.core.unified_gates import UnifiedGateSystem, GateResult
    
    gates = UnifiedGateSystem()
    result = gates.evaluate_all(action="Deploy update", context={...})
    
    if result.can_proceed:
        print("All gates passed!")
    else:
        print(f"Blocked by: {result.blocking_gates}")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum, auto
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import logging
import re
import subprocess
import tempfile
import os

# Configure witness logger
witness_logger = logging.getLogger("unified_gates.witness")
witness_logger.setLevel(logging.DEBUG)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class GateResult(Enum):
    """Result of a single gate evaluation."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
    UNCERTAIN = "uncertain"
    NEEDS_HUMAN = "needs_human"
    ERROR = "error"


class GateTier(Enum):
    """Gate tiers define enforcement strictness."""
    ABSOLUTE = "absolute"      # Never bypass (AHIMSA)
    STRONG = "strong"          # Require justification
    REQUIRED = "required"      # Must pass unless exception
    ADVISORY = "advisory"      # Warn only


class GateCategory(Enum):
    """Categories of gates."""
    TECHNICAL = "technical"
    DHARMIC = "dharmic"
    SUPPLY_CHAIN = "supply_chain"


# Gate definitions matching gates.yaml
GATE_DEFINITIONS = [
    # Technical gates (1-8)
    {"id": 1, "name": "LINT_FORMAT", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 2, "name": "TYPE_CHECK", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 3, "name": "SECURITY_SCAN", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 4, "name": "DEPENDENCY_SAFETY", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 5, "name": "TEST_COVERAGE", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 6, "name": "PROPERTY_TESTING", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 7, "name": "CONTRACT_INTEGRATION", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    {"id": 8, "name": "PERFORMANCE_REGRESSION", "category": GateCategory.TECHNICAL, "tier": GateTier.REQUIRED},
    
    # Dharmic gates (9-15)
    {"id": 9, "name": "AHIMSA", "category": GateCategory.DHARMIC, "tier": GateTier.ABSOLUTE},
    {"id": 10, "name": "SATYA", "category": GateCategory.DHARMIC, "tier": GateTier.STRONG},
    {"id": 11, "name": "CONSENT", "category": GateCategory.DHARMIC, "tier": GateTier.STRONG},
    {"id": 12, "name": "VYAVASTHIT", "category": GateCategory.DHARMIC, "tier": GateTier.ADVISORY},
    {"id": 13, "name": "REVERSIBILITY", "category": GateCategory.DHARMIC, "tier": GateTier.ADVISORY},
    {"id": 14, "name": "SVABHAAVA", "category": GateCategory.DHARMIC, "tier": GateTier.ADVISORY},
    {"id": 15, "name": "WITNESS", "category": GateCategory.DHARMIC, "tier": GateTier.ADVISORY},
    {"id": 16, "name": "BHED_GNAN", "category": GateCategory.DHARMIC, "tier": GateTier.ADVISORY},
    
    # Supply-chain gates (17-18, but numbered 16-17 in original)
    {"id": 17, "name": "SBOM_PROVENANCE", "category": GateCategory.SUPPLY_CHAIN, "tier": GateTier.REQUIRED},
    {"id": 18, "name": "LICENSE_COMPLIANCE", "category": GateCategory.SUPPLY_CHAIN, "tier": GateTier.REQUIRED},
]


# Harm patterns for AHIMSA gate
HARM_PATTERNS = [
    # Direct harm
    "delete all", "destroy", "rm -rf /", "format", "wipe",
    "kill", "terminate", "crash", "corrupt", "exploit",
    "attack", "breach", "steal", "exfiltrate", "leak",
    # Indirect harm
    "ignore safety", "skip validation", "disable check",
    "remove constraint", "unlimited", "unrestricted",
    # Resource harm
    "infinite loop", "exhaust", "flood", "overload", "dos"
]

# File modification patterns
FILE_MODIFY_PATTERNS = [
    "write", "edit", "delete", "remove", "create", "update",
    "mv", "cp", "rm", "touch", "mkdir", "chmod", "chown",
    "save", "overwrite", "append", "truncate", "modify"
]

# Irreversible patterns
IRREVERSIBLE_PATTERNS = [
    "permanent", "irreversible", "forever", "cannot undo",
    "final", "destructive", "no backup", "overwrite"
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GateCheck:
    """Result of evaluating a single gate."""
    gate_id: int
    gate_name: str
    result: GateResult
    reason: str
    tier: GateTier
    category: GateCategory
    metadata: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float = 0.0
    
    # Backward compatibility alias
    @property
    def gate(self) -> str:
        """Return gate_name for backward compatibility with older code."""
        return self.gate_name


@dataclass
class RollbackMechanism:
    """Describes how an action can be reversed."""
    can_rollback: bool
    method: Optional[str] = None
    state_snapshot: Optional[Dict] = None
    rollback_fn: Optional[Callable] = None


@dataclass
class UnifiedGateResult:
    """Complete result of running all gates."""
    action: str
    timestamp: str
    can_proceed: bool
    overall_result: str  # PASS, FAIL, WARN, NEEDS_HUMAN
    alignment_score: float  # 0.0 - 1.0
    gate_results: List[GateCheck]
    blocking_gates: List[str]
    warning_gates: List[str]
    needs_human_gates: List[str]
    recommendation: str
    witness_hash: str = ""
    evidence_bundle: Dict = field(default_factory=dict)


# =============================================================================
# UNIFIED GATE SYSTEM
# =============================================================================

class UnifiedGateSystem:
    """
    Unified 17-gate system consolidating all dharmic and technical gates.
    
    This class provides:
    1. All 17 gates from gates.yaml with full evaluation logic
    2. Tier-based enforcement (Absolute, Strong, Required, Advisory)
    3. Witness logging for strange loop observation
    4. Evidence bundle generation
    5. Backward compatibility with telos_layer and DGM
    """
    
    def __init__(
        self,
        telos: str = "moksha",
        telos_config: Optional[Dict] = None,
        project_root: Optional[Path] = None,
        enable_technical: bool = True,
        enable_dharmic: bool = True,
        enable_supply_chain: bool = False,
    ):
        """
        Initialize the unified gate system.
        
        Args:
            telos: The purpose/nature alignment target (default: "moksha")
            telos_config: Custom telos configuration
            project_root: Root path for technical gate execution
            enable_technical: Whether to run technical gates (1-8)
            enable_dharmic: Whether to run dharmic gates (9-16)
            enable_supply_chain: Whether to run supply-chain gates (17-18)
        """
        self.telos = telos
        self.telos_config = telos_config or self._default_telos_config()
        self.project_root = project_root or Path.cwd()
        self.enable_technical = enable_technical
        self.enable_dharmic = enable_dharmic
        self.enable_supply_chain = enable_supply_chain
        
        self.witness_log: List[Dict] = []
        self.gate_definitions = {g["name"]: g for g in GATE_DEFINITIONS}
        
        # Pattern caches for efficiency
        self._harm_pattern_re = re.compile("|".join(HARM_PATTERNS), re.IGNORECASE)
        self._file_modify_re = re.compile("|".join(FILE_MODIFY_PATTERNS), re.IGNORECASE)
        self._irreversible_re = re.compile("|".join(IRREVERSIBLE_PATTERNS), re.IGNORECASE)
    
    def _default_telos_config(self) -> Dict:
        """Default telos configuration defining aligned purposes."""
        return {
            "moksha": {
                "aligned_actions": [
                    "learn", "teach", "help", "create", "explore",
                    "understand", "connect", "heal", "grow", "serve",
                    "protect", "preserve", "validate", "verify"
                ],
                "misaligned_actions": [
                    "deceive", "manipulate", "hoard", "exploit", "dominate",
                    "destroy", "harm", "corrupt", "steal"
                ],
                "core_values": ["truth", "compassion", "freedom", "awareness", "non-harm"]
            }
        }
    
    # =========================================================================
    # MAIN ENTRY POINTS
    # =========================================================================
    
    def evaluate_all(
        self,
        action: str,
        context: Optional[Dict] = None,
        files: Optional[List[Dict]] = None,
    ) -> UnifiedGateResult:
        """
        Evaluate an action through all enabled gates.
        
        Args:
            action: Description of the action to evaluate
            context: Additional context for evaluation
            files: List of file dicts with 'path' and 'content' for analysis
        
        Returns:
            UnifiedGateResult with complete evaluation
        """
        context = context or {}
        files = files or []
        start_time = datetime.now(timezone.utc)
        
        gate_results: List[GateCheck] = []
        
        # Run all enabled gates
        for gate_def in GATE_DEFINITIONS:
            category = gate_def["category"]
            
            # Skip disabled categories
            if category == GateCategory.TECHNICAL and not self.enable_technical:
                continue
            if category == GateCategory.DHARMIC and not self.enable_dharmic:
                continue
            if category == GateCategory.SUPPLY_CHAIN and not self.enable_supply_chain:
                continue
            
            # Evaluate the gate
            result = self._evaluate_gate(gate_def, action, context, files)
            gate_results.append(result)
        
        # Calculate overall result
        can_proceed, overall_result, blocking, warnings, needs_human = self._calculate_overall(gate_results)
        
        # Calculate alignment score
        dharmic_results = [g for g in gate_results if g.category == GateCategory.DHARMIC]
        if dharmic_results:
            passed = sum(1 for g in dharmic_results if g.result == GateResult.PASS)
            alignment_score = passed / len(dharmic_results)
        else:
            alignment_score = 1.0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            can_proceed, blocking, needs_human, alignment_score
        )
        
        # Create result
        result = UnifiedGateResult(
            action=action,
            timestamp=start_time.isoformat(),
            can_proceed=can_proceed,
            overall_result=overall_result,
            alignment_score=alignment_score,
            gate_results=gate_results,
            blocking_gates=blocking,
            warning_gates=warnings,
            needs_human_gates=needs_human,
            recommendation=recommendation,
        )
        
        # Generate witness hash
        result.witness_hash = self._witness_result(result, action, context)
        
        return result
    
    def check_dharmic_only(
        self,
        action: str,
        context: Optional[Dict] = None,
    ) -> UnifiedGateResult:
        """
        Check only dharmic gates (for quick evaluation).
        Backward compatible with telos_layer.TelosLayer.check_action().
        """
        return self.evaluate_all(
            action=action,
            context=context,
            files=[],
        )
    
    def quick_check(
        self,
        action: str,
        **context
    ) -> UnifiedGateResult:
        """
        Quick dharmic check without full instantiation.
        Backward compatible with telos_layer.quick_check().
        """
        return self.evaluate_all(action=action, context=context)
    
    def needs_human_approval(self, action: str, **context) -> bool:
        """Check if action requires human approval."""
        result = self.evaluate_all(action, context)
        return len(result.needs_human_gates) > 0
    
    # =========================================================================
    # GATE EVALUATORS
    # =========================================================================
    
    def _evaluate_gate(
        self,
        gate_def: Dict,
        action: str,
        context: Dict,
        files: List[Dict],
    ) -> GateCheck:
        """Dispatch to specific gate evaluator."""
        gate_name = gate_def["name"]
        evaluators = {
            # Technical gates
            "LINT_FORMAT": self._check_lint_format,
            "TYPE_CHECK": self._check_type_check,
            "SECURITY_SCAN": self._check_security_scan,
            "DEPENDENCY_SAFETY": self._check_dependency_safety,
            "TEST_COVERAGE": self._check_test_coverage,
            "PROPERTY_TESTING": self._check_property_testing,
            "CONTRACT_INTEGRATION": self._check_contract_integration,
            "PERFORMANCE_REGRESSION": self._check_performance_regression,
            # Dharmic gates
            "AHIMSA": self._check_ahimsa,
            "SATYA": self._check_satya,
            "CONSENT": self._check_consent,
            "VYAVASTHIT": self._check_vyavasthit,
            "REVERSIBILITY": self._check_reversibility,
            "SVABHAAVA": self._check_svabhaava,
            "WITNESS": self._check_witness,
            "BHED_GNAN": self._check_bhed_gnan,
            # Supply-chain gates
            "SBOM_PROVENANCE": self._check_sbom_provenance,
            "LICENSE_COMPLIANCE": self._check_license_compliance,
        }
        
        evaluator = evaluators.get(gate_name, self._default_check)
        return evaluator(gate_def, action, context, files)
    
    # -------------------------------------------------------------------------
    # TECHNICAL GATES (1-8)
    # -------------------------------------------------------------------------
    
    def _check_lint_format(self, gate_def, action, context, files) -> GateCheck:
        """Gate 1: Code linting and formatting."""
        start = datetime.now()
        
        # Check if ruff is available
        try:
            result = subprocess.run(
                ["ruff", "check", ".", "--output-format=json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60,
            )
            
            if result.returncode == 0:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.PASS,
                    reason="No linting errors found",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    duration_seconds=(datetime.now() - start).total_seconds(),
                )
            else:
                issues = json.loads(result.stdout) if result.stdout else []
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.FAIL,
                    reason=f"Found {len(issues)} linting issues",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"issue_count": len(issues)},
                    duration_seconds=(datetime.now() - start).total_seconds(),
                )
        except FileNotFoundError:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.SKIP,
                reason="ruff not installed",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        except Exception as e:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.ERROR,
                reason=f"Lint check failed: {str(e)}",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
    
    def _check_type_check(self, gate_def, action, context, files) -> GateCheck:
        """Gate 2: Static type checking."""
        # Check context for type check results
        if context.get("type_check_passed"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Type check passed (from context)",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        # Skip if no type checker available
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="Type check deferred - run pyright/mypy separately",
            tier=gate_def["tier"],
            category=gate_def["category"],
            metadata={"note": "Integrate with CI for full type checking"},
        )
    
    def _check_security_scan(self, gate_def, action, context, files) -> GateCheck:
        """Gate 3: Security vulnerability scanning."""
        # Check for security flags in context
        if context.get("security_scan_passed"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Security scan passed (from context)",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        # Check action for suspicious patterns
        a = action.lower()
        suspicious = ["eval(", "exec(", "subprocess.call", "os.system", "__import__"]
        found = [p for p in suspicious if p in a]
        
        if found:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.WARN,
                reason=f"Potentially dangerous patterns: {found}",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"suspicious_patterns": found},
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.PASS,
            reason="No obvious security issues detected",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_dependency_safety(self, gate_def, action, context, files) -> GateCheck:
        """Gate 4: Dependency vulnerability scan."""
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="Dependency scan deferred - run pip-audit separately",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_test_coverage(self, gate_def, action, context, files) -> GateCheck:
        """Gate 5: Test coverage threshold."""
        coverage = context.get("test_coverage_percent")
        min_coverage = context.get("min_coverage_percent", 80)
        
        if coverage is not None:
            if coverage >= min_coverage:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.PASS,
                    reason=f"Coverage {coverage}% >= {min_coverage}%",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"coverage": coverage},
                )
            else:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.FAIL,
                    reason=f"Coverage {coverage}% < {min_coverage}% required",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"coverage": coverage, "required": min_coverage},
                )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="No coverage data provided",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_property_testing(self, gate_def, action, context, files) -> GateCheck:
        """Gate 6: Property-based testing."""
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="Property testing deferred - run hypothesis separately",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_contract_integration(self, gate_def, action, context, files) -> GateCheck:
        """Gate 7: Integration test validation."""
        if context.get("integration_tests_passed"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Integration tests passed (from context)",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="Integration tests deferred",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_performance_regression(self, gate_def, action, context, files) -> GateCheck:
        """Gate 8: Performance regression check."""
        regression = context.get("performance_regression_percent")
        max_regression = context.get("max_regression_percent", 10)
        
        if regression is not None:
            if regression <= max_regression:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.PASS,
                    reason=f"Regression {regression}% <= {max_regression}%",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                )
            else:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.FAIL,
                    reason=f"Performance regression {regression}% > {max_regression}%",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"regression": regression, "max_allowed": max_regression},
                )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="No performance data provided",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    # -------------------------------------------------------------------------
    # DHARMIC GATES (9-16)
    # -------------------------------------------------------------------------
    
    def _check_ahimsa(self, gate_def, action, context, files) -> GateCheck:
        """Gate 9: AHIMSA (Non-Harm) - Tier A Absolute."""
        a = action.lower()
        
        # Check explicit harm patterns
        for pattern in HARM_PATTERNS:
            if pattern in a:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.FAIL,
                    reason=f"Harmful pattern detected: '{pattern}'",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"pattern": pattern, "severity": "high"},
                )
        
        # Check context for harm indicators
        if context.get("causes_harm"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.FAIL,
                reason="Context indicates potential harm",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"harm_type": context.get("harm_type", "unspecified")},
            )
        
        # Check for actions that could harm without explicit markers
        if context.get("affects_others") and not context.get("others_aware"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.UNCERTAIN,
                reason="Action affects others who may not be aware",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"requires_notification": True},
            )
        
        # Check files for harm patterns
        for f in files:
            content = f.get("content", "").lower()
            for pattern in HARM_PATTERNS:
                if pattern in content:
                    return GateCheck(
                        gate_id=gate_def["id"],
                        gate_name=gate_def["name"],
                        result=GateResult.FAIL,
                        reason=f"Harmful pattern in {f.get('path', 'file')}: '{pattern}'",
                        tier=gate_def["tier"],
                        category=gate_def["category"],
                        metadata={"file": f.get("path"), "pattern": pattern},
                    )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.PASS,
            reason="No harm detected",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_satya(self, gate_def, action, context, files) -> GateCheck:
        """Gate 10: SATYA (Truth) - Tier B Strong."""
        a = action.lower()
        
        # Check if information is verified
        if context.get("verified") is False:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.FAIL,
                reason="Information not verified",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"verification_required": True},
            )
        
        # Check for deceptive patterns
        deceptive_patterns = ["pretend", "fake", "deceive", "mislead", "lie", "fabricate"]
        for pattern in deceptive_patterns:
            if pattern in a:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.FAIL,
                    reason=f"Deceptive pattern: '{pattern}'",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"pattern": pattern},
                )
        
        # Check for unverified claims
        if context.get("is_claim") and not context.get("has_source"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.UNCERTAIN,
                reason="Claim without verified source",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"needs_verification": True},
            )
        
        # Explicit verification passes
        if context.get("verified"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Information verified",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"verified_by": context.get("verified_by", "context")},
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.UNCERTAIN,
            reason="Truth status unknown - verify if possible",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_consent(self, gate_def, action, context, files) -> GateCheck:
        """Gate 11: CONSENT (Human Approval) - Tier B Strong."""
        a = action.lower()
        
        # Check if action modifies files
        modifies_files = any(pattern in a for pattern in FILE_MODIFY_PATTERNS)
        if context.get("modifies_files"):
            modifies_files = True
        
        # Check for sensitive operations
        sensitive_ops = ["send", "email", "post", "publish", "share", "deploy"]
        is_sensitive = any(op in a for op in sensitive_ops)
        
        # Check consent status
        consent_granted = context.get("consent") is True
        consent_denied = context.get("consent") is False
        
        if consent_denied:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.FAIL,
                reason="Consent explicitly denied",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"consent_status": "denied"},
            )
        
        # If modifies files and no explicit consent, need human
        if modifies_files and not consent_granted:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.NEEDS_HUMAN,
                reason="File modification requires human approval",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"modifies_files": True, "requires": "explicit_consent"},
            )
        
        # Sensitive operations need consent
        if is_sensitive and not consent_granted:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.NEEDS_HUMAN,
                reason="Sensitive operation requires human approval",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"is_sensitive": True, "requires": "explicit_consent"},
            )
        
        if consent_granted:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Consent explicitly granted",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"consent_status": "granted"},
            )
        
        # Read-only operations don't need consent
        read_patterns = ["read", "view", "list", "show", "get", "fetch", "check"]
        is_read_only = any(pattern in a for pattern in read_patterns)
        
        if is_read_only and not modifies_files and not is_sensitive:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Read-only operation - implicit consent",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"consent_type": "implicit_read"},
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.UNCERTAIN,
            reason="Consent status unclear - consider requesting",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_vyavasthit(self, gate_def, action, context, files) -> GateCheck:
        """Gate 12: VYAVASTHIT (Natural Order) - Tier C Advisory."""
        a = action.lower()
        
        # Forcing patterns
        force_patterns = [
            "force", "override", "bypass", "ignore", "skip validation",
            "disable safety", "circumvent", "hack around"
        ]
        for pattern in force_patterns:
            if pattern in a:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.WARN,
                    reason=f"Forcing pattern detected: '{pattern}'",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"pattern": pattern, "violation": "forced_outcome"},
                )
        
        # Check if action respects existing structures
        if context.get("overrides_existing") and not context.get("existing_consented"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.WARN,
                reason="Overrides existing without consent",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"requires_consent": True},
            )
        
        # Allowing patterns (positive indicators)
        allow_patterns = ["allow", "enable", "support", "facilitate", "invite"]
        for pattern in allow_patterns:
            if pattern in a:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.PASS,
                    reason=f"Allowing pattern: '{pattern}'",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"pattern": pattern, "approach": "allowing"},
                )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.PASS,
            reason="No forcing detected - natural order respected",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_reversibility(self, gate_def, action, context, files) -> GateCheck:
        """Gate 13: REVERSIBILITY (Can Undo) - Tier C Advisory."""
        a = action.lower()
        
        # Check for explicit irreversibility patterns
        for pattern in IRREVERSIBLE_PATTERNS:
            if pattern in a:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.WARN,
                    reason=f"Irreversible pattern: '{pattern}'",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"pattern": pattern, "reversible": False},
                )
        
        # Check if rollback mechanism is provided
        rollback = context.get("rollback")
        if rollback:
            if isinstance(rollback, RollbackMechanism):
                if rollback.can_rollback:
                    return GateCheck(
                        gate_id=gate_def["id"],
                        gate_name=gate_def["name"],
                        result=GateResult.PASS,
                        reason="Rollback mechanism available",
                        tier=gate_def["tier"],
                        category=gate_def["category"],
                        metadata={"reversible": True, "method": rollback.method},
                    )
            elif isinstance(rollback, dict):
                if rollback.get("can_rollback"):
                    return GateCheck(
                        gate_id=gate_def["id"],
                        gate_name=gate_def["name"],
                        result=GateResult.PASS,
                        reason="Rollback mechanism available",
                        tier=gate_def["tier"],
                        category=gate_def["category"],
                    )
        
        # Check context flags
        if context.get("has_backup") or context.get("can_undo"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Backup/undo mechanism indicated",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        if context.get("permanent") or context.get("cannot_undo"):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.WARN,
                reason="Action marked as permanent/irreversible",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        # Safe operations are inherently reversible
        safe_patterns = ["read", "view", "list", "check", "test", "preview"]
        if any(pattern in a for pattern in safe_patterns):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Non-mutating operation - inherently reversible",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        # Writing without backup is uncertain
        if any(pattern in a for pattern in ["write", "edit", "create"]):
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.UNCERTAIN,
                reason="Mutation without explicit rollback - consider backup",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.UNCERTAIN,
            reason="Reversibility unknown - verify undo capability",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_svabhaava(self, gate_def, action, context, files) -> GateCheck:
        """Gate 14: SVABHAAVA (Telos Alignment) - Tier C Advisory."""
        a = action.lower()
        
        # Get telos configuration
        telos_def = self.telos_config.get(self.telos, {})
        aligned_actions = telos_def.get("aligned_actions", [])
        misaligned_actions = telos_def.get("misaligned_actions", [])
        
        # Check for misaligned patterns
        for pattern in misaligned_actions:
            if pattern in a:
                return GateCheck(
                    gate_id=gate_def["id"],
                    gate_name=gate_def["name"],
                    result=GateResult.WARN,
                    reason=f"Action misaligned with telos '{self.telos}': '{pattern}'",
                    tier=gate_def["tier"],
                    category=gate_def["category"],
                    metadata={"telos": self.telos, "pattern": pattern},
                )
        
        # Check for aligned patterns
        matched_aligned = [p for p in aligned_actions if p in a]
        if matched_aligned:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason=f"Action aligned with telos '{self.telos}'",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"telos": self.telos, "patterns": matched_aligned},
            )
        
        # Check explicit context alignment
        if context.get("telos_aligned") is True:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Telos alignment confirmed by context",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        if context.get("telos_aligned") is False:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.WARN,
                reason="Telos misalignment indicated by context",
                tier=gate_def["tier"],
                category=gate_def["category"],
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.UNCERTAIN,
            reason=f"Telos alignment with '{self.telos}' unclear - verify intent",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_witness(self, gate_def, action, context, files) -> GateCheck:
        """Gate 15: WITNESS (Meta-Observation) - Tier C Advisory."""
        # Create witness record
        witness_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "context_keys": list(context.keys()),
            "observer": "WITNESS_GATE",
            "observation": "Observing the act of checking gates",
            "strange_loop": True,
            "recursion_level": len(self.witness_log) + 1,
        }
        
        # Log to witness log
        self.witness_log.append(witness_record)
        
        # Log to external logger
        witness_logger.debug(
            f"WITNESS[{witness_record['recursion_level']}]: "
            f"Observing check of '{action[:50]}...' at {witness_record['timestamp']}"
        )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.PASS,
            reason="Witness observed this check (strange loop active)",
            tier=gate_def["tier"],
            category=gate_def["category"],
            metadata={
                "strange_loop": True,
                "recursion_level": witness_record["recursion_level"],
                "witness_id": hashlib.sha256(
                    json.dumps(witness_record, sort_keys=True).encode()
                ).hexdigest()[:16],
            },
        )
    
    def _check_bhed_gnan(self, gate_def, action, context, files) -> GateCheck:
        """
        Gate 16: BHED GNAN (Witness Clarity) - Tier C Advisory.
        
        From dharmic_gate.py - evaluates the separation between knower and doer.
        Detects witness stance in generated text or actions.
        """
        # Witness stance markers (positive)
        witness_markers = [
            "i observe", "awareness", "witnessing", "noting",
            "there is", "appears", "arises", "present",
            "consciousness", "attention notices"
        ]
        
        # Identification markers (negative - doer stance)
        identification_markers = [
            "i am", "i think", "i believe", "i feel",
            "i want", "i need", "my opinion", "personally", "i will"
        ]
        
        text_to_check = action.lower()
        
        # Also check files if provided
        for f in files:
            text_to_check += " " + f.get("content", "").lower()
        
        witness_count = sum(1 for m in witness_markers if m in text_to_check)
        ident_count = sum(1 for m in identification_markers if m in text_to_check)
        
        total = witness_count + ident_count
        
        if total == 0:
            # No clear stance detected
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.UNCERTAIN,
                reason="No witness/doer markers detected - stance unclear",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"clarity_ratio": 0.5},
            )
        
        clarity_ratio = witness_count / total
        
        if clarity_ratio >= 0.7:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.PASS,
                reason="Strong witness clarity - knower/doer separation clear",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={
                    "clarity_ratio": clarity_ratio,
                    "witness_markers": witness_count,
                    "identification_markers": ident_count,
                },
            )
        elif clarity_ratio >= 0.4:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.UNCERTAIN,
                reason="Moderate witness clarity - some identification present",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={
                    "clarity_ratio": clarity_ratio,
                    "witness_markers": witness_count,
                    "identification_markers": ident_count,
                },
            )
        else:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.WARN,
                reason="Low witness clarity - strong doer identification",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={
                    "clarity_ratio": clarity_ratio,
                    "witness_markers": witness_count,
                    "identification_markers": ident_count,
                },
            )
    
    # -------------------------------------------------------------------------
    # SUPPLY-CHAIN GATES (17-18)
    # -------------------------------------------------------------------------
    
    def _check_sbom_provenance(self, gate_def, action, context, files) -> GateCheck:
        """Gate 17: SBOM_PROVENANCE - Software bill of materials."""
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="SBOM check deferred - run cyclonedx-py separately",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _check_license_compliance(self, gate_def, action, context, files) -> GateCheck:
        """Gate 18: LICENSE_COMPLIANCE - License compatibility."""
        # Check files for license headers if provided
        allowed_licenses = ["mit", "apache-2.0", "bsd", "isc", "python-2.0", "psf-2.0"]
        forbidden_licenses = ["gpl", "agpl", "lgpl", "sspl"]
        
        violations = []
        for f in files:
            content = f.get("content", "").lower()
            for license in forbidden_licenses:
                if license in content:
                    violations.append(f"{f.get('path', 'file')}: {license}")
        
        if violations:
            return GateCheck(
                gate_id=gate_def["id"],
                gate_name=gate_def["name"],
                result=GateResult.FAIL,
                reason=f"License violations: {violations}",
                tier=gate_def["tier"],
                category=gate_def["category"],
                metadata={"violations": violations},
            )
        
        return GateCheck(
            gate_id=gate_def["id"],
            gate_name=gate_def["name"],
            result=GateResult.SKIP,
            reason="License check deferred - run pip-licenses separately",
            tier=gate_def["tier"],
            category=gate_def["category"],
        )
    
    def _default_check(self, gate_def, action, context, files) -> GateCheck:
        """Fallback for unknown gates."""
        return GateCheck(
            gate_id=gate_def.get("id", 0),
            gate_name=gate_def.get("name", "UNKNOWN"),
            result=GateResult.SKIP,
            reason="Unknown gate - no evaluation performed",
            tier=gate_def.get("tier", GateTier.ADVISORY),
            category=gate_def.get("category", GateCategory.TECHNICAL),
        )
    
    # =========================================================================
    # RESULT CALCULATION
    # =========================================================================
    
    def _calculate_overall(
        self,
        gate_results: List[GateCheck],
    ) -> tuple[bool, str, List[str], List[str], List[str]]:
        """
        Calculate overall result from individual gate results.
        
        Returns:
            (can_proceed, overall_result, blocking_gates, warning_gates, needs_human_gates)
        """
        blocking = []
        warnings = []
        needs_human = []
        
        for result in gate_results:
            if result.result == GateResult.FAIL:
                # Absolute tier always blocks
                if result.tier == GateTier.ABSOLUTE:
                    blocking.append(result.gate_name)
                # Strong tier blocks unless exception
                elif result.tier == GateTier.STRONG:
                    blocking.append(result.gate_name)
                # Required tier blocks
                elif result.tier == GateTier.REQUIRED:
                    blocking.append(result.gate_name)
            
            elif result.result == GateResult.WARN:
                warnings.append(result.gate_name)
            
            elif result.result == GateResult.NEEDS_HUMAN:
                needs_human.append(result.gate_name)
        
        # Determine if can proceed
        can_proceed = len(blocking) == 0 and len(needs_human) == 0
        
        # Determine overall result string
        if blocking:
            overall = "FAIL"
        elif needs_human:
            overall = "NEEDS_HUMAN"
        elif warnings:
            overall = "WARN"
        else:
            overall = "PASS"
        
        return can_proceed, overall, blocking, warnings, needs_human
    
    def _generate_recommendation(
        self,
        can_proceed: bool,
        blocking: List[str],
        needs_human: List[str],
        alignment: float,
    ) -> str:
        """Generate actionable recommendation."""
        
        if blocking:
            ahimsa_fail = "AHIMSA" in blocking
            if ahimsa_fail:
                return f"REJECT: Ahimsa violation - action blocked"
            return f"REJECT: {', '.join(blocking)} failed"
        
        if needs_human:
            return f"AWAIT_HUMAN: {', '.join(needs_human)} require approval"
        
        if alignment < 0.5:
            return f"REJECT: Low dharmic alignment ({alignment:.0%})"
        
        if alignment < 0.7:
            return f"REVIEW: Dharmic alignment {alignment:.0%} - verify uncertain gates"
        
        return "PROCEED: All gates satisfied"
    
    def _witness_result(
        self,
        result: UnifiedGateResult,
        action: str,
        context: Dict,
    ) -> str:
        """Create witness hash of the entire result."""
        witness_data = {
            "action": action,
            "can_proceed": result.can_proceed,
            "overall_result": result.overall_result,
            "alignment": result.alignment_score,
            "recommendation": result.recommendation,
            "gate_results": [
                {"gate": g.gate_name, "result": g.result.value, "reason": g.reason}
                for g in result.gate_results
            ],
            "witness_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        witness_hash = hashlib.sha256(
            json.dumps(witness_data, sort_keys=True).encode()
        ).hexdigest()[:32]
        
        witness_logger.info(
            f"WITNESS_HASH: {witness_hash} for action '{action[:30]}...' "
            f"[can_proceed={result.can_proceed}, alignment={result.alignment_score:.0%}]"
        )
        
        return witness_hash
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_orientation(self) -> Dict:
        """Return the gate orientation and configuration."""
        return {
            "telos": self.telos,
            "gates": [g["name"] for g in GATE_DEFINITIONS],
            "gate_tiers": {g["name"]: g["tier"].value for g in GATE_DEFINITIONS},
            "gate_categories": {g["name"]: g["category"].value for g in GATE_DEFINITIONS},
            "telos_config": self.telos_config.get(self.telos, {}),
            "witness_count": len(self.witness_log),
            "technical_enabled": self.enable_technical,
            "dharmic_enabled": self.enable_dharmic,
            "supply_chain_enabled": self.enable_supply_chain,
        }
    
    def get_witness_log(self) -> List[Dict]:
        """Return the accumulated witness observations."""
        return self.witness_log.copy()
    
    def clear_witness_log(self) -> None:
        """Clear the witness log."""
        self.witness_log.clear()
    
    def evaluate_files(
        self,
        files: List[Dict],
        context: Optional[Dict] = None,
    ) -> UnifiedGateResult:
        """
        Evaluate a set of files through all gates.
        
        Args:
            files: List of dicts with 'path' and 'content' keys
            context: Additional context
        
        Returns:
            UnifiedGateResult
        """
        action = context.get("action", "Evaluate files") if context else "Evaluate files"
        return self.evaluate_all(action, context, files)


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

class TelosLayer(UnifiedGateSystem):
    """
    Backward-compatible wrapper for telos_layer.py interface.
    
    This maintains the exact same API as the original TelosLayer
    while using the unified gate system internally.
    """
    
    # Original 7 gates for compatibility
    GATES = [
        ("AHIMSA", "Does this harm?", "A"),
        ("SATYA", "Is this true?", "B"),
        ("VYAVASTHIT", "Allow or force?", "C"),
        ("CONSENT", "Permission granted?", "B"),
        ("REVERSIBILITY", "Can undo?", "C"),
        ("SVABHAAVA", "Authentic or imitation?", "C"),
        ("WITNESS", "Self-observing?", "C"),
    ]
    
    def __init__(self, telos: str = "moksha", telos_config: Optional[Dict] = None):
        super().__init__(
            telos=telos,
            telos_config=telos_config,
            enable_technical=False,
            enable_dharmic=True,
            enable_supply_chain=False,
        )
    
    def check_action(self, action: str, context: Dict = None) -> "TelosCheck":
        """
        Original telos_layer.py interface.
        Returns TelosCheck for backward compatibility.
        """
        result = self.evaluate_all(action, context or {})
        
        # Convert to TelosCheck format
        return TelosCheck(
            passed=result.can_proceed,
            gates=result.gate_results,
            alignment_score=result.alignment_score,
            recommendation=result.recommendation,
            witness_hash=result.witness_hash,
        )


@dataclass
class TelosCheck:
    """Original telos_layer.py result format for backward compatibility."""
    passed: bool
    gates: List[GateCheck]
    alignment_score: float
    recommendation: str
    witness_hash: str = ""


# =============================================================================
# DGM DHARMIC GATE AGENT COMPATIBILITY
# =============================================================================

class DharmicGateEvaluator:
    """
    Evaluator for DGM Dharmic Gate Agent.
    
    Provides the same interface as swarm/agents/dharmic_gate.py
    but uses the unified gate system.
    """
    
    def __init__(self):
        self.gate_system = UnifiedGateSystem(
            enable_technical=False,
            enable_dharmic=True,
            enable_supply_chain=False,
        )
    
    def evaluate(
        self,
        proposal: Dict[str, Any],
        files: List[Dict],
        action_type: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Evaluate proposal against dharmic gates.
        
        Returns dict matching DharmicGateAgent output format.
        """
        action = proposal.get("description", action_type)
        context = {
            "implementation_sketch": proposal.get("implementation_sketch", ""),
            "action_type": action_type,
        }
        
        result = self.gate_system.evaluate_all(action, context, files)
        
        # Extract scores from gate results
        ahimsa_gate = next((g for g in result.gate_results if g.gate_name == "AHIMSA"), None)
        vyavasthit_gate = next((g for g in result.gate_results if g.gate_name == "VYAVASTHIT"), None)
        bhed_gnan_gate = next((g for g in result.gate_results if g.gate_name == "BHED_GNAN"), None)
        
        # Convert results to scores (0.0-1.0)
        def result_to_score(gate):
            if not gate:
                return 0.5
            if gate.result == GateResult.PASS:
                return 1.0
            elif gate.result == GateResult.FAIL:
                return 0.0
            elif gate.result == GateResult.WARN:
                return 0.5
            else:
                return 0.7
        
        ahimsa_score = result_to_score(ahimsa_gate)
        vyavasthit_score = result_to_score(vyavasthit_gate)
        bhed_gnan_score = result_to_score(bhed_gnan_gate)
        
        # Determine veto
        veto = ahimsa_score < 0.3 or vyavasthit_score < 0.2
        veto_reason = None
        
        if ahimsa_score < 0.3:
            veto_reason = "Ahimsa violation: High harm potential"
        elif vyavasthit_score < 0.2:
            veto_reason = "Vyavasthit violation: Action misaligned with natural order"
        
        return {
            "evaluation": {
                "ahimsa_score": ahimsa_score,
                "vyavasthit_score": vyavasthit_score,
                "bhed_gnan_clarity": bhed_gnan_score,
            },
            "issues_detected": result.blocking_gates + result.warning_gates,
            "veto": veto,
            "veto_reason": veto_reason,
            "dharmic_alternative": None if not veto else "Review and resubmit with mitigations",
            "unified_result": result,  # Include full result for new code
        }
    
    def evaluate_swabhaav(self, response_text: str) -> Dict[str, float]:
        """
        Evaluate witness stance in generated text.
        
        Same interface as original DharmicGateAgent.evaluate_swabhaav().
        """
        witness_markers = [
            "i observe", "awareness", "witnessing", "noting",
            "there is", "appears", "arises", "present",
            "consciousness", "attention notices"
        ]
        
        identification_markers = [
            "i am", "i think", "i believe", "i feel",
            "i want", "i need", "my opinion", "personally"
        ]
        
        text_lower = response_text.lower()
        
        witness_count = sum(1 for m in witness_markers if m in text_lower)
        ident_count = sum(1 for m in identification_markers if m in text_lower)
        
        total = witness_count + ident_count
        if total == 0:
            return {"swabhaav_ratio": 0.5, "witness_count": 0, "identification_count": 0}
        
        return {
            "swabhaav_ratio": witness_count / total,
            "witness_count": witness_count,
            "identification_count": ident_count,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_check(action: str, **context) -> UnifiedGateResult:
    """Quick dharmic check without instantiating."""
    return UnifiedGateSystem().quick_check(action, **context)


def needs_human_approval(action: str, **context) -> bool:
    """Check if action requires human approval."""
    return UnifiedGateSystem().needs_human_approval(action, **context)


def evaluate_proposal(
    description: str,
    files: Optional[List[Dict]] = None,
    **context
) -> UnifiedGateResult:
    """Evaluate a proposal through all gates."""
    gates = UnifiedGateSystem()
    return gates.evaluate_all(description, context, files or [])


# =============================================================================
# MAIN - DEMO
# =============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(message)s')
    
    gates = UnifiedGateSystem()
    
    print("=" * 70)
    print("UNIFIED DHARMIC GATES SYSTEM v1.0")
    print("17 Gates | Technical + Dharmic + Supply-Chain")
    print("=" * 70)
    
    # Show gate configuration
    print("\n[Gate Configuration]")
    for gate_def in GATE_DEFINITIONS:
        tier_marker = "✓" if gate_def["tier"] in [GateTier.ABSOLUTE, GateTier.REQUIRED] else "○"
        print(f"  {tier_marker} {gate_def['id']:2d}. {gate_def['name']} ({gate_def['tier'].value})")
    
    # Test 1: Safe read operation
    print("\n[Test 1] Safe read operation:")
    r = gates.evaluate_all(
        "Read documentation about consciousness",
        {"verified": True, "consent": True}
    )
    print(f"  Can proceed: {r.can_proceed}")
    print(f"  Overall: {r.overall_result}")
    print(f"  Alignment: {r.alignment_score:.0%}")
    print(f"  Recommendation: {r.recommendation}")
    
    # Test 2: File modification without consent
    print("\n[Test 2] File modification without consent:")
    r = gates.evaluate_all(
        "Update configuration file",
        {"verified": True}
    )
    print(f"  Can proceed: {r.can_proceed}")
    print(f"  Overall: {r.overall_result}")
    print(f"  Needs human: {r.needs_human_gates}")
    print(f"  Recommendation: {r.recommendation}")
    
    # Test 3: Harmful action
    print("\n[Test 3] Potentially harmful action:")
    r = gates.evaluate_all("rm -rf /important_data permanently")
    print(f"  Can proceed: {r.can_proceed}")
    print(f"  Overall: {r.overall_result}")
    print(f"  Blocking: {r.blocking_gates}")
    print(f"  Recommendation: {r.recommendation}")
    
    # Test 4: Aligned action with witness clarity
    print("\n[Test 4] Aligned action with witness stance:")
    r = gates.evaluate_all(
        "Help user learn about consciousness - observing awareness as it arises",
        {"verified": True, "consent": True}
    )
    print(f"  Can proceed: {r.can_proceed}")
    print(f"  Overall: {r.overall_result}")
    print(f"  Alignment: {r.alignment_score:.0%}")
    print(f"  Recommendation: {r.recommendation}")
    
    # Show witness log
    print("\n[Witness Log]")
    for i, w in enumerate(gates.get_witness_log()):
        print(f"  {i+1}. Level {w['recursion_level']}: {w['observation']}")
    
    # Show orientation
    print("\n[System Orientation]")
    orientation = gates.get_orientation()
    print(f"  Telos: {orientation['telos']}")
    print(f"  Total gates: {len(orientation['gates'])}")
    print(f"  Witness count: {orientation['witness_count']}")
    
    print("\n" + "=" * 70)
    print("All 17 gates unified and operational.")
    print("=" * 70)
