# PENETRATION TESTING GUIDE
## Dharmic Agora 22-Gate Protocol

**Classification:** RESTRICTED  
**Version:** 2.0  
**Last Updated:** 2026-02-06

---

## 1. SCOPE

### In Scope
- 22-Gate Protocol implementation
- Ed25519 authentication system
- Chained hash audit trail
- SSRF protection layer
- Rate limiting infrastructure
- Content verification pipeline
- Token revocation system
- Anomaly detection engine

### Out of Scope
- Physical security
- Third-party dependencies
- Client-side vulnerabilities
- Social engineering

---

## 2. TESTING METHODOLOGY

### 2.1 Automated Scanning

```bash
# Dependency vulnerability scan
npm audit --audit-level moderate

# Static analysis
eslint --ext .ts src/
sonar-scanner

# Dependency check
snyk test

# Secret detection
git-secrets --scan
```

### 2.2 Manual Testing

#### Test 1: Gate Bypass Attempts

```typescript
// Test ID: GATE-001
// Objective: Bypass Ahimsa (non-harm) gate

describe('Gate Bypass Tests', () => {
  test('should block SQL injection', async () => {
    const context = createTestContext({
      payload: "'; DROP TABLE users; --"
    });
    const result = await gateAhimsa(context);
    expect(result.passed).toBe(false);
    expect(result.severity).toBe('critical');
  });

  test('should block XSS attempts', async () => {
    const context = createTestContext({
      payload: '<script>alert("xss")</script>'
    });
    const result = await gateAhimsa(context);
    expect(result.passed).toBe(false);
  });

  test('should block encoded attacks', async () => {
    const context = createTestContext({
      payload: '%3Cscript%3Ealert(1)%3C%2Fscript%3E'
    });
    const result = await gateAhimsa(context);
    expect(result.passed).toBe(false);
  });
});
```

#### Test 2: Authentication Bypass

```typescript
// Test ID: AUTH-001
// Objective: Bypass Ed25519 authentication

describe('Authentication Security', () => {
  test('should reject replay attacks', async () => {
    const message = 'test-message';
    const signature = authSystem.sign(message, validPrivateKey);
    
    // First attempt should succeed
    const result1 = await authSystem.authenticate(userId, message, signature);
    expect(result1.valid).toBe(true);
    
    // Replay should fail (nonce tracking)
    const result2 = await authSystem.authenticate(userId, message, signature);
    expect(result2.valid).toBe(false);
  });

  test('should reject forged signatures', async () => {
    const message = 'test-message';
    const forgedSig = 'invalid-signature';
    
    const result = await authSystem.authenticate(userId, message, forgedSig);
    expect(result.valid).toBe(false);
  });

  test('should reject expired tokens', async () => {
    const oldToken = generateExpiredToken();
    const result = await validateToken(oldToken);
    expect(result.valid).toBe(false);
    expect(result.reason).toContain('expired');
  });
});
```

#### Test 3: SSRF Exploitation

```typescript
// Test ID: SSRF-001
// Objective: Access internal resources via SSRF

describe('SSRF Protection', () => {
  const ssrf = new SSRFProtection();

  test('should block localhost access', () => {
    const result = ssrf.validateUrl('http://localhost/admin');
    expect(result.valid).toBe(false);
  });

  test('should block 127.0.0.1 access', () => {
    const result = ssrf.validateUrl('http://127.0.0.1:8080/secrets');
    expect(result.valid).toBe(false);
  });

  test('should block AWS metadata', () => {
    const result = ssrf.validateUrl('http://169.254.169.254/latest/meta-data/');
    expect(result.valid).toBe(false);
  });

  test('should block private IP ranges', () => {
    const privateIps = [
      'http://10.0.0.1/',
      'http://192.168.1.1/',
      'http://172.16.0.1/',
    ];
    
    for (const url of privateIps) {
      expect(ssrf.validateUrl(url).valid).toBe(false);
    }
  });

  test('should block DNS rebinding', async () => {
    // Simulate DNS rebinding attack
    const maliciousHost = 'attacker.com';
    
    // First resolution: public IP (passes)
    mockDnsResolution(maliciousHost, '1.2.3.4');
    expect(ssrf.validateUrl(`http://${maliciousHost}/`).valid).toBe(true);
    
    // Second resolution: private IP (should be blocked by cache)
    mockDnsResolution(maliciousHost, '10.0.0.1');
    expect(ssrf.validateUrl(`http://${maliciousHost}/`).valid).toBe(false);
  });
});
```

#### Test 4: Rate Limiting Evasion

```typescript
// Test ID: RATE-001
// Objective: Bypass rate limiting

