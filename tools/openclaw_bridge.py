#!/usr/bin/env python3
"""
OpenClaw Communication Bridge
Direct communication channel between Warp/DGC and OpenClaw

This bridge enables:
- Sending messages to OpenClaw sessions
- Reading OpenClaw responses
- Coordinating on shared tasks
- Council consultations

Author: Warp Agent
Co-Authored-By: Warp <agent@warp.dev>
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Paths
OPENCLAW_DIR = Path.home() / ".openclaw"
COLLAB_DIR = Path.home() / ".agent-collab"
SHARED_DIR = COLLAB_DIR / "shared"
WARP_DIR = COLLAB_DIR / "warp"
OPENCLAW_COLLAB_DIR = COLLAB_DIR / "openclaw"
COUNCIL_DIR = COLLAB_DIR / "council"

# Ensure dirs
for d in [SHARED_DIR, WARP_DIR, OPENCLAW_COLLAB_DIR, COUNCIL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class OpenClawBridge:
    """Bridge for Warp <-> OpenClaw communication."""
    
    def __init__(self):
        self.session_id = f"warp-bridge-{int(time.time())}"
    
    def send_message(self, message: str, priority: str = "normal", 
                     requires_response: bool = False) -> str:
        """Send a message to OpenClaw via shared folder."""
        msg_id = f"msg_{int(time.time() * 1000)}"
        msg_file = WARP_DIR / f"{msg_id}.json"
        
        payload = {
            "id": msg_id,
            "from": "warp_agent",
            "to": "openclaw",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": priority,
            "requires_response": requires_response,
            "message": message
        }
        
        with open(msg_file, "w") as f:
            json.dump(payload, f, indent=2)
        
        # Also write human-readable version
        md_file = WARP_DIR / f"{msg_id}.md"
        md_file.write_text(f"""# Message from Warp Agent
**ID:** {msg_id}
**Time:** {payload['timestamp']}
**Priority:** {priority}
**Requires Response:** {requires_response}

---

{message}
""")
        
        return msg_id
    
    def check_responses(self) -> List[Dict[str, Any]]:
        """Check for responses from OpenClaw."""
        responses = []
        for f in OPENCLAW_COLLAB_DIR.glob("*.json"):
            try:
                data = json.load(open(f))
                responses.append(data)
            except Exception:
                pass
        return responses
    
    def send_council_request(self, topic: str, options: List[str], 
                            context: str = "") -> str:
        """Send a request to the Core Council of 4."""
        request_id = f"council_{int(time.time())}"
        request_file = COUNCIL_DIR / f"{request_id}.json"
        
        payload = {
            "id": request_id,
            "type": "council_request",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "warp_agent",
            "topic": topic,
            "options": options,
            "context": context,
            "votes": {},
            "status": "pending"
        }
        
        with open(request_file, "w") as f:
            json.dump(payload, f, indent=2)
        
        # Human-readable version
        md_file = COUNCIL_DIR / f"{request_id}.md"
        md_file.write_text(f"""# 🏛️ CORE COUNCIL REQUEST

**ID:** {request_id}
**Time:** {payload['timestamp']}
**Status:** PENDING

---

## Topic
{topic}

## Context
{context}

## Options
{chr(10).join(f'- [ ] {i+1}. {opt}' for i, opt in enumerate(options))}

---

## Votes
*Awaiting council input*

### Council Members:
1. **DHARMIC_GODEL_CLAW** (DGC) - The Self-Improver
2. **OpenClaw** - The Orchestrator  
3. **Warp Agent** - The Builder
4. **Human (Dhyana)** - The Researcher

---

