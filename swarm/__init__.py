from __future__ import annotations
"""
DHARMIC GODEL CLAW - Self-Improving Agent Swarm

A self-improving agent swarm with dharmic alignment constraints,
combining Darwin-Gödel Machine patterns with Akram Vignan ethics.

Components:
- Orchestrator: Coordinates the improvement loop
- ResidualStream: Tracks evolution history and fitness
- Agents: Specialized agents for each phase (Proposer, Writer, Tester, Refiner, Evolver, DharmicGate)

Usage:
    from swarm import Orchestrator, SwarmConfig

    config = SwarmConfig()
    orchestrator = Orchestrator(config)
    results = await orchestrator.run_cycles(n=3, dry_run=True)
"""

from .config import SwarmConfig, SwarmState, AgentConfig
from .residual_stream import ResidualStream, FitnessScore, EvolutionEntry
from .orchestrator import Orchestrator, CycleResult

__all__ = [
    "SwarmConfig",
    "SwarmState",
    "AgentConfig",
    "ResidualStream",
    "FitnessScore",
    "EvolutionEntry",
    "Orchestrator",
    "CycleResult"
]

__version__ = "0.1.0"
