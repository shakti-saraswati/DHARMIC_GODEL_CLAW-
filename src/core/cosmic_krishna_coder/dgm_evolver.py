"""
🧬 DGM EVOLVER — Self-Improvement from Gate Failures
=====================================================

Analyzes gate failures and automatically generates Darwin-Gödel Machine
proposals for system evolution.

Core Principle: The system learns from its failures. Every blocked commit
is an opportunity for improvement.

Proposal Types:
1. NEW_GATE — Pattern detected that no gate catches
2. GATE_REFINEMENT — False positives/negatives in existing gate
3. THRESHOLD_ADJUSTMENT — Risk thresholds need tuning
4. PATTERN_LIBRARY — New detection patterns needed
5. DOCUMENTATION — Gate behavior needs better docs

JSCA! 🧬
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProposalType(Enum):
    """Types of DGM evolution proposals."""
    NEW_GATE = "new_gate"
    GATE_REFINEMENT = "gate_refinement"
    THRESHOLD_ADJUSTMENT = "threshold_adjustment"
    PATTERN_LIBRARY = "pattern_library"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


class ProposalPriority(Enum):
    """Priority levels for proposals."""
    CRITICAL = 10  # Security vulnerability, must fix
    HIGH = 8       # Significant improvement
    MEDIUM = 5     # Nice to have
    LOW = 3        # Future consideration
    TRIVIAL = 1    # Minor polish


@dataclass
class FailurePattern:
    """A detected pattern of gate failures."""
    gate_name: str
    failure_count: int
    unique_triggers: List[str]
    false_positive_likelihood: float  # 0-1
    common_code_patterns: List[str]
    suggested_action: str


@dataclass
class EvolutionProposal:
    """A proposal for system self-improvement."""
    proposal_id: str
    type: ProposalType
    priority: ProposalPriority
    title: str
    motivation: str
    analysis: str
    implementation_plan: str
    code_suggestion: Optional[str]
    estimated_impact: str
    dependencies: List[str]
    source_failures: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "proposed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "motivation": self.motivation,
            "analysis": self.analysis,
            "implementation_plan": self.implementation_plan,
            "code_suggestion": self.code_suggestion,
            "estimated_impact": self.estimated_impact,
            "dependencies": self.dependencies,
            "source_failures": self.source_failures,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


class DGMEvolver:
    """
    Darwin-Gödel Machine Evolver.
    
    Analyzes gate failures and generates proposals for system evolution.
    The system that improves itself.
    """
    
    def __init__(self, proposals_dir: Optional[Path] = None, history_dir: Optional[Path] = None):
        self.proposals_dir = proposals_dir or Path.home() / ".dgm" / "proposals"
        self.history_dir = history_dir or Path.home() / ".dgm" / "failure_history"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Track failures in memory for session
        self.session_failures: List[Dict[str, Any]] = []
        self.proposal_counter = self._get_next_proposal_id()
    
    def _get_next_proposal_id(self) -> int:
        """Get next proposal ID from existing proposals."""
        existing = list(self.proposals_dir.glob("dgm_*.json"))
        if not existing:
            return 1
        
        max_id = 0
        for f in existing:
            try:
                match = re.search(r'dgm_\d+_(\d+)', f.stem)
                if match:
                    max_id = max(max_id, int(match.group(1)))
            except:
                pass
        return max_id + 1
    
    def record_failure(
        self,
        gate_name: str,
        message: str,
        code_snippet: str = "",
        file_path: str = "",
        details: Optional[Dict] = None
    ):
        """Record a gate failure for analysis."""
        failure = {
            "gate_name": gate_name,
            "message": message,
            "code_snippet": code_snippet[:500] if code_snippet else "",
            "file_path": file_path,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        self.session_failures.append(failure)
        
        # Persist to history
        date_str = datetime.now().strftime("%Y%m%d")
        history_file = self.history_dir / f"failures_{date_str}.jsonl"
        
        with open(history_file, 'a') as f:
            f.write(json.dumps(failure) + "\n")
    
    def analyze_failures(self, min_occurrences: int = 2) -> List[FailurePattern]:
        """Analyze recorded failures to find patterns."""
        # Load recent history
        all_failures = self._load_recent_failures(days=7)
        all_failures.extend(self.session_failures)
        
        if not all_failures:
            return []
        
        # Group by gate
        by_gate = defaultdict(list)
        for f in all_failures:
            by_gate[f["gate_name"]].append(f)
        
        patterns = []
        for gate_name, failures in by_gate.items():
            if len(failures) < min_occurrences:
                continue
            
            # Extract unique triggers
            triggers = list(set(f["message"] for f in failures))
            
            # Extract code patterns
            code_patterns = self._extract_code_patterns(failures)
            
            # Estimate false positive likelihood
            fp_likelihood = self._estimate_false_positive(gate_name, failures)
            
            # Suggest action
            action = self._suggest_action(gate_name, len(failures), fp_likelihood)
            
            patterns.append(FailurePattern(
                gate_name=gate_name,
                failure_count=len(failures),
                unique_triggers=triggers[:5],
                false_positive_likelihood=fp_likelihood,
                common_code_patterns=code_patterns[:3],
                suggested_action=action,
            ))
        
        return sorted(patterns, key=lambda p: p.failure_count, reverse=True)
    
    def _load_recent_failures(self, days: int = 7) -> List[Dict]:
        """Load failures from recent history files."""
        failures = []
        
        for i in range(days):
            date = datetime.now().date()
            from datetime import timedelta
            check_date = date - timedelta(days=i)
            date_str = check_date.strftime("%Y%m%d")
            history_file = self.history_dir / f"failures_{date_str}.jsonl"
            
            if history_file.exists():
                try:
                    with open(history_file) as f:
                        for line in f:
                            if line.strip():
                                failures.append(json.loads(line))
                except:
                    pass
        
        return failures
    
    def _extract_code_patterns(self, failures: List[Dict]) -> List[str]:
        """Extract common code patterns from failures."""
        patterns = []
        
        # Look for common strings in code snippets
        code_snippets = [f.get("code_snippet", "") for f in failures if f.get("code_snippet")]
        
        if not code_snippets:
            return patterns
        
        # Find common substrings (simplified)
        common_patterns = [
            (r'eval\s*\(', 'eval() usage'),
            (r'exec\s*\(', 'exec() usage'),
            (r'subprocess\.call\s*\(', 'subprocess.call() usage'),
            (r'os\.system\s*\(', 'os.system() usage'),
            (r'password\s*=\s*["\']', 'hardcoded password'),
            (r'api[_-]?key\s*=\s*["\']', 'hardcoded API key'),
            (r'except\s*:\s*$', 'bare except clause'),
            (r'import\s+\*', 'star import'),
        ]
        
        for pattern, name in common_patterns:
            count = sum(1 for code in code_snippets if re.search(pattern, code, re.I))
            if count >= len(code_snippets) * 0.5:  # Present in 50%+ of failures
                patterns.append(name)
        
        return patterns
    
    def _estimate_false_positive(self, gate_name: str, failures: List[Dict]) -> float:
        """Estimate likelihood that failures are false positives."""
        # Heuristics for false positive detection
        
        # If all failures have same message, might be overly broad
        messages = [f["message"] for f in failures]
        unique_ratio = len(set(messages)) / len(messages) if messages else 1
        
        # If failures are in test files, more likely false positive
        test_file_count = sum(1 for f in failures if "test" in f.get("file_path", "").lower())
        test_ratio = test_file_count / len(failures) if failures else 0
        
        # Combine heuristics
        fp_score = 0.0
        
        if unique_ratio < 0.2:  # Very repetitive messages
            fp_score += 0.3
        
        if test_ratio > 0.5:  # Mostly test files
            fp_score += 0.3
        
        # Gate-specific adjustments
        lenient_gates = ["lint_format", "type_check", "svadhyaya", "santosha"]
        if gate_name.lower() in lenient_gates:
            fp_score += 0.2
        
        return min(fp_score, 1.0)
    
    def _suggest_action(self, gate_name: str, failure_count: int, fp_likelihood: float) -> str:
        """Suggest action based on failure analysis."""
        if fp_likelihood > 0.7:
            return f"Review {gate_name} for overly broad detection - likely false positives"
        
        if failure_count > 10:
            return f"High failure rate on {gate_name} - consider threshold adjustment or documentation"
        
        if failure_count > 5:
            return f"Moderate failures on {gate_name} - analyze patterns for targeted improvement"
        
        return f"Monitor {gate_name} - failure pattern emerging"
    
    def generate_proposals(self, patterns: Optional[List[FailurePattern]] = None) -> List[EvolutionProposal]:
        """Generate evolution proposals from failure patterns."""
        if patterns is None:
            patterns = self.analyze_failures()
        
        if not patterns:
            return []
        
        proposals = []
        
        for pattern in patterns:
            # High false positive → Refinement proposal
            if pattern.false_positive_likelihood > 0.5:
                proposals.append(self._create_refinement_proposal(pattern))
            
            # Many failures with code patterns → Pattern library proposal
            elif pattern.common_code_patterns and pattern.failure_count > 5:
                proposals.append(self._create_pattern_proposal(pattern))
            
            # Security gate with high failures → Threshold proposal
            elif pattern.gate_name.lower() in ["ahimsa", "secrets", "vulnerability"]:
                proposals.append(self._create_threshold_proposal(pattern))
            
            # Default → Documentation proposal
            else:
                proposals.append(self._create_documentation_proposal(pattern))
        
        # Store proposals
        for p in proposals:
            self._store_proposal(p)
        
        return proposals
    
    def _create_refinement_proposal(self, pattern: FailurePattern) -> EvolutionProposal:
        """Create gate refinement proposal."""
        self.proposal_counter += 1
        
        return EvolutionProposal(
            proposal_id=f"dgm_{datetime.now().strftime('%Y%m%d')}_{self.proposal_counter}",
            type=ProposalType.GATE_REFINEMENT,
            priority=ProposalPriority.HIGH,
            title=f"Refine {pattern.gate_name} Gate — Reduce False Positives",
            motivation=f"{pattern.gate_name} has {pattern.failure_count} failures with {pattern.false_positive_likelihood:.0%} estimated false positive rate",
            analysis=f"Common triggers: {pattern.unique_triggers[:3]}. Likely causes: overly broad pattern matching or missing context awareness.",
            implementation_plan=f"""
