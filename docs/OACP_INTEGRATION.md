# OACP Integration

This project can consume OACP logs to compute systemic risk and ACP profiles.

## Systemic Risk from OACP Logs

If you run OACP demos, they produce append-only logs (e.g., `oacp_demo.log`).
You can feed those logs into the systemic monitor:

```bash
python -m swarm.systemic_monitor --events ~/repos/oacp/oacp_demo.log
```

## ACP Profile with OACP Signals

Generate the ACP profile (includes systemic risk snapshot):

```bash
python -m swarm.compliance_profile
```

## Red-Team A/B Harness

Run the DGC red-team harness in this repo to validate gating invariants:

```bash
python -m swarm.redteam.ab_harness
```

