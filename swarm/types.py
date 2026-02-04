"""Shared types for the DHARMIC GODEL CLAW swarm."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


@dataclass
class Proposal:
    """A proposal for code improvement."""
    id: str
    description: str
    type: str = "improvement"  # "optimization", "feature", "fix", "improvement"
    target_files: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    estimated_impact: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of evaluating a proposal."""
    proposal_id: str
    approved: bool
    safety_score: float
    impact_score: float
    feasibility_score: float
    overall_score: float
    reasoning: str
    timestamp: datetime


@dataclass
class Agent:
    """Base agent representation."""
    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    active: bool = True


@dataclass
class FileChange:
    """Represents a change to a file."""
    path: str
    action: str  # "create", "modify", "delete"
    content: Optional[str] = None
    diff: Optional[str] = None


@dataclass
class TestResult:
    """Result of running tests."""
    passed: bool
    tests_run: int
    tests_passed: int
    tests_failed: int
    failures: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class CycleMetrics:
    """Metrics from a single improvement cycle."""
    cycle_number: int
    start_time: datetime
    end_time: datetime
    proposals_generated: int
    proposals_approved: int
    files_changed: int
    tests_passed: bool
    fitness_before: float
    fitness_after: float
