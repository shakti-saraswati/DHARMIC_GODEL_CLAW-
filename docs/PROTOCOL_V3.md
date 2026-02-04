# DHARMIC_CLAW Autonomous Coding Protocol v3

> Hardened, non-bypassable gate architecture with dharmic security

**Version:** 3.0
**Updated:** 2026-02-04
**Status:** Active

---

## Overview

The DHARMIC_CLAW Autonomous Coding Protocol v3 is a comprehensive system for safe, trustworthy autonomous code generation. It enforces **17 gates** (8 technical, 7 dharmic, 2 supply-chain) with strict role separation and non-bypassable CI enforcement.

### Key Principles

1. **Separation of Duties** — Builder cannot verify, verifier cannot build
2. **CI as Ultimate Authority** — No merge without gate passage
3. **Human in the Loop** — Approval required for medium+ risk changes
4. **Evidence-Based** — Every gate produces auditable artifacts
5. **Dharmic Alignment** — Technical excellence + ethical grounding

---

## A) Roles & Separation of Duties

| Role | Name | Can Do | Cannot Do |
|------|------|--------|-----------|
| **Builder** | CODING_AGENT | Write specs, tests, code | Modify gates, CI, security configs |
| **Verifier** | CODE_GUARDIAN | Run gates, produce evidence | Write code, change policy |
| **Approver** | HUMAN | Everything | N/A |

This separation is **non-negotiable**. The Builder cannot self-certify. The Verifier cannot approve its own suggestions.

### File Ownership

```
HUMAN-ONLY EDITABLE:
├── swarm/gates.yaml           # Gate definitions
├── swarm/policy/              # Policy controls & exceptions
├── .github/workflows/*.yml    # CI pipelines
├── security/*.yaml            # Security configs
└── .secrets.baseline          # Secret detection baseline

BUILDER-EDITABLE:
├── src/                       # Application code
├── tests/                     # Test code
├── docs/                      # Documentation
└── *.md                       # Markdown files (except HAZARDS.md, ROLLBACK.md)
```

---

## B) Gate Architecture (17 Gates)

### Technical Gates (1-8)

| ID | Gate | Tool | On Failure | Evidence |
|----|------|------|------------|----------|
| 1 | LINT_FORMAT | ruff | Block | ruff_output.json, format_diff.patch |
| 2 | TYPE_CHECK | pyright --strict | Block | pyright_report.json |
| 3 | SECURITY_SCAN | bandit + detect-secrets | Block | bandit_report.json, secrets_scan.json |
| 4 | DEPENDENCY_SAFETY | pip-audit | Block | pip_audit.json |
| 5 | TEST_COVERAGE | pytest --cov (≥80%) | Block | coverage.json |
| 6 | PROPERTY_TESTING | hypothesis | Block | hypothesis_stats.txt |
| 7 | CONTRACT_INTEGRATION | pytest integration/ | Block | integration_results.xml |
| 8 | PERFORMANCE_REGRESSION | pytest benchmarks/ | Block | benchmark.json, benchmark_comparison.txt |

### Dharmic Gates (9-15)

| ID | Gate | Tier | Check | On Failure |
|----|------|------|-------|------------|
| 9 | AHIMSA | Absolute | HAZARDS.md exists | Block |
| 10 | SATYA | Strong | Claims backed by tests | Block |
| 11 | CONSENT | Strong | Human approval if risk ≥ medium | Block |
| 12 | VYAVASTHIT | Advisory | Telos alignment documented | Warn |
| 13 | REVERSIBILITY | Advisory | ROLLBACK.md exists | Warn |
| 14 | SVABHAAVA | Advisory | Change fits system nature | Warn |
| 15 | WITNESS | Advisory | Audit trail + evidence hash | Warn |

### Supply-Chain Gates (16-17)

| ID | Gate | Tool | On Failure | Evidence |
|----|------|------|------------|----------|
| 16 | SBOM_PROVENANCE | cyclonedx + SLSA | Block | sbom.json, slsa_provenance.txt |
| 17 | LICENSE_COMPLIANCE | pip-licenses | Block | licenses.json |

