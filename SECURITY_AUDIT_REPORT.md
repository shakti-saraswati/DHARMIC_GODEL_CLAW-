# Security Audit Report: Dharmic Agent System

**Date**: 2026-02-02
**Auditor**: Security Engineer (Claude Code)
**System**: Dharmic Agent Core at /Users/dhyana/DHARMIC_GODEL_CLAW
**Scope**: Email processing, credential management, subprocess handling, file system operations

---

## Executive Summary

The Dharmic Agent system processes external email input, invokes subprocess commands (Claude CLI), and manages sensitive credentials. This audit identified **13 security vulnerabilities** ranging from CRITICAL to LOW severity, with **4 CRITICAL issues** requiring immediate attention.

### Critical Findings
1. **Email password hardcoded in .env with world-readable permissions**
2. **Command injection vulnerability in email subject/body processing**
3. **Arbitrary file read/write via email-controlled paths**
4. **Subprocess calls with unsanitized user input**

---

## Vulnerability Assessment

### 1. CRITICAL: Credential Exposure in .env File

**File**: `/Users/dhyana/DHARMIC_GODEL_CLAW/.env`
**Lines**: 1-6

**Issue**:
```bash
EMAIL_ADDRESS=vijnan.shakti@pm.me
EMAIL_PASSWORD=eXy3ffoYEiKb2Ocsf-CTzQ  # PLAINTEXT PASSWORD
```

**Permissions**: `-rw-r--r--` (644 - world readable)

**Impact**:
- Email credentials are stored in plaintext
- Any user on the system can read this file
- Password appears to be a Proton Mail Bridge token (still sensitive)
- If system is compromised, attacker gains email access

**Remediation**:
```bash
# Immediate fix
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/.env
# Verify
ls -la /Users/dhyana/DHARMIC_GODEL_CLAW/.env
# Should show: -rw------- (600)

# Long-term: Use macOS Keychain
# Install keyring library
pip install keyring

# Store password securely
import keyring
keyring.set_password("dharmic_agent", "vijnan.shakti@pm.me", "eXy3ffoYEiKb2Ocsf-CTzQ")

# Retrieve in code
password = keyring.get_password("dharmic_agent", email_address)
```

**Status**: .env is properly gitignored, but local file permissions are too permissive.

---

### 2. CRITICAL: Command Injection via Email Content

**File**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`
**Lines**: 221-275

**Issue**: Email subject and body are directly interpolated into subprocess commands without sanitization.

**Vulnerable Code**:
```python
result = subprocess.run(
    ["claude", "-p", f"{system_prompt}\n\n---\n\nEmail from John:\n{full_message}"],
    capture_output=True,
    text=True,
    timeout=120,
    cwd=str(Path(__file__).parent.parent.parent)
)
```

Where `full_message` contains:
```python
full_message = f"Subject: {message['subject']}\n\n{message['body']}"
```

**Attack Vector**:
An attacker could send an email with malicious content:
```
Subject: Test"; rm -rf /Users/dhyana/DHARMIC_GODEL_CLAW; echo "pwned
Body: Any content
```

While `subprocess.run` with a list is safer than shell=True, the `-p` argument value itself could contain escape sequences that the `claude` CLI might interpret dangerously.

**Impact**:
- Email content becomes part of command execution context
- Potential for arbitrary command execution
- System compromise via crafted email

**Remediation**:
```python
# Sanitize email content before processing
import shlex

def sanitize_email_content(content: str) -> str:
    """Remove potentially dangerous characters from email content."""
    # Remove control characters and shell metacharacters
    dangerous_chars = ['$', '`', '|', '&', ';', '\n\r', '<', '>', '(', ')']
    sanitized = content
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, ' ')
    # Limit length to prevent buffer overflow
    return sanitized[:10000]

# In process_message():
safe_subject = sanitize_email_content(message['subject'])
safe_body = sanitize_email_content(message['body'])
full_message = f"Subject: {safe_subject}\n\n{safe_body}"
```

**Alternative**: Use stdin instead of command-line arguments:
```python
result = subprocess.run(
    ["claude"],
    input=f"{system_prompt}\n\n---\n\nEmail:\n{full_message}",
    capture_output=True,
    text=True,
    timeout=120,
    encoding='utf-8'
)
```

---

### 3. CRITICAL: Path Traversal in Vault Operations

**File**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/vault_bridge.py`
**Lines**: 120-133, 168-173