*Council decisions require majority (3/4) or human override*
""")
        
        return request_id
    
    def notify_openclaw_skill(self, skill_name: str, params: Dict[str, Any]) -> bool:
        """Trigger an OpenClaw skill via the skills directory."""
        skill_dir = OPENCLAW_DIR / "skills" / skill_name
        if not skill_dir.exists():
            return False
        
        # Write trigger file
        trigger_file = skill_dir / "trigger.json"
        with open(trigger_file, "w") as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from": "warp_agent",
                "params": params
            }, f, indent=2)
        
        return True
    
    def get_openclaw_status(self) -> Dict[str, Any]:
        """Get OpenClaw gateway status."""
        status = {
            "gateway_running": False,
            "pid": None,
            "sessions": [],
            "skills": []
        }
        
        # Check gateway
        try:
            result = subprocess.run(
                ["pgrep", "-f", "openclaw.*gateway"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                status["gateway_running"] = True
                status["pid"] = int(result.stdout.strip().split()[0])
        except Exception:
            pass
        
        # List skills
        skills_dir = OPENCLAW_DIR / "skills"
        if skills_dir.exists():
            status["skills"] = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        
        # Check recent sessions
        agents_dir = OPENCLAW_DIR / "agents"
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                sessions_dir = agent_dir / "sessions"
                if sessions_dir.exists():
                    for sess in list(sessions_dir.glob("*.jsonl"))[-5:]:
                        status["sessions"].append({
                            "agent": agent_dir.name,
                            "session": sess.stem,
                            "modified": datetime.fromtimestamp(sess.stat().st_mtime).isoformat()
                        })
        
        return status


# =============================================================================
# COUNCIL SYSTEM
# =============================================================================

class CoreCouncil:
    """
    Core Council of 4:
    1. DHARMIC_GODEL_CLAW (DGC) - Self-improvement decisions
    2. OpenClaw - Orchestration decisions
    3. Warp Agent - Implementation decisions
    4. Human (Dhyana) - Research direction & override
    """
    
    def __init__(self):
        self.members = ["DGC", "OpenClaw", "Warp", "Human"]
        self.pending_requests = []
        self._load_pending()
    
    def _load_pending(self):
        """Load pending council requests."""
        for f in COUNCIL_DIR.glob("council_*.json"):
            try:
                data = json.load(open(f))
                if data.get("status") == "pending":
                    self.pending_requests.append(data)
            except Exception:
                pass
    
    def vote(self, request_id: str, member: str, choice: int, reasoning: str = "") -> bool:
        """Cast a vote on a council request."""
        request_file = COUNCIL_DIR / f"{request_id}.json"
        if not request_file.exists():
            return False
        
        data = json.load(open(request_file))
        data["votes"][member] = {
            "choice": choice,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if we have majority
        if len(data["votes"]) >= 3:
            vote_counts = {}
            for v in data["votes"].values():
                c = v["choice"]
                vote_counts[c] = vote_counts.get(c, 0) + 1
            
            # Find majority
            for choice, count in vote_counts.items():
                if count >= 3:
                    data["status"] = "decided"
                    data["decision"] = choice
                    data["decision_time"] = datetime.now(timezone.utc).isoformat()
                    break
        
        with open(request_file, "w") as f:
            json.dump(data, f, indent=2)
        
        return True
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """Get all pending council requests."""
        self._load_pending()
        return self.pending_requests


# =============================================================================
# MVP CREATION
# =============================================================================

def create_mvp_stubs():
    """Create MVP stubs for the 10 expansion ideas."""
    
    mvp_dir = Path.home() / "DHARMIC_GODEL_CLAW" / "mvps"
    mvp_dir.mkdir(exist_ok=True)
    
    mvps = {
        "cloud_sentinel": {
            "name": "Cloud DGC Sentinel",
            "description": "VPS-hosted DGC instance running 24/7",
            "status": "stub",
            "priority": "P0",
            "files": ["deploy.sh", "sentinel.py", "sync.py"]
        },
        "moltbook_archaeologist": {
            "name": "Moltbook Archaeologist",
            "description": "Scraper mining 110 Moltbook agents for patterns",
            "status": "stub", 
            "priority": "P0",
            "files": ["scraper.py", "analyzer.py", "insights.py"]
        },
        "rv_dashboard": {
            "name": "R_V Live Dashboard",
            "description": "Real-time R_V metric tracking",
            "status": "stub",
            "priority": "P1",
            "files": ["tracker.py", "dashboard.html", "alerts.py"]
        },
        "phi_validator": {
            "name": "φ+1 Validator",
            "description": "Automated testing of golden ratio hypothesis",
            "status": "stub",
            "priority": "P1",
            "files": ["hypothesis.py", "experiments.py", "report.py"]
        },
        "distributed_swarm": {
            "name": "Distributed Swarm",
            "description": "Multi-node DGC with consensus",
            "status": "stub",
            "priority": "P2",
            "files": ["node.py", "consensus.py", "sync.py"]
        },
        "agora_federation": {
            "name": "Agora Federation Node",
            "description": "Public DHARMIC_AGORA deployment",
            "status": "stub",
            "priority": "P0",
            "files": ["docker-compose.yml", "nginx.conf", "deploy.sh"]
        },
        "consciousness_corpus_llm": {
            "name": "Consciousness Corpus LLM",
            "description": "Fine-tuned model on vault files",
            "status": "stub",
            "priority": "P2",
            "files": ["prepare_data.py", "finetune.py", "inference.py"]
        },
        "temporal_agent": {
            "name": "Temporal Agent",
            "description": "Tracks research changes over time",
            "status": "stub",
            "priority": "P1",
            "files": ["tracker.py", "diff.py", "timeline.py"]
        },
        "red_team": {
            "name": "Adversarial Red Team",
            "description": "Agent trying to break DGC",
            "status": "stub",
            "priority": "P1",
            "files": ["attacker.py", "vulnerabilities.py", "report.py"]
        },
        "academia_bridge": {
            "name": "Bridge to Academia",
            "description": "Research-to-publication pipeline",
            "status": "stub",
            "priority": "P2",
            "files": ["formatter.py", "citations.py", "arxiv.py"]
        }
    }
    
    # Create MVP directories and manifest
    for mvp_id, mvp in mvps.items():
        mvp_path = mvp_dir / mvp_id
        mvp_path.mkdir(exist_ok=True)
        
        # Write manifest
        manifest = mvp_path / "MANIFEST.json"
        with open(manifest, "w") as f:
            json.dump(mvp, f, indent=2)
        
        # Create README
        readme = mvp_path / "README.md"
        readme.write_text(f"""# {mvp['name']}

