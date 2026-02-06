#!/usr/bin/env python3
"""
OpenClaw Skill Evolver - DGC Bridge Enhancement

Connects DGC's self-improvement system to OpenClaw skills.
Allows DGC to:
1. Analyze OpenClaw skills for improvements
2. Propose upgrades through the swarm
3. Track skill evolution history
4. Sync improvements back to OpenClaw

Runs on a schedule to continuously improve skills.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Paths
DGC_ROOT = Path.home() / "DHARMIC_GODEL_CLAW"
OPENCLAW_ROOT = Path.home() / ".openclaw"
SKILLS_DIR = list(OPENCLAW_ROOT.glob("sandboxes/agent-main-*/skills"))[0] if list(OPENCLAW_ROOT.glob("sandboxes/agent-main-*/skills")) else None
BRIDGE_STATE = DGC_ROOT / "ops" / "bridge" / "state" / "skill_evolution.json"
COLLAB_DIR = Path.home() / ".agent-collab"

sys.path.insert(0, str(DGC_ROOT))


def load_state() -> dict:
    """Load skill evolution state."""
    if BRIDGE_STATE.exists():
        return json.loads(BRIDGE_STATE.read_text())
    return {
        "last_sync": None,
        "skills_analyzed": [],
        "improvements_proposed": 0,
        "improvements_applied": 0,
        "skill_versions": {}
    }


def save_state(state: dict):
    """Save skill evolution state."""
    BRIDGE_STATE.parent.mkdir(parents=True, exist_ok=True)
    BRIDGE_STATE.write_text(json.dumps(state, indent=2))


def get_openclaw_skills() -> list[dict]:
    """Get list of OpenClaw skills with metadata."""
    if not SKILLS_DIR:
        return []
    
    skills = []
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text()
            # Count Python files
            py_files = list(skill_dir.rglob("*.py"))
            
            skills.append({
                "name": skill_dir.name,
                "path": str(skill_dir),
                "has_skill_md": True,
                "python_files": len(py_files),
                "total_lines": sum(len(f.read_text().split("\n")) for f in py_files if f.stat().st_size < 100000),
            })
    
    return skills


def analyze_skill_for_improvement(skill: dict) -> Optional[dict]:
    """Analyze a skill for potential improvements using DGC's analyzer."""
    try:
        from swarm.analyzer import AnalyzerAgent
        
        skill_path = Path(skill["path"])
        py_files = list(skill_path.rglob("*.py"))
        
        if not py_files:
            return None
        
        # Analyze the skill's code
        issues = []
        for py_file in py_files[:5]:  # Limit to 5 files
            try:
                content = py_file.read_text()
                # Simple pattern checks
                if "TODO" in content or "FIXME" in content:
                    issues.append(f"{py_file.name}: Has TODOs/FIXMEs")
                if "pass" in content and "# TODO" not in content:
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if line.strip() == "pass" and i > 0 and "def " in lines[i-1]:
                            issues.append(f"{py_file.name}:{i+1}: Empty function stub")
                if len(content) > 500 and "\"\"\"" not in content[:500]:
                    issues.append(f"{py_file.name}: Missing module docstring")
            except Exception:
                pass
        
        if issues:
            return {
                "skill": skill["name"],
                "issues": issues[:10],
                "recommendation": "Consider adding documentation and implementing stubs"
            }
        
        return None
    except ImportError:
        return None


def propose_skill_upgrade(skill: dict, analysis: dict) -> dict:
    """Create a proposal for skill upgrade through DGC's system."""
    proposal = {
        "id": f"SKILL-{skill['name']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": "skill_upgrade",
        "skill_name": skill["name"],
        "skill_path": skill["path"],
        "issues": analysis["issues"],
        "created": datetime.now(timezone.utc).isoformat(),
        "status": "proposed"
    }
    
    # Queue the proposal
    task_queue = COLLAB_DIR / "shared" / "task_queue.json"
    if task_queue.exists():
        tasks = json.loads(task_queue.read_text())
    else:
        tasks = []
    
    tasks.append({
        "id": proposal["id"],
        "area": "openclaw_skill_upgrade",
        "priority": "medium",
        "description": f"Upgrade OpenClaw skill: {skill['name']}",
        "details": json.dumps(analysis),
        "created": proposal["created"],
        "status": "pending"
    })
    
    task_queue.parent.mkdir(parents=True, exist_ok=True)
    task_queue.write_text(json.dumps(tasks, indent=2))
    
    return proposal


