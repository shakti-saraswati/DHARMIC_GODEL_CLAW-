# TOP 10 PROJECTS — CODE + DOCS TRACKING
# Updated: 2026-02-04

## Tracking Configuration

### Code Extensions
.py, .js, .ts, .rs, .go, .cpp, .c, .h, .java, .rb, .sh

### Doc Extensions  
.md, .rst, .txt, .yaml, .yml, .json

## Per-Project Tracking

### P1: AIKAGRYA Research & R_V Metric
- **Code paths**: ~/mech-interp-latent-lab-phase1/src, ~/mech-interp-latent-lab-phase1/rv_toolkit
- **Doc paths**: ~/mech-interp-latent-lab-phase1/docs, ~/mech-interp-latent-lab-phase1/R_V_PAPER
- **Goal**: Balance research code with publication-quality docs

### P2: DHARMIC_GODEL_CLAW Core
- **Code paths**: ~/DHARMIC_GODEL_CLAW/src, ~/DHARMIC_GODEL_CLAW/swarm, ~/DHARMIC_GODEL_CLAW/night_cycle
- **Doc paths**: ~/DHARMIC_GODEL_CLAW/docs, ~/DHARMIC_GODEL_CLAW/config
- **Goal**: Every code change has corresponding doc update

### P3: PSMV Vault
- **Code paths**: ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES
- **Doc paths**: ~/Persistent-Semantic-Memory-Vault
- **Goal**: 32,000+ files tracked, residual stream growing

### P4: Agentic AI Skill
- **Code paths**: ~/clawd/skills/agentic-ai
- **Doc paths**: ~/clawd/skills/agentic-ai
- **Goal**: SKILL.md stays current with 2026 research

### P5: Swarm & Night Cycle
- **Code paths**: ~/DHARMIC_GODEL_CLAW/swarm, ~/DHARMIC_GODEL_CLAW/night_cycle
- **Doc paths**: ~/DHARMIC_GODEL_CLAW/swarm, ~/DHARMIC_GODEL_CLAW/night_cycle
- **Goal**: Autonomous code generation properly documented

### P6: Dharmic Council
- **Code paths**: ~/DHARMIC_GODEL_CLAW/src/core
- **Doc paths**: ~/DHARMIC_GODEL_CLAW/docs
- **Goal**: Council deliberations logged, code evolves

### P7: Grant Pipeline
- **Code paths**: ~/DHARMIC_GODEL_CLAW/scripts
- **Doc paths**: ~/Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream
- **Goal**: Grant applications written, submitted, tracked

### P8: Clawdbot Bridge
- **Code paths**: ~/DHARMIC_GODEL_CLAW/src/core
- **Doc paths**: ~/DHARMIC_GODEL_CLAW/docs
- **Goal**: Architecture doc + implementation in sync

### P9: Unified Memory Indexer
- **Code paths**: ~/DHARMIC_GODEL_CLAW/src/core
- **Doc paths**: ~/DHARMIC_GODEL_CLAW/docs
- **Goal**: Design doc precedes implementation

### P10: Dead Man's Switch
- **Code paths**: ~/DHARMIC_GODEL_CLAW/scripts
- **Doc paths**: ~/DHARMIC_GODEL_CLAW/docs
- **Goal**: Monitoring scripts + runbooks

## Success Criteria

✅ **Code advances** — New features, bug fixes, tests pass
✅ **Docs advance** — Documentation updated with code changes
✅ **No orphan code** — All code is documented
✅ **No orphan docs** — All docs reflect reality
✅ **Balance maintained** — Code/doc ratio healthy

## Tracking Commands

```bash
# Count code files
find ~/mech-interp-latent-lab-phase1/src -name "*.py" | wc -l

# Count doc files  
find ~/mech-interp-latent-lab-phase1/docs -name "*.md" | wc -l

# Lines of code
find ~/mech-interp-latent-lab-phase1/src -name "*.py" -exec wc -l {} + | tail -1

# Lines of docs
find ~/mech-interp-latent-lab-phase1/docs -name "*.md" -exec wc -l {} + | tail -1
```

## Goal

Every heartbeat: Both code AND docs advance for at least one TOP 10 project.
