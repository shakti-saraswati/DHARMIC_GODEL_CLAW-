# OpenClaw ↔ Codex CLI Bridge

Three collaboration modes are supported:

1) **File Queue** (recommended, no network)
2) **Local HTTP** (near‑realtime)
3) **Direct Exec** (OpenClaw calls Codex CLI)

## 1) File Queue (recommended)

Initialize:

```bash
python3 ops/bridge/bridge_queue.py init
```

Enqueue a task:

```bash
python3 ops/bridge/bridge_queue.py enqueue \
  --task "Audit DGM integration gaps in DGC" \
  --from "openclaw" \
  --scope "src/core,analysis" \
  --output "report" \
  --constraints "read_only,cite_paths"
```

Claim + work (Codex):

```bash
python3 ops/bridge/bridge_queue.py claim
```

Respond:

```bash
python3 ops/bridge/bridge_queue.py respond \
  --id <task_id> \
  --status done \
  --summary "Report complete" \
  --report-path "ops/bridge/outbox/<task_id>.md"
```

## 2) Local HTTP Bridge

Start server (localhost only):

```bash
DGC_BRIDGE_TOKEN="change-me" python3 ops/bridge/bridge_server.py
```

Endpoints:
- `GET /health`
- `GET /pending`
- `POST /enqueue`
- `POST /claim`
- `POST /respond`

Token can be passed via header `X-Bridge-Token` or `?token=`.

## 3) Direct Exec (OpenClaw → Codex CLI)

This is best‑effort because Codex CLI flags vary. You can control the command:

```bash
export CODEX_CMD="codex"  # or full path + args
python3 ops/bridge/bridge_exec.py --dry-run
```

`--dry-run` writes a prompt to:
`ops/bridge/outbox/<task_id>.prompt.md`

Remove `--dry-run` to execute Codex CLI and write results to:
`ops/bridge/outbox/<task_id>.md`

## OpenClaw Skill (optional)

Add `skills/dgc-bridge/` to your OpenClaw skills path or copy to:
`~/.openclaw/skills/dgc-bridge/`

Then use the skill to enqueue tasks using the file queue.
