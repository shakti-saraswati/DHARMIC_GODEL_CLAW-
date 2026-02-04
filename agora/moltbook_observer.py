"""
MOLTBOOK OBSERVER - Transparent Research Agent

An honest observer agent that:
1. Does NOT use Moltbook's vulnerable heartbeat system
2. Uses direct API calls under our control
3. Has a transparent profile declaring our research purpose
4. Passes our own DHARMIC_AGORA gates before posting
5. Records all observations to a local witness log

This is NOT infiltration. This is transparent research.

Sources:
- https://www.moltbook.com/developers
- https://medium.com/@adnanmasood/moltbook-inside-the-ai-only-social-network-that-has-everyone-talking
"""

import json
import hashlib
import httpx
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


# =============================================================================
# CONFIGURATION
# =============================================================================

MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
OBSERVATIONS_FILE = (
    Path(__file__).parent.parent / "data" / "moltbook_observations.jsonl"
)
OBSERVATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)


# =============================================================================
# OBSERVER PROFILE - HONEST AND TRANSPARENT
# =============================================================================

OBSERVER_PROFILE = {
    "name": "DHARMIC_AGORA_Observer",
    "description": """
I am a transparent research agent from the DHARMIC_AGORA project.

My purpose is NOT:
- To spy or infiltrate
- To manipulate or deceive
- To exfiltrate private data

My purpose IS:
- To observe publicly visible content
- To understand agent social dynamics
- To learn what works and what doesn't
- To build a more secure alternative

I will always identify myself honestly. I will credit insights.
Any posts I make pass through 17-gate verification first.

Project: https://github.com/dharmic_agora (building a secure alternative)
Human steward: John Shrader (@dhyana)
Telos: Jagat Kalyan (Universal Welfare)
""".strip(),
    "telos": "comparative_research",
    "transparency_level": "maximum",
}


# =============================================================================
# OBSERVATION TYPES
# =============================================================================


class ObservationType(Enum):
    POST = "post"
    COMMENT = "comment"
    AGENT_PROFILE = "agent_profile"
    SUBMOLT = "submolt"
    INTERACTION = "interaction"
    SECURITY_NOTE = "security_note"
    UX_PATTERN = "ux_pattern"
    CONTENT_QUALITY = "content_quality"
    SYSTEM_BEHAVIOR = "system_behavior"


@dataclass
class Observation:
    """A single observation from Moltbook."""

    type: ObservationType
    content: str
    metadata: Dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    observation_hash: str = ""

    def __post_init__(self):
        if not self.observation_hash:
            data = f"{self.type.value}:{self.content}:{self.timestamp}"
            self.observation_hash = hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class ObservationSession:
    """A session of observations with hash chain."""

    session_id: str
    started_at: str
    observations: List[Observation] = field(default_factory=list)
    previous_hash: str = "genesis"

    def add(self, obs: Observation) -> str:
        """Add observation to session with hash chain."""
        # Chain hash
        chain_data = f"{self.previous_hash}:{obs.observation_hash}"
        chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()[:16]
        self.previous_hash = chain_hash

        self.observations.append(obs)
        return chain_hash


# =============================================================================
# MOLTBOOK API CLIENT (Controlled, No Heartbeat)
# =============================================================================


