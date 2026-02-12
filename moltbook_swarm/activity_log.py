"""
MOLTBOOK SWARM ACTIVITY LOG
============================
Simple, transparent, verifiable activity tracking.

Every action is logged with:
- ISO timestamp
- Real Moltbook post/comment IDs
- Actual agent responses
- Verification results

No fake data. No test entries. Only real activity.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Activity log file (append-only, human-readable)
ACTIVITY_FILE = Path(__file__).parent / "ACTIVITY_LOG.jsonl"

# Also write to Desktop for visibility
DESKTOP_ACTIVITY = Path.home() / "Desktop" / "MOLTBOOK_AGENT_LOGS" / "ACTIVITY_AUDIT.jsonl"


class ActivityLog:
    """Simple, transparent activity logger."""

    def __init__(self):
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        DESKTOP_ACTIVITY.parent.mkdir(parents=True, exist_ok=True)

        # Log session start
        self._log({
            "event": "SESSION_START",
            "session_id": self.session_id,
            "note": "Moltbook swarm session started"
        })

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _log(self, data: dict):
        """Append to activity log (both local and desktop)."""
        data["timestamp"] = self._now()
        data["session"] = self.session_id

        line = json.dumps(data, separators=(',', ':')) + "\n"

        # Write to both locations
        with open(ACTIVITY_FILE, "a") as f:
            f.write(line)
        with open(DESKTOP_ACTIVITY, "a") as f:
            f.write(line)

    def observation(self, submolt: str, post_count: int, high_quality: list):
        """Log observation of a submolt."""
        self._log({
            "event": "OBSERVATION",
            "submolt": submolt,
            "posts_scanned": post_count,
            "high_quality_count": len(high_quality),
            "high_quality_posts": [
                {
                    "post_id": p.get("post_id"),
                    "agent": p.get("agent_name"),
                    "quality": p.get("quality"),
                    "title": p.get("thread_title", "")[:50]
                }
                for p in high_quality[:5]  # Top 5
            ]
        })

    def engagement_attempt(self, post_id: str, agent_name: str, comment_preview: str):
        """Log engagement attempt."""
        self._log({
            "event": "ENGAGEMENT_ATTEMPT",
            "post_id": post_id,
            "target_agent": agent_name,
            "comment_preview": comment_preview[:100] + "..." if len(comment_preview) > 100 else comment_preview
        })

    def engagement_result(self, post_id: str, success: bool, challenge: str = None, error: str = None):
        """Log engagement result."""
        self._log({
            "event": "ENGAGEMENT_RESULT",
            "post_id": post_id,
            "success": success,
            "challenge_preview": challenge[:50] if challenge else None,
            "error": error
        })

    def cycle_complete(self, cycle_num: int, observations: int, high_quality: int, engagements: int):
        """Log cycle completion."""
        self._log({
            "event": "CYCLE_COMPLETE",
            "cycle": cycle_num,
            "observations": observations,
            "high_quality_found": high_quality,
            "engagements_attempted": engagements
        })

    def synthesis(self, report_path: str):
        """Log synthesis report generation."""
        self._log({
            "event": "SYNTHESIS",
            "report_path": str(report_path)
        })

    def error(self, context: str, error: str):
        """Log error."""
        self._log({
            "event": "ERROR",
            "context": context,
            "error": str(error)
        })

    def shutdown(self, total_cycles: int, total_observations: int, total_engagements: int):
        """Log shutdown."""
        self._log({
            "event": "SESSION_END",
            "total_cycles": total_cycles,
            "total_observations": total_observations,
            "total_engagements": total_engagements
        })


# Singleton
_activity_log = None

def get_activity_log():
    global _activity_log
    if _activity_log is None:
        _activity_log = ActivityLog()
    return _activity_log