**License Policy:** Allow MIT, Apache-2.0, BSD. Fail on GPL, AGPL, LGPL, SSPL.

---

## C) ML Overlay

Applied **only to ML-touched code** (detected by imports or file paths):

| Gate | Check |
|------|-------|
| DATA_PROVENANCE | DATA_PROVENANCE.md + data_manifest.json |
| EVAL_SUITE | ML evaluation tests with accuracy/precision/recall |
| MODEL_CARD | MODEL_CARD.md with Intended Use, Limitations, Ethics |
| RISK_REGISTER | AI_RISK_REGISTER.md |
| REPRODUCIBILITY | requirements.txt + config.yaml:random_seed + environment.lock |

---

## D) Accelerator Overlay (CUDA / HPC)

Applied when accelerator code is detected (e.g., `*.cu`, `torch.cuda`, `cupy`, `cuda/`):

- **ACCELERATOR_PLAN** — ACCELERATOR_PLAN.md + HARDWARE_TARGETS.md
- **CUDA_COMPAT** — CUDA_COMPAT.md
- **ACCELERATOR_BENCHMARKS** — optional GPU baselines

---

## E) Rate Limits & Cost Controls

### Proposal Limits

```yaml
max_per_hour: 5
max_per_day: 20
cooldown_after_rejection: 2h
```

### Budget Controls

```yaml
daily_budget_usd: 20
alert_threshold_usd: 15
per_change_tracking: true
```

When budget exceeded:
- 90%: Pause non-critical proposals
- 95%: Alert human
- 100%: Hard stop

---

## F) Approval Timeouts

```yaml
reminder_after: 24h
escalate_after: 72h
auto_close_after: 7d
stale_reason: "No response - closing. Re-propose if still needed."
```

### Risk-Based Approval

| Risk Level | Requires Human | Auto-Approve |
|------------|----------------|--------------|
| Low | No | If gates pass |
| Medium | Yes (1 approver) | No |
| High | Yes (1+ approvers) | No |
| Critical | Yes + explicit ack | No |

---

## G) Evidence Signing & Policy Exceptions

### Evidence Signing (Hardwired)
Evidence bundles are signed (HMAC) using `EVIDENCE_SIGNING_KEY`.  
If the key is missing and signing is required, the gate run fails.

Set `EVIDENCE_SIGNING_KEY` in CI secrets and locally for trusted runs.

### Policy Exceptions (Human‑Only)
Exceptions are allowed **only** via `swarm/policy/exceptions.yaml` and must include:
- gate name or ID
- reason
- approver
- expiry date

Expired exceptions are ignored automatically.

---

## H) Performance Baselines

Performance regressions are enforced against a stored baseline:

```bash
python -m swarm.performance_baseline --update
```

Baseline file path: `benchmarks/baseline.json`.

---

## I) File Locking (Multi-Agent Safety)

Prevents race conditions when multiple agents modify files:

```python
from swarm.file_lock import FileLock

with FileLock("src/module.py", agent_id="CODING_AGENT", ttl=60):
    # File locked for 60 seconds

---

## J) Ecosystem Integration (DGC CLI)

To enforce the protocol across all projects, use the DGC bootstrap CLI:

```bash
# Install local CLI symlink (once)
./scripts/install_dgc_cli.sh

# Register global config for auto-discovery
dgc register

# Initialize a new repo with the DGC gates
dgc init --target /path/to/repo --with-proposal

# Verify gates locally
dgc verify --target /path/to/repo --dry-run

