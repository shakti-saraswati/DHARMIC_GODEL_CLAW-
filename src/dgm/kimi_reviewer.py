"""
# Suppress noisy httpx logging that conflicts with dharmic_logging
import logging as _logging
_logging.getLogger("httpx").setLevel(_logging.WARNING)

Kimi Reviewer — Deep Code Review with 128k Context
===================================================

Uses Moonshot's Kimi K2.5 model for comprehensive code review.
Unlike narrow-context reviewers, Kimi sees the WHOLE picture.

Key capability: 128k token context allows reviewing mutations
in the context of the entire codebase — catching conflicts,
architectural issues, and integration problems that smaller
models miss.

API: Moonshot at api.moonshot.ai (NOT api.moonshot.cn)
Model: moonshot/kimi-k2.5 (aliased as 'kimi' in Clawdbot)
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import logging

# Optional: Direct API via httpx/requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


logger = logging.getLogger(__name__)


# =============================================================================
# Data Types
# =============================================================================

@dataclass
class KimiReview:
    """
    Deep code review result from Kimi K2.5.
    
    Leverages 128k context to analyze mutations against the full codebase.
    
    Attributes:
        approved: Whether the mutation should proceed
        confidence: 0-1 confidence in the assessment
        issues: Problems found in the proposed code
        suggestions: Improvements to the proposal
        codebase_conflicts: Conflicts with existing code patterns/conventions
        architectural_concerns: Higher-level design problems
        overall_assessment: Human-readable summary
    """
    approved: bool
    confidence: float  # 0.0 - 1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    codebase_conflicts: List[str] = field(default_factory=list)
    architectural_concerns: List[str] = field(default_factory=list)
    overall_assessment: str = ""
    
    # Metadata
    model_used: str = "moonshot/kimi-k2.5"
    context_tokens_used: int = 0
    review_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate confidence bounds."""
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    @property
    def has_blockers(self) -> bool:
        """Check if there are blocking issues."""
        return len(self.issues) > 0 or len(self.codebase_conflicts) > 0
    
    @property
    def severity_score(self) -> float:
        """
        Calculate severity score (lower = worse).
        
        Factors:
        - Number of issues (heavy weight)
        - Architectural concerns (medium weight)
        - Codebase conflicts (heavy weight)
        """
        issue_penalty = len(self.issues) * 0.15
        conflict_penalty = len(self.codebase_conflicts) * 0.2
        arch_penalty = len(self.architectural_concerns) * 0.1
        
        score = 1.0 - issue_penalty - conflict_penalty - arch_penalty
        return max(0.0, min(1.0, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "approved": self.approved,
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "codebase_conflicts": self.codebase_conflicts,
            "architectural_concerns": self.architectural_concerns,
            "overall_assessment": self.overall_assessment,
            "model_used": self.model_used,
            "context_tokens_used": self.context_tokens_used,
            "review_timestamp": self.review_timestamp,
            "has_blockers": self.has_blockers,
            "severity_score": self.severity_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KimiReview":
        """Deserialize from dictionary."""
        return cls(
            approved=data.get("approved", False),
            confidence=float(data.get("confidence", 0.5)),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
            codebase_conflicts=data.get("codebase_conflicts", []),
            architectural_concerns=data.get("architectural_concerns", []),
            overall_assessment=data.get("overall_assessment", ""),
            model_used=data.get("model_used", "moonshot/kimi-k2.5"),
            context_tokens_used=data.get("context_tokens_used", 0),
            review_timestamp=data.get("review_timestamp", datetime.now().isoformat()),
        )
    
    def summary(self) -> str:
        """Human-readable summary."""
        status = "✅ APPROVED" if self.approved else "❌ REJECTED"
        lines = [
            f"{status} (confidence: {self.confidence:.0%})",
            f"  Issues: {len(self.issues)}",
            f"  Conflicts: {len(self.codebase_conflicts)}",
            f"  Architectural concerns: {len(self.architectural_concerns)}",
            f"  Suggestions: {len(self.suggestions)}",
        ]
        if self.overall_assessment:
            # Truncate long assessments
            assessment = self.overall_assessment[:200]
            if len(self.overall_assessment) > 200:
                assessment += "..."
            lines.append(f"  Assessment: {assessment}")
        return "\n".join(lines)


@dataclass
class MutationProposal:
    """
    Mutation proposal for review.
    
    Compatible with both voting.py and mutator.py MutationProposal types.
    """
    id: str
    component: str  # Target file path
    description: str
    diff: str
    rationale: str
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional fields from mutator.MutationProposal
    affected_files: List[str] = field(default_factory=list)
    mutation_type: str = "improve"
    risk_level: str = "low"
    
    @classmethod
    def from_voting_proposal(cls, proposal: Any) -> "MutationProposal":
        """Create from voting.MutationProposal."""
        return cls(
            id=getattr(proposal, "id", hashlib.sha256(str(proposal).encode()).hexdigest()[:12]),
            component=getattr(proposal, "component", ""),
            description=getattr(proposal, "description", ""),
            diff=getattr(proposal, "diff", ""),
            rationale=getattr(proposal, "rationale", ""),
            parent_id=getattr(proposal, "parent_id", None),
            metadata=getattr(proposal, "metadata", {}),
            affected_files=getattr(proposal, "affected_files", []),
            mutation_type=getattr(proposal, "mutation_type", "improve"),
            risk_level=getattr(proposal, "risk_level", "low"),
        )
    
    @classmethod
    def from_mutator_proposal(cls, proposal: Any, component: str = "") -> "MutationProposal":
        """Create from mutator.MutationProposal."""
        return cls(
            id=hashlib.sha256(proposal.diff.encode()).hexdigest()[:12] if hasattr(proposal, 'diff') else "unknown",
            component=component or (proposal.affected_files[0] if hasattr(proposal, 'affected_files') and proposal.affected_files else ""),
            description=getattr(proposal, "rationale", "")[:100],
            diff=getattr(proposal, "diff", ""),
            rationale=getattr(proposal, "rationale", ""),
            affected_files=getattr(proposal, "affected_files", []),
            mutation_type=getattr(proposal, "mutation_type", "improve"),
            risk_level=getattr(proposal, "risk_level", "low"),
        )


# =============================================================================
# Context Gathering
# =============================================================================

class ContextGatherer:
    """
    Gathers relevant codebase context for deep review.
    
    Collects:
    - Target file and its imports
    - Related files (same module, tests)
    - Dependency chain (who imports this?)
    - Type definitions and interfaces
    """
    
    # File extensions to consider
    PYTHON_EXTENSIONS = {".py", ".pyi"}
    
    # Maximum context size (roughly 100k tokens = ~400k chars)
    MAX_CONTEXT_CHARS = 400_000
    
    # Priority weights for different file types
    PRIORITY_WEIGHTS = {
        "target": 1.0,      # The file being modified
        "test": 0.9,        # Test files for the target
        "import": 0.8,      # Files imported by target
        "dependent": 0.7,   # Files that import target
        "sibling": 0.5,     # Same directory
        "related": 0.3,     # Related by name/pattern
    }
    
    def __init__(self, project_root: Path = None):
        """
        Initialize context gatherer.
        
        Args:
            project_root: Root of the project to analyze
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self._import_cache: Dict[str, Set[str]] = {}
    
    def gather_context(
        self,
        target_file: str,
        max_chars: int = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Gather relevant context for reviewing changes to target_file.
        
        Args:
            target_file: Path to the file being modified
            max_chars: Maximum characters to include
            
        Returns:
            Tuple of (context_string, metadata)
        """
        max_chars = max_chars or self.MAX_CONTEXT_CHARS
        
        target_path = self._resolve_path(target_file)
        if not target_path.exists():
            logger.warning(f"Target file not found: {target_file}")
            return "", {"error": f"Target not found: {target_file}"}
        
        # Collect files with priorities
        files_to_include: Dict[Path, Tuple[float, str]] = {}
        
        # 1. Target file (always include)
        files_to_include[target_path] = (self.PRIORITY_WEIGHTS["target"], "target")
        
        # 2. Find test files
        test_files = self._find_test_files(target_path)
        for tf in test_files:
            files_to_include[tf] = (self.PRIORITY_WEIGHTS["test"], "test")
        
        # 3. Find imports (what does target depend on?)
        imports = self._extract_imports(target_path)
        for imp_path in imports:
            if imp_path.exists() and imp_path not in files_to_include:
                files_to_include[imp_path] = (self.PRIORITY_WEIGHTS["import"], "import")
        
        # 4. Find dependents (who imports target?)
        dependents = self._find_dependents(target_path)
        for dep_path in dependents:
            if dep_path not in files_to_include:
                files_to_include[dep_path] = (self.PRIORITY_WEIGHTS["dependent"], "dependent")
        
        # 5. Sibling files (same directory)
        siblings = self._find_siblings(target_path)
        for sib_path in siblings:
            if sib_path not in files_to_include:
                files_to_include[sib_path] = (self.PRIORITY_WEIGHTS["sibling"], "sibling")
        
        # Sort by priority and pack into context
        sorted_files = sorted(
            files_to_include.items(),
            key=lambda x: (-x[1][0], str(x[0]))  # Descending priority, then alphabetical
        )
        
        context_parts = []
        total_chars = 0
        included_files = []
        
        for file_path, (priority, file_type) in sorted_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.debug(f"Could not read {file_path}: {e}")
                continue
            
            # Calculate relative path for display
            try:
                rel_path = file_path.relative_to(self.project_root)
            except ValueError:
                rel_path = file_path
            
            # Format file section
            file_section = f"\n\n{'='*60}\n# FILE: {rel_path} ({file_type})\n{'='*60}\n{content}"
            
            # Check if we'd exceed limit
            if total_chars + len(file_section) > max_chars:
                # Try truncating this file
                remaining = max_chars - total_chars - 200  # Leave room for header
                if remaining > 1000:  # Only include if meaningful
                    truncated = content[:remaining] + "\n\n... [TRUNCATED]"
                    file_section = f"\n\n{'='*60}\n# FILE: {rel_path} ({file_type}) [TRUNCATED]\n{'='*60}\n{truncated}"
                    context_parts.append(file_section)
                    included_files.append({"path": str(rel_path), "type": file_type, "truncated": True})
                break
            
            context_parts.append(file_section)
            total_chars += len(file_section)
            included_files.append({"path": str(rel_path), "type": file_type, "truncated": False})
        
        context_string = "".join(context_parts)
        
        metadata = {
            "target_file": str(target_file),
            "files_included": len(included_files),
            "total_chars": len(context_string),
            "estimated_tokens": len(context_string) // 4,  # Rough estimate
            "included_files": included_files,
        }
        
        return context_string, metadata
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path relative to project root."""
        path = Path(file_path)
        if path.is_absolute():
            return path
        return self.project_root / path
    
    def _find_test_files(self, target_path: Path) -> List[Path]:
        """Find test files for a given target."""
        test_files = []
        
        # Get the module name
        stem = target_path.stem
        
        # Common test file patterns
        test_patterns = [
            f"test_{stem}.py",
            f"{stem}_test.py",
            f"tests/test_{stem}.py",
            f"tests/{stem}_test.py",
        ]
        
        # Check in project root and relative to target
        for pattern in test_patterns:
            for base in [self.project_root, target_path.parent, target_path.parent.parent]:
                candidate = base / pattern
                if candidate.exists():
                    test_files.append(candidate)
        
        # Also check tests/ directory at project root
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.glob(f"*{stem}*.py"):
                if test_file not in test_files:
                    test_files.append(test_file)
        
        return test_files
    
    def _extract_imports(self, file_path: Path) -> List[Path]:
        """Extract local imports from a Python file."""
        if file_path in self._import_cache:
            return [self._resolve_import(imp) for imp in self._import_cache[file_path] if self._resolve_import(imp)]
        
        imports: Set[str] = set()
        
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
        except Exception:
            return []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        
        self._import_cache[file_path] = imports
        
        resolved = []
        for imp in imports:
            resolved_path = self._resolve_import(imp, file_path)
            if resolved_path:
                resolved.append(resolved_path)
        
        return resolved
    
    def _resolve_import(self, import_name: str, source_file: Path = None) -> Optional[Path]:
        """Resolve an import name to a file path."""
        # Try relative to source file
        if source_file:
            rel_path = source_file.parent / f"{import_name}.py"
            if rel_path.exists():
                return rel_path
            
            # Try as package
            pkg_path = source_file.parent / import_name / "__init__.py"
            if pkg_path.exists():
                return pkg_path
        
        # Try relative to project root
        candidates = [
            self.project_root / f"{import_name}.py",
            self.project_root / import_name / "__init__.py",
            self.project_root / "src" / f"{import_name}.py",
            self.project_root / "src" / import_name / "__init__.py",
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return None
    
    def _find_dependents(self, target_path: Path) -> List[Path]:
        """Find files that import the target."""
        dependents = []
        target_module = target_path.stem
        
        # Search Python files in project
        for py_file in self.project_root.rglob("*.py"):
            if py_file == target_path:
                continue
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                # Quick check before full parse
                if target_module not in content:
                    continue
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if target_module in alias.name:
                                dependents.append(py_file)
                                break
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and target_module in node.module:
                            dependents.append(py_file)
                            break
            except Exception:
                continue
            
            if len(dependents) >= 10:  # Limit to prevent explosion
                break
        
        return dependents
    
    def _find_siblings(self, target_path: Path) -> List[Path]:
        """Find sibling Python files in same directory."""
        siblings = []
        for sibling in target_path.parent.glob("*.py"):
            if sibling != target_path and "__pycache__" not in str(sibling):
                siblings.append(sibling)
        return siblings[:5]  # Limit siblings


# =============================================================================
# Kimi API Client
# =============================================================================

class KimiAPIError(Exception):
    """Raised when Kimi API call fails."""
    pass


class KimiReviewer:
    """
    Deep code reviewer using Moonshot's Kimi K2.5.
    
    Leverages 128k context window for comprehensive review that
    understands the full codebase context.
    
    Supports two modes:
    1. Direct API (if MOONSHOT_API_KEY available)
    2. Clawdbot CLI fallback
    """
    
    # Moonshot API configuration
    API_BASE = "https://api.moonshot.ai/v1"
    MODEL = "moonshot-v1-128k"  # 128k context model
    
    # Alternative model names that might work
    ALTERNATIVE_MODELS = [
        "moonshot-v1-128k",
        "kimi-k2.5", 
        "moonshot/kimi-k2.5",
    ]
    
    def __init__(
        self,
        project_root: Path = None,
        api_key: str = None,
        clawdbot_path: str = "clawdbot",
        timeout: int = 180,
        max_context_chars: int = 400_000,
    ):
        """
        Initialize Kimi reviewer.
        
        Args:
            project_root: Root of the project for context gathering
            api_key: Moonshot API key (falls back to MOONSHOT_API_KEY env)
            clawdbot_path: Path to clawdbot CLI for fallback
            timeout: API timeout in seconds
            max_context_chars: Maximum characters for codebase context
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.api_key = api_key or os.environ.get("MOONSHOT_API_KEY")
        self.clawdbot_path = clawdbot_path
        self.timeout = timeout
        self.max_context_chars = max_context_chars
        
        self.context_gatherer = ContextGatherer(self.project_root)
        
        # Determine API mode
        self.use_direct_api = bool(self.api_key) and (HTTPX_AVAILABLE or REQUESTS_AVAILABLE)
        
        logger.info(f"KimiReviewer initialized (direct_api={self.use_direct_api})")
    
    def review_mutation(
        self,
        proposal: MutationProposal,
        codebase_context: str = None,
    ) -> KimiReview:
        """
        Review a mutation proposal with full codebase context.
        
        Args:
            proposal: The mutation proposal to review
            codebase_context: Pre-gathered context (optional, will gather if not provided)
            
        Returns:
            KimiReview with deep analysis
        """
        # Normalize proposal if needed
        if not isinstance(proposal, MutationProposal):
            if hasattr(proposal, "component"):
                proposal = MutationProposal.from_voting_proposal(proposal)
            else:
                proposal = MutationProposal.from_mutator_proposal(proposal)
        
        # Gather context if not provided
        context_metadata = {}
        if codebase_context is None:
            target = proposal.component or (proposal.affected_files[0] if proposal.affected_files else "")
            if target:
                codebase_context, context_metadata = self.context_gatherer.gather_context(
                    target, max_chars=self.max_context_chars
                )
            else:
                codebase_context = ""
        
        # Build review prompt
        prompt = self._build_review_prompt(proposal, codebase_context)
        
        # Call Kimi
        try:
            if self.use_direct_api:
                response = self._call_direct_api(prompt)
            else:
                response = self._call_clawdbot(prompt)
        except Exception as e:
            logger.error(f"Kimi API call failed: {e}")
            # Return a rejection on API failure
            return KimiReview(
                approved=False,
                confidence=0.0,
                issues=[f"API call failed: {str(e)}"],
                overall_assessment="Could not complete review due to API failure.",
            )
        
        # Parse response
        review = self._parse_review_response(response)
        
        # Add context metadata
        review.context_tokens_used = context_metadata.get("estimated_tokens", 0)
        
        return review
    
    def _build_review_prompt(self, proposal: MutationProposal, context: str) -> str:
        """Build the review prompt for Kimi."""
        prompt = f"""You are a senior code reviewer with FULL access to the codebase context.
Your task is to perform a DEEP review of the proposed mutation.

Unlike typical reviewers limited to just the diff, you can see:
- The complete file being modified
- Test files for this component
- Files that import this module
- Related modules in the same package

Use this context to catch issues that narrow-context reviewers miss!

# MUTATION PROPOSAL

## ID: {proposal.id}
## Component: {proposal.component}
## Type: {proposal.mutation_type}
## Risk Level: {proposal.risk_level}

## Description
{proposal.description}

## Rationale
{proposal.rationale}

## Diff
```diff
{proposal.diff}
```

## Affected Files
{', '.join(proposal.affected_files) if proposal.affected_files else proposal.component}

# CODEBASE CONTEXT
{context}

# YOUR REVIEW TASK

Analyze this mutation thoroughly. Consider:

1. **Correctness**: Does the change work as intended?
2. **Integration**: Does it conflict with existing patterns or code?
3. **Tests**: Will existing tests break? Are new tests needed?
4. **Dependencies**: Any issues with imports or dependencies?
5. **Architecture**: Does it fit the codebase's design philosophy?
6. **Edge Cases**: What could go wrong?
7. **Dharmic Alignment**: Is it non-harmful, truthful, orderly?

Be SPECIFIC. Reference actual code from the context.

# REQUIRED OUTPUT FORMAT (JSON)

```json
{{
    "approved": true/false,
    "confidence": 0.0-1.0,
    "issues": [
        "Specific issue 1 with reference to code",
        "Specific issue 2..."
    ],
    "suggestions": [
        "Concrete improvement suggestion 1",
        "..."
    ],
    "codebase_conflicts": [
        "Conflicts with existing pattern in file X",
        "..."
    ],
    "architectural_concerns": [
        "Concern about design decision",
        "..."
    ],
    "overall_assessment": "A 2-3 sentence summary of your review."
}}
```

Be thorough but fair. Approve if the benefits outweigh minor issues.
Reject if there are blocking problems or high-risk issues.
"""
        return prompt
    
    def _call_direct_api(self, prompt: str) -> str:
        """Call Moonshot API directly."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a meticulous senior code reviewer. Respond only with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower for more consistent reviews
            "max_tokens": 4096,
        }
        
        url = f"{self.API_BASE}/chat/completions"
        
        if HTTPX_AVAILABLE:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise KimiAPIError(f"API error {response.status_code}: {response.text}")
                data = response.json()
        elif REQUESTS_AVAILABLE:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if response.status_code != 200:
                raise KimiAPIError(f"API error {response.status_code}: {response.text}")
            data = response.json()
        else:
            raise KimiAPIError("No HTTP library available (install httpx or requests)")
        
        # Extract response content
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise KimiAPIError(f"Unexpected API response format: {e}")
    
    def _call_clawdbot(self, prompt: str) -> str:
        """Call Kimi via clawdbot CLI."""
        try:
            result = subprocess.run(
                [
                    self.clawdbot_path,
                    "ask",
                    "--model", "kimi",
                    "--no-stream",
                    prompt,
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode != 0:
                raise KimiAPIError(f"clawdbot failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise KimiAPIError(f"Clawdbot call timed out after {self.timeout}s")
        except FileNotFoundError:
            raise KimiAPIError(f"clawdbot not found at: {self.clawdbot_path}")
    
    def _parse_review_response(self, response: str) -> KimiReview:
        """Parse Kimi's response into a KimiReview."""
        # Extract JSON from response
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{[^{}]*"approved"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to find JSON anywhere in the response
                try:
                    # Find the first { and last }
                    start = response.index('{')
                    end = response.rindex('}') + 1
                    json_str = response[start:end]
                except ValueError:
                    logger.error(f"Could not extract JSON from response: {response[:500]}")
                    return KimiReview(
                        approved=False,
                        confidence=0.0,
                        issues=["Could not parse review response"],
                        overall_assessment=response[:500],
                    )
        
        try:
            data = json.loads(json_str)
            return KimiReview.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return KimiReview(
                approved=False,
                confidence=0.0,
                issues=[f"JSON parse error: {e}"],
                overall_assessment=response[:500],
            )
    
    def review(
        self,
        proposal: Any = None,
        circuit_result: Any = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Review a proposal - orchestrator-compatible interface.
        
        This is the main entry point called by DGM Orchestrator.
        Wraps review_mutation() and returns a dict format expected by orchestrator.
        
        Args:
            proposal: MutationProposal or similar object with component/diff
            circuit_result: Optional circuit evaluation result for context
            **kwargs: Additional context
            
        Returns:
            Dict with keys: approved, summary, reason, confidence, issues
        """
        if proposal is None:
            return {
                "approved": False,
                "reason": "No proposal provided",
                "summary": "Review skipped - no proposal",
                "confidence": 0.0,
                "issues": ["No proposal provided for review"],
            }
        
        # Convert to MutationProposal if needed
        if not isinstance(proposal, MutationProposal):
            try:
                proposal = MutationProposal.from_voting_proposal(proposal)
            except Exception:
                try:
                    proposal = MutationProposal.from_mutator_proposal(proposal)
                except Exception as e:
                    return {
                        "approved": False,
                        "reason": f"Could not parse proposal: {e}",
                        "summary": "Review failed - proposal format error",
                        "confidence": 0.0,
                        "issues": [str(e)],
                    }
        
        # Run the actual review
        try:
            kimi_review = self.review_mutation(proposal)
            
            # Convert KimiReview to dict format expected by orchestrator
            return {
                "approved": kimi_review.approved,
                "confidence": kimi_review.confidence,
                "summary": kimi_review.overall_assessment[:200] if kimi_review.overall_assessment else "Review complete",
                "reason": kimi_review.issues[0] if kimi_review.issues else None,
                "issues": kimi_review.issues,
                "suggestions": kimi_review.suggestions,
                "codebase_conflicts": kimi_review.codebase_conflicts,
                "architectural_concerns": kimi_review.architectural_concerns,
                "severity_score": kimi_review.severity_score,
                "has_blockers": kimi_review.has_blockers,
            }
        except Exception as e:
            logger.error(f"Review failed: {e}")
            return {
                "approved": True,  # Don't block on review failure
                "reason": f"Review error (non-blocking): {e}",
                "summary": "Review encountered an error but proceeding",
                "confidence": 0.0,
                "issues": [f"Review error: {e}"],
            }

    def quick_review(self, diff: str, file_path: str) -> KimiReview:
        """
        Quick review for a simple diff without full context gathering.
        
        Useful for rapid iteration or testing.
        
        Args:
            diff: The diff string
            file_path: Path to the file being modified
            
        Returns:
            KimiReview
        """
        proposal = MutationProposal(
            id=hashlib.sha256(diff.encode()).hexdigest()[:12],
            component=file_path,
            description="Quick review request",
            diff=diff,
            rationale="",
            affected_files=[file_path],
        )
        
        # Gather minimal context (just the target file)
        context, _ = self.context_gatherer.gather_context(
            file_path, max_chars=50_000
        )
        
        return self.review_mutation(proposal, context)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_reviewer(
    project_root: Path = None,
    api_key: str = None,
) -> KimiReviewer:
    """
    Factory function to create a KimiReviewer.
    
    Args:
        project_root: Optional project root path
        api_key: Optional API key (falls back to env)
        
    Returns:
        Configured KimiReviewer instance
    """
    return KimiReviewer(project_root=project_root, api_key=api_key)


def review_file_change(
    file_path: str,
    diff: str,
    project_root: Path = None,
) -> KimiReview:
    """
    Convenience function to review a file change.
    
    Args:
        file_path: Path to the file being changed
        diff: The diff string
        project_root: Optional project root
        
    Returns:
        KimiReview
    """
    reviewer = create_reviewer(project_root=project_root)
    return reviewer.quick_review(diff, file_path)


# =============================================================================
# Main (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Simple CLI for testing
    if len(sys.argv) < 2:
        print("Usage: python kimi_reviewer.py <file_path> [diff]")
        print("  Or:  python kimi_reviewer.py --test")
        sys.exit(1)
    
    if sys.argv[1] == "--test":
        # Self-test mode
        print("Running self-test...")
        
        # Create reviewer
        reviewer = create_reviewer()
        
        # Test context gathering
        gatherer = ContextGatherer()
        context, meta = gatherer.gather_context(__file__)
        print(f"Context gathered: {meta['files_included']} files, ~{meta['estimated_tokens']} tokens")
        
        # Test proposal creation
        test_proposal = MutationProposal(
            id="test-001",
            component=__file__,
            description="Test mutation",
            diff="+# Test change\n-# Old comment",
            rationale="Testing the reviewer",
        )
        
        print(f"Test proposal: {test_proposal.id}")
        print("Self-test passed!")
    else:
        file_path = sys.argv[1]
        diff = sys.argv[2] if len(sys.argv) > 2 else "+ # No diff provided"
        
        review = review_file_change(file_path, diff)
        print(review.summary())
        print("\nFull review:")
        print(json.dumps(review.to_dict(), indent=2))

# Suppress noisy httpx logging
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
