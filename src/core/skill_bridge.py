"""
SKILL BRIDGE: Connect swarm to skill execution
P0 Bridges: 1. Registry sync | 2. Skill invocation | 3. Feedback loop
P0 WIRE: Now connected to ResidualStream for evolution tracking
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

# Wire to ResidualStream
sys.path.insert(0, str(Path(__file__).parent.parent / "swarm"))
try:
    from residual_stream import ResidualStream, FitnessScore, EvolutionEntry
    RESIDUAL_STREAM_AVAILABLE = True
except ImportError:
    RESIDUAL_STREAM_AVAILABLE = False

@dataclass
class SkillInfo:
    name: str
    domain: str
    path: str
    status: str

class SkillBridge:
    def __init__(self, residual_stream: Optional['ResidualStream'] = None):
        self.paths = [
            Path("~/.claude/skills").expanduser(),
            Path("~/.openclaw/skills").expanduser(),
            Path("~/DHARMIC_GODEL_CLAW/skills").expanduser(),
        ]
        self.registry = Path("~/.claude/skills/registry.json").expanduser()
        self.feedback_log = Path("~/DHARMIC_GODEL_CLAW/swarm/stream/fitness_log.jsonl").expanduser()
        self.feedback_log.parent.mkdir(parents=True, exist_ok=True)

        # Wire to ResidualStream for evolution tracking
        if residual_stream:
            self._residual_stream = residual_stream
        elif RESIDUAL_STREAM_AVAILABLE:
            swarm_base = Path("~/DHARMIC_GODEL_CLAW/swarm/stream").expanduser()
            vault_path = Path("~/Persistent-Semantic-Memory-Vault").expanduser()
            self._residual_stream = ResidualStream(swarm_base, vault_path)
        else:
            self._residual_stream = None
    
    def sync_registry(self) -> Dict:
        """P0 Bridge 1: Enumerate all skills, update registry"""
        skills = []
        for base in self.paths:
            if not base.exists(): continue
            for d in base.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    skills.append(SkillInfo(name=d.name, domain=self._domain(d), path=str(d), status="active"))
        
        reg = {"skills": {s.name: {"domain": s.domain, "path": s.path} for s in skills},
               "last_sync": datetime.utcnow().isoformat()}
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry, "w") as f: json.dump(reg, f, indent=2)
        return {"discovered": len(skills), "skills": [s.name for s in skills]}
    
    def invoke_skill(self, name: str, task: str = "", context: Dict = None) -> Dict:
        """P0 Bridge 2: Load skill for execution"""
        path = self._find(name)
        if not path: return {"success": False, "error": f"Skill '{name}' not found"}
        skill_md = path / "SKILL.md"
        if not skill_md.exists(): return {"success": False, "error": "No SKILL.md"}
        content = skill_md.read_text()
        self._log_invocation(name)
        return {"success": True, "skill": name, "content": content[:1000], "path": str(path)}
    
    def record_fitness(self, skill: str, fitness: float, evidence: str = "") -> Dict:
        """P0 Bridge 3: Record fitness feedback - WIRED to ResidualStream"""
        entry = {"timestamp": datetime.utcnow().isoformat(), "skill": skill, "fitness": fitness, "evidence": evidence}
        with open(self.feedback_log, "a") as f: f.write(json.dumps(entry) + "\n")

        # Wire to ResidualStream for swarm evolution tracking
        if self._residual_stream and RESIDUAL_STREAM_AVAILABLE:
            try:
                fitness_score = FitnessScore(
                    correctness=fitness,  # Map skill fitness to correctness
                    dharmic_alignment=0.8 if fitness > 0.7 else 0.5,  # Heuristic
                    elegance=fitness * 0.9,
                    efficiency=fitness,
                    safety=1.0
                )
                evo_entry = EvolutionEntry(
                    id=self._residual_stream.generate_id(),
                    timestamp=datetime.utcnow().isoformat(),
                    state="skill_fitness",
                    agent="skill_bridge",
                    action=f"fitness_recorded:{skill}",
                    fitness=fitness_score,
                    metadata={"skill": skill, "raw_fitness": fitness, "evidence": evidence}
                )
                self._residual_stream.log_entry(evo_entry)
            except Exception as e:
                # Log but don't fail on residual stream errors
                import logging
                logging.warning(f"ResidualStream write failed: {e}")

        return entry
    
    def list_skills(self, domain: str = None) -> List[SkillInfo]:
        """List all registered skills"""
        if not self.registry.exists(): self.sync_registry()
        with open(self.registry) as f: reg = json.load(f)
        return [SkillInfo(name=n, domain=i.get("domain","?"), path=i.get("path",""), status="active")
                for n, i in reg.get("skills", {}).items() if not domain or i.get("domain") == domain]
    
    def get_fitness_history(self, skill: str = None, limit: int = 10) -> List[Dict]:
        if not self.feedback_log.exists(): return []
        entries = [json.loads(l) for l in open(self.feedback_log) if l.strip()]
        if skill: entries = [e for e in entries if e.get("skill") == skill]
        return entries[-limit:]
    
    def _find(self, name: str) -> Optional[Path]:
        for base in self.paths:
            if base.exists() and (base / name).exists(): return base / name
        return None
    
    def _domain(self, path: Path) -> str:
        try:
            for line in (path / "SKILL.md").read_text()[:300].split("\n"):
                if "domain:" in line.lower(): return line.split(":")[-1].strip()
        except (IOError, PermissionError) as e:
            import logging
            logging.debug(f"Could not read domain from {path}: {e}")
        return "unknown"
    
    def _log_invocation(self, skill: str):
        log = Path("~/DHARMIC_GODEL_CLAW/swarm/stream/invocation_log.jsonl").expanduser()
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as f: f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "skill": skill}) + "\n")

if __name__ == "__main__":
    b = SkillBridge()
    print("Syncing registry...")
    r = b.sync_registry()
    print(f"Discovered {r['discovered']} skills: {r['skills'][:5]}...")
    print("\nListing skills:")
    for s in b.list_skills()[:5]: print(f"  - {s.name} ({s.domain})")