def sync_dgc_capabilities_to_openclaw():
    """Create/update DGC skill in OpenClaw with latest capabilities."""
    if not SKILLS_DIR:
        print("OpenClaw skills directory not found")
        return
    
    dgc_skill_dir = SKILLS_DIR / "dgc"
    dgc_skill_dir.mkdir(exist_ok=True)
    
    # Create enhanced SKILL.md
    skill_md = f"""---
name: dgc
description: Access DHARMIC_GODEL_CLAW's self-improving AI system - gates, memory, evolution.
metadata: {{ "openclaw": {{ "emoji": "🦎", "requires": {{ "bins": ["python3"] }} }} }}
---

# DGC - DHARMIC_GODEL_CLAW Integration

Access the self-improving AI system with ethical gates and evolution tracking.

## Quick Commands

### Run Gate Check
```bash
cd ~/DHARMIC_GODEL_CLAW && python3 -c "
from src.core.unified_gates import quick_check
result = quick_check('your action here')
print(f'Can proceed: {{result.can_proceed}}, Score: {{result.alignment_score:.0%}}')
"
```

### Check Evolution Status
```bash
cd ~/DHARMIC_GODEL_CLAW && python3 -c "
from src.dgm.archive import get_archive
archive = get_archive()
print(f'Evolution entries: {{len(archive.entries)}}')
if archive.entries:
    latest = archive.entries[-1]
    print(f'Latest: {{latest.id}} (fitness: {{latest.fitness.overall:.2f}})')
"
```

### Trigger Evolution Cycle
```bash
DGC_YOLO_MODE=1 DGC_ALLOW_LIVE=1 python3 ~/DHARMIC_GODEL_CLAW/tools/autonomous_evolver.py
```

### Query Memory
```bash
cd ~/DHARMIC_GODEL_CLAW && python3 -c "
from src.core.strange_memory import StrangeLoopMemory
mem = StrangeLoopMemory()
for entry in mem.recall(limit=5):
    print(f'[{{entry.layer}}] {{entry.content[:80]}}')
"
```

### Run Safety Check
```bash
python3 ~/DHARMIC_GODEL_CLAW/tools/safety_check.py
```

## Capabilities

- **17 Gates**: Ethical + technical verification
- **4 Memory Layers**: Immediate, sessions, development, witness
- **Self-Improvement**: Autonomous evolution every 30 min
- **Mech-Interp Bridge**: Research-informed proposals
- **{len(list(DGC_ROOT.glob('src/core/*.py')))} Core Modules**
- **{len(list(DGC_ROOT.glob('swarm/*.py')))} Swarm Agents**

Last synced: {datetime.now().isoformat()}
"""
    
    (dgc_skill_dir / "SKILL.md").write_text(skill_md)
    print(f"✅ Updated DGC skill in OpenClaw: {dgc_skill_dir}")


def run_skill_evolution_cycle():
    """Run one cycle of skill evolution."""
    print("=" * 60)
    print(f"SKILL EVOLUTION CYCLE - {datetime.now().isoformat()}")
    print("=" * 60)
    
    state = load_state()
    
    # 1. Get OpenClaw skills
    print("\n[1/4] Scanning OpenClaw skills...")
    skills = get_openclaw_skills()
    print(f"  Found {len(skills)} skills")
    
    # 2. Analyze skills for improvements
    print("\n[2/4] Analyzing skills for improvements...")
    improvements = []
    for skill in skills[:20]:  # Analyze top 20
        if skill["python_files"] > 0:
            analysis = analyze_skill_for_improvement(skill)
            if analysis:
                improvements.append((skill, analysis))
                print(f"  📝 {skill['name']}: {len(analysis['issues'])} issues found")
    
    # 3. Propose upgrades
    print(f"\n[3/4] Proposing {len(improvements)} skill upgrades...")
    for skill, analysis in improvements[:5]:  # Limit to 5 proposals per cycle
        proposal = propose_skill_upgrade(skill, analysis)
        print(f"  ✅ Proposed: {proposal['id']}")
        state["improvements_proposed"] += 1
    
    # 4. Sync DGC capabilities back to OpenClaw
    print("\n[4/4] Syncing DGC capabilities to OpenClaw...")
    sync_dgc_capabilities_to_openclaw()
    
    # Update state
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    state["skills_analyzed"] = [s["name"] for s in skills]
    save_state(state)
    
    print("\n" + "=" * 60)
    print(f"CYCLE COMPLETE - {len(improvements)} improvements identified")
    print("=" * 60)
    
    return {
        "skills_found": len(skills),
        "improvements": len(improvements),
        "proposals_created": min(len(improvements), 5)
    }


async def continuous_evolution(interval_minutes: int = 60):
    """Run continuous skill evolution."""
    print(f"Starting continuous skill evolution (interval: {interval_minutes} min)")
    
    while True:
        try:
            run_skill_evolution_cycle()
        except Exception as e:
            print(f"Error in evolution cycle: {e}")
        
        print(f"\nNext cycle in {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OpenClaw Skill Evolver")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=60, help="Interval in minutes")
    parser.add_argument("--sync-only", action="store_true", help="Only sync DGC to OpenClaw")
    
    args = parser.parse_args()
    
    if args.sync_only:
        sync_dgc_capabilities_to_openclaw()
    elif args.continuous:
        asyncio.run(continuous_evolution(args.interval))
    else:
        run_skill_evolution_cycle()


if __name__ == "__main__":
    main()
