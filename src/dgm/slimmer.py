"""
Slimmer - Code Bloat Removal System
====================================
Identifies and removes unnecessary code bloat while preserving functionality.

"Perfection is achieved not when there is nothing more to add,
but when there is nothing left to take away." - Antoine de Saint-Exupéry

What counts as bloat:
- Dead code (unreachable, unused)
- Redundant imports
- Over-abstraction (classes that should be functions)
- Duplicate logic
- Excessive comments that restate the obvious
- Unnecessary type hints on obvious types

What is NOT bloat:
- Documentation (docstrings, important comments)
- Error handling (robust > minimal)
- Logging (observability is valuable)
- Type hints on complex types
"""
import ast
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BloatItem:
    """A piece of identified bloat."""
    category: str       # dead_code, redundant_import, over_abstraction, etc.
    description: str    # What's bloated
    location: str       # file:line
    severity: float     # 0.0-1.0, how bloated
    suggestion: str     # How to fix
    removable: bool     # Can it be auto-removed?
    code_snippet: Optional[str] = None


@dataclass
class SlimResult:
    """Result of slimming code."""
    original_code: str
    slimmed_code: str
    bloat_items: List[BloatItem] = field(default_factory=list)
    original_lines: int = 0
    slimmed_lines: int = 0
    bytes_removed: int = 0
    
    @property
    def bloat_score(self) -> float:
        """
        Calculate overall bloat score (0.0 = lean, 1.0 = bloated).
        
        Based on:
        - Ratio of bloat items to total lines
        - Severity of individual items
        - Reduction achieved
        """
        if not self.bloat_items:
            return 0.0
        
        # Factor 1: Item count relative to size
        item_ratio = len(self.bloat_items) / max(self.original_lines, 1)
        
        # Factor 2: Average severity
        avg_severity = sum(b.severity for b in self.bloat_items) / len(self.bloat_items)
        
        # Factor 3: Remaining bloat (after slimming)
        remaining_bloat = len([b for b in self.bloat_items if not b.removable])
        remaining_ratio = remaining_bloat / max(len(self.bloat_items), 1)
        
        # Combined score (weighted)
        score = (
            0.3 * min(item_ratio * 10, 1.0) +  # Cap item ratio contribution
            0.4 * avg_severity +
            0.3 * remaining_ratio
        )
        
        return min(score, 1.0)
    
    @property
    def reduction_percent(self) -> float:
        """Percentage of code removed."""
        if self.original_lines == 0:
            return 0.0
        return (1 - self.slimmed_lines / self.original_lines) * 100
    
    @property
    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Bloat score: {self.bloat_score:.2f} | "
            f"Lines: {self.original_lines} → {self.slimmed_lines} "
            f"(-{self.reduction_percent:.1f}%) | "
            f"Items: {len(self.bloat_items)} found, "
            f"{len([b for b in self.bloat_items if b.removable])} removable"
        )


