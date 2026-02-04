# SEQUENCE VALIDATION: Dharmic Foundation Build

**Validator**: Architect Reviewer
**Date**: 2026-02-03
**Source**: DHARMIC_FOUNDATION_BUILD.md

---

## DEPENDENCY ANALYSIS

### Phase 1: Fix Clawdbot (30 min)
**Components**: claude-max-api-proxy, clawdbot.json config, LaunchAgent
**Dependencies**: None (standalone infrastructure)
**Outputs**: Working proxy on localhost:3456, clawdbot using Max subscription

### Phase 2: Build Core Agent (2-3 hours)
**Components**: dharmic_agent.py, skill_bridge.py
**Dependencies**: NONE on Phase 1
**Outputs**: Standalone Python modules with CLI

### Phase 3: Configure Scheduling (1 hour)
**Components**: HEARTBEAT.md, clawdbot config, cron jobs
**Dependencies**: Phase 1 (clawdbot working), Phase 2 (agent exists)
**Outputs**: Scheduled heartbeat, cron jobs

### Phase 4: Validation (30 min)
**Dependencies**: All phases complete

---

## BLOCKING ANALYSIS

| Blocker Claim | Actual Dependency | Verdict |
|---------------|-------------------|---------|
| Phase 2 needs Phase 1 | dharmic_agent.py uses OpenAI/Anthropic SDK directly | FALSE |
| Phase 3 needs Phase 1 | Heartbeat uses clawdbot CLI | TRUE |
| Phase 3 needs Phase 2 | Cron invokes dharmic_agent.py | TRUE |

---

## CRITICAL FINDING: PHASE 1 IS NOT BLOCKING FOR PHASE 2

### Evidence from dharmic_agent.py (lines 46-86):

```python
def __init__(self, name: str = "DHARMIC_CLAW", model: str = "claude-opus-4", backend: str = "proxy"):
    # Two backends supported:
    # 1. "direct": Uses Anthropic SDK with OAuth token
    # 2. "proxy": Uses OpenAI SDK pointing to localhost:3456
```

The core agent has TWO backend options:
- **proxy mode**: Uses clawdbot's claude-max-api-proxy (Phase 1 dependency)
- **direct mode**: Uses Anthropic SDK with OAuth token (NO Phase 1 dependency)

### Verification:
- Lines 66-85: Direct backend uses `anthropic.Anthropic(api_key=oauth_token)`
- Lines 79-85: Proxy backend uses `OpenAI(base_url="http://localhost:3456/v1")`
- skill_bridge.py: 100% filesystem operations, zero clawdbot dependency

---

## OPTIMAL SEQUENCE (PARALLELIZED)

### TRACK A: Core Development (Independent)
```
[0-120 min] Phase 2: Build dharmic_agent.py + skill_bridge.py
  - Use "direct" backend mode initially
  - Test with: python3 dharmic_agent.py status
  - Test with: python3 dharmic_agent.py chat
  - Set ANTHROPIC_OAUTH_TOKEN env var
  - NO clawdbot dependency during development
```

### TRACK B: Infrastructure (Independent)
```
[0-30 min] Phase 1: Fix clawdbot proxy
  - Install claude-max-api-proxy
  - Configure clawdbot.json
  - Create LaunchAgent
  - Test: clawdbot agent -m "test" --local
```

### CONVERGENCE: Integration
```
[120+ min] Phase 3: Configure Scheduling
  - Requires: Track A complete (agent exists)
  - Requires: Track B complete (clawdbot works)
  - Switch dharmic_agent.py to "proxy" backend
  - Add heartbeat config to clawdbot.json
  - Create cron jobs that invoke agent
```

### FINAL: Validation
```
[180+ min] Phase 4: Validation
  - Test proxy mode works
  - Test heartbeat delivery
  - Test cron execution
  - Document status
```

---

## EFFICIENCY GAINS

| Metric | Sequential | Parallel | Gain |
|--------|-----------|----------|------|
| Time to working agent | 2.5-3.5 hours | 2-3 hours | -30 min |
| Risk of blocked progress | High | Low | - |
| Ability to test core logic | Blocked | Immediate | Critical |

---

## RECOMMENDED CHANGES TO PROMPT

### Replace "Each phase must COMPLETE before next begins" with:

**Phase Execution Strategy**:
1. Run Phase 1 and Phase 2 IN PARALLEL (no dependencies)
2. Once BOTH complete, proceed to Phase 3
3. After Phase 3, run Phase 4

### Add to Phase 2 instructions:

**Backend Selection**:
- For initial development: Use `backend="direct"` mode
- Set environment variable: `export ANTHROPIC_OAUTH_TOKEN="sk-ant-oat-..."`
- Test agent independently of clawdbot
- Switch to `backend="proxy"` only after Phase 1 completes

---

## HIDDEN DEPENDENCIES DISCOVERED

### In Phase 2 (Not documented):
- **Python dependencies**: openai, anthropic SDKs
- **Filesystem dependencies**: ~/DHARMIC_GODEL_CLAW/swarm/stream/ directory structure
- **Module dependencies**: telos_layer.py, strange_memory.py must exist

### In Phase 3 (Implicit):
- **clawdbot features**: Requires clawdbot cron command (may not exist)
- **Heartbeat protocol**: Assumes clawdbot supports heartbeat config
- **WhatsApp gateway**: Assumes configured in clawdbot.json

---

## TIME ESTIMATE VALIDATION

| Phase | Stated | Realistic | Notes |
|-------|--------|-----------|-------|
| Phase 1 | 30 min | 30-45 min | Proxy install simple, config can be tricky |
| Phase 2 | 2-3 hours | 1.5-2.5 hours | Code already exists, just needs placement |
| Phase 3 | 1 hour | 1-2 hours | Depends on clawdbot cron support |
| Phase 4 | 30 min | 15-30 min | Mostly verification |
| **Total** | **4-5 hours** | **3-6 hours** | Parallel: 3-4 hours |

---

## SAFE PARALLEL WORK

### Can run simultaneously without conflict:
1. Phase 1 (clawdbot setup) + Phase 2 (Python development)
2. Reading/analysis tasks during either phase
3. Documentation during development

### CANNOT overlap:
1. Phase 3 requires both Phase 1 AND Phase 2 outputs
2. Phase 4 validation needs full system operational

---

## BLOCKER RISKS

### If Phase 1 fails:
- Agent still works in "direct" mode
- Heartbeat won't deliver (no messaging gateway)
- Cron jobs can still invoke agent locally
- **Severity**: Medium (reduces automation, doesn't kill agent)

### If Phase 2 fails:
- Nothing to schedule
- Foundation doesn't exist
- **Severity**: Critical (entire build fails)

### If Phase 3 fails:
- Agent exists but isn't scheduled
- Manual invocation still works
- **Severity**: Low (automation delayed, core works)

---

## RECOMMENDED EXECUTION ORDER

```
START
├── [PARALLEL]
│   ├── Execute Phase 1 (clawdbot)
│   └── Execute Phase 2 (core agent)
├── [WAIT FOR BOTH]
├── Execute Phase 3 (scheduling integration)
└── Execute Phase 4 (validation)
```

**Rationale**: Phases 1 and 2 are independent. Running them in parallel saves 30-60 minutes and allows immediate testing of core logic without infrastructure blocking.
