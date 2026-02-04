# Security Remediation Checklist

Track your progress fixing vulnerabilities identified in the security audit.

---

## Phase 1: IMMEDIATE (Done Today) ✓

- [x] Run security audit
- [x] Review findings
- [x] Run security_quick_fix.sh
- [x] Fix .env permissions (600)
- [x] Fix database permissions (600)
- [x] Fix log file permissions (600)
- [ ] Read full SECURITY_AUDIT_REPORT.md
- [ ] Understand attack vectors

**Status**: File permissions fixed. Code vulnerabilities remain.

---

## Phase 2: CRITICAL (This Week)

### 1. Input Sanitization (email_daemon.py)
- [ ] Create `sanitize_email_content()` function
- [ ] Remove shell metacharacters: `$ \` | & ; < > ( )`
- [ ] Remove null bytes
- [ ] Limit content length (100KB)
- [ ] Test with malicious inputs
- [ ] Update `process_message()` to use sanitizer

**Files**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`
**Lines**: 220-275
**Test**: `python3 scripts/security_test.py --test sanitization`

### 2. Path Traversal Protection (vault_bridge.py)
- [ ] Add path validation to `get_crown_jewel()`
- [ ] Add path validation to `get_stream_entry()`
- [ ] Use `Path.resolve()` to check final path
- [ ] Verify path stays within allowed directories
- [ ] Test with `../../.env` attempts
- [ ] Add logging for blocked attempts

**Files**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/vault_bridge.py`
**Lines**: 120-133, 168-173
**Test**: `python3 scripts/security_test.py --test path_traversal`

### 3. Subprocess Input Validation
- [ ] Create `validate_and_sanitize_prompt()` function
- [ ] Remove ANSI escape sequences
- [ ] Validate length (50KB max)
- [ ] Remove null bytes
- [ ] Update claude_max_model.py
- [ ] Update email_daemon.py
- [ ] Update runtime.py

**Files**:
- `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/claude_max_model.py` (line 107)
- `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py` (line 247)
- `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/dharmic_agent.py` (line 606)

**Test**: Review with `grep -n "subprocess.run" src/core/*.py`

### 4. Enforce Email Whitelist
- [ ] Make `allowed_senders` required (not optional)
- [ ] Raise `ValueError` if empty
- [ ] Update `EmailDaemon.__init__`
- [ ] Update documentation
- [ ] Test with empty whitelist