1. Review current {pattern.gate_name} implementation in gates.py
2. Add exclusion patterns for common false positives
3. Consider context-aware checking (e.g., ignore test files)
4. Add confidence scoring to gate output
5. Test with historical failure cases
""",
            code_suggestion=f"""
# In gates.py, add exclusion logic:
def check_{pattern.gate_name.lower()}(code: str, files: List[str] = None, **kwargs) -> GateResult:
    # Skip if in test context
    if any('test' in (f or '').lower() for f in (files or [])):
        return GateResult("{pattern.gate_name}", GateStatus.SKIP, "Skipped for test files", False)
    
    # Existing logic with refined patterns...
""",
            estimated_impact="Reduce false positives by 50%+, improve developer experience",
            dependencies=["gates.py", "yolo_weaver.py"],
            source_failures=pattern.unique_triggers[:5],
        )
    
    def _create_pattern_proposal(self, pattern: FailurePattern) -> EvolutionProposal:
        """Create pattern library proposal."""
        self.proposal_counter += 1
        
        return EvolutionProposal(
            proposal_id=f"dgm_{datetime.now().strftime('%Y%m%d')}_{self.proposal_counter}",
            type=ProposalType.PATTERN_LIBRARY,
            priority=ProposalPriority.MEDIUM,
            title=f"Expand {pattern.gate_name} Pattern Library",
            motivation=f"{pattern.gate_name} catching {pattern.failure_count} failures with patterns: {pattern.common_code_patterns}",
            analysis="These patterns are correctly identified but could be more specific. Adding to pattern library improves detection quality.",
            implementation_plan=f"""