**Issue**: User-provided filenames are used directly for file reads without path validation.

**Vulnerable Code**:
```python
def get_crown_jewel(self, name: str) -> Optional[str]:
    jewel_path = self.crown_jewels / f"{name}.md"
    if jewel_path.exists():
        self._record_read(jewel_path)
        return jewel_path.read_text()
```

**Attack Vector**:
```python
# Via email or chat interface
agent.read_crown_jewel("../../../../etc/passwd")
agent.read_stream_entry("../../.env")
```

**Impact**:
- Arbitrary file read from filesystem
- Exposure of sensitive system files
- Credential theft via .env file access

**Remediation**:
```python
from pathlib import Path

def get_crown_jewel(self, name: str) -> Optional[str]:
    """Read a specific crown jewel with path traversal protection."""
    # Sanitize name - remove path separators and parent references
    safe_name = Path(name).name  # Strips directory components
    if '..' in safe_name or safe_name.startswith('/'):
        return None

    jewel_path = self.crown_jewels / f"{safe_name}.md"

    # Verify resolved path is still within crown_jewels directory
    try:
        jewel_path = jewel_path.resolve()
        if not str(jewel_path).startswith(str(self.crown_jewels.resolve())):
            return None
    except Exception:
        return None

    if jewel_path.exists():
        self._record_read(jewel_path)
        return jewel_path.read_text()
    return None
```

Apply same fix to:
- `get_stream_entry()`
- `write_to_vault()` (already has some protection but needs strengthening)

---

### 4. CRITICAL: Subprocess Input Validation Missing

**Files**:
- `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/claude_max_model.py` (lines 107-113)
- `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/dharmic_agent.py` (lines 606-612)
- `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/runtime.py` (lines 470-475)

**Issue**: User messages are passed directly to subprocess commands without validation.

**Vulnerable Code** (claude_max_model.py):
```python
result = subprocess.run(
    ["claude", "-p", full_prompt],  # full_prompt contains user input
    capture_output=True,
    text=True,
    timeout=self.timeout,
    cwd=self.working_dir
)
```

**Impact**:
- Command injection if user input contains special characters
- Potential for privilege escalation
- System compromise

**Remediation**:
```python
import re

def validate_and_sanitize_prompt(prompt: str) -> str:
    """Validate and sanitize prompt for CLI execution."""
    # Remove null bytes
    prompt = prompt.replace('\x00', '')

    # Limit length to prevent resource exhaustion
    max_length = 50000
    if len(prompt) > max_length:
        prompt = prompt[:max_length]

    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    prompt = ansi_escape.sub('', prompt)

    return prompt

# In invoke():
safe_prompt = validate_and_sanitize_prompt(full_prompt)
result = subprocess.run(
    ["claude", "-p", safe_prompt],
    capture_output=True,
    text=True,
    timeout=self.timeout,
    cwd=self.working_dir
)
```

---

### 5. HIGH: Missing Email Sender Verification

**File**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`
**Lines**: 95-100, 158-161

**Issue**: Whitelist is optional and defaults to accepting emails from anyone.

**Vulnerable Code**:
```python
self.allowed_senders = allowed_senders or []  # empty = allow all
# ...
if self.allowed_senders and sender_email not in self.allowed_senders:
    # Only checks if whitelist exists
```

**Impact**:
- Anyone can send commands to the agent via email
- No authentication required
- Potential for abuse/spam/resource exhaustion

**Remediation**:
```python
# Make whitelist REQUIRED
def __init__(
    self,
    agent: DharmicAgent,
    config: EmailConfig = None,
    poll_interval: int = 60,
    allowed_senders: List[str] = None,  # REQUIRED
):
    self.agent = agent
    self.config = config or EmailConfig()
    self.poll_interval = poll_interval

    # ENFORCE whitelist
    if not allowed_senders:
        raise ValueError("allowed_senders is REQUIRED for security. Provide at least one email address.")
    self.allowed_senders = [s.lower() for s in allowed_senders]
