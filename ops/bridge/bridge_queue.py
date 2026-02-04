#!/usr/bin/env python3
"""
Bridge Queue for OpenClaw ↔ Codex CLI

File-based task queue with claim/response lifecycle.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
INBOX_DIR = BASE_DIR / "inbox"
OUTBOX_DIR = BASE_DIR / "outbox"
STATE_DIR = BASE_DIR / "state"
DONE_DIR = STATE_DIR / "done"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_dirs() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)


def _task_path(task_id: str) -> Path:
    return INBOX_DIR / f"{task_id}.json"


def _state_path(task_id: str) -> Path:
    return STATE_DIR / f"{task_id}.json"


def _done_path(task_id: str) -> Path:
    return DONE_DIR / f"{task_id}.json"


def _response_path(task_id: str) -> Path:
    return OUTBOX_DIR / f"{task_id}.json"


def _report_path(task_id: str, ext: str = "md") -> Path:
    return OUTBOX_DIR / f"{task_id}.{ext}"


def _make_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


def enqueue_task(
    task: str,
    sender: str = "openclaw",
    scope: Optional[List[str]] = None,
    output: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    init_dirs()
    task_id = _make_id()
    record = {
        "id": task_id,
        "created_at": _now(),
        "from": sender,
        "task": task,
        "scope": scope or [],
        "output": output or [],
        "constraints": constraints or [],
        "payload": payload or {},
        "status": "queued",
    }
    path = _task_path(task_id)
    path.write_text(json.dumps(record, indent=2))
    return record


def list_pending() -> List[Dict[str, Any]]:
    init_dirs()
    tasks: List[Dict[str, Any]] = []
    for path in sorted(INBOX_DIR.glob("*.json")):
        try:
            tasks.append(json.loads(path.read_text()))
        except Exception:
            tasks.append({"id": path.stem, "error": "unreadable"})
    return tasks


def claim_task(task_id: Optional[str] = None, claimed_by: Optional[str] = None) -> Optional[Dict[str, Any]]:
    init_dirs()
    target: Optional[Path] = None
    if task_id:
        target = _task_path(task_id)
        if not target.exists():
            return None
    else:
        candidates = sorted(INBOX_DIR.glob("*.json"))
        if not candidates:
            return None
        target = candidates[0]

    try:
        state_path = _state_path(target.stem)
        target.rename(state_path)
        record = json.loads(state_path.read_text())
        record["status"] = "in_progress"
        record["claimed_at"] = _now()
        if claimed_by:
            record["claimed_by"] = claimed_by
        state_path.write_text(json.dumps(record, indent=2))
        return record
    except FileNotFoundError:
        return None


def respond_task(
    task_id: str,
    status: str,
    summary: str,
    report_path: Optional[str] = None,
    patch_path: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    init_dirs()
    record = {
        "id": task_id,
        "completed_at": _now(),
        "status": status,
        "summary": summary,
        "report_path": report_path,
        "patch_path": patch_path,
        "error": error,
    }
    _response_path(task_id).write_text(json.dumps(record, indent=2))

    state_path = _state_path(task_id)
    if state_path.exists():
        done = json.loads(state_path.read_text())
        done["status"] = status
        done["completed_at"] = record["completed_at"]
        _done_path(task_id).write_text(json.dumps(done, indent=2))
        state_path.unlink()

    return record


def recover_stale_tasks(timeout_minutes: int = 30) -> List[str]:
    """
    Scan STATE_DIR for tasks older than timeout_minutes and re-queue them.
    
    Args:
        timeout_minutes: Tasks claimed longer than this are considered stale (default 30)
    
    Returns:
        List of recovered task IDs
    """
    init_dirs()
    recovered: List[str] = []
    now = datetime.now(timezone.utc)
    
    for state_path in STATE_DIR.glob("*.json"):
        # Skip the 'done' subdirectory marker if any
        if state_path.is_dir():
            continue
            
        try:
            record = json.loads(state_path.read_text())
            task_id = record.get("id", state_path.stem)
            
            # Check claimed_at timestamp
            claimed_at_str = record.get("claimed_at")
            if not claimed_at_str:
                # No claimed_at means something is wrong, recover it
                age_minutes = timeout_minutes + 1
            else:
                claimed_at = datetime.fromisoformat(claimed_at_str.replace("Z", "+00:00"))
                age_minutes = (now - claimed_at).total_seconds() / 60
            
            if age_minutes > timeout_minutes:
                # Increment retry count
                retry_count = record.get("retry_count", 0) + 1
                record["retry_count"] = retry_count
                record["status"] = "queued"
                record["recovered_at"] = _now()
                record["recovery_reason"] = f"stale after {int(age_minutes)} minutes"
                
                # Remove claim metadata
                record.pop("claimed_at", None)
                record.pop("claimed_by", None)
                
                # Write back to inbox
                inbox_path = _task_path(task_id)
                inbox_path.write_text(json.dumps(record, indent=2))
                
                # Remove from state
                state_path.unlink()
                
                recovered.append(task_id)
                print(f"[RECOVER] {task_id}: retry_count={retry_count}, age={int(age_minutes)}m", file=sys.stderr)
                
        except Exception as e:
            print(f"[RECOVER] Error processing {state_path}: {e}", file=sys.stderr)
            continue
    
    if recovered:
        print(f"[RECOVER] Recovered {len(recovered)} stale task(s)", file=sys.stderr)
    else:
        print("[RECOVER] No stale tasks found", file=sys.stderr)
    
    return recovered


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="OpenClaw ↔ Codex CLI bridge queue")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub_init = sub.add_parser("init", help="Initialize bridge directories")

    sub_enqueue = sub.add_parser("enqueue", help="Enqueue a task")
    sub_enqueue.add_argument("--task", required=True)
    sub_enqueue.add_argument("--from", dest="sender", default="openclaw")
    sub_enqueue.add_argument("--scope", default="")
    sub_enqueue.add_argument("--output", default="")
    sub_enqueue.add_argument("--constraints", default="")
    sub_enqueue.add_argument("--payload", default="")

    sub_list = sub.add_parser("list", help="List pending tasks")

    sub_claim = sub.add_parser("claim", help="Claim a task (first pending by default)")
    sub_claim.add_argument("--id", dest="task_id")
    sub_claim.add_argument("--by", dest="claimed_by", default=None)

    sub_respond = sub.add_parser("respond", help="Respond to a task")
    sub_respond.add_argument("--id", dest="task_id", required=True)
    sub_respond.add_argument("--status", default="done")
    sub_respond.add_argument("--summary", required=True)
    sub_respond.add_argument("--report-path", dest="report_path")
    sub_respond.add_argument("--patch-path", dest="patch_path")
    sub_respond.add_argument("--error", dest="error")

    sub_recover = sub.add_parser("recover", help="Recover stale tasks from state back to inbox")
    sub_recover.add_argument("--timeout", type=int, default=30, help="Minutes before a task is considered stale (default: 30)")

    args = parser.parse_args(argv)

    if args.cmd == "init":
        init_dirs()
        _print_json({"ok": True, "inbox": str(INBOX_DIR), "outbox": str(OUTBOX_DIR)})
        return 0

    if args.cmd == "enqueue":
        scope = [s.strip() for s in args.scope.split(",") if s.strip()]
        output = [s.strip() for s in args.output.split(",") if s.strip()]
        constraints = [s.strip() for s in args.constraints.split(",") if s.strip()]
        payload = json.loads(args.payload) if args.payload else {}
        record = enqueue_task(
            task=args.task,
            sender=args.sender,
            scope=scope,
            output=output,
            constraints=constraints,
            payload=payload,
        )
        _print_json(record)
        return 0

    if args.cmd == "list":
        _print_json(list_pending())
        return 0

    if args.cmd == "claim":
        record = claim_task(task_id=args.task_id, claimed_by=args.claimed_by)
        _print_json(record or {"ok": False, "error": "no_task"})
        return 0

    if args.cmd == "respond":
        record = respond_task(
            task_id=args.task_id,
            status=args.status,
            summary=args.summary,
            report_path=args.report_path,
            patch_path=args.patch_path,
            error=args.error,
        )
        _print_json(record)
        return 0

    if args.cmd == "recover":
        recovered = recover_stale_tasks(timeout_minutes=args.timeout)
        _print_json({"ok": True, "recovered": recovered, "count": len(recovered)})
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
