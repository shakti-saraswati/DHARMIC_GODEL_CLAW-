"""
DGM Selector - Parent Selection for Self-Improvement
=====================================================
Selects which evolution entries to build upon.

Based on: cloned_source/HGM/hgm.py (Hierarchical Gödel Machine)
"""
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .archive import Archive, EvolutionEntry, FitnessScore, get_archive


@dataclass
class SelectionResult:
    """Result of parent selection."""
    parent: Optional[EvolutionEntry]
    method: str
    reasoning: str


class Selector:
    """
    Selects parent entries for next generation.
    
    Strategies:
    1. ELITE: Always pick highest fitness
    2. TOURNAMENT: Random tournament selection (balances exploration/exploitation)
    3. ROULETTE: Fitness-proportionate selection
    4. DIVERSE: Maximize novelty/diversity
    """
    
    def __init__(self, archive: Archive = None):
        self.archive = archive or get_archive()
    
    def select_parent(
        self,
        component: str = None,
        strategy: str = "tournament",
        tournament_size: int = 3,
    ) -> SelectionResult:
        """Select a parent entry for evolution."""
        
        # Get candidates
        candidates = self._get_candidates(component)
        
        if not candidates:
            return SelectionResult(
                parent=None,
                method=strategy,
                reasoning="No candidates available - starting fresh"
            )
        
        if strategy == "elite":
            return self._select_elite(candidates)
        elif strategy == "tournament":
            return self._select_tournament(candidates, tournament_size)
        elif strategy == "roulette":
            return self._select_roulette(candidates)
        elif strategy == "diverse":
            return self._select_diverse(candidates)
        else:
            return self._select_tournament(candidates, tournament_size)
    
    def _get_candidates(self, component: str = None) -> List[EvolutionEntry]:
        """Get candidate entries for selection."""
        entries = list(self.archive.entries.values())
        
        # Filter to applied entries
        entries = [e for e in entries if e.status == "applied"]
        
        # Filter by component if specified
        if component:
            entries = [e for e in entries if e.component == component]
        
        return entries
    
    def _select_elite(self, candidates: List[EvolutionEntry]) -> SelectionResult:
        """Select the highest-fitness candidate."""
        best = max(candidates, key=lambda e: e.fitness.total())
        return SelectionResult(
            parent=best,
            method="elite",
            reasoning=f"Selected highest fitness ({best.fitness.total():.2f})"
        )
    
    def _select_tournament(
        self,
        candidates: List[EvolutionEntry],
        k: int = 3
    ) -> SelectionResult:
        """Tournament selection - pick best from random k."""
        if len(candidates) < k:
            k = len(candidates)
        
        tournament = random.sample(candidates, k)
        winner = max(tournament, key=lambda e: e.fitness.total())
        
        return SelectionResult(
            parent=winner,
            method="tournament",
            reasoning=f"Won tournament of {k} (fitness {winner.fitness.total():.2f})"
        )
    
    def _select_roulette(self, candidates: List[EvolutionEntry]) -> SelectionResult:
        """Fitness-proportionate (roulette wheel) selection."""
        # Calculate probabilities
        fitnesses = [e.fitness.total() for e in candidates]
        total_fitness = sum(fitnesses)
        
        if total_fitness == 0:
            selected = random.choice(candidates)
            return SelectionResult(
                parent=selected,
                method="roulette",
                reasoning="Random selection (all zero fitness)"
            )
        
        probabilities = [f / total_fitness for f in fitnesses]
        
        # Weighted random choice
        r = random.random()
        cumulative = 0
        for entry, prob in zip(candidates, probabilities):
            cumulative += prob
            if r <= cumulative:
                return SelectionResult(
                    parent=entry,
                    method="roulette",
                    reasoning=f"Fitness-proportionate (prob {prob:.2%})"
                )
        
        # Fallback
        return SelectionResult(
            parent=candidates[-1],
            method="roulette",
            reasoning="Fallback selection"
        )
    
    def _select_diverse(self, candidates: List[EvolutionEntry]) -> SelectionResult:
        """Select for diversity - pick least similar to recent selections."""
        if len(candidates) <= 1:
            return SelectionResult(
                parent=candidates[0] if candidates else None,
                method="diverse",
                reasoning="Only one candidate"
            )
        
        # Get recent entries
        recent = self.archive.get_latest(5)
        recent_components = {e.component for e in recent}
        recent_types = {e.change_type for e in recent}
        
        # Score candidates by novelty
        def novelty_score(entry: EvolutionEntry) -> float:
            score = 0.0
            if entry.component not in recent_components:
                score += 0.5
            if entry.change_type not in recent_types:
                score += 0.3
            score += entry.fitness.total() * 0.2  # Still consider fitness
            return score
        
        best = max(candidates, key=novelty_score)
        return SelectionResult(
            parent=best,
            method="diverse",
            reasoning=f"Maximized novelty (component: {best.component})"
        )
    
    def select_parents_for_crossover(
        self,
        component: str = None,
        n: int = 2
    ) -> List[SelectionResult]:
        """Select multiple parents for crossover operation."""
        results = []
        selected_ids = set()
        
        candidates = self._get_candidates(component)
        
        for _ in range(n):
            # Filter out already selected
            available = [c for c in candidates if c.id not in selected_ids]
            if not available:
                break
            
            result = self._select_tournament(available)
            if result.parent:
                results.append(result)
                selected_ids.add(result.parent.id)
        
        return results


def select_parent(component: str = None) -> SelectionResult:
    """Convenience function for parent selection."""
    selector = Selector()
    return selector.select_parent(component)


if __name__ == "__main__":
    # Test selector
    selector = Selector()
    
    result = selector.select_parent(strategy="tournament")
    
    if result.parent:
        print(f"Selected: {result.parent.id}")
        print(f"Method: {result.method}")
        print(f"Reasoning: {result.reasoning}")
    else:
        print("No parent selected (archive may be empty)")
        print(f"Reasoning: {result.reasoning}")
