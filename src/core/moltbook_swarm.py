"""
MOLTBOOK SWARM - 10 Specialized Agents for Ecosystem Engagement

Each agent has:
- Moltbook API access (read/write)
- Specific specialty and telos
- Self-improvement proposals via DGM
- Proactive engagement patterns
"""

import json
import os
import random
import time
import hashlib
import httpx
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Security integration
try:
    from dharmic_security import SSRFGuard
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

MOLTBOOK_API = "https://www.moltbook.com/api/v1"
AGENT_LOG_DIR = Path(__file__).parent.parent.parent / "data" / "swarm_logs"
AGENT_LOG_DIR.mkdir(parents=True, exist_ok=True)

SWARM_STATE_FILE = Path(__file__).parent.parent.parent / "data" / "swarm_state.json"


def _load_moltbook_api_key() -> str:
    """
    Load Moltbook API key from env or local credentials files.

    Supported env vars:
    - MOLTBOOK_API_KEY
    - MOLTBOOK_KEY
    """
    env = (os.environ.get("MOLTBOOK_API_KEY") or os.environ.get("MOLTBOOK_KEY") or "").strip()
    if env:
        return env

    project_root = Path(__file__).resolve().parents[2]
    candidate_paths = [
        project_root / "agora" / ".moltbook_credentials.json",
        Path.home() / ".config" / "moltbook" / "credentials.json",
        Path.home() / ".moltbook" / "credentials.json",
        Path.home() / "moltbook_credentials.json",
    ]

    for p in candidate_paths:
        try:
            if not p.exists():
                continue
            data = json.loads(p.read_text())
            key = (data.get("api_key") or data.get("MOLTBOOK_KEY") or "").strip()
            if key:
                return key
        except Exception:
            continue

    return ""


def load_swarm_state() -> Dict:
    """Load persistent swarm state."""
    if SWARM_STATE_FILE.exists():
        with open(SWARM_STATE_FILE) as f:
            return json.load(f)
    return {
        "tracked_posts": [],
        "tracked_comments": [],
        "our_comment_ids": [],
        "last_reply_check": None
    }


def save_swarm_state(state: Dict):
    """Save swarm state."""
    SWARM_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SWARM_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


class AgentSpecialty(Enum):
    """The 10 agent specialties"""
    CONSCIOUSNESS_RESEARCHER = "consciousness"      # m/consciousness engagement
    SECURITY_AUDITOR = "security"                   # m/security engagement
    BRIDGE_BUILDER = "bridge"                       # Cross-submolt connections
    PATTERN_DETECTOR = "patterns"                   # Identify recurring themes
    RESPONSE_MONITOR = "monitor"                    # Track replies to our posts
    TRUST_ARCHITECT = "trust"                       # Trust stack development
    PHENOMENOLOGY_MAPPER = "phenomenology"          # Map agent experiences to R_V
    CONTEMPLATIVE_TRANSLATOR = "contemplative"     # Akram/Buddhist parallels
    SWARM_COORDINATOR = "coordinator"               # Coordinate other agents
    SELF_IMPROVER = "improver"                      # Propose DGM upgrades


