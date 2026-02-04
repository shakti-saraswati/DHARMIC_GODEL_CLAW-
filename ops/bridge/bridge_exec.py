#!/usr/bin/env python3
"""
Direct OpenClaw → Codex exec bridge (best-effort).

Claims a task, builds a prompt, runs Codex CLI, and writes a response.

Fixed based on team review:
- Uses temp file instead of stdin (Codex doesn't read stdin)
- Added timeout (300s default)
- Added placeholder support in CODEX_CMD
- Added output validation
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from bridge_queue import claim_task, respond_task, _report_path, init_dirs

BASE_DIR = Path(__file__).resolve().parent


def _build_prompt(task: dict) -> str:
    return f"""# Codex Task

## Task
{task.get("task", "")}

## Scope
{", ".join(task.get("scope", []) or [])}

## Constraints
{", ".join(task.get("constraints", []) or [])}

## Expected Output
{", ".join(task.get("output", []) or [])}

## Payload
{json.dumps(task.get("payload", {}), indent=2)}
"""


def run_codex(prompt: str, out_path: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    """
    Run Codex CLI with the given prompt.
    
    Writes prompt to a temp file and passes it as an argument.
    CODEX_CMD can include placeholders:
      {prompt_file} - path to temp file containing prompt
      {out_file}    - path to output file
    
    If no placeholders, prompt is passed as final argument.
    """
    codex_cmd = os.getenv("CODEX_CMD", "codex").strip()
    
    # Pre-flight check: verify command exists
    cmd_name = shlex.split(codex_cmd)[0]
    if not shutil.which(cmd_name):
        raise FileNotFoundError(f"Command not found: {cmd_name}")
    
    # Write prompt to temp file for reliable handoff
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name
    
    try:
        # Support placeholders in CODEX_CMD
        if '{prompt_file}' in codex_cmd or '{out_file}' in codex_cmd:
            codex_cmd = codex_cmd.format(
                prompt_file=prompt_file,
                out_file=str(out_path),
            )
            cmd = shlex.split(codex_cmd)
        else:
            # Default: pass prompt file as last argument
            cmd = shlex.split(codex_cmd) + [prompt_file]
        
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    finally:
        # Clean up temp file
        Path(prompt_file).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Direct OpenClaw → Codex exec bridge")
    parser.add_argument("--id", dest="task_id", default=None, help="Task ID (optional)")
    parser.add_argument("--by", dest="claimed_by", default="openclaw")
    parser.add_argument("--dry-run", action="store_true", help="Write prompt only, skip codex")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")
    args = parser.parse_args()

    init_dirs()
    task = claim_task(task_id=args.task_id, claimed_by=args.claimed_by)
    if not task:
        print("No task to claim")
        return 1

    prompt = _build_prompt(task)
    prompt_path = _report_path(task["id"], ext="prompt.md")
    report_path = _report_path(task["id"])
    prompt_path.write_text(prompt)

    if args.dry_run:
        respond_task(
            task_id=task["id"],
            status="needs_run",
            summary="Prompt written; codex not executed",
            report_path=str(prompt_path),
        )
        print(f"Prompt written to {prompt_path}")
        return 0

    try:
        result = run_codex(prompt, report_path, timeout=args.timeout)
        
        # Validate output
        if not result.stdout.strip():
            respond_task(
                task_id=task["id"],
                status="error",
                summary="Empty output from Codex",
                report_path=str(report_path),
                error="Codex produced no output",
            )
            return 1
        
        report_path.write_text(result.stdout)
        
        if result.returncode != 0:
            respond_task(
                task_id=task["id"],
                status="error",
                summary="Codex execution failed",
                report_path=str(report_path),
                error=result.stderr.strip(),
            )
            return result.returncode
        
        respond_task(
            task_id=task["id"],
            status="done",
            summary="Codex execution complete",
            report_path=str(report_path),
        )
        return 0
        
    except FileNotFoundError as exc:
        respond_task(
            task_id=task["id"],
            status="error",
            summary="Codex command not found",
            report_path=str(report_path),
            error=str(exc),
        )
        return 1
    except subprocess.TimeoutExpired:
        respond_task(
            task_id=task["id"],
            status="error",
            summary=f"Codex timed out after {args.timeout}s",
            report_path=str(report_path),
            error="Process killed due to timeout",
        )
        return 1
    except Exception as exc:
        respond_task(
            task_id=task["id"],
            status="error",
            summary="Codex execution exception",
            report_path=str(report_path),
            error=str(exc),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
