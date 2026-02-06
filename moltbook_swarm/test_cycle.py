#!/usr/bin/env python3
"""Test a single swarm cycle."""

import asyncio
import sys
sys.path.insert(0, '/Users/dhyana/DHARMIC_GODEL_CLAW/moltbook_swarm')

from orchestrator import run_swarm_cycle

if __name__ == "__main__":
    print("Testing single swarm cycle...")
    asyncio.run(run_swarm_cycle())
    print("Test complete.")
