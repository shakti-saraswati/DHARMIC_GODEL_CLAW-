# GAP ANALYSIS — DHARMIC FOUNDATION BUILD

## CRITICAL GAPS

### 1. CLAWDBOT CONFIG MISMATCH
**BUILD.md assumes:** Top-level `model` key in clawdbot.json
**ACTUAL CONFIG:** Has `agents.defaults.model.primary` using OpenRouter format `anthropic/claude-opus-4-5`
**BREAK POINT:** Editing per BUILD.md will create duplicate/conflicting model config
**FIX NEEDED:** Update agents.defaults.model.provider, not add new top-level key

### 2. CLAUDE-MAX-API-PROXY AUTHENTICATION MISSING
**BUILD.md assumes:** Proxy works with `apiKey: "not-needed"`
**REALITY:** Package requires Claude CLI authenticated session
**MISSING VALIDATION:** No check that `claude --version` succeeds before proxy start
**BREAK POINT:** Proxy will fail silently if Claude CLI not authenticated

### 3. LAUNCHAGENT PATH HARDCODED
**BUILD.md hardcodes:** `/Users/dhyana/.npm-global/bin/claude-max-api-proxy`
**REALITY:** npm global install location varies (could be /usr/local/bin, /opt/homebrew/bin)
**BREAK POINT:** LaunchAgent won't start if path wrong
**FIX NEEDED:** Detect actual path via `which claude-max-api-proxy`

### 4. SWARM DIRECTORY STRUCTURE WRONG
**BUILD.md reads from:** `~/DHARMIC_GODEL_CLAW/swarm/stream/synthesis_30min.md`
**ACTUAL STRUCTURE:** `/Users/dhyana/DHARMIC_GODEL_CLAW/swarm/stream/` exists
**BUT:** No `synthesis_30min.md` file present
**BREAK POINT:** heartbeat() will generate false alerts for missing file

### 5. CROWN_JEWEL_FORGE DIRECTORY MISSING
**dharmic_agent.py checks:** `DGC_ROOT / "crown_jewel_forge" / "candidates"`
**REALITY:** Directory does not exist
**BREAK POINT:** First heartbeat will crash on `.exists()` or glob()

### 6. WHATSAPP TARGET HARDCODED
**All prompts use:** `+818054961566`
**REALITY:** May be correct but not validated
**MISSING:** No test for WhatsApp plugin actual connectivity before cron setup
**RISK:** Crons schedule successfully but messages never arrive

### 7. SKILL BRIDGE INVOCATION STUB
**skill_bridge.py invoke():** Returns `NOT_IMPLEMENTED`
**BUILD.md treats as:** "Phase 2 complete"
**REALITY:** P0 Bridge #2 is NOT functional, just scaffolding
**CONFUSION:** Success criteria say "implemented" but it's a stub

## PYTHON CODE GAPS

### dharmic_agent.py Issues

**Line 195:** `DGC_ROOT / "core"` — directory must exist or first run crashes
**Line 292:** `STATE_FILE.parent.mkdir()` — creates core/ but could fail on permissions
**Line 428:** `synthesis_path.exists()` — will always trigger alert since file doesn't exist
**Line 440:** `candidates_path.exists()` — will crash glob() if dir doesn't exist

**Missing imports:** `from datetime import datetime, timezone` used before imported at top

**Gate evaluation defaults:** All gates pass by default (too permissive for production)

### skill_bridge.py Issues

**Line 618:** Iterates `SKILLS_ROOT.iterdir()` — no error handling if dir doesn't exist
**Line 621:** `(skill_dir / "SKILL.md").exists()` — assumes all dirs are skill dirs
**Line 636-646:** Parsing SKILL.md with simple string split — will fail on complex formats
**Line 682:** `json.dump()` — no error handling, could corrupt registry on disk full

**Registry sync:** Creates entries but never validates they're loadable by Claude Code

## COMMAND SEQUENCE GAPS

### Phase 1.2 Config Edit
**Instruction:** "Edit ~/.clawdbot/clawdbot.json to add model configuration at TOP LEVEL"
**PROBLEM:** Manual edit, no validation
**BREAK POINT:** Malformed JSON will crash clawdbot
**MISSING:** Backup restore instructions if edit fails

### Phase 2.0 "Read Before Building"
**Lists:** `cat ~/DHARMIC_GODEL_CLAW/swarm/stream/synthesis_30min.md`
**PROBLEM:** File doesn't exist
**Lists:** `ls ~/Persistent-Semantic-Memory-Vault/crown_jewels/`
**PROBLEM:** No validation if dir exists

### Phase 3.3 Cron Jobs
**Assumes:** All clawdbot cron commands succeed
**REALITY:** No error handling if cron add fails
**MISSING:** How to check if cron actually scheduled

## PERMISSION ISSUES

**LaunchAgent bootstrap:** Requires GUI session — will fail in SSH/remote
**agent_state.json writes:** No check for disk space before write
**registry.json updates:** Concurrent access not locked (race condition possible)

## API ASSUMPTIONS

**Clawdbot heartbeat:** Assumes `clawdbot heartbeat --now` exists — not in clawdbot 2026.1.24-3
**Clawdbot gateway restart:** Assumes command exists — not documented in version
**WhatsApp plugin:** Enabled in config but never validated it works

## EDGE CASES

**Empty skills directory:** skill_bridge.py returns 0/0 coverage but no error
**Missing Python 3:** Code assumes `python3` in PATH
**Clock skew:** Heartbeat timing could fail if system clock wrong
**Large state files:** No size limit on strange_loops_observed list (unbounded growth)
**Unicode in observations:** No encoding validation before JSON dump

## CORRECT CONFIG EDIT FOR PHASE 1.2

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "claude-sonnet-4",
        "provider": {
          "type": "openai-compatible",
          "baseURL": "http://localhost:3456/v1",
          "apiKey": "not-needed"
        }
      }
    }
  }
}
```
**NOT** a new top-level key.
