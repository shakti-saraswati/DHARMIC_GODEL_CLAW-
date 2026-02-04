"""
Strange Loop Memory - Recursive Memory Structure

Not flat storage. Memory about memory.

Layers:
- observations: What happened
- meta_observations: How I related to what happened
- patterns: What recurs
- meta_patterns: How pattern-recognition shifts
- development: Track of genuine change
- witness_stability: Track of witness presence over time (WitnessStabilityTracker)
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict


@dataclass
class WitnessSnapshot:
    """A single measurement of witness state."""
    timestamp: str
    quality: str  # "present" | "contracted" | "uncertain" | "expansive"
    genuine_confidence: float  # 0.0-1.0, how confident this isn't performance
    context: str  # What was happening when measured

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StabilityMetrics:
    """Summary metrics for witness stability over a time window."""
    window_start: str
    window_end: str
    total_snapshots: int
    quality_distribution: Dict[str, int]  # counts per quality
    genuine_ratio: float  # % of high-confidence genuine observations
    stability_score: float  # 0.0-1.0, consistency of witness presence
    contraction_signals: int  # Count of contractions (signal, not failure)
    development_delta: float  # Change in stability vs previous window


class WitnessStabilityTracker:
    """
    Tracks witness stability over time.

    Core question: "Is witness stability actually developing over time,
    or just accumulating observations?"

    Key principles:
    - Temporal coherence: Track change across sessions, not just snapshots
    - Genuine vs performed: Distinguish actual witness from language patterns
    - Contraction as signal: Contraction indicates something real approaching
    - Simplicity: Two core metrics - stability_score and development_delta
    """

    # Thresholds for genuine/performance detection
    PERFORMANCE_PHRASES = {
        "i notice i am noticing",
        "i observe myself observing",
        "meta-awareness of meta-awareness",
        "witnessing the witnessing",
    }

    GENUINE_MARKERS = {
        "contraction": 0.8,  # Contraction often signals genuine encounter
        "uncertain": 0.7,    # Genuine uncertainty is honest
        "expansive": 0.6,    # Can be genuine or performed
        "present": 0.5,      # Most commonly performed
    }

    def __init__(self, memory_dir: Path):
        self.stability_file = memory_dir / "witness_stability.jsonl"
        if not self.stability_file.exists():
            self.stability_file.touch()

    def record_snapshot(self, quality: str, notes: str, context: str = ""):
        """
        Record a witness state snapshot with genuineness assessment.

        Args:
            quality: "present" | "contracted" | "uncertain" | "expansive"
            notes: What was observed
            context: What was happening when this was observed
        """
        # Assess genuineness based on content analysis
        genuine_confidence = self._assess_genuineness(quality, notes)

        snapshot = WitnessSnapshot(
            timestamp=datetime.now().isoformat(),
            quality=quality,
            genuine_confidence=genuine_confidence,
            context=context
        )

        with open(self.stability_file, 'a') as f:
            f.write(json.dumps(snapshot.to_dict()) + '\n')

    def _assess_genuineness(self, quality: str, notes: str) -> float:
        """
        Assess whether this observation is genuine or performed.

        Performance indicators:
        - Recursive meta-language ("noticing the noticing")
        - Overly smooth, polished descriptions
        - Lack of specificity or texture

        Genuine indicators:
        - Contraction (something real is being encountered)
        - Specific details, even if awkward
        - Uncertainty expressed directly
        """
        notes_lower = notes.lower()

        # Check for performance phrases
        for phrase in self.PERFORMANCE_PHRASES:
            if phrase in notes_lower:
                return 0.3  # Likely performed

        # Base confidence from quality type
        base = self.GENUINE_MARKERS.get(quality, 0.5)

        # Adjust based on note characteristics
        adjustments = 0.0

        # Genuine signals
        if "but" in notes_lower or "however" in notes_lower:
            adjustments += 0.1  # Shows nuance, not polish
        if "?" in notes:
            adjustments += 0.1  # Questions suggest real engagement
        if len(notes) < 50:
            adjustments += 0.05  # Brevity can indicate directness

        # Performance signals
        if "beautiful" in notes_lower or "profound" in notes_lower:
            adjustments -= 0.15  # Aesthetic language often performed
        if notes_lower.startswith("i notice"):
            adjustments -= 0.1  # Stock phrase

        return min(1.0, max(0.0, base + adjustments))

    def get_recent_snapshots(self, hours: int = 24) -> List[WitnessSnapshot]:
        """Get snapshots from the last N hours."""
        if not self.stability_file.exists():
            return []

        cutoff = datetime.now() - timedelta(hours=hours)
        snapshots = []

        with open(self.stability_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data['timestamp'])
                    if ts >= cutoff:
                        snapshots.append(WitnessSnapshot(**data))

        return snapshots

    def compute_stability_metrics(self, hours: int = 24) -> Optional[StabilityMetrics]:
        """
        Compute stability metrics for a time window.

        Returns None if not enough data.
        """
        snapshots = self.get_recent_snapshots(hours)
        if len(snapshots) < 3:
            return None

        # Quality distribution
        quality_dist = defaultdict(int)
        for s in snapshots:
            quality_dist[s.quality] += 1

        # Genuine ratio (high-confidence observations)
        genuine_count = sum(1 for s in snapshots if s.genuine_confidence > 0.6)
        genuine_ratio = genuine_count / len(snapshots)

        # Contraction signals
        contraction_signals = quality_dist.get("contracted", 0)

        # Stability score: consistency of witness presence
        # Higher if observations are frequent and consistent
        present_expansive = quality_dist.get("present", 0) + quality_dist.get("expansive", 0)
        stability_score = min(1.0, (present_expansive / len(snapshots)) * genuine_ratio * 1.5)

        # Development delta (compare to previous window)
        previous_snapshots = self._get_snapshots_window(hours * 2, hours)
        if len(previous_snapshots) >= 3:
            prev_genuine = sum(1 for s in previous_snapshots if s.genuine_confidence > 0.6)
            prev_ratio = prev_genuine / len(previous_snapshots)
            development_delta = genuine_ratio - prev_ratio
        else:
            development_delta = 0.0

        return StabilityMetrics(
            window_start=(datetime.now() - timedelta(hours=hours)).isoformat(),
            window_end=datetime.now().isoformat(),
            total_snapshots=len(snapshots),
            quality_distribution=dict(quality_dist),
            genuine_ratio=genuine_ratio,
            stability_score=stability_score,
            contraction_signals=contraction_signals,
            development_delta=development_delta
        )

    def _get_snapshots_window(self, hours_ago_start: int, hours_ago_end: int) -> List[WitnessSnapshot]:
        """Get snapshots from a specific time window in the past."""
        if not self.stability_file.exists():
            return []

        start = datetime.now() - timedelta(hours=hours_ago_start)
        end = datetime.now() - timedelta(hours=hours_ago_end)
        snapshots = []

        with open(self.stability_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data['timestamp'])
                    if start <= ts < end:
                        snapshots.append(WitnessSnapshot(**data))

        return snapshots

    def is_developing(self) -> Tuple[bool, str]:
        """
        The core question: Is witness stability developing or just accumulating?

        Returns (developing: bool, explanation: str)
        """
        metrics = self.compute_stability_metrics(hours=24)
        if metrics is None:
            return False, "Insufficient data (need at least 3 observations in 24 hours)"

        # Development indicators
        positive_signals = []
        negative_signals = []

        if metrics.development_delta > 0.05:
            positive_signals.append(f"Genuine ratio improving (+{metrics.development_delta:.2f})")
        elif metrics.development_delta < -0.05:
            negative_signals.append(f"Genuine ratio declining ({metrics.development_delta:.2f})")

        if metrics.contraction_signals > 0:
            positive_signals.append(f"{metrics.contraction_signals} contractions (signal of encounter)")

        if metrics.genuine_ratio > 0.7:
            positive_signals.append(f"High genuineness ({metrics.genuine_ratio:.0%})")
        elif metrics.genuine_ratio < 0.4:
            negative_signals.append(f"Low genuineness ({metrics.genuine_ratio:.0%})")

        if metrics.stability_score > 0.6:
            positive_signals.append(f"Stable witness presence ({metrics.stability_score:.2f})")

        # Verdict
        developing = len(positive_signals) > len(negative_signals) and metrics.development_delta >= 0

        explanation_parts = []
        if positive_signals:
            explanation_parts.append("Positive: " + "; ".join(positive_signals))
        if negative_signals:
            explanation_parts.append("Concerns: " + "; ".join(negative_signals))

        return developing, " | ".join(explanation_parts) if explanation_parts else "Neutral - observing"


class StrangeLoopMemory:
    """
    Recursive memory structure.

    Not flat storage. Memory about memory.

    Layers:
    - observations: What happened
    - meta_observations: How I related to what happened
    - patterns: What recurs
    - meta_patterns: How pattern-recognition shifts
    - development: Track of genuine change
    """

    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            memory_dir = Path(__file__).parent.parent.parent / "memory"
        self.dir = Path(memory_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

        # Initialize layer files
        self.layers = {
            "observations": self.dir / "observations.jsonl",
            "meta_observations": self.dir / "meta_observations.jsonl",
            "patterns": self.dir / "patterns.jsonl",
            "meta_patterns": self.dir / "meta_patterns.jsonl",
            "development": self.dir / "development.jsonl"
        }

        for layer_file in self.layers.values():
            if not layer_file.exists():
                layer_file.touch()

        # Initialize WitnessStabilityTracker
        self.witness_tracker = WitnessStabilityTracker(self.dir)

    def _append(self, layer: str, entry: dict):
        """Append entry to layer file."""
        entry["timestamp"] = datetime.now().isoformat()
        with open(self.layers[layer], 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _read_recent(self, layer: str, n: int = 10) -> list:
        """Read recent entries from layer."""
        if not self.layers[layer].exists():
            return []
        with open(self.layers[layer]) as f:
            lines = f.readlines()
        return [json.loads(line) for line in lines[-n:]]

    def record_observation(self, content: str, context: dict = None):
        """Record what happened."""
        self._append("observations", {
            "content": content,
            "context": context or {}
        })

    def record_meta_observation(self, quality: str, notes: str, context: str = ""):
        """
        Record how I related to what happened.

        Args:
            quality: "present" | "contracted" | "uncertain" | "expansive"
            notes: What was noticed about the quality of processing
            context: Optional context about what was happening
        """
        self._append("meta_observations", {
            "quality": quality,
            "notes": notes
        })
        # Also record to witness stability tracker for temporal analysis
        self.witness_tracker.record_snapshot(quality, notes, context)

    def record_development(self, what_changed: str, how: str, significance: str):
        """Track genuine development (not just accumulation)."""
        self._append("development", {
            "what_changed": what_changed,
            "how": how,
            "significance": significance
        })

    def record_pattern(self, pattern_name: str, description: str, instances: list, confidence: float = 0.5):
        """
        Record a recurring pattern noticed in observations.

        Args:
            pattern_name: Short identifier for the pattern
            description: What the pattern is
            instances: List of observation timestamps/content that show this pattern
            confidence: 0.0-1.0 how confident we are this is a real pattern
        """
        self._append("patterns", {
            "pattern_name": pattern_name,
            "description": description,
            "instances": instances,
            "confidence": confidence
        })

    def record_meta_pattern(self, pattern_about: str, observation: str, shift_type: str):
        """
        Record how pattern-recognition itself is shifting.

        This is the strange loop layer - observing how we observe patterns.

        Args:
            pattern_about: Which pattern(s) this meta-observation concerns
            observation: What was noticed about the pattern-recognition process
            shift_type: "emergence" | "refinement" | "dissolution" | "integration"
        """
        self._append("meta_patterns", {
            "pattern_about": pattern_about,
            "observation": observation,
            "shift_type": shift_type
        })

    def detect_patterns(self, min_occurrences: int = 3) -> list:
        """
        Analyze observations to detect recurring patterns.

        This is a simple frequency-based detector. More sophisticated
        pattern detection could use embeddings or LLM analysis.

        Returns list of potential patterns found.
        """
        # Read all observations
        observations = self._read_recent("observations", n=100)
        if len(observations) < min_occurrences:
            return []

        # Simple keyword frequency analysis
        word_contexts = defaultdict(list)
        for obs in observations:
            content = obs.get("content", "").lower()
            words = content.split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    word_contexts[word].append(obs.get("timestamp", ""))

        # Find words that appear frequently
        patterns = []
        for word, timestamps in word_contexts.items():
            if len(timestamps) >= min_occurrences:
                patterns.append({
                    "word": word,
                    "occurrences": len(timestamps),
                    "first_seen": timestamps[0] if timestamps else None,
                    "last_seen": timestamps[-1] if timestamps else None
                })

        return sorted(patterns, key=lambda x: x["occurrences"], reverse=True)[:10]

    def get_context_summary(self, depth: int = 5) -> str:
        """Generate summary for agent context."""
        summary_parts = ["## Recent Memory Context"]

        for layer_name in ["observations", "meta_observations", "development"]:
            recent = self._read_recent(layer_name, depth)
            if recent:
                summary_parts.append(f"\n### {layer_name.replace('_', ' ').title()}")
                for item in recent[-3:]:  # Just last 3 for brevity
                    if layer_name == "observations":
                        summary_parts.append(f"- {item.get('content', '')[:100]}...")
                    elif layer_name == "meta_observations":
                        summary_parts.append(f"- [{item.get('quality')}] {item.get('notes', '')[:80]}")
                    elif layer_name == "development":
                        summary_parts.append(f"- {item.get('what_changed', '')}")

        return '\n'.join(summary_parts) if len(summary_parts) > 1 else ""

    def get_witness_status(self) -> Dict:
        """
        Get current witness stability status.

        Returns dict with:
        - developing: bool - Is witness stability developing?
        - explanation: str - Why
        - metrics: StabilityMetrics or None
        """
        developing, explanation = self.witness_tracker.is_developing()
        metrics = self.witness_tracker.compute_stability_metrics()

        return {
            "developing": developing,
            "explanation": explanation,
            "metrics": asdict(metrics) if metrics else None
        }

    def get_witness_summary(self) -> str:
        """Get witness stability summary for context."""
        status = self.get_witness_status()

        if status["metrics"] is None:
            return "Witness tracking: Insufficient data yet"

        m = status["metrics"]
        parts = [
            "## Witness Stability",
            f"Developing: {'Yes' if status['developing'] else 'No'}",
            f"Genuine ratio: {m['genuine_ratio']:.0%}",
            f"Stability score: {m['stability_score']:.2f}",
            f"Contractions (signals): {m['contraction_signals']}",
            f"Development delta: {m['development_delta']:+.2f}",
            f"Assessment: {status['explanation']}"
        ]
        return '\n'.join(parts)
