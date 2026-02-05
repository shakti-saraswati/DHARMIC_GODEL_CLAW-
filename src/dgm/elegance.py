"""
elegance.py — Code Quality & Bloat Detection

Evaluates code changes for elegance, penalizing bloat and complexity growth.
"""

from __future__ import annotations

import ast
import difflib
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import Counter


@dataclass
class EleganceScore:
    """Result of elegance evaluation."""
    total: float  # 0-1, higher is better
    breakdown: Dict[str, float] = field(default_factory=dict)
    concerns: List[str] = field(default_factory=list)
    is_bloated: bool = False
    
    def __post_init__(self):
        # Ensure total is clamped
        self.total = max(0.0, min(1.0, self.total))


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity by counting decision points."""
    
    def __init__(self):
        self.complexity = 1  # Base complexity
        
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds a decision point
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
        
    def visit_comprehension(self, node):
        self.complexity += 1
        # Count 'if' clauses in comprehension
        self.complexity += len(node.ifs)
        self.generic_visit(node)
        
    def visit_IfExp(self, node):
        # Ternary operator
        self.complexity += 1
        self.generic_visit(node)


class EleganceEvaluator:
    """
    Evaluates code changes for elegance and bloat.
    
    Philosophy: Good code is minimal, clear, and focused.
    Bloat is the enemy of maintainability.
    """
    
    # Weights for final score (must sum to 1.0)
    WEIGHTS = {
        'diff_size': 0.20,
        'complexity_delta': 0.25,
        'line_count_delta': 0.15,
        'import_bloat': 0.10,
        'duplication': 0.15,
        'naming_quality': 0.15,
    }
    
    # Thresholds
    BLOAT_LINE_THRESHOLD = 100  # Lines added triggers bloat check
    COMPLEXITY_INCREASE_THRESHOLD = 0.20  # 20% complexity increase = bloat
    REJECT_SCORE_THRESHOLD = 0.5
    
    def __init__(self):
        # Configurable thresholds
        self.max_diff_lines = 200  # Ideal max diff size
        self.max_line_growth = 50  # Flag if >50 lines added
        
    def evaluate(self, original: str, modified: str, diff: str) -> EleganceScore:
        """
        Evaluate code change elegance.
        
        Args:
            original: Original source code
            modified: Modified source code
            diff: Unified diff string
            
        Returns:
            EleganceScore with total, breakdown, concerns, is_bloated
        """
        concerns: List[str] = []
        breakdown: Dict[str, float] = {}
        
        # Parse ASTs (handle parse failures gracefully)
        orig_ast = self._safe_parse(original)
        mod_ast = self._safe_parse(modified)
        
        # Calculate individual metrics
        breakdown['diff_size'] = self._score_diff_size(diff, concerns)
        breakdown['complexity_delta'] = self._score_complexity_delta(
            orig_ast, mod_ast, concerns
        )
        breakdown['line_count_delta'] = self._score_line_count_delta(
            original, modified, concerns
        )
        breakdown['import_bloat'] = self._score_import_bloat(
            orig_ast, mod_ast, concerns
        )
        breakdown['duplication'] = self._score_duplication(modified, concerns)
        breakdown['naming_quality'] = self._score_naming_quality(mod_ast, concerns)
        
        # Calculate weighted total
        total = sum(
            breakdown[key] * self.WEIGHTS[key]
            for key in self.WEIGHTS
        )
        
        # Determine bloat status
        is_bloated = self._check_bloat(
            original, modified, diff, 
            breakdown.get('complexity_delta', 1.0),
            concerns
        )
        
        return EleganceScore(
            total=total,
            breakdown=breakdown,
            concerns=concerns,
            is_bloated=is_bloated,
        )
    
    def _safe_parse(self, code: str) -> Optional[ast.AST]:
        """Parse code, return None on failure."""
        if not code or not code.strip():
            return None
        try:
            return ast.parse(code)
        except SyntaxError:
            return None
    
    def _score_diff_size(self, diff: str, concerns: List[str]) -> float:
        """
        Score based on diff size. Smaller is better.
        
        Returns 1.0 for minimal diffs, decreasing as diff grows.
        """
        if not diff:
            return 1.0
            
        # Count actual change lines (+ and - at start)
        change_lines = sum(
            1 for line in diff.splitlines()
            if line.startswith('+') or line.startswith('-')
        )
        # Exclude diff headers
        change_lines = max(0, change_lines - 4)  # Rough header adjustment
        
        if change_lines > self.max_diff_lines:
            concerns.append(
                f"Large diff: {change_lines} change lines (prefer <{self.max_diff_lines})"
            )
            
        # Sigmoid-like scoring: 1.0 at 0, ~0.5 at max_diff_lines, approaches 0
        score = 1.0 / (1.0 + (change_lines / self.max_diff_lines) ** 1.5)
        return score
    
    def _score_complexity_delta(
        self, 
        orig_ast: Optional[ast.AST], 
        mod_ast: Optional[ast.AST],
        concerns: List[str]
    ) -> float:
        """
        Score complexity change. Lower/same complexity is better.
        
        Returns 1.0 if complexity decreased or stayed same,
        decreasing as complexity increases.
        """
        if orig_ast is None and mod_ast is None:
            return 0.5  # Can't evaluate
        if orig_ast is None:
            # New code - just check absolute complexity
            mod_complexity = self._calculate_complexity(mod_ast)
            # Penalty for high absolute complexity
            return max(0.2, 1.0 - (mod_complexity / 50))
        if mod_ast is None:
            return 0.3  # Modified code doesn't parse - bad
            
        orig_complexity = self._calculate_complexity(orig_ast)
        mod_complexity = self._calculate_complexity(mod_ast)
        
        if orig_complexity == 0:
            orig_complexity = 1  # Avoid division by zero
            
        delta = mod_complexity - orig_complexity
        ratio = delta / orig_complexity
        
        if ratio > self.COMPLEXITY_INCREASE_THRESHOLD:
            concerns.append(
                f"Complexity increased by {ratio*100:.1f}% "
                f"({orig_complexity} → {mod_complexity})"
            )
            
        if delta <= 0:
            return 1.0  # Complexity decreased or same
        elif ratio <= 0.1:
            return 0.9  # Minor increase
        elif ratio <= 0.2:
            return 0.7  # Moderate increase
        elif ratio <= 0.5:
            return 0.4  # Significant increase
        else:
            return 0.2  # Major bloat
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate total cyclomatic complexity."""
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        return visitor.complexity
    
    def _score_line_count_delta(
        self, 
        original: str, 
        modified: str,
        concerns: List[str]
    ) -> float:
        """
        Score line count change. Flag excessive growth.
        
        Returns 1.0 for deletions/small additions, decreasing with growth.
        """
        orig_lines = len(original.splitlines()) if original else 0
        mod_lines = len(modified.splitlines()) if modified else 0
        
        delta = mod_lines - orig_lines
        
        if delta > self.max_line_growth:
            concerns.append(
                f"Added {delta} lines (threshold: {self.max_line_growth})"
            )
            
        if delta <= 0:
            return 1.0  # Removed or same
        elif delta <= 20:
            return 0.95
        elif delta <= 50:
            return 0.8
        elif delta <= 100:
            return 0.5
        else:
            return max(0.1, 0.5 - (delta - 100) / 500)
    
    def _score_import_bloat(
        self,
        orig_ast: Optional[ast.AST],
        mod_ast: Optional[ast.AST],
        concerns: List[str]
    ) -> float:
        """
        Score import growth. Unnecessary imports are bloat.
        
        Returns 1.0 if imports decreased or stayed same.
        """
        orig_imports = self._extract_imports(orig_ast) if orig_ast else set()
        mod_imports = self._extract_imports(mod_ast) if mod_ast else set()
        
        new_imports = mod_imports - orig_imports
        removed_imports = orig_imports - mod_imports
        
        # Net import growth
        net_growth = len(new_imports) - len(removed_imports)
        
        if net_growth > 3:
            concerns.append(
                f"Added {len(new_imports)} new imports: {', '.join(sorted(new_imports)[:5])}"
            )
            
        if net_growth <= 0:
            return 1.0
        elif net_growth <= 2:
            return 0.9
        elif net_growth <= 5:
            return 0.7
        else:
            return max(0.3, 1.0 - net_growth * 0.1)
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract all imported module names."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports
    
    def _score_duplication(self, code: str, concerns: List[str]) -> float:
        """
        Detect copy-paste patterns and code duplication.
        
        Returns 1.0 for no duplication, decreasing with repeated patterns.
        """
        if not code:
            return 1.0
            
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        
        # Find repeated non-trivial lines (>10 chars)
        line_counts = Counter(
            line for line in lines 
            if len(line) > 10 and not line.startswith('#')
        )
        
        duplicated_lines = sum(
            count - 1 for count in line_counts.values() if count > 1
        )
        
        # Find repeated code blocks (3+ consecutive similar lines)
        block_duplicates = self._find_duplicate_blocks(lines)
        
        total_duplication = duplicated_lines + block_duplicates * 3
        
        if total_duplication > 5:
            concerns.append(
                f"Detected {duplicated_lines} duplicate lines, "
                f"{block_duplicates} duplicate blocks"
            )
            
        if total_duplication == 0:
            return 1.0
        elif total_duplication <= 3:
            return 0.9
        elif total_duplication <= 10:
            return 0.7
        else:
            return max(0.2, 1.0 - total_duplication * 0.05)
    
    def _find_duplicate_blocks(self, lines: List[str], block_size: int = 3) -> int:
        """Find repeated consecutive line blocks."""
        if len(lines) < block_size * 2:
            return 0
            
        blocks = []
        for i in range(len(lines) - block_size + 1):
            block = tuple(lines[i:i + block_size])
            # Skip trivial blocks (all short lines)
            if all(len(line) < 15 for line in block):
                continue
            blocks.append(block)
            
        block_counts = Counter(blocks)
        return sum(count - 1 for count in block_counts.values() if count > 1)
    
    def _score_naming_quality(
        self, 
        tree: Optional[ast.AST],
        concerns: List[str]
    ) -> float:
        """
        Evaluate naming quality: length, clarity, consistency.
        
        Returns 1.0 for excellent naming, decreasing with issues.
        """
        if tree is None:
            return 0.5
            
        issues = []
        names: List[str] = []
        
        for node in ast.walk(tree):
            # Function names
            if isinstance(node, ast.FunctionDef):
                name = node.name
                names.append(name)
                if len(name) == 1 and name not in ('_',):
                    issues.append(f"Single-letter function: {name}")
                elif len(name) > 40:
                    issues.append(f"Overly long function name: {name[:20]}...")
                    
            # Variable names in assignments
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                name = node.id
                names.append(name)
                if len(name) == 1 and name not in ('i', 'j', 'k', 'x', 'y', 'z', '_'):
                    issues.append(f"Cryptic variable: {name}")
                    
            # Class names
            elif isinstance(node, ast.ClassDef):
                name = node.name
                names.append(name)
                if not name[0].isupper():
                    issues.append(f"Class should be CamelCase: {name}")
        
        # Check consistency (all snake_case or mixed)
        func_names = [
            n for n in names 
            if not n.startswith('_') and n not in ('self', 'cls')
        ]
        snake_case = sum(1 for n in func_names if '_' in n or n.islower())
        camel_case = sum(1 for n in func_names if n[0].isupper() if n)
        
        if snake_case > 0 and camel_case > 3:
            issues.append("Inconsistent naming style (mixed snake_case and CamelCase)")
            
        if issues:
            concerns.extend(issues[:3])  # Limit reported issues
            
        # Score based on issue count
        issue_count = len(issues)
        if issue_count == 0:
            return 1.0
        elif issue_count <= 2:
            return 0.85
        elif issue_count <= 5:
            return 0.65
        else:
            return max(0.3, 1.0 - issue_count * 0.1)
    
    def _check_bloat(
        self,
        original: str,
        modified: str,
        diff: str,
        complexity_score: float,
        concerns: List[str]
    ) -> bool:
        """
        Determine if change is bloated based on thresholds.
        
        Bloat conditions:
        1. >100 lines added without proportional test coverage
        2. Complexity increased by >20%
        """
        orig_lines = len(original.splitlines()) if original else 0
        mod_lines = len(modified.splitlines()) if modified else 0
        lines_added = mod_lines - orig_lines
        
        # Check line threshold
        if lines_added > self.BLOAT_LINE_THRESHOLD:
            # Check for test coverage (look for test functions/assertions)
            test_indicators = (
                'def test_', 'assert ', 'self.assert', 
                'pytest', 'unittest', '@test'
            )
            test_lines = sum(
                1 for line in modified.splitlines()
                if any(ind in line for ind in test_indicators)
            )
            
            # Require at least 20% test coverage for large additions
            if test_lines < lines_added * 0.2:
                concerns.append(
                    f"Bloat: {lines_added} lines added with insufficient tests "
                    f"({test_lines} test lines)"
                )
                return True
                
        # Check complexity threshold (score < 0.7 means >20% increase)
        if complexity_score < 0.7:
            # Already logged in complexity scoring
            return True
            
        return False


def create_diff(original: str, modified: str) -> str:
    """Helper to create unified diff between two code strings."""
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        orig_lines, mod_lines,
        fromfile='original', tofile='modified',
        lineterm=''
    )
    return ''.join(diff)


def evaluate_elegance(original: str, modified: str, diff: str = None) -> EleganceScore:
    """
    Evaluate code change elegance.
    
    Args:
        original: Original source code
        modified: Modified source code  
        diff: Optional unified diff (generated if not provided)
        
    Returns:
        EleganceScore with total (0-1), breakdown, concerns, is_bloated
    """
    if diff is None:
        diff = create_diff(original, modified)
    
    evaluator = EleganceEvaluator()
    return evaluator.evaluate(original, modified, diff)
