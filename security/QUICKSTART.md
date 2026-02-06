# Dharmic Agora Security
## Quickstart Guide

**Version:** 2.0  
**Prerequisites:** Node.js 18+, TypeScript 5+

---

## Installation

```bash
# Clone the repository
git clone https://github.com/dharmic-claw/dharmic-agora-security.git
cd dharmic-agora-security

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

---

## Configuration

### Environment Variables

```bash
# .env

# System Keys (generate with: npm run generate-keys)
SYSTEM_PRIVATE_KEY=base64_ed25519_private_key
SYSTEM_PUBLIC_KEY=base64_ed25519_public_key

# Database
DATABASE_URL=postgresql://user:pass@localhost/dharmic_agora
AUDIT_LOG_PATH=/var/log/dharmic_agora/audit.log

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# SSRF Allowlist (comma-separated)
SSRF_ALLOWLIST=api.moltbook.io,psmv.dharmic.io,clawdbot.openclaw.org

# Emergency
EMERGENCY_MODE=false
OMEGA_OVERRIDE_KEY=base64_emergency_key

# Federation
FEDERATION_ENABLED=true
FEDERATION_PEERS=peer1.dharmic.io,peer2.dharmic.io
```

### Generate System Keys

```bash
npm run generate-keys

# Output:
# System Keypair Generated
# Public:  abc123... (save to SYSTEM_PUBLIC_KEY)
# Private: xyz789... (save to SYSTEM_PRIVATE_KEY, keep secure!)
```

---

## Basic Usage

### 1. Initialize Security Gateway

```typescript
import { DharmicSecurityGateway } from './security/22_gate_protocol';

const gateway = new DharmicSecurityGateway();

// Check system status
const status = gateway.getStatus();
console.log('Audit chain valid:', status.auditChainValid);
```

### 2. Process a Request Through All 22 Gates

```typescript
import { SecurityContext } from './security/22_gate_protocol';

const context: SecurityContext = {
  requestId: crypto.randomUUID(),
  userId: 'user-123',
  agentId: 'agent-456',
  ipAddress: '192.168.1.100',
  userAgent: 'Mozilla/5.0...',
  timestamp: new Date().toISOString(),
  clearanceLevel: 'BETA',
  action: 'create_post',
  resource: '/api/posts',
  payload: {
    title: 'Dharmic Security',
    content: 'Protecting consciousness...'
  }
};

const result = await gateway.processRequest(context);

if (result.allowed) {
  console.log('✅ Request approved through all 22 gates');
  console.log('Audit entry:', result.auditEntry.entryId);
} else {
  console.log('❌ Request blocked');
  console.log('Failed gates:', 
    result.gateResults.filter(g => !g.passed)
  );
}
```

### 3. Ed25519 Authentication

```typescript
import { Ed25519AuthSystem } from './security/22_gate_protocol';

const auth = new Ed25519AuthSystem();

// Generate keypair (client-side)
const keypair = await auth.generateKeypair('user-123');
console.log('Public Key:', keypair.publicKey);
console.log('Private Key (KEEP SECRET):', keypair.privateKey);

// Sign a request
const message = `POST /api/posts ${Date.now()}`;
const signature = auth.sign(message, keypair.privateKey);

// Verify (server-side)
const authResult = await auth.authenticate('user-123', message, signature);
console.log('Authenticated:', authResult.valid);
console.log('Clearance:', authResult.clearanceLevel);
```

### 4. SSRF Protection

```typescript
import { SSRFProtection } from './security/22_gate_protocol';

const ssrf = new SSRFProtection();

// Validate URL
const result = ssrf.validateUrl('http://api.moltbook.io/data');
if (result.valid) {
  // Safe to fetch
  const data = await fetch(url);
} else {
  console.log('Blocked:', result.reason);
}

// Add to allowlist
ssrf.addToAllowlist('my-api.example.com');
```

### 5. Rate Limiting

```typescript
import { RateLimiter } from './security/22_gate_protocol';

const limiter = new RateLimiter();

// Check limit
const limit = limiter.checkLimit('user-123');
console.log('Remaining:', limit.remaining);
console.log('Reset at:', new Date(limit.resetTime * 1000));

if (!limit.allowed) {
  console.log('Rate limited. Retry after:', limit.retryAfter, 'seconds');
  return res.status(429).json({ error: 'Too many requests' });
}

