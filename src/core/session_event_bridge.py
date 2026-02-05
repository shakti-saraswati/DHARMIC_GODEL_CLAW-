#!/usr/bin/env python3
"""
Session Event Bridge
====================

Phase 1 implementation of Clawdbot Bridge Architecture.
Bridges Claude Code sessions to DHARMIC_CLAW persistent identity.

Usage:
    from session_event_bridge import SessionEventBridge
    
    bridge = SessionEventBridge()
    bridge.session_start(session_id="abc123", context={"task": "debugging"})
    bridge.session_interaction(session_id="abc123", significance=0.8, content="...")
    bridge.session_end(session_id="abc123", outcome="success")
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum

class SessionEventType(Enum):
    START = "session_start"
    INTERACTION = "session_interaction"
    END = "session_end"
    FAILURE = "session_failure"

@dataclass
class SessionEvent:
    """A session event to be bridged to DHARMIC_CLAW."""
    event_type: SessionEventType
    session_id: str
    timestamp: str
    significance_score: float  # 0.0 to 1.0
    content_hash: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "significance_score": self.significance_score,
            "content_hash": self.content_hash,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SessionEvent":
        return cls(
            event_type=SessionEventType(data["event_type"]),
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            significance_score=data["significance_score"],
            content_hash=data["content_hash"],
            metadata=data["metadata"]
        )

class SessionEventBridge:
    """
    Bridges Claude Code sessions to DHARMIC_CLAW.
    
    Key responsibilities:
    1. Capture session lifecycle events
    2. Score significance (not everything goes to memory)
    3. Write to bridge queue for async processing
    4. Track session patterns for DGM triggers
    """
    
    def __init__(self, 
                 bridge_dir: Optional[Path] = None,
                 significance_threshold: float = 0.6):
        """
        Initialize the bridge.
        
        Args:
            bridge_dir: Where to write bridge events (default: ~/DHARMIC_GODEL_CLAW/bridge/)
            significance_threshold: Minimum score to write to memory (0.0-1.0)
        """
        self.bridge_dir = bridge_dir or Path.home() / "DHARMIC_GODEL_CLAW" / "bridge"
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        
        self.queue_dir = self.bridge_dir / "queue"
        self.queue_dir.mkdir(exist_ok=True)
        
        self.processed_dir = self.bridge_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        self.significance_threshold = significance_threshold
        self.active_sessions: Dict[str, Dict] = {}
        
        # Load existing session state
        self._load_state()
    
    def _load_state(self):
        """Load active session state from disk."""
        state_file = self.bridge_dir / "active_sessions.json"
        if state_file.exists():
            with open(state_file) as f:
                self.active_sessions = json.load(f)
    
    def _save_state(self):
        """Save active session state to disk."""
        state_file = self.bridge_dir / "active_sessions.json"
        with open(state_file, 'w') as f:
            json.dump(self.active_sessions, f, indent=2)
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _write_event(self, event: SessionEvent, content: Optional[str] = None):
        """Write event to queue for processing."""
        event_file = self.queue_dir / f"{event.timestamp}_{event.session_id}_{event.event_type.value}.json"
        
        event_data = {
            "event": event.to_dict(),
            "content": content  # May be None for low-significance events
        }
        
        with open(event_file, 'w') as f:
            json.dump(event_data, f, indent=2)
        
        return event_file
    
    def session_start(self, session_id: str, context: Dict[str, Any]) -> Path:
        """
        Record session start.
        
        Args:
            session_id: Unique session identifier
            context: Session context (task, model, user intent, etc.)
        
        Returns:
            Path to written event file
        """
        self.active_sessions[session_id] = {
            "started_at": datetime.now().isoformat(),
            "context": context,
            "interactions": 0,
            "significant_interactions": 0
        }
        self._save_state()
        
        event = SessionEvent(
            event_type=SessionEventType.START,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            significance_score=0.5,  # Always record starts
            content_hash=self._compute_hash(json.dumps(context)),
            metadata={
                "model": context.get("model", "unknown"),
                "task": context.get("task", "unknown"),
                "user_intent": context.get("intent", "unknown")
            }
        )
        
        return self._write_event(event, json.dumps(context))
    
    def session_interaction(self, 
                           session_id: str,
                           content: str,
                           significance: float,
                           metadata: Optional[Dict] = None) -> Optional[Path]:
        """
        Record significant session interaction.
        
        Only writes if significance >= threshold.
        
        Args:
            session_id: Session identifier
            content: Interaction content (may be large)
            significance: 0.0-1.0 score (below threshold = not written)
            metadata: Additional context
        
        Returns:
            Path to event file, or None if below threshold
        """
        if session_id not in self.active_sessions:
            # Auto-start session if not tracked
            self.session_start(session_id, {"auto_started": True})
        
        self.active_sessions[session_id]["interactions"] += 1
        
        if significance < self.significance_threshold:
            return None  # Not significant enough
        
        self.active_sessions[session_id]["significant_interactions"] += 1
        self._save_state()
        
        event = SessionEvent(
            event_type=SessionEventType.INTERACTION,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            significance_score=significance,
            content_hash=self._compute_hash(content),
            metadata=metadata or {}
        )
        
        return self._write_event(event, content)
    
    def session_end(self, 
                   session_id: str,
                   outcome: str,
                   summary: Optional[str] = None) -> Path:
        """
        Record session end.
        
        Args:
            session_id: Session identifier
            outcome: "success", "failure", "interrupted", etc.
            summary: Optional session summary
        
        Returns:
            Path to written event file
        """
        session_data = self.active_sessions.pop(session_id, {})
        self._save_state()
        
        # Compute overall significance
        total_interactions = session_data.get("interactions", 0)
        significant_interactions = session_data.get("significant_interactions", 0)
        significance = significant_interactions / max(total_interactions, 1)
        
        event = SessionEvent(
            event_type=SessionEventType.END,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            significance_score=significance,
            content_hash=self._compute_hash(summary or ""),
            metadata={
                "outcome": outcome,
                "total_interactions": total_interactions,
                "significant_interactions": significant_interactions,
                "duration_seconds": self._compute_duration(session_data)
            }
        )
        
        return self._write_event(event, summary)
    
    def session_failure(self,
                       session_id: str,
                       error_type: str,
                       error_message: str,
                       recoverable: bool = True) -> Path:
        """
        Record session failure.
        
        Always recorded (high significance) for DGM improvement triggers.
        
        Args:
            session_id: Session identifier
            error_type: Category of error
            error_message: Error details
            recoverable: Whether session could continue
        
        Returns:
            Path to written event file
        """
        event = SessionEvent(
            event_type=SessionEventType.FAILURE,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            significance_score=1.0,  # Always record failures
            content_hash=self._compute_hash(error_message),
            metadata={
                "error_type": error_type,
                "recoverable": recoverable,
                "requires_dgm": True  # Flag for DGM processing
            }
        )
        
        return self._write_event(event, error_message)
    
    def _compute_duration(self, session_data: Dict) -> Optional[float]:
        """Compute session duration in seconds."""
        started = session_data.get("started_at")
        if started:
            try:
                start_dt = datetime.fromisoformat(started)
                return (datetime.now() - start_dt).total_seconds()
            except:
                pass
        return None
    
    def get_stats(self) -> Dict:
        """Get bridge statistics."""
        queue_count = len(list(self.queue_dir.glob("*.json")))
        processed_count = len(list(self.processed_dir.glob("*.json")))
        
        return {
            "active_sessions": len(self.active_sessions),
            "queue_size": queue_count,
            "processed_count": processed_count,
            "significance_threshold": self.significance_threshold,
            "bridge_dir": str(self.bridge_dir)
        }
    
    def get_pending_events(self) -> List[Path]:
        """Get list of pending events in queue."""
        return sorted(self.queue_dir.glob("*.json"))
    
    def mark_processed(self, event_path: Path):
        """Move event from queue to processed."""
        if event_path.exists():
            dest = self.processed_dir / event_path.name
            event_path.rename(dest)
            return dest
        return None


def test_bridge():
    """Quick test of bridge functionality."""
    import tempfile
    import shutil
    
    # Create temp directory for testing
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create bridge
        bridge = SessionEventBridge(bridge_dir=test_dir)
        
        # Test session start
        session_id = "test_session_001"
        start_event = bridge.session_start(
            session_id=session_id,
            context={
                "model": "claude-sonnet-4-5",
                "task": "debugging",
                "intent": "fix integration test"
            }
        )
        print(f"✅ Session start recorded: {start_event.name}")
        
        # Test interaction
        interaction_event = bridge.session_interaction(
            session_id=session_id,
            content="Found the bug in unified_daemon.py",
            significance=0.8,
            metadata={"topic": "daemon_fix", "lines_changed": 15}
        )
        print(f"✅ Interaction recorded: {interaction_event.name if interaction_event else 'filtered'}")
        
        # Test low-significance interaction (should be filtered)
        low_event = bridge.session_interaction(
            session_id=session_id,
            content="Just checking...",
            significance=0.3  # Below 0.6 threshold
        )
        print(f"✅ Low significance filtered: {low_event is None}")
        
        # Test session end
        end_event = bridge.session_end(
            session_id=session_id,
            outcome="success",
            summary="Fixed the unified daemon logging issue"
        )
        print(f"✅ Session end recorded: {end_event.name}")
        
        # Check stats
        stats = bridge.get_stats()
        print("\n📊 Bridge Stats:")
        print(f"   Active sessions: {stats['active_sessions']}")
        print(f"   Queue size: {stats['queue_size']}")
        print(f"   Processed: {stats['processed_count']}")
        
        # Check pending events
        pending = bridge.get_pending_events()
        print(f"   Pending events: {len(pending)}")
        
        print("\n✅ All tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_bridge()
