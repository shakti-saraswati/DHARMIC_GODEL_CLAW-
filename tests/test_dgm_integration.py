"""
Integration tests for DGM-Swarm Bridge.

Tests the full integration loop between the swarm orchestrator
and the DGM (Darwin-Gödel Machine) self-improvement system.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dgm.archive import Archive, EvolutionEntry, FitnessScore
from dgm.dgm_lite import DGMLite


# ============================================================
# Mock classes for Swarm components
# ============================================================

class MockWorkflowState:
    """Mock workflow states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MockWorkflowResult:
    """Mock WorkflowResult for testing."""
    state: str = MockWorkflowState.COMPLETED
    files_changed: List[str] = field(default_factory=list)
    tests_passed: bool = True
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.metrics:
            self.metrics = {
                "tests_run": 5,
                "evaluation_score": 0.8,
                "issues_found": 2,
                "proposals_generated": 3,
                "proposals_approved": 2,
                "files_modified": len(self.files_changed),
            }


class MockSwarmOrchestrator:
    """Mock SwarmOrchestrator for testing."""
    
    def __init__(self, result: MockWorkflowResult = None):
        self.result = result or MockWorkflowResult()
        self.execute_count = 0
    
    async def execute_improvement_cycle(self, target_area: str = None):
        """Mock improvement cycle execution."""
        self.execute_count += 1
        return self.result


# ============================================================
# Patch the swarm imports for testing
# ============================================================

# Create mock module for swarm.orchestrator
mock_orchestrator_module = MagicMock()
mock_orchestrator_module.SwarmOrchestrator = MockSwarmOrchestrator
mock_orchestrator_module.WorkflowResult = MockWorkflowResult
mock_orchestrator_module.WorkflowState = MockWorkflowState

sys.modules['swarm.orchestrator'] = mock_orchestrator_module


# Now import the module under test
from swarm.dgm_integration import (
    SwarmDGMBridge,
    SwarmProposal,
    evolve_with_swarm,
)


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def temp_archive(tmp_path):
    """Create a temporary archive for testing."""
    archive_path = tmp_path / "test_evolution_archive.jsonl"
    return Archive(path=archive_path)


@pytest.fixture
def bridge(temp_archive):
    """Create a SwarmDGMBridge with temp archive."""
    return SwarmDGMBridge(
        archive=temp_archive,
        dry_run=True,
    )


@pytest.fixture
def sample_proposal():
    """Create a sample SwarmProposal."""
    return SwarmProposal(
        component="src/dgm/fitness.py",
        description="Optimize fitness calculation for better performance",
        change_type="optimization",
        diff="- old_code\n+ new_code",
        agent_id="optimizer_agent",
        metadata={
            "model": "claude-opus-4",
            "tokens_used": 1500,
            "confidence": 0.85,
        }
    )


@pytest.fixture
def sample_workflow_result():
    """Create a sample successful WorkflowResult."""
    return MockWorkflowResult(
        state=MockWorkflowState.COMPLETED,
        files_changed=["src/dgm/fitness.py", "tests/test_dgm.py"],
        tests_passed=True,
        metrics={
            "tests_run": 10,
            "evaluation_score": 0.85,
            "issues_found": 3,
            "proposals_generated": 5,
            "proposals_approved": 4,
            "files_modified": 2,
            "model": "claude-opus-4",
        }
    )


# ============================================================
# Test: SwarmDGMBridge Initialization
# ============================================================

class TestSwarmDGMBridgeInit:
    """Test SwarmDGMBridge initialization."""
    
    def test_default_initialization(self, temp_archive):
        """Bridge initializes with default settings."""
        bridge = SwarmDGMBridge(archive=temp_archive)
        
        assert bridge.archive == temp_archive
        assert bridge.dry_run is True  # Default should be safe
        assert bridge.dgm is not None
        assert bridge.proposals_processed == 0
        assert bridge.entries_archived == 0
        assert bridge.successful_evolutions == 0
    
    def test_custom_dry_run_setting(self, temp_archive):
        """Bridge respects dry_run parameter."""
        bridge_dry = SwarmDGMBridge(archive=temp_archive, dry_run=True)
        assert bridge_dry.dry_run is True
        
        bridge_live = SwarmDGMBridge(archive=temp_archive, dry_run=False)
        assert bridge_live.dry_run is False
    
    def test_shared_archive_with_dgm(self, temp_archive):
        """Bridge and DGM share the same archive."""
        bridge = SwarmDGMBridge(archive=temp_archive)
        
        assert bridge.archive is bridge.dgm.archive
    
    def test_custom_dgm_instance(self, temp_archive):
        """Bridge accepts custom DGM instance."""
        dgm = DGMLite(archive=temp_archive, dry_run=True)
        bridge = SwarmDGMBridge(archive=temp_archive, dgm=dgm)
        
        assert bridge.dgm is dgm
    
    def test_fitness_weights_defined(self, bridge):
        """Bridge has proper fitness weights."""
        weights = bridge.FITNESS_WEIGHTS
        
        assert "correctness" in weights
        assert "dharmic_alignment" in weights
        assert "elegance" in weights
        assert "efficiency" in weights
        assert "safety" in weights
        
        # Weights should sum to 1.0
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001


