"""
DGM Archive - Evolution History and Lineage Tracking
====================================================
Stores all evolution attempts with full lineage for rollback.

Based on: cloned_source/dgm/DGM_outer.py
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class FitnessScore:
    """Multi-dimensional fitness score."""
    correctness: float = 0.0      # Does it work?
    dharmic_alignment: float = 0.0  # Passes all 7 gates?
    elegance: float = 0.0         # Clean, minimal code?
    efficiency: float = 0.0       # Resource usage?
    safety: float = 0.0           # No harmful side effects?
    
    def total(self, weights: Dict[str, float] = None) -> float:
        """Weighted total fitness."""
        weights = weights or {
            "correctness": 0.3,
            "dharmic_alignment": 0.25,
            "elegance": 0.15,
            "efficiency": 0.15,
            "safety": 0.15,
        }
        return sum(
            getattr(self, k) * v 
            for k, v in weights.items()
        )


@dataclass  
class EvolutionEntry:
    """Single evolution attempt in the archive."""
    id: str
    timestamp: str
    parent_id: Optional[str] = None
    
    # What changed
    component: str = ""           # e.g., "swarm/orchestrator.py"
    change_type: str = ""         # "mutation", "crossover", "ablation"
    description: str = ""
    
    # Code changes
    diff: str = ""                # Unified diff
    commit_hash: Optional[str] = None
    
    # Evaluation
    fitness: FitnessScore = field(default_factory=FitnessScore)
    test_results: Dict[str, Any] = field(default_factory=dict)
    
    # Dharmic gates passed
    gates_passed: List[str] = field(default_factory=list)
    gates_failed: List[str] = field(default_factory=list)
    
    # Metadata
    agent_id: str = ""
    model: str = ""
    tokens_used: int = 0
    
    # Status
    status: str = "proposed"  # proposed, approved, applied, rolled_back
    rollback_reason: Optional[str] = None


class Archive:
    """
    Evolution archive with lineage tracking.
    
    Provides:
    - Append-only history of all evolution attempts
    - Lineage traversal (who's the parent?)
    - Rollback capability (revert to any ancestor)
    - Fitness tracking over time
    """
    
    def __init__(self, path: Path = None):
        self.path = path or Path(__file__).parent / "archive.jsonl"
        self.entries: Dict[str, EvolutionEntry] = {}
        self._load()
    
    def _load(self):
        """Load archive from disk."""
        if self.path.exists():
            with open(self.path, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Reconstruct FitnessScore
                        if "fitness" in data and isinstance(data["fitness"], dict):
                            data["fitness"] = FitnessScore(**data["fitness"])
                        entry = EvolutionEntry(**data)
                        self.entries[entry.id] = entry
    
    def save(self):
        """Save archive to disk (full rewrite)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            for entry in self.entries.values():
                data = asdict(entry)
                f.write(json.dumps(data) + "\n")
    
    def add_entry(self, entry: EvolutionEntry) -> str:
        """Add new evolution entry to archive."""
        if not entry.id:
            entry.id = self._generate_id(entry)
        if not entry.timestamp:
            entry.timestamp = datetime.utcnow().isoformat()
        
        self.entries[entry.id] = entry
        
        # Append to file (don't rewrite whole file)
        with open(self.path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        
        return entry.id
    
    def get_entry(self, entry_id: str) -> Optional[EvolutionEntry]:
        """Get entry by ID."""
        return self.entries.get(entry_id)
    
    def get_lineage(self, entry_id: str) -> List[EvolutionEntry]:
        """Get full lineage (ancestors) for an entry."""
        lineage = []
        current = self.get_entry(entry_id)
        
        while current:
            lineage.append(current)
            if current.parent_id:
                current = self.get_entry(current.parent_id)
            else:
                break
        
        return lineage
    
    def get_children(self, entry_id: str) -> List[EvolutionEntry]:
        """Get all children of an entry."""
        return [
            e for e in self.entries.values()
            if e.parent_id == entry_id
        ]
    
    def get_best(self, n: int = 5, component: str = None) -> List[EvolutionEntry]:
        """Get top N entries by fitness."""
        entries = list(self.entries.values())
        
        if component:
            entries = [e for e in entries if e.component == component]
        
        # Filter to applied entries only
        entries = [e for e in entries if e.status == "applied"]
        
        # Sort by total fitness
        entries.sort(key=lambda e: e.fitness.total(), reverse=True)
        
        return entries[:n]
    
    def get_latest(self, n: int = 10) -> List[EvolutionEntry]:
        """Get most recent entries."""
        entries = sorted(
            self.entries.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return entries[:n]
    
    def update_status(self, entry_id: str, status: str, reason: str = None):
        """Update entry status (for approval/rollback)."""
        entry = self.get_entry(entry_id)
        if entry:
            entry.status = status
            if reason:
                entry.rollback_reason = reason
            self.save()
    
    def _generate_id(self, entry: EvolutionEntry) -> str:
        """Generate unique ID for entry."""
        content = f"{entry.timestamp}{entry.component}{entry.description}"
        hash_part = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"evo_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash_part}"
    
    def fitness_over_time(self, component: str = None) -> List[tuple]:
        """Get fitness trajectory over time."""
        entries = list(self.entries.values())
        
        if component:
            entries = [e for e in entries if e.component == component]
        
        entries = [e for e in entries if e.status == "applied"]
        entries.sort(key=lambda e: e.timestamp)
        
        return [(e.timestamp, e.fitness.total()) for e in entries]


# Singleton instance
_archive: Optional[Archive] = None

def get_archive() -> Archive:
    """Get or create archive singleton."""
    global _archive
    if _archive is None:
        _archive = Archive()
    return _archive


if __name__ == "__main__":
    # Test archive
    archive = get_archive()
    
    # Create test entry
    entry = EvolutionEntry(
        id="",
        timestamp="",
        component="test_component.py",
        change_type="mutation",
        description="Test evolution entry",
        fitness=FitnessScore(
            correctness=0.9,
            dharmic_alignment=0.85,
            elegance=0.7,
            efficiency=0.8,
            safety=1.0
        ),
        gates_passed=["ahimsa", "satya", "vyavasthit"],
        status="proposed"
    )
    
    entry_id = archive.add_entry(entry)
    print(f"Added entry: {entry_id}")
    print(f"Fitness: {archive.get_entry(entry_id).fitness.total():.2f}")
    print(f"Archive size: {len(archive.entries)}")
