"""
Mathematical Evaluator — Rigorous Code Quality Assessment
==========================================================

Evaluates code from a mathematical standpoint using:
1. Compression-based complexity (Kolmogorov approximation)
2. Information density metrics
3. Structural entropy (detecting repetition)
4. MDL principle (does code justify its length?)
5. Compositionality scoring

This is the "master mathematician" in the loop — catching AI slop
that passes heuristic checks but fails mathematical elegance.

Theory:
- Kolmogorov: K(x) = length of shortest program producing x
- MDL: Best model minimizes description_length + error_length
- Shannon: H(X) = -Σ p(x) log p(x) — entropy measures redundancy
"""

from __future__ import annotations

import ast
import lzma
import math
import re
import zlib
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import hashlib


@dataclass
class MathematicalScore:
    """
    Mathematical assessment of code quality.
    
    All scores normalized to 0-1 where higher = better (more elegant).
    """
    # Core metrics
    compression_elegance: float      # 1 - compression_ratio (less compressible = less redundant)
    information_density: float       # meaningful tokens / total tokens
    structural_entropy: float        # normalized entropy (0=repetitive, 1=random, 0.6-0.8=elegant)
    mdl_efficiency: float           # functionality per byte
    compositionality: float         # how well functions compose
    
    # Aggregate
    total: float = 0.0
    
    # Diagnostics
    redundancy_patterns: List[str] = field(default_factory=list)
    bloat_indicators: List[str] = field(default_factory=list)
    slop_signatures: List[str] = field(default_factory=list)
    
    # Raw data
    raw_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Weighted aggregate — compositionality and information density matter most
        base_score = (
            0.15 * self.compression_elegance +
            0.30 * self.information_density +
            0.20 * self.structural_entropy +
            0.15 * self.mdl_efficiency +
            0.20 * self.compositionality
        )
        
        # CRITICAL: Penalize for detected slop signatures
        slop_penalty = len(self.slop_signatures) * 0.15
        bloat_penalty = len(self.bloat_indicators) * 0.05
        redundancy_penalty = len(self.redundancy_patterns) * 0.10
        
        self.total = base_score - slop_penalty - bloat_penalty - redundancy_penalty
        self.total = max(0.0, min(1.0, self.total))
    
    @property
    def is_elegant(self) -> bool:
        """Code passes mathematical elegance threshold."""
        return self.total >= 0.65 and len(self.slop_signatures) == 0
    
    @property
    def is_slop(self) -> bool:
        """Code shows AI slop signatures."""
        return len(self.slop_signatures) >= 2 or self.total < 0.4
    
    def summary(self) -> str:
        status = "✅ ELEGANT" if self.is_elegant else ("❌ SLOP" if self.is_slop else "⚠️ MEDIOCRE")
        lines = [
            f"{status} (score: {self.total:.2f})",
            f"  Compression elegance: {self.compression_elegance:.2f}",
            f"  Information density:  {self.information_density:.2f}",
            f"  Structural entropy:   {self.structural_entropy:.2f}",
            f"  MDL efficiency:       {self.mdl_efficiency:.2f}",
            f"  Compositionality:     {self.compositionality:.2f}",
        ]
        if self.slop_signatures:
            lines.append(f"  Slop signatures: {', '.join(self.slop_signatures)}")
        if self.bloat_indicators:
            lines.append(f"  Bloat: {', '.join(self.bloat_indicators[:3])}")
        return "\n".join(lines)


