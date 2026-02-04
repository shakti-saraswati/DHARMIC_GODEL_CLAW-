"""DGM Integration - Bridges Swarm Orchestrator with Self-Improvement Loop.

Connects the swarm's proposal/evaluation workflow with DGM's
dharmic gates and evolutionary archive. This is the key integration
point between swarm self-improvement and Darwin-Gödel evolution.

The bridge responsibilities:
1. Converts swarm proposals → EvolutionEntry (standardized format)
2. Evaluates fitness through 5 dimensions:
   - correctness (0.35) - Tests pass?
   - dharmic_alignment (0.20) - 7 gates satisfied?
   - elegance (0.15) - Code quality
   - efficiency (0.15) - Performance impact
   - safety (0.15) - No regressions?
3. Archives successful patterns for future lineage-based selection
4. Provides run_evolution_cycle() for full orchestrator integration
5. Tracks parent→child relationships for evolutionary lineage

Key Classes:
- SwarmDGMBridge: Main bridge coordinator
- SwarmProposal: Normalized proposal format from swarm agents

Key Functions:
- evolve_with_swarm(): Convenience function for single evolution cycle

Dharmic Gates Enforced:
- AHIMSA (required) - Must not cause harm
- SATYA (required) - Must be truthful
- VYAVASTHIT - Should allow, not force
- CONSENT - Should have permission
- REVERSIBILITY - Should be undoable
- SVABHAAVA - Should align with telos
- WITNESS - Self-observing (always passes)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# DGM imports
from src.dgm.dgm_lite import DGMLite
from src.dgm.archive import (
    Archive,
    EvolutionEntry,
    FitnessScore,
    get_archive,
)

# Swarm imports - must use relative within package
from .orchestrator import SwarmOrchestrator, WorkflowResult, WorkflowState

logger = logging.getLogger(__name__)


@dataclass
class SwarmProposal:
    """Normalized proposal format from swarm agents."""
    
    component: str              # Target file/module
    description: str            # What the change does
    change_type: str = "mutation"  # mutation, refactor, optimization
    diff: str = ""              # Unified diff if available
    agent_id: str = ""          # Which swarm agent proposed this
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SwarmDGMBridge:
    """
    Bridge between swarm orchestrator and DGM evolution loop.
    
    Responsibilities:
    - Convert swarm workflow results to evolution entries
    - Evaluate fitness using DGM's multi-dimensional scoring
    - Apply dharmic gates to filter proposals
    - Archive successful patterns for lineage tracking
    """
    
    # Fitness weights tuned for swarm output
    FITNESS_WEIGHTS = {
        "correctness": 0.35,       # Tests pass?
        "dharmic_alignment": 0.20, # Gates satisfied?
        "elegance": 0.15,          # Code quality metrics
        "efficiency": 0.15,        # Performance impact
        "safety": 0.15,            # No regressions?
    }
    
    def __init__(
        self,
        archive: Archive = None,
        dgm: DGMLite = None,
        project_root: Path = None,
        dry_run: bool = True,
    ):
        """Initialize the bridge.
        
        Args:
            archive: Evolution archive (uses singleton if None)
            dgm: DGMLite instance (creates new if None)
            project_root: Project root path
            dry_run: If True, don't actually apply changes
        """
        self.archive = archive or get_archive()
        self.project_root = project_root or Path(__file__).parent.parent
        self.dry_run = dry_run
        
        # Initialize DGM with shared archive
        self.dgm = dgm or DGMLite(
            project_root=self.project_root,
            archive=self.archive,
            dry_run=dry_run,
        )
        
        # Track bridge metrics
        self.proposals_processed = 0
        self.entries_archived = 0
        self.successful_evolutions = 0
        
        logger.info(f"SwarmDGMBridge initialized (dry_run={dry_run})")
    
    def proposal_to_entry(
        self,
        proposal: SwarmProposal,
        parent_id: Optional[str] = None,
    ) -> EvolutionEntry:
        """Convert a swarm proposal to an EvolutionEntry.
        
        Args:
            proposal: Normalized swarm proposal
            parent_id: ID of parent entry in evolution lineage
            
        Returns:
            EvolutionEntry ready for evaluation
        """
        entry = EvolutionEntry(
            id="",  # Will be generated on archive
            timestamp="",  # Will be set on archive
            parent_id=parent_id,
            component=proposal.component,
            change_type=proposal.change_type,
            description=proposal.description,
            diff=proposal.diff,
            agent_id=proposal.agent_id,
            model=proposal.metadata.get("model", "swarm"),
            tokens_used=proposal.metadata.get("tokens_used", 0),
            status="proposed",
            fitness=FitnessScore(),  # Will be evaluated
        )
        
        return entry
    
    def workflow_result_to_entry(
        self,
        result: WorkflowResult,
        component: str = "swarm_cycle",
        parent_id: Optional[str] = None,
    ) -> EvolutionEntry:
        """Convert a WorkflowResult to an EvolutionEntry.
        
        Args:
            result: Result from swarm orchestrator cycle
            component: Component identifier
            parent_id: Parent entry ID for lineage
            
        Returns:
            EvolutionEntry with fitness populated from result
        """
        # Extract metrics
        metrics = result.metrics or {}
        
        # Calculate fitness dimensions from workflow result
        fitness = self._calculate_fitness(result)
        
        # Determine change type based on workflow
        if result.files_changed:
            change_type = "mutation"
        else:
            change_type = "evaluation"
        
        entry = EvolutionEntry(
            id="",
            timestamp="",
            parent_id=parent_id,
            component=component,
            change_type=change_type,
            description=f"Swarm cycle: {len(result.files_changed)} files changed",
            diff="",  # Could collect diffs from writer agent
            fitness=fitness,
            test_results={
                "passed": result.tests_passed,
                "tests_run": metrics.get("tests_run", 0),
            },
            agent_id="swarm_orchestrator",
            model=metrics.get("model", "swarm"),
            status="proposed",
        )
        
        return entry
    
    def _calculate_fitness(self, result: WorkflowResult) -> FitnessScore:
        """Calculate multi-dimensional fitness from workflow result.
        
        Args:
            result: WorkflowResult from swarm cycle
            
        Returns:
            FitnessScore with all dimensions populated
        """
        metrics = result.metrics or {}
        
        # Correctness: Did tests pass?
        correctness = 1.0 if result.tests_passed else 0.0
        
        # Adjust for test coverage if available
        tests_run = metrics.get("tests_run", 0)
        if tests_run > 0:
            # More tests = more confidence
            correctness *= min(1.0, tests_run / 10)  # Cap at 10 tests
        
        # Dharmic alignment: Based on evaluation score if available
        eval_score = metrics.get("evaluation_score", 0.5)
        dharmic = float(eval_score) if eval_score else 0.5
        
        # Elegance: Inversely related to issues remaining
        issues = metrics.get("issues_found", 0)
        proposals = metrics.get("proposals_generated", 0)
        if issues > 0 and proposals > 0:
            # More proposals approved = better quality
            approved = metrics.get("proposals_approved", 0)
            elegance = approved / proposals if proposals > 0 else 0.5
        else:
            elegance = 0.7  # Default for no-change cycles
        
        # Efficiency: Files changed should be minimal
        files_modified = metrics.get("files_modified", 0)
        if files_modified == 0:
            efficiency = 1.0  # No changes needed = efficient
        elif files_modified <= 3:
            efficiency = 0.9
        elif files_modified <= 10:
            efficiency = 0.7
        else:
            efficiency = 0.5
        
        # Safety: Tests passing + no rollback = safe
        safety = 1.0 if result.tests_passed else 0.3
        if result.state == WorkflowState.FAILED:
            safety *= 0.5
        
        return FitnessScore(
            correctness=correctness,
            dharmic_alignment=dharmic,
            elegance=elegance,
            efficiency=efficiency,
            safety=safety,
        )
    
    def evaluate_fitness(
        self,
        entry: EvolutionEntry,
        run_tests: bool = True,
    ) -> EvolutionEntry:
        """Evaluate and update fitness for an entry.
        
        Uses DGM's evaluator for consistent scoring across
        both swarm and direct DGM operations.
        
        Args:
            entry: Entry to evaluate
            run_tests: Whether to run test suite
            
        Returns:
            Entry with updated fitness and gate status
        """
        # Use DGM's evaluator for consistency
        eval_result = self.dgm.evaluator.evaluate(
            entry.component,
            run_tests=run_tests,
        )
        
        # Update entry with evaluation results
        entry.fitness = eval_result.score
        entry.gates_passed = eval_result.gates_passed
        entry.gates_failed = eval_result.gates_failed
        entry.test_results = {
            "passed": eval_result.tests_passed,
            "failed": eval_result.tests_failed,
        }
        
        return entry
    
    def check_dharmic_gates(self, entry: EvolutionEntry) -> bool:
        """Check if entry passes required dharmic gates.
        
        Args:
            entry: Entry to check
            
        Returns:
            True if all required gates pass
        """
        required_gates = self.dgm.REQUIRED_GATES
        
        for gate in required_gates:
            if gate not in entry.gates_passed:
                logger.warning(f"Required gate '{gate}' not passed for {entry.id}")
                return False
        
        return True
    
    def archive_entry(
        self,
        entry: EvolutionEntry,
        status: str = None,
    ) -> str:
        """Archive an evolution entry.
        
        Args:
            entry: Entry to archive
            status: Override status (proposed, approved, applied, etc.)
            
        Returns:
            Entry ID
        """
        if status:
            entry.status = status
        
        entry_id = self.archive.add_entry(entry)
        self.entries_archived += 1
        
        logger.info(f"Archived entry {entry_id} (status={entry.status})")
        return entry_id
    
    def archive_successful_pattern(
        self,
        result: WorkflowResult,
        component: str,
        parent_id: Optional[str] = None,
    ) -> Optional[str]:
        """Archive a successful swarm pattern for future reference.
        
        Only archives if:
        - Workflow completed successfully
        - Tests passed
        - Fitness meets threshold
        
        Args:
            result: Successful WorkflowResult
            component: Component identifier
            parent_id: Parent entry for lineage
            
        Returns:
            Entry ID if archived, None otherwise
        """
        # Only archive successes
        if result.state != WorkflowState.COMPLETED:
            logger.debug(f"Not archiving: workflow state = {result.state}")
            return None
        
        if not result.tests_passed:
            logger.debug("Not archiving: tests did not pass")
            return None
        
        # Convert to entry
        entry = self.workflow_result_to_entry(result, component, parent_id)
        
        # Check fitness threshold
        FITNESS_THRESHOLD = 0.6
        total_fitness = entry.fitness.total(self.FITNESS_WEIGHTS)
        
        if total_fitness < FITNESS_THRESHOLD:
            logger.debug(f"Not archiving: fitness {total_fitness:.2f} < {FITNESS_THRESHOLD}")
            return None
        
        # Archive as successful pattern
        entry.status = "applied"
        self.successful_evolutions += 1
        
        return self.archive_entry(entry)
    
    def get_best_parent(self, component: str) -> Optional[EvolutionEntry]:
        """Get the best parent entry for a component.
        
        Used to establish lineage in evolution cycles.
        
        Args:
            component: Component to find parent for
            
        Returns:
            Best entry for component, or None
        """
        best_entries = self.archive.get_best(n=1, component=component)
        return best_entries[0] if best_entries else None
    
    async def run_evolution_cycle(
        self,
        orchestrator: SwarmOrchestrator,
        target_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a complete evolution cycle through the swarm.
        
        This is the main integration point - orchestrates:
        1. Select parent from archive
        2. Run swarm improvement cycle
        3. Evaluate fitness with dharmic gates
        4. Archive if successful
        
        Args:
            orchestrator: SwarmOrchestrator instance
            target_area: Optional area to focus on
            
        Returns:
            Dict with cycle results
        """
        component = target_area or "swarm_evolution"
        
        logger.info(f"=== Evolution Cycle: {component} ===")
        
        result = {
            "component": component,
            "success": False,
            "entry_id": None,
            "fitness": 0.0,
            "gates_passed": [],
            "reason": None,
        }
        
        # 1. Find best parent for lineage
        parent = self.get_best_parent(component)
        parent_id = parent.id if parent else None
        parent_fitness = parent.fitness.total() if parent else 0.0
        
        logger.info(f"Parent: {parent_id or 'None'} (fitness={parent_fitness:.2f})")
        
        # 2. Run swarm improvement cycle
        try:
            workflow_result = await orchestrator.execute_improvement_cycle(target_area)
        except Exception as e:
            logger.error(f"Swarm cycle failed: {e}")
            result["reason"] = str(e)
            return result
        
        # 3. Convert to evolution entry
        entry = self.workflow_result_to_entry(
            workflow_result,
            component=component,
            parent_id=parent_id,
        )
        
        # 4. Full fitness evaluation with gates
        entry = self.evaluate_fitness(entry, run_tests=True)
        current_fitness = entry.fitness.total(self.FITNESS_WEIGHTS)
        
        result["fitness"] = current_fitness
        result["gates_passed"] = entry.gates_passed
        
        logger.info(f"Fitness: {current_fitness:.2f}")
        logger.info(f"Gates passed: {entry.gates_passed}")
        logger.info(f"Gates failed: {entry.gates_failed}")
        
        # 5. Check dharmic gates
        if not self.check_dharmic_gates(entry):
            result["reason"] = f"Required gates not passed: {entry.gates_failed}"
            entry.status = "rejected"
            self.archive_entry(entry)
            result["entry_id"] = entry.id
            return result
        
        # 6. Check improvement over parent
        if parent and current_fitness <= parent_fitness:
            result["reason"] = f"No improvement ({current_fitness:.2f} <= {parent_fitness:.2f})"
            entry.status = "no_improvement"
            self.archive_entry(entry)
            result["entry_id"] = entry.id
            return result
        
        # 7. Archive successful evolution
        if workflow_result.state == WorkflowState.COMPLETED:
            if self.dry_run:
                entry.status = "dry_run"
            else:
                entry.status = "applied"
                self.successful_evolutions += 1
            
            entry_id = self.archive_entry(entry)
            result["entry_id"] = entry_id
            result["success"] = True
            
            logger.info(f"Evolution successful! Entry: {entry_id}")
        else:
            result["reason"] = f"Workflow state: {workflow_result.state}"
            entry.status = "failed"
            self.archive_entry(entry)
            result["entry_id"] = entry.id
        
        self.proposals_processed += 1
        return result
    
    async def run_evolution_loop(
        self,
        orchestrator: SwarmOrchestrator,
        max_generations: int = 10,
        components: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run multiple evolution cycles.
        
        Args:
            orchestrator: SwarmOrchestrator instance
            max_generations: Maximum cycles to run
            components: List of components to evolve (rotates through)
            
        Returns:
            Summary of all cycles
        """
        components = components or ["swarm_evolution"]
        results = []
        no_improvement_streak = 0
        
        for gen in range(max_generations):
            for component in components:
                cycle_result = await self.run_evolution_cycle(
                    orchestrator,
                    target_area=component,
                )
                results.append(cycle_result)
                
                if cycle_result["success"]:
                    no_improvement_streak = 0
                else:
                    no_improvement_streak += 1
                
                # Early stopping
                if no_improvement_streak >= len(components) * 3:
                    logger.info("No improvements for 3 full rounds - stopping")
                    break
            
            if no_improvement_streak >= len(components) * 3:
                break
            
            # Brief pause between generations
            await asyncio.sleep(0.5)
        
        return {
            "generations": gen + 1,
            "total_cycles": len(results),
            "successful": sum(1 for r in results if r["success"]),
            "archived": self.entries_archived,
            "results": results,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bridge status."""
        return {
            "proposals_processed": self.proposals_processed,
            "entries_archived": self.entries_archived,
            "successful_evolutions": self.successful_evolutions,
            "archive_size": len(self.archive.entries),
            "dry_run": self.dry_run,
            "dgm_status": self.dgm.get_status(),
        }


# Convenience function for quick integration
async def evolve_with_swarm(
    target_area: Optional[str] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Run a single evolution cycle with swarm.
    
    Convenience function for simple integration.
    
    Args:
        target_area: Optional focus area
        dry_run: If True, don't apply changes
        
    Returns:
        Evolution cycle result
    """
    bridge = SwarmDGMBridge(dry_run=dry_run)
    orchestrator = SwarmOrchestrator()
    
    return await bridge.run_evolution_cycle(orchestrator, target_area)


if __name__ == "__main__":
    # Test the bridge
    import sys
    
    async def main():
        logging.basicConfig(level=logging.INFO)
        
        bridge = SwarmDGMBridge(dry_run=True)
        print(f"Bridge status: {bridge.get_status()}")
        
        # Test proposal conversion
        proposal = SwarmProposal(
            component="test_module.py",
            description="Test improvement",
            change_type="mutation",
            agent_id="test_agent",
        )
        
        entry = bridge.proposal_to_entry(proposal)
        print(f"Converted proposal to entry: {entry.component}")
        
        print("\nTo run full evolution cycle:")
        print("  result = await evolve_with_swarm(dry_run=True)")
    
    asyncio.run(main())
