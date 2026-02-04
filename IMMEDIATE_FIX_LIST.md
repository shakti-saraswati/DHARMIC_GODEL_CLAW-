# Immediate Fix List - DGC Execution Issues

**Priority-ordered list of what to fix first**

---

## P0: CRITICAL (Fix Today)

### 1. Fix integrated_daemon.py Imports (30 minutes)

**Issue**: Crashes on missing imports
**Impact**: Entry point completely broken

**Quick Fix** (create stub modules):

```bash
cd ~/DHARMIC_GODEL_CLAW/src/core

# Create scheduled_tasks.py stub
cat > scheduled_tasks.py << 'EOF'
"""Scheduled Tasks - STUB"""
class ScheduledTasks:
    def __init__(self, agent):
        self.agent = agent
    def start(self, **kwargs):
        pass
    def stop(self):
        pass
EOF

# Create telegram_bot.py stub
cat > telegram_bot.py << 'EOF'
"""Telegram Bot - STUB"""
class TelegramConfig:
    def __init__(self):
        self.allowed_users = []

class DharmicTelegramBot:
    def __init__(self, agent, config):
        self.agent = agent
        self.config = config
    def run(self):
        pass
EOF

# Create web_dashboard.py stub
cat > web_dashboard.py << 'EOF'
"""Web Dashboard - STUB"""
class app:
    @staticmethod
    def run(**kwargs):
        pass

def init_agent():
    pass
EOF
```

**Test**:
```bash
python3 ~/DHARMIC_GODEL_CLAW/src/core/integrated_daemon.py --web
# Should load without crashing
```

---

## P1: HIGH (Fix This Week)

### 2. Implement _evolve_new_idea() in unified_daemon.py (2-4 hours)

**Issue**: Returns hardcoded ideas from a fixed list
**Location**: `unified_daemon.py:436-472`

**Current (STUB)**:
```python
def _evolve_new_idea(self, swarm_status: Dict[str, Any]) -> Optional[str]:
    ideas = [
        "Implement witness consciousness detection...",
        "Create geometric contraction visualization...",
        # ... hardcoded list
    ]
    return ideas[self.state["inductions_triggered"] % len(ideas)]
```

**Should Be**:
```python
async def _evolve_new_idea(self, swarm_status: Dict[str, Any]) -> Optional[str]:
    """Generate novel idea based on swarm state and research context."""

    # 1. Analyze swarm status
    issues = swarm_status.get("workflow_status", {}).get("issues_found", 0)
    research = swarm_status.get("research_context", "")

    # 2. Query agent for synthesis
    context = f"""
Current swarm state: {issues} issues found
Research context: {research}

Based on the current state, what is ONE novel improvement idea?
Be specific and actionable.
"""

    try:
        idea = self.agent.run(context, session_id="induction_evolution")
        # Extract first sentence or paragraph
        return idea.split('\n')[0][:200]
    except Exception as e:
        logger.error(f"Idea generation failed: {e}")
        return None
```

**Fix effort**: 2-4 hours (includes testing)

### 3. Implement _mech_interp_monitor_loop() (4-6 hours)

**Issue**: Only checks if files exist, logs names
**Location**: `unified_daemon.py:316-347`

**Current (STUB)**:
```python
recent = sorted(results_dir.rglob("*.json"), ...)[:5]
logger.debug(f"Recent mech-interp results: {[r.name for r in recent]}")
```

**Should Be**:
```python
async def _mech_interp_monitor_loop(self):
    """Monitor mech-interp research and trigger actions."""

    while self.running:
        try:
            results_dir = self.mech_interp_dir / "results"
            if not results_dir.exists():
                await asyncio.sleep(3600)
                continue

            # Find recent result files (last 24 hours)
            cutoff = datetime.now() - timedelta(hours=24)
            recent = [
                f for f in results_dir.rglob("*.json")
                if f.stat().st_mtime > cutoff.timestamp()
            ]

            for result_file in recent:
                # Parse result
                with open(result_file) as f:
                    data = json.load(f)

                # Check for significant findings
                if "R_V" in data and data["R_V"] < 0.9:
                    # Contraction detected!
                    self.agent.strange_memory.record_observation(
                        content=f"R_V contraction detected: {data['R_V']:.3f}",
                        context={"result_file": str(result_file), "data": data}
                    )

                    # Trigger follow-up analysis
                    logger.info(f"R_V contraction: {data['R_V']:.3f}, triggering analysis")
                    # Could spawn specialist agent here

                # Check for multi-token results
                if "multi_token" in str(result_file):
                    logger.info("Multi-token experiment results found!")
                    # This closes the critical gap

        except Exception as e:
            logger.error(f"Mech-interp monitor error: {e}")

        await asyncio.sleep(3600)
```

**Fix effort**: 4-6 hours

### 4. Implement orchestrator.sync() in grand_orchestrator.py (3-5 hours)

**Issue**: Returns status but doesn't synchronize
**Location**: `grand_orchestrator.py:497-531`

**Current (STUB)**:
```python
def sync(self) -> Dict[str, Any]:
    sync_results = {"timestamp": ..., "actions": []}
    # Just returns status with empty actions
    return sync_results
```