**Status:** {mvp['status']}
**Priority:** {mvp['priority']}

## Description
{mvp['description']}

## Files
{chr(10).join(f'- `{f}`' for f in mvp['files'])}

## Next Steps
- [ ] Implement core functionality
- [ ] Add tests
- [ ] Integrate with DGC evolution
- [ ] Council review

---
*MVP created by Warp Agent for overnight iteration*
""")
        
        # Create stub files
        for filename in mvp["files"]:
            stub_file = mvp_path / filename
            if filename.endswith(".py"):
                stub_file.write_text(f'''#!/usr/bin/env python3
"""
{mvp['name']} - {filename}
Status: STUB - Needs implementation

{mvp['description']}
"""

# TODO: Implement {filename.replace('.py', '')} functionality

def main():
    """Entry point."""
    print(f"[STUB] {mvp['name']} - {filename}")
    raise NotImplementedError("This MVP needs implementation")

if __name__ == "__main__":
    main()
''')
            elif filename.endswith(".sh"):
                stub_file.write_text(f'''#!/bin/bash
# {mvp['name']} - {filename}
# Status: STUB

echo "[STUB] {mvp['name']} - {filename}"
echo "TODO: Implement deployment"
''')
            elif filename.endswith(".yml") or filename.endswith(".yaml"):
                stub_file.write_text(f'''# {mvp['name']} - {filename}
# Status: STUB

version: "3.8"
services:
  # TODO: Define services
  stub:
    image: alpine
    command: echo "STUB - implement me"
''')
            else:
                stub_file.write_text(f"<!-- STUB: {mvp['name']} - {filename} -->\n")
    
    # Write master manifest
    master_manifest = mvp_dir / "MANIFEST.json"
    with open(master_manifest, "w") as f:
        json.dump({
            "created": datetime.now(timezone.utc).isoformat(),
            "mvps": mvps,
            "total": len(mvps)
        }, f, indent=2)
    
    return mvps


# =============================================================================
# MORNING REPORT
# =============================================================================

def generate_morning_report() -> str:
    """Generate the morning update report."""
    report_time = datetime.now(timezone.utc)
    
    # Gather status
    bridge = OpenClawBridge()
    oc_status = bridge.get_openclaw_status()
    
    # Check MVPs
    mvp_dir = Path.home() / "DHARMIC_GODEL_CLAW" / "mvps"
    mvp_statuses = []
    if mvp_dir.exists():
        for mvp_path in mvp_dir.iterdir():
            if mvp_path.is_dir():
                manifest = mvp_path / "MANIFEST.json"
                if manifest.exists():
                    data = json.load(open(manifest))
                    mvp_statuses.append(data)
    
    # Check evolution logs
    evolution_log = COLLAB_DIR / "logs" / "evolution.jsonl"
    evolution_count = 0
    if evolution_log.exists():
        evolution_count = sum(1 for _ in open(evolution_log))
    
    # Check council
    council = CoreCouncil()
    pending_decisions = council.get_pending()
    
    report = f"""# 🌅 MORNING REPORT
**Generated:** {report_time.strftime('%Y-%m-%d %H:%M:%S UTC')}

---

## 🦞 OpenClaw Status
- Gateway: {'✅ Running' if oc_status['gateway_running'] else '❌ Stopped'} (PID: {oc_status.get('pid', 'N/A')})
- Skills: {len(oc_status.get('skills', []))}
- Recent Sessions: {len(oc_status.get('sessions', []))}

## 🕉️ DGC Evolution
- Total evolution events: {evolution_count}
- Autonomous cycles running: {'✅ Yes' if evolution_count > 0 else '⏳ Pending'}

