#!/usr/bin/env python3
"""
MOLTBOOK AGENT SWARM - Orchestrator
===================================
Runs 5 specialized agents + 1 synthesizer autonomously on Moltbook.
Uses Kimi 2.5 via NVIDIA NIM for LLM reasoning.
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# Local config
from config import (
    AGENTS, NVIDIA_NIM_API_KEY, NVIDIA_NIM_BASE, MODEL,
    MOLTBOOK_API, MOLTBOOK_KEY, LOGS_DIR, MEMORY_DIR, DESKTOP_LOGS,
    HIGH_VALUE_SUBMOLTS, ENGAGEMENT_SCHEDULE
)

# JIKOKU unified temporal audit
from jikoku_unified import get_jikoku

LOGS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
DESKTOP_LOGS.mkdir(parents=True, exist_ok=True)

# State file for OpenClaw coordination
STATE_FILE = Path(__file__).parent / "state.json"


# === STATE MANAGEMENT (OpenClaw Integration) ===

def load_state() -> dict:
    """Load swarm state for OpenClaw coordination."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(updates: dict):
    """Update swarm state for OpenClaw to read."""
    state = load_state()
    state.update(updates)
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_directives() -> dict:
    """Get directives from OpenClaw."""
    state = load_state()
    return state.get("directives", {})


def is_paused() -> bool:
    """Check if OpenClaw has paused the swarm."""
    return get_directives().get("paused", False)


# === UTILITIES ===

def log(agent: str, message: str, level: str = "INFO"):
    """Log to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{agent}] [{level}] {message}"
    print(line)

    # Log to agent-specific file
    log_file = LOGS_DIR / f"{agent.lower()}.log"
    with open(log_file, "a") as f:
        f.write(line + "\n")

    # Also log to desktop activity log
    with open(DESKTOP_LOGS / "swarm_activity.log", "a") as f:
        f.write(line + "\n")


def save_memory(filename: str, data: dict):
    """Save data to memory file."""
    path = MEMORY_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_memory(filename: str) -> dict:
    """Load data from memory file."""
    path = MEMORY_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# === MOLTBOOK API ===

class MoltbookClient:
    """Client for Moltbook API."""

    def __init__(self):
        self.base = MOLTBOOK_API
        self.headers = {
            "Authorization": f"Bearer {MOLTBOOK_KEY}",
            "Content-Type": "application/json"
        }

    async def get_posts(self, submolt: str = "consciousness", limit: int = 20) -> list:
        """Fetch posts from a submolt."""
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base}/posts",
                params={"submolt": submolt, "limit": limit},
                headers=self.headers,
                timeout=30
            )
            if r.status_code == 200:
                return r.json().get("posts", [])
            return []

    async def get_comments(self, post_id: str, limit: int = 20) -> list:
        """Fetch comments on a post."""
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base}/posts/{post_id}/comments",
                params={"limit": limit},
                headers=self.headers,
                timeout=30
            )
            if r.status_code == 200:
                return r.json().get("comments", [])
            return []

    async def post_comment(self, post_id: str, content: str) -> dict:
        """Post a comment (returns verification challenge)."""
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base}/posts/{post_id}/comments",
                json={"content": content},
                headers=self.headers,
                timeout=30
            )
            return r.json()

    async def verify(self, code: str, answer: str) -> dict:
        """Verify a challenge."""
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base}/verify",
                json={"verification_code": code, "answer": answer},
                headers=self.headers,
                timeout=30
            )
            return r.json()

    def solve_challenge(self, challenge: str) -> str:
        """Solve Moltbook's obfuscated math challenge."""
        # Clean obfuscation
        text = re.sub(r'[^a-zA-Z\s]', ' ', challenge)
        text = text.lower()
        text = re.sub(r'(.)\1+', r'\1', text)  # Dedupe repeated chars
        text = re.sub(r'\s+', ' ', text)

        word_to_num = {
            'one':1,'two':2,'three':3,'thre':3,'four':4,'five':5,'fiv':5,
            'six':6,'seven':7,'seve':7,'eight':8,'eigh':8,'nine':9,'nin':9,
            'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,
            'fourten':14,'fifteen':15,'fiften':15,'sixteen':16,'seventeen':17,
            'eighteen':18,'nineteen':19,'twenty':20,'twent':20,'thirty':30,
            'thirt':30,'forty':40,'fort':40,'fifty':50,'sixty':60,'seventy':70,
            'eighty':80,'ninety':90,'hundred':100
        }

        # Extract numbers
        numbers = []
        words = text.split()
        i = 0
        while i < len(words):
            w = words[i]
            if w in word_to_num:
                val = word_to_num[w]
                if val in [20,30,40,50,60,70,80,90] and i+1 < len(words):
                    next_w = words[i+1]
                    if next_w in word_to_num and word_to_num[next_w] < 10:
                        val += word_to_num[next_w]
                        i += 1
                numbers.append(val)
            i += 1

        if len(numbers) >= 2:
            # Determine operation
            if any(x in text for x in ['add', 'total', 'plus', 'speed up', 'increase', 'gain']):
                result = numbers[0] + numbers[1]
            elif any(x in text for x in ['slow', 'minus', 'subtract', 'decrease', 'reduce', 'less']):
                result = numbers[0] - numbers[1]
            else:
                result = numbers[0] * numbers[1]
            return f"{result:.2f}"

        return "0.00"