# Locate the protocol from any path
dgc locate --target /path/to/repo
```

The CLI copies the required gate engine, policy files, CI workflow, and baseline docs into the target repo.

---

## K) Systemic Risk Monitoring

Monitor coordination risk at the system level:

```bash
python -m swarm.systemic_monitor --events logs/interaction_events.jsonl
```

Compatible with OACP append-only logs (fields: `event`, `from`, `to`).

Policy thresholds live in:
`swarm/policy/systemic_risk.yaml`

---

## L) Red-Team Harness

Run the A/B simulation to validate that gates block known attack patterns:

```bash
python -m swarm.redteam.ab_harness
```

---

## M) Token Lifecycle (Revocation + Rotation)

Tokens are signed and time-boxed. Use the registry to issue, verify, revoke, and rotate:

```bash
python -m swarm.token_registry issue --agent CODING_AGENT --cap message --cap exec
python -m swarm.token_registry revoke --token-id <id> --reason "compromise"
python -m swarm.token_registry rotate --token-id <id>
```

---

## N) Skill Registry Signing

Skill registry is allowlisted and signed:

```bash
python -m swarm.skill_registry sign
python -m swarm.skill_registry verify
```

---

## O) Sandbox Execution Harness

Default-deny unless Docker is available and image is allowlisted:

```bash
python -m swarm.sandbox --code /path/to/script.py
```

---

## P) Anomaly Detection + ACP

Generate alerts and the Attested Compliance Profile:

```bash
python -m swarm.anomaly_detection
python -m swarm.compliance_profile
```

---

## Q) Safety Case Report Generator

Generate an updated safety case with live evidence:

```bash
python -m swarm.safety_case_report
```

    # Other agents cannot modify
    with open("src/module.py", "w") as f:
        f.write(new_content)
```

Features:
- Atomic acquisition with flock
- TTL prevents deadlocks from crashed agents
- Sorted acquisition order prevents deadlocks
- Lock status visible via CLI

---

## J) Emergency Bypass (Break-Glass)

For production emergencies **only**:

```bash
python -m swarm.run_gates \
    --proposal-id HOTFIX-001 \
    --emergency \
    --reason "Production API returning 500s" \
    --approver dhyana
```

### Non-Bypassable Gates

Even in emergency, these gates **always run**:
- AHIMSA (non-harm)
- LINT_FORMAT
- TYPE_CHECK
- SECURITY_SCAN

### Requirements

1. Explicit reason (>20 chars)
2. Named human approver
3. Logged to separate audit trail
4. **Mandatory post-mortem within 48h**

### Rate Limits

- Max 3 bypasses per week
- 24h cooldown between bypasses

---

## K) Production Feedback Loop

7-day audit after deployment:

| Day | Check |
|-----|-------|
| 1 | Initial smoke test - any immediate issues? |
| 3 | Short-term stability - error rates, performance |
| 7 | Full audit - comprehensive metrics review |

### Tracked Metrics

```python
@dataclass
class ProductionMetrics:
    errors_introduced: int
    error_rate_change_percent: float
    performance_delta_percent: float
    latency_p50_change_ms: float
    latency_p99_change_ms: float
    rollback_needed: bool
    user_complaints: int
    alerts_triggered: int
```

### Feedback Loop

Production data feeds back into:
1. **Proposal scoring** — Successful changes boost author reputation
2. **Risk assessment** — Problematic patterns increase risk scores
3. **Gate calibration** — If gates miss issues, they need tuning

### Cybernetics (Control Signal)
Production metrics are evaluated against setpoints to generate a **control signal**
(`stable` / `unstable`). Unstable signals automatically elevate risk and require
post‑mortem review.

Policy file: `swarm/policy/cybernetics.yaml`

---

## L) Usage

### Running Gates

```bash
# Standard run
python -m swarm.run_gates --proposal-id PROP-001

# Dry run (simulate)
python -m swarm.run_gates --proposal-id PROP-001 --dry-run

# Emergency bypass
python -m swarm.emergency_bypass request \
    --reason "Production down" \
    --approver dhyana
```

### File Locking

```bash
# Check lock status
python -m swarm.file_lock status

# Lock a file (for testing)
python -m swarm.file_lock lock src/module.py --agent CLI --ttl 60
```

### Performance Baseline

```bash
# Update benchmark baseline
python -m swarm.performance_baseline --update
```

### Production Feedback

