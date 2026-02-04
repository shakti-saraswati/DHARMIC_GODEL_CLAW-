# ROLLBACK.md - DHARMIC_CLAW Rollback Procedures

> Required by REVERSIBILITY gate (Gate 13)

## Purpose

This document provides rollback procedures for all deployable changes. The REVERSIBILITY gate requires this file to exist and contain tested procedures.

---

## Quick Rollback

For most changes, use git revert:

```bash
# Identify the commit to rollback
git log --oneline -10

# Revert the specific commit
git revert <commit-sha>

# Push the revert
git push origin main
```

---

## Component-Specific Rollbacks

### Daemon (unified_daemon.py)

```bash
# Stop the daemon
launchctl unload ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist

# Restore previous version
git checkout HEAD~1 -- src/core/unified_daemon.py

# Restart
launchctl load ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
```

### Swarm Orchestrator

```bash
# Stop any running swarm process
pkill -f "swarm.run_swarm"

# Restore previous version
git checkout HEAD~1 -- swarm/orchestrator.py swarm/dgm_integration.py

# Verify syntax
python -m py_compile swarm/orchestrator.py
```

### Gate Configuration

```bash
# Gates are HUMAN-ONLY editable
# If gates.yaml is corrupted, restore from backup

cp backups/gates.yaml.backup swarm/gates.yaml

# Verify
python -c "import yaml; yaml.safe_load(open('swarm/gates.yaml'))"
```

### Telos Layer

```bash
# Restore telos layer
git checkout HEAD~1 -- src/core/telos_layer.py

# Run tests to verify
pytest tests/test_telos_layer.py -v
```

---

## Database Rollbacks

If using database migrations:

```bash
# List migrations
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>
```

---

## Full System Rollback

For complete system rollback:

```bash
# 1. Stop all services
launchctl unload ~/Library/LaunchAgents/com.dharmic.*.plist

# 2. Identify last known good state
git log --oneline | head -20

# 3. Hard reset (CAUTION: loses uncommitted changes)
git reset --hard <last-good-commit>

# 4. Restore dependencies
pip install -r requirements.txt

# 5. Run tests
pytest tests/ -v

# 6. Restart services
launchctl load ~/Library/LaunchAgents/com.dharmic.unified-daemon.plist
```

---

## Rollback Verification

After any rollback:

1. **Check logs:** `tail -f logs/unified_daemon/*.log`
2. **Run health check:** `python -m swarm.run_gates --proposal-id ROLLBACK-VERIFY --dry-run`
3. **Verify core functions:** `pytest tests/test_core.py -v`

---

## Rollback Decision Matrix

| Symptom | First Action | Escalation |
|---------|--------------|------------|
| API errors | Check logs, restart daemon | Rollback daemon |
| Gate failures | Dry-run gates, check config | Rollback gates.yaml |
| Performance degradation | Check benchmarks | Rollback recent changes |
| Security alert | Immediate rollback | Notify human |

---

## Emergency Contacts

- **Primary:** dhyana (johnvincentshrader@gmail.com)
- **WhatsApp:** +818054961566

---

## Rollback Log

Record all rollbacks here:

| Date | Component | Reason | Commit | Duration |
|------|-----------|--------|--------|----------|
| TBD | - | - | - | - |

---

*Last tested: 2026-02-04*
*Reviewed by: dhyana*