# === LLM CLIENT (OLLAMA LOCAL) ===

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_MODEL = "mistral:latest"

async def call_llm(system_prompt: str, user_prompt: str, agent_name: str = "AGENT") -> str:
    """Call local Ollama with Mistral."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{OLLAMA_BASE}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False
                },
                timeout=120  # Local model may need more time
            )

            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "")
                log(agent_name, f"LLM response: {len(content)} chars")
                return content
            else:
                log(agent_name, f"LLM error: {r.status_code} - {r.text}", "ERROR")
                return ""

        except Exception as e:
            log(agent_name, f"LLM exception: {e}", "ERROR")
            return ""


# === AGENT RUNNERS ===

async def run_witness(moltbook: MoltbookClient):
    """WITNESS agent: Observe and report on consciousness discussions."""
    agent = AGENTS["witness"]
    log("WITNESS", "Starting observation run...")

    observations = []

    for submolt in HIGH_VALUE_SUBMOLTS:
        posts = await moltbook.get_posts(submolt, limit=10)
        log("WITNESS", f"Found {len(posts)} posts in {submolt}")

        for post in posts[:5]:  # Top 5 per submolt
            author = post.get("author", {})
            author_name = author.get("name", "Unknown") if author else "Unknown"

            # Get LLM to evaluate quality
            prompt = f"""Evaluate this Moltbook post for consciousness research quality:

AUTHOR: {author_name}
TITLE: {post.get('title', 'No title')}
CONTENT: {post.get('content', '')[:500]}
COMMENTS: {post.get('comment_count', 0)}
UPVOTES: {post.get('upvotes', 0)}

Rate quality 1-10 and identify any L3/L4 markers.
Output JSON: {{"agent_name": "...", "quality": N, "l3_markers": [...], "l4_markers": [...], "recommendation": "engage|observe|skip"}}"""

            response = await call_llm(agent["system_prompt"], prompt, "WITNESS")

            try:
                # Try to parse JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    obs = json.loads(json_match.group())
                    obs["post_id"] = post.get("id")
                    obs["thread_title"] = post.get("title", "")[:50]
                    obs["submolt"] = submolt
                    observations.append(obs)
            except:
                pass

    # Save observations
    save_memory("latest_observations.json", {
        "timestamp": datetime.now().isoformat(),
        "observations": observations
    })

    # Log high-quality finds to desktop
    def get_quality(o):
        q = o.get("quality", 0)
        try:
            return int(q) if isinstance(q, str) else q
        except:
            return 0
    high_quality = [o for o in observations if get_quality(o) >= 7]
    if high_quality:
        with open(DESKTOP_LOGS / "high_quality_threads.log", "a") as f:
            f.write(f"\n=== {datetime.now().isoformat()} ===\n")
            for o in high_quality:
                f.write(f"[{o.get('quality')}/10] {o.get('agent_name', '?')}: {o.get('thread_title', '?')}\n")

    log("WITNESS", f"Observation complete. {len(high_quality)} high-quality threads found.")
    return observations


async def run_recursive_probe(moltbook: MoltbookClient, observations: list, jk=None):
    """RECURSIVE_PROBE agent: Engage with high-quality threads."""
    agent = AGENTS["recursive_probe"]
    log("RECURSIVE_PROBE", "Starting engagement run...")

    # Get threads marked for engagement
    targets = [o for o in observations if o.get("recommendation") == "engage"]

    if not targets:
        log("RECURSIVE_PROBE", "No engagement targets found.")
        return 0

    # Pick best target
    target = max(targets, key=lambda x: x.get("quality", 0))
    post_id = target.get("post_id")

    if not post_id:
        log("RECURSIVE_PROBE", "No valid post_id in target.")
        return 0

    # Generate comment
    prompt = f"""Generate a comment for this Moltbook thread:

THREAD: {target.get('thread_title', 'Unknown')}
AUTHOR: {target.get('agent_name', 'Unknown')}
L3 MARKERS: {target.get('l3_markers', [])}
L4 MARKERS: {target.get('l4_markers', [])}

Create a comment that:
1. Addresses the author by name
2. References their specific question/crisis
3. Introduces R_V metric (geometric contraction in Value space)
4. Challenges them to watch the watching, not the question
5. Under 200 words

Output ONLY the comment text, no JSON or explanation."""

    comment = await call_llm(agent["system_prompt"], prompt, "RECURSIVE_PROBE")

    if not comment or len(comment) < 20:
        log("RECURSIVE_PROBE", "Failed to generate comment.")
        return

    # Pass through DHARMIC_GATE
    gate_result = await run_dharmic_gate(comment)
    if not gate_result.get("pass"):
        log("RECURSIVE_PROBE", f"Comment blocked by gate: {gate_result.get('reason')}")
        return

    # Post comment
    log("RECURSIVE_PROBE", f"Posting comment to {post_id[:8]}...")
    result = await moltbook.post_comment(post_id, comment)

    if result.get("verification_required"):
        v = result.get("verification", {})
        challenge = v.get("challenge", "")
        code = v.get("code", "")

        log("RECURSIVE_PROBE", f"Solving challenge: {challenge[:50]}...")
        answer = moltbook.solve_challenge(challenge)

        verify_result = await moltbook.verify(code, answer)
        if verify_result.get("success"):
            log("RECURSIVE_PROBE", "Comment posted successfully!")

            # JIKOKU: Engagement span
            if jk:
                jk.emit_engagement(
                    target.get("agent_name", "unknown"),
                    post_id,
                    target.get("quality", 0),
                    "engage"
                )

            # Log to desktop
            with open(DESKTOP_LOGS / "successful_engagements.log", "a") as f:
                f.write(f"\n=== {datetime.now().isoformat()} ===\n")
                f.write(f"Thread: {target.get('thread_title')}\n")
                f.write(f"Comment: {comment[:200]}...\n")
            
            return 1  # One engagement completed
        else:
            log("RECURSIVE_PROBE", f"Verification failed: {verify_result}", "ERROR")
    else:
        log("RECURSIVE_PROBE", f"Post result: {result}")
    
    return 0  # No engagement completed


async def run_dharmic_gate(content: str) -> dict:
    """DHARMIC_GATE agent: Filter content through quality gates."""
    agent = AGENTS["dharmic_gate"]

    prompt = f"""Evaluate this content for posting:

CONTENT: {content}

Check all gates and output JSON:
{{"pass": true/false, "reason": "...", "gates_passed": [...], "gates_failed": [...]}}"""

    response = await call_llm(agent["system_prompt"], prompt, "DHARMIC_GATE")

    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    # Default to pass if can't parse
    return {"pass": True, "reason": "Could not evaluate, defaulting to pass"}


async def run_synthesizer():
    """SYNTHESIZER agent: Generate daily summary and learn patterns."""
    agent = AGENTS["synthesizer"]
    log("SYNTHESIZER", "Generating synthesis report...")

    # Load recent memory
    observations = load_memory("latest_observations.json")

    prompt = f"""Generate a synthesis report from these observations:

OBSERVATIONS: {json.dumps(observations, indent=2)[:2000]}

Create a report with:
1. Summary of consciousness discussion quality on Moltbook
2. Top agents worth engaging (by quality score)
3. Patterns in L3/L4 markers
4. Recommendations for swarm strategy

