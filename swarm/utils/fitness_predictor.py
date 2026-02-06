"""
Fitness Predictor - Learns from evolution history to predict fitness

This addresses a key DGM gap: using archive history to inform future proposals.
Instead of just logging, we learn patterns from what worked.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class FitnessPattern:
    """A pattern learned from evolution history."""
    pattern_type: str  # "file_type", "change_type", "keyword"
    pattern_value: str
    avg_fitness: float
    sample_count: int
    success_rate: float  # % that exceeded baseline


class FitnessPredictor:
    """
    Learns from evolution history to predict fitness of proposals.

    This bridges the gap between "just logging" and DGM's benchmark-driven
    selection. We use historical fitness data to guide proposal selection.
    """

    def __init__(self, stream_dir: str = None):
        if stream_dir is None:
            stream_dir = Path(__file__).parent.parent / "stream"
        self.stream_dir = Path(stream_dir)
        self.history_file = self.stream_dir / "history.jsonl"
        self.archive_dir = self.stream_dir / "archive"

        # Learned patterns
        self.patterns: Dict[str, FitnessPattern] = {}
        self.baseline_fitness = 0.765  # Default, updated from state

        # Load state
        self._load_state()
        self._learn_patterns()

    def _load_state(self):
        """Load baseline fitness from state."""
        state_file = self.stream_dir / "state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                self.baseline_fitness = state.get("baseline_fitness", 0.765)

    def _learn_patterns(self):
        """Extract patterns from evolution history."""
        if not self.history_file.exists():
            return

        # Collect data by pattern
        file_type_fitness = defaultdict(list)
        change_type_fitness = defaultdict(list)
        keyword_fitness = defaultdict(list)

        with open(self.history_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    fitness = entry.get("fitness", {})
                    if isinstance(fitness, dict):
                        total = fitness.get("total", 0)
                    else:
                        total = float(fitness) if fitness else 0

                    proposal = entry.get("proposal", "")

                    # Extract file types mentioned
                    for ext in [".py", ".yaml", ".json", ".md"]:
                        if ext in proposal:
                            file_type_fitness[ext].append(total)

                    # Extract change types
                    for change_type in ["add", "fix", "improve", "refactor", "remove"]:
                        if change_type in proposal.lower():
                            change_type_fitness[change_type].append(total)

                    # Extract keywords
                    keywords = ["test", "error", "memory", "telos", "dharmic", "agent"]
                    for kw in keywords:
                        if kw in proposal.lower():
                            keyword_fitness[kw].append(total)

                except (json.JSONDecodeError, KeyError):
                    continue

        # Convert to patterns
        for ext, scores in file_type_fitness.items():
            if scores:
                self.patterns[f"file_{ext}"] = FitnessPattern(
                    pattern_type="file_type",
                    pattern_value=ext,
                    avg_fitness=sum(scores) / len(scores),
                    sample_count=len(scores),
                    success_rate=sum(1 for s in scores if s > self.baseline_fitness) / len(scores)
                )

        for ct, scores in change_type_fitness.items():
            if scores:
                self.patterns[f"change_{ct}"] = FitnessPattern(
                    pattern_type="change_type",
                    pattern_value=ct,
                    avg_fitness=sum(scores) / len(scores),
                    sample_count=len(scores),
                    success_rate=sum(1 for s in scores if s > self.baseline_fitness) / len(scores)
                )

        for kw, scores in keyword_fitness.items():
            if scores:
                self.patterns[f"keyword_{kw}"] = FitnessPattern(
                    pattern_type="keyword",
                    pattern_value=kw,
                    avg_fitness=sum(scores) / len(scores),
                    sample_count=len(scores),
                    success_rate=sum(1 for s in scores if s > self.baseline_fitness) / len(scores)
                )

    def predict_fitness(self, proposal: str) -> Tuple[float, List[str]]:
        """
        Predict fitness of a proposal based on learned patterns.

        Returns:
            (predicted_fitness, list of contributing patterns)
        """
        if not self.patterns:
            return self.baseline_fitness, ["no_history"]

        matching_patterns = []
        weighted_sum = 0.0
        total_weight = 0.0

        proposal_lower = proposal.lower()

        for pattern_key, pattern in self.patterns.items():
            # Check if pattern matches
            matches = False
            if pattern.pattern_type == "file_type":
                matches = pattern.pattern_value in proposal
            elif pattern.pattern_type == "change_type":
                matches = pattern.pattern_value in proposal_lower
            elif pattern.pattern_type == "keyword":
                matches = pattern.pattern_value in proposal_lower

            if matches:
                # Weight by sample count (more samples = more reliable)
                weight = min(pattern.sample_count, 10) / 10.0
                weighted_sum += pattern.avg_fitness * weight
                total_weight += weight
                matching_patterns.append(f"{pattern_key}:{pattern.avg_fitness:.3f}")

        if total_weight > 0:
            predicted = weighted_sum / total_weight
        else:
            predicted = self.baseline_fitness

        return predicted, matching_patterns

    def rank_proposals(self, proposals: List[str]) -> List[Tuple[str, float, List[str]]]:
        """
        Rank multiple proposals by predicted fitness.

        Returns list of (proposal, predicted_fitness, patterns) sorted by fitness desc.
        """
        ranked = []
        for p in proposals:
            fitness, patterns = self.predict_fitness(p)
            ranked.append((p, fitness, patterns))

        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def get_high_success_patterns(self, min_success_rate: float = 0.5) -> List[FitnessPattern]:
        """Get patterns with high success rate for proposal guidance."""
        return [
            p for p in self.patterns.values()
            if p.success_rate >= min_success_rate and p.sample_count >= 2
        ]

    def get_guidance(self) -> str:
        """Generate guidance text for the proposer agent."""
        high_success = self.get_high_success_patterns(0.5)
        if not high_success:
            return "No clear patterns yet. Explore freely."

        guidance_parts = ["Based on history, these patterns tend to succeed:"]
        for p in sorted(high_success, key=lambda x: x.success_rate, reverse=True)[:5]:
            guidance_parts.append(
                f"- {p.pattern_type}={p.pattern_value}: "
                f"{p.success_rate*100:.0f}% success, avg fitness {p.avg_fitness:.3f}"
            )

        return "\n".join(guidance_parts)

    def get_stats(self) -> Dict:
        """Get predictor statistics."""
        return {
            "baseline_fitness": self.baseline_fitness,
            "patterns_learned": len(self.patterns),
            "high_success_patterns": len(self.get_high_success_patterns()),
            "top_patterns": [
                {"key": k, "fitness": p.avg_fitness, "success_rate": p.success_rate}
                for k, p in sorted(
                    self.patterns.items(),
                    key=lambda x: x[1].success_rate,
                    reverse=True
                )[:5]
            ]
        }


# CLI test
if __name__ == "__main__":
    predictor = FitnessPredictor()

    print("=" * 60)
    print("FITNESS PREDICTOR - Stats")
    print("=" * 60)

    stats = predictor.get_stats()
    print(f"Baseline fitness: {stats['baseline_fitness']:.3f}")
    print(f"Patterns learned: {stats['patterns_learned']}")
    print(f"High success patterns: {stats['high_success_patterns']}")

    if stats['top_patterns']:
        print("\nTop patterns:")
        for p in stats['top_patterns']:
            print(f"  {p['key']}: fitness={p['fitness']:.3f}, success={p['success_rate']*100:.0f}%")

    print("\n" + "=" * 60)
    print("Guidance for proposer:")
    print("=" * 60)
    print(predictor.get_guidance())

    # Test prediction
    print("\n" + "=" * 60)
    print("Test predictions:")
    print("=" * 60)

    test_proposals = [
        "Add error handling to dharmic_agent.py",
        "Improve test coverage for memory module",
        "Refactor telos.yaml structure",
        "Fix bug in agent spawning"
    ]

    for proposal, fitness, patterns in predictor.rank_proposals(test_proposals):
        print(f"\n{proposal[:50]}...")
        print(f"  Predicted fitness: {fitness:.3f}")
        print(f"  Matching patterns: {patterns}")
