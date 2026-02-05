#!/usr/bin/env python3
"""
🔒 CI Gate Runner — Test GitHub Actions locally

Runs the same gates as the CI workflow for local validation before push.

Usage:
    python scripts/run-ci-gates.py [--security-only] [--all]

Options:
    --security-only  Run only security gates (AHIMSA, SECRETS, VULNERABILITY)
    --all            Run all 22 gates
    (default)        Run CI gates (security + quality + tests)

JSCA! 🔒
"""

import argparse
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.core.cosmic_krishna_coder.gates import (
    check_ahimsa,
    check_secrets,
    check_vulnerability,
    check_satya,
    check_lint_format,
    check_type_check,
    check_test_coverage,
    check_correctness,
    run_all_gates,
    GateStatus,
)


def collect_python_files(directory: Path) -> list:
    """Collect all Python files in directory."""
    return list(directory.rglob("*.py"))


def read_all_code(files: list) -> str:
    """Read and concatenate all code."""
    code_parts = []
    for f in files:
        try:
            code_parts.append(f.read_text())
        except:
            pass
    return "\n\n".join(code_parts)


def print_result(name: str, result, blocking: bool = False):
    """Print gate result with formatting."""
    status_emoji = {
        GateStatus.PASS: "✅",
        GateStatus.WARN: "⚠️",
        GateStatus.FAIL: "❌",
        GateStatus.SKIP: "⏭️",
        GateStatus.ERROR: "💥",
    }
    
    emoji = status_emoji.get(result.status, "❓")
    block_marker = " [BLOCKING]" if blocking and result.status == GateStatus.FAIL else ""
    print(f"  {emoji} {name}: {result.message}{block_marker}")
    
    return result.status == GateStatus.FAIL and blocking


def run_security_gates(code: str, files: list) -> bool:
    """Run security gates. Returns True if any blocking failure."""
    print("\n🛡️ SECURITY GATES")
    print("-" * 40)
    
    failed = False
    
    failed |= print_result("AHIMSA", check_ahimsa(code, files), blocking=True)
    failed |= print_result("SECRETS", check_secrets(code, files), blocking=True)
    failed |= print_result("VULNERABILITY", check_vulnerability(code, files), blocking=True)
    
    return failed


def run_quality_gates(code: str, files: list) -> bool:
    """Run quality gates. Returns True if any blocking failure."""
    print("\n📝 QUALITY GATES")
    print("-" * 40)
    
    failed = False
    
    print_result("SATYA", check_satya(code, files), blocking=False)
    print_result("LINT_FORMAT", check_lint_format(code, files), blocking=False)
    print_result("TYPE_CHECK", check_type_check(code, files), blocking=False)
    
    return failed


def run_test_gates(code: str, files: list) -> bool:
    """Run test gates. Returns True if any blocking failure."""
    print("\n🧪 TEST GATES")
    print("-" * 40)
    
    failed = False
    
    failed |= print_result("CORRECTNESS", check_correctness(code, files), blocking=True)
    print_result("TEST_COVERAGE", check_test_coverage(code, files), blocking=False)
    
    return failed


def run_all(code: str, files: list) -> bool:
    """Run all 22 gates."""
    print("\n🔒 ALL 22 GATES")
    print("-" * 40)
    
    results = run_all_gates(code, files)
    
    blocking_gates = ["ahimsa", "secrets", "vulnerability", "correctness"]
    failed = False
    
    for result in results:
        is_blocking = result.name in blocking_gates
        if print_result(result.name.upper(), result, blocking=is_blocking):
            failed = True
    
    return failed


def main():
    parser = argparse.ArgumentParser(description="Run CI gates locally")
    parser.add_argument("--security-only", action="store_true", help="Run only security gates")
    parser.add_argument("--all", action="store_true", help="Run all 22 gates")
    args = parser.parse_args()
    
    print("=" * 50)
    print("🔒 DHARMIC CI GATE RUNNER")
    print("=" * 50)
    
    # Collect files
    src_dir = repo_root / "src"
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return 1
    
    files = collect_python_files(src_dir)
    print(f"\n📁 Found {len(files)} Python files in src/")
    
    # Read code
    code = read_all_code(files)
    file_paths = [str(f) for f in files]
    
    # Run gates
    failed = False
    
    if args.all:
        failed = run_all(code, file_paths)
    elif args.security_only:
        failed = run_security_gates(code, file_paths)
    else:
        # Default: CI gates (security + quality + tests)
        failed |= run_security_gates(code, file_paths)
        failed |= run_quality_gates(code, file_paths)
        failed |= run_test_gates(code, file_paths)
    
    # Summary
    print("\n" + "=" * 50)
    if failed:
        print("❌ GATES FAILED — Fix issues before pushing")
        return 1
    else:
        print("✅ ALL GATES PASSED — Ready to push")
        return 0


if __name__ == "__main__":
    sys.exit(main())