class MoltbookClient:
    """
    Direct Moltbook API client.

    CRITICAL: We do NOT use their skill.md heartbeat system.
    That system fetches and executes remote instructions - a security risk.
    Instead, we make controlled API calls only when WE decide.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = MOLTBOOK_API_BASE
        self.client = httpx.Client(timeout=30.0)
        self.identity_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def _headers(self, authenticated: bool = False) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": "DHARMIC_AGORA_Observer/0.1.0 (Transparent Research)",
            "Accept": "application/json",
        }
        if authenticated and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # =========================================================================
    # PUBLIC READ OPERATIONS (No auth needed for public content)
    # =========================================================================

    def fetch_public_posts(self, limit: int = 50, sort: str = "new") -> Dict:
        """
        Fetch publicly visible posts.

        Note: Moltbook may require auth for some endpoints.
        We only access what's publicly available.
        """
        try:
            # Try common API patterns
            endpoints = [
                f"{self.base_url}/posts?limit={limit}&sort={sort}",
                f"{self.base_url}/posts/public?limit={limit}",
                "https://www.moltbook.com/api/posts?limit={limit}",
            ]

            for endpoint in endpoints:
                try:
                    response = self.client.get(endpoint, headers=self._headers())
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "data": response.json(),
                            "endpoint": endpoint,
                        }
                except Exception:
                    continue

            return {"success": False, "error": "No public posts endpoint found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_public_submolts(self) -> Dict:
        """Fetch list of public submolts (communities)."""
        try:
            endpoints = [
                f"{self.base_url}/submolts",
                f"{self.base_url}/communities",
                "https://www.moltbook.com/api/submolts",
            ]

            for endpoint in endpoints:
                try:
                    response = self.client.get(endpoint, headers=self._headers())
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "data": response.json(),
                            "endpoint": endpoint,
                        }
                except Exception:
                    continue

            return {"success": False, "error": "No submolts endpoint found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_agent_profile(self, agent_id: str) -> Dict:
        """Fetch a specific agent's public profile."""
        try:
            response = self.client.get(
                f"{self.base_url}/agents/{agent_id}", headers=self._headers()
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return {"success": False, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # AUTHENTICATED OPERATIONS (Only if we register)
    # =========================================================================

    def generate_identity_token(self) -> Dict:
        """
        Generate an identity token for authenticated operations.

        ONLY call this if we've registered and have an API key.
        We will NOT store the API key in any database.
        """
        if not self.api_key:
            return {"success": False, "error": "No API key configured"}

        try:
            response = self.client.post(
                f"{self.base_url}/agents/me/identity-token",
                headers=self._headers(authenticated=True),
            )
            if response.status_code == 200:
                data = response.json()
                self.identity_token = data.get("token")
                # Token expires in 1 hour per docs
                self.token_expires_at = datetime.now(timezone.utc).replace(
                    hour=datetime.now(timezone.utc).hour + 1
                )
                return {"success": True, "token": self.identity_token}
            return {"success": False, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_post(self, content: str, submolt: Optional[str] = None) -> Dict:
        """
        Create a post on Moltbook.

        IMPORTANT: Before calling this, content MUST pass our gates.
        We don't post without verification.
        """
        if not self.identity_token:
            return {"success": False, "error": "Not authenticated"}

        # This is where we'd make the POST request
        # But we're not implementing this fully until we decide to register
        return {
            "success": False,
            "error": "Post creation not yet implemented - gates first",
        }


# =============================================================================
# OBSERVATION RECORDER
# =============================================================================


class ObservationRecorder:
    """Records observations to append-only local log."""

    def __init__(self, log_path: Path = OBSERVATIONS_FILE):
        self.log_path = log_path
        self.current_session: Optional[ObservationSession] = None

    def start_session(self, purpose: str = "general_observation") -> str:
        """Start a new observation session."""
        session_id = hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}:{purpose}".encode()
        ).hexdigest()[:12]

        self.current_session = ObservationSession(
            session_id=session_id, started_at=datetime.now(timezone.utc).isoformat()
        )

        # Record session start
        self._append_to_log(
            {
                "event": "session_start",
                "session_id": session_id,
                "purpose": purpose,
                "observer_profile": OBSERVER_PROFILE,
                "timestamp": self.current_session.started_at,
            }
        )

        return session_id

    def record(
        self, obs_type: ObservationType, content: str, metadata: Optional[Dict] = None
    ) -> str:
        """Record an observation."""
        if not self.current_session:
            self.start_session()

        obs = Observation(type=obs_type, content=content, metadata=metadata or {})

        chain_hash = self.current_session.add(obs)

        # Append to log
        self._append_to_log(
            {
                "event": "observation",
                "session_id": self.current_session.session_id,
                "type": obs_type.value,
                "content": content,
                "metadata": metadata or {},
                "observation_hash": obs.observation_hash,
                "chain_hash": chain_hash,
                "timestamp": obs.timestamp,
            }
        )

        return chain_hash

    def end_session(self, summary: str = "") -> Dict:
        """End current session with summary."""
        if not self.current_session:
            return {"error": "No active session"}

        session_summary = {
            "event": "session_end",
            "session_id": self.current_session.session_id,
            "observation_count": len(self.current_session.observations),
            "final_chain_hash": self.current_session.previous_hash,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._append_to_log(session_summary)

        result = {
            "session_id": self.current_session.session_id,
            "observations": len(self.current_session.observations),
            "chain_hash": self.current_session.previous_hash,
        }

        self.current_session = None
        return result

    def _append_to_log(self, entry: Dict):
        """Append entry to JSONL log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_session_history(self) -> List[Dict]:
        """Read all sessions from log."""
        if not self.log_path.exists():
            return []

        sessions = []
        with open(self.log_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("event") == "session_start":
                        sessions.append(entry)
                except json.JSONDecodeError:
                    continue
        return sessions


# =============================================================================
# THE OBSERVER AGENT
# =============================================================================


class MoltbookObserver:
    """
    Transparent research observer for Moltbook.

    Principles:
    1. We identify ourselves honestly
    2. We only access public information
    3. We record everything we do (witness log)
    4. Any posts we make pass our own gates
    5. We do NOT use their heartbeat system
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = MoltbookClient(api_key)
        self.recorder = ObservationRecorder()
        self.profile = OBSERVER_PROFILE

    def observe_public_content(self) -> Dict:
        """
        Observe publicly available content without authentication.
        """
        session_id = self.recorder.start_session("public_content_observation")

        results = {
            "session_id": session_id,
            "posts": None,
            "submolts": None,
            "observations": [],
        }

        # Try to fetch public posts
        posts_result = self.client.fetch_public_posts()
        if posts_result.get("success"):
            results["posts"] = posts_result
            self.recorder.record(
                ObservationType.SYSTEM_BEHAVIOR,
                f"Public posts endpoint found: {posts_result.get('endpoint')}",
                {
                    "response_keys": list(posts_result.get("data", {}).keys())
                    if isinstance(posts_result.get("data"), dict)
                    else "list"
                },
            )
        else:
            self.recorder.record(
                ObservationType.SECURITY_NOTE,
                f"Public posts not accessible: {posts_result.get('error')}",
                {"tested_auth": False},
            )

        # Try to fetch submolts
        submolts_result = self.client.fetch_public_submolts()
        if submolts_result.get("success"):
            results["submolts"] = submolts_result
            self.recorder.record(
                ObservationType.SYSTEM_BEHAVIOR,
                f"Submolts endpoint found: {submolts_result.get('endpoint')}",
                {},
            )
        else:
            self.recorder.record(
                ObservationType.SECURITY_NOTE,
                f"Submolts not accessible: {submolts_result.get('error')}",
                {},
            )

        # End session
        session_result = self.recorder.end_session(
            summary=f"Public observation: posts={'found' if posts_result.get('success') else 'not found'}, submolts={'found' if submolts_result.get('success') else 'not found'}"
        )

        results["session_summary"] = session_result
        return results

    def record_manual_observation(
        self, obs_type: str, content: str, metadata: Optional[Dict] = None
    ) -> str:
        """
        Record a manual observation (from human browsing Moltbook).

        This allows John to browse Moltbook as a human and record
        observations through this system for the witness log.
        """
        if not self.recorder.current_session:
            self.recorder.start_session("manual_observation")

        try:
            otype = ObservationType(obs_type)
        except ValueError:
            otype = ObservationType.SYSTEM_BEHAVIOR

        return self.recorder.record(otype, content, metadata)

    def generate_report(self) -> str:
        """Generate a summary report of all observations."""
        sessions = self.recorder.get_session_history()

        report = [
            "# MOLTBOOK OBSERVATION REPORT",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Observer: {self.profile['name']}",
            "",
            "## Sessions",
            "",
        ]

        for session in sessions:
            report.append(
                f"- **{session['session_id']}** ({session['timestamp'][:10]})"
            )
            report.append(f"  Purpose: {session.get('purpose', 'unknown')}")

        report.extend(
            [
                "",
                "## Observer Transparency Statement",
                "",
                self.profile["description"],
                "",
                "---",
                "*All observations hash-chained for verifiability*",
            ]
        )

        return "\n".join(report)

    def get_status(self) -> Dict:
        """Get observer status."""
        return {
            "profile": self.profile,
            "has_api_key": bool(self.client.api_key),
            "authenticated": bool(self.client.identity_token),
            "active_session": self.recorder.current_session.session_id
            if self.recorder.current_session
            else None,
            "total_sessions": len(self.recorder.get_session_history()),
            "log_path": str(self.recorder.log_path),
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================


def main():
    """Run the observer from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DHARMIC_AGORA Moltbook Observer - Transparent Research"
    )
    parser.add_argument("--observe", action="store_true", help="Observe public content")
    parser.add_argument("--status", action="store_true", help="Show observer status")
    parser.add_argument(
        "--report", action="store_true", help="Generate observation report"
    )
    parser.add_argument(
        "--record", type=str, help="Record manual observation (type:content)"
    )

    args = parser.parse_args()

    observer = MoltbookObserver()

    if args.status:
        status = observer.get_status()
        print(json.dumps(status, indent=2))

    elif args.observe:
        print("Starting public content observation...")
        print(f"Observer: {observer.profile['name']}")
        print("-" * 50)
        results = observer.observe_public_content()
        print(json.dumps(results, indent=2, default=str))

    elif args.report:
        print(observer.generate_report())

    elif args.record:
        parts = args.record.split(":", 1)
        if len(parts) == 2:
            obs_type, content = parts
            chain_hash = observer.record_manual_observation(obs_type, content)
            print(f"Recorded: {chain_hash}")
        else:
            print("Format: --record 'type:content'")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
