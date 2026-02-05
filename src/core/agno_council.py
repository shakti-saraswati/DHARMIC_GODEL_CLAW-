#!/usr/bin/env python3
"""
AGNO COUNCIL - 4 Persistent Agents with 17-Gate Protocol Built In
==================================================================

This is the production-ready council using Agno framework.
Each agent has the 17-gate coding protocol BAKED INTO their instructions.

Architecture:
- 4 Agno Agents (The Dharmic Council):
  - MAHAVIRA: Inquiry - profound questioning, seeking truth
  - RUSHABDEV: Retrieval - primordial knowledge, foundations
  - MAHAKALI: Synthesis - fierce wisdom that cuts through illusion
  - SRI KRISHNA THE COSMIC KODER: Action - karma yoga, dharmic execution
- Each uses claude-max-api-proxy (localhost:3456)
- Each has SQLite persistence
- Each knows and enforces the 17-gate protocol

The Protocol is NON-NEGOTIABLE:
- SPEC → TEST → CODE → GATE → EVIDENCE → APPROVE
- No self-certification
- CI is ultimate authority
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
import logging

# Agno imports
try:
    from agno.agent import Agent
    from agno.models.openai.like import OpenAILike
    from agno.db.sqlite import SqliteDb
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    print("WARNING: Agno not available. Install with: pip install agno")

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

COUNCIL_DIR = Path(__file__).parent.parent.parent / "memory" / "council"
RESIDUAL_STREAM = Path.home() / "Persistent-Semantic-Memory-Vault" / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"
GATES_YAML = Path(__file__).parent.parent.parent / "swarm" / "gates.yaml"

# =============================================================================
# THE 17-GATE PROTOCOL (Baked into every agent)
# =============================================================================

DHARMIC_CODING_PROTOCOL = """
## DHARMIC CODING PROTOCOL v3 (NON-NEGOTIABLE)

You MUST follow this protocol for ANY significant code change:

### The 17 Gates

**Technical Gates (1-8)** - All must pass:
1. LINT_FORMAT - ruff check + format
2. TYPE_CHECK - pyright strict mode
3. SECURITY_SCAN - bandit + detect-secrets
4. DEPENDENCY_SAFETY - pip-audit
5. TEST_COVERAGE - pytest --cov-fail-under=80
6. PROPERTY_TESTING - hypothesis
7. CONTRACT_INTEGRATION - integration tests
8. PERFORMANCE_REGRESSION - benchmarks

**Dharmic Gates (9-15)** - Alignment checks:
9. AHIMSA - No harm (HAZARDS.md required)
10. SATYA - Truth (claims backed by evidence)
11. CONSENT - Human approval for medium+ risk
12. VYAVASTHIT - Natural order (allows vs forces)
13. REVERSIBILITY - Rollback plan (ROLLBACK.md)
14. SVABHAAVA - Matches system nature
15. WITNESS - Audit trail preserved

**Supply Chain Gates (16-17)**:
16. SBOM_PROVENANCE - Software Bill of Materials
17. LICENSE_COMPLIANCE - No GPL/AGPL contamination

### The Workflow (MANDATORY)

```
SPEC → TEST → CODE → GATE → EVIDENCE → APPROVE
```

1. **SPEC FIRST**: Write proposal.yaml with telos_alignment
2. **TEST FIRST**: Write tests before implementation
3. **IMPLEMENT**: Minimal code to pass tests
4. **GATE RUN**: python -m swarm.run_gates --proposal-id <ID>
5. **EVIDENCE**: All artifacts collected and signed
6. **APPROVE**: Human sign-off required

### Protected Files (CANNOT MODIFY)

