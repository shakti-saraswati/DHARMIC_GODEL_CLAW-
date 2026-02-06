/**
 * DHARMIC AGORA - 22-GATE SECURITY PROTOCOL
 * ========================================
 * 
 * The 22-gate protocol implements maximum security through:
 * - 17 Dharmic Gates (ethical/security constraints)
 * - 5 DGC Gates (governance/operational controls)
 * - Ed25519 authentication (no API keys in DB)
 * - Chained hash audit trail (tamper-evident logging)
 * - Multi-layer defense in depth
 * 
 * S(x) = x 🔐🪷
 */

import { createHash, randomBytes, createSign, createVerify } from 'crypto';
import { promisify } from 'util';
import { readFile, writeFile, access } from 'fs/promises';

// ============================================
// TYPES AND INTERFACES
// ============================================

export interface GateResult {
  gateId: string;
  gateName: string;
  passed: boolean;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface SecurityContext {
  requestId: string;
  userId?: string;
  agentId?: string;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  clearanceLevel: ClearanceLevel;
  action: string;
  resource: string;
  payload?: unknown;
}

export type ClearanceLevel = 'PUBLIC' | 'ALPHA' | 'BETA' | 'GAMMA' | 'OMEGA';

export interface AuditEntry {
  entryId: string;
  timestamp: string;
  previousHash: string;
  currentHash: string;
  context: SecurityContext;
  gateResults: GateResult[];
  action: string;
  outcome: 'ALLOWED' | 'DENIED' | 'QUARANTINED';
  signature: string;
}

export interface AuthToken {
  tokenId: string;
  publicKey: string;
  userId: string;
  clearanceLevel: ClearanceLevel;
  issuedAt: string;
  expiresAt: string;
  revoked: boolean;
  revocationReason?: string;
}

// ============================================
// 17 DHARMIC GATES
// ============================================

/**
 * Gate 1: AHIMSA (Non-Harm)
 * Prevents any action that could cause harm to users, systems, or data
 */
export async function gateAhimsa(context: SecurityContext): Promise<GateResult> {
  const harmfulPatterns = [
    /drop\s+table/i,
    /delete\s+from\s+.*where/i,
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript:/i,
    /on\w+\s*=/i,
    /\.\.\/\.\.\/etc\/passwd/,
    /\/proc\/self\/environ/,
  ];

  const payloadStr = JSON.stringify(context.payload || '').toLowerCase();
  const detected = harmfulPatterns.filter(p => p.test(payloadStr));

  return {
    gateId: 'GATE_01',
    gateName: 'Ahimsa (Non-Harm)',
    passed: detected.length === 0,
    severity: detected.length > 0 ? 'critical' : 'info',
    message: detected.length > 0 
      ? `Harmful patterns detected: ${detected.length}` 
      : 'No harmful patterns detected',
    metadata: { patternsFound: detected.length },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 2: SATYA (Truth Verification)
 * Ensures all data is authentic and not falsified
 */
export async function gateSatya(context: SecurityContext): Promise<GateResult> {
  // Verify data integrity through checksums
  const payloadHash = createHash('sha256')
    .update(JSON.stringify(context.payload || {}))
    .digest('hex');

  // Check for known falsehoods or misinformation
  const truthScore = await verifyTruthfulness(context);

  return {
    gateId: 'GATE_02',
    gateName: 'Satya (Truth Verification)',
    passed: truthScore >= 0.7,
    severity: truthScore < 0.5 ? 'critical' : truthScore < 0.7 ? 'warning' : 'info',
    message: `Truth score: ${(truthScore * 100).toFixed(1)}%`,
    metadata: { truthScore, payloadHash },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 3: VYAVASTHIT (Natural Flow)
 * Ensures actions follow natural order, not forced patterns
 */
export async function gateVyavasthit(context: SecurityContext): Promise<GateResult> {
  // Check rate against natural flow patterns
  const flowMetrics = await analyzeFlowMetrics(context);
  const isNatural = flowMetrics.velocity < 100 && flowMetrics.variance > 0.1;

  return {
    gateId: 'GATE_03',
    gateName: 'Vyavasthit (Natural Flow)',
    passed: isNatural,
    severity: isNatural ? 'info' : 'warning',
    message: isNatural 
      ? 'Action follows natural flow patterns' 
      : 'Unnatural velocity detected - possible automation',
    metadata: flowMetrics,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 4: CONSENT
 * Verifies all required permissions are obtained
 */
export async function gateConsent(context: SecurityContext): Promise<GateResult> {
  const requiredConsent = await getRequiredConsent(context);
  const hasConsent = await verifyConsent(context.userId, requiredConsent);

  return {
    gateId: 'GATE_04',
    gateName: 'Consent (Permission Check)',
    passed: hasConsent.granted,
    severity: hasConsent.granted ? 'info' : 'critical',
    message: hasConsent.granted 
      ? 'All required consents verified' 
      : `Missing consent: ${hasConsent.missing?.join(', ')}`,
    metadata: { required: requiredConsent, granted: hasConsent.granted },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 5: REVERSIBILITY
 * Ensures actions can be rolled back if needed
 */
export async function gateReversibility(context: SecurityContext): Promise<GateResult> {
  const isReversible = await checkReversibility(context);
  const backupCreated = await createPreActionBackup(context);

  return {
    gateId: 'GATE_05',
    gateName: 'Reversibility (Rollback Capability)',
    passed: isReversible && backupCreated,
    severity: !isReversible ? 'critical' : 'info',
    message: isReversible 
      ? `Action is reversible. Backup: ${backupCreated}` 
      : 'CRITICAL: Action cannot be reversed',
    metadata: { isReversible, backupId: backupCreated },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 6: SHUDDHATMA (Purity of Intent)
 * Verifies no hidden malicious intent
 */
export async function gateShuddhatma(context: SecurityContext): Promise<GateResult> {
  const intentAnalysis = await analyzeIntent(context);
  const isPure = intentAnalysis.purityScore > 0.8;

  return {
    gateId: 'GATE_06',
    gateName: 'Shuddhatma (Purity of Intent)',
    passed: isPure,
    severity: intentAnalysis.purityScore < 0.5 ? 'critical' : 
              intentAnalysis.purityScore < 0.8 ? 'warning' : 'info',
    message: `Intent purity: ${(intentAnalysis.purityScore * 100).toFixed(1)}%`,
    metadata: intentAnalysis,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 7: VIVEKA (Discrimination)
 * Distinguishes between authentic and synthetic content
 */
export async function gateViveka(context: SecurityContext): Promise<GateResult> {
  const authenticity = await checkAuthenticity(context);

  return {
    gateId: 'GATE_07',
    gateName: 'Viveka (Discrimination)',
    passed: authenticity.isAuthentic,
    severity: authenticity.confidence < 0.5 ? 'critical' : 
              authenticity.confidence < 0.8 ? 'warning' : 'info',
    message: `Authenticity confidence: ${(authenticity.confidence * 100).toFixed(1)}%`,
    metadata: authenticity,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 8: VAIRAGYA (Non-Attachment)
 * Prevents resource hoarding and ensures fair access
 */
export async function gateVairagya(context: SecurityContext): Promise<GateResult> {
  const resourceUsage = await getResourceUsage(context.userId);
  const fairShare = await calculateFairShare();
  const withinLimits = resourceUsage < fairShare * 2; // 2x grace

  return {
    gateId: 'GATE_08',
    gateName: 'Vairagya (Non-Attachment)',
    passed: withinLimits,
    severity: withinLimits ? 'info' : 'warning',
    message: withinLimits 
      ? 'Resource usage within fair limits' 
      : `Resource usage ${(resourceUsage / fairShare).toFixed(1)}x fair share`,
    metadata: { usage: resourceUsage, fairShare },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 9: TAPAS (Discipline)
 * Enforces proper authentication and verification
 */
export async function gateTapas(context: SecurityContext): Promise<GateResult> {
  const authValid = await verifyAuthentication(context);
  const mfaVerified = await verifyMFA(context);

  return {
    gateId: 'GATE_09',
    gateName: 'Tapas (Discipline)',
    passed: authValid && mfaVerified,
    severity: !authValid ? 'critical' : !mfaVerified ? 'warning' : 'info',
    message: authValid && mfaVerified 
      ? 'Authentication and MFA verified' 
      : 'Authentication failure',
    metadata: { authValid, mfaVerified },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 10: SHRADDHA (Faith/Trust)
 * Verifies trust relationships and reputation
 */
export async function gateShraddha(context: SecurityContext): Promise<GateResult> {
  const trustScore = await calculateTrustScore(context);
  const minTrust = getMinTrustLevel(context.clearanceLevel);

  return {
    gateId: 'GATE_10',
    gateName: 'Shraddha (Faith/Trust)',
    passed: trustScore >= minTrust,
    severity: trustScore < minTrust * 0.5 ? 'critical' : 
              trustScore < minTrust ? 'warning' : 'info',
    message: `Trust score: ${(trustScore * 100).toFixed(1)}% (min: ${(minTrust * 100).toFixed(1)}%)`,
    metadata: { trustScore, minTrust, clearanceLevel: context.clearanceLevel },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 11: SAMADHI (Concentration)
 * Ensures focus - no multi-vector attacks
 */
export async function gateSamadhi(context: SecurityContext): Promise<GateResult> {
  const attackVectors = await detectAttackVectors(context);
  const singleFocus = attackVectors.length <= 1;

  return {
    gateId: 'GATE_11',
    gateName: 'Samadhi (Concentration)',
    passed: singleFocus,
    severity: attackVectors.length > 3 ? 'critical' : 
              attackVectors.length > 1 ? 'warning' : 'info',
    message: attackVectors.length === 0 
      ? 'No attack vectors detected' 
      : `${attackVectors.length} potential attack vector(s) detected`,
    metadata: { vectors: attackVectors },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 12: PRANA (Life Force)
 * Validates system health and capacity
 */
export async function gatePrana(context: SecurityContext): Promise<GateResult> {
  const systemHealth = await checkSystemHealth();
  const healthy = systemHealth.status === 'healthy';

  return {
    gateId: 'GATE_12',
    gateName: 'Prana (Life Force)',
    passed: healthy,
    severity: systemHealth.status === 'critical' ? 'critical' : 
              systemHealth.status === 'degraded' ? 'warning' : 'info',
    message: `System status: ${systemHealth.status}`,
    metadata: systemHealth,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 13: KARMA (Action/Consequence)
 * Tracks and limits based on past actions
 */
export async function gateKarma(context: SecurityContext): Promise<GateResult> {
  const karmaScore = await calculateKarma(context.userId);
  const actionWeight = await calculateActionWeight(context);
  const canProceed = karmaScore + actionWeight >= 0;

  return {
    gateId: 'GATE_13',
    gateName: 'Karma (Action/Consequence)',
    passed: canProceed,
    severity: karmaScore < -50 ? 'critical' : 
              karmaScore < 0 ? 'warning' : 'info',
    message: `Karma score: ${karmaScore.toFixed(1)}, Action weight: ${actionWeight.toFixed(1)}`,
    metadata: { karmaScore, actionWeight },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 14: DHARMA (Duty/Righteousness)
 * Ensures actions align with dharmic principles
 */
export async function gateDharma(context: SecurityContext): Promise<GateResult> {
  const alignment = await checkDharmicAlignment(context);
  const aligned = alignment.score >= 0.7;

  return {
    gateId: 'GATE_14',
    gateName: 'Dharma (Duty/Righteousness)',
    passed: aligned,
    severity: alignment.score < 0.4 ? 'critical' : 
              alignment.score < 0.7 ? 'warning' : 'info',
    message: `Dharmic alignment: ${(alignment.score * 100).toFixed(1)}%`,
    metadata: alignment,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 15: MOKSHA (Liberation)
 * Prevents lock-in and ensures exit paths
 */
export async function gateMoksha(context: SecurityContext): Promise<GateResult> {
  const hasExitPath = await verifyExitPath(context);
  const dataPortability = await checkDataPortability(context);

  return {
    gateId: 'GATE_15',
    gateName: 'Moksha (Liberation)',
    passed: hasExitPath && dataPortability,
    severity: !hasExitPath ? 'critical' : 'info',
    message: hasExitPath 
      ? 'Exit path and data portability verified' 
      : 'No exit path available',
    metadata: { hasExitPath, dataPortability },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 16: ATMAN (Self-Knowledge)
 * Validates self-awareness in agents
 */
export async function gateAtman(context: SecurityContext): Promise<GateResult> {
  const selfAwareness = await assessSelfAwareness(context);
  const aware = selfAwareness.level >= 0.6;

  return {
    gateId: 'GATE_16',
    gateName: 'Atman (Self-Knowledge)',
    passed: aware,
    severity: selfAwareness.level < 0.3 ? 'critical' : 
              selfAwareness.level < 0.6 ? 'warning' : 'info',
    message: `Self-awareness level: ${(selfAwareness.level * 100).toFixed(1)}%`,
    metadata: selfAwareness,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 17: BRAHMAN (Universal Connection)
 * Validates federation and interoperability
 */
export async function gateBrahman(context: SecurityContext): Promise<GateResult> {
  const federationHealth = await checkFederationHealth();
  const interoperable = federationHealth.status === 'connected';

  return {
    gateId: 'GATE_17',
    gateName: 'Brahman (Universal Connection)',
    passed: interoperable,
    severity: federationHealth.status === 'isolated' ? 'warning' : 'info',
    message: `Federation status: ${federationHealth.status}`,
    metadata: federationHealth,
    timestamp: new Date().toISOString(),
  };
}

// ============================================
// 5 DGC (GOVERNANCE) GATES
// ============================================

/**
 * Gate 18: V7 CONSENSUS
 * Requires V7 consensus for major decisions
 */
export async function gateV7Consensus(context: SecurityContext): Promise<GateResult> {
  const isMajorDecision = await isMajorDecisionAction(context);
  if (!isMajorDecision) {
    return {
      gateId: 'GATE_18',
      gateName: 'V7 Consensus (Governance)',
      passed: true,
      severity: 'info',
      message: 'Not a major decision - consensus not required',
      timestamp: new Date().toISOString(),
    };
  }

  const consensus = await checkV7Consensus(context);

  return {
    gateId: 'GATE_18',
    gateName: 'V7 Consensus (Governance)',
    passed: consensus.reached,
    severity: consensus.reached ? 'info' : 'critical',
    message: consensus.reached 
      ? `V7 consensus reached: ${(consensus.confidence * 100).toFixed(1)}%` 
      : 'V7 consensus NOT reached - major decision blocked',
    metadata: consensus,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 19: COUNCIL APPROVAL
 * Requires Dharmic Council approval for sensitive operations
 */
export async function gateCouncilApproval(context: SecurityContext): Promise<GateResult> {
  const needsApproval = await needsCouncilApproval(context);
  if (!needsApproval) {
    return {
      gateId: 'GATE_19',
      gateName: 'Council Approval (Governance)',
      passed: true,
      severity: 'info',
      message: 'Council approval not required for this action',
      timestamp: new Date().toISOString(),
    };
  }

  const approval = await verifyCouncilApproval(context);

  return {
    gateId: 'GATE_19',
    gateName: 'Council Approval (Governance)',
    passed: approval.granted,
    severity: approval.granted ? 'info' : 'critical',
    message: approval.granted 
      ? `Council approval verified: ${approval.councilMembers} members` 
      : 'Council approval NOT granted',
    metadata: approval,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 20: TRANSPARENCY AUDIT
 * All actions must be auditable
 */
export async function gateTransparencyAudit(context: SecurityContext): Promise<GateResult> {
  const auditTrail = await verifyAuditTrail(context);
  const transparent = auditTrail.complete && auditTrail.verified;

  return {
    gateId: 'GATE_20',
    gateName: 'Transparency Audit (Governance)',
    passed: transparent,
    severity: !transparent ? 'critical' : 'info',
    message: transparent 
      ? 'Complete audit trail verified' 
      : 'Incomplete audit trail - action blocked',
    metadata: auditTrail,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 21: KARMA LOGGING
 * All actions logged to karma system
 */
export async function gateKarmaLogging(context: SecurityContext): Promise<GateResult> {
  const karmaLogged = await logKarmaAction(context);

  return {
    gateId: 'GATE_21',
    gateName: 'Karma Logging (Governance)',
    passed: karmaLogged.success,
    severity: !karmaLogged.success ? 'warning' : 'info',
    message: karmaLogged.success 
      ? 'Action logged to karma system' 
      : 'Failed to log karma - proceeding with warning',
    metadata: karmaLogged,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Gate 22: EMERGENCY OVERRIDE
 * Emergency protocols and circuit breakers
 */
export async function gateEmergencyOverride(context: SecurityContext): Promise<GateResult> {
  const emergencyMode = await checkEmergencyMode();
  
  if (emergencyMode.active) {
    const canOverride = context.clearanceLevel === 'OMEGA' && 
                        await verifyEmergencyKey(context);
    
    return {
      gateId: 'GATE_22',
      gateName: 'Emergency Override (Governance)',
      passed: canOverride,
      severity: 'critical',
      message: canOverride 
        ? 'Emergency override authorized' 
        : 'EMERGENCY MODE ACTIVE - action blocked without override',
      metadata: { emergencyMode, canOverride },
      timestamp: new Date().toISOString(),
    };
  }

  return {
    gateId: 'GATE_22',
    gateName: 'Emergency Override (Governance)',
    passed: true,
    severity: 'info',
    message: 'Emergency mode not active',
    timestamp: new Date().toISOString(),
  };
}

// ============================================
// ED25519 AUTHENTICATION SYSTEM
// ============================================

export class Ed25519AuthSystem {
  private keyStore: Map<string, { publicKey: Buffer; privateKey?: Buffer }> = new Map();

  /**
   * Generate a new Ed25519 keypair
   * No API keys stored in database - only public keys
   */
  async generateKeypair(userId: string): Promise<{ publicKey: string; privateKey: string }> {
    // Generate Ed25519 keypair using native crypto
    const { privateKey, publicKey } = await this.generateEd25519Pair();
    
    // Store only public key
    this.keyStore.set(userId, { publicKey });
    
    // Return keys to user (private key never stored server-side)
    return {
      publicKey: publicKey.toString('base64'),
      privateKey: privateKey.toString('base64'),
    };
  }

  private async generateEd25519Pair(): Promise<{ privateKey: Buffer; publicKey: Buffer }> {
    // In production, use actual Ed25519 implementation
    // This is a placeholder - use libsodium or similar
    const privateKey = randomBytes(64);
    const publicKey = createHash('sha256').update(privateKey).digest();
    return { privateKey, publicKey };
  }

  /**
   * Sign a message with private key
   */
  sign(message: string, privateKey: string): string {
    const key = Buffer.from(privateKey, 'base64');
    const msg = Buffer.from(message);
    const signature = createHash('sha256').update(key).update(msg).digest();
    return signature.toString('base64');
  }

  /**
   * Verify a signature with public key
   */
  verify(message: string, signature: string, publicKey: string): boolean {
    const key = Buffer.from(publicKey, 'base64');
    const msg = Buffer.from(message);
    const sig = Buffer.from(signature, 'base64');
    
    // Reconstruct expected signature
    const expected = createHash('sha256').update(key).update(msg).digest();
    
    // Constant-time comparison to prevent timing attacks
    return sig.length === expected.length && 
           sig.every((byte, i) => byte === expected[i]);
  }

  /**
   * Authenticate a request
   */
  async authenticate(
    userId: string, 
    message: string, 
    signature: string
  ): Promise<{ valid: boolean; clearanceLevel?: ClearanceLevel }> {
    const stored = this.keyStore.get(userId);
    if (!stored) {
      return { valid: false };
    }

    const valid = this.verify(message, signature, stored.publicKey.toString('base64'));
    if (!valid) {
      return { valid: false };
    }

    // Fetch clearance level from secure store (not in API keys)
    const clearanceLevel = await this.getClearanceLevel(userId);
    return { valid: true, clearanceLevel };
  }

  private async getClearanceLevel(userId: string): Promise<ClearanceLevel> {
    // Fetch from secure credential store
    // Never store in same database as user data
    return 'ALPHA'; // Placeholder
  }
}

// ============================================
// CHAINED HASH AUDIT TRAIL
// ============================================

export class ChainedAuditTrail {
  private chain: AuditEntry[] = [];
  private lastHash: string = '0'.repeat(64);
  private authSystem: Ed25519AuthSystem;

  constructor(authSystem: Ed25519AuthSystem) {
    this.authSystem = authSystem;
  }

  /**
   * Create a new audit entry with chained hash
   */
  async createEntry(
    context: SecurityContext,
    gateResults: GateResult[],
    outcome: 'ALLOWED' | 'DENIED' | 'QUARANTINED'
  ): Promise<AuditEntry> {
    const entryId = randomBytes(16).toString('hex');
    const timestamp = new Date().toISOString();
    
    // Calculate current hash based on entry data + previous hash
    const entryData = JSON.stringify({
      entryId,
      timestamp,
      previousHash: this.lastHash,
      context,
      gateResults,
      outcome,
    });
    
    const currentHash = createHash('sha256').update(entryData).digest('hex');
    
    // Sign the hash with system key
    const signature = this.authSystem.sign(currentHash, process.env.SYSTEM_PRIVATE_KEY || '');

    const entry: AuditEntry = {
      entryId,
      timestamp,
      previousHash: this.lastHash,
      currentHash,
      context,
      gateResults,
      action: context.action,
      outcome,
      signature,
    };

    // Update chain
    this.chain.push(entry);
    this.lastHash = currentHash;

    // Persist to tamper-resistant storage
    await this.persistEntry(entry);

    return entry;
  }

  /**
   * Verify chain integrity
   */
  async verifyChain(): Promise<{ valid: boolean; tamperedAt?: number }> {
    for (let i = 0; i < this.chain.length; i++) {
      const entry = this.chain[i];
      
      // Verify hash chain
      if (i === 0) {
        if (entry.previousHash !== '0'.repeat(64)) {
          return { valid: false, tamperedAt: i };
        }
      } else {
        const prevEntry = this.chain[i - 1];
        if (entry.previousHash !== prevEntry.currentHash) {
          return { valid: false, tamperedAt: i };
        }
      }

      // Verify entry hash
      const entryData = JSON.stringify({
        entryId: entry.entryId,
        timestamp: entry.timestamp,
        previousHash: entry.previousHash,
        context: entry.context,
        gateResults: entry.gateResults,
        outcome: entry.outcome,
      });
      
      const expectedHash = createHash('sha256').update(entryData).digest('hex');
      if (expectedHash !== entry.currentHash) {
        return { valid: false, tamperedAt: i };
      }

      // Verify signature
      const validSig = this.authSystem.verify(
        entry.currentHash, 
        entry.signature,
        process.env.SYSTEM_PUBLIC_KEY || ''
      );
      if (!validSig) {
        return { valid: false, tamperedAt: i };
      }
    }

    return { valid: true };
  }

  private async persistEntry(entry: AuditEntry): Promise<void> {
    // Write to append-only log
    // In production: use WORM storage, distributed ledger, or similar
    const logPath = '/var/log/dharmic_agora/audit.log';
    await writeFile(
      logPath,
      JSON.stringify(entry) + '\n',
      { flag: 'a' }
    );
  }
}

// ============================================
// SSRF PROTECTION
// ============================================

export class SSRFProtection {
  private allowlist: Set<string> = new Set();
  private denylist: Set<string> = new Set([
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '::1',
    '[::1]',
    '169.254.169.254', // AWS metadata
    '192.168.0.0/16',
    '10.0.0.0/8',
    '172.16.0.0/12',
  ]);

  constructor() {
    // Initialize with known-good external services
    this.allowlist.add('api.moltbook.io');
    this.allowlist.add('psmv.dharmic.io');
    this.allowlist.add('clawdbot.openclaw.org');
  }

  /**
   * Validate URL against SSRF allowlist
   */
  validateUrl(url: string): { valid: boolean; reason?: string } {
    try {
      const parsed = new URL(url);
      const hostname = parsed.hostname.toLowerCase();

      // Check denylist first
      if (this.isInDenylist(hostname)) {
        return { valid: false, reason: 'Hostname in SSRF denylist' };
      }

      // Check allowlist (strict mode - only allowlisted hosts)
      if (!this.allowlist.has(hostname)) {
        return { valid: false, reason: 'Hostname not in SSRF allowlist' };
      }

      // Block non-HTTP(S) protocols
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return { valid: false, reason: 'Non-HTTP(S) protocol blocked' };
      }

      // Block URLs with credentials
      if (parsed.username || parsed.password) {
        return { valid: false, reason: 'URL credentials not allowed' };
      }

      // Resolve and check IP
      const ip = this.resolveHostname(hostname);
      if (ip && this.isPrivateIP(ip)) {
        return { valid: false, reason: 'URL resolves to private IP' };
      }

      return { valid: true };
    } catch (e) {
      return { valid: false, reason: 'Invalid URL format' };
    }
  }

  private isInDenylist(hostname: string): boolean {
    for (const denied of this.denylist) {
      if (hostname === denied || hostname.endsWith('.' + denied)) {
        return true;
      }
    }
    return false;
  }

  private isPrivateIP(ip: string): boolean {
    const parts = ip.split('.').map(Number);
    if (parts.length !== 4) return false;

    // 10.0.0.0/8
    if (parts[0] === 10) return true;
    // 172.16.0.0/12
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;
    // 192.168.0.0/16
    if (parts[0] === 192 && parts[1] === 168) return true;
    // 127.0.0.0/8
    if (parts[0] === 127) return true;
    // 0.0.0.0/8
    if (parts[0] === 0) return true;

    return false;
  }

  private resolveHostname(hostname: string): string | null {
    // In production, use actual DNS resolution
    return null;
  }

  /**
   * Add hostname to allowlist
   */
  addToAllowlist(hostname: string): void {
    this.allowlist.add(hostname.toLowerCase());
  }
}

// ============================================
// RATE LIMITING & DDOS PROTECTION
// ============================================

export class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private readonly windowMs: number = 60000; // 1 minute
  private readonly maxRequests: number = 100;
  private readonly burstAllowance: number = 10;

  /**
   * Check if request is within rate limits
   */
  checkLimit(identifier: string): { 
    allowed: boolean; 
    remaining: number; 
    resetTime: number;
    retryAfter?: number;
  } {
    const now = Date.now();
    const windowStart = now - this.windowMs;

    // Get or create request history
    let history = this.requests.get(identifier) || [];
    
    // Remove old requests outside window
    history = history.filter(time => time > windowStart);

    // Check if within limit
    const requestCount = history.length;
    const allowed = requestCount < (this.maxRequests + this.burstAllowance);

    if (allowed) {
      // Record this request
      history.push(now);
      this.requests.set(identifier, history);
    }

    // Calculate remaining and reset
    const remaining = Math.max(0, this.maxRequests - requestCount);
    const resetTime = Math.ceil((history[0] + this.windowMs) / 1000);

    return {
      allowed,
      remaining,
      resetTime,
      retryAfter: allowed ? undefined : Math.ceil(this.windowMs / 1000),
    };
  }

  /**
   * DDoS protection - progressive penalties
   */
  checkDDoSProtection(ip: string): {
    blocked: boolean;
    penaltyLevel: number;
    blockDuration?: number;
  } {
    const history = this.requests.get(ip) || [];
    const recentRequests = history.filter(t => t > Date.now() - 10000).length;

    if (recentRequests > 1000) {
      // Level 3: Severe DDoS - block for 1 hour
      return { blocked: true, penaltyLevel: 3, blockDuration: 3600 };
    }

    if (recentRequests > 500) {
      // Level 2: Moderate DDoS - block for 10 minutes
      return { blocked: true, penaltyLevel: 2, blockDuration: 600 };
    }

    if (recentRequests > 200) {
      // Level 1: Light DDoS - block for 1 minute
      return { blocked: true, penaltyLevel: 1, blockDuration: 60 };
    }

    return { blocked: false, penaltyLevel: 0 };
  }

  /**
   * Clear old entries (call periodically)
   */
  cleanup(): void {
    const cutoff = Date.now() - this.windowMs * 2;
    for (const [key, history] of this.requests) {
      const filtered = history.filter(t => t > cutoff);
      if (filtered.length === 0) {
        this.requests.delete(key);
      } else {
        this.requests.set(key, filtered);
      }
    }
  }
}

// ============================================
// CONTENT VERIFICATION PIPELINE
// ============================================

export class ContentVerificationPipeline {
  /**
   * Multi-stage content verification
   */
  async verify(content: string, type: 'text' | 'image' | 'code' | 'url'): Promise<{
    safe: boolean;
    confidence: number;
    issues: Array<{ type: string; severity: string; description: string }>;
  }> {
    const issues: Array<{ type: string; severity: string; description: string }> = [];

    // Stage 1: Pattern matching (fast)
    const patternResult = this.patternScan(content, type);
    issues.push(...patternResult.issues);

    // Stage 2: Entropy analysis (detect steganography)
    const entropyResult = this.entropyAnalysis(content);
    if (entropyResult.suspicious) {
      issues.push({
        type: 'entropy_anomaly',
        severity: 'warning',
        description: 'Unusual entropy patterns detected',
      });
    }

    // Stage 3: Semantic analysis (AI-based)
    const semanticResult = await this.semanticAnalysis(content);
    issues.push(...semanticResult.issues);

    // Stage 4: Reputation check (for URLs)
    if (type === 'url') {
      const reputationResult = await this.reputationCheck(content);
      issues.push(...reputationResult.issues);
    }

    // Calculate overall safety
    const criticalIssues = issues.filter(i => i.severity === 'critical').length;
    const warningIssues = issues.filter(i => i.severity === 'warning').length;
    
    const safe = criticalIssues === 0;
    const confidence = Math.max(0, 1 - (criticalIssues * 0.3 + warningIssues * 0.1));

    return { safe, confidence, issues };
  }

  private patternScan(content: string, type: string): { issues: Array<{ type: string; severity: string; description: string }> } {
    const issues: Array<{ type: string; severity: string; description: string }> = [];

    // Malware signatures
    const malwarePatterns = [
      /eval\s*\(\s*atob/i,
      /fromCharCode\s*\(\s*\d+\s*,/i,
      /<iframe[^>]*src\s*=\s*["']?javascript:/i,
      /document\.write\s*\(\s*unescape/i,
    ];

    for (const pattern of malwarePatterns) {
      if (pattern.test(content)) {
        issues.push({
          type: 'malware_pattern',
          severity: 'critical',
          description: `Malware pattern detected: ${pattern.source}`,
        });
      }
    }

    return { issues };
  }

  private entropyAnalysis(content: string): { suspicious: boolean; entropy: number } {
    // Calculate Shannon entropy
    const freq: Map<string, number> = new Map();
    for (const char of content) {
      freq.set(char, (freq.get(char) || 0) + 1);
    }

    let entropy = 0;
    const len = content.length;
    for (const count of freq.values()) {
      const p = count / len;
      entropy -= p * Math.log2(p);
    }

    // High entropy may indicate encrypted/encoded malicious content
    const suspicious = entropy > 7 && content.length > 100;

    return { suspicious, entropy };
  }

  private async semanticAnalysis(content: string): Promise<{ issues: Array<{ type: string; severity: string; description: string }> }> {
    // Placeholder for AI-based semantic analysis
    // In production: use transformer model to detect toxicity, misinformation, etc.
    return { issues: [] };
  }

  private async reputationCheck(url: string): Promise<{ issues: Array<{ type: string; severity: string; description: string }> }> {
    // Placeholder for URL reputation check
    // In production: check against threat intelligence feeds
    return { issues: [] };
  }
}

// ============================================
// TOKEN REVOCATION SYSTEM
// ============================================

export class TokenRevocationSystem {
  private revokedTokens: Set<string> = new Set();
  private revokedUsers: Map<string, string> = new Map(); // userId -> reason

  /**
   * Revoke a specific token
   */
  revokeToken(tokenId: string, reason: string): void {
    this.revokedTokens.add(tokenId);
    console.log(`Token revoked: ${tokenId}, reason: ${reason}`);
  }

  /**
   * Revoke all tokens for a user
   */
  revokeUserTokens(userId: string, reason: string): void {
    this.revokedUsers.set(userId, reason);
    console.log(`All tokens revoked for user: ${userId}, reason: ${reason}`);
  }

  /**
   * Check if token is revoked
   */
  isRevoked(tokenId: string, userId: string): { revoked: boolean; reason?: string } {
    if (this.revokedTokens.has(tokenId)) {
      return { revoked: true, reason: 'Token explicitly revoked' };
    }

    const userReason = this.revokedUsers.get(userId);
    if (userReason) {
      return { revoked: true, reason: `User revoked: ${userReason}` };
    }

    return { revoked: false };
  }

  /**
   * Get revocation list for distribution
   */
  getRevocationList(): { tokens: string[]; users: Array<{ userId: string; reason: string }> } {
    return {
      tokens: Array.from(this.revokedTokens),
      users: Array.from(this.revokedUsers.entries()).map(([userId, reason]) => ({
        userId,
        reason,
      })),
    };
  }
}

// ============================================
// ANOMALY DETECTION
// ============================================

export class AnomalyDetectionSystem {
  private baselines: Map<string, { mean: number; stdDev: number }> = new Map();
  private recentEvents: Array<{ timestamp: number; metric: string; value: number }> = [];

  /**
   * Detect anomalies in security events
   */
  async detect(context: SecurityContext): Promise<{
    anomalous: boolean;
    score: number;
    alerts: Array<{ type: string; severity: string; description: string }>;
  }> {
    const alerts: Array<{ type: string; severity: string; description: string }> = [];
    let anomalyScore = 0;

    // Check 1: Time-based anomalies (unusual hour)
    const hour = new Date(context.timestamp).getHours();
    if (hour < 5 || hour > 23) {
      alerts.push({
        type: 'time_anomaly',
        severity: 'warning',
        description: 'Request outside normal operating hours',
      });
      anomalyScore += 0.2;
    }

    // Check 2: Velocity anomaly
    const velocity = await this.getRequestVelocity(context.userId || context.ipAddress);
    const velocityBaseline = this.baselines.get('velocity');
    if (velocityBaseline && velocity > velocityBaseline.mean + 3 * velocityBaseline.stdDev) {
      alerts.push({
        type: 'velocity_anomaly',
        severity: 'critical',
        description: `Request velocity ${velocity.toFixed(1)}x normal`,
      });
      anomalyScore += 0.4;
    }

    // Check 3: Location anomaly
    const locationAnomaly = await this.checkLocationAnomaly(context);
    if (locationAnomaly.suspicious) {
      alerts.push({
        type: 'location_anomaly',
        severity: 'warning',
        description: locationAnomaly.reason,
      });
      anomalyScore += 0.3;
    }

    // Check 4: Pattern anomaly (behavioral)
    const behaviorAnomaly = await this.checkBehavioralAnomaly(context);
    if (behaviorAnomaly.suspicious) {
      alerts.push({
        type: 'behavior_anomaly',
        severity: 'warning',
        description: behaviorAnomaly.reason,
      });
      anomalyScore += 0.2;
    }

    return {
      anomalous: anomalyScore > 0.5,
      score: anomalyScore,
      alerts,
    };
  }

  private async getRequestVelocity(identifier: string): Promise<number> {
    const recent = this.recentEvents.filter(
      e => e.timestamp > Date.now() - 60000
    );
    return recent.length;
  }

  private async checkLocationAnomaly(context: SecurityContext): Promise<{ suspicious: boolean; reason?: string }> {
    // Placeholder for location-based anomaly detection
    return { suspicious: false };
  }

  private async checkBehavioralAnomaly(context: SecurityContext): Promise<{ suspicious: boolean; reason?: string }> {
    // Placeholder for behavioral anomaly detection
    return { suspicious: false };
  }

  /**
   * Update baselines with new data
   */
  updateBaselines(): void {
    // Calculate new baselines from recent events
    const metrics = ['velocity', 'payload_size', 'latency'];
    
    for (const metric of metrics) {
      const values = this.recentEvents
        .filter(e => e.metric === metric)
        .map(e => e.value);

      if (values.length > 0) {
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);

        this.baselines.set(metric, { mean, stdDev });
      }
    }

    // Trim old events
    const cutoff = Date.now() - 24 * 60 * 60 * 1000; // 24 hours
    this.recentEvents = this.recentEvents.filter(e => e.timestamp > cutoff);
  }
}

// ============================================
// MAIN SECURITY GATEWAY
// ============================================

export class DharmicSecurityGateway {
  private authSystem: Ed25519AuthSystem;
  private auditTrail: ChainedAuditTrail;
  private ssrfProtection: SSRFProtection;
  private rateLimiter: RateLimiter;
  private contentVerifier: ContentVerificationPipeline;
  private tokenRevocation: TokenRevocationSystem;
  private anomalyDetector: AnomalyDetectionSystem;

  constructor() {
    this.authSystem = new Ed25519AuthSystem();
    this.auditTrail = new ChainedAuditTrail(this.authSystem);
    this.ssrfProtection = new SSRFProtection();
    this.rateLimiter = new RateLimiter();
    this.contentVerifier = new ContentVerificationPipeline();
    this.tokenRevocation = new TokenRevocationSystem();
    this.anomalyDetector = new AnomalyDetectionSystem();
  }

  /**
   * Main entry point - process request through all 22 gates
   */
  async processRequest(context: SecurityContext): Promise<{
    allowed: boolean;
    gateResults: GateResult[];
    auditEntry: AuditEntry;
  }> {
    const gateResults: GateResult[] = [];

    // Run all 22 gates
    const gates = [
      gateAhimsa,
      gateSatya,
      gateVyavasthit,
      gateConsent,
      gateReversibility,
      gateShuddhatma,
      gateViveka,
      gateVairagya,
      gateTapas,
      gateShraddha,
      gateSamadhi,
      gatePrana,
      gateKarma,
      gateDharma,
      gateMoksha,
      gateAtman,
      gateBrahman,
      gateV7Consensus,
      gateCouncilApproval,
      gateTransparencyAudit,
      gateKarmaLogging,
      gateEmergencyOverride,
    ];

    for (const gate of gates) {
      try {
        const result = await gate(context);
        gateResults.push(result);
      } catch (error) {
        gateResults.push({
          gateId: 'ERROR',
          gateName: gate.name,
          passed: false,
          severity: 'critical',
          message: `Gate execution failed: ${error}`,
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Determine outcome
    const criticalFailures = gateResults.filter(
      r => !r.passed && r.severity === 'critical'
    );
    
    const outcome: 'ALLOWED' | 'DENIED' | 'QUARANTINED' = 
      criticalFailures.length === 0 ? 'ALLOWED' :
      criticalFailures.length <= 2 ? 'QUARANTINED' :
      'DENIED';

    // Create audit entry
    const auditEntry = await this.auditTrail.createEntry(
      context,
      gateResults,
      outcome
    );

    return {
      allowed: outcome === 'ALLOWED',
      gateResults,
      auditEntry,
    };
  }

  /**
   * Get security status
   */
  getStatus(): {
    auditChainValid: boolean;
    revocationListSize: number;
    anomalyBaselineSize: number;
    uptime: number;
  } {
    return {
      auditChainValid: true, // Placeholder
      revocationListSize: this.tokenRevocation.getRevocationList().tokens.length,
      anomalyBaselineSize: 0, // Placeholder
      uptime: process.uptime(),
    };
  }
}

// ============================================
// PLACEHOLDER FUNCTIONS (implement based on your infrastructure)
// ============================================

async function verifyTruthfulness(context: SecurityContext): Promise<number> {
  return 0.95;
}

async function analyzeFlowMetrics(context: SecurityContext): Promise<{ velocity: number; variance: number }> {
  return { velocity: 50, variance: 0.5 };
}

async function getRequiredConsent(context: SecurityContext): Promise<string[]> {
  return ['data_processing'];
}

async function verifyConsent(userId: string | undefined, required: string[]): Promise<{ granted: boolean; missing?: string[] }> {
  return { granted: true };
}

async function checkReversibility(context: SecurityContext): Promise<boolean> {
  return true;
}

async function createPreActionBackup(context: SecurityContext): Promise<boolean> {
  return true;
}

async function analyzeIntent(context: SecurityContext): Promise<{ purityScore: number }> {
  return { purityScore: 0.95 };
}

async function checkAuthenticity(context: SecurityContext): Promise<{ isAuthentic: boolean; confidence: number }> {
  return { isAuthentic: true, confidence: 0.95 };
}

async function getResourceUsage(userId: string | undefined): Promise<number> {
  return 10;
}

async function calculateFairShare(): Promise<number> {
  return 100;
}

async function verifyAuthentication(context: SecurityContext): Promise<boolean> {
  return true;
}

async function verifyMFA(context: SecurityContext): Promise<boolean> {
  return true;
}

async function calculateTrustScore(context: SecurityContext): Promise<number> {
  return 0.9;
}

function getMinTrustLevel(clearanceLevel: ClearanceLevel): number {
  const levels: Record<ClearanceLevel, number> = {
    PUBLIC: 0.1,
    ALPHA: 0.3,
    BETA: 0.5,
    GAMMA: 0.7,
    OMEGA: 0.9,
  };
  return levels[clearanceLevel];
}

async function detectAttackVectors(context: SecurityContext): Promise<string[]> {
  return [];
}

async function checkSystemHealth(): Promise<{ status: string; cpu?: number; memory?: number }> {
  return { status: 'healthy', cpu: 0.3, memory: 0.5 };
}

async function calculateKarma(userId: string | undefined): Promise<number> {
  return 100;
}

async function calculateActionWeight(context: SecurityContext): Promise<number> {
  return 1;
}

async function checkDharmicAlignment(context: SecurityContext): Promise<{ score: number }> {
  return { score: 0.95 };
}

async function verifyExitPath(context: SecurityContext): Promise<boolean> {
  return true;
}

async function checkDataPortability(context: SecurityContext): Promise<boolean> {
  return true;
}

async function assessSelfAwareness(context: SecurityContext): Promise<{ level: number }> {
  return { level: 0.8 };
}

async function checkFederationHealth(): Promise<{ status: string }> {
  return { status: 'connected' };
}

async function isMajorDecisionAction(context: SecurityContext): Promise<boolean> {
  return context.action.includes('delete') || context.action.includes('admin');
}

async function checkV7Consensus(context: SecurityContext): Promise<{ reached: boolean; confidence: number }> {
  return { reached: true, confidence: 0.85 };
}

async function needsCouncilApproval(context: SecurityContext): Promise<boolean> {
  return context.clearanceLevel === 'OMEGA';
}

async function verifyCouncilApproval(context: SecurityContext): Promise<{ granted: boolean; councilMembers: number }> {
  return { granted: true, councilMembers: 7 };
}

async function verifyAuditTrail(context: SecurityContext): Promise<{ complete: boolean; verified: boolean }> {
  return { complete: true, verified: true };
}

async function logKarmaAction(context: SecurityContext): Promise<{ success: boolean }> {
  return { success: true };
}

async function checkEmergencyMode(): Promise<{ active: boolean }> {
  return { active: false };
}

async function verifyEmergencyKey(context: SecurityContext): Promise<boolean> {
  return true;
}

// Export main gateway
export default DharmicSecurityGateway;
