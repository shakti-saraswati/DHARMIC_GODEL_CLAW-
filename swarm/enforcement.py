#!/usr/bin/env python3
"""
DHARMIC_CLAW Protocol v3 - Enforcement Module

Wires rate limits, cost tracking, and file locking into the swarm orchestrator.
This module loads policy YAML files and provides enforcement functions.

Usage:
    from swarm.enforcement import ProposalEnforcer

    enforcer = ProposalEnforcer()
    if enforcer.can_propose(agent_id="CODING_AGENT"):
        # Proceed with proposal
        pass
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import logging

# =============================================================================
# CONSTANTS
# =============================================================================

POLICY_DIR = Path(__file__).parent / "policy"
TRACKING_DIR = Path(__file__).parent.parent / "logs" / "enforcement"

logger = logging.getLogger(__name__)

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ProposalRecord:
    """Record of a proposal attempt."""
    timestamp: str
    agent_id: str
    proposal_id: str
    success: bool
    cost_usd: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0

@dataclass
class EnforcementResult:
    """Result of an enforcement check."""
    allowed: bool
    reason: str = ""
    wait_seconds: int = 0
    budget_remaining_usd: float = 0.0

# =============================================================================
# POLICY LOADER
# =============================================================================

def load_policy(name: str) -> Dict[str, Any]:
    """Load a policy YAML file."""
    policy_file = POLICY_DIR / f"{name}.yaml"
    if not policy_file.exists():
        logger.warning(f"Policy file not found: {policy_file}")
        return {}

    with open(policy_file) as f:
        return yaml.safe_load(f) or {}

# =============================================================================
# PROPOSAL ENFORCER
# =============================================================================

class ProposalEnforcer:
    """
    Enforces rate limits and budget controls on proposals.

    Loads policy from:
    - swarm/policy/proposal_limits.yaml
    - swarm/policy/cost_tracking.yaml
    """

    def __init__(self):
        self.proposal_limits = load_policy("proposal_limits")
        self.cost_tracking = load_policy("cost_tracking")
        self.tracking_dir = TRACKING_DIR
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize tracking state
        self.state_file = self.tracking_dir / "enforcement_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load tracking state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load enforcement state: {e}")

        return {
            "proposals": [],
            "daily_cost_usd": 0.0,
            "daily_reset": datetime.utcnow().date().isoformat(),
            "consecutive_failures": 0,
            "last_rejection": None
        }

    def _save_state(self):
        """Save tracking state to disk."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save enforcement state: {e}")

    def _reset_daily_if_needed(self):
        """Reset daily counters if it's a new day."""
        today = datetime.utcnow().date().isoformat()
        if self.state.get("daily_reset") != today:
            self.state["proposals"] = [
                p for p in self.state.get("proposals", [])
                if p.get("timestamp", "").startswith(today)
            ]
            self.state["daily_cost_usd"] = 0.0
            self.state["daily_reset"] = today
            self._save_state()

    def _get_recent_proposals(self, hours: int = 1) -> List[Dict]:
        """Get proposals from the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        return [
            p for p in self.state.get("proposals", [])
            if p.get("timestamp", "") >= cutoff_str
        ]

    def can_propose(self, agent_id: str = "CODING_AGENT") -> EnforcementResult:
        """
        Check if a new proposal is allowed.

        Checks:
        1. Hourly rate limit
        2. Daily rate limit
        3. Cooldown after rejection
        4. Budget limits
        5. Agent-specific limits
        """
        self._reset_daily_if_needed()

        limits = self.proposal_limits.get("proposal_limits", {})
        budget = self.cost_tracking.get("budget", {})
        agent_limits = self.proposal_limits.get("agent_limits", {}).get(agent_id, {})

        # Check cooldown after rejection
        if self.state.get("last_rejection"):
            cooldown_str = limits.get("cooldown_after_rejection", "2h")
            cooldown_hours = int(cooldown_str.replace("h", ""))
            cooldown_until = datetime.fromisoformat(self.state["last_rejection"]) + timedelta(hours=cooldown_hours)

            if datetime.utcnow() < cooldown_until:
                wait = int((cooldown_until - datetime.utcnow()).total_seconds())
                return EnforcementResult(
                    allowed=False,
                    reason=f"In cooldown after rejection ({wait}s remaining)",
                    wait_seconds=wait
                )

        # Check consecutive failures cooldown
        fail_threshold = limits.get("consecutive_failure_threshold", 3)
        if self.state.get("consecutive_failures", 0) >= fail_threshold:
            cooldown_str = limits.get("cooldown_after_consecutive_failures", "4h")
            cooldown_hours = int(cooldown_str.replace("h", ""))
            # For simplicity, use last rejection time
            if self.state.get("last_rejection"):
                cooldown_until = datetime.fromisoformat(self.state["last_rejection"]) + timedelta(hours=cooldown_hours)
                if datetime.utcnow() < cooldown_until:
                    wait = int((cooldown_until - datetime.utcnow()).total_seconds())
                    return EnforcementResult(
                        allowed=False,
                        reason=f"Consecutive failures cooldown ({wait}s remaining)",
                        wait_seconds=wait
                    )

        # Check hourly limit
        max_per_hour = limits.get("max_per_hour", 5)
        recent_hour = self._get_recent_proposals(hours=1)
        if len(recent_hour) >= max_per_hour:
            return EnforcementResult(
                allowed=False,
                reason=f"Hourly limit reached ({len(recent_hour)}/{max_per_hour})",
                wait_seconds=3600  # Wait an hour
            )

        # Check daily limit
        max_per_day = limits.get("max_per_day", 20)
        recent_day = self._get_recent_proposals(hours=24)
        if len(recent_day) >= max_per_day:
            return EnforcementResult(
                allowed=False,
                reason=f"Daily limit reached ({len(recent_day)}/{max_per_day})",
                wait_seconds=86400  # Wait a day
            )

        # Check agent-specific daily limit
        agent_daily_limit = agent_limits.get("daily_budget_proposals", max_per_day)
        agent_proposals_today = [
            p for p in recent_day
            if p.get("agent_id") == agent_id
        ]
        if len(agent_proposals_today) >= agent_daily_limit:
            return EnforcementResult(
                allowed=False,
                reason=f"Agent daily limit reached ({len(agent_proposals_today)}/{agent_daily_limit})",
                wait_seconds=86400
            )

        # Check budget
        daily_budget = budget.get("daily_budget_usd", 20.0)
        current_cost = self.state.get("daily_cost_usd", 0.0)
        critical_threshold = budget.get("alert_thresholds", {}).get("critical_percent", 90) / 100

        if current_cost >= daily_budget:
            return EnforcementResult(
                allowed=False,
                reason=f"Daily budget exhausted (${current_cost:.2f}/${daily_budget:.2f})",
                budget_remaining_usd=0.0
            )

        if current_cost >= daily_budget * critical_threshold:
            logger.warning(f"Budget at critical level: ${current_cost:.2f}/${daily_budget:.2f}")

        return EnforcementResult(
            allowed=True,
            budget_remaining_usd=daily_budget - current_cost
        )

    def record_proposal(
        self,
        proposal_id: str,
        agent_id: str = "CODING_AGENT",
        success: bool = True,
        cost_usd: float = 0.0,
        tokens_input: int = 0,
        tokens_output: int = 0
    ):
        """Record a proposal attempt."""
        self._reset_daily_if_needed()

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "proposal_id": proposal_id,
            "agent_id": agent_id,
            "success": success,
            "cost_usd": cost_usd,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output
        }

        self.state["proposals"].append(record)
        self.state["daily_cost_usd"] = self.state.get("daily_cost_usd", 0.0) + cost_usd

        if success:
            self.state["consecutive_failures"] = 0
            self.state["last_rejection"] = None
        else:
            self.state["consecutive_failures"] = self.state.get("consecutive_failures", 0) + 1
            self.state["last_rejection"] = datetime.utcnow().isoformat()

        self._save_state()
        logger.info(f"Recorded proposal {proposal_id}: success={success}, cost=${cost_usd:.4f}")

    def get_status(self) -> Dict[str, Any]:
        """Get current enforcement status."""
        self._reset_daily_if_needed()

        limits = self.proposal_limits.get("proposal_limits", {})
        budget = self.cost_tracking.get("budget", {})

        recent_hour = self._get_recent_proposals(hours=1)
        recent_day = self._get_recent_proposals(hours=24)

        return {
            "hourly_proposals": len(recent_hour),
            "hourly_limit": limits.get("max_per_hour", 5),
            "daily_proposals": len(recent_day),
            "daily_limit": limits.get("max_per_day", 20),
            "daily_cost_usd": self.state.get("daily_cost_usd", 0.0),
            "daily_budget_usd": budget.get("daily_budget_usd", 20.0),
            "consecutive_failures": self.state.get("consecutive_failures", 0),
            "in_cooldown": self.state.get("last_rejection") is not None
        }

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_enforcer: Optional[ProposalEnforcer] = None

def get_enforcer() -> ProposalEnforcer:
    """Get the singleton enforcer instance."""
    global _enforcer
    if _enforcer is None:
        _enforcer = ProposalEnforcer()
    return _enforcer

def can_propose(agent_id: str = "CODING_AGENT") -> EnforcementResult:
    """Check if a new proposal is allowed."""
    return get_enforcer().can_propose(agent_id)

def record_proposal(proposal_id: str, success: bool = True, cost_usd: float = 0.0):
    """Record a proposal attempt."""
    get_enforcer().record_proposal(proposal_id, success=success, cost_usd=cost_usd)
