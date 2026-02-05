# Cosmic Krishna Coder System

The **Cosmic Krishna Coder** is the action layer of the Dharmic Council
("Sri Krishna the Cosmic Koder") combined with the **17‑Gate Protocol**
and the **Top‑50 Quality Rubric**. Its purpose is to make enforcement
memorable, visible, and non‑bypassable.

## What it includes

- **CosmicChrisnaCoder_Gate_Runner** alias (memorable gate runner)
- **Quality Rubric** anchored to Top‑50 references
- **ML Overlay** gates for ML‑touched changes
- **TUI visibility** via `/cosmic` and status row
- **Skill availability** for OpenClaw / Clawdbot / Claude Code

## Primary entrypoints

- Gate runner alias:
  ```bash
  python3 swarm/CosmicChrisnaCoder_Gate_Runner.py --proposal-id PROP-001 --dry-run
  ```

- Unified TUI:
  ```bash
  dgc
  # then /cosmic
```

## Shared skill install (team setup)

Shared skill root (team-wide):
`/Users/Shared/skills-shared`

Install symlinks for any user:
```bash
~/DHARMIC_GODEL_CLAW/scripts/install_shared_skills.sh
```

## Canonical references

- `docs/QUALITY_RUBRIC.md`
- `docs/TOP_50_QUALITY_REFERENCES.md`
- `swarm/gates.yaml`

## Design intent

The Cosmic Krishna Coder is not a single script. It is a **system**:
- a memorable gate runner alias,
- formalized quality rubric + exemplars,
- TUI visibility,
- and gate enforcement embedded in the pipeline.

If any of the references above are missing, the SATYA gate will fail.