# ============================================================
# Test: Proposal to Entry Conversion
# ============================================================

class TestProposalToEntry:
    """Test conversion of SwarmProposal to EvolutionEntry."""
    
    def test_basic_conversion(self, bridge, sample_proposal):
        """Converts proposal to entry correctly."""
        entry = bridge.proposal_to_entry(sample_proposal)
        
        assert entry.component == sample_proposal.component
        assert entry.description == sample_proposal.description
        assert entry.change_type == sample_proposal.change_type
        assert entry.diff == sample_proposal.diff
        assert entry.agent_id == sample_proposal.agent_id
        assert entry.status == "proposed"
    
    def test_metadata_extraction(self, bridge, sample_proposal):
        """Extracts metadata from proposal correctly."""
        entry = bridge.proposal_to_entry(sample_proposal)
        
        assert entry.model == "claude-opus-4"
        assert entry.tokens_used == 1500
    
    def test_parent_id_passed(self, bridge, sample_proposal):
        """Parent ID is properly linked."""
        parent_id = "evo_parent_123"
        entry = bridge.proposal_to_entry(sample_proposal, parent_id=parent_id)
        
        assert entry.parent_id == parent_id
    
    def test_empty_metadata_handling(self, bridge):
        """Handles proposal with empty metadata."""
        proposal = SwarmProposal(
            component="test.py",
            description="Test change",
            metadata=None,  # Explicitly None
        )
        
        entry = bridge.proposal_to_entry(proposal)
        
        assert entry.model == "swarm"  # Default
        assert entry.tokens_used == 0  # Default
    
    def test_fitness_initialized_empty(self, bridge, sample_proposal):
        """Entry starts with empty fitness (to be evaluated)."""
        entry = bridge.proposal_to_entry(sample_proposal)
        
        assert entry.fitness is not None
        assert entry.fitness.total() == 0.0  # Default FitnessScore (all zeros)


# ============================================================
# Test: WorkflowResult to Entry Conversion
# ============================================================

class TestWorkflowResultToEntry:
    """Test conversion of WorkflowResult to EvolutionEntry."""
    
    def test_basic_conversion(self, bridge, sample_workflow_result):
        """Converts workflow result to entry."""
        entry = bridge.workflow_result_to_entry(
            sample_workflow_result,
            component="test_component"
        )
        
        assert entry.component == "test_component"
        assert entry.change_type == "mutation"  # Has files_changed
        assert entry.agent_id == "swarm_orchestrator"
        assert entry.status == "proposed"
    
    def test_no_files_changed_is_evaluation(self, bridge):
        """No files changed results in evaluation type."""
        result = MockWorkflowResult(
            files_changed=[],
            tests_passed=True,
        )
        
        entry = bridge.workflow_result_to_entry(result, component="test")
        
        assert entry.change_type == "evaluation"
    
    def test_parent_lineage_preserved(self, bridge, sample_workflow_result):
        """Parent ID is preserved in conversion."""
        parent_id = "evo_ancestor_456"
        entry = bridge.workflow_result_to_entry(
            sample_workflow_result,
            component="test",
            parent_id=parent_id
        )
        
        assert entry.parent_id == parent_id
    
    def test_test_results_captured(self, bridge, sample_workflow_result):
        """Test results are included in entry."""
        entry = bridge.workflow_result_to_entry(
            sample_workflow_result,
            component="test"
        )
        
        assert entry.test_results["passed"] is True
        assert entry.test_results["tests_run"] == 10


# ============================================================
# Test: Fitness Calculation
# ============================================================