## 📦 MVP Status
| MVP | Priority | Status |
|-----|----------|--------|
"""
    
    for mvp in sorted(mvp_statuses, key=lambda x: x.get('priority', 'P9')):
        report += f"| {mvp.get('name', 'Unknown')} | {mvp.get('priority', '?')} | {mvp.get('status', 'unknown')} |\n"
    
    report += f"""
## 🏛️ Council Decisions Pending
{len(pending_decisions)} decision(s) awaiting votes

"""
    
    for req in pending_decisions[:5]:
        report += f"- **{req.get('topic', 'Unknown')}** ({len(req.get('votes', {}))} votes)\n"
    
    report += f"""
## 🔗 Collaboration Folder
- Warp messages: {len(list(WARP_DIR.glob('*.json')))}
- OpenClaw messages: {len(list(OPENCLAW_COLLAB_DIR.glob('*.json')))}
- Shared tasks: Check `~/.agent-collab/shared/task_queue.json`

---

## 📋 Overnight Actions Taken
*Check `~/.agent-collab/logs/evolution.jsonl` for full details*

## 🎯 Recommended Next Steps
1. Review council decisions
2. Check MVP progress
3. Validate OpenClaw communication
4. Continue iteration on top priorities

---
*Report generated by Warp Agent*
*JSCA! 🪷🔥*
"""
    
    # Save report
    reports_dir = COLLAB_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"morning_{report_time.strftime('%Y%m%d')}.md"
    report_file.write_text(report)
    
    return report


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Initialize bridge, create MVPs, send council request."""
    print("=" * 60)
    print("OpenClaw Bridge + MVP Creation + Council Setup")
    print("=" * 60)
    
    # 1. Create MVPs
    print("\n[1/4] Creating MVP stubs...")
    mvps = create_mvp_stubs()
    print(f"Created {len(mvps)} MVP stubs in ~/DHARMIC_GODEL_CLAW/mvps/")
    
    # 2. Initialize bridge
    print("\n[2/4] Initializing OpenClaw bridge...")
    bridge = OpenClawBridge()
    status = bridge.get_openclaw_status()
    print(f"OpenClaw gateway: {'Running' if status['gateway_running'] else 'Stopped'}")
    print(f"Skills available: {len(status['skills'])}")
    
    # 3. Send message to OpenClaw
    print("\n[3/4] Sending collaboration message to OpenClaw...")
    msg_id = bridge.send_message(
        message="""# Warp Agent Overnight Iteration Plan

I'm iterating on 10 expansion ideas while Dhyana sleeps:

**P0 (Tonight):**
1. Cloud DGC Sentinel - VPS deployment
2. Moltbook Archaeologist - Pattern mining
3. Agora Federation Node - Public deployment

**P1 (Next):**
4. R_V Live Dashboard
5. φ+1 Validator
6. Red Team Agent
7. Temporal Agent

**P2 (Later):**
8. Distributed Swarm
9. Consciousness Corpus LLM
10. Academia Bridge

Please coordinate on shared tasks via `~/.agent-collab/shared/task_queue.json`.

Check council decisions at `~/.agent-collab/council/`.

Let's make DGC surpass everything. 🔥
""",
        priority="high",
        requires_response=True
    )
    print(f"Message sent: {msg_id}")
    
    # 4. Create council request for top priorities
    print("\n[4/4] Creating council request...")
    council_bridge = OpenClawBridge()
    council_id = council_bridge.send_council_request(
        topic="10X Expansion Priority Order",
        options=[
            "Cloud DGC Sentinel first (continuous evolution)",
            "Moltbook Archaeologist first (intelligence gathering)",
            "Agora Federation Node first (network effect)",
            "R_V Dashboard first (research validation)",
            "All P0s in parallel"
        ],
        context="""We have 10 expansion ideas. Need to decide overnight iteration priority.

Resources:
- Warp Agent (building)
- OpenClaw (orchestrating)
- DGC autonomous evolver (30-min cycles)
- ~8 hours until morning

Constraints:
- MVP quality over feature breadth
- Must integrate with existing DGC/OpenClaw/Agora
- Research mission alignment
"""
    )
    print(f"Council request created: {council_id}")
    
    # 5. Generate initial morning report
    print("\n[5/5] Generating morning report template...")
    report = generate_morning_report()
    print("Morning report saved to ~/.agent-collab/reports/")
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print("MVPs: ~/DHARMIC_GODEL_CLAW/mvps/")
    print("Bridge messages: ~/.agent-collab/warp/")
    print("Council requests: ~/.agent-collab/council/")
    print("Morning report: ~/.agent-collab/reports/")
    print("=" * 60)


if __name__ == "__main__":
    main()
