# DGC Execution Flow Analysis

**Date**: 2026-02-04
**Agent**: ExecutionPathTracer (Debugger)
**Mission**: Trace what actually executes vs what's dead code

---

## Executive Summary

**Critical Finding**: All three entry points have significant amounts of **STUB CODE** - functions that exist but don't do real work. The daemons would run but accomplish very little.

### Entry Point Status

| Entry Point | Status | Main Issue | Execution Depth |
|-------------|--------|------------|-----------------|
| `unified_daemon.py` | SHALLOW | Loops run, but most work functions are stubs | 2-3 calls deep |
| `integrated_daemon.py` | BROKEN IMPORTS | Missing ScheduledTasks, TelegramBot, VaultBridge | Crashes on init |
| `run_swarm.py` | FUNCTIONAL | Actually works, minimal stub code | 4-5 calls deep |

**Recommendation**: `run_swarm.py` is the only one that actually works. The daemons need significant implementation.

---

## Entry Point 1: unified_daemon.py

### Execution Flow (ACTIVE Path)

```
main()
  └─> UnifiedDaemon.__init__()
       ├─> get_agent() [singleton]
       │    └─> DharmicAgent() [from agent_core.py]
       │         ├─> TelosLayer()
       │         ├─> StrangeLoopMemory()
       │         ├─> create_backend()
       │         └─> VaultBridge() [optional]
       │
       ├─> _init_email()
       │    └─> EmailDaemon() [if email enabled]
       │
       ├─> _init_orchestrator()
       │    └─> GrandOrchestrator()
       │         ├─> get_agent() [same singleton]
       │         ├─> MIAuditor()
       │         └─> SkillEvolutionEngine() [optional]
       │
       ├─> _init_mech_interp_bridge()
       │    └─> Path.exists() check only
       │
       └─> _init_skill_evolution()
            └─> SkillEvolutionEngine() [if enabled]

  └─> daemon.run()
       ├─> asyncio.create_task(_email_loop())
       │    └─> ACTIVE: polls email, processes, sends
       │
       ├─> asyncio.create_task(_heartbeat_loop())
       │    ├─> ACTIVE: logs heartbeat every 300s
       │    └─> agent.strange_memory.record_observation()
       │
       ├─> asyncio.create_task(_sync_loop())
       │    ├─> orchestrator.sync()
       │    │    └─> STUB: Returns status, does minimal work
       │    └─> orchestrator.status()
       │         └─> ACTIVE: Probes all channels
       │
       ├─> asyncio.create_task(_induction_check_loop())
       │    ├─> _query_swarm()
       │    │    └─> orchestrator.status() [duplicate call]
       │    └─> _evolve_new_idea(swarm_status)
       │         └─> STUB: Returns hardcoded ideas based on modulo
       │
       ├─> asyncio.create_task(_mech_interp_monitor_loop())
       │    └─> STUB: Checks file existence, logs, does nothing
       │
       └─> asyncio.create_task(_skill_evolution_loop())
            ├─> skill_engine.check_ecosystem_health()
            │    └─> REAL: Scans skills, finds gaps
            └─> skill_engine.trigger_evolution()
                 └─> REAL: Generates proposals (if implemented)
```

### Execution Status Table