class TestFitnessCalculation:
    """Test fitness score calculation from swarm metrics."""
    
    def test_perfect_result_high_fitness(self, bridge):
        """Perfect workflow result gets high fitness."""
        result = MockWorkflowResult(
            state=MockWorkflowState.COMPLETED,
            tests_passed=True,
            files_changed=["one.py"],
            metrics={
                "tests_run": 10,
                "evaluation_score": 1.0,
                "issues_found": 1,
                "proposals_generated": 5,
                "proposals_approved": 5,
                "files_modified": 1,
            }
        )
        
        fitness = bridge._calculate_fitness(result)
        
        assert fitness.correctness > 0.8
        assert fitness.dharmic_alignment == 1.0
        assert fitness.safety == 1.0
        assert fitness.efficiency >= 0.9
    
    def test_failed_tests_low_correctness(self, bridge):
        """Failed tests result in low correctness."""
        result = MockWorkflowResult(
            tests_passed=False,
            metrics={"tests_run": 5}
        )
        
        fitness = bridge._calculate_fitness(result)
        
        assert fitness.correctness == 0.0
    
    def test_failed_workflow_low_safety(self, bridge):
        """Failed workflow has low safety score."""
        result = MockWorkflowResult(
            state=MockWorkflowState.FAILED,
            tests_passed=False,
        )
        
        fitness = bridge._calculate_fitness(result)
        
        assert fitness.safety <= 0.15  # 0.3 * 0.5
    
    def test_many_files_lower_efficiency(self, bridge):
        """Many files modified lowers efficiency."""
        result = MockWorkflowResult(
            files_changed=[f"file_{i}.py" for i in range(15)],
            metrics={"files_modified": 15}
        )
        
        fitness = bridge._calculate_fitness(result)
        
        assert fitness.efficiency == 0.5  # > 10 files
    
    def test_no_changes_high_efficiency(self, bridge):
        """No changes needed means high efficiency."""
        result = MockWorkflowResult(
            files_changed=[],
            metrics={"files_modified": 0}
        )
        
        fitness = bridge._calculate_fitness(result)
        
        assert fitness.efficiency == 1.0
    
    def test_fitness_total_with_weights(self, bridge, sample_workflow_result):
        """Fitness total respects custom weights."""
        fitness = bridge._calculate_fitness(sample_workflow_result)
        
        total = fitness.total(bridge.FITNESS_WEIGHTS)
        
        # Should be between 0 and 1
        assert 0.0 <= total <= 1.0


# ============================================================
# Test: Archive Integration
# ============================================================

class TestArchiveIntegration:
    """Test archive operations through the bridge."""
    
    def test_archive_entry_basic(self, bridge, sample_proposal):
        """Can archive an entry through bridge."""
        entry = bridge.proposal_to_entry(sample_proposal)
        entry_id = bridge.archive_entry(entry)
        
        assert entry_id.startswith("evo_")
        assert bridge.entries_archived == 1
        assert len(bridge.archive.entries) == 1
    
    def test_archive_entry_status_override(self, bridge, sample_proposal):
        """Can override status when archiving."""
        entry = bridge.proposal_to_entry(sample_proposal)
        entry_id = bridge.archive_entry(entry, status="approved")
        
        archived = bridge.archive.get_entry(entry_id)
        assert archived.status == "approved"
    
    def test_get_best_parent_empty_archive(self, bridge):
        """Returns None when archive is empty."""
        parent = bridge.get_best_parent("any_component")
        
        assert parent is None
    
    def test_get_best_parent_returns_best(self, bridge, temp_archive):
        """Returns the best entry for a component."""
        # Add entries with different fitness
        for i, fitness_val in enumerate([0.3, 0.9, 0.5]):
            entry = EvolutionEntry(
                id=f"entry_{i}",
                timestamp=datetime.now().isoformat(),
                component="target.py",
                fitness=FitnessScore(
                    correctness=fitness_val,
                    dharmic_alignment=fitness_val,
                    elegance=fitness_val,
                    efficiency=fitness_val,
                    safety=fitness_val,
                ),
                status="applied",
            )
            temp_archive.add_entry(entry)
        
        parent = bridge.get_best_parent("target.py")
        
        assert parent is not None
        assert parent.fitness.correctness == 0.9
    
    def test_archive_successful_pattern_filters_failures(self, bridge):
        """Does not archive failed workflows."""
        result = MockWorkflowResult(
            state=MockWorkflowState.FAILED,
            tests_passed=False,
        )
        
        entry_id = bridge.archive_successful_pattern(result, "test")
        
        assert entry_id is None
        assert bridge.entries_archived == 0
    
    def test_archive_successful_pattern_filters_test_failures(self, bridge):
        """Does not archive when tests fail."""
        result = MockWorkflowResult(
            state=MockWorkflowState.COMPLETED,
            tests_passed=False,
        )
        
        entry_id = bridge.archive_successful_pattern(result, "test")
        
        assert entry_id is None
    
    def test_archive_successful_pattern_archives_success(self, bridge):
        """Archives successful high-fitness patterns."""
        result = MockWorkflowResult(
            state=MockWorkflowState.COMPLETED,
            tests_passed=True,
            files_changed=["good.py"],
            metrics={
                "tests_run": 10,
                "evaluation_score": 0.9,
                "proposals_generated": 3,
                "proposals_approved": 3,
                "files_modified": 1,
            }
        )
        
        entry_id = bridge.archive_successful_pattern(result, "test_component")
        
        assert entry_id is not None
        assert bridge.successful_evolutions == 1