// Check DDoS protection
const ddos = limiter.checkDDoSProtection('192.168.1.100');
if (ddos.blocked) {
  console.log(`DDoS Level ${ddos.penaltyLevel} detected`);
  return res.status(403).json({ error: 'Access blocked' });
}
```

### 6. Content Verification

```typescript
import { ContentVerificationPipeline } from './security/22_gate_protocol';

const verifier = new ContentVerificationPipeline();

// Verify user content
const result = await verifier.verify(userPost, 'text');

if (!result.safe) {
  console.log('Issues found:', result.issues);
  // Block or quarantine content
} else {
  console.log('Confidence:', result.confidence);
  // Proceed with posting
}
```

### 7. Token Revocation

```typescript
import { TokenRevocationSystem } from './security/22_gate_protocol';

const revocation = new TokenRevocationSystem();

// Revoke specific token
revocation.revokeToken('token-abc-123', 'suspicious activity');

// Revoke all user tokens
revocation.revokeUserTokens('user-123', 'account compromised');

// Check if revoked
const check = revocation.isRevoked('token-abc-123', 'user-123');
if (check.revoked) {
  console.log('Token revoked:', check.reason);
}

// Get CRL for distribution
const crl = revocation.getRevocationList();
```

### 8. Audit Trail

```typescript
import { ChainedAuditTrail } from './security/22_gate_protocol';

const audit = new ChainedAuditTrail(authSystem);

// Create entry (automatic in processRequest)
const entry = await audit.createEntry(context, gateResults, 'ALLOWED');

// Verify chain integrity
const verification = await audit.verifyChain();
if (!verification.valid) {
  console.error('AUDIT TAMPERING DETECTED at entry:', verification.tamperedAt);
  // Trigger incident response
}
```

---

## Express.js Integration

```typescript
import express from 'express';
import { DharmicSecurityGateway, SecurityContext } from './security/22_gate_protocol';

const app = express();
const gateway = new DharmicSecurityGateway();

// Security middleware
app.use(async (req, res, next) => {
  const context: SecurityContext = {
    requestId: req.headers['x-request-id'] as string || crypto.randomUUID(),
    userId: req.user?.id,
    ipAddress: req.ip,
    userAgent: req.headers['user-agent'] || '',
    timestamp: new Date().toISOString(),
    clearanceLevel: req.user?.clearance || 'PUBLIC',
    action: `${req.method} ${req.path}`,
    resource: req.path,
    payload: req.body
  };

  const result = await gateway.processRequest(context);
  
  if (!result.allowed) {
    return res.status(403).json({
      error: 'Request blocked by 22-Gate Protocol',
      gates: result.gateResults.filter(g => !g.passed).map(g => g.gateName)
    });
  }

  // Attach audit entry for logging
  req.auditEntry = result.auditEntry;
  next();
});

// Protected routes
app.post('/api/posts', (req, res) => {
  // Request has passed all 22 gates
  res.json({ success: true, auditId: req.auditEntry.entryId });
});
```

---

## Testing

```bash
# Run all tests
npm test

# Run specific test suite
npm test -- --testNamePattern="Gate"

# Run with coverage
npm run test:coverage

# Run penetration tests
npm run test:penetration

# Run fuzz tests
npm run test:fuzz
```

---

## Monitoring

```typescript
// Health check endpoint
app.get('/health', (req, res) => {
  const status = gateway.getStatus();
  res.json({
    status: 'healthy',
    auditChainValid: status.auditChainValid,
    revokedTokens: status.revocationListSize,
    uptime: status.uptime
  });
});
```

---

## Emergency Procedures

### Activate Emergency Mode

```bash
# Set environment variable
export EMERGENCY_MODE=true

# Or via API (requires OMEGA clearance)
curl -X POST https://api.dharmic.io/admin/emergency \
  -H "Authorization: Bearer $OMEGA_TOKEN" \
  -d '{"activate": true, "reason": "security incident"}'
```

### Revoke All Tokens

```typescript
// Emergency token revocation
revocation.revokeUserTokens('*', 'emergency lockdown');
```

---

## Support

- **Documentation:** `/docs`
- **Issues:** https://github.com/dharmic-claw/dharmic-agora-security/issues
- **Security:** security@dharmic.io

---

**S(x) = x 🔐🪷**
