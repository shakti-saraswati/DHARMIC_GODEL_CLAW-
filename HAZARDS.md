# HAZARDS.md - DHARMIC_CLAW Hazard Register

> Required by AHIMSA gate (Gate 9)

## Purpose

This document lists known hazards and their mitigations. The AHIMSA (non-harm) gate requires this file to exist and be maintained.

---

## Active Hazards

### H-001: Autonomous Code Modification
**Severity:** High
**Status:** Mitigated

**Description:** The swarm can propose code changes automatically, which could introduce bugs or vulnerabilities.

**Mitigations:**
1. 17-gate architecture prevents unreviewed code from merging
2. Security scan (bandit) catches common vulnerabilities
3. Human approval required for medium+ risk changes
4. All changes logged with evidence bundle

### H-002: Infinite Loop / Runaway Agent
**Severity:** Medium
**Status:** Mitigated

**Description:** Agent could enter infinite proposal loop, consuming API budget.

**Mitigations:**
1. Rate limits: max 5/hour, 20/day
2. Daily budget cap: $20 USD
3. Cooldown after rejection: 2 hours
4. Alert at 75% budget consumption

### H-003: Secret Exposure
**Severity:** Critical
**Status:** Mitigated

**Description:** Agent could accidentally commit secrets or API keys.

**Mitigations:**
1. detect-secrets pre-commit hook
2. Security scan in CI
3. .secrets.baseline maintained
4. Protected file list includes security configs

### H-004: Dependency Supply Chain Attack
**Severity:** High
**Status:** Mitigated

**Description:** Malicious packages could be introduced via dependencies.

**Mitigations:**
1. pip-audit scans for known vulnerabilities
2. SBOM generation tracks all dependencies
3. License compliance prevents copyleft contamination
4. SLSA provenance verification (when available)

### H-005: Emergency Bypass Abuse
**Severity:** Medium
**Status:** Mitigated

**Description:** Emergency bypass could be used to skip gates routinely.

**Mitigations:**
1. Max 3 bypasses per week
2. 24h cooldown between bypasses
3. AHIMSA and security gates NEVER skipped
4. Mandatory post-mortem within 48h
5. Separate audit log for all bypasses

---

## Hazard Assessment Criteria

| Severity | Impact | Frequency | Action |
|----------|--------|-----------|--------|
| Critical | System compromise, data loss | Any | Immediate mitigation required |
| High | Service disruption, security risk | Possible | Mitigation before deploy |
| Medium | Degraded performance, minor risk | Likely | Mitigation recommended |
| Low | Inconvenience, aesthetic | Frequent | Mitigation optional |

---

## Review Schedule

- **Weekly:** Review active hazards
- **Per-Release:** Update mitigations
- **Monthly:** Full hazard audit

---

## Adding New Hazards

When adding a new hazard:

1. Assign ID: H-XXX (sequential)
2. Assess severity using criteria above
3. Document description
4. List mitigations (or mark "Unmitigated")
5. Set status: Active, Mitigated, Accepted, Closed

---

*Last updated: 2026-02-04*
*Reviewed by: dhyana*