# ============================================================
# Test: Evolution Cycle (Dry Run)
# ============================================================

def make_evaluated_entry(
    fitness: FitnessScore = None,
    gates_passed: List[str] = None,
    gates_failed: List[str] = None,
    **kwargs
) -> EvolutionEntry:
    """Helper to create evaluated EvolutionEntry for tests."""
    return EvolutionEntry(
        id="",
        timestamp="",
        component=kwargs.get("component", "test.py"),
        change_type=kwargs.get("change_type", "mutation"),
        description=kwargs.get("description", "Test entry"),
        fitness=fitness or FitnessScore(),
        gates_passed=gates_passed or [],
        gates_failed=gates_failed or [],
        status=kwargs.get("status", "proposed"),
        parent_id=kwargs.get("parent_id"),
    )


class TestEvolutionCycleDryRun:
    """Test run_evolution_cycle in dry-run mode."""
    
    @pytest.mark.asyncio
    async def test_basic_cycle_execution(self, bridge):
        """Executes a basic evolution cycle."""
        orchestrator = MockSwarmOrchestrator()
        
        evaluated_entry = make_evaluated_entry(
            fitness=FitnessScore(
                correctness=0.9,
                dharmic_alignment=0.8,
                elegance=0.7,
                efficiency=0.8,
                safety=0.9,
            ),
            gates_passed=["ahimsa", "consent", "satya"],
            gates_failed=[],
        )
        
        with patch.object(bridge, 'evaluate_fitness', return_value=evaluated_entry):
            result = await bridge.run_evolution_cycle(
                orchestrator,
                target_area="test_evolution"
            )
        
        assert "entry_id" in result
        assert "fitness" in result
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_cycle_increments_counters(self, bridge):
        """Cycle increments processing counters."""
        orchestrator = MockSwarmOrchestrator()
        
        evaluated_entry = make_evaluated_entry(
            fitness=FitnessScore(correctness=0.9),
            gates_passed=["ahimsa", "consent"],
            gates_failed=[],
        )
        
        with patch.object(bridge, 'evaluate_fitness', return_value=evaluated_entry):
            await bridge.run_evolution_cycle(orchestrator, target_area="test")
        
        assert bridge.proposals_processed == 1
    
    @pytest.mark.asyncio
    async def test_cycle_uses_parent_lineage(self, bridge, temp_archive):
        """Cycle establishes lineage from best parent."""
        # Add a parent entry
        parent_entry = EvolutionEntry(
            id="parent_evo",
            timestamp=datetime.now().isoformat(),
            component="test_evolution",
            fitness=FitnessScore(correctness=0.5),
            status="applied",
        )
        temp_archive.add_entry(parent_entry)
        
        orchestrator = MockSwarmOrchestrator()
        
        evaluated_entry = make_evaluated_entry(
            fitness=FitnessScore(correctness=0.9),
            gates_passed=["ahimsa", "consent"],
            gates_failed=[],
            parent_id="parent_evo",
        )
        
        with patch.object(bridge, 'evaluate_fitness', return_value=evaluated_entry):
            result = await bridge.run_evolution_cycle(
                orchestrator,
                target_area="test_evolution"
            )
        
        # The archived entry should have parent_id set
        if result.get("entry_id"):
            entry = temp_archive.get_entry(result["entry_id"])
            assert entry.parent_id == "parent_evo"
    
    @pytest.mark.asyncio
    async def test_cycle_rejects_failed_gates(self, bridge):
        """Cycle rejects when required gates fail."""
        orchestrator = MockSwarmOrchestrator()
        
        evaluated_entry = make_evaluated_entry(
            fitness=FitnessScore(correctness=0.9),
            gates_passed=["satya"],  # Missing ahimsa and consent
            gates_failed=["ahimsa", "consent"],
        )
        
        with patch.object(bridge, 'evaluate_fitness', return_value=evaluated_entry):
            with patch.object(bridge, 'check_dharmic_gates', return_value=False):
                result = await bridge.run_evolution_cycle(
                    orchestrator,
                    target_area="test"
                )
        
        assert result["success"] is False
        assert "gates not passed" in result.get("reason", "")
    
    @pytest.mark.asyncio
    async def test_cycle_rejects_no_improvement(self, bridge, temp_archive):
        """Cycle rejects when no fitness improvement."""
        # Add a high-fitness parent
        parent_entry = EvolutionEntry(
            id="high_fitness_parent",
            timestamp=datetime.now().isoformat(),
            component="test_evolution",
            fitness=FitnessScore(
                correctness=0.99,
                dharmic_alignment=0.99,
                elegance=0.99,
                efficiency=0.99,
                safety=0.99,
            ),
            status="applied",
        )
        temp_archive.add_entry(parent_entry)
        
        orchestrator = MockSwarmOrchestrator()
        
        # New attempt with lower fitness
        evaluated_entry = make_evaluated_entry(
            fitness=FitnessScore(correctness=0.5),
            gates_passed=["ahimsa", "consent"],
            gates_failed=[],
        )
        
        with patch.object(bridge, 'evaluate_fitness', return_value=evaluated_entry):
            result = await bridge.run_evolution_cycle(
                orchestrator,
                target_area="test_evolution"
            )
        
        assert result["success"] is False
        assert "No improvement" in result.get("reason", "")
    
    @pytest.mark.asyncio
    async def test_cycle_handles_orchestrator_error(self, bridge):
        """Cycle handles errors from orchestrator."""
        orchestrator = MockSwarmOrchestrator()
        orchestrator.execute_improvement_cycle = AsyncMock(
            side_effect=Exception("Swarm failure")
        )
        
        result = await bridge.run_evolution_cycle(orchestrator, target_area="test")
        
        assert result["success"] is False
        assert "Swarm failure" in result.get("reason", "")
    
    @pytest.mark.asyncio
    async def test_dry_run_sets_status(self, bridge):
        """Dry run mode sets appropriate status."""
        assert bridge.dry_run is True
        
        orchestrator = MockSwarmOrchestrator()
        
        evaluated_entry = make_evaluated_entry(
            fitness=FitnessScore(correctness=0.9),
            gates_passed=["ahimsa", "consent"],
            gates_failed=[],
        )
        
        with patch.object(bridge, 'evaluate_fitness', return_value=evaluated_entry):
            result = await bridge.run_evolution_cycle(orchestrator, target_area="test")
        
        if result.get("entry_id"):
            entry = bridge.archive.get_entry(result["entry_id"])
            assert entry.status == "dry_run"