class MathematicalEvaluator:
    """
    The Master Mathematician — evaluates code with mathematical rigor.
    
    Unlike heuristic evaluators that count lines and branches,
    this measures fundamental properties:
    
    1. How much can the code be compressed? (redundancy)
    2. How much meaning per token? (density)
    3. How predictable is the structure? (entropy)
    4. Does the length justify the functionality? (MDL)
    5. Do the parts compose cleanly? (category theory)
    """
    
    # Thresholds tuned for Python code
    OPTIMAL_ENTROPY_RANGE = (0.55, 0.85)  # Too low = repetitive, too high = random
    MIN_INFORMATION_DENSITY = 0.3
    MAX_COMPRESSION_RATIO = 0.7  # If code compresses more than 70%, it's redundant
    
    # AI slop signatures (patterns that indicate low-quality generation)
    SLOP_PATTERNS = [
        r'# TODO: implement',
        r'# This function',
        r'"""[\s\S]{0,20}"""',  # Empty or near-empty docstrings
        r'pass\s*$',  # Stub implementations
        r'\.\.\.(\s*#.*)?$',  # Ellipsis placeholders
        r'raise NotImplementedError',
        r'return None\s*$',  # Meaningless returns
    ]
    
    # Verbose patterns that indicate AI padding
    VERBOSE_PATTERNS = [
        r'if\s+\w+\s+is\s+not\s+None\s+and\s+len\(\w+\)\s*>\s*0',  # verbose truthiness
        r'== True|== False',  # explicit boolean comparison
        r'if\s+len\(\w+\)\s*==\s*0',  # instead of `if not x`
        r'\.append\([^)]+\)\s*\n.*\.append\(',  # repeated appends (should be extend)
        r'for\s+\w+\s+in\s+range\(len\(',  # instead of enumerate
    ]

    def __init__(self):
        self._slop_regexes = [re.compile(p, re.MULTILINE) for p in self.SLOP_PATTERNS]
        self._verbose_regexes = [re.compile(p, re.MULTILINE) for p in self.VERBOSE_PATTERNS]

    def evaluate(self, code: str, context: Optional[str] = None) -> MathematicalScore:
        """
        Evaluate code mathematically.
        
        Args:
            code: Source code to evaluate
            context: Optional context about what the code should do
            
        Returns:
            MathematicalScore with detailed metrics
        """
        if not code.strip():
            return MathematicalScore(
                compression_elegance=0.0,
                information_density=0.0,
                structural_entropy=0.0,
                mdl_efficiency=0.0,
                compositionality=0.0,
                slop_signatures=["empty_code"],
            )
        
        # Calculate all metrics
        comp_elegance, comp_ratio = self._compression_elegance(code)
        info_density, token_stats = self._information_density(code)
        entropy, entropy_dist = self._structural_entropy(code)
        mdl_eff = self._mdl_efficiency(code, context)
        composability = self._compositionality(code)
        
        # Detect problems
        redundancy = self._detect_redundancy(code)
        bloat = self._detect_bloat(code, token_stats)
        slop = self._detect_slop(code)
        
        return MathematicalScore(
            compression_elegance=comp_elegance,
            information_density=info_density,
            structural_entropy=entropy,
            mdl_efficiency=mdl_eff,
            compositionality=composability,
            redundancy_patterns=redundancy,
            bloat_indicators=bloat,
            slop_signatures=slop,
            raw_metrics={
                "compression_ratio": comp_ratio,
                "unique_tokens": token_stats.get("unique", 0),
                "total_tokens": token_stats.get("total", 0),
                "entropy_raw": entropy_dist,
                "function_count": self._count_functions(code),
                "avg_function_size": self._avg_function_size(code),
            }
        )
    
    def _compression_elegance(self, code: str) -> Tuple[float, float]:
        """
        Measure elegance via compression ratio.
        
        Intuition: Highly compressible code has lots of redundancy.
        Elegant code is already "compressed" conceptually.
        
        Returns:
            (elegance_score, raw_compression_ratio)
        """
        code_bytes = code.encode('utf-8')
        
        # Use LZMA for better pattern detection than gzip
        compressed = lzma.compress(code_bytes, preset=9)
        ratio = len(compressed) / len(code_bytes)
        
        # Transform: lower compression ratio = more elegant
        # But very low ratio might mean trivial code
        if ratio < 0.2:
            elegance = 0.5  # Suspicious: maybe too simple
        elif ratio < 0.4:
            elegance = 0.9  # Great: dense, non-redundant
        elif ratio < 0.6:
            elegance = 0.7  # Good: some structure, not too redundant
        elif ratio < 0.8:
            elegance = 0.5  # Mediocre: getting redundant
        else:
            elegance = 0.3  # Poor: highly compressible = redundant
        
        return elegance, ratio
    
    def _information_density(self, code: str) -> Tuple[float, Dict[str, int]]:
        """
        Measure meaningful tokens per total tokens.
        
        High density = every token carries meaning
        Low density = lots of boilerplate, repeated identifiers
        """
        # Tokenize (simple approach - split on non-alphanumeric)
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
        
        if not tokens:
            return 0.0, {"unique": 0, "total": 0}
        
        total = len(tokens)
        unique = len(set(tokens))
        
        # Filter out Python keywords and very common tokens
        COMMON = {'self', 'def', 'return', 'if', 'else', 'for', 'in', 'is', 'not', 
                  'and', 'or', 'None', 'True', 'False', 'class', 'import', 'from',
                  'try', 'except', 'with', 'as', 'lambda', 'yield', 'raise'}
        
        meaningful = [t for t in tokens if t not in COMMON and len(t) > 1]
        meaningful_unique = len(set(meaningful))
        
        # Density = unique meaningful / total
        density = meaningful_unique / total if total > 0 else 0
        
        # Normalize to 0-1 (empirically, good code is 0.15-0.4)
        normalized = min(1.0, density / 0.35)
        
        return normalized, {
            "unique": unique,
            "total": total,
            "meaningful_unique": meaningful_unique,
            "meaningful_total": len(meaningful),
        }
    
    def _structural_entropy(self, code: str) -> Tuple[float, float]:
        """
        Calculate Shannon entropy of code structure.
        
        Uses n-grams of AST node types to measure structural predictability.
        
        - Low entropy = highly repetitive structure (AI slop often)
        - Very high entropy = random noise (broken code)
        - Medium entropy = well-structured (elegant)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.0, 0.0
        
        # Extract sequence of AST node types
        node_types = []
        for node in ast.walk(tree):
            node_types.append(type(node).__name__)
        
        if len(node_types) < 3:
            return 0.5, 0.0
        
        # Calculate bigram distribution
        bigrams = []
        for i in range(len(node_types) - 1):
            bigrams.append((node_types[i], node_types[i+1]))
        
        # Shannon entropy
        counter = Counter(bigrams)
        total = len(bigrams)
        entropy = 0.0
        for count in counter.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize by maximum possible entropy
        max_entropy = math.log2(len(counter)) if len(counter) > 1 else 1
        normalized = entropy / max_entropy if max_entropy > 0 else 0
        
        # Transform to score: optimal is in the middle range
        low, high = self.OPTIMAL_ENTROPY_RANGE
        if low <= normalized <= high:
            score = 0.9  # Optimal range
        elif normalized < low:
            score = 0.3 + (normalized / low) * 0.4  # Too repetitive
        else:
            score = 0.9 - (normalized - high) * 0.5  # Too random
        
        return max(0.0, min(1.0, score)), normalized
    
    def _mdl_efficiency(self, code: str, context: Optional[str] = None) -> float:
        """
        Minimum Description Length efficiency.
        
        Measures: Does the code length justify its functionality?
        
        Approximation: 
        - Count distinct operations/capabilities
        - Divide by code length
        - Elegant code does more per byte
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.3
        
        # Count "functionality units"
        func_count = 0
        class_count = 0
        operation_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.BinOp, ast.Compare, ast.BoolOp, ast.Call)):
                operation_count += 1
        
        # Functionality score
        functionality = func_count * 3 + class_count * 5 + operation_count * 0.5
        
        # Code length (non-whitespace, non-comment)
        lines = [l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        code_length = sum(len(l.strip()) for l in lines)
        
        if code_length == 0:
            return 0.0
        
        # Efficiency = functionality per 100 characters
        efficiency = (functionality / code_length) * 100
        
        # Normalize (empirically, good code is 1-5 functionality units per 100 chars)
        normalized = min(1.0, efficiency / 3.0)
        
        return normalized
    
    def _compositionality(self, code: str) -> float:
        """
        Measure how well functions compose.
        
        Category-theoretic intuition:
        - Functions should be pure where possible
        - Side effects should be explicit
        - Components should be usable in isolation
        
        Practical metrics:
        - Function argument count (fewer = more composable)
        - Return statement presence
        - Global/nonlocal usage (bad)
        - Nested function depth
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.3
        
        scores = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_score = 1.0
                
                # Penalty for too many arguments
                arg_count = len(node.args.args)
                if arg_count > 5:
                    func_score -= 0.1 * (arg_count - 5)
                
                # Penalty for no return (probably side-effect only)
                has_return = any(isinstance(n, ast.Return) and n.value is not None 
                               for n in ast.walk(node))
                if not has_return:
                    func_score -= 0.2
                
                # Penalty for global/nonlocal
                for child in ast.walk(node):
                    if isinstance(child, (ast.Global, ast.Nonlocal)):
                        func_score -= 0.3
                        break
                
                # Penalty for deep nesting
                depth = self._max_depth(node)
                if depth > 4:
                    func_score -= 0.1 * (depth - 4)
                
                scores.append(max(0.0, func_score))
        
        if not scores:
            return 0.5  # No functions to evaluate
        
        return sum(scores) / len(scores)
    
    def _max_depth(self, node: ast.AST, current: int = 0) -> int:
        """Calculate maximum nesting depth."""
        max_child_depth = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._max_depth(child, current + 1)
                max_child_depth = max(max_child_depth, child_depth)
            else:
                child_depth = self._max_depth(child, current)
                max_child_depth = max(max_child_depth, child_depth)
        return max_child_depth
    
    def _detect_redundancy(self, code: str) -> List[str]:
        """Detect redundant patterns."""
        issues = []
        
        lines = code.split('\n')
        
        # Check for repeated lines
        line_counts = Counter(l.strip() for l in lines if l.strip())
        for line, count in line_counts.most_common(5):
            if count > 2 and len(line) > 20:
                issues.append(f"repeated_line:{count}x")
                break
        
        # Check for repeated blocks (3+ consecutive lines appearing multiple times)
        for i in range(len(lines) - 2):
            block = tuple(lines[i:i+3])
            block_str = '\n'.join(block)
            if code.count(block_str) > 1 and len(block_str.strip()) > 30:
                issues.append("repeated_block")
                break
        
        return issues
    
    def _detect_bloat(self, code: str, token_stats: Dict) -> List[str]:
        """Detect code bloat indicators."""
        issues = []
        
        # Very long lines
        lines = code.split('\n')
        long_lines = sum(1 for l in lines if len(l) > 120)
        if long_lines > len(lines) * 0.1:
            issues.append(f"long_lines:{long_lines}")
        
        # Too many imports
        import_lines = sum(1 for l in lines if l.strip().startswith(('import ', 'from ')))
        if import_lines > 20:
            issues.append(f"import_heavy:{import_lines}")
        
        # Low meaningful token ratio
        if token_stats.get("meaningful_unique", 0) < token_stats.get("total", 1) * 0.1:
            issues.append("low_semantic_density")
        
        return issues
    
    def _detect_slop(self, code: str) -> List[str]:
        """Detect AI slop signatures."""
        signatures = []
        
        # Check slop patterns
        for i, regex in enumerate(self._slop_regexes):
            if regex.search(code):
                signatures.append(f"slop_pattern_{i}")
        
        # Check verbose patterns
        verbose_count = sum(1 for r in self._verbose_regexes if r.search(code))
        if verbose_count >= 2:
            signatures.append("verbose_idioms")
        
        # Check for excessive comments relative to code
        lines = code.split('\n')
        comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
        if code_lines > 0 and comment_lines / code_lines > 0.5:
            signatures.append("over_commented")
        
        # Check for very long docstrings (AI loves verbose docs)
        docstring_matches = re.findall(r'"""[\s\S]*?"""', code)
        total_docstring_len = sum(len(d) for d in docstring_matches)
        if total_docstring_len > len(code) * 0.3:
            signatures.append("docstring_heavy")
        
        return signatures
    
    def _count_functions(self, code: str) -> int:
        try:
            tree = ast.parse(code)
            return sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        except:
            return 0
    
    def _avg_function_size(self, code: str) -> float:
        try:
            tree = ast.parse(code)
            sizes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sizes.append(node.end_lineno - node.lineno + 1)
            return sum(sizes) / len(sizes) if sizes else 0
        except:
            return 0


def evaluate_mathematically(code: str, context: str = None) -> MathematicalScore:
    """Convenience function for mathematical evaluation."""
    return MathematicalEvaluator().evaluate(code, context)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            code = f.read()
    else:
        code = '''
def process_data(data):
    """Process the data."""
    result = []
    for item in data:
        if item is not None:
            result.append(item)
    return result
'''
    
    evaluator = MathematicalEvaluator()
    score = evaluator.evaluate(code)
    print(score.summary())
    print(f"\nRaw metrics: {score.raw_metrics}")