class Slimmer:
    """
    Code slimming system.
    
    Analyzes code for bloat and optionally removes it.
    
    Usage:
        slimmer = Slimmer()
        result = await slimmer.slim(code)
        if result.bloat_score > 0.3:
            print("Too bloated!")
        else:
            use(result.slimmed_code)
    """
    
    def __init__(self, aggressive: bool = False):
        """
        Initialize the slimmer.
        
        Args:
            aggressive: If True, remove more aggressively (might break things)
        """
        self.aggressive = aggressive
    
    async def slim(self, code: str, filename: str = "unknown") -> SlimResult:
        """
        Analyze and slim code.
        
        Args:
            code: Source code to slim
            filename: File name for reporting
            
        Returns:
            SlimResult with original, slimmed code, and bloat items
        """
        original_lines = len(code.split('\n'))
        bloat_items = []
        
        # Run all bloat detectors
        bloat_items.extend(self._detect_dead_code(code, filename))
        bloat_items.extend(self._detect_redundant_imports(code, filename))
        bloat_items.extend(self._detect_over_abstraction(code, filename))
        bloat_items.extend(self._detect_duplicate_logic(code, filename))
        bloat_items.extend(self._detect_comment_bloat(code, filename))
        
        # Apply automatic removals
        slimmed_code = self._apply_removals(code, bloat_items)
        
        # Calculate stats
        slimmed_lines = len(slimmed_code.split('\n'))
        bytes_removed = len(code) - len(slimmed_code)
        
        result = SlimResult(
            original_code=code,
            slimmed_code=slimmed_code,
            bloat_items=bloat_items,
            original_lines=original_lines,
            slimmed_lines=slimmed_lines,
            bytes_removed=bytes_removed
        )
        
        logger.info(f"Slimming complete: {result.summary}")
        return result
    
    def _detect_dead_code(self, code: str, filename: str) -> List[BloatItem]:
        """Detect unreachable and unused code."""
        items = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return items
        
        # Find all defined names
        defined_names: Dict[str, int] = {}  # name -> line number
        used_names: Set[str] = set()
        
        for node in ast.walk(tree):
            # Track definitions
            if isinstance(node, ast.FunctionDef):
                defined_names[node.name] = node.lineno
            elif isinstance(node, ast.ClassDef):
                defined_names[node.name] = node.lineno
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names[target.id] = node.lineno
            
            # Track usage
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    used_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # Track attribute access
                    current = node.func
                    while isinstance(current, ast.Attribute):
                        current = current.value
                    if isinstance(current, ast.Name):
                        used_names.add(current.id)
        
        # Find unused definitions (but skip dunder methods and public API)
        for name, line in defined_names.items():
            if name.startswith('_') and not name.startswith('__'):
                # Private names should be used internally
                if name not in used_names:
                    items.append(BloatItem(
                        category="dead_code",
                        description=f"Unused private definition: {name}",
                        location=f"{filename}:{line}",
                        severity=0.6,
                        suggestion=f"Remove unused '{name}' or make it public if needed",
                        removable=False  # Too risky to auto-remove
                    ))
        
        # Detect unreachable code after return/raise
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                for i, stmt in enumerate(body[:-1]):  # All but last
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        # Everything after this is unreachable
                        unreachable = body[i+1:]
                        if unreachable:
                            items.append(BloatItem(
                                category="dead_code",
                                description=f"Unreachable code after return/raise in {node.name}",
                                location=f"{filename}:{unreachable[0].lineno}",
                                severity=0.8,
                                suggestion="Remove unreachable code",
                                removable=self.aggressive
                            ))
                        break
        
        return items
    
    def _detect_redundant_imports(self, code: str, filename: str) -> List[BloatItem]:
        """Detect unused or duplicate imports."""
        items = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return items
        
        # Collect all imports
        imports: Dict[str, int] = {}  # name -> line number
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = node.lineno
        
        # Find all names used in code (excluding import statements)
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Get the root name
                current = node
                while isinstance(current, ast.Attribute):
                    current = current.value
                if isinstance(current, ast.Name):
                    used_names.add(current.id)
        
        # Check for unused imports
        for name, line in imports.items():
            # Skip certain always-needed imports
            if name in ('__future__', 'typing', 'TYPE_CHECKING'):
                continue
            
            if name not in used_names and name.split('.')[0] not in used_names:
                items.append(BloatItem(
                    category="redundant_import",
                    description=f"Unused import: {name}",
                    location=f"{filename}:{line}",
                    severity=0.4,
                    suggestion=f"Remove unused import '{name}'",
                    removable=True
                ))
        
        return items
    
    def _detect_over_abstraction(self, code: str, filename: str) -> List[BloatItem]:
        """Detect classes that should be functions or modules."""
        items = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return items
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                public_methods = [m for m in methods if not m.name.startswith('_')]
                
                # Check for single-method class (excluding __init__)
                non_init_methods = [m for m in public_methods if m.name != '__init__']
                if len(non_init_methods) == 1:
                    items.append(BloatItem(
                        category="over_abstraction",
                        description=f"Class '{node.name}' has only one public method",
                        location=f"{filename}:{node.lineno}",
                        severity=0.5,
                        suggestion=f"Consider converting to a function: {non_init_methods[0].name}()",
                        removable=False
                    ))
                
                # Check for class with no state (no __init__ or empty __init__)
                init_methods = [m for m in methods if m.name == '__init__']
                if not init_methods:
                    if len(methods) > 0:
                        items.append(BloatItem(
                            category="over_abstraction",
                            description=f"Class '{node.name}' has no __init__ (stateless)",
                            location=f"{filename}:{node.lineno}",
                            severity=0.3,
                            suggestion="Consider using a module with functions instead",
                            removable=False
                        ))
                elif init_methods:
                    init = init_methods[0]
                    # Check if __init__ only has 'pass' or 'self' assignments
                    if len(init.body) == 1 and isinstance(init.body[0], ast.Pass):
                        items.append(BloatItem(
                            category="over_abstraction",
                            description=f"Class '{node.name}' has empty __init__",
                            location=f"{filename}:{node.lineno}",
                            severity=0.4,
                            suggestion="Consider using @dataclass or functions",
                            removable=False
                        ))
        
        return items
    
    def _detect_duplicate_logic(self, code: str, filename: str) -> List[BloatItem]:
        """Detect duplicate code patterns."""
        items = []
        lines = code.split('\n')
        
        # Simple approach: find repeated non-trivial lines
        line_counts: Dict[str, List[int]] = {}  # normalized line -> line numbers
        
        for i, line in enumerate(lines, 1):
            # Normalize line (strip whitespace, ignore comments)
            normalized = line.strip()
            if not normalized or normalized.startswith('#'):
                continue
            if len(normalized) < 20:  # Skip short lines
                continue
            
            if normalized not in line_counts:
                line_counts[normalized] = []
            line_counts[normalized].append(i)
        
        # Find duplicates
        for line_text, occurrences in line_counts.items():
            if len(occurrences) >= 3:  # 3+ repetitions is suspicious
                items.append(BloatItem(
                    category="duplicate_logic",
                    description=f"Repeated code pattern ({len(occurrences)} times)",
                    location=f"{filename}:{occurrences[0]}",
                    severity=0.6,
                    suggestion=f"Extract to a function or variable",
                    removable=False,
                    code_snippet=line_text[:60] + "..." if len(line_text) > 60 else line_text
                ))
        
        return items
    
    def _detect_comment_bloat(self, code: str, filename: str) -> List[BloatItem]:
        """Detect comments that add no value."""
        items = []
        lines = code.split('\n')
        
        # Patterns for useless comments
        useless_patterns = [
            r'#\s*increment\s+\w+',              # # increment counter
            r'#\s*set\s+\w+\s+to',               # # set x to 5
            r'#\s*return\s+(the\s+)?result',     # # return the result
            r'#\s*initialize',                   # # initialize
            r'#\s*loop\s+(through|over)',        # # loop through items
            r'#\s*if\s+.*then',                  # # if condition then
            r'#\s*create\s+(a\s+)?(new\s+)?',    # # create a new
            r'#\s*call\s+',                      # # call function
            r'#\s*import\s+',                    # # import module
        ]
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped.startswith('#'):
                continue
            
            for pattern in useless_patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    items.append(BloatItem(
                        category="comment_bloat",
                        description="Comment restates the obvious",
                        location=f"{filename}:{i}",
                        severity=0.2,
                        suggestion="Remove comment - code is self-documenting",
                        removable=True,
                        code_snippet=stripped[:50]
                    ))
                    break
        
        return items
    
    def _apply_removals(self, code: str, bloat_items: List[BloatItem]) -> str:
        """Apply automatic removals for removable bloat items."""
        if not bloat_items:
            return code
        
        lines = code.split('\n')
        lines_to_remove: Set[int] = set()
        
        for item in bloat_items:
            if not item.removable:
                continue
            
            # Extract line number from location
            try:
                line_num = int(item.location.split(':')[1])
                
                if item.category == "redundant_import":
                    # Remove the entire import line
                    lines_to_remove.add(line_num)
                
                elif item.category == "comment_bloat":
                    # Remove the comment line
                    lines_to_remove.add(line_num)
            except (IndexError, ValueError):
                continue
        
        # Remove marked lines
        if lines_to_remove:
            new_lines = [
                line for i, line in enumerate(lines, 1)
                if i not in lines_to_remove
            ]
            return '\n'.join(new_lines)
        
        return code
    
    def analyze_only(self, code: str, filename: str = "unknown") -> List[BloatItem]:
        """
        Analyze code for bloat without modifying it.
        
        Returns list of bloat items found.
        """
        items = []
        items.extend(self._detect_dead_code(code, filename))
        items.extend(self._detect_redundant_imports(code, filename))
        items.extend(self._detect_over_abstraction(code, filename))
        items.extend(self._detect_duplicate_logic(code, filename))
        items.extend(self._detect_comment_bloat(code, filename))
        return items


