#!/usr/bin/env python3
"""
COUNCIL BRIDGE - Connects Persistent Council to DHARMIC CLAW
============================================================

This bridge allows the Persistent Council to request specialist spawns
and DHARMIC CLAW (via Clawdbot) to execute them.

Flow:
1. Council detects need → writes SpawnRequest to queue
2. DHARMIC CLAW reads queue on heartbeat
3. DHARMIC CLAW spawns via sessions_spawn
4. Result written back to queue
5. Council reads result on next heartbeat

Queue is SQLite-backed for persistence.
"""

import sqlite3
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from enum import Enum

# =============================================================================
# CONSTANTS
# =============================================================================

BRIDGE_DB = Path(__file__).parent.parent.parent / "memory" / "council_bridge.db"

# =============================================================================
# ENUMS
# =============================================================================

class SpawnStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SpecialistType(Enum):
    BUILDER = "builder"
    RESEARCHER = "researcher"
    INTEGRATOR = "integrator"
    OUTREACH = "outreach"

# Model mapping for specialists
SPECIALIST_MODELS = {
    SpecialistType.BUILDER: "kimi",       # Fast, good at code
    SpecialistType.RESEARCHER: "haiku",   # Cheap, good at research
    SpecialistType.INTEGRATOR: "sonnet",  # Balanced
    SpecialistType.OUTREACH: "kimi",      # Good at writing
}

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SpawnRequest:
    """Request from Council to spawn a specialist."""
    id: str
    specialist_type: str
    task: str
    context: str
    priority: int = 5  # 1-10, higher = more urgent
    requested_by: str = "council"
    requested_at: str = ""
    status: str = "pending"
    result: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.requested_at:
            self.requested_at = datetime.now(timezone.utc).isoformat()

# =============================================================================
# BRIDGE CLASS
# =============================================================================

class CouncilBridge:
    """Bridge between Persistent Council and DHARMIC CLAW."""
    
    def __init__(self, db_path: Path = BRIDGE_DB):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spawn_requests (
                    id TEXT PRIMARY KEY,
                    specialist_type TEXT NOT NULL,
                    task TEXT NOT NULL,
                    context TEXT,
                    priority INTEGER DEFAULT 5,
                    requested_by TEXT,
                    requested_at TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    completed_at TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON spawn_requests(status)
            """)
            conn.commit()
    
    # -------------------------------------------------------------------------
    # COUNCIL SIDE: Request spawns
    # -------------------------------------------------------------------------
    
    def request_spawn(
        self,
        specialist_type: SpecialistType,
        task: str,
        context: str = "",
        priority: int = 5
    ) -> str:
        """
        Request a specialist spawn. Called by Council.
        
        Returns: request_id
        """
        import hashlib
        request_id = hashlib.sha256(
            f"{task}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        request = SpawnRequest(
            id=request_id,
            specialist_type=specialist_type.value,
            task=task,
            context=context,
            priority=priority
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO spawn_requests 
                (id, specialist_type, task, context, priority, requested_by, requested_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.id,
                request.specialist_type,
                request.task,
                request.context,
                request.priority,
                request.requested_by,
                request.requested_at,
                request.status
            ))
            conn.commit()
        
        return request_id
    
    # -------------------------------------------------------------------------
    # DHARMIC CLAW SIDE: Process spawns
    # -------------------------------------------------------------------------
    
    def get_pending_requests(self, limit: int = 5) -> List[SpawnRequest]:
        """Get pending spawn requests, ordered by priority."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM spawn_requests 
                WHERE status = 'pending'
                ORDER BY priority DESC, requested_at ASC
                LIMIT ?
            """, (limit,)).fetchall()
        
        return [SpawnRequest(**dict(row)) for row in rows]
    
    def mark_running(self, request_id: str):
        """Mark request as running."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE spawn_requests SET status = 'running' WHERE id = ?
            """, (request_id,))
            conn.commit()
    
    def complete_request(self, request_id: str, result: str, success: bool = True):
        """Mark request as completed with result."""
        status = "completed" if success else "failed"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE spawn_requests 
                SET status = ?, result = ?, completed_at = ?
                WHERE id = ?
            """, (status, result, datetime.now(timezone.utc).isoformat(), request_id))
            conn.commit()
    
    # -------------------------------------------------------------------------
    # COUNCIL SIDE: Read results
    # -------------------------------------------------------------------------
    
    def get_completed_requests(self, since_hours: int = 24) -> List[SpawnRequest]:
        """Get recently completed requests."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM spawn_requests 
                WHERE status IN ('completed', 'failed')
                AND completed_at > ?
                ORDER BY completed_at DESC
            """, (cutoff.isoformat(),)).fetchall()
        
        return [SpawnRequest(**dict(row)) for row in rows]
    
    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    
    def get_model_for_specialist(self, specialist_type: str) -> str:
        """Get recommended model for specialist type."""
        try:
            st = SpecialistType(specialist_type)
            return SPECIALIST_MODELS.get(st, "haiku")
        except ValueError:
            return "haiku"
    
    def status(self) -> dict:
        """Get bridge status."""
        with sqlite3.connect(self.db_path) as conn:
            pending = conn.execute(
                "SELECT COUNT(*) FROM spawn_requests WHERE status = 'pending'"
            ).fetchone()[0]
            running = conn.execute(
                "SELECT COUNT(*) FROM spawn_requests WHERE status = 'running'"
            ).fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM spawn_requests WHERE status = 'completed'"
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM spawn_requests WHERE status = 'failed'"
            ).fetchone()[0]
        
        return {
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "db_path": str(self.db_path)
        }