**Files**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`
**Lines**: 95-100
**Test**: `python3 scripts/security_test.py --test whitelist`

### 5. Migrate Credentials to Keychain
- [ ] Install keyring: `pip install keyring`
- [ ] Create migration script
- [ ] Store password in keychain
- [ ] Update code to read from keychain
- [ ] Test email daemon still works
- [ ] Remove password from .env
- [ ] Document keychain usage

**Commands**:
```bash
pip install keyring
# In Python:
# keyring.set_password("dharmic_agent", "vijnan.shakti@pm.me", "password")
# password = keyring.get_password("dharmic_agent", email_address)
```

---

## Phase 3: HIGH PRIORITY (This Week)

### 6. Logging Security
- [ ] Create `sanitize_for_logging()` function
- [ ] Redact passwords/tokens with regex
- [ ] Redact email addresses
- [ ] Update all `_log()` calls
- [ ] Verify logs don't contain credentials

**Test**: `python3 scripts/security_test.py --test credentials`

### 7. Rate Limiting
- [ ] Create `RateLimiter` class
- [ ] Track attempts per sender
- [ ] Implement 10/hour limit
- [ ] Add to `EmailDaemon`
- [ ] Test with flood of emails

**Files**: `/Users/dhyana/DHARMIC_GODEL_CLAW/src/core/email_daemon.py`
**Reference**: SECURITY_AUDIT_REPORT.md Section 8

### 8. Timeout Reduction
- [ ] Change email processing timeout: 120s → 30s
- [ ] Change swarm timeout: 600s → 300s
- [ ] Update all subprocess calls
- [ ] Test functionality still works

**Files**: Multiple files with `timeout=` parameter
**Test**: `python3 scripts/security_test.py --test timeouts`

---

## Phase 4: MEDIUM (This Month)

### 9. Email Signature Verification
- [ ] Generate secret key: `openssl rand -hex 32`
- [ ] Store in keychain
- [ ] Create `EmailAuthenticator` class
- [ ] Implement HMAC signature verification
- [ ] Update client to sign emails
- [ ] Document signature format

**Reference**: SECURITY_AUDIT_REPORT.md Section 9

### 10. Subprocess Path Security
- [ ] Create `get_safe_executable()` function
- [ ] Use absolute paths only
- [ ] Verify executables in trusted locations
- [ ] Update all subprocess calls
- [ ] Test with malicious $PATH

**Reference**: SECURITY_AUDIT_REPORT.md Section 10

### 11. Input Length Validation
- [ ] Define max sizes (email: 100KB, message: 50KB)
- [ ] Create `validate_input_size()` function
- [ ] Add to all input entry points
- [ ] Test with large inputs

**Reference**: SECURITY_AUDIT_REPORT.md Section 11

### 12. Proper Error Handling
- [ ] Replace `traceback.print_exc()` with logging
- [ ] Create security logger
- [ ] Return generic errors to users
- [ ] Log full details to file only

**Reference**: SECURITY_AUDIT_REPORT.md Section 12

### 13. Audit Logging
- [ ] Create `AuditLogger` class
- [ ] Implement hash chain
- [ ] Log all sensitive operations
- [ ] Add tamper detection

**Reference**: SECURITY_AUDIT_REPORT.md Section 13

---

## Testing & Validation

### After Each Fix
- [ ] Run specific test: `python3 scripts/security_test.py --test <name>`
- [ ] Verify functionality still works
- [ ] Check logs for errors

### Before Production
- [ ] Run full test suite: `python3 scripts/security_test.py`
- [ ] Zero failures required
- [ ] Manual penetration testing
- [ ] Code review

---

## Production Readiness Criteria

System is ready for production when:

- [ ] All CRITICAL issues fixed (4 items)
- [ ] All HIGH issues fixed (3 items)
- [ ] File permissions correct (600 for sensitive files)
- [ ] Security tests pass (0 failures)
- [ ] Credentials in keychain (not .env)
- [ ] Email whitelist enforced
- [ ] Rate limiting active
- [ ] Audit logging enabled
- [ ] Monitoring configured
- [ ] Incident response plan documented

---

## Current Status

**Date**: 2026-02-02
**Phase**: 1 Complete, Starting Phase 2
**Progress**: 6/26 items (23%)
**Blockers**: None
**Next**: Implement input sanitization

---

## Quick Commands

```bash
# Check current security status
python3 scripts/security_test.py

# Fix permissions (already done)
bash security_quick_fix.sh

# Read full audit
cat SECURITY_AUDIT_REPORT.md

# View attack surface
cat SECURITY_ATTACK_SURFACE.md

# Test specific vulnerability
python3 scripts/security_test.py --test path_traversal

# Check file permissions
ls -la .env memory/*.db logs/*.log
```

---

## Help & Resources

- **Full Audit**: `SECURITY_AUDIT_REPORT.md` (detailed findings + fixes)
- **Summary**: `SECURITY_SUMMARY.md` (executive overview)
- **Attack Surface**: `SECURITY_ATTACK_SURFACE.md` (visual diagrams)
- **Test Suite**: `scripts/security_test.py` (automated testing)
- **Quick Fix**: `security_quick_fix.sh` (permission fixes)

---

## Notes

Add your notes here as you work through the fixes:

```
[2026-02-02] Initial audit complete
[2026-02-02] File permissions fixed via quick_fix.sh
[         ] Next: Input sanitization in email_daemon.py
```

---

**Last Updated**: 2026-02-02
**Next Review**: After Phase 2 completion