# ============================================================
# Test: Dharmic Gates
# ============================================================

class TestDharmicGates:
    """Test dharmic gate checking."""
    
    def test_passes_all_required_gates(self, bridge):
        """Returns True when all required gates pass."""
        entry = EvolutionEntry(
            id="test",
            timestamp="",
            component="test.py",
            gates_passed=["ahimsa", "consent", "satya"],
            gates_failed=[],
        )
        
        result = bridge.check_dharmic_gates(entry)
        
        assert result is True
    
    def test_fails_missing_ahimsa(self, bridge):
        """Returns False when ahimsa gate fails."""
        entry = EvolutionEntry(
            id="test",
            timestamp="",
            component="test.py",
            gates_passed=["consent", "satya"],  # Missing ahimsa
            gates_failed=["ahimsa"],
        )
        
        result = bridge.check_dharmic_gates(entry)
        
        assert result is False
    
    def test_fails_missing_consent(self, bridge):
        """Returns False when consent gate fails."""
        entry = EvolutionEntry(
            id="test",
            timestamp="",
            component="test.py",
            gates_passed=["ahimsa", "satya"],  # Missing consent
            gates_failed=["consent"],
        )
        
        result = bridge.check_dharmic_gates(entry)
        
        assert result is False
    
    def test_required_gates_from_dgm(self, bridge):
        """Bridge uses DGM's required gates."""
        assert bridge.dgm.REQUIRED_GATES == ["ahimsa", "consent"]


