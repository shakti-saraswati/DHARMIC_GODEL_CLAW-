from __future__ import annotations
"""
Benchmark Harness - Real Evaluation for Self-Improvement

This addresses the key DGM gap: LLM-judged fitness vs benchmark-scored fitness.

Implements:
1. Syntax validation (AST parsing)
2. Import validation (can the code be imported?)
3. Test execution (pytest with timeout and sandboxing)
4. Coverage measurement
5. Type checking (optional, mypy)

This gives us REAL metrics, not just LLM opinions.
"""

import ast
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Result of running benchmarks on code."""
    syntax_valid: bool = False
    syntax_errors: List[str] = field(default_factory=list)

    import_valid: bool = False
    import_errors: List[str] = field(default_factory=list)

    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    test_errors: List[str] = field(default_factory=list)

    coverage_percent: float = 0.0

    type_check_passed: bool = False
    type_errors: List[str] = field(default_factory=list)

    execution_time_ms: float = 0.0
    timeout_occurred: bool = False

    # Composite score (0-1)
    score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "syntax_valid": self.syntax_valid,
            "syntax_errors": self.syntax_errors,
            "import_valid": self.import_valid,
            "import_errors": self.import_errors,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "test_errors": self.test_errors,
            "coverage_percent": self.coverage_percent,
            "type_check_passed": self.type_check_passed,
            "type_errors": self.type_errors,
            "execution_time_ms": self.execution_time_ms,
            "timeout_occurred": self.timeout_occurred,
            "score": self.score
        }


class BenchmarkHarness:
    """
    Runs real benchmarks on code changes.

    Unlike LLM-judged fitness, this gives objective metrics.
    """

    def __init__(
        self,
        project_root: str = None,
        test_timeout: int = 60,
        enable_coverage: bool = True,
        enable_type_check: bool = False,
    ):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        self.project_root = Path(project_root)
        self.test_timeout = test_timeout
        self.enable_coverage = enable_coverage
        self.enable_type_check = enable_type_check

        # Weights for composite score
        self.weights = {
            "syntax": 0.2,
            "import": 0.2,
            "tests": 0.4,
            "coverage": 0.1,
            "type_check": 0.1
        }

    def validate_syntax(self, code: str, filename: str = "<code>") -> Tuple[bool, List[str]]:
        """
        Validate Python syntax using AST.

        Returns (valid, errors)
        """
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            return False, [f"{filename}:{e.lineno}: {e.msg}"]

    def validate_file_syntax(self, filepath: Path) -> Tuple[bool, List[str]]:
        """Validate syntax of a file."""
        try:
            code = filepath.read_text()
            return self.validate_syntax(code, str(filepath))
        except Exception as e:
            return False, [str(e)]

    def validate_import(self, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Test if a file can be imported.

        Uses subprocess for isolation.
        """
        try:
            # Create a simple import test script
            module_name = filepath.stem
            test_code = f"""
import sys
sys.path.insert(0, '{filepath.parent}')
try:
    import {module_name}
    print("IMPORT_OK")
except Exception as e:
    print(f"IMPORT_FAILED: {{e}}")
"""
            result = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root
            )

            if "IMPORT_OK" in result.stdout:
                return True, []
            else:
                error = result.stdout + result.stderr
                return False, [error.strip()]

        except subprocess.TimeoutExpired:
            return False, ["Import timed out"]
        except Exception as e:
            return False, [str(e)]

    def run_tests(
        self,
        test_path: Path = None,
        test_pattern: str = "test_*.py"
    ) -> Tuple[int, int, int, List[str]]:
        """
        Run pytest on the project or specific path.

        Returns (total, passed, failed, errors)
        """
        if test_path is None:
            # Look for tests directory
            test_dirs = ["tests", "test", "swarm/tests"]
            for td in test_dirs:
                candidate = self.project_root / td
                if candidate.exists():
                    test_path = candidate
                    break

        if test_path is None or not test_path.exists():
            return 0, 0, 0, ["No tests found"]

        try:
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_path),
                "-v",
                "--tb=short",
                "-q"
            ]

            if self.enable_coverage:
                cmd.extend(["--cov=" + str(self.project_root), "--cov-report=json"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
                cwd=self.project_root
            )

            # Parse pytest output
            output = result.stdout + result.stderr
            lines = output.split("\n")

            # Look for summary line like "5 passed, 2 failed"
            total = passed = failed = 0
            errors = []

            for line in lines:
                if "passed" in line or "failed" in line or "error" in line:
                    # Parse counts
                    import re
                    passed_match = re.search(r"(\d+) passed", line)
                    failed_match = re.search(r"(\d+) failed", line)
                    error_match = re.search(r"(\d+) error", line)

                    if passed_match:
                        passed = int(passed_match.group(1))
                    if failed_match:
                        failed = int(failed_match.group(1))
                    if error_match:
                        failed += int(error_match.group(1))

                # Collect error messages
                if "FAILED" in line or "ERROR" in line:
                    errors.append(line.strip())

            total = passed + failed
            return total, passed, failed, errors

        except subprocess.TimeoutExpired:
            return 0, 0, 0, ["Tests timed out"]
        except Exception as e:
            return 0, 0, 0, [str(e)]

    def get_coverage(self) -> float:
        """Get coverage percentage from coverage.json if available."""
        coverage_file = self.project_root / "coverage.json"
        if not coverage_file.exists():
            return 0.0

        try:
            with open(coverage_file) as f:
                data = json.load(f)
            return data.get("totals", {}).get("percent_covered", 0.0)
        except Exception:
            return 0.0

    def run_type_check(self, filepath: Path = None) -> Tuple[bool, List[str]]:
        """
        Run mypy type checking.

        Returns (passed, errors)
        """
        try:
            target = str(filepath) if filepath else str(self.project_root / "src")

            result = subprocess.run(
                [sys.executable, "-m", "mypy", target, "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root
            )

            if result.returncode == 0:
                return True, []
            else:
                errors = [l for l in result.stdout.split("\n") if "error:" in l]
                return False, errors[:10]  # Limit errors

        except subprocess.TimeoutExpired:
            return False, ["Type check timed out"]
        except Exception as e:
            return False, [str(e)]

    def benchmark_file(self, filepath: Path) -> BenchmarkResult:
        """Run full benchmark suite on a single file."""
        result = BenchmarkResult()
        start_time = datetime.now()

        # 1. Syntax validation
        result.syntax_valid, result.syntax_errors = self.validate_file_syntax(filepath)
        if not result.syntax_valid:
            result.score = 0.0
            return result

        # 2. Import validation
        result.import_valid, result.import_errors = self.validate_import(filepath)

        # 3. Run tests (if they exist)
        result.tests_run, result.tests_passed, result.tests_failed, result.test_errors = self.run_tests()

        # 4. Coverage
        if self.enable_coverage:
            result.coverage_percent = self.get_coverage()

        # 5. Type check (optional)
        if self.enable_type_check:
            result.type_check_passed, result.type_errors = self.run_type_check(filepath)

        # Calculate execution time
        result.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Calculate composite score
        result.score = self._calculate_score(result)

        return result

    def benchmark_code(self, code: str, filename: str = "test_module.py") -> BenchmarkResult:
        """
        Benchmark code string by writing to temp file.

        Provides sandboxed evaluation.
        """
        result = BenchmarkResult()
        start_time = datetime.now()

        # Create temp directory for sandboxing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir) / filename

            # Write code to temp file
            tmppath.write_text(code)

            # 1. Syntax validation
            result.syntax_valid, result.syntax_errors = self.validate_syntax(code, filename)
            if not result.syntax_valid:
                result.score = 0.0
                return result

            # 2. Import validation (in sandbox)
            result.import_valid, result.import_errors = self.validate_import(tmppath)

        result.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.score = self._calculate_score(result)

        return result

    def benchmark_changes(self, changes: List[Dict]) -> BenchmarkResult:
        """
        Benchmark a set of file changes.

        Each change dict has: {"filepath": str, "content": str}

        Creates temp sandbox, applies changes, runs benchmarks.
        """
        result = BenchmarkResult()
        start_time = datetime.now()

        # Create sandbox copy of project
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = Path(tmpdir) / "sandbox"

            # Copy relevant project files
            src_dir = self.project_root / "src"
            if src_dir.exists():
                shutil.copytree(src_dir, sandbox / "src")

            # Apply changes
            all_valid = True
            for change in changes:
                filepath = Path(change["filepath"])
                content = change["content"]

                # Validate syntax first
                valid, errors = self.validate_syntax(content, str(filepath))
                if not valid:
                    result.syntax_errors.extend(errors)
                    all_valid = False
                    continue

                # Write to sandbox
                target = sandbox / filepath.relative_to(self.project_root) if filepath.is_absolute() else sandbox / filepath
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)

            result.syntax_valid = all_valid

            if all_valid:
                # Run tests in sandbox
                result.tests_run, result.tests_passed, result.tests_failed, result.test_errors = self._run_sandbox_tests(sandbox)

        result.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.score = self._calculate_score(result)

        return result

    def _run_sandbox_tests(self, sandbox: Path) -> Tuple[int, int, int, List[str]]:
        """Run tests in a sandbox directory."""
        test_dir = sandbox / "tests"
        if not test_dir.exists():
            return 0, 0, 0, ["No tests in sandbox"]

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir), "-v", "-q"],
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
                cwd=sandbox,
                env={**os.environ, "PYTHONPATH": str(sandbox)}
            )

            # Parse output (same as run_tests)
            import re
            output = result.stdout + result.stderr
            passed = failed = 0

            for line in output.split("\n"):
                passed_match = re.search(r"(\d+) passed", line)
                failed_match = re.search(r"(\d+) failed", line)
                if passed_match:
                    passed = int(passed_match.group(1))
                if failed_match:
                    failed = int(failed_match.group(1))

            return passed + failed, passed, failed, []

        except subprocess.TimeoutExpired:
            return 0, 0, 0, ["Sandbox tests timed out"]
        except Exception as e:
            return 0, 0, 0, [str(e)]

    def _calculate_score(self, result: BenchmarkResult) -> float:
        """Calculate composite score from benchmark results."""
        score = 0.0

        # Syntax (binary)
        if result.syntax_valid:
            score += self.weights["syntax"]

        # Import (binary)
        if result.import_valid:
            score += self.weights["import"]

        # Tests (ratio)
        if result.tests_run > 0:
            test_score = result.tests_passed / result.tests_run
            score += self.weights["tests"] * test_score

        # Coverage (ratio)
        score += self.weights["coverage"] * (result.coverage_percent / 100.0)

        # Type check (binary)
        if result.type_check_passed:
            score += self.weights["type_check"]

        return min(1.0, score)


