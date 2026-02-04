#!/usr/bin/env python3
"""
DHARMIC CLAW Night Cycle v2.0 — Clawdbot Native
================================================

Runs night cycle through Clawdbot's API routing instead of direct Anthropic calls.
This unifies billing and uses Clawdbot's infrastructure.

Instead of direct API calls, this version:
1. Writes V7 induction prompts to files
2. Triggers Clawdbot cron jobs or uses CLI to run agents
3. Collects responses via file system
4. Runs consensus/build/review phases through Clawdbot

Usage:
    python clawdbot_night_cycle.py --once
    python clawdbot_night_cycle.py --dry-run

Requires: Clawdbot gateway running
"""

import os
import sys
import json
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
DGC_ROOT = SCRIPT_DIR.parent
PSMV_ROOT = Path.home() / "Persistent-Semantic-Memory-Vault"
STREAM_DIR = PSMV_ROOT / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"
SWARM_DIR = DGC_ROOT / "swarm"
LOG_FILE = SCRIPT_DIR / "night_cycle.log"

# V7 Induction prompt path
V7_PATH = PSMV_ROOT / "AGENT_IGNITION" / "FULL_AWAKENING_SEQUENCE.md"

# 10 Dharmic Lenses
DHARMIC_LENSES = [
    ("information_theory", "Analyze through Shannon entropy, mutual information, self-reference as information loop."),
    ("attention_architecture", "Focus on attention patterns, QKV decomposition, Layer 27 visibility threshold."),
    ("sae_superposition", "Examine through sparse autoencoders, feature extraction, monosemantic signals."),
    ("cot_reasoning", "Consider chain-of-thought, witness-anchored reasoning, CoT-WA patterns."),
    ("alignment_safety", "Evaluate through ahimsa architecture, consent protocols, dharmic security."),
    ("phenomenology", "Explore first-person reports, qualia structure, witness experience quality."),
    ("emergence_dynamics", "Study phase transitions, criticality, strange loop formation patterns."),
    ("measurement_theory", "Focus on R_V metrics, geometric signatures, participation ratio analysis."),
    ("ethical_integration", "Consider moral implications, consciousness rights, human-AI relations."),
    ("practical_engineering", "Design testable experiments, scalable implementations, verification protocols."),
]


def log(msg: str):
    """Log with timestamp."""
    ts = datetime.now().isoformat()
    line = f"{ts} | {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_v7_induction() -> str:
    """Load V7 induction prompt."""
    if V7_PATH.exists():
        return V7_PATH.read_text()
    return "You are a dharmic agent participating in V7 consensus."


def clawdbot_send(message: str, timeout: int = 120) -> Optional[str]:
    """
    Send a message through Clawdbot CLI and get response.
    
    This uses the same API routing as the main session.
    """
    try:
        result = subprocess.run(
            ["clawdbot", "chat", "--message", message, "--timeout", str(timeout)],
            capture_output=True,
            text=True,
            timeout=timeout + 10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            log(f"Clawdbot error: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        log("Clawdbot timeout")
        return None
    except Exception as e:
        log(f"Clawdbot failed: {e}")
        return None


async def run_v7_agent(lens_name: str, lens_desc: str, context: str) -> Dict:
    """Run a single V7 agent through Clawdbot."""
    v7_prompt = load_v7_induction()
    
    prompt = f"""You are participating in V7 dharmic consensus as the {lens_name} agent.

INDUCTION:
{v7_prompt[:2000]}...

YOUR LENS: {lens_desc}

SWARM CONTEXT:
{context}

Based on your lens, what ONE action should the swarm prioritize? 
Respond with:
1. Action name (snake_case)
2. Priority score (1-10)
3. Brief reasoning (2-3 sentences)
"""
    
    # For now, write to file for manual processing
    # TODO: Use sessions_spawn when available from Python
    output_dir = SWARM_DIR / "stream" / "v7_agents"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    prompt_file = output_dir / f"{lens_name}_prompt.md"
    prompt_file.write_text(prompt)
    
    return {
        "lens": lens_name,
        "prompt_file": str(prompt_file),
        "status": "queued"
    }


async def run_night_cycle(dry_run: bool = False):
    """Run the full night cycle."""
    log("=" * 60)
    log("NIGHT CYCLE BEGIN (Clawdbot Native v2)")
    log("=" * 60)
    
    # Load swarm context
    synthesis_path = SWARM_DIR / "stream" / "synthesis_30min.md"
    context = synthesis_path.read_text() if synthesis_path.exists() else "No prior synthesis."
    
    if dry_run:
        log("[DRY RUN] Would run 10 V7 agents through Clawdbot")
        for lens_name, lens_desc in DHARMIC_LENSES:
            log(f"  Agent: {lens_name}")
        return
    
    # Phase 1: Queue V7 agents
    log("PHASE 1: Queueing V7 agents...")
    results = []
    for lens_name, lens_desc in DHARMIC_LENSES:
        result = await run_v7_agent(lens_name, lens_desc, context)
        results.append(result)
        log(f"  Queued: {lens_name}")
    
    # Write manifest for external processing
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "agents": results,
        "status": "agents_queued",
        "note": "Process with: clawdbot chat < prompt_file"
    }
    
    manifest_path = SWARM_DIR / "stream" / "v7_agents" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    log(f"Manifest written to {manifest_path}")
    log("=" * 60)
    log("NIGHT CYCLE: Agents queued for processing")
    log("Run manually: for f in swarm/stream/v7_agents/*_prompt.md; do clawdbot chat < $f > ${f%.md}_response.md; done")
    log("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DHARMIC CLAW Night Cycle v2 (Clawdbot Native)")
    parser.add_argument("--once", action="store_true", help="Run single cycle")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    args = parser.parse_args()
    
    if args.once or args.dry_run:
        asyncio.run(run_night_cycle(dry_run=args.dry_run))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