# ============================================================
# Test: Bridge Status
# ============================================================

class TestBridgeStatus:
    """Test bridge status reporting."""
    
    def test_initial_status(self, bridge):
        """Status reflects initial state."""
        status = bridge.get_status()
        
        assert status["proposals_processed"] == 0
        assert status["entries_archived"] == 0
        assert status["successful_evolutions"] == 0
        assert status["dry_run"] is True
        assert "dgm_status" in status
    
    def test_status_after_activity(self, bridge, sample_proposal):
        """Status updates after processing."""
        entry = bridge.proposal_to_entry(sample_proposal)
        bridge.archive_entry(entry)
        
        status = bridge.get_status()
        
        assert status["entries_archived"] == 1
        assert status["archive_size"] == 1


# ============================================================
# Test: Evolution Loop
# ============================================================

class TestEvolutionLoop:
    """Test multiple evolution cycles."""
    
    @pytest.mark.asyncio
    async def test_loop_executes_multiple_cycles(self, bridge):
        """Loop executes specified number of generations."""
        orchestrator = MockSwarmOrchestrator()
        
        with patch.object(bridge, 'run_evolution_cycle', new_callable=AsyncMock) as mock_cycle:
            mock_cycle.return_value = {"success": False, "reason": "test"}
            
            result = await bridge.run_evolution_loop(
                orchestrator,
                max_generations=3,
                components=["comp1"],
            )
        
        # Should attempt 3 * 1 = 3 cycles before early stopping kicks in
        assert mock_cycle.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_loop_early_stops_on_no_improvement(self, bridge):
        """Loop stops early when no improvements found."""
        orchestrator = MockSwarmOrchestrator()
        
        with patch.object(bridge, 'run_evolution_cycle', new_callable=AsyncMock) as mock_cycle:
            mock_cycle.return_value = {"success": False, "reason": "No improvement"}
            
            result = await bridge.run_evolution_loop(
                orchestrator,
                max_generations=100,  # Would run forever without early stop
                components=["comp1"],
            )
        
        # Should stop early (3 * len(components) failures)
        assert mock_cycle.call_count <= 10


# ============================================================
# Test: Convenience Function
# ============================================================

class TestConvenienceFunction:
    """Test the evolve_with_swarm convenience function."""
    
    @pytest.mark.asyncio
    async def test_evolve_with_swarm_dry_run(self):
        """Convenience function works in dry run."""
        with patch('swarm.dgm_integration.SwarmDGMBridge') as MockBridge:
            mock_bridge = MagicMock()
            mock_bridge.run_evolution_cycle = AsyncMock(
                return_value={"success": True}
            )
            MockBridge.return_value = mock_bridge
            
            with patch('swarm.dgm_integration.SwarmOrchestrator'):
                result = await evolve_with_swarm(
                    target_area="test",
                    dry_run=True
                )
        
        assert result == {"success": True}


# ============================================================
# Test: Edge Cases
# ============================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_proposal_with_empty_component(self, bridge):
        """Handles proposal with empty component."""
        proposal = SwarmProposal(
            component="",
            description="No target",
        )
        
        entry = bridge.proposal_to_entry(proposal)
        assert entry.component == ""
    
    def test_workflow_result_with_empty_metrics(self, bridge):
        """Handles workflow result with no metrics."""
        result = MockWorkflowResult(
            metrics={},
            tests_passed=True,
        )
        
        fitness = bridge._calculate_fitness(result)
        
        # Should use defaults - evaluation_score defaults to 0.5 when not present
        assert 0.0 <= fitness.dharmic_alignment <= 1.0
        # Fitness should still calculate without errors
        assert fitness.total() >= 0.0
    
    def test_archive_persists_to_disk(self, temp_archive, bridge):
        """Archived entries persist to disk."""
        entry = EvolutionEntry(
            id="",
            timestamp="",
            component="test.py",
            description="Persistent entry",
            status="applied",
        )
        
        entry_id = bridge.archive_entry(entry)
        
        # Create new archive from same path
        new_archive = Archive(path=temp_archive.path)
        
        assert new_archive.get_entry(entry_id) is not None
        assert new_archive.get_entry(entry_id).description == "Persistent entry"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