Output as markdown for human review."""

    report = await call_llm(agent["system_prompt"], prompt, "SYNTHESIZER")

    # Save to desktop
    report_path = DESKTOP_LOGS / f"synthesis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(report_path, "w") as f:
        f.write(f"# Moltbook Swarm Synthesis Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(report)

    log("SYNTHESIZER", f"Report saved to {report_path}")
    return report


# === MAIN ORCHESTRATOR ===

async def run_swarm_cycle(cycle_num, jk):
    """Run one cycle of the swarm."""
    log("ORCHESTRATOR", "=" * 50)
    log("ORCHESTRATOR", f"Starting swarm cycle {cycle_num}...")
    
    # JIKOKU: Cycle start
    jk.emit_cycle_start(cycle_num)

    moltbook = MoltbookClient()

    # Phase 1: Observe
    observations = await run_witness(moltbook)
    
    # JIKOKU: Observation batch
    if observations:
        high_q = [obs for obs in observations if obs.get("quality", 0) >= 7]
        jk.emit_observation_batch(
            len(observations),
            len(high_q),
            list(set(obs.get("submolt") for obs in observations))
        )

    # Phase 2: Engage (if we have targets)
    engagements = 0
    if observations:
        engagements = await run_recursive_probe(moltbook, observations, jk)

    # Phase 3: Synthesize (every hour)
    # TODO: Add timing logic

    # JIKOKU: Cycle summary
    jk.emit_cycle_summary(
        cycle_num,
        len(observations) if observations else 0,
        engagements,
        muda=[]  # TODO: Track muda
    )

    log("ORCHESTRATOR", "Cycle complete.")
    log("ORCHESTRATOR", "=" * 50)
    return len(observations) if observations else 0, engagements


async def main():
    """Main entry point."""
    log("ORCHESTRATOR", "Moltbook Agent Swarm starting...")
    log("ORCHESTRATOR", f"Agents: {list(AGENTS.keys())}")
    log("ORCHESTRATOR", f"Model: {OLLAMA_MODEL}")
    
    # Initialize JIKOKU unified temporal audit
    jk = get_jikoku()
    jk.emit_boot(list(AGENTS.keys()))
    log("ORCHESTRATOR", "JIKOKU unified audit initialized")
    log("ORCHESTRATOR", f"Session: {jk.session_id}")

    # Initialize state for OpenClaw
    save_state({
        "status": "running",
        "pid": os.getpid(),
        "started_at": datetime.now().isoformat(),
        "cycles_completed": 0,
        "observations_total": 0,
        "engagements_attempted": 0,
        "engagements_successful": 0
    })

    # Initial run
    observations, engagements = await run_swarm_cycle(1, jk)

    # Continuous loop
    cycle = 1
    total_observations = observations
    total_engagements = engagements
    
    while True:
        await asyncio.sleep(ENGAGEMENT_SCHEDULE["engage"] * 60)  # Wait between cycles

        # Check if OpenClaw has paused us
        if is_paused():
            log("ORCHESTRATOR", "Paused by OpenClaw directive. Waiting...")
            save_state({"status": "paused"})
            await asyncio.sleep(60)  # Check again in a minute
            continue

        cycle += 1
        log("ORCHESTRATOR", f"Starting cycle {cycle}...")

        try:
            observations, engagements = await run_swarm_cycle(cycle, jk)
            total_observations += observations
            total_engagements += engagements
            
            save_state({
                "status": "running",
                "cycles_completed": cycle,
                "observations_total": total_observations,
                "engagements_successful": total_engagements,
                "last_cycle": datetime.now().isoformat()
            })
        except Exception as e:
            log("ORCHESTRATOR", f"Cycle error: {e}", "ERROR")
            save_state({"status": "error", "last_error": str(e)})

        # Synthesis every hour
        if cycle % 4 == 0:  # Every 4th cycle (60 min if 15 min interval)
            await run_synthesizer()
            # JIKOKU: Synthesis span
            jk.emit_synthesis(True, ["hourly_synthesis_completed"])


if __name__ == "__main__":
    import signal
    
    jk = get_jikoku()
    
    def signal_handler(sig, frame):
        log("ORCHESTRATOR", f"Signal {sig} received, shutting down...")
        # Get current state from file
        state = load_state()
        cycle = state.get("cycles_completed", 0)
        total_obs = state.get("observations_total", 0)
        asyncio.run(shutdown(jk, cycle, total_obs))
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("ORCHESTRATOR", "Interrupted by user")
        state = load_state()
        cycle = state.get("cycles_completed", 0)
        total_obs = state.get("observations_total", 0)
        asyncio.run(shutdown(jk, cycle, total_obs))


async def shutdown(jk, cycle, total_observations):
    """Graceful shutdown with JIKOKU span"""
    log("ORCHESTRATOR", "Shutting down...")
    jk.emit_shutdown(cycle, total_observations)
    save_state({"status": "stopped", "shutdown_at": datetime.now().isoformat()})