# Need os for subprocess env
import os


# CLI test
if __name__ == "__main__":
    print("=" * 60)
    print("BENCHMARK HARNESS - Test")
    print("=" * 60)

    harness = BenchmarkHarness()

    # Test syntax validation
    print("\n--- Syntax Validation ---")
    good_code = "def hello():\n    return 'world'"
    bad_code = "def hello(\n    return 'world'"

    valid, errors = harness.validate_syntax(good_code)
    print(f"Good code valid: {valid}")

    valid, errors = harness.validate_syntax(bad_code)
    print(f"Bad code valid: {valid}, errors: {errors}")

    # Test code benchmark
    print("\n--- Code Benchmark ---")
    test_code = '''
def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b
'''
    result = harness.benchmark_code(test_code)
    print(f"Syntax valid: {result.syntax_valid}")
    print(f"Import valid: {result.import_valid}")
    print(f"Score: {result.score:.3f}")
    print(f"Execution time: {result.execution_time_ms:.0f}ms")

    # Test project benchmark
    print("\n--- Project Benchmark ---")
    src_core = harness.project_root / "src" / "core" / "dharmic_agent.py"
    if src_core.exists():
        result = harness.benchmark_file(src_core)
        print(f"File: {src_core.name}")
        print(f"Syntax valid: {result.syntax_valid}")
        print(f"Import valid: {result.import_valid}")
        print(f"Tests: {result.tests_passed}/{result.tests_run} passed")
        print(f"Score: {result.score:.3f}")