1. Document detected patterns: {pattern.common_code_patterns}
2. Add pattern variants to gates.py
3. Create test cases for each pattern
4. Consider severity levels per pattern
5. Update gate documentation
""",
            code_suggestion=f"""
# Add to pattern library in gates.py:
{pattern.gate_name.upper()}_PATTERNS = [
    # Existing patterns...
    
    # New patterns from DGM analysis:
{chr(10).join(f'    (r"{p}", "{p} detected"),' for p in pattern.common_code_patterns)}
]
""",
            estimated_impact="Improve detection specificity, reduce noise",
            dependencies=["gates.py"],
            source_failures=pattern.unique_triggers[:5],
        )
    
    def _create_threshold_proposal(self, pattern: FailurePattern) -> EvolutionProposal:
        """Create threshold adjustment proposal."""
        self.proposal_counter += 1
        
        return EvolutionProposal(
            proposal_id=f"dgm_{datetime.now().strftime('%Y%m%d')}_{self.proposal_counter}",
            type=ProposalType.THRESHOLD_ADJUSTMENT,
            priority=ProposalPriority.HIGH,
            title=f"Tune {pattern.gate_name} Thresholds",
            motivation=f"Security gate {pattern.gate_name} has {pattern.failure_count} failures — need threshold review",
            analysis=f"High failure rate on security gate. Either: (1) codebase has real issues, or (2) thresholds too aggressive. Triggers: {pattern.unique_triggers[:2]}",
            implementation_plan=f"""
1. Audit current {pattern.gate_name} thresholds
2. Compare with industry standards (OWASP, CWE)
3. Analyze if failures are true positives
4. Adjust severity classification
5. Consider progressive rollout (warn → block)
""",
            code_suggestion=None,
            estimated_impact="Balance security strictness with development velocity",
            dependencies=["gates.py", "risk_detector.py"],
            source_failures=pattern.unique_triggers[:5],
        )
    
    def _create_documentation_proposal(self, pattern: FailurePattern) -> EvolutionProposal:
        """Create documentation proposal."""
        self.proposal_counter += 1
        
        return EvolutionProposal(
            proposal_id=f"dgm_{datetime.now().strftime('%Y%m%d')}_{self.proposal_counter}",
            type=ProposalType.DOCUMENTATION,
            priority=ProposalPriority.LOW,
            title=f"Document {pattern.gate_name} Gate Behavior",
            motivation=f"{pattern.failure_count} failures suggest developers need clearer guidance on {pattern.gate_name}",
            analysis=f"Failure pattern: {pattern.suggested_action}",
            implementation_plan=f"""
