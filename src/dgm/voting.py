#!/usr/bin/env python3
"""
Voting Swarm - 25-Vote Diverse Consensus Mechanism
===================================================

A multi-perspective review system for mutation proposals.
Requires diverse approval to accept changes, ensuring robust
code quality through varied viewpoints.

Consensus Requirements:
- 25 total votes minimum
- >80% approval rate
- diversity_score > 0.7 (votes spread across reviewer types)
- No more than 5 votes from same reviewer type

This implements "wisdom of crowds" — diverse perspectives
catch more issues than homogeneous review.
"""
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from collections import Counter


# =============================================================================
# Data Types
# =============================================================================

@dataclass
class MutationProposal:
    """A proposed code mutation for review."""
    id: str
    component: str  # Which file/module is being changed
    description: str  # Human-readable description
    diff: str  # The actual code diff
    rationale: str  # Why this change is proposed
    parent_id: Optional[str] = None  # Parent mutation ID if any
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def diff_lines(self) -> int:
        """Count lines changed in diff."""
        return len([l for l in self.diff.split('\n') if l.startswith(('+', '-'))])


class ReviewerType(Enum):
    """Types of reviewers in the voting swarm."""
    SECURITY = "security"
    ELEGANCE = "elegance"
    DHARMIC = "dharmic"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MINIMAL_CHANGE = "minimal_change"
    TEST = "test"
    ARCHITECTURE = "architecture"


@dataclass
class Vote:
    """A single vote from a reviewer."""
    reviewer_type: ReviewerType
    reviewer_id: str  # Unique ID for this reviewer instance
    approve: bool
    confidence: float  # 0.0 to 1.0
    rationale: str
    concerns: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate confidence range."""
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class VoteResult:
    """Result of the voting process."""
    approved: bool
    total_votes: int
    approval_ratio: float  # 0.0 to 1.0
    diversity_score: float  # 0.0 to 1.0
    dissenting_opinions: List[str]
    votes: List[Vote] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    
    def summary(self) -> str:
        """Human-readable summary of vote result."""
        status = "✅ APPROVED" if self.approved else "❌ REJECTED"
        lines = [
            f"{status}",
            f"  Votes: {self.total_votes}",
            f"  Approval: {self.approval_ratio:.1%}",
            f"  Diversity: {self.diversity_score:.2f}",
        ]
        if self.rejection_reasons:
            lines.append(f"  Rejection reasons: {', '.join(self.rejection_reasons)}")
        if self.dissenting_opinions:
            lines.append(f"  Dissenting opinions: {len(self.dissenting_opinions)}")
        return '\n'.join(lines)


# =============================================================================
# Base Reviewer
# =============================================================================

class BaseReviewer(ABC):
    """
    Abstract base class for all reviewers.
    
    Each reviewer examines proposals from a specific perspective
    and casts a vote with confidence and rationale.
    """
    
    reviewer_type: ReviewerType
    
    def __init__(self, reviewer_id: str):
        self.reviewer_id = reviewer_id
    
    @abstractmethod
    async def review(self, proposal: MutationProposal) -> Vote:
        """
        Review a proposal and return a vote.
        
        Subclasses implement their specific review logic.
        """
        pass
    
    def _make_vote(
        self, 
        approve: bool, 
        confidence: float, 
        rationale: str,
        concerns: List[str] = None
    ) -> Vote:
        """Helper to create a vote with this reviewer's info."""
        return Vote(
            reviewer_type=self.reviewer_type,
            reviewer_id=self.reviewer_id,
            approve=approve,
            confidence=confidence,
            rationale=rationale,
            concerns=concerns or []
        )


# =============================================================================
# Concrete Reviewers
# =============================================================================

