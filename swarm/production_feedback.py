#!/usr/bin/env python3
"""
DHARMIC_CLAW Protocol v3 - Production Feedback Loop

Tracks the real-world impact of changes after deployment.
Feeds back into proposal scoring and risk assessment.

The 7-day audit answers: "Did this change work in production?"
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Any
import hashlib
from swarm.cybernetics import evaluate_control, asdict_signal
from swarm import systemic_monitor

# =============================================================================
# CONSTANTS
# =============================================================================

FEEDBACK_DIR = Path(__file__).parent.parent / "logs" / "production_feedback"
INTERACTION_LOG = Path(__file__).parent.parent / "logs" / "interaction_events.jsonl"
REMINDER_HOURS = [24, 72, 168]  # 1 day, 3 days, 7 days

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ProductionMetrics:
    """Metrics collected from production."""
    errors_introduced: int = 0
    error_rate_change_percent: float = 0.0
    performance_delta_percent: float = 0.0
    latency_p50_change_ms: float = 0.0
    latency_p99_change_ms: float = 0.0
    rollback_needed: bool = False
    rollback_reason: Optional[str] = None
    user_complaints: int = 0
    alerts_triggered: int = 0

@dataclass
class FeedbackRecord:
    """Complete feedback record for a deployed change."""
    proposal_id: str
    deployed_at: str
    feedback_collected_at: Optional[str] = None
    days_in_production: int = 0
    status: str = "monitoring"  # monitoring | stable | problematic | rolled_back
    metrics: ProductionMetrics = field(default_factory=ProductionMetrics)
    notes: list[str] = field(default_factory=list)
    final_verdict: Optional[str] = None  # success | partial_success | failure
    lessons_learned: list[str] = field(default_factory=list)
    control_state: dict[str, Any] = field(default_factory=dict)
    systemic_risk: dict[str, Any] = field(default_factory=dict)

@dataclass
class FeedbackReminder:
    """Reminder to collect feedback."""
    proposal_id: str
    reminder_type: str  # day_1 | day_3 | day_7
    due_at: str
    sent: bool = False

# =============================================================================
# FEEDBACK MANAGER
# =============================================================================

class ProductionFeedbackManager:
    """
    Manages the production feedback loop.
    
    After a change is deployed:
    1. Day 1: Initial smoke test - any immediate issues?
    2. Day 3: Short-term stability - error rates, performance
    3. Day 7: Full audit - comprehensive metrics review
    
    This data feeds back into:
    - Proposal scoring (successful changes boost author reputation)
    - Risk assessment (problematic patterns increase risk scores)
    - Gate calibration (if gates miss issues, they need tuning)
    """
    
    def __init__(self):
        self.feedback_dir = FEEDBACK_DIR
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
    
    def register_deployment(self, proposal_id: str) -> FeedbackRecord:
        """
        Register a new deployment for tracking.
        
        Call this when a proposal is merged and deployed.
        """
        record = FeedbackRecord(
            proposal_id=proposal_id,
            deployed_at=datetime.now(timezone.utc).isoformat(),
            status="monitoring"
        )
        
        self._save_record(record)
        self._schedule_reminders(record)
        
        return record
    
    def record_metrics(
        self,
        proposal_id: str,
        metrics: ProductionMetrics,
        notes: Optional[list[str]] = None
    ) -> FeedbackRecord:
        """
        Record production metrics for a deployment.
        
        Can be called multiple times as data becomes available.
        """
        record = self._load_record(proposal_id)
        if not record:
            raise ValueError(f"No deployment record for: {proposal_id}")
        
        record.metrics = metrics
        record.feedback_collected_at = datetime.now(timezone.utc).isoformat()
        
        # Calculate days in production
        deployed = datetime.fromisoformat(record.deployed_at)
        record.days_in_production = (
            datetime.now(timezone.utc) - deployed
        ).days
        
        if notes:
            record.notes.extend(notes)

        # Cybernetics control loop evaluation
        try:
            control = evaluate_control(asdict(metrics))
            record.control_state = asdict_signal(control)
            if control.status == "unstable" and record.status not in ["rolled_back"]:
                record.status = "problematic"
        except Exception:
            pass

        # Systemic risk snapshot
        try:
            record.systemic_risk = self.capture_systemic_risk()
        except Exception:
            pass

        # Auto-update status based on metrics
        if metrics.rollback_needed:
            record.status = "rolled_back"
        elif metrics.errors_introduced > 0 or metrics.error_rate_change_percent > 10:
            record.status = "problematic"
        elif record.days_in_production >= 7:
            record.status = "stable"
        
        self._save_record(record)
        return record

    def capture_systemic_risk(self, events_path: Optional[Path] = None) -> dict:
        """Capture a systemic risk snapshot from interaction events."""
        events_path = events_path or INTERACTION_LOG
        events = systemic_monitor.load_events(events_path)
        policy = systemic_monitor.load_policy(None)
        report = systemic_monitor.evaluate(events, policy)

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": asdict(report.metrics),
            "flags": report.flags,
            "status": report.status,
        }

        out_path = self.feedback_dir / f"systemic_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        return payload
    
    def record_rollback(
        self,
        proposal_id: str,
        reason: str
    ) -> FeedbackRecord:
        """Record that a change was rolled back."""
        record = self._load_record(proposal_id)
        if not record:
            raise ValueError(f"No deployment record for: {proposal_id}")
        
        record.metrics.rollback_needed = True
        record.metrics.rollback_reason = reason
        record.status = "rolled_back"
        record.final_verdict = "failure"
        record.notes.append(f"ROLLBACK: {reason}")
        
        self._save_record(record)
        return record
    
    def complete_audit(
        self,
        proposal_id: str,
        verdict: str,
        lessons_learned: list[str]
    ) -> FeedbackRecord:
        """
        Complete the 7-day audit.
        
        Args:
            proposal_id: The proposal ID
            verdict: "success" | "partial_success" | "failure"
            lessons_learned: What we learned from this deployment
        """
        record = self._load_record(proposal_id)
        if not record:
            raise ValueError(f"No deployment record for: {proposal_id}")
        
        record.final_verdict = verdict
        record.lessons_learned = lessons_learned
        
        if verdict == "success":
            record.status = "stable"
        elif verdict == "failure":
            record.status = "problematic"
        
        self._save_record(record)
        
        # Update scoring model
        self._update_proposal_scoring(record)
        
        return record
    
    def get_pending_audits(self) -> list[FeedbackRecord]:
        """Get deployments needing audit."""
        pending = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        for record_file in self.feedback_dir.glob("*.json"):
            if record_file.name.startswith("reminder_"):
                continue
            
            record = self._load_record(record_file.stem)
            if not record:
                continue
            
            # Check if audit needed
            deployed = datetime.fromisoformat(record.deployed_at)
            if (
                record.final_verdict is None and
                deployed < cutoff and
                record.status not in ["rolled_back"]
            ):
                pending.append(record)
        
        return pending
    
    def get_reminders_due(self) -> list[FeedbackReminder]:
        """Get reminders that are due to be sent."""
        due = []
        now = datetime.now(timezone.utc)
        
        for reminder_file in self.feedback_dir.glob("reminder_*.json"):
            with open(reminder_file) as f:
                data = json.load(f)
            
            reminder = FeedbackReminder(**data)
            if not reminder.sent:
                due_at = datetime.fromisoformat(reminder.due_at)
                if due_at <= now:
                    due.append(reminder)
        
        return due
    
    def mark_reminder_sent(self, proposal_id: str, reminder_type: str) -> None:
        """Mark a reminder as sent."""
        reminder_path = self.feedback_dir / f"reminder_{proposal_id}_{reminder_type}.json"
        if reminder_path.exists():
            with open(reminder_path) as f:
                data = json.load(f)
            data["sent"] = True
            with open(reminder_path, "w") as f:
                json.dump(data, f, indent=2)
    
    def get_statistics(self, days: int = 30) -> dict:
        """
        Get feedback statistics for the last N days.
        
        Returns metrics useful for tuning gates and risk assessment.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        total = 0
        successes = 0
        failures = 0
        rollbacks = 0
        errors_introduced = 0
        avg_performance_delta = []
        
        for record_file in self.feedback_dir.glob("*.json"):
            if record_file.name.startswith("reminder_"):
                continue
            
            record = self._load_record(record_file.stem)
            if not record:
                continue
            
            deployed = datetime.fromisoformat(record.deployed_at)
            if deployed < cutoff:
                continue
            
            total += 1
            
            if record.final_verdict == "success":
                successes += 1
            elif record.final_verdict == "failure":
                failures += 1
            
            if record.metrics.rollback_needed:
                rollbacks += 1
            
            errors_introduced += record.metrics.errors_introduced
            if record.metrics.performance_delta_percent != 0:
                avg_performance_delta.append(record.metrics.performance_delta_percent)
        
        return {
            "period_days": days,
            "total_deployments": total,
            "successes": successes,
            "failures": failures,
            "rollbacks": rollbacks,
            "success_rate": successes / total if total > 0 else 0,
            "rollback_rate": rollbacks / total if total > 0 else 0,
            "total_errors_introduced": errors_introduced,
            "avg_performance_delta_percent": (
                sum(avg_performance_delta) / len(avg_performance_delta)
                if avg_performance_delta else 0
            )
        }
    
    def _save_record(self, record: FeedbackRecord) -> None:
        """Save a feedback record."""
        path = self.feedback_dir / f"{record.proposal_id}.json"
        with open(path, "w") as f:
            json.dump(asdict(record), f, indent=2)
    
    def _load_record(self, proposal_id: str) -> Optional[FeedbackRecord]:
        """Load a feedback record."""
        path = self.feedback_dir / f"{proposal_id}.json"
        if not path.exists():
            return None
        
        with open(path) as f:
            data = json.load(f)
        
        # Handle nested metrics
        if "metrics" in data and isinstance(data["metrics"], dict):
            data["metrics"] = ProductionMetrics(**data["metrics"])
        
        return FeedbackRecord(**data)
    
    def _schedule_reminders(self, record: FeedbackRecord) -> None:
        """Schedule feedback reminders."""
        deployed = datetime.fromisoformat(record.deployed_at)
        
        reminder_types = [
            ("day_1", 24),
            ("day_3", 72),
            ("day_7", 168)
        ]
        
        for reminder_type, hours in reminder_types:
            due_at = deployed + timedelta(hours=hours)
            reminder = FeedbackReminder(
                proposal_id=record.proposal_id,
                reminder_type=reminder_type,
                due_at=due_at.isoformat(),
                sent=False
            )
            
            path = self.feedback_dir / f"reminder_{record.proposal_id}_{reminder_type}.json"
            with open(path, "w") as f:
                json.dump(asdict(reminder), f, indent=2)
    
    def _update_proposal_scoring(self, record: FeedbackRecord) -> None:
        """Update proposal scoring model based on feedback."""
        # This would update a scoring model used by the swarm
        # For now, just log the update
        score_update = {
            "proposal_id": record.proposal_id,
            "verdict": record.final_verdict,
            "metrics": asdict(record.metrics),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        scoring_log = self.feedback_dir / "scoring_updates.jsonl"
        with open(scoring_log, "a") as f:
            f.write(json.dumps(score_update) + "\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Feedback Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register deployment
    reg_parser = subparsers.add_parser("register", help="Register a deployment")
    reg_parser.add_argument("--proposal-id", required=True)
    
    # Record metrics
    met_parser = subparsers.add_parser("metrics", help="Record metrics")
    met_parser.add_argument("--proposal-id", required=True)
    met_parser.add_argument("--errors", type=int, default=0)
    met_parser.add_argument("--error-rate-change", type=float, default=0.0)
    met_parser.add_argument("--perf-delta", type=float, default=0.0)
    met_parser.add_argument("--note", action="append")
    
    # Record rollback
    roll_parser = subparsers.add_parser("rollback", help="Record rollback")
    roll_parser.add_argument("--proposal-id", required=True)
    roll_parser.add_argument("--reason", required=True)
    
    # Complete audit
    audit_parser = subparsers.add_parser("audit", help="Complete 7-day audit")
    audit_parser.add_argument("--proposal-id", required=True)
    audit_parser.add_argument("--verdict", choices=["success", "partial_success", "failure"])
    audit_parser.add_argument("--lesson", action="append")
    
    # Check pending
    subparsers.add_parser("pending", help="Show pending audits")
    
    # Statistics
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--days", type=int, default=30)

    # Systemic risk snapshot
    sys_parser = subparsers.add_parser("systemic", help="Capture systemic risk snapshot")
    sys_parser.add_argument("--events", help="Path to interaction events JSONL")
    
    args = parser.parse_args()
    manager = ProductionFeedbackManager()
    
    if args.command == "register":
        record = manager.register_deployment(args.proposal_id)
        print(f"✓ Registered deployment: {args.proposal_id}")
        print(f"  Deployed at: {record.deployed_at}")
        print(f"  Status: {record.status}")
        print(f"\nReminders scheduled for: Day 1, Day 3, Day 7")
        
    elif args.command == "metrics":
        metrics = ProductionMetrics(
            errors_introduced=args.errors,
            error_rate_change_percent=args.error_rate_change,
            performance_delta_percent=args.perf_delta
        )
        record = manager.record_metrics(
            args.proposal_id,
            metrics,
            notes=args.note
        )
        print(f"✓ Metrics recorded for: {args.proposal_id}")
        print(f"  Status: {record.status}")
        print(f"  Days in production: {record.days_in_production}")
        
    elif args.command == "rollback":
        record = manager.record_rollback(args.proposal_id, args.reason)
        print(f"⚠️  Rollback recorded: {args.proposal_id}")
        print(f"  Reason: {args.reason}")
        
    elif args.command == "audit":
        record = manager.complete_audit(
            args.proposal_id,
            args.verdict,
            args.lesson or []
        )
        print(f"✓ Audit completed: {args.proposal_id}")
        print(f"  Verdict: {record.final_verdict}")
        
    elif args.command == "pending":
        pending = manager.get_pending_audits()
        if not pending:
            print("✓ No pending audits")
        else:
            print(f"⚠️  {len(pending)} PENDING AUDITS:")
            for record in pending:
                print(f"\n  {record.proposal_id}")
                print(f"    Deployed: {record.deployed_at}")
                print(f"    Days: {record.days_in_production}")
                print(f"    Status: {record.status}")
        
    elif args.command == "stats":
        stats = manager.get_statistics(args.days)
        print(f"\nProduction Feedback Statistics ({args.days} days)")
        print(f"{'='*40}")
        print(f"Total deployments: {stats['total_deployments']}")
        print(f"Successes: {stats['successes']}")
        print(f"Failures: {stats['failures']}")
        print(f"Rollbacks: {stats['rollbacks']}")
        print(f"Success rate: {stats['success_rate']:.1%}")
        print(f"Rollback rate: {stats['rollback_rate']:.1%}")
        print(f"Errors introduced: {stats['total_errors_introduced']}")
        print(f"Avg perf delta: {stats['avg_performance_delta_percent']:.2f}%")

    elif args.command == "systemic":
        events_path = Path(args.events) if args.events else None
        report = manager.capture_systemic_risk(events_path)
        print("Systemic risk snapshot recorded")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
