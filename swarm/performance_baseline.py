#!/usr/bin/env python3
from __future__ import annotations
"""
Performance Baseline Manager

Creates and manages benchmark baselines for the PERFORMANCE_REGRESSION gate.

Usage:
  python -m swarm.performance_baseline --update
  python -m swarm.performance_baseline --show
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

GATES_CONFIG = Path(__file__).parent / "gates.yaml"
REPO_ROOT = Path(__file__).parent.parent


def _load_baseline_path() -> Path:
    config = yaml.safe_load(GATES_CONFIG.read_text())
    for gate in config.get("gates", []):
        if gate.get("name") == "PERFORMANCE_REGRESSION":
            baseline = gate.get("baseline_path", "benchmarks/baseline.json")
            return REPO_ROOT / baseline
    return REPO_ROOT / "benchmarks/baseline.json"


def _load_benchmark_json() -> dict:
    bench_path = REPO_ROOT / "benchmark.json"
    if not bench_path.exists():
        raise FileNotFoundError("benchmark.json not found. Run benchmarks first.")
    return json.loads(bench_path.read_text())


def update_baseline() -> Path:
    baseline_path = _load_baseline_path()
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    bench = _load_benchmark_json()
    baseline = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "benchmark.json",
        "benchmarks": bench.get("benchmarks", [])
    }
    baseline_path.write_text(json.dumps(baseline, indent=2))
    return baseline_path


def show_baseline() -> None:
    baseline_path = _load_baseline_path()
    if not baseline_path.exists():
        print(f"No baseline found at {baseline_path}")
        return
    print(baseline_path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark baseline manager")
    parser.add_argument("--update", action="store_true", help="Update baseline from benchmark.json")
    parser.add_argument("--show", action="store_true", help="Show current baseline")
    args = parser.parse_args()

    if args.update:
        path = update_baseline()
        print(f"✓ Baseline updated: {path}")
        return

    if args.show:
        show_baseline()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