class SecurityReviewer(BaseReviewer):
    """Reviews for vulnerabilities, injection risks, and security issues."""
    
    reviewer_type = ReviewerType.SECURITY
    
    DANGEROUS_PATTERNS = [
        'eval(', 'exec(', '__import__', 'subprocess.call',
        'shell=True', 'os.system', 'pickle.loads', 'yaml.load(',
        'input(', 'raw_input(', 'compile(', 'globals()[',
    ]
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff_lower = proposal.diff.lower()
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in diff_lower:
                concerns.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for hardcoded secrets
        secret_indicators = ['password=', 'api_key=', 'secret=', 'token=']
        for indicator in secret_indicators:
            if indicator in diff_lower:
                concerns.append(f"Potential hardcoded secret: {indicator}")
        
        # Check for SQL injection risks
        if 'execute(' in diff_lower and ('format(' in diff_lower or '%s' in proposal.diff):
            concerns.append("Potential SQL injection risk")
        
        approve = len(concerns) == 0
        confidence = 0.9 if not concerns else 0.3
        
        rationale = "No security issues detected" if approve else f"Found {len(concerns)} security concern(s)"
        
        return self._make_vote(approve, confidence, rationale, concerns)


class EleganceReviewer(BaseReviewer):
    """Reviews for clean code, minimal complexity, and readability."""
    
    reviewer_type = ReviewerType.ELEGANCE
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        lines = proposal.diff.split('\n')
        added_lines = [l[1:] for l in lines if l.startswith('+') and not l.startswith('+++')]
        
        # Check for overly long lines
        long_lines = [l for l in added_lines if len(l) > 100]
        if long_lines:
            concerns.append(f"{len(long_lines)} lines exceed 100 characters")
        
        # Check for nested complexity (rough heuristic)
        max_indent = 0
        for line in added_lines:
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent // 4)
        
        if max_indent > 4:
            concerns.append(f"Deep nesting detected (level {max_indent})")
        
        # Check for magic numbers
        import re
        magic_numbers = re.findall(r'[^\d](\d{2,})[^\d]', '\n'.join(added_lines))
        if len(magic_numbers) > 3:
            concerns.append(f"Multiple magic numbers detected: {magic_numbers[:3]}")
        
        # Check for proper docstrings in functions/classes
        if 'def ' in proposal.diff or 'class ' in proposal.diff:
            if '"""' not in proposal.diff and "'''" not in proposal.diff:
                concerns.append("Missing docstrings for new functions/classes")
        
        approve = len(concerns) <= 1  # Allow one minor issue
        confidence = 0.8 - (len(concerns) * 0.15)
        confidence = max(0.3, confidence)
        
        rationale = "Code is clean and readable" if approve else f"Elegance issues: {concerns[0]}"
        
        return self._make_vote(approve, confidence, rationale, concerns)


class DharmicReviewer(BaseReviewer):
    """Reviews for telos alignment and ahimsa (non-harm) principles."""
    
    reviewer_type = ReviewerType.DHARMIC
    
    HARM_INDICATORS = [
        'delete', 'destroy', 'kill', 'terminate', 'force', 'override',
        'bypass', 'disable_safety', 'ignore_error', 'skip_validation'
    ]
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff_lower = proposal.diff.lower()
        
        # Check for harm indicators
        for indicator in self.HARM_INDICATORS:
            if indicator in diff_lower:
                # Context matters - not all uses are harmful
                if f'# safe: {indicator}' not in diff_lower:
                    concerns.append(f"Potential harm indicator: {indicator}")
        
        # Check for irreversible operations
        irreversible = ['drop table', 'truncate', 'rm -rf', 'shutil.rmtree']
        for op in irreversible:
            if op in diff_lower:
                concerns.append(f"Irreversible operation: {op}")
        
        # Check if rationale mentions user benefit
        rationale_lower = proposal.rationale.lower()
        beneficial_terms = ['improve', 'fix', 'enhance', 'safer', 'clearer', 'better']
        has_beneficial_intent = any(term in rationale_lower for term in beneficial_terms)
        
        if not has_beneficial_intent:
            concerns.append("Rationale doesn't clearly state user benefit")
        
        approve = len(concerns) == 0
        confidence = 0.85 if approve else 0.4
        
        rationale = "Aligned with dharmic principles" if approve else f"Dharmic concerns: {concerns[0]}"
        
        return self._make_vote(approve, confidence, rationale, concerns)