# Async convenience function
async def slim(code: str, filename: str = "unknown", aggressive: bool = False) -> SlimResult:
    """
    Convenience function to slim code.
    
    Args:
        code: Source code to slim
        filename: File name for reporting
        aggressive: If True, remove more aggressively
        
    Returns:
        SlimResult with slimmed code and analysis
    """
    slimmer = Slimmer(aggressive=aggressive)
    return await slimmer.slim(code, filename)


if __name__ == "__main__":
    import asyncio
    
    # Test with bloated code
    test_code = '''
import os
import sys  # unused
import json  # unused
from typing import List, Dict, Optional

# Set x to 5
x = 5

# Increment counter
counter = counter + 1

class SingleMethodClass:
    """A class with just one method."""
    
    def do_thing(self):
        """Do the thing."""
        return "thing done"


def process_items(items: List[int]) -> int:
    """Process items and return sum."""
    result = sum(items)
    return result
    # This code is unreachable
    print("never runs")


def _unused_helper():
    """This function is never called."""
    pass


# Loop through items
for item in items:
    process(item)
    
# Loop through items
for item in items:
    process(item)
    
# Loop through items  
for item in items:
    process(item)
'''
    
    async def main():
        result = await slim(test_code, "test.py")
        print(f"\n{'='*60}")
        print("SLIMMER RESULTS")
        print('='*60)
        print(f"\n{result.summary}")
        print(f"\nBloat Items Found:")
        for item in result.bloat_items:
            print(f"\n  [{item.category}] {item.description}")
            print(f"    Location: {item.location}")
            print(f"    Severity: {item.severity:.2f}")
            print(f"    Removable: {item.removable}")
            print(f"    Suggestion: {item.suggestion}")
            if item.code_snippet:
                print(f"    Snippet: {item.code_snippet}")
        
        print(f"\n{'='*60}")
        print("BLOAT SCORE:", result.bloat_score)
        print("Pass threshold (< 0.3):", "✓ PASS" if result.bloat_score < 0.3 else "✗ FAIL")
    
    asyncio.run(main())
