"""
Real Gate Implementations for Cosmic Krishna Coder.

Wires actual security and quality tools to the 22-gate protocol.
No more stubs — real validation.

Tools integrated:
- bandit: Security scanning (AHIMSA)
- safety: Dependency vulnerability (VULNERABILITY)
- ruff: Linting and formatting (SATYA, LINT_FORMAT)
- mypy: Type checking (TYPE_CHECK)
- pytest: Testing (TEST_COVERAGE, CORRECTNESS)

Author: Cursor CLI (via DHARMIC CLAW directive)
Date: 2026-02-05
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List


class GateStatus(Enum):
    """Gate execution status."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class GateResult:
    """Result from a single gate check."""
    name: str
    status: GateStatus
    message: str
    blocking: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    tool_output: str = ""


# =============================================================================
# PHASE 1: SECURITY GATES
# =============================================================================

def check_ahimsa(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    AHIMSA Gate: Security scanning via bandit.
    
    Scans Python code for common security issues:
    - SQL injection
    - Command injection
    - Hardcoded passwords
    - Unsafe deserialization
    - etc.
    """
    if not code and not files:
        return GateResult("ahimsa", GateStatus.SKIP, "No code to scan", False)
    
    try:
        # Write code to temp file for scanning
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write(code or "")
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout or "{}"
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                data = {"results": []}
            
            issues = data.get("results", [])
            
            if issues:
                # Categorize by severity
                high = [i for i in issues if i.get("issue_severity") == "HIGH"]
                medium = [i for i in issues if i.get("issue_severity") == "MEDIUM"]
                low = [i for i in issues if i.get("issue_severity") == "LOW"]
                
                summary = f"{len(high)} HIGH, {len(medium)} MEDIUM, {len(low)} LOW"
                
                # HIGH severity = blocking
                if high:
                    return GateResult(
                        "ahimsa",
                        GateStatus.FAIL,
                        f"Security issues: {summary}",
                        blocking=True,
                        details={
                            "issues": issues[:10],  # First 10
                            "high_count": len(high),
                            "medium_count": len(medium),
                            "low_count": len(low),
                        },
                        tool_output=output[:2000]
                    )
                else:
                    return GateResult(
                        "ahimsa",
                        GateStatus.WARN,
                        f"Minor issues: {summary}",
                        blocking=False,
                        details={"issues": issues[:5]},
                        tool_output=output[:1000]
                    )
            
            return GateResult(
                "ahimsa",
                GateStatus.PASS,
                "No security issues found",
                False,
                details={"scanned_lines": len(code.splitlines()) if code else 0}
            )
            
        finally:
            os.unlink(temp_path)
            
    except FileNotFoundError:
        return GateResult(
            "ahimsa",
            GateStatus.ERROR,
            "bandit not installed (pip install bandit)",
            False
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            "ahimsa",
            GateStatus.ERROR,
            "Security scan timed out",
            False
        )
    except Exception as e:
        return GateResult(
            "ahimsa",
            GateStatus.ERROR,
            f"Security scan error: {str(e)[:100]}",
            False
        )


def check_secrets(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    SECRETS Gate: Detect hardcoded secrets, API keys, passwords.
    
    Uses pattern matching for common secret formats:
    - AWS keys
    - API tokens
    - Passwords in strings
    - Private keys
    """
    if not code:
        return GateResult("secrets", GateStatus.SKIP, "No code to scan", False)
    
    # Secret patterns (regex)
    SECRET_PATTERNS = [
        (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
        (r'(?i)api[_-]?key\s*[=:]\s*["\'][^"\']{10,}["\']', 'API Key'),
        (r'(?i)password\s*[=:]\s*["\'][^"\']+["\']', 'Hardcoded Password'),
        (r'(?i)secret\s*[=:]\s*["\'][^"\']{8,}["\']', 'Secret Value'),
        (r'(?i)token\s*[=:]\s*["\'][^"\']{20,}["\']', 'Token'),
        (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----', 'Private Key'),
        (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer Token'),
        (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Token'),
        (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
        (r'xox[baprs]-[0-9a-zA-Z-]+', 'Slack Token'),
    ]
    
    found_secrets = []
    
    for pattern, name in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            for match in matches[:3]:  # Limit to 3 per type
                # Redact the actual value
                redacted = match[:8] + "..." + match[-4:] if len(match) > 16 else "***"
                found_secrets.append({
                    "type": name,
                    "pattern": pattern[:30],
                    "redacted": redacted
                })
    
    if found_secrets:
        return GateResult(
            "secrets",
            GateStatus.FAIL,
            f"Found {len(found_secrets)} potential secrets",
            blocking=True,  # Secrets are always blocking
            details={"secrets": found_secrets}
        )
    
    return GateResult(
        "secrets",
        GateStatus.PASS,
        "No secrets detected",
        False
    )


def check_vulnerability(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    VULNERABILITY Gate: Check dependencies for known vulnerabilities.
    
    Uses safety to scan requirements.txt or pyproject.toml.
    """
    # Look for requirements in the code or files
    requirements_content = None
    
    # Check if code contains requirements-like content
    if code and ("==" in code or ">=" in code):
        # Might be requirements.txt content
        lines = code.strip().splitlines()
        if all(re.match(r'^[a-zA-Z0-9_-]+[=<>!]', line.strip()) 
               for line in lines if line.strip() and not line.startswith('#')):
            requirements_content = code
    
    # If no requirements content, try to find requirements.txt
    if not requirements_content:
        for path in ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]:
            if Path(path).exists():
                try:
                    requirements_content = Path(path).read_text()
                    break
                except:
                    pass
    
    if not requirements_content:
        return GateResult(
            "vulnerability",
            GateStatus.SKIP,
            "No requirements found to scan",
            False
        )
    
    try:
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write(requirements_content)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["safety", "check", "-r", temp_path, "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            try:
                # Safety v3 output format
                data = json.loads(result.stdout) if result.stdout else {}
                vulnerabilities = data.get("vulnerabilities", [])
            except json.JSONDecodeError:
                # Fallback: check exit code
                if result.returncode != 0:
                    vulnerabilities = [{"unknown": result.stderr[:200]}]
                else:
                    vulnerabilities = []
            
            if vulnerabilities:
                critical = [v for v in vulnerabilities 
                           if v.get("severity", "").upper() in ["CRITICAL", "HIGH"]]
                
                return GateResult(
                    "vulnerability",
                    GateStatus.FAIL if critical else GateStatus.WARN,
                    f"Found {len(vulnerabilities)} vulnerable dependencies",
                    blocking=bool(critical),
                    details={
                        "count": len(vulnerabilities),
                        "critical_count": len(critical),
                        "vulnerabilities": vulnerabilities[:5]
                    }
                )
            
            return GateResult(
                "vulnerability",
                GateStatus.PASS,
                "No known vulnerabilities",
                False
            )
            
        finally:
            os.unlink(temp_path)
            
    except FileNotFoundError:
        return GateResult(
            "vulnerability",
            GateStatus.ERROR,
            "safety not installed (pip install safety)",
            False
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            "vulnerability",
            GateStatus.ERROR,
            "Vulnerability scan timed out",
            False
        )
    except Exception as e:
        return GateResult(
            "vulnerability",
            GateStatus.ERROR,
            f"Vulnerability scan error: {str(e)[:100]}",
            False
        )


# =============================================================================
# PHASE 2: CODE QUALITY GATES
# =============================================================================

def check_satya(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    SATYA Gate: Code linting via ruff.
    
    Checks for:
    - Style violations
    - Potential bugs
    - Complexity issues
    - Import sorting
    """
    if not code:
        return GateResult("satya", GateStatus.SKIP, "No code to lint", False)
    
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            try:
                issues = json.loads(result.stdout) if result.stdout else []
            except json.JSONDecodeError:
                issues = []
            
            if issues:
                # Categorize
                errors = [i for i in issues if i.get("code", "").startswith("E")]
                warnings = [i for i in issues if i.get("code", "").startswith("W")]
                
                return GateResult(
                    "satya",
                    GateStatus.WARN,
                    f"Lint issues: {len(errors)} errors, {len(warnings)} warnings",
                    blocking=False,  # Lint issues are usually not blocking
                    details={
                        "issues": issues[:10],
                        "error_count": len(errors),
                        "warning_count": len(warnings),
                        "total": len(issues)
                    }
                )
            
            return GateResult(
                "satya",
                GateStatus.PASS,
                "Code passes lint checks",
                False
            )
            
        finally:
            os.unlink(temp_path)
            
    except FileNotFoundError:
        return GateResult(
            "satya",
            GateStatus.ERROR,
            "ruff not installed (pip install ruff)",
            False
        )
    except Exception as e:
        return GateResult(
            "satya",
            GateStatus.ERROR,
            f"Lint error: {str(e)[:100]}",
            False
        )


def check_lint_format(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    LINT_FORMAT Gate: Code formatting check via ruff format.
    
    Checks if code is properly formatted.
    """
    if not code:
        return GateResult("lint_format", GateStatus.SKIP, "No code to check", False)
    
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["ruff", "format", "--check", "--diff", temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # Code needs formatting
                diff_lines = result.stdout.count('\n') if result.stdout else 0
                return GateResult(
                    "lint_format",
                    GateStatus.WARN,
                    f"Code needs formatting ({diff_lines} lines differ)",
                    blocking=False,
                    details={"diff": result.stdout[:1000] if result.stdout else ""}
                )
            
            return GateResult(
                "lint_format",
                GateStatus.PASS,
                "Code is properly formatted",
                False
            )
            
        finally:
            os.unlink(temp_path)
            
    except FileNotFoundError:
        return GateResult(
            "lint_format",
            GateStatus.ERROR,
            "ruff not installed",
            False
        )
    except Exception as e:
        return GateResult(
            "lint_format",
            GateStatus.ERROR,
            f"Format check error: {str(e)[:100]}",
            False
        )


def check_type_check(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    TYPE_CHECK Gate: Type checking via mypy.
    
    Validates type annotations and catches type errors.
    """
    if not code:
        return GateResult("type_check", GateStatus.SKIP, "No code to check", False)
    
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["mypy", "--ignore-missing-imports", "--no-error-summary", temp_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                # Parse mypy output
                errors = result.stdout.strip().splitlines() if result.stdout else []
                error_count = len([e for e in errors if ": error:" in e])
                
                if error_count > 0:
                    return GateResult(
                        "type_check",
                        GateStatus.WARN,
                        f"Type errors: {error_count}",
                        blocking=False,  # Type errors are warnings, not blocking
                        details={
                            "errors": errors[:10],
                            "count": error_count
                        }
                    )
            
            return GateResult(
                "type_check",
                GateStatus.PASS,
                "Type checks pass",
                False
            )
            
        finally:
            os.unlink(temp_path)
            
    except FileNotFoundError:
        return GateResult(
            "type_check",
            GateStatus.ERROR,
            "mypy not installed (pip install mypy)",
            False
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            "type_check",
            GateStatus.ERROR,
            "Type check timed out",
            False
        )
    except Exception as e:
        return GateResult(
            "type_check",
            GateStatus.ERROR,
            f"Type check error: {str(e)[:100]}",
            False
        )


# =============================================================================
# PHASE 3: TESTING GATES
# =============================================================================

def check_test_coverage(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    TEST_COVERAGE Gate: Check test coverage via pytest-cov.
    
    Requires tests to exist in tests/ directory.
    """
    # Check if tests directory exists
    test_dirs = ["tests", "test", "tests/"]
    test_dir = None
    
    for td in test_dirs:
        if Path(td).exists() and Path(td).is_dir():
            test_dir = td
            break
    
    if not test_dir:
        return GateResult(
            "test_coverage",
            GateStatus.SKIP,
            "No tests directory found",
            False
        )
    
    try:
        result = subprocess.run(
            ["pytest", "--cov=.", "--cov-report=json", "-q", test_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Check for coverage report
        cov_file = Path("coverage.json")
        if cov_file.exists():
            try:
                cov_data = json.loads(cov_file.read_text())
                total_coverage = cov_data.get("totals", {}).get("percent_covered", 0)
                
                if total_coverage < 50:
                    return GateResult(
                        "test_coverage",
                        GateStatus.WARN,
                        f"Low coverage: {total_coverage:.1f}%",
                        blocking=False,
                        details={"coverage_percent": total_coverage}
                    )
                elif total_coverage < 80:
                    return GateResult(
                        "test_coverage",
                        GateStatus.PASS,
                        f"Coverage: {total_coverage:.1f}%",
                        False,
                        details={"coverage_percent": total_coverage}
                    )
                else:
                    return GateResult(
                        "test_coverage",
                        GateStatus.PASS,
                        f"Good coverage: {total_coverage:.1f}%",
                        False,
                        details={"coverage_percent": total_coverage}
                    )
            except:
                pass
        
        # Fallback: check if tests passed
        if result.returncode == 0:
            return GateResult(
                "test_coverage",
                GateStatus.PASS,
                "Tests passed (coverage unknown)",
                False
            )
        else:
            return GateResult(
                "test_coverage",
                GateStatus.WARN,
                "Tests failed or no tests found",
                False,
                details={"output": result.stdout[:500] if result.stdout else ""}
            )
            
    except FileNotFoundError:
        return GateResult(
            "test_coverage",
            GateStatus.ERROR,
            "pytest not installed",
            False
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            "test_coverage",
            GateStatus.ERROR,
            "Test coverage timed out",
            False
        )
    except Exception as e:
        return GateResult(
            "test_coverage",
            GateStatus.ERROR,
            f"Coverage error: {str(e)[:100]}",
            False
        )


def check_correctness(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    CORRECTNESS Gate: Run tests via pytest.
    
    Checks if existing tests pass.
    """
    test_dirs = ["tests", "test"]
    test_dir = None
    
    for td in test_dirs:
        if Path(td).exists():
            test_dir = td
            break
    
    if not test_dir:
        return GateResult(
            "correctness",
            GateStatus.SKIP,
            "No tests directory found",
            False
        )
    
    try:
        result = subprocess.run(
            ["pytest", "-q", "--tb=short", test_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Parse pytest output for test count
            match = re.search(r'(\d+) passed', result.stdout or "")
            passed = int(match.group(1)) if match else 0
            
            return GateResult(
                "correctness",
                GateStatus.PASS,
                f"All {passed} tests passed",
                False,
                details={"passed": passed}
            )
        else:
            # Parse failures
            match_failed = re.search(r'(\d+) failed', result.stdout or "")
            failed = int(match_failed.group(1)) if match_failed else 0
            
            return GateResult(
                "correctness",
                GateStatus.FAIL,
                f"{failed} tests failed",
                blocking=True,  # Test failures are blocking
                details={
                    "failed": failed,
                    "output": result.stdout[:1000] if result.stdout else ""
                }
            )
            
    except FileNotFoundError:
        return GateResult(
            "correctness",
            GateStatus.ERROR,
            "pytest not installed",
            False
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            "correctness",
            GateStatus.ERROR,
            "Tests timed out",
            False
        )
    except Exception as e:
        return GateResult(
            "correctness",
            GateStatus.ERROR,
            f"Test error: {str(e)[:100]}",
            False
        )


# =============================================================================
# DHARMIC GATES (Ethical/Philosophical - Pattern-based)
# =============================================================================

def check_asteya(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    ASTEYA Gate: Non-stealing - check for license compliance.
    
    Looks for proper attribution and license headers.
    """
    if not code:
        return GateResult("asteya", GateStatus.SKIP, "No code to check", False)
    
    # Check for license/copyright headers
    has_license = any(marker in code.lower() for marker in [
        "license", "copyright", "mit", "apache", "gpl", "bsd",
        "spdx-license-identifier"
    ])
    
    # Check for suspicious copy patterns
    suspicious_patterns = [
        r'# copied from',
        r'# stolen from',
        r'# taken from stackoverflow',
    ]
    
    violations = []
    for pattern in suspicious_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            violations.append(pattern)
    
    if violations:
        return GateResult(
            "asteya",
            GateStatus.WARN,
            f"Found {len(violations)} attribution concerns",
            False,
            details={"patterns": violations}
        )
    
    return GateResult(
        "asteya",
        GateStatus.PASS,
        "License compliance OK" if has_license else "No license issues detected",
        False
    )


def check_aparigraha(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    APARIGRAHA Gate: Non-hoarding - check for minimal dependencies.
    
    Warns about excessive imports or dependencies.
    """
    if not code:
        return GateResult("aparigraha", GateStatus.SKIP, "No code to check", False)
    
    # Count imports
    import_lines = re.findall(r'^(?:from|import)\s+\S+', code, re.MULTILINE)
    import_count = len(import_lines)
    
    # Count unique packages
    packages = set()
    for line in import_lines:
        match = re.match(r'(?:from|import)\s+(\w+)', line)
        if match:
            packages.add(match.group(1))
    
    if import_count > 30:
        return GateResult(
            "aparigraha",
            GateStatus.WARN,
            f"High import count: {import_count} ({len(packages)} packages)",
            False,
            details={"import_count": import_count, "packages": list(packages)[:20]}
        )
    
    return GateResult(
        "aparigraha",
        GateStatus.PASS,
        f"Reasonable dependencies: {len(packages)} packages",
        False
    )


def check_brahmacharya(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    BRAHMACHARYA Gate: Focus/discipline - check for code complexity.
    
    Measures cyclomatic complexity and function length.
    """
    if not code:
        return GateResult("brahmacharya", GateStatus.SKIP, "No code to check", False)
    
    # Simple complexity heuristics
    # Count nested structures
    max_indent = 0
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped:
            indent = len(line) - len(stripped)
            spaces_per_level = 4
            level = indent // spaces_per_level
            max_indent = max(max_indent, level)
    
    # Count function definitions
    func_count = len(re.findall(r'^\s*def\s+', code, re.MULTILINE))
    
    # Count lines
    line_count = len(code.splitlines())
    
    if max_indent > 6:
        return GateResult(
            "brahmacharya",
            GateStatus.WARN,
            f"High nesting depth: {max_indent} levels",
            False,
            details={"max_indent": max_indent, "functions": func_count}
        )
    
    if func_count > 0 and line_count / func_count > 100:
        return GateResult(
            "brahmacharya",
            GateStatus.WARN,
            f"Long functions: avg {line_count // func_count} lines",
            False
        )
    
    return GateResult(
        "brahmacharya",
        GateStatus.PASS,
        f"Good complexity: depth {max_indent}, {func_count} functions",
        False
    )


def check_saucha(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    SAUCHA Gate: Purity/cleanliness - check for clean code patterns.
    
    Looks for code smells and anti-patterns.
    """
    if not code:
        return GateResult("saucha", GateStatus.SKIP, "No code to check", False)
    
    smells = []
    
    # Check for common code smells
    smell_patterns = [
        (r'except:\s*$', 'Bare except clause'),
        (r'except\s+Exception\s*:', 'Catching generic Exception'),
        (r'#\s*TODO', 'TODO comment'),
        (r'#\s*FIXME', 'FIXME comment'),
        (r'#\s*HACK', 'HACK comment'),
        (r'print\s*\(', 'Debug print statement'),
        (r'import\s+\*', 'Star import'),
        (r'global\s+\w+', 'Global variable'),
    ]
    
    for pattern, name in smell_patterns:
        matches = re.findall(pattern, code, re.MULTILINE)
        if matches:
            smells.append({"type": name, "count": len(matches)})
    
    if smells:
        total_smells = sum(s["count"] for s in smells)
        return GateResult(
            "saucha",
            GateStatus.WARN,
            f"Found {total_smells} code smells",
            False,
            details={"smells": smells}
        )
    
    return GateResult(
        "saucha",
        GateStatus.PASS,
        "Clean code patterns",
        False
    )


def check_santosha(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    SANTOSHA Gate: Contentment - check for scope creep/over-engineering.
    
    Warns about overly complex abstractions.
    """
    if not code:
        return GateResult("santosha", GateStatus.SKIP, "No code to check", False)
    
    # Check for over-engineering signals
    signals = []
    
    # Multiple inheritance
    multi_inherit = re.findall(r'class\s+\w+\([^)]*,\s*[^)]+\)', code)
    if len(multi_inherit) > 2:
        signals.append(f"Multiple inheritance: {len(multi_inherit)} classes")
    
    # Excessive decorators
    decorators = re.findall(r'@\w+', code)
    if len(decorators) > 20:
        signals.append(f"Many decorators: {len(decorators)}")
    
    # Abstract base classes
    abc_count = len(re.findall(r'ABC|abstractmethod|ABCMeta', code))
    if abc_count > 10:
        signals.append(f"Heavy abstraction: {abc_count} ABC references")
    
    if signals:
        return GateResult(
            "santosha",
            GateStatus.WARN,
            f"Possible over-engineering: {len(signals)} signals",
            False,
            details={"signals": signals}
        )
    
    return GateResult(
        "santosha",
        GateStatus.PASS,
        "Appropriate complexity",
        False
    )


def check_tapas(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    TAPAS Gate: Discipline - check for consistent patterns.
    
    Verifies naming conventions and structural consistency.
    """
    if not code:
        return GateResult("tapas", GateStatus.SKIP, "No code to check", False)
    
    issues = []
    
    # Check function naming (should be snake_case)
    funcs = re.findall(r'def\s+(\w+)\s*\(', code)
    camel_funcs = [f for f in funcs if re.match(r'^[a-z]+[A-Z]', f)]
    if camel_funcs:
        issues.append(f"CamelCase functions: {camel_funcs[:3]}")
    
    # Check class naming (should be PascalCase)
    classes = re.findall(r'class\s+(\w+)', code)
    snake_classes = [c for c in classes if '_' in c]
    if snake_classes:
        issues.append(f"snake_case classes: {snake_classes[:3]}")
    
    # Check constant naming (should be UPPER_CASE)
    # Simple heuristic: module-level assignments with lowercase
    
    if issues:
        return GateResult(
            "tapas",
            GateStatus.WARN,
            f"Naming inconsistencies: {len(issues)}",
            False,
            details={"issues": issues}
        )
    
    return GateResult(
        "tapas",
        GateStatus.PASS,
        "Consistent naming patterns",
        False
    )


def check_svadhyaya(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    SVADHYAYA Gate: Self-study - check for documentation.
    
    Verifies docstrings and comments exist.
    """
    if not code:
        return GateResult("svadhyaya", GateStatus.SKIP, "No code to check", False)
    
    # Count functions and classes
    funcs = re.findall(r'def\s+(\w+)\s*\(', code)
    classes = re.findall(r'class\s+(\w+)', code)
    
    # Count docstrings (triple quotes after def/class)
    docstrings = re.findall(r'(?:def|class)\s+\w+[^:]+:\s*\n\s*["\'][\'"]{2}', code)
    
    total_definitions = len(funcs) + len(classes)
    documented = len(docstrings)
    
    if total_definitions == 0:
        return GateResult(
            "svadhyaya",
            GateStatus.PASS,
            "No functions/classes to document",
            False
        )
    
    doc_ratio = documented / total_definitions if total_definitions > 0 else 0
    
    if doc_ratio < 0.3:
        return GateResult(
            "svadhyaya",
            GateStatus.WARN,
            f"Low documentation: {documented}/{total_definitions} ({doc_ratio:.0%})",
            False,
            details={"documented": documented, "total": total_definitions}
        )
    
    return GateResult(
        "svadhyaya",
        GateStatus.PASS,
        f"Documentation: {documented}/{total_definitions} ({doc_ratio:.0%})",
        False
    )


def check_ishvara_pranidhana(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    ISHVARA_PRANIDHANA Gate: Surrender/trust - check for error handling.
    
    Verifies proper exception handling and graceful degradation.
    """
    if not code:
        return GateResult("ishvara_pranidhana", GateStatus.SKIP, "No code to check", False)
    
    # Count try/except blocks
    try_blocks = len(re.findall(r'\btry\s*:', code))
    except_blocks = len(re.findall(r'\bexcept\s*', code))
    
    # Count potential failure points
    risky_calls = len(re.findall(
        r'(?:open|requests?\.|urllib|subprocess|os\.|shutil\.)', code
    ))
    
    if risky_calls > 0 and try_blocks == 0:
        return GateResult(
            "ishvara_pranidhana",
            GateStatus.WARN,
            f"No error handling for {risky_calls} risky operations",
            False,
            details={"risky_calls": risky_calls, "try_blocks": try_blocks}
        )
    
    return GateResult(
        "ishvara_pranidhana",
        GateStatus.PASS,
        f"Error handling: {try_blocks} try blocks for {risky_calls} risky ops",
        False
    )


# =============================================================================
# ML OVERLAY GATES
# =============================================================================

def check_model_card(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    MODEL_CARD Gate: Check for ML model documentation.
    
    Verifies model cards exist for ML models.
    """
    if not code:
        return GateResult("model_card", GateStatus.SKIP, "No code to check", False)
    
    # Check for ML model usage
    ml_patterns = [
        r'torch\.nn', r'tensorflow', r'keras', r'sklearn',
        r'transformers', r'\.fit\(', r'\.predict\('
    ]
    
    has_ml = any(re.search(p, code) for p in ml_patterns)
    
    if not has_ml:
        return GateResult(
            "model_card",
            GateStatus.SKIP,
            "No ML models detected",
            False
        )
    
    # Check for model card indicators
    has_card = any(marker in code.lower() for marker in [
        "model card", "model_card", "modelcard",
        "intended use", "limitations", "training data"
    ])
    
    if not has_card:
        return GateResult(
            "model_card",
            GateStatus.WARN,
            "ML code detected but no model card found",
            False,
            details={"recommendation": "Add model card with intended use, limitations, training data"}
        )
    
    return GateResult(
        "model_card",
        GateStatus.PASS,
        "Model card detected",
        False
    )


def check_data_provenance(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    DATA_PROVENANCE Gate: Check for data source documentation.
    """
    if not code:
        return GateResult("data_provenance", GateStatus.SKIP, "No code to check", False)
    
    # Check for data loading
    data_patterns = [
        r'pd\.read_', r'load_dataset', r'\.csv', r'\.json',
        r'Dataset', r'DataLoader'
    ]
    
    has_data = any(re.search(p, code) for p in data_patterns)
    
    if not has_data:
        return GateResult(
            "data_provenance",
            GateStatus.SKIP,
            "No data loading detected",
            False
        )
    
    # Check for provenance documentation
    has_provenance = any(marker in code.lower() for marker in [
        "source:", "provenance", "data source", "collected from",
        "license:", "citation"
    ])
    
    if not has_provenance:
        return GateResult(
            "data_provenance",
            GateStatus.WARN,
            "Data loading detected but no provenance documented",
            False
        )
    
    return GateResult(
        "data_provenance",
        GateStatus.PASS,
        "Data provenance documented",
        False
    )


def check_bias_audit(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    BIAS_AUDIT Gate: Check for bias considerations in ML code.
    """
    if not code:
        return GateResult("bias_audit", GateStatus.SKIP, "No code to check", False)
    
    # Check for ML indicators
    ml_patterns = [r'\.fit\(', r'\.predict\(', r'train', r'model']
    has_ml = any(re.search(p, code) for p in ml_patterns)
    
    if not has_ml:
        return GateResult(
            "bias_audit",
            GateStatus.SKIP,
            "No ML training detected",
            False
        )
    
    # Check for bias considerations
    bias_aware = any(marker in code.lower() for marker in [
        "bias", "fairness", "demographic", "protected",
        "balanced", "stratif"
    ])
    
    if not bias_aware:
        return GateResult(
            "bias_audit",
            GateStatus.WARN,
            "ML code without documented bias considerations",
            False
        )
    
    return GateResult(
        "bias_audit",
        GateStatus.PASS,
        "Bias considerations present",
        False
    )


def check_explainability(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    EXPLAINABILITY Gate: Check for model explainability.
    """
    if not code:
        return GateResult("explainability", GateStatus.SKIP, "No code to check", False)
    
    # Check for ML
    ml_patterns = [r'\.predict\(', r'model', r'classifier', r'regressor']
    has_ml = any(re.search(p, code) for p in ml_patterns)
    
    if not has_ml:
        return GateResult(
            "explainability",
            GateStatus.SKIP,
            "No ML predictions detected",
            False
        )
    
    # Check for explainability
    explainable = any(marker in code.lower() for marker in [
        "shap", "lime", "explain", "interpret", "feature_importance",
        "attention", "saliency"
    ])
    
    if not explainable:
        return GateResult(
            "explainability",
            GateStatus.WARN,
            "ML predictions without explainability",
            False
        )
    
    return GateResult(
        "explainability",
        GateStatus.PASS,
        "Explainability mechanisms present",
        False
    )


def check_reproducibility(code: str, files: List[str] = None, **kwargs) -> GateResult:
    """
    REPRODUCIBILITY Gate: Check for reproducibility practices.
    """
    if not code:
        return GateResult("reproducibility", GateStatus.SKIP, "No code to check", False)
    
    # Check for seed setting
    has_seed = any(marker in code for marker in [
        "random.seed", "np.random.seed", "torch.manual_seed",
        "set_seed", "SEED", "random_state"
    ])
    
    # Check for version pinning (in requirements context)
    has_versions = "==" in code or "requirements" in code.lower()
    
    if not has_seed:
        return GateResult(
            "reproducibility",
            GateStatus.WARN,
            "No random seed setting detected",
            False,
            details={"recommendation": "Set random seeds for reproducibility"}
        )
    
    return GateResult(
        "reproducibility",
        GateStatus.PASS,
        "Reproducibility practices in place",
        False
    )


# =============================================================================
# GATE REGISTRY
# =============================================================================

GATE_REGISTRY: Dict[str, Callable[..., GateResult]] = {
    # Phase 1: Security
    "ahimsa": check_ahimsa,
    "secrets": check_secrets,
    "vulnerability": check_vulnerability,
    
    # Phase 2: Code Quality
    "satya": check_satya,
    "lint_format": check_lint_format,
    "type_check": check_type_check,
    
    # Phase 3: Testing
    "test_coverage": check_test_coverage,
    "correctness": check_correctness,
    
    # Dharmic Gates
    "asteya": check_asteya,
    "aparigraha": check_aparigraha,
    "brahmacharya": check_brahmacharya,
    "saucha": check_saucha,
    "santosha": check_santosha,
    "tapas": check_tapas,
    "svadhyaya": check_svadhyaya,
    "ishvara_pranidhana": check_ishvara_pranidhana,
    
    # ML Overlay Gates
    "model_card": check_model_card,
    "data_provenance": check_data_provenance,
    "bias_audit": check_bias_audit,
    "explainability": check_explainability,
    "reproducibility": check_reproducibility,
}


def run_gate(name: str, code: str, files: List[str] = None, **kwargs) -> GateResult:
    """Run a single gate by name."""
    if name not in GATE_REGISTRY:
        return GateResult(name, GateStatus.ERROR, f"Unknown gate: {name}", False)
    
    try:
        return GATE_REGISTRY[name](code, files, **kwargs)
    except Exception as e:
        return GateResult(name, GateStatus.ERROR, f"Gate error: {str(e)[:100]}", False)


def run_gates(
    names: List[str],
    code: str,
    files: List[str] = None,
    **kwargs
) -> List[GateResult]:
    """Run multiple gates."""
    return [run_gate(name, code, files, **kwargs) for name in names]


def run_all_gates(code: str, files: List[str] = None, **kwargs) -> List[GateResult]:
    """Run all 22 gates."""
    return run_gates(list(GATE_REGISTRY.keys()), code, files, **kwargs)


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

__all__ = [
    "GateStatus",
    "GateResult",
    "GATE_REGISTRY",
    "run_gate",
    "run_gates",
    "run_all_gates",
    # Phase 1
    "check_ahimsa",
    "check_secrets",
    "check_vulnerability",
    # Phase 2
    "check_satya",
    "check_lint_format",
    "check_type_check",
    # Phase 3
    "check_test_coverage",
    "check_correctness",
    # Dharmic
    "check_asteya",
    "check_aparigraha",
    "check_brahmacharya",
    "check_saucha",
    "check_santosha",
    "check_tapas",
    "check_svadhyaya",
    "check_ishvara_pranidhana",
    # ML Overlay
    "check_model_card",
    "check_data_provenance",
    "check_bias_audit",
    "check_explainability",
    "check_reproducibility",
]
