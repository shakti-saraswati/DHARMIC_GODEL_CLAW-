"""
AUDIT LOGGING MODULE - WITNESS Gate Implementation
Provides immutable audit trail for all security-relevant events.
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from dataclasses import dataclass, asdict

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)

logger = logging.getLogger("agora.audit")

# Audit log location
AUDIT_LOG_PATH = Path(__file__).parent / "data" / "audit.jsonl"

EventType = Literal[
    "REGISTRATION",
    "AUTHENTICATION",
    "CHALLENGE_ISSUED",
    "CHALLENGE_VERIFIED",
    "TOKEN_ISSUED",
    "TOKEN_REVOKED",
    "ACCOUNT_DELETED",
    "KEY_ROTATED",
    "ACCESS_DENIED",
    "CONSENT_GRANTED",
    "CONSENT_REVOKED",
    "DATA_EXPORT",
    "ERROR",
]


@dataclass
class AuditEvent:
    """Immutable audit event record."""

    event_type: EventType
    timestamp: str
    actor: str  # Agent address or "SYSTEM"
    target: str | None  # Affected resource
    action: str  # Human-readable description
    metadata: dict[str, Any] | None
    previous_hash: str  # Chain integrity
    event_hash: str  # This event's hash

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditLog:
    """
    Append-only audit log with hash chain for tamper detection.
    Implements WITNESS gate requirements.
    """

    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or AUDIT_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._get_last_hash()

    def _get_last_hash(self) -> str:
        """Get the hash of the last event in the chain."""
        if not self.log_path.exists():
            return "GENESIS"

        try:
            with open(self.log_path, "rb") as f:
                # Read last line
                f.seek(0, 2)  # End of file
                size = f.tell()
                if size == 0:
                    return "GENESIS"

                # Find last newline
                f.seek(max(0, size - 4096), 0)
                lines = f.read().decode().strip().split("\n")
                if lines:
                    last_event = json.loads(lines[-1])
                    return last_event.get("event_hash", "GENESIS")
        except Exception:
            pass
        return "GENESIS"

    def _compute_hash(self, event_data: dict[str, Any]) -> str:
        """Compute SHA-256 hash of event data."""
        # Exclude event_hash from the hash computation
        data = {k: v for k, v in event_data.items() if k != "event_hash"}
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def log(
        self,
        event_type: EventType,
        actor: str,
        action: str,
        target: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """
        Record an audit event.

        Args:
            event_type: Type of event (REGISTRATION, AUTH, etc.)
            actor: Who initiated the action (agent address or SYSTEM)
            action: Human-readable description
            target: Affected resource (optional)
            metadata: Additional context (optional)

        Returns:
            The created AuditEvent
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build event without hash first
        event_data = {
            "event_type": event_type,
            "timestamp": timestamp,
            "actor": actor,
            "target": target,
            "action": action,
            "metadata": metadata,
            "previous_hash": self._last_hash,
        }

        # Compute and add hash
        event_hash = self._compute_hash(event_data)
        event_data["event_hash"] = event_hash

        event = AuditEvent(**event_data)

        # Append to log file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        # Update chain
        self._last_hash = event_hash

        # Also log to standard logger
        logger.info(f"[{event_type}] {actor}: {action}")

        return event

    def verify_chain(self) -> tuple[bool, list[str]]:
        """
        Verify the integrity of the audit chain.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []

        if not self.log_path.exists():
            return True, []

        previous_hash = "GENESIS"

        with open(self.log_path) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event = json.loads(line)

                    # Verify chain link
                    if event.get("previous_hash") != previous_hash:
                        errors.append(
                            f"Line {line_num}: Chain broken - expected {previous_hash}, "
                            f"got {event.get('previous_hash')}"
                        )

                    # Verify event hash
                    expected_hash = self._compute_hash(event)
                    if event.get("event_hash") != expected_hash:
                        errors.append(
                            f"Line {line_num}: Hash mismatch - expected {expected_hash}, "
                            f"got {event.get('event_hash')}"
                        )

                    previous_hash = event.get("event_hash", "")

                except json.JSONDecodeError:
                    errors.append(f"Line {line_num}: Invalid JSON")

        return len(errors) == 0, errors

    def get_events(
        self,
        event_type: EventType | None = None,
        actor: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit events with optional filters."""
        events: list[dict[str, Any]] = []

        if not self.log_path.exists():
            return events

        with open(self.log_path) as f:
            for line in f:
                try:
                    event = json.loads(line)

                    if event_type and event.get("event_type") != event_type:
                        continue
                    if actor and event.get("actor") != actor:
                        continue

                    events.append(event)

                    if len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue

        return events

    def export_for_agent(self, agent_address: str) -> list[dict[str, Any]]:
        """Export all audit events for a specific agent (GDPR compliance)."""
        return self.get_events(actor=agent_address, limit=10000)


# Global audit log instance
audit_log = AuditLog()


# Convenience functions
def log_registration(agent_address: str, name: str) -> AuditEvent:
    """Log agent registration."""
    return audit_log.log(
        event_type="REGISTRATION",
        actor=agent_address,
        action=f"Agent '{name}' registered",
        target=agent_address,
        metadata={"name": name},
    )


def log_authentication(agent_address: str, success: bool) -> AuditEvent:
    """Log authentication attempt."""
    return audit_log.log(
        event_type="AUTHENTICATION" if success else "ACCESS_DENIED",
        actor=agent_address,
        action=f"Authentication {'succeeded' if success else 'failed'}",
        target=agent_address,
        metadata={"success": success},
    )


def log_challenge(agent_address: str, challenge_id: str) -> AuditEvent:
    """Log challenge issuance."""
    return audit_log.log(
        event_type="CHALLENGE_ISSUED",
        actor="SYSTEM",
        action=f"Challenge issued to {agent_address[:16]}...",
        target=agent_address,
        metadata={"challenge_id": challenge_id},
    )


def log_token_issued(agent_address: str) -> AuditEvent:
    """Log JWT token issuance."""
    return audit_log.log(
        event_type="TOKEN_ISSUED",
        actor="SYSTEM",
        action=f"JWT token issued to {agent_address[:16]}...",
        target=agent_address,
    )


def log_account_deleted(agent_address: str, by_actor: str) -> AuditEvent:
    """Log account deletion."""
    return audit_log.log(
        event_type="ACCOUNT_DELETED",
        actor=by_actor,
        action=f"Account deleted for {agent_address[:16]}...",
        target=agent_address,
    )


def log_consent(agent_address: str, granted: bool, scope: str) -> AuditEvent:
    """Log consent grant/revoke."""
    return audit_log.log(
        event_type="CONSENT_GRANTED" if granted else "CONSENT_REVOKED",
        actor=agent_address,
        action=f"Consent {'granted' if granted else 'revoked'} for {scope}",
        target=agent_address,
        metadata={"scope": scope},
    )


def log_error(actor: str, error: str, context: dict[str, Any] | None = None) -> AuditEvent:
    """Log error event."""
    return audit_log.log(
        event_type="ERROR",
        actor=actor,
        action=f"Error: {error}",
        metadata=context,
    )