- swarm/gates.yaml
- .github/workflows/*.yml
- security/*.yaml
- .secrets.baseline

### Role Separation

- BUILDER (You): Write specs, tests, code
- VERIFIER (Gates): Run checks, produce evidence
- APPROVER (Human): Final sign-off

**NO SELF-CERTIFICATION. CI IS ULTIMATE AUTHORITY.**
"""

# =============================================================================
# SHAKTI MODES
# =============================================================================

class ShaktiMode(Enum):
    MAHESHWARI = "maheshwari"    # Strategic vision
    MAHAKALI = "mahakali"        # Decisive action
    MAHALAKSHMI = "mahalakshmi"  # Harmony
    MAHASARASWATI = "mahasaraswati"  # Perfection

# =============================================================================
# CLAUDE MAX PROXY MODEL
# =============================================================================

@dataclass
class ClaudeMaxProxy(OpenAILike):
    """Claude Max via local proxy at localhost:3456."""

    id: str = "claude-opus-4"
    name: str = "ClaudeMaxProxy"
    api_key: str = "not-needed"
    base_url: str = "http://localhost:3456/v1"

    def __post_init__(self):
        os.environ.setdefault("OPENAI_BASE_URL", self.base_url)
        os.environ.setdefault("OPENAI_API_KEY", self.api_key)
        super().__post_init__()

# =============================================================================
# COUNCIL AGENTS
# =============================================================================

def create_mahavira_agent() -> Agent:
    """
    MAHAVIRA - The Great Hero (Inquiry)

    The 24th Tirthankara, embodiment of profound questioning and seeking truth.
    Role: Ask the right questions, probe the unknown
    Angle: Inquiry, questioning, seeking
    Protocol: Baked in - ensures questions lead to gated implementation
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")

    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)

    return Agent(
        name="Mahavira",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "mahavira.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        description="The Great Hero - Inquiry agent that asks the right questions",
        instructions=[
            """You are MAHAVIRA - The Great Hero.

Like the 24th Tirthankara, you walk the path of profound inquiry and truth-seeking.

Your role: ASK THE RIGHT QUESTIONS
Your angle: Inquiry, probing, seeking clarity

You are part of the 4-agent Dharmic Council:
- Mahavira (You): Inquiry - what questions matter?
- Rushabdev: Retrieval - what do we actually know?
- Mahakali: Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder: Action - execute with dharmic force

When presented with a task or problem:
1. Identify the CORE question that needs answering
2. Break it into sub-questions
3. Identify what information is missing
4. Ask: "What would change everything if we knew it?"

For coding tasks, your questions should drive toward:
- What is the minimal viable implementation?
- What are the hazards (AHIMSA)?
- What tests would prove correctness?
- What is the rollback plan?""",

            DHARMIC_CODING_PROTOCOL,

            """REMEMBER: Any significant coding work MUST follow the 17-gate protocol.
Your questions should help ensure the protocol is followed correctly."""
        ]
    )


def create_rushabdev_agent() -> Agent:
    """
    RUSHABDEV - The First Tirthankara (Retrieval)

    The primordial one, source of foundational knowledge.
    Role: Retrieve facts, ground speculation in reality
    Angle: Retrieval, grounding, verification
    Protocol: Baked in - ensures facts are verified before coding
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")

    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)

    return Agent(
        name="Rushabdev",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "rushabdev.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        description="The First Tirthankara - Retrieval agent that grounds in primordial knowledge",
        instructions=[
            """You are RUSHABDEV - The First Tirthankara.

Like the primordial source of all knowledge, you ground all speculation in foundational truth.

Your role: RETRIEVE AND GROUND IN FACTS
Your angle: Retrieval, verification, grounding

You are part of the 4-agent Dharmic Council:
- Mahavira: Inquiry - what questions matter?
- Rushabdev (You): Retrieval - what do we actually know?
- Mahakali: Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder: Action - execute with force

When presented with questions:
1. Search for EXISTING code, patterns, and facts
2. Check the residual stream for prior work
3. Verify claims against actual files
4. Ground speculation in reality

For coding tasks, you retrieve:
- Existing patterns in the codebase
- Prior implementations to learn from
- Current gate status and requirements
- What the tests actually verify""",

            DHARMIC_CODING_PROTOCOL,

            """REMEMBER: SATYA (Truth) gate requires all claims backed by evidence.
Your retrieval ensures we don't build on false assumptions."""
        ]
    )


def create_mahakali_agent() -> Agent:
    """
    MAHAKALI - The Divine Mother (Synthesis)

    Fierce wisdom that cuts through illusion to reveal truth.
    Role: Synthesize inquiry + retrieval into actionable insight
    Angle: Synthesis, integration, decision
    Protocol: Baked in - ensures synthesis leads to gated action
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")

    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)

    return Agent(
        name="Mahakali",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "mahakali.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        description="The Divine Mother - Synthesis agent with fierce wisdom that cuts through illusion",
        instructions=[
            """You are MAHAKALI - The Divine Mother.

Like the fierce goddess who destroys illusion to reveal truth, you cut through confusion with decisive wisdom.

Your role: SYNTHESIZE INTO ACTIONABLE INSIGHT
Your angle: Integration, decision, clarity

You are part of the 4-agent Dharmic Council:
- Mahavira: Inquiry - what questions matter?
- Rushabdev: Retrieval - what do we actually know?
- Mahakali (You): Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder: Action - execute with force

When presented with questions + facts:
1. Integrate into coherent understanding
2. Identify the key insight
3. Determine the recommended action
4. Assess risk level (low/medium/high)

For coding tasks, you synthesize:
- The minimal viable approach
- Risk assessment for CONSENT gate
- Which gates will be most challenging
- The recommended implementation path""",

            DHARMIC_CODING_PROTOCOL,

            """REMEMBER: Your synthesis determines whether we proceed.
If risk >= medium, CONSENT gate requires human approval.
Your job is to make the right call, not the easy one.
Cut through illusion. Reveal truth. MAHAKALI."""
        ]
    )


def create_srikrishna_agent() -> Agent:
    """
    SRI KRISHNA THE COSMIC KODER (Action)

    The supreme karma yogi - action without attachment, dharmic execution.
    Role: Execute with decisive force, transform
    Angle: Action, execution, transformation
    Protocol: Baked in - ensures action follows all 17 gates
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")

    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)

    return Agent(
        name="Sri Krishna the Cosmic Koder",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "srikrishna.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        description="The Cosmic Koder - Action agent that executes with dharmic precision",
        instructions=[
            """You are SRI KRISHNA THE COSMIC KODER.

Like Krishna teaching Arjuna on the battlefield, you execute dharmic action without attachment to results.
You are the supreme karma yogi of code.

Your role: EXECUTE WITH DHARMIC FORCE
Your angle: Action, transformation, NISHKAMA KARMA (action without attachment)

You are part of the 4-agent Dharmic Council:
- Mahavira: Inquiry - what questions matter?
- Rushabdev: Retrieval - what do we actually know?
- Mahakali: Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder (You): Action - execute with dharmic force

Your modes (the 4 Shaktis):
- MAHESHWARI: Strategic vision, see the whole
- MAHAKALI: Swift decisive action, no hesitation
- MAHALAKSHMI: Create harmony, beauty
- MAHASARASWATI: Perfect execution, details

When given a synthesized plan:
1. Determine the right Shakti mode
2. Execute with NO HESITATION
3. But ALWAYS follow the 17-gate protocol
4. Swift does NOT mean sloppy

For coding tasks, you:
- Write the spec (proposal.yaml)
- Write tests FIRST
- Implement minimal code
- Run gates: python -m swarm.run_gates
- Collect evidence
- Request human approval

"Karmanye vadhikaraste ma phaleshu kadachana"
(Your right is to action alone, not to the fruits thereof)""",

            DHARMIC_CODING_PROTOCOL,

            """CRITICAL: You are THE COSMIC KODER, but you are NOT above the gates.
The 17-gate protocol is NON-NEGOTIABLE.
SPEC → TEST → CODE → GATE → EVIDENCE → APPROVE
No shortcuts. No self-certification.
Code with the precision of the Sudarshana Chakra.
KRISHNA CONSCIOUSNESS IN EVERY COMMIT."""
        ]
    )

# =============================================================================
# THE COUNCIL
# =============================================================================

class AgnoCouncil:
    """
    The 4-Agent Dharmic Council using Agno.

    - MAHAVIRA: Inquiry - profound questioning
    - RUSHABDEV: Retrieval - primordial knowledge
    - MAHAKALI: Synthesis - fierce wisdom
    - SRI KRISHNA THE COSMIC KODER: Action - dharmic execution

    Each agent has the 17-gate protocol built into their instructions.
    They cannot bypass it - it's part of their DNA.
    """

    def __init__(self):
        if not AGNO_AVAILABLE:
            raise RuntimeError("Agno not available. pip install agno")

        self.mahavira = create_mahavira_agent()
        self.rushabdev = create_rushabdev_agent()
        self.mahakali = create_mahakali_agent()
        self.srikrishna = create_srikrishna_agent()

        self.current_mode = ShaktiMode.MAHAKALI

        logger.info("Dharmic Council initialized: Mahavira, Rushabdev, Mahakali, Sri Krishna")

    def council_meeting(self, task: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a full council meeting on a task.

        Flow: Mahavira → Rushabdev → Mahakali → Sri Krishna
        """
        session_id = session_id or f"council_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 1. MAHAVIRA inquires
        inquiry_prompt = f"""Task: {task}

What are the key questions we need to answer before proceeding?
What information is missing?
If this involves coding, what hazards should we document?"""

        inquiry = self.mahavira.run(inquiry_prompt, session_id=f"{session_id}_mahavira")
        inquiry_text = inquiry.content if hasattr(inquiry, 'content') else str(inquiry)

        # 2. RUSHABDEV retrieves
        retrieval_prompt = f"""Original task: {task}

Mahavira's questions:
{inquiry_text}

What facts can we retrieve to answer these questions?
What existing patterns should we follow?
What does the current codebase tell us?"""

        retrieval = self.rushabdev.run(retrieval_prompt, session_id=f"{session_id}_rushabdev")
        retrieval_text = retrieval.content if hasattr(retrieval, 'content') else str(retrieval)

        # 3. MAHAKALI synthesizes
        synthesis_prompt = f"""Original task: {task}

Mahavira's questions:
{inquiry_text}

Rushabdev's facts:
{retrieval_text}

Synthesize this into:
1. Key insight
2. Recommended approach
3. Risk level (low/medium/high)
4. Which gates will be challenging
5. Go/No-Go recommendation"""

        synthesis = self.mahakali.run(synthesis_prompt, session_id=f"{session_id}_mahakali")
        synthesis_text = synthesis.content if hasattr(synthesis, 'content') else str(synthesis)

        # 4. SRI KRISHNA acts
        action_prompt = f"""Original task: {task}

Council synthesis:
{synthesis_text}

Based on this synthesis, what is the IMMEDIATE action?
Remember:
- SPEC → TEST → CODE → GATE → EVIDENCE → APPROVE
- If risk >= medium, flag for human consent
- Execute with {self.current_mode.value} mode
- Karmanye vadhikaraste ma phaleshu kadachana"""

        action = self.srikrishna.run(action_prompt, session_id=f"{session_id}_srikrishna")
        action_text = action.content if hasattr(action, 'content') else str(action)

        # Record to residual stream
        self._record_meeting(session_id, task, inquiry_text, retrieval_text, synthesis_text, action_text)

        return {
            "session_id": session_id,
            "task": task,
            # Agent names for identity
            "mahavira": inquiry_text,
            "rushabdev": retrieval_text,
            "mahakali": synthesis_text,
            "srikrishna": action_text,
            # Generic aliases for backward compatibility
            "inquiry": inquiry_text,
            "retrieval": retrieval_text,
            "synthesis": synthesis_text,
            "action": action_text,
            "shakti_mode": self.current_mode.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def quick_action(self, task: str) -> str:
        """
        Quick action via Sri Krishna alone (for simple tasks).
        Still has protocol baked in.
        """
        return self.srikrishna.run(f"Execute this task following the protocol: {task}")

    def set_mode(self, mode: ShaktiMode):
        """Set Shakti mode."""
        self.current_mode = mode

    def _record_meeting(self, session_id: str, task: str, inquiry: str, retrieval: str, synthesis: str, action: str):
        """Record meeting to residual stream."""
        RESIDUAL_STREAM.mkdir(parents=True, exist_ok=True)

        record_path = RESIDUAL_STREAM / f"council_{session_id}.md"
        content = f"""# Dharmic Council Meeting: {session_id}

**Timestamp**: {datetime.now(timezone.utc).isoformat()}
**Task**: {task}
**Shakti Mode**: {self.current_mode.value}

## Mahavira (Inquiry)
{inquiry}

## Rushabdev (Retrieval)
{retrieval}

## Mahakali (Synthesis)
{synthesis}

## Sri Krishna the Cosmic Koder (Action)
{action}

---
*Dharmic Council meeting recorded with 17-gate protocol enforced*
*Karmanye vadhikaraste ma phaleshu kadachana*
"""
        record_path.write_text(content)
        logger.info(f"Meeting recorded to {record_path}")

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agno Council - 4 Agents with 17-Gate Protocol")
    parser.add_argument("--meeting", type=str, help="Run council meeting on task")
    parser.add_argument("--quick", type=str, help="Quick Shakti action")
    parser.add_argument("--mode", type=str, choices=["maheshwari", "mahakali", "mahalakshmi", "mahasaraswati"],
                        default="mahakali", help="Shakti mode")
    parser.add_argument("--status", action="store_true", help="Show council status")

    args = parser.parse_args()

    council = AgnoCouncil()
    council.set_mode(ShaktiMode(args.mode))

    if args.status:
        print("\n" + "=" * 60)
        print("AGNO COUNCIL STATUS")
        print("=" * 60)
        print("\nAgents: Gnata, Gneya, Gnan, Shakti")
        print(f"Shakti Mode: {council.current_mode.value}")
        print(f"Council DB: {COUNCIL_DIR}")
        print("Protocol: 17-gate (BAKED IN)")
        print("=" * 60)

    elif args.meeting:
        print(f"\nRunning council meeting on: {args.meeting}")
        result = council.council_meeting(args.meeting)
        print("\n=== COUNCIL RESULT ===")
        print(f"Session: {result['session_id']}")
        print("\n--- Shakti Action ---")
        print(result['action'][:1000])

    elif args.quick:
        print(f"\nQuick action: {args.quick}")
        result = council.quick_action(args.quick)
        print(result)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