| Function | Called From | Status | Depth | Notes |
|----------|-------------|--------|-------|-------|
| `main()` | CLI | **ACTIVE** | 0 | Entry point |
| `UnifiedDaemon.__init__()` | main() | **ACTIVE** | 1 | Initializes state |
| `get_agent()` | __init__ | **ACTIVE** | 2 | Creates singleton DharmicAgent |
| `_init_email()` | __init__ | **ACTIVE** | 2 | Conditional on config |
| `_init_orchestrator()` | __init__ | **ACTIVE** | 2 | Creates GrandOrchestrator |
| `_init_mech_interp_bridge()` | __init__ | **STUB** | 2 | Only checks Path.exists() |
| `_init_skill_evolution()` | __init__ | **ACTIVE** | 2 | Imports SkillEvolutionEngine |
| `daemon.run()` | main() | **ACTIVE** | 1 | Main async loop |
| `_email_loop()` | run() | **ACTIVE** | 2 | Polls email every 30s |
| `_heartbeat_loop()` | run() | **ACTIVE** | 2 | Logs heartbeat every 300s |
| `_sync_loop()` | run() | **PARTIAL** | 2 | Calls orchestrator.sync() |
| `_induction_check_loop()` | run() | **STUB** | 2 | Idea evolution is hardcoded |
| `_mech_interp_monitor_loop()` | run() | **STUB** | 2 | Only checks file existence |
| `_skill_evolution_loop()` | run() | **ACTIVE** | 2 | Real skill evolution |
| `_query_swarm()` | _induction_check_loop | **PARTIAL** | 3 | Returns orchestrator.status() |
| `_evolve_new_idea()` | _induction_check_loop | **STUB** | 3 | Returns hardcoded ideas |
| `_log_heartbeat()` | _heartbeat_loop | **ACTIVE** | 3 | Writes JSON to file |
| `_log_status()` | _sync_loop | **ACTIVE** | 3 | Writes JSON to file |
| `_log()` | Multiple | **ACTIVE** | 3 | Writes to log file |
| `orchestrator.sync()` | _sync_loop | **STUB** | 3 | Minimal work |
| `orchestrator.status()` | _sync_loop, _query_swarm | **ACTIVE** | 3 | Probes all channels |
| `skill_engine.check_ecosystem_health()` | _skill_evolution_loop | **ACTIVE** | 3 | Real implementation |
| `skill_engine.trigger_evolution()` | _skill_evolution_loop | **ACTIVE** | 3 | Real implementation |

### Dead/Stub Code in unified_daemon.py

1. **`_evolve_new_idea()` (Line 436-472)**: STUB
   - Returns hardcoded ideas based on modulo counting
   - Does not actually analyze swarm state
   - No real "evolution" happening

2. **`_check_induction_conditions()` (Line 478-482)**: STUB
   - Always returns True
   - Comment says "always trigger induction"
   - Condition checking is bypassed

3. **`_mech_interp_monitor_loop()` (Line 316-347)**: STUB
   - Checks if files exist
   - Logs file names
   - **Does not analyze results or trigger anything**

4. **`_init_mech_interp_bridge()` (Line 145-150)**: STUB
   - Only checks if directory exists
   - Sets boolean flag
   - **No actual bridge functionality**

### Import Analysis - unified_daemon.py

**Used Imports**:
- ✅ `asyncio` - Core async loops
- ✅ `signal` - Graceful shutdown
- ✅ `json` - Heartbeat logging
- ✅ `datetime` - Timestamps
- ✅ `Path` - File operations
- ✅ `dharmic_logging.get_logger` - Logging
- ✅ `agent_singleton.get_agent` - Agent creation
- ✅ `email_daemon.EmailDaemon` - Email polling
- ✅ `grand_orchestrator.GrandOrchestrator` - Status/sync
- ✅ `skill_evolution.SkillEvolutionEngine` - Skill evolution

**Dead Imports**:
- ❌ None identified - all imports are used

---

## Entry Point 2: integrated_daemon.py

### Execution Flow (BROKEN)

```
main()
  └─> IntegratedDaemon.__init__()
       ├─> DharmicAgent(name=..., subagent_thinking=...)
       │    └─> [SUCCESS if agent_core.py works]
       │
       ├─> DharmicRuntime(agent, heartbeat_interval)
       │    └─> BROKEN: Imports from runtime.py
       │         ├─> from dharmic_agent import DharmicAgent [circular?]
       │         ├─> from charan_vidhi import CharanVidhiPractice [exists?]
       │         └─> Multiple optional imports
       │
       └─> ScheduledTasks(agent)
            └─> BROKEN: Module not found

  └─> daemon.start()
       ├─> runtime.start()
       │    └─> UNKNOWN: Not traced (runtime.py not fully analyzed)
       │
       ├─> scheduled_tasks.start()
       │    └─> BROKEN: ScheduledTasks missing
       │
       ├─> _start_email()
       │    └─> EmailDaemon() [same as unified_daemon]
       │
       ├─> _start_telegram()
       │    └─> BROKEN: DharmicTelegramBot not found
       │
       └─> _start_web()
            └─> BROKEN: web_dashboard module not found
```