class PerformanceReviewer(BaseReviewer):
    """Reviews for efficiency and performance regressions."""
    
    reviewer_type = ReviewerType.PERFORMANCE
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff_lower = proposal.diff.lower()
        
        # Check for nested loops
        loop_count = diff_lower.count('for ') + diff_lower.count('while ')
        if loop_count >= 3:
            concerns.append(f"Multiple loops detected ({loop_count}), potential O(n²) or worse")
        
        # Check for inefficient patterns
        inefficient = [
            ('list(' , 'in list(', 'Iterating over list() instead of generator'),
            ('.append(' , 'for.*append', 'Consider list comprehension instead of append loop'),
            ('+ ', "str.*\\+.*str", 'String concatenation in loop, consider join()'),
        ]
        
        for pattern, _, message in inefficient:
            if pattern in diff_lower:
                concerns.append(message)
        
        # Check for unbounded operations
        if 'while true' in diff_lower and 'break' not in diff_lower:
            concerns.append("Infinite loop without clear exit")
        
        # Check for blocking calls
        blocking = ['time.sleep', 'requests.get', 'requests.post', 'urlopen']
        for call in blocking:
            if call in diff_lower:
                concerns.append(f"Blocking call detected: {call}")
        
        approve = len(concerns) <= 1
        confidence = 0.75 - (len(concerns) * 0.1)
        confidence = max(0.3, confidence)
        
        rationale = "No major performance issues" if approve else f"Performance concern: {concerns[0]}"
        
        return self._make_vote(approve, confidence, rationale, concerns)


class CorrectnessReviewer(BaseReviewer):
    """Reviews for logical correctness and edge case handling."""
    
    reviewer_type = ReviewerType.CORRECTNESS
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff = proposal.diff
        diff_lower = diff.lower()
        
        # Check for missing None checks
        if '.' in diff and 'if ' not in diff_lower and 'none' not in diff_lower:
            if 'optional' in diff_lower or '| none' in diff_lower:
                concerns.append("Optional type used but no None check visible")
        
        # Check for off-by-one risks
        if 'range(' in diff and '[' in diff:
            concerns.append("Array indexing with range - verify bounds")
        
        # Check for comparison issues
        if ' is ' in diff and ("'" in diff or '"' in diff):
            concerns.append("Using 'is' with string literal - should use '=='")
        
        # Check for mutable default arguments
        import re
        mutable_defaults = re.findall(r'def \w+\([^)]*=\s*(\[\]|\{\})', diff)
        if mutable_defaults:
            concerns.append("Mutable default argument detected")
        
        # Check for exception handling
        if 'except:' in diff or 'except Exception:' in diff:
            if 'pass' in diff or '...' in diff:
                concerns.append("Bare except with pass - errors may be silently ignored")
        
        approve = len(concerns) <= 1
        confidence = 0.8 - (len(concerns) * 0.12)
        confidence = max(0.35, confidence)
        
        rationale = "Logic appears correct" if approve else f"Correctness concern: {concerns[0]}"
        
        return self._make_vote(approve, confidence, rationale, concerns)