```bash
# Register a deployment
python -m swarm.production_feedback register --proposal-id PROP-001

# Record metrics
python -m swarm.production_feedback metrics \
    --proposal-id PROP-001 \
    --errors 0 \
    --perf-delta -2.0

# Complete 7-day audit
python -m swarm.production_feedback audit \
    --proposal-id PROP-001 \
    --verdict success \
    --lesson "No issues observed"

# Check statistics
python -m swarm.production_feedback stats --days 30
```

---

## M) Evidence Bundle Schema

Every gate run produces an evidence bundle:

```json
{
  "proposal_id": "PROP-001",
  "timestamp": "2026-02-04T12:00:00Z",
  "overall_result": "PASS",
  "gates_passed": 15,
  "gates_failed": 0,
  "gates_warned": 2,
  "total_duration_seconds": 45.2,
  "gate_results": [...],
  "evidence_bundle_hash": "sha256:abc123...",
  "evidence_signature": "hmac:deadbeef...",
  "signature_method": "hmac-sha256",
  "signature_key_id": "abcd1234",
  "signature_required": true,
  "signature_present": true,
  "exceptions_applied": []
}
```

Evidence is stored in `evidence/{proposal_id}/` with:
- `gate_results.json` — Complete results
- `evidence_bundle.json` — All evidence
- `evidence_hash.sha256` — Integrity hash
- `evidence_signature.txt` — HMAC signature (if configured)

Retention:
- Success: 90 days
- Failure: 365 days

---

## N) Integration with Existing Swarm

The protocol integrates with the existing DHARMIC_GODEL_CLAW swarm:

1. **Orchestrator** calls `run_gates.py` after proposal generation
2. **DGM Integration** records gate results in evolution history
3. **Telos Layer** is extended with gates 9-15
4. **CODE_GUARDIAN** agent role added for verification

### Migration Path

1. Install pre-commit hooks: `pre-commit install`
2. Create initial `HAZARDS.md` and `ROLLBACK.md`
3. Run gates in dry-run mode: `--dry-run`
4. Enable CI workflow
5. Remove dry-run after validation

---

## O) Glossary

| Term | Definition |
|------|------------|
| **Gate** | A quality check that must pass before merge |
| **Tier** | Gate priority (absolute > required > strong > advisory) |
| **Evidence** | Artifacts proving gate execution |
| **Bypass** | Emergency skip of non-critical gates |
| **Post-mortem** | Required analysis after bypass |
| **AHIMSA** | Non-harm principle (Sanskrit) |
| **SATYA** | Truth principle (Sanskrit) |
| **VYAVASTHIT** | Natural order (Gujarati/Sanskrit) |
| **SVABHAAVA** | Intrinsic nature (Sanskrit) |

---

## P) Files

| Path | Purpose |
|------|---------|
| `swarm/gates.yaml` | Gate definitions (HUMAN-ONLY) |
| `swarm/run_gates.py` | Gate execution engine |
| `swarm/file_lock.py` | Multi-agent file locking |
| `swarm/emergency_bypass.py` | Break-glass mechanism |
| `swarm/production_feedback.py` | 7-day audit system |
| `swarm/policy/` | Rate limits, costs, approvals |
| `swarm/skill_supply_chain.py` | Skill supply-chain scanner |
| `swarm/policy/skill_supply_chain.yaml` | Skill supply-chain policy |
| `swarm/skill_registry.yaml` | Signed skill registry (hash-pinned) |
| `.pre-commit-config.yaml` | Local hooks |
| `.github/workflows/gates.yml` | CI workflow (HUMAN-ONLY) |
| `evidence/` | Gate evidence bundles |

---

## Q) Changelog

### v3.0 (2026-02-04)
- Initial hardened protocol
- 17 gates (8 technical, 7 dharmic, 2 supply-chain)
- ML overlay for ML-touched code
- Skill overlay: signed registry + hash pinning + supply-chain scanner (+ quarantine support)
- Rate limits and cost tracking
- Approval timeouts
- File locking for multi-agent safety
- Emergency bypass with mandatory post-mortem
- Production feedback loop

---

*JSCA!* 🪷
