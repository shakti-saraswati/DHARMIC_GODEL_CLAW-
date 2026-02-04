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
    
    Grounded in:
    - Kolmogorov complexity (compression_elegance)
    - Shannon entropy (structural_entropy)
    - MDL principle (mdl_efficiency)
    - Category theory (compositionality)
    - Curry-Howard (type_coverage)
    - Holographic principle (interface_balance)
    """
    # Core metrics (all 0-1, higher = better)
    compression_elegance: float      # K(x) approximation: less compressible = less redundant
    information_density: float       # Meaningful tokens / total tokens
    structural_entropy: float        # Shannon H: 0=repetitive, 1=random, 0.6-0.8=elegant
    mdl_efficiency: float           # Functionality per byte (MDL principle)
    compositionality: float         # Category theory: clean morphism composition
    type_coverage: float = 0.5      # Curry-Howard: typed functions = proven functions
    interface_balance: float = 0.5  # Holographic: API surface ≈ implementation depth
    
    # Aggregate
    total: float = 0.0
    
    # Diagnostics
    redundancy_patterns: List[str] = field(default_factory=list)
    bloat_indicators: List[str] = field(default_factory=list)
    slop_signatures: List[str] = field(default_factory=list)
    context_notes: List[str] = field(default_factory=list)
    
    # Raw data
    raw_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Weighted aggregate based on mathematical importance
        # Compression elegance and compositionality are most fundamental
        base_score = (
            0.20 * self.compression_elegance +  # Kolmogorov
            0.15 * self.information_density +    # Shannon density
            0.15 * self.structural_entropy +     # Shannon structure
            0.10 * self.mdl_efficiency +         # MDL
            0.20 * self.compositionality +       # Category theory
            0.10 * self.type_coverage +          # Curry-Howard
            0.10 * self.interface_balance        # Holographic
        )
        
        # Penalty approach revised per audit: slop is a gate, not a heavy subtraction
        # Use diminishing returns to avoid 2 hits erasing the score
        slop_count = len(self.slop_signatures)
        bloat_count = len(self.bloat_indicators)
        redundancy_count = len(self.redundancy_patterns)
        
        # Diminishing penalty: first hit = 0.08, second = 0.05, third+ = 0.03 each
        def diminishing_penalty(count: int, base: float, decay: float) -> float:
            if count == 0:
                return 0.0
            penalty = base  # First hit
            for i in range(1, count):
                penalty += max(base * (decay ** i), 0.02)
            return penalty
        
        slop_penalty = diminishing_penalty(slop_count, 0.08, 0.6)
        bloat_penalty = diminishing_penalty(bloat_count, 0.03, 0.7)
        redundancy_penalty = diminishing_penalty(redundancy_count, 0.05, 0.6)
        
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
        if self.context_notes:
            lines.append(f"  Context notes: {', '.join(self.context_notes[:3])}")
        return "\n".join(lines)


class MathematicalEvaluator:
    """
    The Master Mathematician — evaluates code with mathematical rigor.
    
    Grounded in fundamental mathematics (ALL CPU-computable, no GPU needed):
    
    1. KOLMOGOROV COMPLEXITY (K)
       - K(x) = length of shortest program producing x
       - Approximated via LZMA compression
       - Elegant code: K(code) ≈ len(code) (incompressible)
       - AI slop: K(code) << len(code) (highly compressible)
    
    2. SOLOMONOFF INDUCTION
       - P(x) ∝ 2^(-K(x)) — simpler = more probable
       - Universal prior favors shorter programs
       - Occam's razor mathematized
    
    3. SHANNON ENTROPY
       - H(X) = -Σ p(x) log p(x)
       - Measures structural predictability
       - Optimal: 0.6-0.8 (structured but not repetitive)
    
    4. MINIMUM DESCRIPTION LENGTH (MDL)
       - Best model minimizes: description + error
       - Code should justify its length with functionality
    
    5. CATEGORICAL COMPOSITIONALITY
       - Clean composition ≈ associative morphisms
       - Functions as arrows, types as objects
       - Measured via: purity, argument count, nesting
    
    6. HOLOGRAPHIC PRINCIPLE (adapted)
       - Interface complexity bounds internal complexity
       - API surface ≈ implementation depth
    """
    
    # Thresholds tuned for Python code
    OPTIMAL_ENTROPY_RANGE = (0.55, 0.85)  # Too low = repetitive, too high = random
    MIN_INFORMATION_DENSITY = 0.3
    MAX_COMPRESSION_RATIO = 0.7  # If code compresses more than 70%, it's redundant
    
    # AI slop signatures — ONLY clear indicators of lazy generation
    # (Revised per audit: avoid false positives on legitimate patterns)
    SLOP_PATTERNS = [
        r'# TODO: implement\s*$',           # Unfinished placeholder
        r'# This function\s+\w+',           # AI-style "This function does X" comment
        r'"""[\s]{0,5}"""',                 # TRULY empty docstrings only (not short ones)
        r'def\s+\w+\([^)]*\):\s*\n\s*pass\s*$',  # pass ONLY if entire function body is pass
        r'\.\.\.(\s*#.*)?$',                # Ellipsis placeholders (but allow in type stubs)
    ]
    
    # Patterns legitimate in some contexts (ABC, protocols, stubs)
    # These are NOT penalized, just noted
    CONTEXT_DEPENDENT_PATTERNS = [
        (r'raise NotImplementedError', 'abstract_method'),
        (r'return None\s*$', 'explicit_none_return'),
        (r'pass\s*$', 'stub_or_protocol'),
    ]
    
    # Verbose patterns that indicate AI padding / non-idiomatic Python
    VERBOSE_PATTERNS = [
        r'if\s+\w+\s+is\s+not\s+None\s+and\s+len\(\w+\)\s*>\s*0',  # verbose truthiness combo
        r'== True(?!\w)|== False(?!\w)',    # explicit boolean comparison
        r'if\s+len\(\w+\)\s*[=<>]+\s*0',    # if len(x) == 0, > 0, etc. (use truthiness)
        r'for\s+\w+\s+in\s+range\(len\(',   # instead of enumerate
        r'if\s+\w+\s+is\s+not\s+None:\s*\n\s*if\s+',  # nested None check then condition
        r'\[\w+\].*\[\w+\].*\[\w+\]',       # triple indexing (use unpacking)
        r'\.append\([^)]+\)\s*\n\s*\w+\.append\(',  # repeated appends (use extend)
    ]

    def __init__(self):
        self._slop_regexes = [re.compile(p, re.MULTILINE) for p in self.SLOP_PATTERNS]
        self._verbose_regexes = [re.compile(p, re.MULTILINE) for p in self.VERBOSE_PATTERNS]
        self._context_regexes = [
            (re.compile(p, re.MULTILINE), label)
            for p, label in self.CONTEXT_DEPENDENT_PATTERNS
        ]

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
        type_cov = self._type_coverage(code)  # Curry-Howard
        interface_bal = self._interface_balance(code)  # Holographic principle
        
        # Detect problems
        redundancy = self._detect_redundancy(code)
        bloat = self._detect_bloat(code, token_stats)
        slop = self._detect_slop(code)
        context_notes = self._detect_context_notes(code)
        
        return MathematicalScore(
            compression_elegance=comp_elegance,
            information_density=info_density,
            structural_entropy=entropy,
            mdl_efficiency=mdl_eff,
            compositionality=composability,
            type_coverage=type_cov,
            interface_balance=interface_bal,
            redundancy_patterns=redundancy,
            bloat_indicators=bloat,
            slop_signatures=slop,
            context_notes=context_notes,
            raw_metrics={
                "compression_ratio": comp_ratio,
                "unique_tokens": token_stats.get("unique", 0),
                "total_tokens": token_stats.get("total", 0),
                "entropy_raw": entropy_dist,
                "function_count": self._count_functions(code),
                "type_coverage_raw": type_cov,
                "interface_balance_raw": interface_bal,
                "avg_function_size": self._avg_function_size(code),
            }
        )
    
    def _compression_elegance(self, code: str) -> Tuple[float, float]:
        """
        Measure elegance via compression ratio (Kolmogorov approximation).
        
        Intuition: 
        - ratio = compressed_size / original_size
        - Low ratio (0.2) = compresses to 20% = HIGHLY redundant = SLOP
        - High ratio (0.9) = compresses to 90% = barely compressible = ELEGANT
        
        Elegant code is already conceptually compressed — can't be reduced further.
        AI slop is verbose and repetitive — compresses dramatically.
        
        Returns:
            (elegance_score, raw_compression_ratio)
        """
        code_bytes = code.encode('utf-8')
        
        # Use LZMA for better pattern detection than gzip
        compressed = lzma.compress(code_bytes, preset=9)
        
        # Handle LZMA overhead for small files (< 200 bytes can have ratio > 1)
        if len(code_bytes) < 200:
            overhead = len(lzma.compress(b"", preset=9))
            adjusted = max(len(compressed) - overhead, 1)
            ratio = min(1.0, adjusted / max(len(code_bytes), 1))
        else:
            ratio = len(compressed) / len(code_bytes)
        
        # CORRECT mapping: HIGHER ratio = LESS compressible = MORE elegant
        # (Previous version was inverted!)
        if ratio > 0.85:
            elegance = 0.95  # Excellent: barely compressible, very dense
        elif ratio > 0.7:
            elegance = 0.85  # Great: low redundancy
        elif ratio > 0.55:
            elegance = 0.7   # Good: moderate compression
        elif ratio > 0.4:
            elegance = 0.5   # Mediocre: notable redundancy
        elif ratio > 0.25:
            elegance = 0.3   # Poor: high redundancy
        else:
            elegance = 0.15  # Very poor: extremely compressible = slop
        
        return elegance, ratio
    
    def _information_density(self, code: str) -> Tuple[float, Dict[str, int]]:
        """
        Measure semantic information per byte of code.
        
        Revised per audit: lexical diversity (unique/total) is NOT a good metric
        because repeated consistent identifiers are GOOD in real code.
        
        Better approach: Measure semantic content per character
        - Subtract boilerplate (whitespace, brackets, keywords-only lines)
        - Reward high AST node count per byte (lots of semantics packed in)
        """
        # Tokenize
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
        
        if not tokens:
            return 0.0, {"unique": 0, "total": 0}
        
        total = len(tokens)
        unique = len(set(tokens))
        
        # Calculate semantic density: AST nodes per non-whitespace character
        try:
            tree = ast.parse(code)
            ast_nodes = sum(1 for _ in ast.walk(tree))
        except SyntaxError:
            ast_nodes = 0
        
        # Non-whitespace, non-comment characters
        code_chars = len(re.sub(r'\s+|#[^\n]*', '', code))
        
        # AST nodes per 100 characters (semantic density)
        if code_chars > 0:
            semantic_density = (ast_nodes / code_chars) * 100
        else:
            semantic_density = 0
        
        # Normalize (empirically, good code has 5-15 AST nodes per 100 chars)
        normalized = min(1.0, semantic_density / 12.0)
        
        return normalized, {
            "unique": unique,
            "total": total,
            "ast_nodes": ast_nodes,
            "code_chars": code_chars,
            "semantic_density": semantic_density,
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
        - Cyclomatic complexity (fewer paths = simpler to compose)
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
                    func_score -= 0.15  # Reduced from 0.2
                
                # Penalty for global/nonlocal
                for child in ast.walk(node):
                    if isinstance(child, (ast.Global, ast.Nonlocal)):
                        func_score -= 0.3
                        break
                
                # Penalty for deep nesting
                depth = self._max_depth(node)
                if depth > 4:
                    func_score -= 0.1 * (depth - 4)
                
                # Cyclomatic complexity penalty (per audit recommendation)
                # CC = E - N + 2P, approximated by counting decision points
                cyclomatic = self._cyclomatic_complexity(node)
                if cyclomatic > 10:
                    func_score -= 0.15 * ((cyclomatic - 10) / 10)  # Gradual penalty
                elif cyclomatic > 5:
                    func_score -= 0.05  # Small penalty for moderate complexity
                
                scores.append(max(0.0, func_score))
        
        if not scores:
            return 0.5  # No functions to evaluate
        
        return sum(scores) / len(scores)
    
    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity for a function.
        
        CC = number of decision points + 1
        Decision points: if, for, while, and, or, except, with, assert
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Branching statements
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                   ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            # Boolean operators add paths
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Ternary expressions
            elif isinstance(child, ast.IfExp):
                complexity += 1
        
        return complexity
    
    def _type_coverage(self, code: str) -> float:
        """
        Measure type annotation coverage (Curry-Howard correspondence).
        
        In Curry-Howard, types are propositions and programs are proofs.
        A well-typed function is a PROVEN function.
        
        - Fully typed function: proof of correctness
        - Untyped function: unproven claim
        - `Any` type: trivial proof (proves nothing)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.3
        
        total_functions = 0
        typed_functions = 0
        total_args = 0
        typed_args = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                
                # Check return type annotation
                has_return_type = node.returns is not None
                
                # Check argument type annotations
                func_args = node.args.args
                func_typed_args = sum(1 for arg in func_args if arg.annotation is not None)
                
                total_args += len(func_args)
                typed_args += func_typed_args
                
                # Function is "typed" if it has return type and >50% args typed
                if has_return_type and (len(func_args) == 0 or func_typed_args / len(func_args) > 0.5):
                    typed_functions += 1
        
        if total_functions == 0:
            return 0.5  # No functions to evaluate
        
        # Combine function coverage and argument coverage
        func_coverage = typed_functions / total_functions
        arg_coverage = typed_args / total_args if total_args > 0 else 0.5
        
        return 0.6 * func_coverage + 0.4 * arg_coverage
    
    def _interface_balance(self, code: str) -> float:
        """
        Measure interface/implementation balance (Holographic principle).
        
        The holographic principle: information in a region is bounded by
        its surface area, not its volume.
        
        For code: the complexity of the public interface should be
        proportional to the internal implementation complexity.
        
        - Tiny interface, huge internals = hidden complexity (bad)
        - Huge interface, tiny internals = over-abstracted (bad)
        - Balanced = elegant
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.3
        
        # Count public interface (functions, classes, their signatures)
        public_functions = 0
        public_args = 0
        public_classes = 0
        
        # Count implementation (statements, expressions inside functions)
        impl_statements = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Public if not starting with _
                if not node.name.startswith('_'):
                    public_functions += 1
                    public_args += len(node.args.args)
                
                # Count implementation depth
                for child in ast.walk(node):
                    if isinstance(child, (ast.Assign, ast.AugAssign, ast.Return, 
                                         ast.If, ast.For, ast.While, ast.Call)):
                        impl_statements += 1
            
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    public_classes += 1
        
        # Interface complexity = public surface area
        interface_complexity = public_functions + public_args * 0.5 + public_classes * 2
        
        # Implementation complexity = internal volume  
        impl_complexity = impl_statements
        
        if interface_complexity == 0 or impl_complexity == 0:
            return 0.5  # Can't measure
        
        # Ratio: ideal is roughly 1:5 to 1:20 (interface:impl)
        ratio = interface_complexity / impl_complexity
        
        # Score: penalize extremes
        if 0.03 <= ratio <= 0.3:
            return 0.9  # Good balance
        elif 0.01 <= ratio <= 0.5:
            return 0.7  # Acceptable
        elif ratio < 0.01:
            return 0.4  # Hidden complexity (tiny interface, huge impl)
        else:
            return 0.5  # Over-abstracted (huge interface, small impl)
    
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
        
        # Low semantic density (AST nodes per 100 chars)
        semantic_density = token_stats.get("semantic_density", 0.0)
        if semantic_density < 3.0:
            issues.append("low_semantic_density")
        
        return issues
    
    def _detect_slop(self, code: str) -> List[str]:
        """
        Detect AI slop signatures.
        
        Revised per audit: be conservative, avoid false positives.
        """
        signatures = []
        
        # Check definite slop patterns only
        for i, regex in enumerate(self._slop_regexes):
            if regex.search(code):
                signatures.append(f"slop_pattern_{i}")
        
        # Check verbose patterns — require 3+ hits to flag (was 2)
        verbose_count = sum(1 for r in self._verbose_regexes if r.search(code))
        if verbose_count >= 3:
            signatures.append("verbose_idioms")
        
        # Comment ratio check — MUCH more lenient
        # Only flag if comments > 80% of code lines (extreme case)
        lines = code.split('\n')
        comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
        if code_lines > 0 and comment_lines > code_lines * 0.8:
            signatures.append("over_commented")
        
        # Docstring check — only flag if >50% AND docstrings are repetitive
        docstring_matches = re.findall(r'"""[\s\S]*?"""', code)
        total_docstring_len = sum(len(d) for d in docstring_matches)
        if total_docstring_len > len(code) * 0.5:
            # Additional check: are docstrings actually repetitive?
            if len(docstring_matches) > 1:
                # Check for copy-paste patterns
                ds_texts = [d.lower() for d in docstring_matches]
                unique_ratio = len(set(ds_texts)) / len(ds_texts)
                if unique_ratio < 0.7:  # >30% duplicated docstrings
                    signatures.append("repetitive_docstrings")
        
        return signatures

    def _detect_context_notes(self, code: str) -> List[str]:
        """Detect context-dependent patterns without penalizing."""
        notes = []
        for regex, label in self._context_regexes:
            if regex.search(code):
                notes.append(label)
        return notes
    
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