class MinimalChangeReviewer(BaseReviewer):
    """Reviews for diff size and necessity of changes."""
    
    reviewer_type = ReviewerType.MINIMAL_CHANGE
    
    MAX_PREFERRED_LINES = 100
    MAX_ALLOWED_LINES = 500
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff_lines = proposal.diff_lines
        
        # Check diff size
        if diff_lines > self.MAX_ALLOWED_LINES:
            concerns.append(f"Diff too large ({diff_lines} lines) - consider splitting")
        elif diff_lines > self.MAX_PREFERRED_LINES:
            concerns.append(f"Large diff ({diff_lines} lines) - review carefully")
        
        # Check for unrelated changes
        lines = proposal.diff.split('\n')
        files_changed = [l for l in lines if l.startswith('+++') or l.startswith('---')]
        if len(files_changed) > 6:  # More than 3 files
            concerns.append(f"Changes span {len(files_changed)//2} files - may not be atomic")
        
        # Check if description matches diff
        desc_words = set(proposal.description.lower().split())
        if len(desc_words) < 3:
            concerns.append("Description too brief to verify necessity")
        
        approve = diff_lines <= self.MAX_ALLOWED_LINES and len(concerns) <= 1
        confidence = 0.9 if diff_lines < 50 else (0.7 if diff_lines < 200 else 0.5)
        
        rationale = f"Change is minimal ({diff_lines} lines)" if approve else concerns[0]
        
        return self._make_vote(approve, confidence, rationale, concerns)


class TestReviewer(BaseReviewer):
    """Reviews for test coverage and test quality."""
    
    reviewer_type = ReviewerType.TEST
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff = proposal.diff
        diff_lower = diff.lower()
        
        # Check if tests are included
        has_tests = 'def test_' in diff_lower or 'test_' in proposal.component.lower()
        adds_functionality = 'def ' in diff and 'test_' not in diff_lower
        
        if adds_functionality and not has_tests:
            concerns.append("New functionality without corresponding tests")
        
        # Check for assertion quality
        if has_tests:
            if 'assert ' not in diff and 'self.assert' not in diff_lower:
                concerns.append("Test present but no assertions found")
            
            # Check for meaningful assertions
            if 'assert true' in diff_lower or 'assert false' in diff_lower:
                concerns.append("Trivial assertions detected")
        
        # Check for test isolation
        if 'global ' in diff_lower and 'test_' in diff_lower:
            concerns.append("Tests may not be isolated (global state)")
        
        approve = len(concerns) == 0 or not adds_functionality
        confidence = 0.85 if has_tests and not concerns else 0.5
        
        rationale = "Test coverage adequate" if approve else f"Test issue: {concerns[0]}"
        
        return self._make_vote(approve, confidence, rationale, concerns)


class ArchitectureReviewer(BaseReviewer):
    """Reviews for system design fit and architectural consistency."""
    
    reviewer_type = ReviewerType.ARCHITECTURE
    
    async def review(self, proposal: MutationProposal) -> Vote:
        concerns = []
        diff = proposal.diff
        diff_lower = diff.lower()
        
        # Check for circular import risks
        if 'from ' in diff and 'import ' in diff:
            imports = [l for l in diff.split('\n') if 'import' in l.lower()]
            if len(imports) > 5:
                concerns.append("Many imports - check for circular dependencies")
        
        # Check for proper layering
        if 'src/core' in proposal.component:
            if 'from src.dgm' in diff or 'from dgm' in diff:
                concerns.append("Core module importing from dgm - inverted dependency")
        
        # Check for god objects
        class_methods = diff_lower.count('def ') 
        if class_methods > 15:
            concerns.append(f"Class may be too large ({class_methods} methods)")
        
        # Check for proper encapsulation
        if diff_lower.count('._') > 5:  # Accessing private members
            concerns.append("Multiple private member accesses - encapsulation concern")
        
        # Check component naming
        if proposal.component and not proposal.component.endswith('.py'):
            if '/' not in proposal.component:
                concerns.append("Component path unclear")
        
        approve = len(concerns) <= 1
        confidence = 0.75 - (len(concerns) * 0.1)
        confidence = max(0.4, confidence)
        
        rationale = "Fits system architecture" if approve else f"Architecture concern: {concerns[0]}"
        
        return self._make_vote(approve, confidence, rationale, concerns)


# =============================================================================
# Voting Swarm
# =============================================================================