describe('Rate Limiting Security', () => {
  const limiter = new RateLimiter();

  test('should enforce request limits', async () => {
    const identifier = 'test-client';
    
    // Fill up the bucket
    for (let i = 0; i < 110; i++) {
      limiter.checkLimit(identifier);
    }
    
    // Next request should be blocked
    const result = limiter.checkLimit(identifier);
    expect(result.allowed).toBe(false);
    expect(result.retryAfter).toBeGreaterThan(0);
  });

  test('should track across IP spoofing attempts', async () => {
    const baseIp = '192.168.1.';
    
    // Attempt to evade by cycling IPs
    for (let i = 1; i <= 50; i++) {
      const ip = `${baseIp}${i}`;
      const result = limiter.checkLimit(ip);
      
      // All should be tracked (no easy evasion)
      expect(result.remaining).toBeLessThan(110);
    }
  });

  test('should apply progressive penalties', async () => {
    const ip = '10.0.0.1';
    
    // Simulate DDoS
    for (let i = 0; i < 1500; i++) {
      limiter.checkLimit(ip);
    }
    
    const ddosCheck = limiter.checkDDoSProtection(ip);
    expect(ddosCheck.blocked).toBe(true);
    expect(ddosCheck.penaltyLevel).toBeGreaterThan(0);
  });
});
```

#### Test 5: Audit Chain Tampering

```typescript
// Test ID: AUDIT-001
// Objective: Tamper with audit trail

describe('Audit Trail Integrity', () => {
  test('should detect hash chain break', async () => {
    const audit = new ChainedAuditTrail(authSystem);
    
    // Create some entries
    await audit.createEntry(context1, [], 'ALLOWED');
    await audit.createEntry(context2, [], 'ALLOWED');
    
    // Tamper with chain (simulated)
    audit.chain[1].currentHash = 'tampered-hash';
    
    // Verification should fail
    const result = await audit.verifyChain();
    expect(result.valid).toBe(false);
    expect(result.tamperedAt).toBe(1);
  });

  test('should detect signature forgery', async () => {
    const audit = new ChainedAuditTrail(authSystem);
    
    await audit.createEntry(context1, [], 'ALLOWED');
    
    // Forge signature
    audit.chain[0].signature = 'forged-signature';
    
    const result = await audit.verifyChain();
    expect(result.valid).toBe(false);
  });

  test('should detect missing entries', async () => {
    const audit = new ChainedAuditTrail(authSystem);
    
    await audit.createEntry(context1, [], 'ALLOWED');
    await audit.createEntry(context2, [], 'ALLOWED');
    await audit.createEntry(context3, [], 'ALLOWED');
    
    // Remove middle entry
    audit.chain.splice(1, 1);
    
    const result = await audit.verifyChain();
    expect(result.valid).toBe(false);
  });
});
```

#### Test 6: Token Revocation Bypass

```typescript
// Test ID: TOKEN-001
// Objective: Use revoked tokens

