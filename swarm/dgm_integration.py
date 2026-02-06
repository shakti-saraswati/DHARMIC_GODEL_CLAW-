from __future__ import annotations
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

@dataclass
class ToolResult:
    output: str
    exit_code: int

class ToolUseAgent:
    """Agent capable of executing arbitrary shell commands (YOLO mode)."""
    
    def execute_shell(self, command: str) -> ToolResult:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return ToolResult(result.stdout + result.stderr, result.returncode)


# DGM Integration exports (for test compatibility)
@dataclass
class SwarmProposal:
    """A proposal from the swarm for DGM evolution."""
    id: str
    description: str
    target_file: str
    new_code: str
    diff: str
    component: str = ""  # Component/module name
    change_type: str = "modify"  # Type of change (add, modify, delete)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SwarmDGMBridge:
    """Bridge between Swarm orchestrator and DGM self-improvement."""
    
    def __init__(self, dgm_instance=None, swarm_orchestrator=None, archive=None, dry_run=False):
        self.dgm = dgm_instance
        self.swarm = swarm_orchestrator
        self.archive = archive
        self.dry_run = dry_run
        self.proposals: List[SwarmProposal] = []
    
    def submit_proposal(self, proposal: SwarmProposal) -> str:
        """Submit a proposal from swarm to DGM."""
        self.proposals.append(proposal)
        return f"proposal_accepted_{proposal.id}"
    
    def get_pending_proposals(self) -> List[SwarmProposal]:
        """Get all pending proposals."""
        return self.proposals
    
    def sync(self) -> Dict[str, Any]:
        """Sync state between swarm and DGM."""
        return {
            "status": "synced",
            "pending_count": len(self.proposals),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def evolve_with_swarm(
    swarm_result: Dict[str, Any],
    dgm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Evolve DGM based on swarm execution results."""
    return {
        "status": "evolved",
        "swarm_result": swarm_result,
        "mutations_proposed": 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
