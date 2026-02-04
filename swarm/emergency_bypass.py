#!/usr/bin/env python3
"""
DHARMIC_CLAW Protocol v3 - Emergency Bypass (Break-Glass)

Provides controlled bypass of non-critical gates for emergencies.
All bypasses are logged and require mandatory post-mortem.

Usage:
    python -m swarm.emergency_bypass --reason "Production down" --approver dhyana
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import hashlib

# =============================================================================
# CONSTANTS
# =============================================================================

EMERGENCY_LOG = Path(__file__).parent.parent / "logs" / "emergency_bypass.jsonl"
POSTMORTEM_DIR = Path(__file__).parent.parent / "postmortems"
BYPASS_COOLDOWN_HOURS = 24
MAX_BYPASSES_PER_WEEK = 3

# Gates that can NEVER be bypassed (absolute tier)
NON_BYPASSABLE_GATES = [
    "AHIMSA",      # Non-harm is absolute
    "LINT_FORMAT", # Basic code quality
    "TYPE_CHECK",  # Type safety
    "SECURITY_SCAN", # Security is non-negotiable
]

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BypassRequest:
    """Emergency bypass request."""
    request_id: str
    timestamp: str
    reason: str
    approver: str
    proposal_id: Optional[str]
    gates_bypassed: list[str]
    gates_still_run: list[str]
    status: str  # pending | approved | executed | postmortem_required | closed

@dataclass
class PostMortem:
    """Post-mortem record for a bypass."""
    bypass_id: str
    completed_at: str
    root_cause: str
    impact: str
    prevention_measures: list[str]
    follow_up_actions: list[str]
    reviewed_by: str

# =============================================================================
# BYPASS MANAGER
# =============================================================================

class EmergencyBypassManager:
    """
    Manages emergency bypass requests and post-mortems.
    
    Emergency bypass is a controlled mechanism to skip non-critical gates
    when production is down or there's an urgent security fix. It:
    
    1. Never bypasses AHIMSA or security gates
    2. Requires explicit human approval
    3. Logs everything to separate audit trail
    4. Enforces mandatory post-mortem
    5. Rate-limits to prevent abuse
    """
    
    def __init__(self):
        self.log_path = EMERGENCY_LOG
        self.postmortem_dir = POSTMORTEM_DIR
        
        # Ensure directories exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.postmortem_dir.mkdir(parents=True, exist_ok=True)
    
    def request_bypass(
        self,
        reason: str,
        approver: str,
        proposal_id: Optional[str] = None
    ) -> BypassRequest:
        """
        Request an emergency bypass.
        
        Args:
            reason: Why bypass is needed (must be substantive)
            approver: Human approver name
            proposal_id: Optional proposal this bypass is for
        
        Returns:
            BypassRequest with status
        
        Raises:
            ValueError: If request is invalid
            RuntimeError: If rate limit exceeded or cooldown active
        """
        # Validate reason
        if len(reason) < 20:
            raise ValueError("Reason must be substantive (>20 chars)")
        
        # Check rate limits
        self._check_rate_limits()
        
        # Generate request ID
        request_id = hashlib.md5(
            f"{datetime.now().isoformat()}{reason}".encode()
        ).hexdigest()[:12]
        
        # Determine which gates can be bypassed
        from swarm.run_gates import GateRunner
        runner = GateRunner()
        all_gates = [g["name"] for g in runner.config["gates"]]
        
        gates_bypassed = [
            g for g in all_gates
            if g not in NON_BYPASSABLE_GATES
        ]
        gates_still_run = NON_BYPASSABLE_GATES.copy()
        
        request = BypassRequest(
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            approver=approver,
            proposal_id=proposal_id,
            gates_bypassed=gates_bypassed,
            gates_still_run=gates_still_run,
            status="pending"
        )
        
        # Log the request
        self._log_event("bypass_requested", request)
        
        return request
    
    def approve_bypass(
        self,
        request_id: str,
        approver: str,
        confirmation: str
    ) -> BypassRequest:
        """
        Approve an emergency bypass request.
        
        Args:
            request_id: The bypass request ID
            approver: Human approver (must match request)
            confirmation: Must be "I APPROVE EMERGENCY BYPASS"
        
        Returns:
            Updated BypassRequest
        """
        if confirmation != "I APPROVE EMERGENCY BYPASS":
            raise ValueError("Must confirm with exact phrase: 'I APPROVE EMERGENCY BYPASS'")
        
        # Find the request
        request = self._find_request(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.approver != approver:
            raise ValueError(f"Approver mismatch: expected {request.approver}")
        
        request.status = "approved"
        self._log_event("bypass_approved", request)
        
        return request
    
    def execute_bypass(self, request_id: str) -> dict:
        """
        Execute an approved bypass.
        
        Returns the command to run gates with bypass.
        """
        request = self._find_request(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status != "approved":
            raise ValueError(f"Request not approved (status: {request.status})")
        
        request.status = "executed"
        self._log_event("bypass_executed", request)
        
        # Return the command to run
        cmd = [
            "python", "-m", "swarm.run_gates",
            f"--proposal-id={request.proposal_id or 'EMERGENCY'}",
            "--emergency",
            f"--reason={request.reason}",
            f"--approver={request.approver}"
        ]
        
        return {
            "command": " ".join(cmd),
            "request": asdict(request),
            "postmortem_due": (
                datetime.now(timezone.utc) + timedelta(hours=48)
            ).isoformat()
        }
    
    def submit_postmortem(
        self,
        bypass_id: str,
        root_cause: str,
        impact: str,
        prevention_measures: list[str],
        follow_up_actions: list[str],
        reviewed_by: str
    ) -> PostMortem:
        """
        Submit a post-mortem for a bypass.
        
        Post-mortems are MANDATORY within 48 hours.
        """
        postmortem = PostMortem(
            bypass_id=bypass_id,
            completed_at=datetime.now(timezone.utc).isoformat(),
            root_cause=root_cause,
            impact=impact,
            prevention_measures=prevention_measures,
            follow_up_actions=follow_up_actions,
            reviewed_by=reviewed_by
        )
        
        # Save post-mortem
        pm_path = self.postmortem_dir / f"{bypass_id}.json"
        with open(pm_path, "w") as f:
            json.dump(asdict(postmortem), f, indent=2)
        
        # Update request status
        request = self._find_request(bypass_id)
        if request:
            request.status = "closed"
            self._log_event("postmortem_submitted", {
                "bypass_id": bypass_id,
                "postmortem": asdict(postmortem)
            })
        
        return postmortem
    
    def check_pending_postmortems(self) -> list[dict]:
        """
        Check for bypasses missing post-mortems.
        
        Returns list of overdue post-mortems.
        """
        overdue = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        
        for entry in self._read_log():
            if entry.get("event") == "bypass_executed":
                request = entry.get("data", {})
                bypass_id = request.get("request_id")
                
                # Check if postmortem exists
                pm_path = self.postmortem_dir / f"{bypass_id}.json"
                if not pm_path.exists():
                    timestamp = datetime.fromisoformat(
                        request.get("timestamp", datetime.now().isoformat())
                    )
                    if timestamp < cutoff:
                        overdue.append({
                            "bypass_id": bypass_id,
                            "timestamp": request.get("timestamp"),
                            "reason": request.get("reason"),
                            "hours_overdue": (
                                datetime.now(timezone.utc) - timestamp
                            ).total_seconds() / 3600
                        })
        
        return overdue
    
    def _check_rate_limits(self) -> None:
        """Check if bypass rate limits are exceeded."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        cooldown_cutoff = now - timedelta(hours=BYPASS_COOLDOWN_HOURS)
        
        recent_bypasses = []
        last_bypass = None
        
        for entry in self._read_log():
            if entry.get("event") == "bypass_executed":
                timestamp = datetime.fromisoformat(
                    entry.get("data", {}).get("timestamp", "2000-01-01")
                )
                if timestamp > week_ago:
                    recent_bypasses.append(timestamp)
                if last_bypass is None or timestamp > last_bypass:
                    last_bypass = timestamp
        
        # Check weekly limit
        if len(recent_bypasses) >= MAX_BYPASSES_PER_WEEK:
            raise RuntimeError(
                f"Weekly bypass limit exceeded ({MAX_BYPASSES_PER_WEEK}). "
                f"Recent bypasses: {len(recent_bypasses)}"
            )
        
        # Check cooldown
        if last_bypass and last_bypass > cooldown_cutoff:
            remaining = (last_bypass + timedelta(hours=BYPASS_COOLDOWN_HOURS) - now)
            raise RuntimeError(
                f"Bypass cooldown active. Wait {remaining.total_seconds() / 3600:.1f} hours."
            )
    
    def _log_event(self, event: str, data: any) -> None:
        """Log an event to the audit trail."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "data": asdict(data) if hasattr(data, "__dataclass_fields__") else data
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def _read_log(self) -> list[dict]:
        """Read all log entries."""
        if not self.log_path.exists():
            return []
        
        entries = []
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return entries
    
    def _find_request(self, request_id: str) -> Optional[BypassRequest]:
        """Find a bypass request by ID."""
        for entry in reversed(self._read_log()):
            data = entry.get("data", {})
            if data.get("request_id") == request_id:
                return BypassRequest(**data)
        return None


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Emergency Bypass Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Request a bypass
    python -m swarm.emergency_bypass request \\
        --reason "Production API returning 500s, need hotfix" \\
        --approver dhyana
    
    # Approve a bypass
    python -m swarm.emergency_bypass approve \\
        --request-id abc123 \\
        --approver dhyana
    
    # Check for overdue post-mortems
    python -m swarm.emergency_bypass check-postmortems
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Request command
    req_parser = subparsers.add_parser("request", help="Request a bypass")
    req_parser.add_argument("--reason", required=True, help="Reason for bypass")
    req_parser.add_argument("--approver", required=True, help="Human approver")
    req_parser.add_argument("--proposal-id", help="Proposal ID")
    
    # Approve command
    app_parser = subparsers.add_parser("approve", help="Approve a bypass")
    app_parser.add_argument("--request-id", required=True, help="Request ID")
    app_parser.add_argument("--approver", required=True, help="Approver name")
    
    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute approved bypass")
    exec_parser.add_argument("--request-id", required=True, help="Request ID")
    
    # Check postmortems
    subparsers.add_parser("check-postmortems", help="Check for overdue post-mortems")
    
    args = parser.parse_args()
    manager = EmergencyBypassManager()
    
    if args.command == "request":
        request = manager.request_bypass(
            reason=args.reason,
            approver=args.approver,
            proposal_id=args.proposal_id
        )
        print(f"\n✓ Bypass requested")
        print(f"  Request ID: {request.request_id}")
        print(f"  Status: {request.status}")
        print(f"\nGates that will STILL run (non-bypassable):")
        for g in request.gates_still_run:
            print(f"  - {g}")
        print(f"\nGates that will be bypassed:")
        for g in request.gates_bypassed:
            print(f"  - {g}")
        print(f"\nTo approve, run:")
        print(f"  python -m swarm.emergency_bypass approve --request-id {request.request_id} --approver {args.approver}")
        
    elif args.command == "approve":
        print("\n⚠️  EMERGENCY BYPASS APPROVAL")
        print("This will skip non-critical gates. A post-mortem is MANDATORY.")
        confirm = input("\nType 'I APPROVE EMERGENCY BYPASS' to confirm: ")
        
        request = manager.approve_bypass(
            request_id=args.request_id,
            approver=args.approver,
            confirmation=confirm
        )
        print(f"\n✓ Bypass approved: {request.request_id}")
        print(f"\nTo execute, run:")
        print(f"  python -m swarm.emergency_bypass execute --request-id {request.request_id}")
        
    elif args.command == "execute":
        result = manager.execute_bypass(args.request_id)
        print(f"\n✓ Bypass executed")
        print(f"\nRun this command:")
        print(f"  {result['command']}")
        print(f"\n⚠️  POST-MORTEM DUE: {result['postmortem_due']}")
        
    elif args.command == "check-postmortems":
        overdue = manager.check_pending_postmortems()
        if not overdue:
            print("✓ No overdue post-mortems")
        else:
            print(f"⚠️  {len(overdue)} OVERDUE POST-MORTEMS:")
            for pm in overdue:
                print(f"\n  Bypass: {pm['bypass_id']}")
                print(f"  Reason: {pm['reason']}")
                print(f"  Hours overdue: {pm['hours_overdue']:.1f}")


if __name__ == "__main__":
    main()