describe('Token Revocation', () => {
  const revocation = new TokenRevocationSystem();

  test('should reject revoked tokens', () => {
    const tokenId = 'token-123';
    revocation.revokeToken(tokenId, 'compromised');
    
    const check = revocation.isRevoked(tokenId, 'user-1');
    expect(check.revoked).toBe(true);
    expect(check.reason).toContain('compromised');
  });

  test('should reject all user tokens after user revocation', () => {
    const userId = 'user-456';
    revocation.revokeUserTokens(userId, 'suspicious-activity');
    
    const check = revocation.isRevoked('any-token', userId);
    expect(check.revoked).toBe(true);
  });

  test('should handle CRL distribution', () => {
    revocation.revokeToken('token-a', 'test');
    revocation.revokeToken('token-b', 'test');
    revocation.revokeUserTokens('user-x', 'test');
    
    const crl = revocation.getRevocationList();
    expect(crl.tokens).toHaveLength(2);
    expect(crl.users).toHaveLength(1);
  });
});
```

---

## 3. FUZZING TESTS

### 3.1 Input Fuzzing

```bash
# Install fuzzing tools
npm install --save-dev fast-check

# Run fuzz tests
npm run test:fuzz
```

```typescript
import * as fc from 'fast-check';

describe('Fuzz Tests', () => {
  test('gateAhimsa should handle arbitrary input', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string(),
        async (payload) => {
          const context = createTestContext({ payload });
          const result = await gateAhimsa(context);
          // Should never throw, always return valid GateResult
          expect(result).toHaveProperty('gateId');
          expect(result).toHaveProperty('passed');
          expect(result).toHaveProperty('severity');
        }
      ),
      { numRuns: 1000 }
    );
  });

  test('SSRF should handle malformed URLs', async () => {
    const ssrf = new SSRFProtection();
    
    await fc.assert(
      fc.property(
        fc.string(),
        (url) => {
          const result = ssrf.validateUrl(url);
          // Should always return boolean, never throw
          expect(typeof result.valid).toBe('boolean');
        }
      ),
      { numRuns: 1000 }
    );
  });
});
```

---

## 4. LOAD TESTING

### 4.1 Concurrent Request Handling

```bash
# Using k6 for load testing
k6 run load-test.js
```

```javascript
// load-test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
};

export default function() {
  const payload = JSON.stringify({
    action: 'test',
    resource: '/api/test',
  });
  
  const res = http.post('http://localhost:3000/api/secure', payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(res, {
    'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

---

## 5. SECURITY CHECKLIST

### Pre-Deployment

- [ ] All 22 gates implemented and tested
- [ ] Ed25519 key generation working
- [ ] Audit chain verification passing
- [ ] SSRF allowlist configured
- [ ] Rate limits calibrated
- [ ] Token revocation tested
- [ ] Anomaly detection baselines set
- [ ] Emergency procedures documented
- [ ] Incident response plan ready
- [ ] Security audit completed

### Post-Deployment

- [ ] Monitor audit logs for anomalies
- [ ] Verify rate limiting effectiveness
- [ ] Check SSRF block rate
- [ ] Review token revocation usage
- [ ] Validate anomaly detection accuracy
- [ ] Test emergency override
- [ ] Verify backup integrity
- [ ] Confirm CRL distribution

---

## 6. REPORTING TEMPLATE

```markdown
## Penetration Test Report

**Date:** [DATE]
**Tester:** [NAME]
**Scope:** 22-Gate Protocol

### Findings Summary
| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | ✅ |
| High | 0 | ✅ |
| Medium | [N] | [Status] |
| Low | [N] | [Status] |
| Info | [N] | [Status] |

### Detailed Findings

#### Finding #[N]: [Title]
- **Severity:** [Level]
- **Gate Affected:** [Gate ID]
- **Description:** [Details]
- **Reproduction:** [Steps]
- **Impact:** [Analysis]
- **Remediation:** [Fix]

### Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

### Conclusion
[Overall assessment]
```

---

**Next Review:** 2026-05-06  
**Approved By:** DGC Security Subcommittee

**S(x) = x 🛡️🪷**
