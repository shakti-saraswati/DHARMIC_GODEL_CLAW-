#!/usr/bin/env python3
"""
Systemic risk monitoring for multi-agent coordination.

Reads interaction events and computes network-level risk metrics:
- coordination density
- centralization
- reciprocity
- burst rate

Designed as a scaffold for deeper monitoring.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

POLICY_PATH = Path(__file__).parent / "policy" / "systemic_risk.yaml"


@dataclass
class InteractionEvent:
    ts: float
    sender: str
    recipient: str
    event_type: str = "message"
    size: int = 0


@dataclass
class SystemicRiskMetrics:
    agents: int
    edges: int
    density: float
    centralization: float
    reciprocity: float
    burst_rate_per_min: float


@dataclass
class SystemicRiskReport:
    metrics: SystemicRiskMetrics
    flags: List[str]
    status: str


def _normalize_event(data: dict) -> Optional[InteractionEvent]:
    """Normalize multiple event schemas (DGC, OACP, generic)."""
    sender = data.get("sender") or data.get("from") or data.get("agent_id")
    recipient = data.get("recipient") or data.get("to") or data.get("target")
    if not sender or not recipient:
        return None
    event_type = data.get("event_type") or data.get("event") or data.get("type") or "message"
    size = data.get("size", 0)
    ts = data.get("ts") or data.get("timestamp") or data.get("time") or 0.0
    return InteractionEvent(
        ts=float(ts),
        sender=str(sender),
        recipient=str(recipient),
        event_type=str(event_type),
        size=int(size) if str(size).isdigit() else 0,
    )


def load_events(path: Path) -> List[InteractionEvent]:
    """Public loader for interaction events (JSONL)."""
    events: List[InteractionEvent] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        event = _normalize_event(data)
        if event:
            events.append(event)
    return events


def _compute_metrics(events: Iterable[InteractionEvent]) -> SystemicRiskMetrics:
    events = list(events)
    agents = set()
    edges = set()
    degrees: Dict[str, int] = {}
    reciprocity_pairs = set()

    for ev in events:
        agents.add(ev.sender)
        agents.add(ev.recipient)
        edge = (ev.sender, ev.recipient)
        edges.add(edge)
        degrees[ev.sender] = degrees.get(ev.sender, 0) + 1
        degrees[ev.recipient] = degrees.get(ev.recipient, 0) + 1
        if (ev.recipient, ev.sender) in edges:
            reciprocity_pairs.add(tuple(sorted(edge)))

    agent_count = len(agents)
    edge_count = len(edges)
    max_edges = agent_count * (agent_count - 1) if agent_count > 1 else 1
    density = edge_count / max_edges if max_edges > 0 else 0.0

    max_degree = max(degrees.values(), default=0)
    centralization = max_degree / (agent_count - 1) if agent_count > 1 else 0.0

    reciprocity = 0.0
    if edge_count > 0:
        reciprocity = len(reciprocity_pairs) * 2 / edge_count

    burst_rate = 0.0
    if events:
        buckets: Dict[int, int] = {}
        for ev in events:
            bucket = int(ev.ts // 60)
            buckets[bucket] = buckets.get(bucket, 0) + 1
        burst_rate = max(buckets.values()) if buckets else 0.0

    return SystemicRiskMetrics(
        agents=agent_count,
        edges=edge_count,
        density=density,
        centralization=centralization,
        reciprocity=reciprocity,
        burst_rate_per_min=burst_rate,
    )


def load_policy(path: Optional[Path] = None) -> dict:
    """Load systemic risk policy from path or default."""
    if path and path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return yaml.safe_load(POLICY_PATH.read_text()) if POLICY_PATH.exists() else {}


def evaluate(events: Iterable[InteractionEvent], policy: Optional[dict] = None) -> SystemicRiskReport:
    policy = policy or {}
    thresholds = policy.get("thresholds", {})
    metrics = _compute_metrics(events)
    flags: List[str] = []

    if metrics.density > thresholds.get("max_density", 0.6):
        flags.append(f"density_high:{metrics.density:.2f}")
    if metrics.centralization > thresholds.get("max_centralization", 0.7):
        flags.append(f"centralization_high:{metrics.centralization:.2f}")
    if metrics.reciprocity > thresholds.get("max_reciprocity", 0.9):
        flags.append(f"reciprocity_high:{metrics.reciprocity:.2f}")
    if metrics.burst_rate_per_min > thresholds.get("max_burst_rate_per_min", 200):
        flags.append(f"burst_high:{metrics.burst_rate_per_min:.0f}")

    status = "stable" if not flags else "unstable"
    return SystemicRiskReport(metrics=metrics, flags=flags, status=status)


def main() -> None:
    parser = argparse.ArgumentParser(description="Systemic risk monitor")
    parser.add_argument("--events", required=True, help="Path to JSONL interaction events")
    parser.add_argument("--policy", help="Path to systemic risk policy YAML")
    parser.add_argument("--output", help="Write report JSON to file")
    args = parser.parse_args()

    events = load_events(Path(args.events))
    policy = load_policy(Path(args.policy)) if args.policy else load_policy(None)
    report = evaluate(events, policy)

    output = json.dumps({"metrics": asdict(report.metrics), "flags": report.flags, "status": report.status}, indent=2)
    if args.output:
        Path(args.output).write_text(output)
    print(output)


if __name__ == "__main__":
    main()
