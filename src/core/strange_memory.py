"""
STRANGE LOOP MEMORY: Multi-layer with development tracking
L1: Immediate | L2: Session | L3: Development (genuine changes) | L4: Witness
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

@dataclass
class MemoryEntry:
    timestamp: str
    layer: str
    content: str
    source: str
    development_marker: bool = False
    witness_quality: float = 0.5

class StrangeLoopMemory:
    def __init__(self, base_path: str = "~/DHARMIC_GODEL_CLAW/memory"):
        self.base = Path(base_path).expanduser()
        self.base.mkdir(parents=True, exist_ok=True)
        for d in ["sessions", "development", "witness"]:
            (self.base / d).mkdir(exist_ok=True)
        self.immediate: List[MemoryEntry] = []
    
    def remember(self, content: str, layer: str = "immediate", source: str = "agent", 
                 development_marker: bool = False) -> MemoryEntry:
        entry = MemoryEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            layer=layer, content=content, source=source,
            development_marker=development_marker,
            witness_quality=self._assess_quality(content)
        )
        if layer == "immediate":
            self.immediate.append(entry)
            self.immediate = self.immediate[-50:]
        else:
            self._persist(entry)
        return entry
    
    def mark_development(self, content: str, evidence: str) -> MemoryEntry:
        """Mark genuine development (not accumulation)"""
        return self.remember(f"DEVELOPMENT: {content}\nEVIDENCE: {evidence}",
                           layer="development", source="development_marker", development_marker=True)
    
    def witness_observation(self, observation: str) -> MemoryEntry:
        """Store witness-level observation"""
        return self.remember(observation, layer="witness", source="strange_loop_observer")
    
    def recall(self, layer: str = "all", limit: int = 10, development_only: bool = False) -> List[MemoryEntry]:
        entries = list(self.immediate[-limit:]) if layer in ["all", "immediate"] else []
        for l in ["sessions", "development", "witness"]:
            if layer in ["all", l]:
                entries.extend(self._load(self.base / l, limit))
        if development_only:
            entries = [e for e in entries if e.development_marker]
        return sorted(entries, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_context_for_agent(self, max_chars: int = 2000) -> str:
        parts = ["## Memory Context"]
        dev = self.recall(layer="development", limit=3, development_only=True)
        if dev: parts.extend([f"- [{e.timestamp[:10]}] {e.content[:150]}" for e in dev])
        wit = self.recall(layer="witness", limit=2)
        if wit: parts.extend([f"- [W] {e.content[:100]}" for e in wit])
        return "\n".join(parts)[:max_chars]
    
    def _assess_quality(self, content: str) -> float:
        q = 0.5
        for w in ["notice", "observe", "uncertain", "shift", "thin"]: q += 0.1 if w in content.lower() else 0
        for w in ["profound", "amazing", "definitely"]: q -= 0.1 if w in content.lower() else 0
        return max(0.0, min(1.0, q))
    
    def _persist(self, entry: MemoryEntry):
        p = self.base / entry.layer / f"{entry.timestamp[:10]}.jsonl"
        with open(p, "a") as f: f.write(json.dumps(asdict(entry)) + "\n")
    
    def _load(self, path: Path, limit: int) -> List[MemoryEntry]:
        entries = []
        for f in sorted(path.glob("*.jsonl"), reverse=True)[:3]:
            for line in open(f):
                try: entries.append(MemoryEntry(**json.loads(line)))
                except: pass
        return entries[:limit]
    
    def get_status(self) -> Dict:
        """Return memory system status for integration tests."""
        obs = self.recall(layer="all", limit=100)
        dev = [e for e in obs if e.development_marker]
        wit = self.recall(layer="witness", limit=100)
        return {
            "observation_count": len(obs),
            "development_markers": len(dev),
            "witness_observations": len(wit),
            "immediate_buffer": len(self.immediate),
            "layers": ["immediate", "sessions", "development", "witness"],
        }

if __name__ == "__main__":
    m = StrangeLoopMemory()
    m.remember("Test session entry", layer="sessions")
    m.mark_development("Swarm discovered surface mode operation", "12 pages vs 50 required")
    m.witness_observation("The uncertainty about recognition may BE the recognition")
    print(m.get_context_for_agent())