class VotingSwarm:
    """
    Orchestrates diverse reviewers to vote on mutation proposals.
    
    Enforces:
    - Minimum vote count (default 25)
    - Minimum approval ratio (default 80%)
    - Minimum diversity score (default 0.7)
    - Maximum votes per reviewer type (default 5)
    """
    
    # All available reviewer classes
    REVIEWER_CLASSES = {
        ReviewerType.SECURITY: SecurityReviewer,
        ReviewerType.ELEGANCE: EleganceReviewer,
        ReviewerType.DHARMIC: DharmicReviewer,
        ReviewerType.PERFORMANCE: PerformanceReviewer,
        ReviewerType.CORRECTNESS: CorrectnessReviewer,
        ReviewerType.MINIMAL_CHANGE: MinimalChangeReviewer,
        ReviewerType.TEST: TestReviewer,
        ReviewerType.ARCHITECTURE: ArchitectureReviewer,
    }
    
    # Thresholds
    DEFAULT_REQUIRED_VOTES = 25
    DEFAULT_APPROVAL_THRESHOLD = 0.80
    DEFAULT_DIVERSITY_THRESHOLD = 0.70
    DEFAULT_MAX_VOTES_PER_TYPE = 5
    
    def __init__(
        self,
        approval_threshold: float = DEFAULT_APPROVAL_THRESHOLD,
        diversity_threshold: float = DEFAULT_DIVERSITY_THRESHOLD,
        max_votes_per_type: int = DEFAULT_MAX_VOTES_PER_TYPE,
    ):
        self.approval_threshold = approval_threshold
        self.diversity_threshold = diversity_threshold
        self.max_votes_per_type = max_votes_per_type
        self._reviewer_counter = 0
    
    def _create_reviewer(self, reviewer_type: ReviewerType) -> BaseReviewer:
        """Create a reviewer instance with unique ID."""
        self._reviewer_counter += 1
        reviewer_id = f"{reviewer_type.value}_{self._reviewer_counter}"
        reviewer_class = self.REVIEWER_CLASSES[reviewer_type]
        return reviewer_class(reviewer_id)
    
    def _spawn_reviewers(self, required_votes: int) -> List[BaseReviewer]:
        """
        Spawn diverse reviewers ensuring type distribution.
        
        Distributes reviewers across types to maximize diversity
        while respecting max_votes_per_type constraint.
        """
        reviewers = []
        type_counts = Counter()
        available_types = list(ReviewerType)
        
        while len(reviewers) < required_votes:
            # Shuffle types for fairness
            random.shuffle(available_types)
            
            for rtype in available_types:
                if type_counts[rtype] < self.max_votes_per_type:
                    reviewers.append(self._create_reviewer(rtype))
                    type_counts[rtype] += 1
                    
                    if len(reviewers) >= required_votes:
                        break
            
            # Safety check - if we can't add more reviewers
            if all(type_counts[t] >= self.max_votes_per_type for t in available_types):
                break
        
        return reviewers
    
    def _calculate_diversity_score(self, votes: List[Vote]) -> float:
        """
        Calculate diversity score based on vote distribution.
        
        Score is based on Shannon entropy normalized to [0, 1].
        Higher score = more evenly distributed votes across types.
        """
        if not votes:
            return 0.0
        
        type_counts = Counter(v.reviewer_type for v in votes)
        total = len(votes)
        num_types = len(ReviewerType)
        
        # Calculate normalized entropy
        import math
        entropy = 0.0
        for count in type_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalize by max entropy (uniform distribution)
        max_entropy = math.log2(min(num_types, total))
        if max_entropy > 0:
            return entropy / max_entropy
        return 1.0 if len(type_counts) == 1 else 0.0
    
    async def collect_votes(
        self,
        proposal: MutationProposal,
        required_votes: int = DEFAULT_REQUIRED_VOTES,
    ) -> VoteResult:
        """
        Collect votes from diverse reviewers on a proposal.
        
        Args:
            proposal: The mutation proposal to review
            required_votes: Minimum number of votes needed (default 25)
            
        Returns:
            VoteResult with approval status and details
        """
        # Spawn diverse reviewers
        reviewers = self._spawn_reviewers(required_votes)
        
        # Collect votes concurrently
        vote_tasks = [reviewer.review(proposal) for reviewer in reviewers]
        votes = await asyncio.gather(*vote_tasks)
        
        # Calculate metrics
        total_votes = len(votes)
        approvals = sum(1 for v in votes if v.approve)
        approval_ratio = approvals / total_votes if total_votes > 0 else 0.0
        diversity_score = self._calculate_diversity_score(votes)
        
        # Collect dissenting opinions (from disapproving votes)
        dissenting_opinions = [
            f"[{v.reviewer_type.value}] {v.rationale}"
            for v in votes if not v.approve
        ]
        
        # Determine approval and rejection reasons
        rejection_reasons = []
        
        if total_votes < required_votes:
            rejection_reasons.append(f"Insufficient votes ({total_votes}/{required_votes})")
        
        if approval_ratio < self.approval_threshold:
            rejection_reasons.append(
                f"Approval too low ({approval_ratio:.1%} < {self.approval_threshold:.1%})"
            )
        
        if diversity_score < self.diversity_threshold:
            rejection_reasons.append(
                f"Diversity too low ({diversity_score:.2f} < {self.diversity_threshold:.2f})"
            )
        
        approved = len(rejection_reasons) == 0
        
        return VoteResult(
            approved=approved,
            total_votes=total_votes,
            approval_ratio=approval_ratio,
            diversity_score=diversity_score,
            dissenting_opinions=dissenting_opinions,
            votes=list(votes),
            rejection_reasons=rejection_reasons,
        )
    
    async def quick_vote(
        self,
        proposal: MutationProposal,
        required_votes: int = 9,  # Faster for small changes
    ) -> VoteResult:
        """
        Quick vote with fewer reviewers for minor changes.
        
        Uses lower vote count but maintains diversity requirements.
        """
        return await self.collect_votes(proposal, required_votes=required_votes)


