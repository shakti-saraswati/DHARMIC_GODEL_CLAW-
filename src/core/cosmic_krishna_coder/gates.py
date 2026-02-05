"""Gate runner wrapper for Cosmic Krishna Coder."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

DGC_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GATE_ALIAS = DGC_ROOT / "swarm" / "CosmicChrisnaCoder_Gate_Runner.py"


def run_gates(args: List[str]) -> subprocess.CompletedProcess:
    """Run the gate runner alias with provided CLI args."""
    cmd = ["python3", str(GATE_ALIAS)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