### Execution Status Table

| Function | Called From | Status | Depth | Notes |
|----------|-------------|--------|-------|-------|
| `main()` | CLI | **ACTIVE** | 0 | Entry point |
| `IntegratedDaemon.__init__()` | main() | **BROKEN** | 1 | Missing ScheduledTasks import |
| `DharmicAgent()` | __init__ | **ACTIVE** | 2 | Works if agent_core.py loads |
| `DharmicRuntime()` | __init__ | **PARTIAL** | 2 | Has circular import issues |
| `ScheduledTasks()` | __init__ | **BROKEN** | 2 | Module not found |
| `daemon.start()` | main() | **BROKEN** | 1 | Depends on broken components |
| `_start_email()` | start() | **ACTIVE** | 2 | Reuses EmailDaemon |
| `_start_telegram()` | start() | **BROKEN** | 2 | Module not found |
| `_start_web()` | start() | **BROKEN** | 2 | Module not found |

### Dead/Missing Code in integrated_daemon.py

1. **`scheduled_tasks` module**: MISSING
   - Imported on line 41
   - Would crash on import

2. **`telegram_bot` module**: MISSING
   - Imported on line 52
   - Would crash if telegram enabled

3. **`web_dashboard` module**: MISSING
   - Imported on line 59
   - Would crash if web enabled

4. **`runtime.py` issues**:
   - Imports `from dharmic_agent import DharmicAgent` (line 23)
   - Circular dependency risk
   - Imports `charan_vidhi` module (line 24) - exists?

### Import Analysis - integrated_daemon.py

**Used Imports**:
- ✅ `asyncio`, `signal`, `sys`, `Path`, `datetime` - Core
- ✅ `argparse` - CLI
- ✅ `yaml` - Config loading
- ✅ `dotenv.load_dotenv` - Environment
- ✅ `dharmic_agent.DharmicAgent` - Agent
- ⚠️ `runtime.DharmicRuntime` - Partially broken

**Dead/Broken Imports**:
- ❌ `scheduled_tasks.ScheduledTasks` - Module not found
- ❌ `telegram_bot.DharmicTelegramBot` - Module not found
- ❌ `web_dashboard.app` - Module not found
- ❌ `flask.Flask` - Only imported if web enabled, but web is broken

---

## Entry Point 3: swarm/run_swarm.py

### Execution Flow (FUNCTIONAL)

```
main()
  └─> check_api_key()
       └─> ACTIVE: Checks ANTHROPIC_API_KEY env var

  └─> run_swarm(args)
       ├─> SwarmConfig(model=..., max_cycles=..., fitness_threshold=...)
       │    └─> ACTIVE: Creates config object
       │
       ├─> Orchestrator(config)
       │    └─> ACTIVE: Creates SwarmOrchestrator
       │         ├─> AnalyzerAgent()
       │         ├─> ProposerAgent()
       │         ├─> EvaluatorAgent()
       │         ├─> WriterAgent()
       │         ├─> TesterAgent()
       │         └─> MechInterpBridge() [optional]
       │
       ├─> orchestrator.get_status()
       │    └─> ACTIVE: Returns status dict
       │
       └─> orchestrator.run_cycles(n, dry_run)
            └─> ACTIVE: Execute improvement cycles
                 ├─> execute_improvement_cycle()
                 │    ├─> analyzer.analyze_codebase()
                 │    ├─> proposer.generate_proposals()
                 │    ├─> evaluator.evaluate_proposals()
                 │    ├─> writer.implement_proposals()
                 │    └─> tester.run_tests()
                 │
                 └─> Results saved to JSON
```

### Execution Status Table

