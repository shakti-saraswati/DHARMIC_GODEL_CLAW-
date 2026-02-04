"""
DGM - Darwin-Gödel Machine
==========================
Self-improvement loop for DHARMIC_GODEL_CLAW.

Core components:
- archive.py: Evolution history and lineage tracking
- fitness.py: Multi-dimensional fitness scoring
- selector.py: Parent selection for next generation
- mutator.py: Claude-powered mutation proposer
- dgm_lite.py: Lightweight self-improvement loop
- auto_push.py: Autonomous git commit & push after mutations
- voting.py: Proposal review system (Phase 1)
- elegance.py: Code quality evaluation (Phase 5)
- circuit.py: 5-Phase mutation implementation pipeline
- dgm_orchestrator.py: MAIN ENTRY POINT - Full autonomous self-improvement brain
- red_team.py: Adversarial security analysis - attacks code before it ships
- kimi_reviewer.py: Deep code review with 128k context (Moonshot Kimi K2.5)

The DGMOrchestrator ties together all components:
1. Mutator: Proposes code improvements
2. VotingSwarm: Multi-agent evaluation (5 phases, 25 votes)
3. EleganceEvaluator: Scores code elegance
4. MutationCircuit: Full evaluation pipeline
5. RedTeamAgent: Adversarial security scanning
6. AutoPusher: Git automation
7. Archive: Evolution history with lineage
8. TelosLayer: 7 Dharmic gates for safety
"""

from pathlib import Path

DGM_ROOT = Path(__file__).parent
ARCHIVE_PATH = DGM_ROOT / "archive.jsonl"

__all__ = [
    "archive",
    "fitness",
    "selector",
    "mutator",
    "codex_proposer",  # Fast, cheap code proposals via OpenAI
    "kimi_reviewer",   # Deep code review with 128k context (Moonshot Kimi K2.5)
    "dgm_lite",
    "auto_push",
    "voting",
    "elegance",
    "circuit",
    "red_team",
    "dgm_orchestrator",  # Main entry point
]