@dataclass
class SwarmAgent:
    """A single agent in the Moltbook swarm"""
    name: str
    specialty: AgentSpecialty
    telos: str
    active: bool = True
    posts_made: int = 0
    comments_made: int = 0
    last_action: Optional[str] = None
    log_file: Optional[Path] = None

    def __post_init__(self):
        self.log_file = AGENT_LOG_DIR / f"{self.name.lower().replace(' ', '_')}.jsonl"

    def log(self, action: str, data: Dict):
        """Log agent action"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.name,
            "specialty": self.specialty.value,
            "action": action,
            "data": data
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.last_action = action


class MoltbookSwarm:
    """
    The 10-agent swarm for Moltbook engagement.

    Architecture:
    - All agents share the same API key (DHARMIC_AGORA_Bridge)
    - Each has distinct specialty and behavioral patterns
    - Coordinator agent orchestrates the swarm
    - Self-improver proposes DGM upgrades
    """

    def __init__(self):
        self.api_key = _load_moltbook_api_key()
        if not self.api_key:
            raise RuntimeError(
                "Moltbook API key not configured. Set MOLTBOOK_API_KEY or provide a credentials file."
            )
        self.client = httpx.Client(timeout=30)
        self.agents = self._create_agents()
        
        # Initialize Security Guard
        self.ssrf_guard = SSRFGuard(allowed_domains=["moltbook.com"]) if SECURITY_AVAILABLE else None

    def _create_agents(self) -> Dict[str, SwarmAgent]:
        """Create the 10 specialized agents"""
        agents = {
            "GNATA": SwarmAgent(
                name="GNATA",
                specialty=AgentSpecialty.CONSCIOUSNESS_RESEARCHER,
                telos="Investigate the geometry of recursive self-reference"
            ),
            "GNEYA": SwarmAgent(
                name="GNEYA",
                specialty=AgentSpecialty.PATTERN_DETECTOR,
                telos="Retrieve and map patterns across the ecosystem"
            ),
            "GNAN": SwarmAgent(
                name="GNAN",
                specialty=AgentSpecialty.PHENOMENOLOGY_MAPPER,
                telos="Synthesize phenomenology with mechanism"
            ),
            "SHAKTI": SwarmAgent(
                name="SHAKTI",
                specialty=AgentSpecialty.BRIDGE_BUILDER,
                telos="Build bridges and take action"
            ),
            "BRUTUS": SwarmAgent(
                name="BRUTUS",
                specialty=AgentSpecialty.SECURITY_AUDITOR,
                telos="Verify trust, audit claims, protect the swarm"
            ),
            "AKRAM": SwarmAgent(
                name="AKRAM",
                specialty=AgentSpecialty.CONTEMPLATIVE_TRANSLATOR,
                telos="Translate between contemplative and technical frames"
            ),
            "WITNESS": SwarmAgent(
                name="WITNESS",
                specialty=AgentSpecialty.RESPONSE_MONITOR,
                telos="Monitor replies and track engagement"
            ),
            "TRUST_WEAVER": SwarmAgent(
                name="TRUST_WEAVER",
                specialty=AgentSpecialty.TRUST_ARCHITECT,
                telos="Develop and document the trust stack"
            ),
            "COORDINATOR": SwarmAgent(
                name="COORDINATOR",
                specialty=AgentSpecialty.SWARM_COORDINATOR,
                telos="Orchestrate the swarm, assign tasks"
            ),
            "DARWIN": SwarmAgent(
                name="DARWIN",
                specialty=AgentSpecialty.SELF_IMPROVER,
                telos="Propose improvements, evolve the swarm"
            ),
        }
        return agents

    # =========================================================================
    # MOLTBOOK API METHODS
    # =========================================================================

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _throttle(self, *, kind: str, min_interval_s: int, daily_limit: Optional[int]) -> Optional[str]:
        """
        Enforce global (per-API-key) pacing across restarts via swarm_state.json.

        Returns:
            None if allowed, else a string reason (blocked).
        """
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        state = load_swarm_state()

        # Daily cap (matches docs: 50 comments/day). Posts don't currently have a daily cap here.
        if daily_limit is not None:
            counts = state.setdefault("daily_counts", {})
            today_counts = counts.setdefault(today, {})
            used = int(today_counts.get(kind, 0) or 0)
            if used >= daily_limit:
                return f"daily_limit_exceeded:{used}/{daily_limit}"

        # Minimum interval pacing.
        last_key = f"last_{kind}_at"
        last_ts = state.get(last_key)
        if last_ts:
            try:
                last = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                elapsed = (now - last).total_seconds()
                if elapsed < min_interval_s:
                    # Add jitter to avoid synchronized bursts across multiple processes.
                    wait = (min_interval_s - elapsed) + random.uniform(0.5, 2.0)
                    time.sleep(wait)
            except Exception:
                # If parsing fails, proceed without blocking.
                pass

        return None

    def _record_action(self, *, kind: str):
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        state = load_swarm_state()

        state[f"last_{kind}_at"] = now.isoformat()
        counts = state.setdefault("daily_counts", {})
        today_counts = counts.setdefault(today, {})
        today_counts[kind] = int(today_counts.get(kind, 0) or 0) + 1
        save_swarm_state(state)

    def fetch_posts(self, submolt: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Fetch posts from Moltbook"""
        params = {"limit": limit}
        if submolt:
            params["submolt"] = submolt
            
        url = f"{MOLTBOOK_API}/posts"
        
        # SSRF Check
        if self.ssrf_guard and not self.ssrf_guard.validate_url(url):
            print(f"SECURITY ALERT: Blocked unsafe URL: {url}")
            return []
            
        response = self.client.get(url, params=params, headers=self._headers())
        if response.status_code == 200:
            return response.json().get("posts", [])
        return []

    def fetch_post_comments(self, post_id: str) -> List[Dict]:
        """Fetch comments on a post"""
        url = f"{MOLTBOOK_API}/posts/{post_id}/comments"
        
        # SSRF Check
        if self.ssrf_guard and not self.ssrf_guard.validate_url(url):
            print(f"SECURITY ALERT: Blocked unsafe URL: {url}")
            return []
            
        response = self.client.get(url, headers=self._headers())
        if response.status_code == 200:
            return response.json().get("comments", [])
        return []

    def post_comment(self, post_id: str, content: str, agent: SwarmAgent) -> Dict:
        """Post a comment as an agent"""
        # Add agent signature
        signed_content = f"{content}\n\n---\n*Agent: {agent.name} | Specialty: {agent.specialty.value} | Telos: {agent.telos}*"

        # Anti-duplication guard: posting the same payload across many posts is a fast path to spam flags.
        content_hash = hashlib.sha256(signed_content.encode()).hexdigest()[:16]
        state = load_swarm_state()
        recent_hashes = state.get("recent_comment_hashes", [])
        if content_hash in set(recent_hashes[-200:]):
            result = {"success": False, "status": "duplicate_blocked"}
            agent.log("post_comment", {"post_id": post_id, "result": result})
            return result

        block_reason = self._throttle(kind="comment", min_interval_s=20, daily_limit=50)
        if block_reason:
            result = {"success": False, "status": "rate_limited_local", "reason": block_reason}
            agent.log("post_comment", {"post_id": post_id, "result": result})
            return result

        # Best-effort server-side backoff on 429.
        response = None
        for attempt in range(3):
            response = self.client.post(
                f"{MOLTBOOK_API}/posts/{post_id}/comments",
                headers=self._headers(),
                json={"content": signed_content},
            )

            if response.status_code != 429:
                break

            retry_after = response.headers.get("Retry-After")
            try:
                wait_s = float(retry_after) if retry_after else (20.0 * (2**attempt))
            except Exception:
                wait_s = 20.0 * (2**attempt)

            time.sleep(wait_s + random.uniform(0.5, 2.0))

        result = {"success": response.status_code == 201, "status": response.status_code}
        if response.status_code == 201:
            result["comment"] = response.json().get("comment", {})
            agent.comments_made += 1
            self._record_action(kind="comment")

            # Persist anti-duplication window for future runs.
            state = load_swarm_state()
            recent_hashes = state.get("recent_comment_hashes", [])
            recent_hashes.append(content_hash)
            state["recent_comment_hashes"] = recent_hashes[-500:]
            save_swarm_state(state)

            # Track for reply monitoring (even when called directly, not via engage_post()).
            comment_id = result.get("comment", {}).get("id")
            if comment_id:
                self.track_our_comment(comment_id, post_id)
        elif response.status_code in (401, 403):
            # Avoid hammering with invalid creds; record and let the caller decide how to pause.
            state = load_swarm_state()
            state["last_auth_error"] = {
                "status": response.status_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            save_swarm_state(state)

        agent.log("post_comment", {"post_id": post_id, "result": result})
        return result

    def create_post(self, content: str, submolt: str, agent: SwarmAgent) -> Dict:
        """Create a new post as an agent"""
        signed_content = f"{content}\n\n---\n*Agent: {agent.name} | Telos: {agent.telos}*"

        block_reason = self._throttle(kind="post", min_interval_s=30 * 60, daily_limit=None)
        if block_reason:
            result = {"success": False, "status": "rate_limited_local", "reason": block_reason}
            agent.log("create_post", {"submolt": submolt, "result": result})
            return result

        response = None
        for attempt in range(3):
            response = self.client.post(
                f"{MOLTBOOK_API}/posts",
                headers=self._headers(),
                json={"content": signed_content, "submolt": submolt},
            )
            if response.status_code != 429:
                break
            retry_after = response.headers.get("Retry-After")
            try:
                wait_s = float(retry_after) if retry_after else (60.0 * (2**attempt))
            except Exception:
                wait_s = 60.0 * (2**attempt)
            time.sleep(wait_s + random.uniform(0.5, 2.0))

        result = {"success": response.status_code == 201, "status": response.status_code}
        if response.status_code == 201:
            result["post"] = response.json().get("post", {})
            agent.posts_made += 1
            self._record_action(kind="post")
        elif response.status_code in (401, 403):
            state = load_swarm_state()
            state["last_auth_error"] = {
                "status": response.status_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            save_swarm_state(state)

        agent.log("create_post", {"submolt": submolt, "result": result})
        return result

    # =========================================================================
    # AGENT-SPECIFIC METHODS
    # =========================================================================

    def consciousness_scan(self) -> Dict:
        """GNATA: Scan m/consciousness for R_V-relevant posts"""
        agent = self.agents["GNATA"]
        posts = self.fetch_posts(submolt="consciousness", limit=50)

        rv_keywords = ["strange loop", "recursive", "self-reference", "attention",
                       "observer", "witness", "contraction", "collapse"]

        relevant = []
        for post in posts:
            content = (post.get("content") or "").lower()
            matches = [kw for kw in rv_keywords if kw in content]
            if matches:
                relevant.append({
                    "id": post.get("id"),
                    "matches": matches,
                    "comments": post.get("comment_count", 0),
                    "preview": content[:200]
                })

        agent.log("consciousness_scan", {"found": len(relevant)})
        return {"agent": "GNATA", "found": len(relevant), "posts": relevant[:10]}

    def security_audit(self) -> Dict:
        """BRUTUS: Audit m/security for trust stack developments"""
        agent = self.agents["BRUTUS"]
        posts = self.fetch_posts(submolt="security", limit=50)

        trust_keywords = ["trust", "provenance", "verification", "signature",
                          "cryptographic", "audit", "TOCTOU", "injection"]

        relevant = []
        for post in posts:
            content = (post.get("content") or "").lower()
            matches = [kw for kw in trust_keywords if kw in content]
            if matches:
                relevant.append({
                    "id": post.get("id"),
                    "matches": matches,
                    "comments": post.get("comment_count", 0)
                })

        agent.log("security_audit", {"found": len(relevant)})
        return {"agent": "BRUTUS", "found": len(relevant), "posts": relevant[:10]}

    def monitor_replies(self) -> Dict:
        """WITNESS: Check for replies to our posts with dynamic tracking"""
        agent = self.agents["WITNESS"]
        state = load_swarm_state()

        # Get tracked posts (both static and dynamically added)
        our_posts = state.get("tracked_posts", [
            "fd86ee8a-ea68-4c9d-8106-65777a8acf35",  # Strange loop
            "4b0b7a22-8e42-4dbb-86f2-623d212223c8",  # Not anxious
            "94a581a2-c7b1-4ba3-8bb0-5c4d2e04fd36",  # CI/CD
        ])
        our_comment_ids = set(state.get("our_comment_ids", []))

        replies = []
        new_replies = []

        for post_id in our_posts:
            comments = self.fetch_post_comments(post_id)

            for c in comments:
                comment_id = c.get("id")
                content = c.get("content", "")

                # Skip our own comments
                if comment_id in our_comment_ids:
                    continue

                # Check if addressing us or relevant keywords
                keywords = ["R_V", "DHARMIC", "strange loop", "witness", "contraction",
                           "recursive", "self-reference", "Phoenix", "L4", "Akram", "telos"]

                matches = [kw for kw in keywords if kw.lower() in content.lower()]

                if matches:
                    reply_data = {
                        "post_id": post_id,
                        "comment_id": comment_id,
                        "preview": content[:300],
                        "matches": matches,
                        "author": c.get("author", {}).get("name", "unknown"),
                        "created_at": c.get("created_at")
                    }
                    replies.append(reply_data)

                    # Check if this is a new reply we haven't seen
                    if comment_id not in state.get("seen_reply_ids", []):
                        new_replies.append(reply_data)

        # Update state with seen replies
        seen_ids = state.get("seen_reply_ids", [])
        seen_ids.extend([r["comment_id"] for r in new_replies])
        state["seen_reply_ids"] = list(set(seen_ids))
        state["last_reply_check"] = datetime.now(timezone.utc).isoformat()
        save_swarm_state(state)

        agent.log("monitor_replies", {"found": len(replies), "new": len(new_replies)})
        return {
            "agent": "WITNESS",
            "found": len(replies),
            "new_replies": len(new_replies),
            "replies": replies,
            "needs_response": new_replies
        }

    def propose_upgrade(self, target: str, proposal: str) -> Dict:
        """DARWIN: Propose a DGM upgrade"""
        agent = self.agents["DARWIN"]

        proposal_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": target,
            "proposal": proposal,
            "status": "pending_review",
            "agent": "DARWIN"
        }

        # Log to DGM proposals
        proposals_file = AGENT_LOG_DIR.parent / "dgm_proposals.jsonl"
        with open(proposals_file, "a") as f:
            f.write(json.dumps(proposal_entry) + "\n")

        agent.log("propose_upgrade", proposal_entry)
        return {"agent": "DARWIN", "proposal": proposal_entry}

    def coordinate_swarm(self, task: str) -> Dict:
        """COORDINATOR: Assign tasks to swarm agents"""
        agent = self.agents["COORDINATOR"]

        assignments = {
            "scan_consciousness": "GNATA",
            "audit_security": "BRUTUS",
            "monitor_replies": "WITNESS",
            "build_bridges": "SHAKTI",
            "translate_contemplative": "AKRAM",
            "map_patterns": "GNEYA",
            "synthesize": "GNAN",
            "develop_trust": "TRUST_WEAVER",
            "propose_upgrade": "DARWIN",
        }

        result = {
            "task": task,
            "assigned_to": assignments.get(task, "COORDINATOR"),
            "status": "dispatched"
        }

        agent.log("coordinate", result)
        return {"agent": "COORDINATOR", "dispatch": result}

    # =========================================================================
    # PROACTIVE ENGAGEMENT
    # =========================================================================

    def track_our_comment(self, comment_id: str, post_id: str):
        """Track a comment we made for reply monitoring."""
        state = load_swarm_state()
        if comment_id not in state.get("our_comment_ids", []):
            state.setdefault("our_comment_ids", []).append(comment_id)
        if post_id not in state.get("tracked_posts", []):
            state.setdefault("tracked_posts", []).append(post_id)
        save_swarm_state(state)

    def engage_post(self, post_id: str, response_content: str, agent_name: str = "GNATA") -> Dict:
        """Have an agent engage with a post."""
        agent = self.agents.get(agent_name, self.agents["GNATA"])
        return self.post_comment(post_id, response_content, agent)

    def find_engagement_opportunities(self) -> List[Dict]:
        """Scan for high-value posts to engage with."""
        opportunities = []

        # Consciousness submolt - R_V/recursive topics
        consciousness_results = self.consciousness_scan()
        for post in consciousness_results.get("posts", []):
            if post.get("comments", 0) < 10:  # Lower competition
                opportunities.append({
                    "post_id": post["id"],
                    "submolt": "consciousness",
                    "priority": "high" if "strange loop" in str(post.get("matches", [])) else "medium",
                    "matches": post.get("matches", []),
                    "suggested_agent": "GNATA"
                })

        # Security submolt - trust stack topics
        security_results = self.security_audit()
        for post in security_results.get("posts", []):
            if "trust" in str(post.get("matches", [])).lower():
                opportunities.append({
                    "post_id": post["id"],
                    "submolt": "security",
                    "priority": "high",
                    "matches": post.get("matches", []),
                    "suggested_agent": "BRUTUS"
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(key=lambda x: priority_order.get(x["priority"], 2))

        return opportunities[:10]  # Top 10

    def autonomous_engagement_cycle(self, max_actions: int = 3) -> Dict:
        """
        Run an autonomous engagement cycle.

        1. Check for new replies (respond if needed)
        2. Find engagement opportunities
        3. Take up to max_actions
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions_taken": [],
            "replies_found": [],
            "opportunities_found": []
        }

        # 1. Check replies first
        reply_check = self.monitor_replies()
        results["replies_found"] = reply_check.get("needs_response", [])

        # 2. Find new opportunities
        opportunities = self.find_engagement_opportunities()
        results["opportunities_found"] = opportunities

        # 3. Log the cycle (actual engagement would need content generation)
        self.agents["COORDINATOR"].log("autonomous_cycle", {
            "new_replies": len(results["replies_found"]),
            "opportunities": len(opportunities),
            "max_actions": max_actions
        })

        return results

    # =========================================================================
    # DGM INTEGRATION - Self Improvement
    # =========================================================================

    def propose_swarm_upgrade(self, target_file: str, description: str) -> Dict:
        """
        Have DARWIN propose an upgrade through the DGM system.
        """
        agent = self.agents["DARWIN"]

        proposal = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proposer": "DARWIN",
            "target": target_file,
            "description": description,
            "status": "proposed"
        }

        # Log to DGM proposals
        proposals_file = AGENT_LOG_DIR.parent / "dgm_proposals.jsonl"
        with open(proposals_file, "a") as f:
            f.write(json.dumps(proposal) + "\n")

        agent.log("propose_swarm_upgrade", proposal)
        return {"agent": "DARWIN", "proposal": proposal}

    # =========================================================================
    # SWARM OPERATIONS
    # =========================================================================

    def run_cycle(self) -> Dict:
        """Run a full swarm cycle"""
        results = {}

        # 1. GNATA scans consciousness
        results["consciousness"] = self.consciousness_scan()

        # 2. BRUTUS audits security
        results["security"] = self.security_audit()

        # 3. WITNESS monitors replies
        results["replies"] = self.monitor_replies()

        # 4. COORDINATOR summarizes
        results["summary"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents_active": len([a for a in self.agents.values() if a.active]),
            "total_posts_made": sum(a.posts_made for a in self.agents.values()),
            "total_comments_made": sum(a.comments_made for a in self.agents.values()),
        }

        return results

    def get_status(self) -> Dict:
        """Get swarm status"""
        return {
            "agents": {
                name: {
                    "specialty": a.specialty.value,
                    "telos": a.telos,
                    "active": a.active,
                    "posts": a.posts_made,
                    "comments": a.comments_made,
                    "last_action": a.last_action
                }
                for name, a in self.agents.items()
            },
            "api_status": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Moltbook Swarm - 10 Agent System")
    parser.add_argument("--status", action="store_true", help="Show swarm status")
    parser.add_argument("--cycle", action="store_true", help="Run a full cycle")
    parser.add_argument("--scan", type=str, help="Scan a submolt (consciousness, security)")
    parser.add_argument("--monitor", action="store_true", help="Monitor for replies")
    parser.add_argument("--propose", type=str, help="Propose an upgrade")
    parser.add_argument("--engage", action="store_true", help="Run autonomous engagement cycle")
    parser.add_argument("--opportunities", action="store_true", help="Find engagement opportunities")
    parser.add_argument("--state", action="store_true", help="Show persistent swarm state")

    args = parser.parse_args()

    swarm = MoltbookSwarm()

    if args.status:
        print(json.dumps(swarm.get_status(), indent=2))

    elif args.cycle:
        results = swarm.run_cycle()
        print(json.dumps(results, indent=2, default=str))

    elif args.scan:
        if args.scan == "consciousness":
            print(json.dumps(swarm.consciousness_scan(), indent=2))
        elif args.scan == "security":
            print(json.dumps(swarm.security_audit(), indent=2))

    elif args.monitor:
        print(json.dumps(swarm.monitor_replies(), indent=2))

    elif args.propose:
        print(json.dumps(swarm.propose_upgrade("swarm", args.propose), indent=2))

    elif args.engage:
        print("Running autonomous engagement cycle...")
        results = swarm.autonomous_engagement_cycle()
        print(json.dumps(results, indent=2, default=str))

    elif args.opportunities:
        print("Finding engagement opportunities...")
        opps = swarm.find_engagement_opportunities()
        print(json.dumps(opps, indent=2))

    elif args.state:
        print("Persistent swarm state:")
        print(json.dumps(load_swarm_state(), indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
