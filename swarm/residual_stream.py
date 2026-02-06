from __future__ import annotations
"""
DHARMIC GODEL CLAW - Residual Stream
Tracks swarm evolution, fitness history, and provides continuity.
"""

import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import uuid


def atomic_write_json(filepath: Path, data: dict, indent: int = 2):
    """Write JSON atomically: write to temp, then rename."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (ensures same filesystem)
    fd, tmp_path = tempfile.mkstemp(dir=filepath.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=indent)
        # Atomic rename
        os.replace(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

@dataclass
class FitnessScore:
    """Multi-dimensional fitness score."""
    correctness: float = 0.0
    dharmic_alignment: float = 0.0
    elegance: float = 0.0
    efficiency: float = 0.0
    safety: float = 1.0

    def weighted(self, weights: Dict[str, float]) -> float:
        """Calculate weighted fitness score."""
        total = 0.0
        for dim, weight in weights.items():
            total += getattr(self, dim, 0.0) * weight
        return total

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

@dataclass
class EvolutionEntry:
    """Single entry in the evolution history."""
    id: str
    timestamp: str
    state: str  # SwarmState value
    agent: str
    action: str
    parent_id: Optional[str] = None
    fitness: Optional[FitnessScore] = None
    files_changed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        if self.fitness:
            d['fitness'] = self.fitness.to_dict()
        return d

class ResidualStream:
    """
    Persistent memory for swarm evolution.

    Tracks:
    - Evolution history (all state transitions)
    - Fitness progression over time
    - Archive of successful implementations
    - Patterns extracted from successful evolutions
    """

    def __init__(self, base_path: Path, vault_path: Optional[Path] = None):
        self.base_path = Path(base_path)
        self.vault_path = Path(vault_path) if vault_path else None

        # Ensure directories exist
        self.history_path = self.base_path / "history"
        self.archive_path = self.base_path / "archive"
        self.patterns_path = self.base_path / "patterns"
        self.fitness_path = self.base_path / "fitness"

        for path in [self.history_path, self.archive_path, self.patterns_path, self.fitness_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self._load_state()

    def _load_state(self):
        """Load current state from disk."""
        state_file = self.base_path / "state.json"
        if state_file.exists():
            with open(state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "cycle_count": 0,
                "total_evolutions": 0,
                "current_baseline_fitness": 0.0,
                "last_updated": datetime.now().isoformat(),
                "active_lineage": None
            }
            self._save_state()

    def _save_state(self):
        """Persist state to disk (atomic write)."""
        state_file = self.base_path / "state.json"
        self.state["last_updated"] = datetime.now().isoformat()
        atomic_write_json(state_file, self.state)

    def generate_id(self) -> str:
        """Generate unique evolution ID."""
        return f"evo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def log_entry(self, entry: EvolutionEntry) -> str:
        """Log an evolution entry to history (atomic write)."""
        # Save to history
        entry_file = self.history_path / f"{entry.id}.json"
        atomic_write_json(entry_file, entry.to_dict())

        # Update state
        self.state["total_evolutions"] += 1
        if entry.fitness:
            weighted = entry.fitness.weighted({
                "correctness": 0.3,
                "dharmic_alignment": 0.25,
                "elegance": 0.2,
                "efficiency": 0.15,
                "safety": 0.1
            })
            if weighted > self.state["current_baseline_fitness"]:
                self.state["current_baseline_fitness"] = weighted

        self._save_state()
        return entry.id

    def log_proposal(self, agent: str, proposals: List[Dict]) -> str:
        """Log a proposal from proposer agent."""
        entry = EvolutionEntry(
            id=self.generate_id(),
            timestamp=datetime.now().isoformat(),
            state="propose",
            agent=agent,
            action="proposal_generated",
            metadata={"proposals": proposals}
        )
        return self.log_entry(entry)

    def log_implementation(self, agent: str, files: List[Dict], parent_id: str) -> str:
        """Log an implementation from writer agent."""
        entry = EvolutionEntry(
            id=self.generate_id(),
            timestamp=datetime.now().isoformat(),
            state="write",
            agent=agent,
            action="implementation_complete",
            parent_id=parent_id,
            files_changed=[f["path"] for f in files],
            metadata={"files": files}
        )
        return self.log_entry(entry)

    def log_test_result(self, agent: str, fitness: FitnessScore, passed: bool, parent_id: str) -> str:
        """Log test results from tester agent."""
        entry = EvolutionEntry(
            id=self.generate_id(),
            timestamp=datetime.now().isoformat(),
            state="test",
            agent=agent,
            action="test_complete",
            parent_id=parent_id,
            fitness=fitness,
            metadata={"passed": passed}
        )
        return self.log_entry(entry)

    def log_refinement(self, agent: str, refinements: List[Dict], parent_id: str) -> str:
        """Log refinements from refiner agent."""
        entry = EvolutionEntry(
            id=self.generate_id(),
            timestamp=datetime.now().isoformat(),
            state="refine",
            agent=agent,
            action="refinement_complete",
            parent_id=parent_id,
            files_changed=[r["file"] for r in refinements],
            metadata={"refinements": refinements}
        )
        return self.log_entry(entry)

    def log_evolution(self, agent: str, archive_entry: Dict, fitness: FitnessScore, parent_id: str) -> str:
        """Log successful evolution to archive."""
        entry_id = self.generate_id()

        # Save to archive (atomic write)
        archive_file = self.archive_path / f"{entry_id}.json"
        archive_entry["id"] = entry_id
        archive_entry["parent_id"] = parent_id
        archive_entry["fitness"] = fitness.to_dict()
        archive_entry["timestamp"] = datetime.now().isoformat()

        atomic_write_json(archive_file, archive_entry)

        # Log entry
        entry = EvolutionEntry(
            id=entry_id,
            timestamp=datetime.now().isoformat(),
            state="evolve",
            agent=agent,
            action="archived_to_evolution",
            parent_id=parent_id,
            fitness=fitness,
            metadata={"archive_entry": archive_entry}
        )

        self.state["active_lineage"] = entry_id
        return self.log_entry(entry)

    def log_veto(self, agent: str, reason: str, target_id: str) -> str:
        """Log a dharmic veto."""
        entry = EvolutionEntry(
            id=self.generate_id(),
            timestamp=datetime.now().isoformat(),
            state="veto",
            agent=agent,
            action="dharmic_veto",
            parent_id=target_id,
            metadata={"veto_reason": reason}
        )
        return self.log_entry(entry)

    def get_recent_history(self, limit: int = 20) -> List[Dict]:
        """Get recent evolution history."""
        entries = []
        for entry_file in sorted(self.history_path.glob("*.json"), reverse=True)[:limit]:
            with open(entry_file) as f:
                entries.append(json.load(f))
        return entries

    def get_fitness_history(self, limit: int = 100) -> List[Dict]:
        """Get fitness score history."""
        fitness_entries = []
        for entry in self.get_recent_history(limit):
            if entry.get("fitness"):
                fitness_entries.append({
                    "id": entry["id"],
                    "timestamp": entry["timestamp"],
                    "fitness": entry["fitness"]
                })
        return fitness_entries

    def get_archive_entries(self, limit: int = 50) -> List[Dict]:
        """Get archived successful evolutions."""
        entries = []
        for archive_file in sorted(self.archive_path.glob("*.json"), reverse=True)[:limit]:
            with open(archive_file) as f:
                entries.append(json.load(f))
        return entries

    def get_lineage(self, entry_id: str) -> List[Dict]:
        """Trace lineage of an evolution entry."""
        lineage = []
        current_id = entry_id

        while current_id:
            entry_file = self.history_path / f"{current_id}.json"
            if not entry_file.exists():
                break
            with open(entry_file) as f:
                entry = json.load(f)
                lineage.append(entry)
                current_id = entry.get("parent_id")

        return list(reversed(lineage))

    def extract_patterns(self, min_fitness: float = 0.8) -> List[Dict]:
        """Extract patterns from successful evolutions."""
        patterns = []
        for archive_entry in self.get_archive_entries():
            if archive_entry.get("fitness", {}).get("weighted", 0) >= min_fitness:
                if "patterns_extracted" in archive_entry:
                    patterns.extend(archive_entry["patterns_extracted"])
        return patterns

    def get_baseline_fitness(self) -> float:
        """Get current baseline fitness."""
        return self.state.get("current_baseline_fitness", 0.0)

    def get_cycle_count(self) -> int:
        """Get number of improvement cycles completed."""
        return self.state.get("cycle_count", 0)

    def increment_cycle(self):
        """Increment cycle counter."""
        self.state["cycle_count"] = self.state.get("cycle_count", 0) + 1
        self._save_state()

    def sync_to_vault(self):
        """Sync important evolutions to the Persistent Semantic Memory Vault."""
        if not self.vault_path:
            return

        # Get high-fitness entries
        high_fitness = [e for e in self.get_archive_entries()
                       if e.get("fitness", {}).get("weighted", 0) >= 0.85]

        if not high_fitness:
            return

        # Write to vault's agent workspace (atomic write)
        vault_output = self.vault_path / "AGENT_IGNITION" / "swarm_evolutions.json"
        atomic_write_json(vault_output, {
            "synced_at": datetime.now().isoformat(),
            "evolutions": high_fitness[:20],  # Top 20
            "baseline_fitness": self.get_baseline_fitness(),
            "total_cycles": self.get_cycle_count()
        })
