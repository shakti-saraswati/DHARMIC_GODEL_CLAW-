"""
CKC Risk Detector — 5-Dimensional Risk Scoring for Autonomous Coding

Implements the proactive risk detection system from SKILL.md spec.
Routes builds through appropriate gate levels based on risk score.

Dimensions:
    1. IMPACT (25%)     - Blast radius, financial exposure, scope
    2. EXPOSURE (20%)   - Users affected, network exposure, tier
    3. PERSISTENCE (20%) - Data changes duration, state scope
    4. SENSITIVITY (20%) - Data classification, PII, privilege
    5. REVERSIBILITY (15%) - Undo capability, test coverage

Risk Tiers:
    YOLO (0-20)    → 4 gates, auto-approve
    LOW (21-35)    → 8 gates, auto-approve
    MEDIUM (36-60) → 14 gates, overseer review
    HIGH (61-100)  → 22 gates, human approval

Usage:
    detector = RiskDetector()
    result = detector.analyze("Build payment gateway", files=["payment.py"])
    print(f"Risk: {result.tier} ({result.score}/100)")
    print(f"Gates: {result.gate_count}")

Created: 2026-02-05
JSCA! 🔥
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class RiskTier(Enum):
    """Risk tiers determining gate activation."""
    YOLO = "yolo"         # 0-20: Fast iteration, 4 gates
    LOW = "low"           # 21-35: Safe changes, 8 gates
    MEDIUM = "medium"     # 36-60: Careful review, 14 gates
    HIGH = "high"         # 61-100: Full security, 22 gates
    CRITICAL = "critical" # 90+: Human required, 22+ gates


class WeaveMode(Enum):
    """YOLO-Gate integration modes."""
    YOLO_NAVIGATE = "navigate"   # Gates in advisory mode
    YOLO_OVERSEER = "overseer"   # YOLO produces → Overseer reviews
    FULL_GATES = "full"          # All gates blocking


@dataclass
class RiskSignal:
    """A detected risk signal with metadata."""
    category: str
    pattern: str
    weight: float
    dimension: str
    description: str


@dataclass
class RiskResult:
    """Complete risk assessment result."""
    score: int                          # 0-100
    tier: RiskTier
    weave_mode: WeaveMode
    gate_count: int
    dimensions: Dict[str, int]          # Breakdown by dimension
    signals: List[RiskSignal]           # Detected signals
    auto_approve: bool                  # Can self-approve?
    human_required: bool                # Needs human approval?
    suggestions: List[str]              # Risk mitigation suggestions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "tier": self.tier.value,
            "weave_mode": self.weave_mode.value,
            "gate_count": self.gate_count,
            "dimensions": self.dimensions,
            "signals": [
                {"category": s.category, "pattern": s.pattern, "dimension": s.dimension}
                for s in self.signals
            ],
            "auto_approve": self.auto_approve,
            "human_required": self.human_required,
            "suggestions": self.suggestions
        }


class RiskDetector:
    """
    5-Dimensional Risk Scoring System.
    
    Analyzes code changes and task descriptions to determine
    appropriate security level and gate activation.
    """
    
    # Dimension weights (must sum to 100)
    WEIGHTS = {
        "impact": 25,
        "exposure": 20,
        "persistence": 20,
        "sensitivity": 20,
        "reversibility": 15
    }
    
    # Risk tier thresholds
    THRESHOLDS = {
        RiskTier.YOLO: (0, 20),
        RiskTier.LOW: (21, 35),
        RiskTier.MEDIUM: (36, 60),
        RiskTier.HIGH: (61, 89),
        RiskTier.CRITICAL: (90, 100)
    }
    
    # Gates per tier
    GATE_COUNTS = {
        RiskTier.YOLO: 4,
        RiskTier.LOW: 8,
        RiskTier.MEDIUM: 14,
        RiskTier.HIGH: 22,
        RiskTier.CRITICAL: 22
    }
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize risk detection patterns."""
        
        # IMPACT patterns (blast radius, financial, scope)
        self.impact_patterns = {
            # Financial (highest impact)
            "payment": 100,
            "billing": 95,
            "transaction": 95,
            "wallet": 90,
            "crypto": 90,
            "money": 85,
            "invoice": 80,
            "subscription": 75,
            "pricing": 70,
            # Infrastructure
            "database": 85,
            "migration": 90,
            "deploy": 85,
            "terraform": 90,
            "kubernetes": 85,
            "k8s": 85,
            "docker": 60,
            "ci/cd": 70,
            "pipeline": 65,
            # System-wide
            "global": 60,
            "system": 50,
            "core": 55,
            "framework": 50,
            "orchestrat": 70,
            "swarm": 65,
        }
        
        # EXPOSURE patterns (users affected, network)
        self.exposure_patterns = {
            # Authentication
            "login": 90,
            "auth": 95,
            "password": 100,
            "oauth": 90,
            "jwt": 85,
            "token": 80,
            "session": 75,
            "mfa": 85,
            "2fa": 85,
            # User-facing
            "api": 70,
            "endpoint": 65,
            "webhook": 75,
            "public": 60,
            "customer": 70,
            "user": 50,
            # Network
            "http": 40,
            "request": 35,
            "socket": 60,
            "websocket": 65,
        }
        
        # PERSISTENCE patterns (data duration, state)
        self.persistence_patterns = {
            # Database ops
            "insert": 60,
            "update": 65,
            "delete": 80,
            "drop": 100,
            "truncate": 95,
            "alter": 75,
            "schema": 80,
            # State
            "cache": 40,
            "store": 50,
            "persist": 60,
            "save": 45,
            "write": 50,
            "commit": 55,
            # Configuration
            "config": 55,
            "setting": 50,
            "environment": 60,
            "env": 55,
        }
        
        # SENSITIVITY patterns (data classification)
        self.sensitivity_patterns = {
            # Secrets
            "secret": 100,
            "credential": 100,
            "api_key": 95,
            "apikey": 95,
            "private_key": 100,
            "certificate": 90,
            "ssl": 80,
            "tls": 80,
            # PII
            "email": 60,
            "phone": 65,
            "address": 60,
            "ssn": 100,
            "social_security": 100,
            "credit_card": 100,
            "dob": 70,
            "birthdate": 70,
            # Encryption
            "encrypt": 75,
            "decrypt": 80,
            "hash": 60,
            "salt": 65,
        }
        
        # REVERSIBILITY patterns (undo capability)
        # Lower score = harder to reverse = higher risk
        self.reversibility_patterns = {
            # Hard to reverse (high risk)
            "rm -rf": 100,
            "delete": 70,
            "remove": 60,
            "destroy": 90,
            "purge": 85,
            "wipe": 95,
            "overwrite": 75,
            "force": 50,
            # Easy to reverse (low risk, negative weight)
            "backup": -30,
            "snapshot": -25,
            "rollback": -35,
            "undo": -30,
            "revert": -25,
            "test": -20,
            "mock": -15,
            "dry_run": -40,
            "dry-run": -40,
        }
        
        # Safe path patterns (reduce risk)
        self.safe_paths = [
            r"test[s]?/",
            r"spec[s]?/",
            r"__test__",
            r"_test\.py$",
            r"test_.*\.py$",
            r".*_test\.py$",
            r"docs?/",
            r"example[s]?/",
            r"prototype[s]?/",
            r"spike[s]?/",
            r"scratch/",
            r"temp/",
            r"tmp/",
        ]
        
        # High-risk path patterns
        self.risky_paths = [
            r"prod(uction)?/",
            r"live/",
            r"deploy/",
            r"infra(structure)?/",
            r"security/",
            r"auth/",
            r"payment[s]?/",
            r"billing/",
            r"config/",
            r"secrets?/",
        ]
        
        # YOLO override patterns
        self.yolo_patterns = [
            "spike", "experiment", "learning", "demo", "prototype",
            "scratch", "temp", "throwaway", "test", "poc", "proof of concept"
        ]
    
    def analyze(
        self,
        description: str,
        code: str = "",
        files: Optional[List[str]] = None,
        branch: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> RiskResult:
        """
        Analyze a task/code for risk level.
        
        Args:
            description: Task description
            code: Code content to analyze
            files: List of file paths being modified
            branch: Git branch name
            context: Additional context
        
        Returns:
            RiskResult with score, tier, and recommendations
        """
        files = files or []
        context = context or {}
        
        # Combine all text for analysis
        combined = f"{description} {code} {' '.join(files)} {branch}".lower()
        
        # Calculate dimension scores
        dimensions = {
            "impact": self._score_dimension(combined, self.impact_patterns),
            "exposure": self._score_dimension(combined, self.exposure_patterns),
            "persistence": self._score_dimension(combined, self.persistence_patterns),
            "sensitivity": self._score_dimension(combined, self.sensitivity_patterns),
            "reversibility": self._score_dimension(combined, self.reversibility_patterns),
        }
        
        # Collect signals
        signals = self._collect_signals(combined)
        
        # Apply path modifiers
        path_modifier = self._analyze_paths(files)
        
        # Apply branch modifiers
        branch_modifier = self._analyze_branch(branch)
        
        # Check for YOLO override
        yolo_override = self._check_yolo_override(combined, context)
        
        # Calculate weighted score
        raw_score = sum(
            dimensions[dim] * (self.WEIGHTS[dim] / 100)
            for dim in dimensions
        )
        
        # Apply modifiers
        final_score = int(raw_score + path_modifier + branch_modifier)
        
        # Apply YOLO override
        if yolo_override and final_score < 50:
            final_score = min(final_score, 20)
        
        # Clamp to 0-100
        final_score = max(0, min(100, final_score))
        
        # Determine tier
        tier = self._score_to_tier(final_score)
        
        # Determine weave mode
        weave_mode = self._tier_to_weave_mode(tier)
        
        # Determine gate count
        gate_count = self.GATE_COUNTS[tier]
        
        # Determine approval requirements
        auto_approve = tier in (RiskTier.YOLO, RiskTier.LOW)
        human_required = tier in (RiskTier.HIGH, RiskTier.CRITICAL)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(signals, tier)
        
        return RiskResult(
            score=final_score,
            tier=tier,
            weave_mode=weave_mode,
            gate_count=gate_count,
            dimensions=dimensions,
            signals=signals,
            auto_approve=auto_approve,
            human_required=human_required,
            suggestions=suggestions
        )
    
    def _score_dimension(self, text: str, patterns: Dict[str, int]) -> int:
        """Score a dimension based on pattern matches."""
        matches = []
        for pattern, weight in patterns.items():
            if pattern.lower() in text:
                matches.append(weight)
        
        if not matches:
            return 0
        
        # Use max + average of top 3 to avoid over-counting
        matches.sort(reverse=True)
        top_matches = matches[:3]
        return int((max(top_matches) + sum(top_matches) / len(top_matches)) / 2)
    
    def _collect_signals(self, text: str) -> List[RiskSignal]:
        """Collect all risk signals from text."""
        signals = []
        
        all_patterns = [
            (self.impact_patterns, "impact", "Impact/Scope"),
            (self.exposure_patterns, "exposure", "Exposure/Users"),
            (self.persistence_patterns, "persistence", "Persistence/State"),
            (self.sensitivity_patterns, "sensitivity", "Sensitivity/Data"),
            (self.reversibility_patterns, "reversibility", "Reversibility"),
        ]
        
        for patterns, dimension, desc in all_patterns:
            for pattern, weight in patterns.items():
                if pattern.lower() in text and weight > 50:
                    signals.append(RiskSignal(
                        category=desc,
                        pattern=pattern,
                        weight=weight,
                        dimension=dimension,
                        description=f"{desc}: '{pattern}' detected"
                    ))
        
        return signals
    
    def _analyze_paths(self, files: List[str]) -> int:
        """Analyze file paths for risk modifiers."""
        if not files:
            return 0
        
        modifier = 0
        
        for filepath in files:
            # Check safe paths
            for pattern in self.safe_paths:
                if re.search(pattern, filepath, re.IGNORECASE):
                    modifier -= 15
                    break
            
            # Check risky paths
            for pattern in self.risky_paths:
                if re.search(pattern, filepath, re.IGNORECASE):
                    modifier += 20
                    break
        
        return modifier
    
    def _analyze_branch(self, branch: str) -> int:
        """Analyze git branch for risk modifier."""
        if not branch:
            return 0
        
        branch_lower = branch.lower()
        
        # High-risk branches
        if any(b in branch_lower for b in ["main", "master", "prod", "release", "live"]):
            return 25
        
        # Medium-risk branches
        if any(b in branch_lower for b in ["develop", "staging", "stage"]):
            return 10
        
        # Low-risk branches
        if any(b in branch_lower for b in ["feature", "fix", "test", "spike", "experiment"]):
            return -10
        
        return 0
    
    def _check_yolo_override(self, text: str, context: Dict[str, Any]) -> bool:
        """Check if YOLO mode is explicitly requested."""
        # Check context flags
        if context.get("yolo") or context.get("DGC_YOLO_MODE"):
            return True
        
        # Check text patterns
        for pattern in self.yolo_patterns:
            if pattern in text:
                return True
        
        return False
    
    def _score_to_tier(self, score: int) -> RiskTier:
        """Convert score to risk tier."""
        for tier, (low, high) in self.THRESHOLDS.items():
            if low <= score <= high:
                return tier
        return RiskTier.HIGH
    
    def _tier_to_weave_mode(self, tier: RiskTier) -> WeaveMode:
        """Determine weave mode from tier."""
        if tier in (RiskTier.YOLO, RiskTier.LOW):
            return WeaveMode.YOLO_NAVIGATE
        elif tier == RiskTier.MEDIUM:
            return WeaveMode.YOLO_OVERSEER
        else:
            return WeaveMode.FULL_GATES
    
    def _generate_suggestions(self, signals: List[RiskSignal], tier: RiskTier) -> List[str]:
        """Generate risk mitigation suggestions."""
        suggestions = []
        
        # Based on detected signals
        signal_dims = {s.dimension for s in signals}
        
        if "sensitivity" in signal_dims:
            suggestions.append("Ensure sensitive data is encrypted/masked")
        
        if "persistence" in signal_dims:
            suggestions.append("Create backup before destructive operations")
        
        if "exposure" in signal_dims:
            suggestions.append("Add rate limiting and input validation")
        
        if "reversibility" in signal_dims:
            suggestions.append("Implement rollback mechanism")
        
        # Based on tier
        if tier in (RiskTier.HIGH, RiskTier.CRITICAL):
            suggestions.append("Request human review before deployment")
            suggestions.append("Add comprehensive test coverage")
        
        if tier == RiskTier.MEDIUM:
            suggestions.append("Consider adding integration tests")
        
        return suggestions


# Convenience function
def analyze_risk(
    description: str,
    code: str = "",
    files: Optional[List[str]] = None
) -> RiskResult:
    """Quick risk analysis."""
    detector = RiskDetector()
    return detector.analyze(description, code, files)


if __name__ == "__main__":
    # Demo
    detector = RiskDetector()
    
    examples = [
        ("Learn asyncio basics", [], ""),
        ("Fix typo in README", ["docs/README.md"], ""),
        ("Add coverage report", ["tests/coverage.py"], ""),
        ("Build authentication system", ["src/auth/login.py"], "main"),
        ("Payment webhook handler", ["src/payments/webhook.py"], "production"),
    ]
    
    print("=" * 60)
    print("🔥 CKC RISK DETECTOR — Demo")
    print("=" * 60)
    
    for desc, files, branch in examples:
        result = detector.analyze(desc, files=files, branch=branch)
        print(f"\n📝 '{desc}'")
        print(f"   Files: {files}")
        print(f"   Branch: {branch or 'N/A'}")
        print(f"   → Score: {result.score}/100")
        print(f"   → Tier: {result.tier.value.upper()}")
        print(f"   → Mode: {result.weave_mode.value}")
        print(f"   → Gates: {result.gate_count}")
        print(f"   → Auto-approve: {result.auto_approve}")
        if result.suggestions:
            print(f"   → Suggestions: {result.suggestions[0]}")
    
    print("\n" + "=" * 60)
    print("JSCA! 🪷")
