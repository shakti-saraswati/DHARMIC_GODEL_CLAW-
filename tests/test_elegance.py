"""
Unit tests for elegance.py — Code Quality & Bloat Detection
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.expanduser('~/DHARMIC_GODEL_CLAW/src'))

from dgm.elegance import (
    EleganceScore, 
    evaluate_elegance,
    create_diff,
    ComplexityVisitor
)
import ast


class TestEleganceScore:
    """Test EleganceScore dataclass."""
    
    def test_score_clamping(self):
        """Total score should be clamped to [0, 1]."""
        score = EleganceScore(total=1.5)
        assert score.total == 1.0
        
        score = EleganceScore(total=-0.5)
        assert score.total == 0.0
        
    def test_default_values(self):
        """Test default values are set correctly."""
        score = EleganceScore(total=0.8)
        assert score.breakdown == {}
        assert score.concerns == []
        assert score.is_bloated == False


class TestComplexityVisitor:
    """Test cyclomatic complexity calculation."""
    
    def test_simple_function(self):
        """Simple function has complexity 1."""
        code = "def foo():\n    return 42"
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        assert visitor.complexity == 1
        
    def test_if_statement(self):
        """If statement adds complexity."""
        code = """
def foo(x):
    if x > 0:
        return x
    return 0
"""
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        assert visitor.complexity == 2  # base + if
        
    def test_loop_complexity(self):
        """Loops add complexity."""
        code = """
def foo(items):
    for item in items:
        while item > 0:
            item -= 1
"""
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        assert visitor.complexity == 3  # base + for + while
        
    def test_boolean_operators(self):
        """Boolean operators add decision points."""
        code = """
def foo(a, b, c):
    if a and b and c:
        return True
"""
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        assert visitor.complexity == 4  # base + if + 2 'and's
        
    def test_comprehension_complexity(self):
        """List comprehensions with conditions add complexity."""
        code = "result = [x for x in items if x > 0]"
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        assert visitor.complexity == 3  # base + comprehension + if


class TestElegantCode:
    """Test with examples of elegant code."""
    
    def test_small_refactor(self):
        """Small focused refactors should score high."""
        original = """