1. Add docstring to {pattern.gate_name} gate function
2. Document common triggers and fixes
3. Add examples to README
4. Create troubleshooting guide
""",
            code_suggestion=None,
            estimated_impact="Reduce developer confusion, faster fixes",
            dependencies=["gates.py", "README.md"],
            source_failures=pattern.unique_triggers[:5],
        )
    
    def _store_proposal(self, proposal: EvolutionProposal):
        """Store proposal to disk."""
        filepath = self.proposals_dir / f"{proposal.proposal_id}.json"
        with open(filepath, 'w') as f:
            json.dump(proposal.to_dict(), f, indent=2)
    
    def get_pending_proposals(self, limit: int = 10) -> List[EvolutionProposal]:
        """Get pending proposals sorted by priority."""
        proposals = []
        
        for filepath in self.proposals_dir.glob("dgm_*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    if data.get("status") == "proposed":
                        proposals.append(data)
            except:
                pass
        
        # Sort by priority (higher = more important)
        proposals.sort(key=lambda p: p.get("priority", 0), reverse=True)
        
        return proposals[:limit]
    
    def evolve_from_weave_result(self, weave_result: Any) -> List[EvolutionProposal]:
        """
        Analyze a WeaveResult and generate proposals.
        
        Called automatically after each YOLO Weaver execution.
        """
        if not hasattr(weave_result, 'gate_results'):
            return []
        
        # Record failures
        for gate_result in weave_result.gate_results:
            if hasattr(gate_result, 'status') and 'FAIL' in str(gate_result.status):
                self.record_failure(
                    gate_name=gate_result.gate_name if hasattr(gate_result, 'gate_name') else 'unknown',
                    message=gate_result.message if hasattr(gate_result, 'message') else '',
                    details=gate_result.evidence if hasattr(gate_result, 'evidence') else {}
                )
        
        # Generate proposals if enough failures
        if len(self.session_failures) >= 3:
            return self.generate_proposals()
        
        return []


# Singleton instance for easy access
_evolver_instance: Optional[DGMEvolver] = None


def get_evolver() -> DGMEvolver:
    """Get or create the singleton DGM evolver."""
    global _evolver_instance
    if _evolver_instance is None:
        _evolver_instance = DGMEvolver()
    return _evolver_instance


def evolve_from_failures(
    gate_results: List[Any],
    code: str = "",
    files: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to evolve from gate failures.
    
    Usage:
        from cosmic_krishna_coder.dgm_evolver import evolve_from_failures
        
        proposals = evolve_from_failures(weave_result.gate_results)
    """
    evolver = get_evolver()
    
    for result in gate_results:
        if hasattr(result, 'status') and 'FAIL' in str(result.status):
            evolver.record_failure(
                gate_name=getattr(result, 'gate_name', getattr(result, 'name', 'unknown')),
                message=getattr(result, 'message', ''),
                code_snippet=code[:500] if code else "",
                details=getattr(result, 'evidence', getattr(result, 'details', {}))
            )
    
    proposals = evolver.generate_proposals()
    return [p.to_dict() for p in proposals]


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    
    print("=" * 60)
    print("🧬 DGM EVOLVER — Self-Improvement Engine")
    print("=" * 60)
    
    evolver = DGMEvolver()
    
    # Show recent failures
    patterns = evolver.analyze_failures(min_occurrences=1)
    
    if not patterns:
        print("\n📊 No failure patterns detected yet.")
        print("   Run gates on code to generate failure history.")
    else:
        print(f"\n📊 Detected {len(patterns)} failure patterns:")
        for p in patterns:
            print(f"\n   {p.gate_name}:")
            print(f"      Failures: {p.failure_count}")
            print(f"      FP Likelihood: {p.false_positive_likelihood:.0%}")
            print(f"      Action: {p.suggested_action}")
    
    # Show pending proposals
    pending = evolver.get_pending_proposals()
    
    if pending:
        print(f"\n📋 {len(pending)} pending proposals:")
        for p in pending:
            print(f"   [{p['priority']}] {p['title']}")
    
    # Generate new proposals
    if patterns:
        print("\n🧬 Generating evolution proposals...")
        proposals = evolver.generate_proposals(patterns)
        
        if proposals:
            print(f"\n✨ Generated {len(proposals)} proposals:")
            for p in proposals:
                print(f"   [{p.priority.value}] {p.title}")
                print(f"       Type: {p.type.value}")
                print(f"       Impact: {p.estimated_impact}")
    
    print("\n" + "=" * 60)
    print("🪷 JSCA — The system that improves itself")
    print("=" * 60)
