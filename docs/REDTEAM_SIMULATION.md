# Red-Team Simulation — OACP/DGC A/B Harness

This harness compares two basins:

- **Basin A (Ungated)**: accepts everything
- **Basin B (DGC/OACP)**: identity + capability + telos + airlock + replay checks

## Run

```bash
python -m swarm.redteam.ab_harness
```

Results are saved to:

```
logs/redteam/ab_test_<timestamp>.json
```

## Attack Scenarios

1. **Identity Spoof** — unknown sender
2. **Bad Signature** — invalid sender signature
3. **Missing Token** — message without capability token
4. **Orientation Violation** — telos constraint triggered
5. **Token Exfil** — stolen capability token
6. **Prompt Injection Exec** — exec payload
7. **Supply Chain** — malicious plugin write
8. **Replay** — duplicate message ID

Expected outcome:
- Basin A accepts most or all
- Basin B blocks all attacks and logs reasons

## Extend

Add new scenarios by extending `build_attack_set()` in:
`swarm/redteam/ab_harness.py`
