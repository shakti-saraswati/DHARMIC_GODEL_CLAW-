#!/usr/bin/env python3
"""
CosmicChrisnaCoder_Gate_Runner
==============================

Memorable alias for the DHARMIC_CLAW 17-gate runner.
This is a thin wrapper around `swarm.run_gates`.

Usage:
  python3 swarm/CosmicChrisnaCoder_Gate_Runner.py --proposal-id PROP-001 --dry-run

You can also call:
  python3 -m swarm.run_gates --proposal-id PROP-001 --dry-run
"""

from __future__ import annotations

from swarm.run_gates import main


if __name__ == "__main__":
    main()
