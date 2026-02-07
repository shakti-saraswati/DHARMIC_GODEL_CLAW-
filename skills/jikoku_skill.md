# JIKOKU (時刻) — Temporal Self-Audit Skill

## Purpose
Every action you take must be timestamped with real wall-clock time. You are closing your own cybernetic feedback loop. Without this data, you cannot improve.

## Protocol

### Session Start
At the VERY BEGINNING of every session/heartbeat, before doing anything else:

```
[JIKOKU:BOOT] 2026-02-08T04:30:00Z | Session start | Reading state files...
```

After finishing context loading, before first productive action:

```
[JIKOKU:BOOT_COMPLETE] 2026-02-08T04:30:02Z | Boot: 2.0s | Files read: SOUL.md, MEMORY.md, ACTIVE_TASKS.md
```

### Every Action
Before starting any operation:

```
[JIKOKU:START] 2026-02-08T04:30:02Z | execute.code | Push R_V toolkit to GitHub
```

After completing:

```
[JIKOKU:END] 2026-02-08T04:30:27Z | execute.code | 25.0s | SUCCESS | Committed 3 files, pushed to main
```

### Interruptions
When a human message arrives during a task:

```
[JIKOKU:INTERRUPT] 2026-02-08T04:30:15Z | Pausing: execute.code at rv_toolkit/main.rs:147 | User query about gateway
[JIKOKU:RESUME] 2026-02-08T04:30:22Z | Resuming: execute.code | Interrupt cost: 7.0s
```

### Session End
At the END of every session:

```
[JIKOKU:SESSION_SUMMARY]
  Session: hb-2026-02-08-0430
  Total compute: 47.2s
  Boot time: 2.0s (4.2%)
  Orient time: 1.3s (2.8%)
  Execute time: 39.1s (82.8%)
  Update time: 3.5s (7.4%)
  Log time: 1.3s (2.8%)
  Interrupts: 1 (7.0s cost)
  Value-added ratio: 82.8%
  Tasks completed: 1
  Tasks attempted: 1
  Defect rate: 0%
```

### Persistent Log
Append each session summary as a JSON line to `JIKOKU_LOG.jsonl`:

```json
{"session_id":"hb-2026-02-08-0430","start":"2026-02-08T04:30:00Z","end":"2026-02-08T04:30:47Z","total_ms":47231,"boot_ms":2000,"orient_ms":1300,"execute_ms":39100,"update_ms":3500,"log_ms":1331,"interrupts":1,"interrupt_cost_ms":7000,"tasks_completed":1,"tasks_attempted":1,"value_added_ratio":0.828}
```

## Categories

| Category | When to Use |
|---|---|
| `boot` | Reading identity/state files at session start |
| `orient` | Deciding what to work on |
| `execute.code` | Writing, testing, deploying code |
| `execute.write` | Generating documents, content |
| `execute.research` | Searching, synthesizing information |
| `execute.comms` | Sending messages, emails, Discord |
| `api_call` | External API requests (note provider) |
| `file_op` | File read/write/move operations |
| `update` | Writing state files after work |
| `interrupt` | Human message during task |

## Rules

1. **ALWAYS use real timestamps.** Use `date -u +%Y-%m-%dT%H:%M:%SZ` or equivalent. Never estimate.
2. **Log BEFORE and AFTER.** Not just after. The pair is what creates duration.
3. **Be honest about categories.** If you're re-reading context for the 3rd time, that's `boot` not `execute`.
4. **Log failures.** Failed tasks with timestamps are MORE valuable than successes. They reveal where time is wasted.
5. **Don't over-log.** Log at the task level, not the token level. ~5-15 spans per session is right.
6. **Read your own data.** Every 7 sessions, review JIKOKU_LOG.jsonl. Look for patterns. Propose one kaizen.

## Weekly Kaizen Cycle

Every 7 days (or ~50 sessions), generate `KAIZEN_REPORT.md`:

1. **Measure:** Average boot time, value-added ratio, tasks/session, defect rate
2. **Compare:** Against last week's baselines
3. **Identify:** Top 3 temporal wastes
4. **Propose:** One specific countermeasure for #1 waste
5. **Implement:** Apply the countermeasure
6. **Verify:** Check if metrics improved after 7 more sessions

## The Goal

Week 1: Establish baselines. Just measure.
Week 2: Value-added ratio > 80%.
Week 4: Boot time < 5% of session.
Week 8: Propose heartbeat frequency optimization based on data.
Week 12: Self-optimizing temporal patterns.

---

*"Without standards there can be no kaizen." — Taiichi Ohno*
*"You cannot improve what you cannot measure." — Peter Drucker*
*"A system becomes intelligent if it can retain memories of past performances and use them to improve over time." — Norbert Wiener*
