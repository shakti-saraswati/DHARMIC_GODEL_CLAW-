# Ecosystem Integration

Goal: make DGC gates automatic, memorable, and repeatable for every project.

## One-Time Setup

```bash
# Install the CLI (adds a stable `dgc` command)
./scripts/install_dgc_cli.sh

# Register global config for auto-discovery
dgc register
```

Ensure `~/.local/bin` is on PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Per-Project Bootstrap

```bash
# Initialize a repo with the DGC protocol
# (copies gates, policy, CI, and templates)
dgc init --target /path/to/repo --with-proposal

# Verify locally (dry-run)
dgc verify --target /path/to/repo --dry-run

# Locate protocol from any subdirectory
dgc locate --target /path/to/repo
```

## Recommended Team Practice
- Always create a `proposal.yaml` for any change.
- Run `dgc verify` before pushing.
- Keep `EVIDENCE_SIGNING_KEY` set for trusted runs.

## Auto-Discovery (for Clawdbot / Claude Code)

Both can discover the protocol via:

- Global config: `~/.config/dgc/config.yaml`
- Project marker: `.dgc/config.yaml`
- CLI: `dgc locate --export` to export `DGC_ROOT`, `DGC_GATES_PATH`, `DGC_POLICY_PATH`

## OACP Integration

If OACP is installed at `~/repos/oacp`, you can feed its logs into the systemic monitor:

```bash
python -m swarm.systemic_monitor --events ~/repos/oacp/oacp_demo.log
```

See `docs/OACP_INTEGRATION.md` for more.

## CI Requirements
- Add `EVIDENCE_SIGNING_KEY` to repo secrets.
- Ensure Python deps + gate tools are installed in CI.

## Optional: Repo Bootstrap Script

You can wrap project creation with DGC init:

```bash
mkdir new-project && cd new-project

# init git and apply DGC gates
# (do this before writing code)
git init
DGC_ROOT="$HOME/DHARMIC_GODEL_CLAW"
"$DGC_ROOT/scripts/dgc" init --target . --with-proposal
```
