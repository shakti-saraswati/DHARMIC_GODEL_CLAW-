from __future__ import annotations
"""Tester Agent - Tests implemented changes."""

from dataclasses import dataclass
from typing import List
import logging
import os
import shlex
import subprocess


@dataclass
class TestResult:
    """Result of testing changes."""
    passed: bool
    tests_run: int
    failures: List[str]
    skipped: bool = False


class TesterAgent:
    """Tests implemented changes to validate correctness."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run_tests(self, files_changed: List[str]) -> TestResult:
        """
        Run tests on changed files.

        Args:
            files_changed: List of files that were modified

        Returns:
            TestResult with pass/fail status
        """
        self.logger.info(f"Testing changes in {len(files_changed)} files")

        if not files_changed:
            return TestResult(passed=True, tests_run=0, failures=[], skipped=True)

        if os.getenv("DGC_SKIP_TESTS") == "1":
            self.logger.info("Tests skipped (DGC_SKIP_TESTS=1)")
            return TestResult(passed=True, tests_run=0, failures=[], skipped=True)

        test_cmd = os.getenv("DGC_TEST_CMD")
        if not test_cmd:
            self.logger.info("No test command configured (DGC_TEST_CMD not set)")
            return TestResult(passed=True, tests_run=0, failures=[], skipped=True)

        try:
            cmd = shlex.split(test_cmd)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            passed = result.returncode == 0
            failures = []
            if not passed:
                failures.append(result.stderr.strip() or "Tests failed")
            return TestResult(passed=passed, tests_run=1, failures=failures, skipped=False)
        except Exception as e:
            return TestResult(passed=False, tests_run=0, failures=[str(e)], skipped=False)