# =============================================================================
# HELPER: Generate Clawdbot spawn command
# =============================================================================

def generate_spawn_command(request: SpawnRequest) -> dict:
    """
    Generate the sessions_spawn parameters for DHARMIC CLAW.
    
    DHARMIC CLAW should call:
        sessions_spawn(
            task=<generated_task>,
            model=<model>,
            label=<label>
        )
    """
    bridge = CouncilBridge()
    model = bridge.get_model_for_specialist(request.specialist_type)
    
    # Build full task with context
    full_task = f"""## Specialist Task: {request.specialist_type.upper()}

### Task
{request.task}

### Context
{request.context}

### Instructions
1. Complete the task thoroughly
2. Output should be actionable
3. If code, make it complete and runnable
4. Report back with clear summary

### Output Format
Start with a one-line summary, then detailed work.
"""
    
    return {
        "task": full_task,
        "model": model,
        "label": f"{request.specialist_type}-{request.id}",
        "cleanup": "keep"
    }

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Council Bridge")
    parser.add_argument("--status", action="store_true", help="Show bridge status")
    parser.add_argument("--pending", action="store_true", help="Show pending requests")
    parser.add_argument("--request", type=str, help="Request a spawn (type:task)")
    parser.add_argument("--complete", type=str, help="Complete a request (id:result)")
    
    args = parser.parse_args()
    bridge = CouncilBridge()
    
    if args.status:
        print(json.dumps(bridge.status(), indent=2))
    
    elif args.pending:
        requests = bridge.get_pending_requests()
        for r in requests:
            print(f"[{r.id}] {r.specialist_type}: {r.task[:50]}... (priority={r.priority})")
        if not requests:
            print("No pending requests.")
    
    elif args.request:
        parts = args.request.split(":", 1)
        if len(parts) != 2:
            print("Format: --request type:task")
            return
        specialist_type = SpecialistType(parts[0])
        task = parts[1]
        request_id = bridge.request_spawn(specialist_type, task)
        print(f"Created request: {request_id}")
    
    elif args.complete:
        parts = args.complete.split(":", 1)
        if len(parts) != 2:
            print("Format: --complete id:result")
            return
        bridge.complete_request(parts[0], parts[1])
        print(f"Completed: {parts[0]}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
