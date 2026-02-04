#!/usr/bin/env python3
"""
Cybernetics Control Loop Utilities

Evaluates production metrics against setpoints to provide
stable/unstable control signals and feedback for the system.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEFAULT_POLICY = Path(__file__).parent / "policy" / "cybernetics.yaml"


@dataclass
class ControlSignal:
    status: str  # stable | unstable
    evaluated_at: str
    violations: list[str]
    metrics: dict[str, Any]
    setpoints: dict[str, Any]


def evaluate_control(metrics: dict[str, Any], policy_path: Path | None = None) -> ControlSignal:
    policy_file = policy_path or DEFAULT_POLICY
    setpoints = {}
    if policy_file.exists():
        policy = yaml.safe_load(policy_file.read_text()) or {}
        setpoints = policy.get("setpoints", {}) or {}

    violations: list[str] = []
    for key, bounds in setpoints.items():
        value = metrics.get(key)
        if value is None:
            continue
        if "max" in bounds and value > bounds["max"]:
            violations.append(f"{key}={value} > max {bounds['max']}")
        if "min" in bounds and value < bounds["min"]:
            violations.append(f"{key}={value} < min {bounds['min']}")
        if "target" in bounds:
            target = bounds["target"]
            delta = value - target
            tol = bounds.get("tolerance", 0)
            if abs(delta) > tol:
                violations.append(f"{key}={value} != target {target} ±{tol}")

    status = "unstable" if violations else "stable"
    return ControlSignal(
        status=status,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
        violations=violations,
        metrics=metrics,
        setpoints=setpoints
    )


def asdict_signal(signal: ControlSignal) -> dict[str, Any]:
    return asdict(signal)