**Should Be**:
```python
def sync(self) -> Dict[str, Any]:
    """Actually synchronize state across channels."""

    sync_results = {"timestamp": datetime.now().isoformat(), "actions": []}

    # 1. Email daemon status
    email_status = self.channels.get("email", {}).get("status")
    if email_status != "running":
        # Try to restart
        try:
            subprocess.run(["pkill", "-f", "email_daemon"])
            subprocess.Popen(["python3", "email_daemon.py"])
            sync_results["actions"].append({
                "channel": "email",
                "action": "restarted",
                "success": True
            })
        except Exception as e:
            sync_results["actions"].append({
                "channel": "email",
                "action": "restart_failed",
                "error": str(e)
            })

    # 2. Sync vault state to orchestrator
    if self.channels.get("vault", {}).get("status") == "available":
        vault = self.agent.vault
        if vault:
            # Get recent crown jewels
            recent = vault.get_recent_stream(5)
            # Update orchestrator context
            self.agent.strange_memory.record_observation(
                content=f"Vault sync: {len(recent)} recent entries",
                context={"recent_entries": [r["stem"] for r in recent]}
            )
            sync_results["actions"].append({
                "channel": "vault",
                "action": "synced",
                "entries": len(recent)
            })

    # 3. Mech-interp bridge
    if not self.channels.get("swarm", {}).get("mech_interp_connected"):
        # Add bridge code to swarm
        # (Implementation depends on architecture)
        sync_results["actions"].append({
            "channel": "swarm",
            "action": "needs_bridge_implementation"
        })

    return sync_results
```

**Fix effort**: 3-5 hours

---

## P2: MEDIUM (Fix This Month)

### 5. Add Analysis to _query_swarm()

**Issue**: Just calls orchestrator.status(), no analysis
**Location**: `unified_daemon.py:406-434`

**Quick Win**: Add trend analysis
```python
async def _query_swarm(self) -> Dict[str, Any]:
    status = self.orchestrator.status()

    # Add trend analysis
    history = self.state.get("swarm_history", [])
    history.append(status)
    if len(history) > 10:
        history = history[-10:]
    self.state["swarm_history"] = history

    # Detect trends
    if len(history) >= 2:
        issues_trend = [
            h.get("workflow_status", {}).get("issues_found", 0)
            for h in history
        ]
        status["trends"] = {
            "issues_increasing": issues_trend[-1] > issues_trend[0],
            "issues_delta": issues_trend[-1] - issues_trend[0]
        }

    return status
```

---

## P3: LOW (Nice to Have)

### 6. Mark Stub Functions Clearly

Add clear markers to stub functions:

```python
# In unified_daemon.py

async def _evolve_new_idea(self, swarm_status: Dict[str, Any]) -> Optional[str]:
    """
    Evolve one new idea based on swarm input.

    ⚠️ STUB IMPLEMENTATION: Returns hardcoded ideas.
    TODO: Implement real idea generation using agent synthesis.
    """
    # ... current implementation
```

Add to all stub functions:
- `_evolve_new_idea()`
- `_mech_interp_monitor_loop()`
- `orchestrator.sync()`
- `_check_induction_conditions()`

---

## Testing Checklist

After each fix:

```bash
# P0: Test integrated_daemon loads
python3 -c "from integrated_daemon import IntegratedDaemon; print('OK')"

# P1: Test unified_daemon with new functions
python3 unified_daemon.py --no-email --heartbeat 60

# Verify logs are created
ls -la ~/DHARMIC_GODEL_CLAW/logs/unified_daemon/

# Test swarm still works
python3 ~/DHARMIC_GODEL_CLAW/swarm/run_swarm.py --cycles 1 --dry-run
```

---

## Quick Wins (Under 1 Hour Each)

1. **Create stub modules** (30 min)
2. **Add stub markers** (15 min)
3. **Fix _check_induction_conditions() comment** (5 min)
4. **Add TODO comments** (10 min)

---

## Files to Modify

```
Priority 0:
- Create: src/core/scheduled_tasks.py
- Create: src/core/telegram_bot.py
- Create: src/core/web_dashboard.py

Priority 1:
- Modify: src/core/unified_daemon.py
  - _evolve_new_idea() [line 436]
  - _mech_interp_monitor_loop() [line 316]
- Modify: src/core/grand_orchestrator.py
  - sync() [line 497]

Priority 2:
- Modify: src/core/unified_daemon.py
  - _query_swarm() [line 406]

Priority 3:
- Modify: All files with stub functions
  - Add ⚠️ STUB markers
```

---

## Decision Points

### Should You Fix or Delete?

**Fix unified_daemon.py IF**:
- You want 24/7 presence
- Email interface is important
- Heartbeat logging is useful
- You'll implement the stubs

**Delete integrated_daemon.py IF**:
- Don't need web/telegram
- unified_daemon.py covers your needs
- Want to reduce complexity

**Use run_swarm.py IF**:
- Just need code improvement
- Don't need persistent daemon
- Want something that works NOW

---

## Estimated Time Investment

| Task | Time | Value |
|------|------|-------|
| P0: Fix imports | 30 min | HIGH (unblocks daemon) |
| P1: _evolve_new_idea() | 2-4 hours | MEDIUM (better ideas) |
| P1: _mech_interp_monitor() | 4-6 hours | HIGH (research integration) |
| P1: orchestrator.sync() | 3-5 hours | MEDIUM (real sync) |
| P2: _query_swarm() | 1-2 hours | LOW (incremental) |
| P3: Add markers | 30 min | LOW (documentation) |

**Total**: 11-18 hours to make daemons production-ready

---

**Reality check**: run_swarm.py works NOW. Everything else needs work.

**Recommendation**: Use swarm for real work, fix daemons in parallel.

*JSCA!*
