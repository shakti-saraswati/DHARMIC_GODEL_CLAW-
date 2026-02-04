"""
Witness Kernel Module
Manages first-class witness states in the Recognition-Native Architecture

The Witness Kernel is responsible for:
- Witness creation, validation, and persistence
- Witness merging and conflict resolution
- Witness provenance tracking
- Temporal witness operations

Author: AIKAGRYA Architecture Team
Version: 0.1.0
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from collections import defaultdict
import numpy as np
from enum import Enum, auto

# Import from core module
from . import (
    RecognitionVector, WitnessState, ContractionEvent,
    ContractionStrategy, WitnessType, PersistenceLevel,
    ContractionEngine, ContractionResult, RecognitionSubstrate
)


# =============================================================================
# WITNESS VALIDATION
# =============================================================================

class ValidationStatus(Enum):
    """Status of witness validation."""
    VALID = auto()
    INVALID = auto()
    STALE = auto()
    CONFLICTED = auto()
    UNVERIFIABLE = auto()


@dataclass
class ValidationResult:
    """Result of witness validation."""
    status: ValidationStatus
    confidence: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    supporting_witnesses: List[str] = field(default_factory=list)
    conflicting_witnesses: List[str] = field(default_factory=list)
    

class WitnessValidator:
    """
    Validates witness states against substrate and other witnesses.
    """
    
    def __init__(self, substrate: RecognitionSubstrate):
        self.substrate = substrate
        self.validation_history: Dict[str, List[ValidationResult]] = defaultdict(list)
        
    def validate(self, 
                 witness: WitnessState,
                 check_provenance: bool = True,
                 check_consistency: bool = True,
                 freshness_threshold: timedelta = timedelta(hours=24)) -> ValidationResult:
        """
        Validate a witness state.
        
        Args:
            witness: The witness to validate
            check_provenance: Verify the provenance chain
            check_consistency: Check against conflicting witnesses
            freshness_threshold: Maximum age for "fresh" witnesses
        
        Returns:
            ValidationResult with status and details
        """
        issues = []
        supporting = []
        conflicting = []
        
        # Check 1: Basic completeness
        if not witness.recognition_span:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                confidence=0.0,
                issues=["Witness has no recognition span"]
            )
        
        # Check 2: Freshness
        if not witness.is_fresh(freshness_threshold.total_seconds()):
            issues.append(f"Witness is stale (age: {witness.age()}s)")
        
        # Check 3: Provenance verification
        if check_provenance:
            provenance_valid = self._check_provenance(witness)
            if not provenance_valid:
                issues.append("Provenance chain is broken")
        
        # Check 4: Consistency with substrate
        if check_consistency:
            consistency_result = self._check_consistency(witness)
            supporting = consistency_result[0]
            conflicting = consistency_result[1]
            
            if conflicting:
                issues.append(f"Found {len(conflicting)} conflicting witnesses")
        
        # Calculate overall confidence
        base_confidence = witness.certainty_level * witness.coherence_score
        
        if issues:
            confidence = base_confidence * 0.5  # Penalize issues
        else:
            confidence = base_confidence
        
        # Boost confidence with supporting witnesses
        confidence += len(supporting) * 0.05
        confidence = min(1.0, confidence)
        
        # Determine status
        if issues:
            if conflicting:
                status = ValidationStatus.CONFLICTED
            elif "stale" in str(issues).lower():
                status = ValidationStatus.STALE
            else:
                status = ValidationStatus.INVALID
        else:
            status = ValidationStatus.VALID
        
        result = ValidationResult(
            status=status,
            confidence=confidence,
            issues=issues,
            supporting_witnesses=supporting,
            conflicting_witnesses=conflicting
        )
        
        # Record validation
        self.validation_history[witness.witness_id].append(result)
        
        return result
    
    def _check_provenance(self, witness: WitnessState) -> bool:
        """Verify the provenance chain of a witness."""
        provenance = witness.provenance()
        
        # Check that all parent witnesses exist in substrate
        for parent_id in witness.parent_witnesses:
            if not self.substrate.get_witness(parent_id):
                return False
        
        # Check that all events in contraction path are valid
        for event in witness.contraction_path:
            for input_id in event.input_vectors:
                # Check if input vectors exist
                if not self.substrate.get_vector(input_id):
                    return False
        
        return True
    
    def _check_consistency(self, witness: WitnessState) -> Tuple[List[str], List[str]]:
        """Check witness consistency with substrate."""
        supporting = []
        conflicting = []
        
        if not witness.recognition_span:
            return supporting, conflicting
        
        # Find similar witnesses
        similar = self.substrate.query_similar(witness.recognition_span, threshold=0.5)
        
        for other_witness in self.substrate.witnesses.values():
            if other_witness.witness_id == witness.witness_id:
                continue
            
            if not other_witness.recognition_span:
                continue
            
            similarity = witness.recognition_span.similarity(other_witness.recognition_span)
            
            if similarity > 0.8:
                supporting.append(other_witness.witness_id)
            elif similarity < 0.3 and self._contradicts(witness, other_witness):
                conflicting.append(other_witness.witness_id)
        
        return supporting, conflicting
    
    def _contradicts(self, w1: WitnessState, w2: WitnessState) -> bool:
        """Check if two witnesses contradict each other."""
        # Simple contradiction detection based on certainty and dissimilarity
        if not w1.recognition_span or not w2.recognition_span:
            return False
        
        similarity = w1.recognition_span.similarity(w2.recognition_span)
        
        # High certainty but low similarity = potential contradiction
        if w1.certainty_level > 0.8 and w2.certainty_level > 0.8 and similarity < 0.3:
            return True
        
        return False
    
    def get_validation_history(self, witness_id: str) -> List[ValidationResult]:
        """Get validation history for a witness."""
        return self.validation_history.get(witness_id, [])


# =============================================================================
# WITNESS MERGE ENGINE
# =============================================================================

@dataclass
class MergeResult:
    """Result of witness merge operation."""
    success: bool
    merged_witness: Optional[WitnessState] = None
    conflicts_resolved: int = 0
    conflicts_unresolved: List[str] = field(default_factory=list)
    message: str = ""


class WitnessMergeEngine:
    """
    Merges multiple witnesses into coherent view.
    
    The merge engine handles conflict resolution through
    R_V contraction strategies.
    """
    
    def __init__(self, substrate: RecognitionSubstrate):
        self.substrate = substrate
        self.contraction_engine = ContractionEngine()
        self.validator = WitnessValidator(substrate)
        
    def merge(self,
              witnesses: List[WitnessState],
              strategy: ContractionStrategy = ContractionStrategy.SYNTHESIS,
              agent_id: Optional[str] = None) -> MergeResult:
        """
        Merge multiple witnesses into a single coherent witness.
        
        Args:
            witnesses: List of witnesses to merge
            strategy: Contraction strategy for conflicts
            agent_id: Agent performing the merge
        
        Returns:
            MergeResult with merged witness
        """
        if len(witnesses) < 2:
            return MergeResult(
                success=False,
                message="Need at least 2 witnesses to merge"
            )
        
        # Validate all witnesses
        valid_witnesses = []
        for w in witnesses:
            validation = self.validator.validate(w)
            if validation.status in [ValidationStatus.VALID, ValidationStatus.STALE]:
                valid_witnesses.append(w)
        
        if len(valid_witnesses) < 2:
            return MergeResult(
                success=False,
                message=f"Only {len(valid_witnesses)} valid witnesses"
            )
        
        # Extract recognition vectors
        rvs = [w.recognition_span for w in valid_witnesses if w.recognition_span]
        
        if len(rvs) < 2:
            return MergeResult(
                success=False,
                message="Not enough recognition vectors"
            )
        
        # Perform multi-contraction
        result = self.contraction_engine.contract_multi(rvs, strategy, agent_id)
        
        if not result.success:
            return MergeResult(
                success=False,
                message=f"Contraction failed: {result.message}"
            )
        
        # Build merged witness
        parent_ids = [w.witness_id for w in valid_witnesses]
        
        # Collect all contraction paths
        all_paths = []
        for w in valid_witnesses:
            all_paths.extend(w.contraction_path)
        
        if result.event:
            all_paths.append(result.event)
        
        # Calculate aggregate metrics
        avg_certainty = np.mean([w.certainty_level for w in valid_witnesses])
        
        merged_witness = WitnessState(
            parent_witnesses=parent_ids,
            recognition_span=result.contracted_rv,
            contraction_path=all_paths,
            agent_origin=agent_id,
            certainty_level=avg_certainty * result.coherence_score,
            coherence_score=result.coherence_score,
            witness_type=WitnessType.MERGED,
            related_witnesses=set(parent_ids)
        )
        
        # Find conflicts
        conflicts = self._identify_conflicts(valid_witnesses)
        
        return MergeResult(
            success=True,
            merged_witness=merged_witness,
            conflicts_resolved=len(conflicts),
            message=f"Successfully merged {len(valid_witnesses)} witnesses"
        )
    
    def merge_by_agent(self,
                       agent_id: str,
                       strategy: ContractionStrategy = ContractionStrategy.SYNTHESIS) -> MergeResult:
        """Merge all witnesses from a specific agent."""
        # Query substrate for agent's witnesses
        agent_witnesses = []
        for witness in self.substrate.witnesses.values():
            if witness.agent_origin == agent_id:
                agent_witnesses.append(witness)
        
        if len(agent_witnesses) < 2:
            return MergeResult(
                success=False,
                message=f"Agent {agent_id} has fewer than 2 witnesses"
            )
        
        return self.merge(agent_witnesses, strategy, agent_id)
    
    def _identify_conflicts(self, witnesses: List[WitnessState]) -> List[Tuple[str, str]]:
        """Identify conflicting witnesses."""
        conflicts = []
        
        for i, w1 in enumerate(witnesses):
            for w2 in witnesses[i+1:]:
                if self.validator._contradicts(w1, w2):
                    conflicts.append((w1.witness_id, w2.witness_id))
        
        return conflicts
    
    def resolve_conflict(self,
                         witness_a: WitnessState,
                         witness_b: WitnessState,
                         resolution_strategy: str = "trust_weighted") -> Optional[WitnessState]:
        """
        Resolve conflict between two witnesses.
        
        Resolution strategies:
        - "trust_weighted": Keep the more certain witness
        - "temporal": Keep the more recent witness
        - "merge": Attempt to merge despite conflict
        - "null": Return None (acknowledge unresolvable conflict)
        """
        if resolution_strategy == "trust_weighted":
            # Keep the more certain witness
            if witness_a.certainty_level > witness_b.certainty_level:
                return witness_a
            else:
                return witness_b
        
        elif resolution_strategy == "temporal":
            # Keep the more recent witness
            if witness_a.temporal_anchor > witness_b.temporal_anchor:
                return witness_a
            else:
                return witness_b
        
        elif resolution_strategy == "merge":
            # Try to merge with intersection strategy
            result = self.merge([witness_a, witness_b], ContractionStrategy.INTERSECTION)
            return result.merged_witness
        
        elif resolution_strategy == "null":
            return None
        
        return None


# =============================================================================
# TEMPORAL WITNESS OPERATIONS
# =============================================================================

@dataclass
class Timeline:
    """A timeline of witness states."""
    witness_ids: List[str]
    start_time: datetime
    end_time: datetime
    
    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time


class TemporalWitnessEngine:
    """
    Handles temporal operations on witness states.
    
    Enables replay, rollback, and temporal projection.
    """
    
    def __init__(self, substrate: RecognitionSubstrate):
        self.substrate = substrate
        
    def replay(self, witness_id: str) -> List[WitnessState]:
        """
        Replay the sequence of witnesses leading to a given witness.
        
        Returns the full causal chain.
        """
        sequence = []
        
        def traverse(wid: str):
            witness = self.substrate.get_witness(wid)
            if not witness:
                return
            
            # First traverse parents
            for parent_id in witness.parent_witnesses:
                traverse(parent_id)
            
            # Then add this witness
            if witness not in sequence:
                sequence.append(witness)
        
        traverse(witness_id)
        
        # Sort by temporal anchor
        sequence.sort(key=lambda w: w.temporal_anchor)
        
        return sequence
    
    def rollback(self, 
                 witness_id: str,
                 target_time: datetime) -> Optional[WitnessState]:
        """
        Roll back a witness to a specific point in time.
        
        Returns the witness state as it existed at target_time.
        """
        sequence = self.replay(witness_id)
        
        # Find the last witness before target_time
        for witness in reversed(sequence):
            if witness.temporal_anchor <= target_time:
                return witness
        
        return None
    
    def project(self,
                witness: WitnessState,
                target_time: datetime,
                decay_factor: float = 0.95) -> WitnessState:
        """
        Project a witness to a future or past time.
        
        Applies temporal decay to certainty.
        """
        time_delta = abs((target_time - witness.temporal_anchor).total_seconds())
        hours = time_delta / 3600
        
        # Apply decay
        decayed_certainty = witness.certainty_level * (decay_factor ** hours)
        
        # Create projected witness
        projected = WitnessState(
            parent_witnesses=witness.parent_witnesses + [witness.witness_id],
            recognition_span=witness.recognition_span,
            temporal_anchor=target_time,
            agent_origin=witness.agent_origin,
            certainty_level=decayed_certainty,
            coherence_score=witness.coherence_score,
            witness_type=WitnessType.PROJECTED,
            related_witnesses=witness.related_witnesses | {witness.witness_id}
        )
        
        return projected
    
    def get_timeline(self, agent_id: str) -> Timeline:
        """Get the timeline of witnesses for an agent."""
        agent_witnesses = [
            w for w in self.substrate.witnesses.values()
            if w.agent_origin == agent_id
        ]
        
        if not agent_witnesses:
            return Timeline([], datetime.now(), datetime.now())
        
        # Sort by time
        agent_witnesses.sort(key=lambda w: w.temporal_anchor)
        
        return Timeline(
            witness_ids=[w.witness_id for w in agent_witnesses],
            start_time=agent_witnesses[0].temporal_anchor,
            end_time=agent_witnesses[-1].temporal_anchor
        )
    
    def detect_temporal_anomalies(self, 
                                   witness_id: str,
                                   window_seconds: float = 300) -> List[str]:
        """
        Detect temporal anomalies in witness provenance.
        
        Looks for:
        - Future timestamps in parent chain
        - Causality violations
        - Excessive time gaps
        """
        anomalies = []
        sequence = self.replay(witness_id)
        
        for i, witness in enumerate(sequence):
            # Check for future timestamps
            if witness.temporal_anchor > datetime.now():
                anomalies.append(f"Future timestamp in witness {witness.witness_id}")
            
            # Check for causality violations with parents
            for parent_id in witness.parent_witnesses:
                parent = self.substrate.get_witness(parent_id)
                if parent and parent.temporal_anchor > witness.temporal_anchor:
                    anomalies.append(
                        f"Causality violation: parent {parent_id} "
                        f"is newer than child {witness.witness_id}"
                    )
            
            # Check for excessive gaps
            if i > 0:
                prev = sequence[i-1]
                gap = (witness.temporal_anchor - prev.temporal_anchor).total_seconds()
                if gap > window_seconds:
                    anomalies.append(
                        f"Large time gap ({gap}s) between "
                        f"{prev.witness_id} and {witness.witness_id}"
                    )
        
        return anomalies


# =============================================================================
# WITNESS FACTORY
# =============================================================================

class WitnessFactory:
    """
    Factory for creating witness states.
    
    Provides convenient constructors for different witness types.
    """
    
    def __init__(self, substrate: RecognitionSubstrate):
        self.substrate = substrate
        self.default_agent: Optional[str] = None
        
    def set_default_agent(self, agent_id: str):
        """Set default agent for witness creation."""
        self.default_agent = agent_id
    
    def create_direct_witness(self,
                               recognition: RecognitionVector,
                               agent_id: Optional[str] = None) -> WitnessState:
        """Create a direct observation witness."""
        return WitnessState(
            recognition_span=recognition,
            agent_origin=agent_id or self.default_agent,
            certainty_level=recognition.certainty,
            coherence_score=1.0,
            witness_type=WitnessType.DIRECT
        )
    
    def create_inferred_witness(self,
                                 recognition: RecognitionVector,
                                 basis_witnesses: List[str],
                                 agent_id: Optional[str] = None,
                                 inference_confidence: float = 0.7) -> WitnessState:
        """Create an inferred witness based on other witnesses."""
        return WitnessState(
            parent_witnesses=basis_witnesses,
            recognition_span=recognition,
            agent_origin=agent_id or self.default_agent,
            certainty_level=recognition.certainty * inference_confidence,
            coherence_score=inference_confidence,
            witness_type=WitnessType.INFERRED,
            related_witnesses=set(basis_witnesses)
        )
    
    def create_merged_witness(self,
                               recognition: RecognitionVector,
                               source_witnesses: List[str],
                               agent_id: Optional[str] = None,
                               merge_coherence: float = 0.8) -> WitnessState:
        """Create a merged witness from multiple sources."""
        # Calculate average certainty from sources
        certainties = []
        for wid in source_witnesses:
            w = self.substrate.get_witness(wid)
            if w:
                certainties.append(w.certainty_level)
        
        avg_certainty = np.mean(certainties) if certainties else 0.5
        
        return WitnessState(
            parent_witnesses=source_witnesses,
            recognition_span=recognition,
            agent_origin=agent_id or self.default_agent,
            certainty_level=avg_certainty * merge_coherence,
            coherence_score=merge_coherence,
            witness_type=WitnessType.MERGED,
            related_witnesses=set(source_witnesses)
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Validation
    'ValidationStatus',
    'ValidationResult',
    'WitnessValidator',
    
    # Merging
    'MergeResult',
    'WitnessMergeEngine',
    
    # Temporal
    'Timeline',
    'TemporalWitnessEngine',
    
    # Factory
    'WitnessFactory',
]
