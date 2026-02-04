---
name: dgc-bridge
description: Enqueue tasks for Codex CLI via the DGC bridge (file queue or local HTTP).
metadata: { "openclaw": { "emoji": "🔁", "requires": { "bins": ["python3"] } } }
---

# DGC Bridge

Use this skill to queue tasks for Codex CLI via the local DGC bridge.

## File Queue (recommended)

```bash
python3 ~/DHARMIC_GODEL_CLAW/ops/bridge/bridge_queue.py enqueue \
  --task "Describe the task clearly" \
  --from "openclaw" \
  --scope "src/core,analysis" \
  --output "report,patch_optional" \
  --constraints "read_only,cite_paths"
```

## Local HTTP (optional)

```bash
curl -s http://127.0.0.1:5056/enqueue \
  -H "Content-Type: application/json" \
  -H "X-Bridge-Token: $DGC_BRIDGE_TOKEN" \
  -d '{"task":"Audit DGM integration gaps","scope":["src/core","analysis"]}'
```

## Direct Exec (best-effort)

```bash
CODEX_CMD="codex" python3 ~/DHARMIC_GODEL_CLAW/ops/bridge/bridge_exec.py --dry-run
```

Remove `--dry-run` to run Codex CLI for a claimed task.
