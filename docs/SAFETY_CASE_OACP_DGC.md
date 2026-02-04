# Safety Case — OACP/DGC v3 (Control Safety)

**Version:** 0.1
**Date:** 2026-02-04
**Scope:** Multi-agent coordination runtime with cryptographic identity, capability gating, and auditability.

---

## 1) System Description

OACP/DGC is a multi-agent runtime protocol that enforces:
- Cryptographic identity + steward binding
- Machine-readable telos constraints
- Explicit, time-boxed capability elevation
- Default-deny airlock for execution
- Append-only, hash-chained audit logs
- 17-gate protocol with evidence signing and CI enforcement

This safety case is **system-level** and addresses risks from **distributed/patchwork agents** (not model-level training safety).

---

## 2) Threat Model (v0.1)

**Threats in-scope**:
- Identity spoofing
- Capability abuse / token theft
- Prompt-injection → execution chain
- Supply-chain contamination
- Replay attacks
- Silent policy/gate bypass

**Out of scope (v0.1)**:
- Side-channel attacks on hardware
- Model weight extraction
- Fully automated governance

---

## 3) Claims

### C1 — Inability
**Claim:** High-risk actions cannot occur without explicit capability tokens and airlock approval.

**Controls:**
- Capability tokens (time-boxed)
- Telos constraints
- Airlock default-deny for exec

**Evidence:**
- `evidence/<proposal_id>/gate_results.json`
- `logs/redteam/ab_test_*.json` (airlock blocks)

### C2 — Control
**Claim:** All actions are logged, signed, and auditable; policy changes are non-bypassable.

**Controls:**
- Evidence signing (HMAC)
- Append-only audit logs
- CI as ultimate authority
- Policy guard for protected files

**Evidence:**
- `evidence/<proposal_id>/evidence_signature.txt`
- `evidence/<proposal_id>/gate_results.json`
- `.github/workflows/gates.yml`

---

## 4) Traceability to DeepMind Safety Requirements

**Reference:** DeepMind — *An Approach to Technical AGI Safety and Security* (Apr 2025) and *Distributional AGI Safety* (Dec 2025).

| DeepMind Requirement | OACP/DGC Control | Evidence |
|---|---|---|
| Restrict access to dangerous capabilities | Capability tokens + airlock | gate_results.json, redteam logs |
| Treat agents as untrusted insiders | Identity + least-privilege + audits | gate_results.json |
| Defense-in-depth | 17 gates + overlays | gates.yaml + evidence |
| Auditability / monitoring | Append-only logs + evidence signing | audit trails |
| System-level monitoring | Systemic risk monitor | systemic_monitor.py reports |

---

## 5) Evidence Bundle (Required)

A compliant change must include:
- Gate evidence outputs
- Signed evidence bundle
- SBOM + license compliance
- Red-team simulation (for high-risk changes)

**Required files:**
- `evidence/<proposal_id>/gate_results.json`
- `evidence/<proposal_id>/evidence_signature.txt`
- `sbom.json`, `licenses.json`

**OACP Coordination:** The systemic monitor accepts OACP append-only logs
(`event`, `from`, `to`) as input for graph-level risk metrics.

---

## 6) Residual Risks

- Reputation and market design not yet implemented
- Real-time anomaly detection not fully integrated
- Human approval required for critical changes

---

## 7) Planned Iterations

1) Integrate systemic risk monitoring into production feedback loop.
2) Add reputation or compliance profiles based on audit history.
3) Expand red-team scenarios to include data exfiltration and lateral movement.

---

## 8) Verification

Run the red-team harness:

```bash
python -m swarm.redteam.ab_harness
```

Generate systemic risk report:

```bash
python -m swarm.systemic_monitor --events logs/interaction_events.jsonl
```

Generate the safety case report with live evidence:

```bash
python -m swarm.safety_case_report
```