```

**Configuration**:
```bash
# In .env or startup script
ALLOWED_SENDERS="john@example.com,dhyana@protonmail.com"
```

---

### 6. HIGH: Database Files World-Readable

**Files**: `/Users/dhyana/DHARMIC_GODEL_CLAW/memory/*.db`

**Permissions**:
```bash
-rw-r--r--  deep_memory.db       (644)
-rw-r--r--  dharmic_agent.db     (644)
-rw-r--r--  dharmic_team.db      (644)
```

**Issue**: Database files containing conversation history, memories, and potentially sensitive information are readable by all users on the system.

**Impact**:
- Privacy breach - anyone can read conversation history
- Memory data exposure
- Potential credential leakage if stored in memories

**Remediation**:
```bash
# Immediate fix
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/memory/*.db
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/memory/*.jsonl
chmod 700 /Users/dhyana/DHARMIC_GODEL_CLAW/memory

# Verify
ls -la /Users/dhyana/DHARMIC_GODEL_CLAW/memory/

# Add to initialization code (deep_memory.py, dharmic_agent.py)
import os
import stat

db_path = Path("memory/dharmic_agent.db")
if db_path.exists():
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
```

---

### 7. HIGH: Logging May Expose Credentials

**Files**: All logging throughout the system

**Issue**: System prompt and message content are logged, which may contain credentials or sensitive data.

**Vulnerable Code** (email_daemon.py line 248):
```python
result = subprocess.run(
    ["claude", "-p", f"{system_prompt}\n\n---\n\nEmail from John:\n{full_message}"],
    # ...
)
# If this fails, stderr might be logged with the full command
```

**Impact**:
- Credentials logged to disk
- Log files may be world-readable
- Forensic analysis reveals sensitive data

**Remediation**:
```python
def sanitize_for_logging(content: str) -> str:
    """Remove sensitive data from log messages."""
    import re
    # Redact email passwords, API keys, tokens
    content = re.sub(r'(password|token|api_key|secret)["\s:=]+([^"\s,}]+)',
                     r'\1: [REDACTED]', content, flags=re.IGNORECASE)
    # Redact email addresses
    content = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', content)
    return content

# In _log():
log_line = f"[{timestamp}] {sanitize_for_logging(message)}"
```

**Log File Permissions**:
```bash
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/logs/*.log
chmod 700 /Users/dhyana/DHARMIC_GODEL_CLAW/logs
```

---

### 8. MEDIUM: Timeout Too Long for Untrusted Input

**Files**: Multiple files with subprocess timeouts

**Issue**: 120-600 second timeouts allow resource exhaustion attacks.

**Vulnerable Code**:
```python
# email_daemon.py line 251
timeout=120  # 2 minutes per email

# runtime.py line 474
timeout=600  # 10 minutes for swarm
```

**Impact**:
- Attacker can send many emails to exhaust resources
- Long-running processes block daemon
- Denial of service

**Remediation**:
```python
# Shorter timeouts for external input
timeout=30  # 30 seconds for email processing

# Rate limiting
from collections import defaultdict
from time import time

class RateLimiter:
    def __init__(self, max_per_hour=10):
        self.attempts = defaultdict(list)
        self.max_per_hour = max_per_hour

    def is_allowed(self, sender: str) -> bool:
        now = time()
        cutoff = now - 3600  # 1 hour ago
        # Clean old attempts
        self.attempts[sender] = [t for t in self.attempts[sender] if t > cutoff]

        if len(self.attempts[sender]) >= self.max_per_hour:
            return False

        self.attempts[sender].append(now)
        return True

# In EmailDaemon.__init__:
self.rate_limiter = RateLimiter(max_per_hour=10)

# In process_message:
if not self.rate_limiter.is_allowed(message['from']):
    return "Rate limit exceeded. Try again later."
```

---

### 9. MEDIUM: No CSRF/Request Signing on Email Commands

**File**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`

**Issue**: No way to verify that commands via email are legitimate (no HMAC, no signature).

**Impact**:
- Email spoofing attacks possible
- Attacker can forge "From" addresses
- No non-repudiation

**Remediation**:
```python
import hmac
import hashlib
from datetime import datetime

class EmailAuthenticator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def verify_email(self, message: dict) -> bool:
        """Verify email has valid signature in subject or body."""
        # Expected format: "Command text [SIG:timestamp:signature]"
        content = message['body']

        # Extract signature
        import re
        match = re.search(r'\[SIG:(\d+):([a-f0-9]+)\]', content)
        if not match:
            return False

        timestamp = int(match.group(1))
        signature = match.group(2)

        # Check timestamp is recent (within 5 minutes)
        now = int(datetime.now().timestamp())
        if abs(now - timestamp) > 300:
            return False

        # Verify signature
        message_to_sign = f"{message['from']}:{timestamp}:{content[:match.start()]}"
        expected_sig = hmac.new(
            self.secret_key,
            message_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_sig)

# Usage:
SECRET_KEY = os.getenv("EMAIL_SECRET_KEY")  # Generate and store securely
authenticator = EmailAuthenticator(SECRET_KEY)

if not authenticator.verify_email(message):
    self._log(f"SECURITY: Email from {message['from']} failed authentication")
    continue
```

---

### 10. MEDIUM: Working Directory May Be Untrusted

**Files**: Multiple subprocess calls with `cwd=` parameter

**Issue**: Working directory is set to project root, which may contain malicious files.

**Vulnerable Code** (runtime.py line 452):
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=600,
    cwd=str(Path(__file__).parent.parent.parent)  # Project root
)
```

**Impact**:
- If attacker writes malicious `claude` script to project directory
- PATH manipulation could execute wrong binary
- Relative path attacks

**Remediation**:
```python
# Use absolute paths for executables
import shutil

def get_safe_executable(name: str) -> str:
    """Get absolute path to executable, verify it's safe."""
    exe_path = shutil.which(name)
    if exe_path is None:
        raise FileNotFoundError(f"{name} not found in PATH")

    # Verify it's in a trusted location
    trusted_paths = ['/usr/local/bin', '/usr/bin', '/opt/homebrew/bin']
    if not any(exe_path.startswith(p) for p in trusted_paths):
        raise SecurityError(f"{name} not in trusted path: {exe_path}")

    return exe_path

# Usage:
claude_exe = get_safe_executable('claude')
result = subprocess.run(
    [claude_exe, "-p", sanitized_prompt],
    capture_output=True,
    text=True,
    timeout=30
)
```

---

### 11. LOW: Missing Input Length Validation

**Files**: Multiple files accepting user input

**Issue**: No limits on input length, could cause memory exhaustion.

**Impact**:
- Out of memory errors
- Denial of service
- System instability

**Remediation**:
```python
MAX_EMAIL_SIZE = 100_000  # 100KB
MAX_MESSAGE_SIZE = 50_000  # 50KB

def validate_input_size(content: str, max_size: int, name: str) -> str:
    """Validate input size and truncate if needed."""
    if len(content) > max_size:
        raise ValueError(f"{name} exceeds maximum size of {max_size} bytes")
    return content

# In fetch_unread():
body = validate_input_size(body, MAX_EMAIL_SIZE, "Email body")

# In run():
message = validate_input_size(message, MAX_MESSAGE_SIZE, "Message")
```

---

### 12. LOW: Exception Handling Exposes Stack Traces

**Files**: Multiple files with bare except blocks

**Vulnerable Code**:
```python
except Exception as e:
    self._log(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

**Issue**: Stack traces may reveal file paths, library versions, system information.

**Remediation**:
```python
import traceback
import logging

# Use proper logging with levels
logger = logging.getLogger(__name__)

try:
    # ... code ...
except Exception as e:
    # Log full trace to file (not console)
    logger.error("Operation failed", exc_info=True)
    # Return generic message to user
    return "An error occurred. Please contact support."
```

---

### 13. LOW: Missing Audit Trail for Sensitive Operations

**File**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/vault_bridge.py`

**Issue**: Vault writes are logged but not audit-logged with tamper protection.

**Recommendation**:
```python
import hashlib
import json

class AuditLogger:
    def __init__(self, audit_file: Path):
        self.audit_file = audit_file
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

    def log_action(self, action: str, details: dict, user: str = "dharmic_agent"):
        """Log action with hash chain for tamper detection."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": user,
            "details": details
        }

        # Read last hash
        last_hash = self._get_last_hash()
        entry["prev_hash"] = last_hash

        # Calculate current hash
        entry_json = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["hash"] = current_hash

        # Append to audit log
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _get_last_hash(self) -> str:
        """Get hash of last audit entry."""
        if not self.audit_file.exists():
            return "0" * 64

        with open(self.audit_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64
            last_entry = json.loads(lines[-1])
            return last_entry.get("hash", "0" * 64)
```

---

## Additional Security Recommendations

### 1. Environment Hardening

```bash
# Set up proper file permissions
chmod 700 /Users/dhyana/DHARMIC_GODEL_CLAW
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/.env
chmod 700 /Users/dhyana/DHARMIC_GODEL_CLAW/memory
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/memory/*
chmod 700 /Users/dhyana/DHARMIC_GODEL_CLAW/logs
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/logs/*.log

# Verify no secrets in git history
git log --all --full-history --source -- '*.env'
```

### 2. Dependency Security

```bash
# Scan dependencies for vulnerabilities
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
```

### 3. Network Security

```bash
# Verify Proton Bridge is running locally
lsof -i :1143
lsof -i :1025

# Firewall rules (macOS)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
```

### 4. Process Isolation

Consider running the email daemon with reduced privileges:
```bash
# Create dedicated user
sudo dscl . -create /Users/dharmic_daemon
sudo dscl . -create /Users/dharmic_daemon UserShell /bin/bash

# Run daemon as that user
sudo -u dharmic_daemon python3 email_daemon.py
```

### 5. Monitoring and Alerting

```python
# Add security event logging
class SecurityMonitor:
    def __init__(self):
        self.failed_auth_count = defaultdict(int)

    def log_security_event(self, event_type: str, details: dict):
        """Log and alert on security events."""
        logger = logging.getLogger("security")
        logger.warning(f"SECURITY EVENT: {event_type}", extra=details)

        # Alert on suspicious patterns
        if event_type == "failed_authentication":
            sender = details.get("sender")
            self.failed_auth_count[sender] += 1
            if self.failed_auth_count[sender] > 5:
                self.send_alert(f"Multiple failed auth from {sender}")

    def send_alert(self, message: str):
        """Send alert to admin."""
        # Email, SMS, or notification service
        pass
```

---

## Priority Remediation Plan

### Phase 1: IMMEDIATE (Do Today)

1. Fix .env file permissions: `chmod 600 .env`
2. Fix database file permissions: `chmod 600 memory/*.db`
3. Fix log file permissions: `chmod 600 logs/*.log`
4. Add whitelist enforcement to email daemon
5. Deploy sanitization for email content

**Time**: 30 minutes
**Impact**: Prevents credential exposure and unauthorized access

### Phase 2: URGENT (This Week)

1. Implement path traversal protection in vault_bridge.py
2. Add input validation to all subprocess calls
3. Implement rate limiting on email processing
4. Add proper error handling without stack trace exposure
5. Migrate credentials to keychain

**Time**: 4 hours
**Impact**: Prevents command injection and path traversal attacks

### Phase 3: IMPORTANT (This Month)

1. Implement email signature verification
2. Add audit logging for all sensitive operations
3. Set up security monitoring and alerting
4. Conduct penetration testing of email interface
5. Add process isolation for daemon

**Time**: 8 hours
**Impact**: Defense in depth, forensics capability

---

## Testing Recommendations

### Security Test Cases

```python
# Test 1: Path traversal protection
agent.read_crown_jewel("../../.env")  # Should fail
agent.read_crown_jewel("../../../../../etc/passwd")  # Should fail

# Test 2: Command injection protection
malicious_email = {
    'subject': '"; rm -rf /',
    'body': '$(cat /etc/passwd)',
    'from': 'attacker@evil.com'
}
# Should not execute commands

# Test 3: Rate limiting
for i in range(20):
    send_email_to_agent()
# Should block after limit

# Test 4: Input validation
huge_email = "A" * 1_000_000
send_email_with_body(huge_email)
# Should reject or truncate

# Test 5: Unauthorized sender
send_email_from("notwhitelisted@example.com")
# Should reject
```

---

## Compliance Notes

### Data Protection
- Email content may contain PII
- Conversation history stored in databases
- Consider GDPR/privacy implications
- Implement data retention policies

### Access Control
- No multi-user access control currently
- Single-user system assumed
- Consider role-based access if multi-user needed

---

## Conclusion

The Dharmic Agent system has significant security vulnerabilities primarily around:
1. Credential management
2. Input validation
3. Command injection prevention
4. File access control

**Immediate action required** on the 4 CRITICAL vulnerabilities to prevent system compromise.

The system is **NOT PRODUCTION-READY** in its current state for processing untrusted email input.

Estimated time to reach production security: **16-20 hours** of focused security engineering work.

---

## Contact

For questions about this audit:
- Review with John (Dhyana) Shrader
- Implement fixes before enabling email daemon in production
- Re-audit after remediation

**END AUDIT REPORT**