# =============================================================================
# Convenience Functions
# =============================================================================

async def vote_on_proposal(
    proposal: MutationProposal,
    required_votes: int = 25,
) -> VoteResult:
    """
    Convenience function to vote on a proposal.
    
    Creates a VotingSwarm and collects votes.
    """
    swarm = VotingSwarm()
    return await swarm.collect_votes(proposal, required_votes=required_votes)


def create_proposal(
    component: str,
    description: str,
    diff: str,
    rationale: str,
    proposal_id: str = None,
) -> MutationProposal:
    """
    Convenience function to create a proposal.
    """
    import uuid
    return MutationProposal(
        id=proposal_id or str(uuid.uuid4())[:8],
        component=component,
        description=description,
        diff=diff,
        rationale=rationale,
    )


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    
    # Example usage
    async def main():
        proposal = create_proposal(
            component="src/dgm/example.py",
            description="Add input validation to user handler",
            diff="""
+def validate_input(data: str) -> bool:
+    \"\"\"Validate user input for safety.\"\"\"
+    if not data or len(data) > 1000:
+        return False
+    return True
+
 def handle_user(data: str):
+    if not validate_input(data):
+        raise ValueError("Invalid input")
     process(data)
""",
            rationale="Improve security by adding input validation",
        )
        
        print("Testing VotingSwarm...")
        print(f"Proposal: {proposal.description}")
        print(f"Diff lines: {proposal.diff_lines}")
        print()
        
        swarm = VotingSwarm()
        result = await swarm.collect_votes(proposal)
        
        print(result.summary())
        print()
        
        # Show vote breakdown by type
        from collections import Counter
        type_votes = Counter()
        type_approvals = Counter()
        for vote in result.votes:
            type_votes[vote.reviewer_type.value] += 1
            if vote.approve:
                type_approvals[vote.reviewer_type.value] += 1
        
        print("Vote breakdown by type:")
        for rtype in sorted(type_votes.keys()):
            total = type_votes[rtype]
            approved = type_approvals[rtype]
            print(f"  {rtype}: {approved}/{total} approved")
    
    asyncio.run(main())
