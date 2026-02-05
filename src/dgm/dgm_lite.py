#!/usr/bin/env python3
"""
DGM-Lite - The Self-Improvement Loop
=====================================
Darwin-Gödel Machine implementation for DHARMIC_GODEL_CLAW.

This is the core self-improvement loop:
1. SELECT parent from archive (best fitness)
2. PROPOSE mutation/improvement
3. EVALUATE fitness (tests + dharmic gates)
4. If better AND passes gates → APPLY
5. ARCHIVE the attempt (success or failure)
6. Repeat

Based on:
- cloned_source/dgm/DGM_outer.py
- cloned_source/HGM/hgm.py

CRITICAL: All changes require CONSENT gate (human approval) by default.
"""
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any

from .archive import Archive, EvolutionEntry, get_archive
from .fitness import FitnessEvaluator
from .selector import Selector

# Use dharmic structured logging
from src.core.dharmic_logging import get_logger, log_gate_event, log_fitness

logger = get_logger("dgm_lite")


class DGMLite:
    """
    Self-improvement loop with dharmic safety gates.
    
    This is the "Gödel Machine" that can rewrite itself,
    but only through dharmic gates (consent, reversibility, etc.)
    """
    
    # Dharmic gates that must pass
    REQUIRED_GATES = ["ahimsa", "consent"]  # Minimum required
    ALL_GATES = ["ahimsa", "satya", "vyavasthit", "consent", 
                 "reversibility", "svabhaava", "witness"]
    
    def __init__(
        self,
        project_root: Path = None,
        archive: Archive = None,
        dry_run: bool = True,  # Default to dry run for safety
        require_consent: bool = True,
    ):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.archive = archive or get_archive()
        self.selector = Selector(self.archive)
        self.evaluator = FitnessEvaluator(self.project_root)
        self.dry_run = dry_run
        self.require_consent = require_consent
        
        # State
        self.current_fitness: float = 0.0
        self.generation: int = 0
        self.improvements_made: int = 0
    
    async def run_cycle(
        self,
        component: str,
        improvement_prompt: str = None,
    ) -> Dict[str, Any]:
        """
        Run one improvement cycle.
        
        1. Select parent
        2. Propose improvement
        3. Evaluate
        4. Apply if better
        5. Archive
        """
        logger.info(f"=== DGM Cycle {self.generation} ===", context={
            "generation": self.generation,
            "component": component,
            "dry_run": self.dry_run
        })
        
        result = {
            "generation": self.generation,
            "component": component,
            "success": False,
            "reason": None,
            "entry_id": None,
        }
        
        # 1. Select parent
        parent_result = self.selector.select_parent(
            component=component,
            strategy="tournament"
        )
        parent = parent_result.parent
        logger.info("Parent selected", context={
            "parent_id": parent.id if parent else None,
            "starting_fresh": parent is None
        })
        
        # 2. Create evolution entry (proposal stage)
        entry = EvolutionEntry(
            id="",
            timestamp="",
            parent_id=parent.id if parent else None,
            component=component,
            change_type="mutation",
            description=improvement_prompt or "Automated improvement",
            status="proposed",
        )
        
        # 3. Evaluate current fitness
        eval_result = self.evaluator.evaluate(component, run_tests=True)
        entry.fitness = eval_result.score
        entry.gates_passed = eval_result.gates_passed
        entry.gates_failed = eval_result.gates_failed
        entry.test_results = {
            "passed": eval_result.tests_passed,
            "failed": eval_result.tests_failed,
        }
        
        log_fitness(logger, eval_result.score.total(), component=component, breakdown={
            "correctness": eval_result.score.correctness,
            "dharmic_alignment": eval_result.score.dharmic_alignment,
            "elegance": eval_result.score.elegance,
            "efficiency": eval_result.score.efficiency,
            "safety": eval_result.score.safety,
        })
        
        for gate in eval_result.gates_passed:
            log_gate_event(logger, gate, passed=True, component=component)
        for gate in eval_result.gates_failed:
            log_gate_event(logger, gate, passed=False, component=component)
        
        # 4. Check dharmic gates
        for gate in self.REQUIRED_GATES:
            if gate not in eval_result.gates_passed:
                result["reason"] = f"Required gate '{gate}' not passed"
                logger.dharmic(f"Required gate failed: {gate}", gate=gate, result=False, context={
                    "component": component,
                    "required": True
                })
                entry.status = "rejected"
                self.archive.add_entry(entry)
                result["entry_id"] = entry.id
                return result
        
        # 5. Check consent gate
        if self.require_consent and "consent" not in eval_result.gates_passed:
            if self.dry_run:
                logger.info("DRY RUN: Would require human consent")
                entry.status = "needs_consent"
            else:
                result["reason"] = "Consent gate requires human approval"
                logger.warning(result["reason"])
                entry.status = "awaiting_consent"
                self.archive.add_entry(entry)
                result["entry_id"] = entry.id
                result["needs_consent"] = True
                return result
        
        # 6. Compare to parent fitness
        if parent:
            parent_fitness = parent.fitness.total()
            current_fitness = eval_result.score.total()
            
            if current_fitness <= parent_fitness:
                result["reason"] = f"No improvement ({current_fitness:.2f} <= {parent_fitness:.2f})"
                logger.info(result["reason"])
                entry.status = "no_improvement"
                self.archive.add_entry(entry)
                result["entry_id"] = entry.id
                return result
        
        # 7. Apply improvement
        if self.dry_run:
            logger.info("DRY RUN: Would apply improvement")
            entry.status = "dry_run"
        else:
            # In real implementation, this would:
            # - Create backup
            # - Apply changes
            # - Run tests
            # - Commit
            entry.status = "applied"
            self.improvements_made += 1
        
        # 8. Archive
        entry_id = self.archive.add_entry(entry)
        result["entry_id"] = entry_id
        result["success"] = True
        result["fitness"] = eval_result.score.total()
        
        logger.info(f"Archived: {entry_id}")
        
        self.generation += 1
        return result
    
    async def run_loop(
        self,
        components: list,
        max_generations: int = 10,
        improvement_threshold: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Run multiple improvement cycles.
        """
        results = []
        no_improvement_count = 0
        
        for gen in range(max_generations):
            for component in components:
                result = await self.run_cycle(component)
                results.append(result)
                
                if result["success"]:
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
                
                # Early stopping if stuck
                if no_improvement_count >= len(components) * 3:
                    logger.info("No improvements for 3 rounds - stopping")
                    break
            
            if no_improvement_count >= len(components) * 3:
                break
        
        return {
            "generations": self.generation,
            "improvements": self.improvements_made,
            "results": results,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current DGM status."""
        return {
            "generation": self.generation,
            "improvements_made": self.improvements_made,
            "archive_size": len(self.archive.entries),
            "dry_run": self.dry_run,
            "require_consent": self.require_consent,
            "best_entries": [
                {"id": e.id, "fitness": e.fitness.total(), "component": e.component}
                for e in self.archive.get_best(5)
            ],
        }


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="DGM-Lite Self-Improvement Loop")
    parser.add_argument("--component", "-c", help="Component to improve")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Don't apply changes (default: True)")
    parser.add_argument("--live", action="store_true",
                       help="Actually apply changes (CAREFUL!)")
    parser.add_argument("--generations", "-g", type=int, default=1,
                       help="Number of generations")
    parser.add_argument("--status", action="store_true",
                       help="Show DGM status")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    dgm = DGMLite(dry_run=dry_run)
    
    if args.status:
        status = dgm.get_status()
        print("\n=== DGM-Lite Status ===")
        print(f"Generation: {status['generation']}")
        print(f"Improvements: {status['improvements_made']}")
        print(f"Archive size: {status['archive_size']}")
        print(f"Mode: {'DRY RUN' if status['dry_run'] else 'LIVE'}")
        print("\nBest entries:")
        for entry in status['best_entries']:
            print(f"  - {entry['id']}: {entry['fitness']:.2f} ({entry['component']})")
        return
    
    if args.component:
        result = await dgm.run_cycle(args.component)
        print(f"\nResult: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Reason: {result.get('reason', 'N/A')}")
        print(f"Entry ID: {result.get('entry_id')}")
    else:
        print("Specify --component or --status")
        print("Example: python -m src.dgm.dgm_lite --component src/dgm/archive.py --dry-run")


if __name__ == "__main__":
    asyncio.run(main())
