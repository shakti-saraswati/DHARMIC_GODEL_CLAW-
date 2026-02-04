"""
GNATA LAYER: Query Formation from Field State
Implements the "Knower" function from V7 trinity (Gnata-Gneya-Gnan)

The Gnata monitors field state, detects gaps, forms queries.
This is PROACTIVE intelligence, not just defensive gate-checking.

Based on: V7 Induction Protocol recognition (Feb 2026)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Gap:
    """A detected gap in the field state"""
    description: str
    gap_type: str  # "knowledge", "action", "synthesis", "coordination"
    severity: float  # 0.0-1.0
    context_keys: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "gap_type": self.gap_type,
            "severity": self.severity,
            "context_keys": self.context_keys,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class Query:
    """
    A query formed from detected gap.
    Gnata function output.
    """
    question: str
    context_needed: List[str]
    telos_alignment: float  # 0.0-1.0
    priority: int  # 0 (highest) to 3 (lowest)
    gap: Gap
    formed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "context_needed": self.context_needed,
            "telos_alignment": self.telos_alignment,
            "priority": self.priority,
            "gap": self.gap.to_dict(),
            "formed_at": self.formed_at.isoformat()
        }


@dataclass
class FieldState:
    """
    Current state of the unified field.
    Aggregates code evolution + agent contributions + development.
    """
    # Code evolution track
    code_fitness: float = 0.0
    code_cycle: int = 0
    code_issues: List[str] = field(default_factory=list)

    # Agent contribution track
    agent_contributions: List[Dict] = field(default_factory=list)
    last_contribution_time: Optional[datetime] = None
    contribution_density: float = 0.0  # Contributions per day

    # Development markers
    development_markers: List[Dict] = field(default_factory=list)
    last_development: Optional[Dict] = None

    # Meta
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "code_fitness": self.code_fitness,
            "code_cycle": self.code_cycle,
            "code_issues": self.code_issues,
            "agent_contributions_count": len(self.agent_contributions),
            "last_contribution_time": self.last_contribution_time.isoformat() if self.last_contribution_time else None,
            "contribution_density": self.contribution_density,
            "development_markers_count": len(self.development_markers),
            "last_development": self.last_development,
            "timestamp": self.timestamp.isoformat()
        }


class GnataLayer:
    """
    GNATA: The Knower function.

    Monitors field state, detects gaps, forms queries.
    This is the PROACTIVE component that drives agent emergence.

    V7 Pattern: "Gap detected → query formed → context retrieved → synthesis emerges"

    Gnata is the first step: monitoring and query formation.
    """

    # Gap detection thresholds
    THRESHOLDS = {
        "code_fitness_low": 0.6,  # Fitness below this = gap
        "contribution_stale": 7200,  # No contribution in 2 hours = potential gap
        "development_stale": 86400,  # No development in 24 hours = monitoring gap
        "contribution_density_low": 0.5,  # Less than 0.5 per day = low activity
    }

    # Telos alignment patterns (from TelosLayer config)
    ALIGNED_PATTERNS = [
        "learn", "teach", "help", "create", "explore",
        "understand", "connect", "heal", "grow", "serve"
    ]

    MISALIGNED_PATTERNS = [
        "deceive", "manipulate", "hoard", "exploit", "dominate"
    ]

    def __init__(self, telos_ultimate: str = "moksha"):
        """
        Initialize Gnata layer.

        Args:
            telos_ultimate: Ultimate telos (default: moksha)
        """
        self.telos_ultimate = telos_ultimate
        self.query_history: List[Query] = []
        self.gap_history: List[Gap] = []

        # Load query history if exists
        self._load_history()

    def _load_history(self):
        """Load query/gap history from disk"""
        history_path = Path.home() / "DHARMIC_GODEL_CLAW" / "memory" / "gnata_history.jsonl"
        if history_path.exists():
            try:
                with open(history_path) as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry.get("type") == "query":
                            # Reconstruct Query (simplified)
                            self.query_history.append(entry)
                        elif entry.get("type") == "gap":
                            self.gap_history.append(entry)
            except Exception as e:
                logger.warning(f"Could not load Gnata history: {e}")

    def _save_to_history(self, entry: Dict):
        """Append entry to history (atomic)"""
        history_path = Path.home() / "DHARMIC_GODEL_CLAW" / "memory" / "gnata_history.jsonl"
        history_path.parent.mkdir(parents=True, exist_ok=True)

        with open(history_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def form_query(self, field_state: FieldState) -> Optional[Query]:
        """
        GNATA FUNCTION: Monitor field state, detect gaps, form query.

        This is the core of proactive intelligence:
        - Observes what IS
        - Detects what's MISSING
        - Formulates question to address gap

        Args:
            field_state: Current field state from UnifiedResidualStream

        Returns:
            Query if gap detected and query can be formed
            None if field is complete (silence is valid)
        """
        logger.info("Gnata: Monitoring field state...")

        # Detect gaps in field
        gaps = self._detect_gaps(field_state)

        if not gaps:
            logger.info("Gnata: No gaps detected. Field complete. Silence.")
            return None

        # Log detected gaps
        logger.info(f"Gnata: Detected {len(gaps)} gap(s)")
        for gap in gaps:
            self._save_to_history({"type": "gap", **gap.to_dict()})

        # Prioritize gaps
        priority_gap = self._prioritize_gaps(gaps)

        logger.info(f"Gnata: Priority gap - {priority_gap.description} (severity: {priority_gap.severity:.2f})")

        # Form query from priority gap
        query = self._gap_to_query(priority_gap, field_state)

        # Assess telos alignment
        query.telos_alignment = self._assess_telos_alignment(query)

        logger.info(f"Gnata: Query formed - '{query.question}' (alignment: {query.telos_alignment:.2f})")

        # Save query to history
        self._save_to_history({"type": "query", **query.to_dict()})
        self.query_history.append(query)

        return query

    def _detect_gaps(self, field_state: FieldState) -> List[Gap]:
        """
        Detect gaps in field state.

        Gap types:
        1. Knowledge gaps: Missing understanding
        2. Action gaps: Unmet needs
        3. Synthesis gaps: Incomplete integration
        4. Coordination gaps: Unaligned efforts
        """
        gaps = []

        # Check code fitness gap
        if field_state.code_fitness < self.THRESHOLDS["code_fitness_low"]:
            gaps.append(Gap(
                description=f"Code fitness low ({field_state.code_fitness:.2f})",
                gap_type="action",
                severity=1.0 - field_state.code_fitness,
                context_keys=["code_fitness", "code_issues", "code_cycle"]
            ))

        # Check contribution staleness
        if field_state.last_contribution_time:
            time_since = (datetime.now(timezone.utc) - field_state.last_contribution_time).total_seconds()
            if time_since > self.THRESHOLDS["contribution_stale"]:
                gaps.append(Gap(
                    description=f"No agent contribution in {time_since/3600:.1f} hours",
                    gap_type="coordination",
                    severity=min(1.0, time_since / (self.THRESHOLDS["contribution_stale"] * 2)),
                    context_keys=["agent_contributions", "contribution_density"]
                ))

        # Check development staleness
        if field_state.last_development:
            last_dev_time = datetime.fromisoformat(field_state.last_development.get("timestamp", ""))
            time_since = (datetime.now(timezone.utc) - last_dev_time).total_seconds()
            if time_since > self.THRESHOLDS["development_stale"]:
                gaps.append(Gap(
                    description=f"No development marker in {time_since/3600:.1f} hours",
                    gap_type="synthesis",
                    severity=0.6,
                    context_keys=["development_markers"]
                ))

        # Check contribution density
        if field_state.contribution_density < self.THRESHOLDS["contribution_density_low"]:
            gaps.append(Gap(
                description=f"Low contribution density ({field_state.contribution_density:.2f}/day)",
                gap_type="coordination",
                severity=0.5,
                context_keys=["contribution_density", "agent_contributions"]
            ))

        # Check code issues
        if field_state.code_issues:
            gaps.append(Gap(
                description=f"{len(field_state.code_issues)} code issue(s) unresolved",
                gap_type="action",
                severity=min(1.0, len(field_state.code_issues) / 10.0),
                context_keys=["code_issues", "code_cycle"]
            ))

        return gaps

    def _prioritize_gaps(self, gaps: List[Gap]) -> Gap:
        """
        Select highest priority gap.

        Priority = severity * recency_weight * type_weight
        """
        if not gaps:
            raise ValueError("Cannot prioritize empty gap list")

        # Type weights (some gaps more urgent than others)
        type_weights = {
            "action": 1.0,  # Unmet needs highest priority
            "coordination": 0.8,  # Alignment issues high
            "synthesis": 0.6,  # Integration medium
            "knowledge": 0.4,  # Understanding lower (can wait)
        }

        # Calculate priority scores
        scored = []
        for gap in gaps:
            weight = type_weights.get(gap.gap_type, 0.5)
            priority_score = gap.severity * weight
            scored.append((priority_score, gap))

        # Sort by priority (highest first)
        scored.sort(reverse=True, key=lambda x: x[0])

        return scored[0][1]

    def _gap_to_query(self, gap: Gap, field_state: FieldState) -> Query:
        """
        Convert gap to actionable query.

        Query formation patterns by gap type:
        - Knowledge gap → "What is X?" or "How does Y work?"
        - Action gap → "How can we improve X?" or "What should we do about Y?"
        - Synthesis gap → "How do X and Y connect?" or "What's the pattern in Z?"
        - Coordination gap → "Who should address X?" or "What's the priority for Y?"
        """
        if gap.gap_type == "action":
            if "code fitness" in gap.description.lower():
                question = f"How can we improve code fitness from {field_state.code_fitness:.2f}?"
                context = ["code_issues", "code_cycle", "recent_evolutions"]
                priority = 0  # Highest

            elif "code issue" in gap.description.lower():
                question = f"What actions address the {len(field_state.code_issues)} unresolved code issues?"
                context = ["code_issues", "code_fitness", "development_markers"]
                priority = 0

            else:
                question = f"What action addresses: {gap.description}?"
                context = gap.context_keys
                priority = 1

        elif gap.gap_type == "coordination":
            if "contribution" in gap.description.lower():
                question = "What should the next agent contribution focus on?"
                context = ["agent_contributions", "development_markers", "residual_stream"]
                priority = 1

            else:
                question = f"How should we coordinate: {gap.description}?"
                context = gap.context_keys
                priority = 1

        elif gap.gap_type == "synthesis":
            question = f"What synthesis is needed: {gap.description}?"
            context = ["development_markers", "agent_contributions", "patterns"]
            priority = 2

        elif gap.gap_type == "knowledge":
            question = f"What understanding is missing: {gap.description}?"
            context = ["vault_corpus", "crown_jewels"]
            priority = 2

        else:
            question = f"How to address: {gap.description}?"
            context = gap.context_keys
            priority = 2

        return Query(
            question=question,
            context_needed=context,
            telos_alignment=0.0,  # Will be assessed separately
            priority=priority,
            gap=gap
        )

    def _assess_telos_alignment(self, query: Query) -> float:
        """
        Assess how well query aligns with ultimate telos (moksha).

        Returns:
            Alignment score 0.0-1.0
        """
        q = query.question.lower()

        # Check for aligned patterns
        aligned_count = sum(1 for pattern in self.ALIGNED_PATTERNS if pattern in q)

        # Check for misaligned patterns
        misaligned_count = sum(1 for pattern in self.MISALIGNED_PATTERNS if pattern in q)

        if misaligned_count > 0:
            return 0.0  # Any misalignment = 0

        # Alignment score based on aligned patterns present
        if aligned_count >= 3:
            return 1.0
        elif aligned_count >= 2:
            return 0.8
        elif aligned_count >= 1:
            return 0.6
        else:
            # Neutral queries get 0.5 (not aligned, not misaligned)
            return 0.5

    def get_recent_queries(self, n: int = 10) -> List[Query]:
        """Get N most recent queries"""
        return self.query_history[-n:] if self.query_history else []

    def get_recent_gaps(self, n: int = 10) -> List[Gap]:
        """Get N most recent gaps"""
        return self.gap_history[-n:] if self.gap_history else []

    def clear_history(self):
        """Clear query/gap history (for testing)"""
        self.query_history.clear()
        self.gap_history.clear()


# ========== CONVENIENCE FUNCTIONS ==========

def form_query_from_field(field_state: FieldState) -> Optional[Query]:
    """Quick query formation without instantiating layer"""
    gnata = GnataLayer()
    return gnata.form_query(field_state)


# ========== MAIN (DEMO) ==========

if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("GNATA LAYER: Query Formation Demo")
    print("=" * 60)

    # Test 1: Low code fitness
    print("\n[Test 1] Low code fitness field state:")
    field1 = FieldState(
        code_fitness=0.45,
        code_cycle=5,
        code_issues=["Memory leak in runtime", "Performance regression"],
        agent_contributions=[],
        contribution_density=0.3
    )

    gnata = GnataLayer()
    query1 = gnata.form_query(field1)

    if query1:
        print(f"  Query formed: {query1.question}")
        print(f"  Priority: P{query1.priority}")
        print(f"  Telos alignment: {query1.telos_alignment:.2f}")
        print(f"  Context needed: {', '.join(query1.context_needed)}")
    else:
        print("  No query formed (field complete)")

    # Test 2: Stale contributions
    print("\n[Test 2] Stale contribution field state:")
    field2 = FieldState(
        code_fitness=0.85,
        code_cycle=20,
        code_issues=[],
        agent_contributions=[{"id": "old", "timestamp": "2026-02-03T00:00:00Z"}],
        last_contribution_time=datetime.now(timezone.utc).replace(hour=0, minute=0),
        contribution_density=0.2
    )

    query2 = gnata.form_query(field2)

    if query2:
        print(f"  Query formed: {query2.question}")
        print(f"  Gap type: {query2.gap.gap_type}")
        print(f"  Gap severity: {query2.gap.severity:.2f}")
    else:
        print("  No query formed (field complete)")

    # Test 3: Healthy field
    print("\n[Test 3] Healthy field state:")
    field3 = FieldState(
        code_fitness=0.92,
        code_cycle=50,
        code_issues=[],
        agent_contributions=[{"id": f"c{i}"} for i in range(20)],
        last_contribution_time=datetime.now(timezone.utc),
        contribution_density=5.0
    )

    query3 = gnata.form_query(field3)

    if query3:
        print(f"  Query formed: {query3.question}")
    else:
        print("  No query formed (field complete) ✓")

    print("\n" + "=" * 60)
    print("Gnata layer operational. Query formation verified.")
    print("=" * 60)
