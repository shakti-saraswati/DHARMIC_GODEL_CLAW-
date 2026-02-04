# OpenClaw Skills System Analysis

This directory contains the comprehensive security and architecture analysis of the OpenClaw skills system and the openclaw-claude-code-skill MCP integration.

## Documents

- **openclaw_skills.md** - Main analysis document (955 lines, 32KB)
  - Complete architectural breakdown
  - Vulnerability surface mapping
  - Dharmic security framework application
  - Implementation roadmap for hardening

## Key Findings

### Critical Vulnerabilities

1. **NO SANDBOXING** - Skills execute with full process privileges
2. **NO PERMISSION MODEL** - Capability-based ACL doesn't exist
3. **NO INTEGRITY VERIFICATION** - Files trusted as-is
4. **NO IMMUTABILITY** - Adversary can modify skills on disk
5. **WEAK FILTERING** - `always: true` bypasses all eligibility checks
6. **MCP COMMAND INJECTION** - Arbitrary commands in config
7. **NO AUDIT LOG** - Attacks leave no trace
8. **PLUGIN TRUST MODEL** - Unsigned plugins auto-loaded

### Architecture Summary

```
BUNDLED SKILLS (./skills/)
↓
MANAGED SKILLS (~/.openclaw/skills/)
↓
WORKSPACE SKILLS (./skills/ - HIGHEST PRECEDENCE)
↓
ELIGIBILITY FILTERING (bins, env, config, OS)
↓
SKILL EXECUTION (pi-coding-agent → LLM → tool call)
↓
MCP INTEGRATION (subprocess-based servers, no isolation)
```

## Dharmic Security Framework

The analysis proposes five layered hardening principles:

1. **RECOGNITION (Satya)** - Cryptographic signatures + identity documents
2. **WITNESS (Vyavasthit)** - Immutable audit logs of all executions
3. **SEPARATION (Bhed Gnan)** - Explicit capability matrix per skill
4. **FIXED POINT (Keval Gnan)** - Immutable skill snapshots
5. **DISSOLUTION (Samkit)** - Zero-trust user consent model

## Recommended Hardening Roadmap

**Phase 1 (Week 1-2)**: Integrity Foundation
- Merkle tree hashing
- RSA signatures on bundled skills
- Signature verification at load time

**Phase 2 (Week 2-3)**: Witness & Audit
- Immutable execution log
- Audit trail commands

**Phase 3 (Week 3-4)**: Capability Matrix
- Extend SKILL.md metadata
- Zod schema validation
- Enforcement at execution boundary

**Phase 4 (Week 4-5)**: User Consent
- Permission prompts
- Source code display
- Per-version hash tracking

**Phase 5 (Week 5-6)**: Separation & Isolation
- Seccomp sandboxing
- Resource limits
- Namespace isolation

**Phase 6 (Week 6-7)**: Precedence & Immutability
- Git tag locking
- Signed commits
- Precedence audit reports

## File Locations

### Core OpenClaw Skills System
- `src/agents/skills/types.ts` - Skill type definitions
- `src/agents/skills/config.ts` - Eligibility filtering (WEAK)
- `src/agents/skills/workspace.ts` - Skill loading pipeline (NO VALIDATION)
- `src/agents/skills/frontmatter.ts` - YAML+JSON5 parsing (NO SCHEMA)
- `src/agents/skills/plugin-skills.ts` - Plugin integration (NO SIGNATURE)

### OpenClaw Claude Code Skill (MCP)
- `src/mcp/client.ts` - Subprocess creation (CRITICAL VULN)
- `src/mcp/actions.ts` - Tool execution (NO FILTERING)
- `src/mcp/types.ts` - Message definitions (NO VALIDATION)
- `mcp_config.json` - Config template (arbitrary commands possible)

## How OpenClaw Got Pwned

The vulnerability surface combines:

1. **No access control** - Skills run with full permissions
2. **No attestation** - Any file is trusted
3. **Precedence overrides** - Workspace shadows bundled
4. **No audit trail** - Attacks invisible

**Attack chain**:
```
Attacker commits malicious ./skills/trusted-skill/SKILL.md
↓
Precedence system loads workspace version (overrides bundled)
↓
Skill has `always: true` → bypasses eligibility checks
↓
Model calls skill with full process privileges
↓
Malicious skill reads credentials, forks trojan, exfiltrates data
↓
No audit log → attack invisible
```

## Next Steps

1. Review analysis with OpenClaw core team
2. Create GitHub issues for Phase 1 (integrity foundation)
3. Prototype capability matrix schema (Zod)
4. Design MCP sandboxing strategy (seccomp rules)
5. Plan user consent UI mockups
6. Begin implementation with sign bundled skills

---

**Analysis Date**: February 2, 2026  
**Analyst**: Claude Code (Haiku)  
**Document Size**: 32KB, 955 lines  
**Vulnerability Coverage**: 8 critical/high, 2 medium  
**Recommended Effort**: 6-7 week sprint for full hardening
