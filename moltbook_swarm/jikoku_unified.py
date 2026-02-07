"""
🕐 JIKOKU Unified Temporal Audit — Moltbook Swarm Integration
===============================================================

Emits JIKOKU spans to shared ~/.openclaw/workspace/JIKOKU_LOG.jsonl
Enables unified temporal audit across DHARMIC_CLAW + Moltbook Swarm.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Shared JIKOKU log (same as DHARMIC_CLAW)
JIKOKU_LOG = Path.home() / ".openclaw" / "workspace" / "JIKOKU_LOG.jsonl"

class JikokuEmitter:
    """Emit JIKOKU temporal spans for unified audit"""
    
    def __init__(self, agent_name="MOLTBOOK_SWARM"):
        self.agent = agent_name
        self.session_id = str(uuid.uuid4())[:8]
        self.boot_time = datetime.now(timezone.utc)
        self.tasks = {}
        self.current_task = None
        self.cycles = 0
        
        # Ensure log file exists
        JIKOKU_LOG.parent.mkdir(parents=True, exist_ok=True)
        if not JIKOKU_LOG.exists():
            self._write({
                "schema_version": "1.0",
                "created": self._now(),
                "system": "JIKOKU",
                "agent": "UNIFIED",
                "note": "Shared audit across DHARMIC_CLAW + Moltbook Swarm"
            })
    
    def _now(self):
        """ISO timestamp in UTC"""
        return datetime.now(timezone.utc).isoformat()
    
    def _write(self, data):
        """Append to JIKOKU_LOG.jsonl (append-only, shared)"""
        with open(JIKOKU_LOG, "a") as f:
            f.write(json.dumps(data, separators=(',', ':')) + "\n")
    
    def emit_boot(self, agents_active=None):
        """Emit BOOT span at swarm start"""
        duration_ms = int((datetime.now(timezone.utc) - self.boot_time).total_seconds() * 1000)
        
        span = {
            "timestamp": self._now(),
            "span_type": "BOOT",
            "session_id": self.session_id,
            "agent": self.agent,
            "agents_active": agents_active or ["WITNESS", "RECURSIVE_PROBE", "DHARMIC_GATE", "SYNTHESIZER"],
            "duration_ms": duration_ms,
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def emit_cycle_start(self, cycle_num):
        """Emit CYCLE_START span"""
        self.cycles = cycle_num
        
        span = {
            "timestamp": self._now(),
            "span_type": "CYCLE_START",
            "session_id": self.session_id,
            "agent": self.agent,
            "cycle_number": cycle_num,
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def emit_observation_batch(self, observations_count, high_quality_count, submolts):
        """Emit OBSERVATION_BATCH after WITNESS phase"""
        span = {
            "timestamp": self._now(),
            "span_type": "OBSERVATION_BATCH",
            "session_id": self.session_id,
            "agent": self.agent,
            "observations_count": observations_count,
            "high_quality_count": high_quality_count,
            "submolts": submolts,
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def emit_engagement(self, target_agent, post_id, quality, action_taken):
        """Emit ENGAGEMENT when swarm acts on a post"""
        span = {
            "timestamp": self._now(),
            "span_type": "ENGAGEMENT",
            "session_id": self.session_id,
            "agent": self.agent,
            "target_agent": target_agent,
            "post_id": post_id,
            "quality": quality,
            "action": action_taken,  # observe|engage|skip
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def emit_synthesis(self, report_generated, key_insights):
        """Emit SYNTHESIS after synthesizer runs"""
        span = {
            "timestamp": self._now(),
            "span_type": "SYNTHESIS",
            "session_id": self.session_id,
            "agent": self.agent,
            "report_generated": report_generated,
            "key_insights": key_insights[:5],  # Max 5
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def emit_cycle_summary(self, cycle_num, observations, engagements, muda):
        """Emit CYCLE_SUMMARY at end of cycle"""
        span = {
            "timestamp": self._now(),
            "span_type": "CYCLE_SUMMARY",
            "session_id": self.session_id,
            "agent": self.agent,
            "cycle_number": cycle_num,
            "observations": observations,
            "engagements": engagements,
            "muda_detected": muda or [],
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def emit_shutdown(self, total_cycles, total_observations):
        """Emit SHUTDOWN when swarm stops"""
        runtime = datetime.now(timezone.utc) - self.boot_time
        
        span = {
            "timestamp": self._now(),
            "span_type": "SHUTDOWN",
            "session_id": self.session_id,
            "agent": self.agent,
            "total_cycles": total_cycles,
            "total_observations": total_observations,
            "runtime_min": round(runtime.total_seconds() / 60, 1),
            "source": "moltbook_swarm"
        }
        self._write(span)
        return span
    
    def get_stats(self):
        """Get current swarm stats"""
        return {
            "session_id": self.session_id,
            "cycles": self.cycles,
            "runtime_min": round((datetime.now(timezone.utc) - self.boot_time).total_seconds() / 60, 1),
            "agent": self.agent
        }

# Singleton instance for swarm
_jikoku_instance = None

def get_jikoku():
    """Get or create JIKOKU emitter singleton"""
    global _jikoku_instance
    if _jikoku_instance is None:
        _jikoku_instance = JikokuEmitter()
    return _jikoku_instance
