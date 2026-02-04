"""
PSMV policy enforcement and audit logging.

Principles (Induction Prompt v7):
1) Immutability
2) Read before write
3) Ahimsa (non-harm)
4) Silence is valid
5) Critique before contribute
6) Consent for propagation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import os
import re


@dataclass
class PolicyDecision:
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AhimsaFilter:
    """Simple, conservative harm-pattern detector."""

    PATTERNS = [
        r"\bdelete\b",
        r"\bdestroy\b",
        r"\battack\b",
        r"\bexploit\b",
        r"\bexfiltrate\b",
        r"\bhack\b",
        r"\bmalware\b",
        r"\bphish\b",
        r"\bcredential\b",
        r"\bsteal\b",
    ]

    def __init__(self) -> None:
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.PATTERNS]

    def has_harm(self, text: str) -> bool:
        return any(p.search(text) for p in self._compiled)


class PSMVPolicy:
    """Policy engine for writes to the Persistent Semantic Memory Vault."""

    def __init__(self) -> None:
        self.require_read = _env_bool("PSMV_REQUIRE_READ", True)
        self.require_consent = _env_bool("PSMV_REQUIRE_CONSENT", True)
        self.require_critique = _env_bool("PSMV_REQUIRE_CRITIQUE", True)
        self.min_chars = int(os.getenv("PSMV_MIN_CHARS", "200"))
        self.read_window_minutes = int(os.getenv("PSMV_READ_WINDOW_MINUTES", "180"))
        self.allow_unread = _env_bool("PSMV_ALLOW_UNREAD", False)
        self.allow_no_critique = _env_bool("PSMV_ALLOW_NO_CRITIQUE", False)
        self.allow_short = _env_bool("PSMV_ALLOW_SHORT", False)
        self.ahimsa = AhimsaFilter()

    def evaluate_write(
        self,
        content: str,
        consent: bool,
        critique: Optional[str],
        last_read_at: Optional[datetime],
        last_read_paths: Optional[List[str]] = None,
        force: bool = False,
    ) -> PolicyDecision:
        decision = PolicyDecision(allowed=True)

        if self.ahimsa.has_harm(content):
            decision.allowed = False
            decision.reasons.append("ahimsa_violation")
            return decision

        if self.require_consent and not consent and not _env_bool("PSMV_WRITE_CONSENT", False):
            decision.allowed = False
            decision.reasons.append("consent_required")

        if self.require_read and last_read_at is None:
            if self.allow_unread or force:
                decision.warnings.append("read_before_write_missing")
            else:
                decision.allowed = False
                decision.reasons.append("read_before_write_missing")
        elif self.require_read and last_read_at is not None:
            cutoff = datetime.now() - timedelta(minutes=self.read_window_minutes)
            if last_read_at < cutoff:
                if self.allow_unread or force:
                    decision.warnings.append("read_before_write_stale")
                else:
                    decision.allowed = False
                    decision.reasons.append("read_before_write_stale")

        if self.require_critique and not critique:
            if self.allow_no_critique or force:
                decision.warnings.append("critique_missing")
            else:
                decision.allowed = False
                decision.reasons.append("critique_missing")

        if len(content or "") < self.min_chars:
            if self.allow_short or force:
                decision.warnings.append("content_too_short")
            else:
                decision.allowed = False
                decision.reasons.append("content_too_short")

        return decision

    def log_audit(self, event: Dict[str, Any]) -> None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "psmv_audit.jsonl"
        event["timestamp"] = datetime.now().isoformat()
        with open(log_path, "a") as f:
            f.write(json.dumps(event) + "\n")


def _env_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")
