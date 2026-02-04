#!/usr/bin/env python3
"""
Swarm CLI - Run the DGC self-evolution loop.

This is the entrypoint used by `dgc2 /evolve`.
Defaults to dry-run; set DGC_ALLOW_LIVE=1 or pass --live to enable writes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repo root is on sys.path when invoked as a script
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from swarm.config import SwarmConfig
from swarm.orchestrator import SwarmOrchestrator


def _resolve_target(target: Optional[str]) -> Optional[str]:
    if not target:
        return None
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return str(path)


async def _run_cycles(
    orchestrator: SwarmOrchestrator,
    cycles: int,
    dry_run: bool,
    target: Optional[str],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for i in range(cycles):
        if dry_run:
            analysis = await orchestrator.analyzer.analyze_codebase(target)
            issues_found = len(analysis.issues) if analysis else 0
            results.append({
                "cycle": i + 1,
                "result": "dry-run",
                "files_changed": [],
                "tests_passed": True,
                "metrics": {
                    "issues_found": issues_found,
                    "dry_run": True,
                    "target": target,
                },
                "fitness": 0.5,
                "evolution_id": None,
            })
        else:
            workflow = await orchestrator.execute_improvement_cycle(target_area=target)
            results.append({
                "cycle": i + 1,
                "result": workflow.state.value,
                "files_changed": workflow.files_changed,
                "tests_passed": workflow.tests_passed,
                "metrics": workflow.metrics or {},
                "fitness": (workflow.metrics or {}).get("evaluation_score", 0.0),
                "evolution_id": workflow.evolution_id,
            })
            if workflow.state.value == "failed":
                break
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DGC swarm evolution loop")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run")
    parser.add_argument("--target", type=str, default=None, help="Target file or directory")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run only (default)")
    parser.add_argument("--live", action="store_true", help="Apply changes (requires DGC_ALLOW_LIVE=1)")
    parser.add_argument("--status", action="store_true", help="Print orchestrator status and exit")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if args.live and os.getenv("DGC_ALLOW_LIVE") != "1":
        print("Live evolution blocked. Set DGC_ALLOW_LIVE=1 to enable.")
        raise SystemExit(2)

    dry_run = True
    if args.live:
        dry_run = False
    elif args.dry_run:
        dry_run = True

    target = _resolve_target(args.target)

    orchestrator = SwarmOrchestrator(SwarmConfig())

    if args.status:
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2))
        return

    results = asyncio.run(_run_cycles(orchestrator, args.cycles, dry_run, target))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"Cycle {result['cycle']}: {result['result']} | files: {len(result['files_changed'])}")


if __name__ == "__main__":
    main()