def process(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""
        modified = """
def process(data):
    return [item * 2 for item in data if item > 0]
"""
        score = evaluate_elegance(original, modified)
        
        assert score.total > 0.7, f"Elegant refactor scored too low: {score.total}"
        assert not score.is_bloated
        assert len(score.concerns) < 3
        
    def test_rename_for_clarity(self):
        """Clear renames should score well."""
        original = """
def f(x):
    return x * 2
"""
        modified = """
def double_value(number):
    return number * 2
"""
        score = evaluate_elegance(original, modified)
        
        assert score.total > 0.6
        assert not score.is_bloated
        
    def test_removed_code(self):
        """Removing unnecessary code is elegant."""
        original = """
def process(data):
    # Old unused import
    result = []
    temp = None  # Unused variable
    for item in data:
        result.append(item)
    return result
"""
        modified = """
def process(data):
    return list(data)
"""
        score = evaluate_elegance(original, modified)
        
        assert score.total > 0.8
        assert not score.is_bloated


class TestBloatedCode:
    """Test with examples of bloated code."""
    
    def test_massive_addition(self):
        """Adding too many lines triggers bloat detection."""
        original = "def foo(): pass"
        # Generate 150 lines of filler
        modified = "def foo():\n" + "\n".join(
            f"    x{i} = {i}" for i in range(150)
        )
        
        score = evaluate_elegance(original, modified)
        
        assert score.is_bloated, "Should detect bloat from massive addition"
        # Total score may still be decent (other metrics fine), but is_bloated is key
        assert score.breakdown['line_count_delta'] < 0.5, "Line count penalty not applied"
        assert any("lines" in c.lower() for c in score.concerns)
        
    def test_complexity_explosion(self):
        """Large complexity increase triggers bloat."""
        original = """
def simple():
    return 42
"""
        modified = """
def complex():
    if a:
        if b:
            if c:
                if d:
                    for x in items:
                        while x > 0:
                            if x % 2 == 0:
                                return x
    return 0
"""
        score = evaluate_elegance(original, modified)
        
        assert score.is_bloated or score.total < 0.5
        assert any("complexity" in c.lower() for c in score.concerns)
        
    def test_import_bloat(self):
        """Adding many unnecessary imports is penalized."""
        original = "import os\n\ndef foo(): pass"
        modified = """
import os
import sys
import json
import re
import collections
import itertools
import functools
import typing

def foo(): pass
"""
        score = evaluate_elegance(original, modified)
        
        assert score.breakdown['import_bloat'] < 0.8
        assert any("import" in c.lower() for c in score.concerns)
        
    def test_copy_paste_duplication(self):
        """Duplicate code blocks are detected."""
        original = "def foo(): pass"
        modified = """
def foo():
    result = process_data(input_value)
    validate_result(result)
    save_to_database(result)
    
def bar():
    result = process_data(input_value)
    validate_result(result)
    save_to_database(result)
    
def baz():
    result = process_data(input_value)
    validate_result(result)
    save_to_database(result)
"""
        score = evaluate_elegance(original, modified)
        
        assert score.breakdown['duplication'] < 0.9
        
    def test_poor_naming(self):
        """Single-letter and cryptic names are penalized."""
        original = ""
        modified = """
def f(a, b, c, d, e):
    x = a + b
    y = c * d
    z = x - y + e
    return z

def g(q):
    return q * 2

class foo:
    pass
"""
        score = evaluate_elegance(original, modified)
        
        assert score.breakdown['naming_quality'] < 0.8
        assert any("name" in c.lower() or "class" in c.lower() for c in score.concerns)


class TestThresholds:
    """Test specific threshold conditions."""
    
    def test_reject_threshold(self):
        """Score < 0.5 should indicate rejection."""
        # Create obviously bad code
        original = "def foo(): return 1"
        modified = "def foo():\n" + "\n".join(
            f"    if x{i} > 0:\n        pass" for i in range(50)
        ) + "\n    return 1"
        
        score = evaluate_elegance(original, modified)
        
        # Either bloated or score indicates rejection
        should_reject = score.is_bloated or score.total < 0.5
        assert should_reject or score.total < 0.7
        
    def test_100_line_threshold_with_tests(self):
        """100+ lines OK if includes tests."""
        original = "def foo(): pass"
        
        # Generate code with test coverage
        code_lines = [f"    line{i} = {i}" for i in range(80)]
        test_lines = [
            "def test_foo():",
            "    assert foo() is not None",
            "    assert True",
        ] + [f"    assert line{i} == {i}" for i in range(30)]
        
        modified = "def foo():\n" + "\n".join(code_lines) + "\n\n" + "\n".join(test_lines)
        
        score = evaluate_elegance(original, modified)
        
        # Should not be bloated if tests are proportional
        # (20% test coverage requirement: 30+ test lines for 110 total)
        assert score.total > 0.3  # At least not terrible


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_original(self):
        """New file (empty original) should work."""
        score = evaluate_elegance("", "def foo(): return 42")
        assert 0 <= score.total <= 1
        assert isinstance(score.breakdown, dict)
        
    def test_empty_modified(self):
        """Deleted file (empty modified) should work."""
        score = evaluate_elegance("def foo(): return 42", "")
        assert 0 <= score.total <= 1
        
    def test_invalid_syntax(self):
        """Invalid Python syntax should not crash."""
        score = evaluate_elegance(
            "def foo(): return 42",
            "def broken( return"  # Invalid syntax
        )
        assert 0 <= score.total <= 1
        assert isinstance(score.concerns, list)
        
    def test_both_empty(self):
        """Both empty should not crash."""
        score = evaluate_elegance("", "")
        assert 0 <= score.total <= 1
        
    def test_whitespace_only(self):
        """Whitespace changes should score high."""
        original = "def foo():\n    return 42"
        modified = "def foo():\n    return 42\n\n"
        
        score = evaluate_elegance(original, modified)
        assert score.total > 0.8


class TestCreateDiff:
    """Test diff generation helper."""
    
    def test_creates_unified_diff(self):
        """Should create valid unified diff."""
        original = "line1\nline2\nline3"
        modified = "line1\nchanged\nline3"
        
        diff = create_diff(original, modified)
        
        assert "---" in diff
        assert "+++" in diff
        assert "-line2" in diff
        assert "+changed" in diff
        
    def test_empty_diff_for_identical(self):
        """Identical code produces minimal diff."""
        code = "def foo(): return 42"
        diff = create_diff(code, code)
        
        # Unified diff of identical files is empty
        assert diff == "" or all(
            not line.startswith(('+', '-')) or line.startswith(('+++', '---'))
            for line in diff.splitlines()
        )


class TestConvenienceFunction:
    """Test the evaluate_elegance convenience function."""
    
    def test_auto_generates_diff(self):
        """Should auto-generate diff if not provided."""
        original = "def foo(): pass"
        modified = "def foo(): return 42"
        
        score = evaluate_elegance(original, modified)
        
        assert isinstance(score, EleganceScore)
        assert score.breakdown.get('diff_size') is not None
        
    def test_accepts_custom_diff(self):
        """Should accept pre-computed diff."""
        original = "def foo(): pass"
        modified = "def foo(): return 42"
        custom_diff = "fake diff content"
        
        score = evaluate_elegance(original, modified, diff=custom_diff)
        
        assert isinstance(score, EleganceScore)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
