"""
Shared context system for agent communication with thread-safe operations.
"""

import threading
from typing import Any, Dict, Optional, Set, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import copy


@dataclass
class ContextEntry:
    """Single context entry with metadata."""
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    version: int = 1


class SharedContext:
    """Thread-safe shared context for agent communication."""
    
    def __init__(self) -> None:
        self._data: Dict[str, ContextEntry] = {}
        self._lock = threading.RLock()
        self._subscribers: Dict[str, Set[Callable[[str, Any], None]]] = {}
        self._access_log: List[Dict[str, Any]] = []
    
    def set(self, key: str, value: Any, agent_id: Optional[str] = None) -> None:
        """Set a context value with optional agent tracking."""
        with self._lock:
            old_entry = self._data.get(key)
            version = (old_entry.version + 1) if old_entry else 1
            
            self._data[key] = ContextEntry(
                value=value,
                timestamp=datetime.now(),
                agent_id=agent_id,
                version=version
            )
            
            self._log_access("set", key, agent_id)
            self._notify_subscribers(key, value)
    
    def get(self, key: str, default: Any = None, agent_id: Optional[str] = None) -> Any:
        """Get a context value with optional default."""
        with self._lock:
            self._log_access("get", key, agent_id)
            entry = self._data.get(key)
            return entry.value if entry else default
    
    def get_with_metadata(self, key: str, agent_id: Optional[str] = None) -> Optional[ContextEntry]:
        """Get context entry with full metadata."""
        with self._lock:
            self._log_access("get_metadata", key, agent_id)
            entry = self._data.get(key)
            return copy.deepcopy(entry) if entry else None
    
    def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """Delete a context key. Returns True if key existed."""
        with self._lock:
            self._log_access("delete", key, agent_id)
            existed = key in self._data
            if existed:
                del self._data[key]
                self._notify_subscribers(key, None)
            return existed
    
    def keys(self) -> List[str]:
        """Get all context keys."""
        with self._lock:
            return list(self._data.keys())
    
    def update(self, updates: Dict[str, Any], agent_id: Optional[str] = None) -> None:
        """Update multiple keys atomically."""
        with self._lock:
            for key, value in updates.items():
                self.set(key, value, agent_id)
    
    def subscribe(self, key: str, callback: Callable[[str, Any], None]) -> None:
        """Subscribe to changes on a specific key."""
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = set()
            self._subscribers[key].add(callback)
    
    def unsubscribe(self, key: str, callback: Callable[[str, Any], None]) -> None:
        """Unsubscribe from key changes."""
        with self._lock:
            if key in self._subscribers:
                self._subscribers[key].discard(callback)
                if not self._subscribers[key]:
                    del self._subscribers[key]
    
    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get recent access log entries."""
        with self._lock:
            return copy.deepcopy(self._access_log[-100:])  # Last 100 entries
    
    def clear(self, agent_id: Optional[str] = None) -> None:
        """Clear all context data."""
        with self._lock:
            self._data.clear()
            self._log_access("clear", "*", agent_id)
    
    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current context values."""
        with self._lock:
            return {key: entry.value for key, entry in self._data.items()}
    
    def restore_snapshot(self, snapshot: Dict[str, Any], agent_id: Optional[str] = None) -> None:
        """Restore context from a snapshot."""
        with self._lock:
            self._data.clear()
            for key, value in snapshot.items():
                self._data[key] = ContextEntry(
                    value=value,
                    timestamp=datetime.now(),
                    agent_id=agent_id,
                    version=1
                )
            self._log_access("restore", "*", agent_id)
    
    def _notify_subscribers(self, key: str, value: Any) -> None:
        """Notify subscribers of key changes."""
        if key in self._subscribers:
            for callback in self._subscribers[key].copy():
                try:
                    callback(key, value)
                except Exception:
                    # Remove broken callbacks
                    self._subscribers[key].discard(callback)
    
    def _log_access(self, operation: str, key: str, agent_id: Optional[str]) -> None:
        """Log context access for debugging."""
        self._access_log.append({
            "operation": operation,
            "key": key,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep log size manageable
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-500:]


# Global shared context instance
global_context = SharedContext()