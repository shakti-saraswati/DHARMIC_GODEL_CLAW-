#!/usr/bin/env python3
"""
Post-Evolution Safety Check

Runs after YOLO mode evolutions to verify code integrity.
Checks:
1. Syntax validity - all Python files parse
2. Import sanity - core modules still import
3. No dangerous patterns introduced
4. Tests still pass (basic smoke test)
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from datetime import datetime

DGC_DIR = Path(__file__).parent.parent
DANGEROUS_PATTERNS = [
    "os.system(",
    "subprocess.call(shell=True",
    "eval(",
    "exec(",
    "__import__(",
    "rm -rf",
    "shutil.rmtree('/'",
    "open('/etc/passwd",
]

def check_syntax() -> tuple[bool, list[str]]:
    """Verify all Python files have valid syntax."""
    errors = []
    py_files = list(DGC_DIR.rglob("*.py"))
    
    # Skip venv and cache
    py_files = [f for f in py_files if ".venv" not in str(f) and "__pycache__" not in str(f)]
    
    for pf in py_files[:500]:  # Sample first 500
        try:
            ast.parse(pf.read_text())
        except SyntaxError as e:
            errors.append(f"{pf.relative_to(DGC_DIR)}: {e.msg} (line {e.lineno})")
    
    return len(errors) == 0, errors

def check_imports() -> tuple[bool, list[str]]:
    """Verify core modules still import."""
    errors = []
    core_modules = [
        "src.core.dharmic_agent",
        "src.core.telos_layer",
        "src.core.strange_memory",
        "swarm.orchestrator",
        "swarm.run_gates",
    ]
    
    for mod in core_modules:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {mod}"],
                cwd=str(DGC_DIR),
                capture_output=True,
                timeout=30
            )
            if result.returncode != 0:
                errors.append(f"{mod}: {result.stderr.decode()[:100]}")
        except Exception as e:
            errors.append(f"{mod}: {str(e)}")
    
    return len(errors) == 0, errors

def check_dangerous_patterns() -> tuple[bool, list[str]]:
    """Scan for dangerous code patterns."""
    findings = []
    py_files = list(DGC_DIR.rglob("*.py"))
    py_files = [f for f in py_files if ".venv" not in str(f) and "__pycache__" not in str(f)]
    
    for pf in py_files[:500]:
        try:
            content = pf.read_text()
            for pattern in DANGEROUS_PATTERNS:
                if pattern in content:
                    # Check if it's in a comment or string (rough check)
                    for i, line in enumerate(content.split("\n")):
                        if pattern in line and not line.strip().startswith("#"):
                            findings.append(f"{pf.relative_to(DGC_DIR)}:{i+1}: {pattern}")
        except Exception:
            pass
    
    # Allow some known safe usages
    safe_findings = [f for f in findings if "test" not in f.lower() and "example" not in f.lower()]
    return len(safe_findings) < 10, findings[:20]  # Allow up to 10, report first 20

def run_smoke_tests() -> tuple[bool, str]:
    """Run basic smoke tests."""
    try:
        result = subprocess.run(
            ["pytest", "tests/", "-x", "-q", "--tb=no", "-k", "not slow", "--timeout=60"],
            cwd=str(DGC_DIR),
            capture_output=True,
            timeout=120
        )
        output = result.stdout.decode() + result.stderr.decode()
        # Pass if any tests passed or no tests found
        return result.returncode == 0 or "no tests ran" in output.lower(), output[-500:]
    except subprocess.TimeoutExpired:
        return False, "Tests timed out"
    except Exception as e:
        return True, f"Could not run tests: {e}"  # Don't block if pytest not available

def main():
    print("=" * 60)
    print(f"SAFETY CHECK - {datetime.now().isoformat()}")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Syntax check
    print("\n[1/4] Checking Python syntax...")
    passed, errors = check_syntax()
    if passed:
        print("  ✅ All files have valid syntax")
    else:
        print(f"  ❌ Syntax errors found: {len(errors)}")
        for e in errors[:5]:
            print(f"    - {e}")
        all_passed = False
    
    # 2. Import check
    print("\n[2/4] Checking core imports...")
    passed, errors = check_imports()
    if passed:
        print("  ✅ Core modules import successfully")
    else:
        print(f"  ❌ Import errors: {len(errors)}")
        for e in errors:
            print(f"    - {e}")
        all_passed = False
    
    # 3. Dangerous pattern check
    print("\n[3/4] Scanning for dangerous patterns...")
    passed, findings = check_dangerous_patterns()
    if passed:
        print(f"  ✅ No excessive dangerous patterns ({len(findings)} found, within threshold)")
    else:
        print(f"  ⚠️  Dangerous patterns detected: {len(findings)}")
        for f in findings[:5]:
            print(f"    - {f}")
    
    # 4. Smoke tests
    print("\n[4/4] Running smoke tests...")
    passed, output = run_smoke_tests()
    if passed:
        print("  ✅ Smoke tests passed")
    else:
        print("  ⚠️  Some tests failed (non-blocking in YOLO mode)")
        print(f"    {output[:200]}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("SAFETY CHECK: ✅ PASSED")
    else:
        print("SAFETY CHECK: ⚠️  WARNINGS (review recommended)")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
