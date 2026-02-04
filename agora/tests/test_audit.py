#!/usr/bin/env python3
"""
DHARMIC_AGORA Audit Log Tests

Tests the WITNESS gate implementation:
- Event logging
- Hash chain integrity
- Chain verification
- Event querying
- Tamper detection
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit import (
    AuditLog,
    AuditEvent,
    log_registration,
    log_authentication,
    log_challenge,
    log_token_issued,
    log_account_deleted,
    log_consent,
    log_error,
)


@pytest.fixture
def temp_log():
    """Create temporary log file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def audit(temp_log):
    """Create AuditLog instance with temp file."""
    return AuditLog(log_path=temp_log)


class TestAuditLogging:
    """Tests for basic audit logging."""

    def test_log_event(self, audit):
        """Can log a basic event."""
        event = audit.log(
            event_type="REGISTRATION",
            actor="test-agent-123",
            action="Agent registered",
            target="test-agent-123",
        )

        assert event.event_type == "REGISTRATION"
        assert event.actor == "test-agent-123"
        assert event.action == "Agent registered"
        assert event.previous_hash == "GENESIS"  # First event
        assert len(event.event_hash) == 16

    def test_log_with_metadata(self, audit):
        """Can log event with metadata."""
        event = audit.log(
            event_type="AUTHENTICATION",
            actor="test-agent",
            action="Auth succeeded",
            metadata={"ip": "127.0.0.1", "method": "challenge"},
        )

        assert event.metadata == {"ip": "127.0.0.1", "method": "challenge"}

    def test_events_form_chain(self, audit):
        """Events link together via previous_hash."""
        event1 = audit.log("REGISTRATION", "agent1", "Registered")
        event2 = audit.log("REGISTRATION", "agent2", "Registered")
        event3 = audit.log("AUTHENTICATION", "agent1", "Authenticated")

        # event2 should reference event1's hash
        assert event2.previous_hash == event1.event_hash
        # event3 should reference event2's hash
        assert event3.previous_hash == event2.event_hash


class TestChainVerification:
    """Tests for chain integrity verification."""

    def test_empty_chain_is_valid(self, audit):
        """Empty/new chain is valid."""
        valid, errors = audit.verify_chain()
        assert valid is True
        assert errors == []

    def test_valid_chain_verifies(self, audit):
        """Chain with valid events passes verification."""
        audit.log("REGISTRATION", "agent1", "Registered")
        audit.log("AUTHENTICATION", "agent1", "Authenticated")
        audit.log("TOKEN_ISSUED", "SYSTEM", "Token issued")

        valid, errors = audit.verify_chain()
        assert valid is True
        assert errors == []

    def test_tampered_chain_detected(self, audit, temp_log):
        """Tampered chain is detected."""
        # Create some events
        audit.log("REGISTRATION", "agent1", "Registered")
        audit.log("AUTHENTICATION", "agent1", "Authenticated")

        # Tamper with the log file
        lines = temp_log.read_text().strip().split("\n")
        event = json.loads(lines[0])
        event["action"] = "TAMPERED!"
        lines[0] = json.dumps(event)
        temp_log.write_text("\n".join(lines) + "\n")

        # Verification should fail
        new_audit = AuditLog(log_path=temp_log)
        valid, errors = new_audit.verify_chain()
        assert valid is False
        assert len(errors) > 0


class TestEventQuerying:
    """Tests for querying events."""

    def test_get_events_by_type(self, audit):
        """Can filter events by type."""
        audit.log("REGISTRATION", "agent1", "Registered")
        audit.log("AUTHENTICATION", "agent1", "Authenticated")
        audit.log("REGISTRATION", "agent2", "Registered")

        events = audit.get_events(event_type="REGISTRATION")
        assert len(events) == 2

        events = audit.get_events(event_type="AUTHENTICATION")
        assert len(events) == 1

    def test_get_events_by_actor(self, audit):
        """Can filter events by actor."""
        audit.log("REGISTRATION", "agent1", "Registered")
        audit.log("AUTHENTICATION", "agent1", "Authenticated")
        audit.log("REGISTRATION", "agent2", "Registered")

        events = audit.get_events(actor="agent1")
        assert len(events) == 2

    def test_get_events_with_limit(self, audit):
        """Limit parameter works."""
        for i in range(10):
            audit.log("REGISTRATION", f"agent{i}", "Registered")

        events = audit.get_events(limit=5)
        assert len(events) == 5

    def test_export_for_agent(self, audit):
        """Can export all events for an agent."""
        audit.log("REGISTRATION", "agent1", "Registered")
        audit.log("AUTHENTICATION", "agent1", "Auth")
        audit.log("TOKEN_ISSUED", "agent1", "Token")
        audit.log("REGISTRATION", "agent2", "Registered")

        export = audit.export_for_agent("agent1")
        assert len(export) == 3


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_log_registration(self, monkeypatch, temp_log):
        """log_registration convenience function works."""
        from audit import audit_log
        monkeypatch.setattr("audit.audit_log", AuditLog(temp_log))

        # Import again to use patched version
        from audit import log_registration as lr
        event = lr("agent-abc", "TestAgent")

        assert event.event_type == "REGISTRATION"
        assert "TestAgent" in event.action

    def test_log_authentication(self, monkeypatch, temp_log):
        """log_authentication convenience function works."""
        from audit import audit_log
        audit = AuditLog(temp_log)
        monkeypatch.setattr("audit.audit_log", audit)

        from audit import log_authentication as la
        event_success = la("agent-abc", success=True)
        event_fail = la("agent-xyz", success=False)

        assert event_success.event_type == "AUTHENTICATION"
        assert event_fail.event_type == "ACCESS_DENIED"


class TestPersistence:
    """Tests for log persistence."""

    def test_events_persist_across_instances(self, temp_log):
        """Events survive creating new AuditLog instance."""
        audit1 = AuditLog(temp_log)
        audit1.log("REGISTRATION", "agent1", "Registered")
        audit1.log("AUTHENTICATION", "agent1", "Authenticated")

        # Create new instance
        audit2 = AuditLog(temp_log)
        events = audit2.get_events()

        assert len(events) == 2

    def test_chain_continues_across_instances(self, temp_log):
        """Chain continues properly with new instance."""
        audit1 = AuditLog(temp_log)
        event1 = audit1.log("REGISTRATION", "agent1", "Registered")

        audit2 = AuditLog(temp_log)
        event2 = audit2.log("AUTHENTICATION", "agent1", "Authenticated")

        # event2 should reference event1
        assert event2.previous_hash == event1.event_hash

        # Full chain should verify
        valid, errors = audit2.verify_chain()
        assert valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