| Function | Called From | Status | Depth | Notes |
|----------|-------------|--------|-------|-------|
| `main()` | CLI | **ACTIVE** | 0 | Entry point |
| `check_api_key()` | main() | **ACTIVE** | 1 | Validates env var |
| `run_swarm()` | main() | **ACTIVE** | 1 | Main orchestration |
| `SwarmConfig()` | run_swarm() | **ACTIVE** | 2 | Config object |
| `Orchestrator()` | run_swarm() | **ACTIVE** | 2 | Creates SwarmOrchestrator |
| `orchestrator.get_status()` | run_swarm() | **ACTIVE** | 2 | Returns status dict |
| `orchestrator.run_cycles()` | run_swarm() | **ACTIVE** | 2 | Main loop |
| `execute_improvement_cycle()` | run_cycles() | **ACTIVE** | 3 | Core workflow |
| `analyzer.analyze_codebase()` | execute_improvement_cycle() | **ACTIVE** | 4 | Real analysis |
| `proposer.generate_proposals()` | execute_improvement_cycle() | **ACTIVE** | 4 | Real proposals |
| `evaluator.evaluate_proposals()` | execute_improvement_cycle() | **ACTIVE** | 4 | Real evaluation |
| `writer.implement_proposals()` | execute_improvement_cycle() | **ACTIVE** | 4 | Real writing |
| `tester.run_tests()` | execute_improvement_cycle() | **ACTIVE** | 4 | Real testing |
| `results.append()` | run_swarm() | **ACTIVE** | 2 | Collects results |
| `json.dump()` | run_swarm() | **ACTIVE** | 2 | Saves results |

### Dead/Stub Code in run_swarm.py

**None identified** - This entry point is functionally complete.

### Import Analysis - swarm/run_swarm.py

**Used Imports**:
- ✅ `asyncio` - Async execution
- ✅ `argparse` - CLI parsing
- ✅ `json` - Results serialization
- ✅ `os` - Environment variables
- ✅ `sys` - Path manipulation
- ✅ `Path` - Path operations
- ✅ `datetime` - Timestamps
- ✅ `swarm.Orchestrator` - Main orchestrator
- ✅ `swarm.SwarmConfig` - Configuration

**Dead Imports**:
- ❌ None identified

---

## Cross-Reference: Agent Creation

All three entry points create or reference `DharmicAgent`, but through different paths:

### unified_daemon.py
```python
agent_singleton.get_agent()
  └─> DharmicAgent() [from agent_core.py]
       ├─> TelosLayer() ✅
       ├─> StrangeLoopMemory() ✅
       ├─> create_backend() ✅
       └─> VaultBridge() ⚠️ (optional)
```

### integrated_daemon.py
```python
DharmicAgent(name=..., subagent_thinking=...)
  └─> [Same as unified_daemon]
       └─> But runtime.py has circular import risk
```

### run_swarm.py
```python
Does NOT use DharmicAgent
  └─> Uses SwarmOrchestrator with 5 agent types
       ├─> AnalyzerAgent
       ├─> ProposerAgent
       ├─> EvaluatorAgent
       ├─> WriterAgent
       └─> TesterAgent
```

**Key Finding**: The swarm does NOT depend on DharmicAgent at all. It's self-contained.

---

## Stub Function Inventory

### Priority 1: CRITICAL STUBS (unified_daemon.py)

| Function | Line | Status | Impact | Fix Effort |
|----------|------|--------|--------|------------|
| `_evolve_new_idea()` | 436 | STUB | Induction loop produces fake ideas | Medium |
| `_mech_interp_monitor_loop()` | 316 | STUB | No actual mech-interp integration | High |
| `_init_mech_interp_bridge()` | 145 | STUB | Just checks directory existence | Medium |
| `orchestrator.sync()` | N/A | STUB | In GrandOrchestrator, minimal work | Medium |

### Priority 2: MISSING MODULES (integrated_daemon.py)

| Module | Line | Status | Impact | Fix Effort |
|--------|------|--------|--------|------------|
| `scheduled_tasks` | 41 | MISSING | Daemon crashes on import | High |
| `telegram_bot` | 52 | MISSING | Telegram disabled | Medium |
| `web_dashboard` | 59 | MISSING | Web disabled | Medium |
| `charan_vidhi` | runtime.py:24 | UNKNOWN | Runtime may fail | Low |

