# 🔥 COSMIC KRISHNA CODER — Quick Start Guide

## Installation

Already installed globally:
- `~/clawd/skills/cosmic-krishna-coder/SKILL.md`
- `~/.openclaw/skills/cosmic-krishna-coder`
- `~/.clawdbot/skills/cosmic-krishna-coder`
- `~/.claude/skills/cosmic-krishna-coder.md`

## Usage

### 1. Automatic Risk Detection (Recommended)

Just describe what you want to build:

```bash
dgc-code "Build authentication system for Aghora"
```

**Auto-detects HIGH risk** (contains "authentication"):
- Activates 22 gates
- Requires human approval
- Generates spec.yaml, tests, sbom.json

### 2. Explicit Risk Levels

```bash
# Force specific risk level
dgc-code "Build payment gateway" --risk high      # 22 gates
dgc-code "Add API endpoint" --risk medium         # 14 gates
dgc-code "Fix typo" --risk low                    # 4 gates
```

### 3. YOLO Mode (Fast Iteration)

```bash
# For prototypes and spikes
dgc-code "Spike new feature" --yolo

# Or set environment variable
export DGC_YOLO_MODE=1
dgc-code "Quick experiment"

# Or touch .yolo file in repo
touch .yolo
dgc-code "Rapid prototype"
```

**YOLO mode:** 4 gates only (lint, type, security, basic tests)

### 4. From Python

```python
from skills.cosmic_krishna_coder import Coder, RiskLevel

coder = Coder()

# Auto-detect
result = coder.execute(
    task="Build login system",
    files=["src/auth.py"],
    context="User-facing, handles passwords"
)
# Auto-detects HIGH, activates 22 gates

# Explicit
result = coder.execute(
    task="Fix typo",
    files=["README.md"],
    risk_level=RiskLevel.LOW
)
# Forces LOW, 4 gates
```

## Risk Detection Logic

### HIGH Risk (22 gates) — Auto-detected for:
- Authentication (login, passwords, tokens)
- Security (encryption, secrets)
- Financial (payments, crypto)
- Infrastructure (databases, deployments)
- Multi-agent systems (swarm, orchestration)
- Network interfaces (APIs, webhooks)
- System modifications (file writes, migrations)

### MEDIUM Risk (14 gates) — Auto-detected for:
- Business logic (algorithms, calculations)
- Integration points (APIs, SDKs)
- Configuration (env vars, feature flags)
- Testing infrastructure

### LOW Risk (4 gates) — Auto-detected for:
- Read-only operations (queries, reports)
- Documentation (READMEs, comments)
- Internal utilities
- Style-only changes

### YOLO Override:
Set `DGC_YOLO_MODE=1` or use `--yolo` flag to bypass detection

## Gate Summary

| Gates | Risk | Description |
|-------|------|-------------|
| 4 | YOLO/LOW | Lint, type, security, basic tests |
| 14 | MEDIUM | + Coverage, property tests, contracts, dharmic gates |
| 22 | HIGH | + Performance, SBOM, license, ML gates |

## Integration with Your Workflow

### For DGC Development:
```bash
dgc-code "Add ML gate verification" src/dgm/
# Auto-detects HIGH (infrastructure code)
# 22 gates activated
```

### For Aghora Webpage:
```bash
dgc-code "Build user profile component" aghora/src/
# Auto-detects HIGH (user-facing, auth)
# 22 gates activated
```

### For Quick Scripts:
```bash
dgc-code "Generate daily report" --yolo
# 4 gates, fast execution
```

## Proactive Security

The skill **automatically** applies the right level of security without being asked. You don't need to remember which gates to use — it detects from context.

Until your intuition develops, the skill will:
1. Announce detected risk level before executing
2. Show which gates will activate
3. Allow override
4. Log decisions for review

## Files Created

Based on risk level:

| File | YOLO | MEDIUM | HIGH |
|------|------|--------|------|
| Code | ✅ | ✅ | ✅ |
| Tests | Optional | ✅ | ✅ Required |
| spec.yaml | No | ✅ | ✅ Detailed |
| risk_register.md | No | Basic | ✅ Full |
| sbom.json | No | No | ✅ |
| gate_results.json | Minimal | Standard | ✅ Complete |

## Dharmic Alignment

Every execution automatically checks:
- Does this serve moksha (liberation)?
- Is it non-harming (ahimsa)?
- Is it truthful (satya)?
- Does it create value (seva)?

If any check fails, execution pauses for reflection.

## Quality Standards

Based on top-50 code research:
- **HIGH risk target:** SQLite-grade (100% coverage, 10:1 test ratio)
- **MEDIUM risk target:** Industry standard (80% coverage)
- **YOLO target:** Works (lints pass, types check)

## Next Steps

1. Try risk detection: `dgc-code "Build auth" --preview`
2. Review full skill: `cat ~/clawd/skills/cosmic-krishna-coder/SKILL.md`
3. Calibrate detection: Review `~/.ckc_learning_log.jsonl` after 30 days

## Support

- **Research docs:** `docs/COSMIC_KRISHNA_CODER_UNIFIED_PLAN_v3.md`
- **Top-50 quality:** `docs/TOP_50_QUALITY_REFERENCE.md`
- **ML gates:** `docs/ML_GATES_SPECIFICATION.md`
- **Pi comparison:** `clawd/research/PI_PHILOSOPHY_DGC_COMPARISON.md`

---

**JAI HO! 🔥🪷**

*Build fast when safe. Build safe when serious. Never compromise on alignment.*