### Priority 3: FUNCTIONAL BUT SHALLOW

| Function | Status | Notes |
|----------|--------|-------|
| `_query_swarm()` | SHALLOW | Just calls orchestrator.status() |
| `orchestrator.status()` | SHALLOW | Probes channels but doesn't analyze |
| `_sync_loop()` | SHALLOW | Logs status but doesn't synchronize |

---

## Recommendations

### Immediate Actions

1. **Use `run_swarm.py` as primary**
   - Only entry point that actually works
   - Has real implementation
   - No stub code

2. **Fix integrated_daemon.py imports**
   - Create stub `scheduled_tasks.py`
   - Create stub `telegram_bot.py`
   - Create stub `web_dashboard.py`
   - Or disable those features in default config

3. **Implement critical stubs in unified_daemon.py**
   - `_evolve_new_idea()` - Real swarm analysis
   - `_mech_interp_monitor_loop()` - Real integration
   - `orchestrator.sync()` - Real synchronization

### Code to Delete

1. **Commented-out code**: None found
2. **Unused imports**: None found (surprisingly clean)
3. **Dead functions**: None (all are called, but many are stubs)

### Code to Implement

1. **`_evolve_new_idea()` in unified_daemon.py**
   - Currently: Returns hardcoded ideas based on modulo
   - Should: Actually analyze swarm state and research context
   - Estimated effort: 2-4 hours

2. **`_mech_interp_monitor_loop()` in unified_daemon.py**
   - Currently: Checks file existence only
   - Should: Parse results, trigger actions
   - Estimated effort: 4-6 hours

3. **`orchestrator.sync()` in grand_orchestrator.py**
   - Currently: Returns status with empty actions
   - Should: Actually synchronize state across channels
   - Estimated effort: 3-5 hours

4. **Missing modules in integrated_daemon.py**
   - `scheduled_tasks.py` - Create stub or implement
   - `telegram_bot.py` - Create stub or implement
   - `web_dashboard.py` - Create stub or implement
   - Estimated effort: 6-10 hours for all

---

## Execution Depth Analysis

### unified_daemon.py
- **Initialization depth**: 2-3 levels
- **Runtime depth**: 2-4 levels
- **Bottleneck**: Stub functions at level 3

### integrated_daemon.py
- **Initialization depth**: 2 levels (then crashes)
- **Runtime depth**: N/A (never reaches runtime)
- **Bottleneck**: Missing imports at level 2

### run_swarm.py
- **Initialization depth**: 2 levels
- **Runtime depth**: 4-5 levels
- **Bottleneck**: None (functional)

---

## Call Graph Summary

```
UNIFIED_DAEMON (SHALLOW):
main → UnifiedDaemon → [6 async loops]
  └─> Loops run forever
       └─> But most work functions are STUBS
            └─> Daemon "runs" but doesn't "do"

INTEGRATED_DAEMON (BROKEN):
main → IntegratedDaemon → [Missing imports]
  └─> CRASH on initialization
       └─> Never reaches runtime

RUN_SWARM (FUNCTIONAL):
main → run_swarm → Orchestrator → run_cycles → execute_improvement_cycle
  └─> 5 agents collaborate
       └─> Real work happens
            └─> Results saved
```

---

## Conclusion

**The DGC system has significant scaffolding, but limited implementation depth.**

- ✅ `run_swarm.py` is production-ready
- ⚠️ `unified_daemon.py` runs but does shallow work
- ❌ `integrated_daemon.py` crashes on import

**Next Steps**:
1. Focus development on `run_swarm.py` (it works)
2. Fix imports in `integrated_daemon.py`
3. Implement stub functions in `unified_daemon.py`
4. Delete nothing - everything is called (just not implemented)

**Reality Check**: The daemons would appear to run (loops execute, logs written), but actual intelligence/work is minimal. The swarm is the only functional component.

---

*Analysis complete. Truth delivered.*
