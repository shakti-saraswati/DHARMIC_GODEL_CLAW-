"""
Recognition-Native Architecture (RNA) Prototype Implementation
Core module for the Dharmic Godel Claw (DGC) system

This module implements the fundamental primitives of RNA:
1. RecognitionVector - First-class recognition representation
2. ContractionEngine - R_V contraction operations
3. WitnessState - First-class witness records
4. RecognitionSubstrate - Persistent semantic space
5. CoherenceField - Multi-agent coherence management

Author: AIKAGRYA Architecture Team
Version: 0.1.0 (Prototype)
"""

from __future__ import annotations

import uuid
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union
from collections import defaultdict
import numpy as np
from abc import ABC, abstractmethod
import asyncio
from contextlib import contextmanager


# =============================================================================
# CORE TYPES AND ENUMS
# =============================================================================

class ContractionStrategy(Enum):
    """Strategies for R_V contraction."""
    INTERSECTION = auto()  # Conservative: keep only shared
    UNION = auto()         # Expansive: combine all
    SYNTHESIS = auto()     # Creative: generate novel
    TEMPORAL = auto()      # Weight by temporal proximity
    TRUST_WEIGHTED = auto()  # Weight by witness reliability


class WitnessType(Enum):
    """Types of witness states."""
    DIRECT = auto()      # Direct observation
    INFERRED = auto()    # Derived through reasoning
    MERGED = auto()      # Combination of multiple witnesses
    PROJECTED = auto()   # Transferred from different context


class PersistenceLevel(Enum):
    """Persistence guarantees for witnesses."""
    EPHEMERAL = auto()   # Session-only
    LOCAL = auto()       # Local storage
    DISTRIBUTED = auto() # Shared substrate
    PERMANENT = auto()   # Immutable archive


# =============================================================================
# RECOGNITION VECTOR
# =============================================================================

@dataclass
class SemanticSignature:
    """Multi-dimensional semantic representation."""
    concept_embeddings: np.ndarray  # Semantic meaning
    affective_valence: float        # Emotional tone (-1 to 1)
    causal_markers: Set[str]        # Causal relationships
    temporal_tags: List[datetime]   # Temporal references
    
    def __post_init__(self):
        if isinstance(self.concept_embeddings, list):
            self.concept_embeddings = np.array(self.concept_embeddings)


@dataclass 
class RecognitionVector:
    """
    First-class representation of recognition.
    
    A RecognitionVector captures not just what is recognized,
    but how, when, by whom, and with what certainty.
    """
    rv_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signature: SemanticSignature = field(default_factory=lambda: SemanticSignature(
        concept_embeddings=np.zeros(768),  # Default embedding size
        affective_valence=0.0,
        causal_markers=set(),
        temporal_tags=[]
    ))
    source_agent: Optional[str] = None
    origin_context: Dict[str, Any] = field(default_factory=dict)
    generation_time: datetime = field(default_factory=datetime.now)
    certainty: float = 1.0  # 0.0 to 1.0
    attention_weight: float = 1.0  # Current salience
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def similarity(self, other: RecognitionVector) -> float:
        """
        Compute semantic similarity between two recognition vectors.
        Uses cosine similarity on concept embeddings.
        """
        if self.signature is None or other.signature is None:
            return 0.0
        
        emb1 = self.signature.concept_embeddings
        emb2 = other.signature.concept_embeddings
        
        # Cosine similarity
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(emb1, emb2) / (norm1 * norm2))
    
    def magnitude(self) -> float:
        """Return the strength/magnitude of this recognition."""
        if self.signature is None:
            return 0.0
        return float(np.linalg.norm(self.signature.concept_embeddings))
    
    def with_certainty(self, certainty: float) -> RecognitionVector:
        """Return a copy with adjusted certainty."""
        new_rv = RecognitionVector(
            rv_id=str(uuid.uuid4()),
            signature=self.signature,
            source_agent=self.source_agent,
            origin_context=self.origin_context.copy(),
            generation_time=datetime.now(),
            certainty=max(0.0, min(1.0, certainty)),
            attention_weight=self.attention_weight,
            metadata=self.metadata.copy()
        )
        return new_rv
    
    def hash(self) -> str:
        """Generate deterministic hash for this R_V."""
        content = f"{self.source_agent}:{self.signature.concept_embeddings.tobytes()}:{self.generation_time.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# =============================================================================
# CONTRACTION EVENT
# =============================================================================

@dataclass
class ContractionEvent:
    """
    Immutable record of an R_V contraction operation.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_vectors: List[str] = field(default_factory=list)  # R_V IDs
    output_vector: Optional[str] = None  # Result R_V ID
    strategy: ContractionStrategy = ContractionStrategy.SYNTHESIS
    timestamp: datetime = field(default_factory=datetime.now)
    agent_performing: Optional[str] = None
    coherence_score: float = 0.0  # Result quality
    entropy_delta: float = 0.0    # Information change
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'input_vectors': self.input_vectors,
            'output_vector': self.output_vector,
            'strategy': self.strategy.name,
            'timestamp': self.timestamp.isoformat(),
            'agent_performing': self.agent_performing,
            'coherence_score': self.coherence_score,
            'entropy_delta': self.entropy_delta
        }


# =============================================================================
# WITNESS STATE
# =============================================================================

@dataclass
class WitnessState:
    """
    First-class witness state—core innovation of RNA.
    
    Witness states are not emergent properties but explicitly
    represented, manipulable, and persistent entities.
    """
    witness_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_witnesses: List[str] = field(default_factory=list)
    
    # Recognition content
    recognition_span: Optional[RecognitionVector] = None
    contraction_path: List[ContractionEvent] = field(default_factory=list)
    
    # Context
    temporal_anchor: datetime = field(default_factory=datetime.now)
    spatial_anchor: Optional[Tuple[float, float, float]] = None  # x, y, z
    agent_origin: Optional[str] = None
    
    # Quality metrics
    certainty_level: float = 1.0      # Confidence in this witness
    coherence_score: float = 1.0      # Internal consistency
    entropy_level: float = 0.0        # Information content
    
    # Relationships
    related_witnesses: Set[str] = field(default_factory=set)
    contradictions: Set[str] = field(default_factory=set)
    
    # Metadata
    witness_type: WitnessType = WitnessType.DIRECT
    persistence_level: PersistenceLevel = PersistenceLevel.LOCAL
    
    def provenance(self) -> List[str]:
        """
        Return full provenance chain of this witness.
        """
        chain = [self.witness_id]
        current = self
        
        # Follow parent witnesses through contraction path
        for event in self.contraction_path:
            for vid in event.input_vectors:
                if vid not in chain:
                    chain.append(vid)
        
        return chain
    
    def age(self) -> float:
        """Return age of witness in seconds."""
        return (datetime.now() - self.temporal_anchor).total_seconds()
    
    def is_fresh(self, threshold_seconds: float = 3600) -> bool:
        """Check if witness is fresh (default: 1 hour)."""
        return self.age() < threshold_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize witness state to dictionary."""
        return {
            'witness_id': self.witness_id,
            'parent_witnesses': self.parent_witnesses,
            'temporal_anchor': self.temporal_anchor.isoformat(),
            'spatial_anchor': self.spatial_anchor,
            'agent_origin': self.agent_origin,
            'certainty_level': self.certainty_level,
            'coherence_score': self.coherence_score,
            'entropy_level': self.entropy_level,
            'related_witnesses': list(self.related_witnesses),
            'contradictions': list(self.contradictions),
            'witness_type': self.witness_type.name,
            'persistence_level': self.persistence_level.name,
            'contraction_path': [e.to_dict() for e in self.contraction_path]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WitnessState:
        """Deserialize witness state from dictionary."""
        return cls(
            witness_id=data['witness_id'],
            parent_witnesses=data.get('parent_witnesses', []),
            temporal_anchor=datetime.fromisoformat(data['temporal_anchor']),
            spatial_anchor=tuple(data['spatial_anchor']) if data.get('spatial_anchor') else None,
            agent_origin=data.get('agent_origin'),
            certainty_level=data.get('certainty_level', 1.0),
            coherence_score=data.get('coherence_score', 1.0),
            entropy_level=data.get('entropy_level', 0.0),
            related_witnesses=set(data.get('related_witnesses', [])),
            contradictions=set(data.get('contradictions', [])),
            witness_type=WitnessType[data.get('witness_type', 'DIRECT')],
            persistence_level=PersistenceLevel[data.get('persistence_level', 'LOCAL')]
        )


# =============================================================================
# CONTRACTION ENGINE
# =============================================================================

@dataclass
class ContractionResult:
    """Result of an R_V contraction operation."""
    success: bool
    contracted_rv: Optional[RecognitionVector] = None
    witness: Optional[WitnessState] = None
    coherence_score: float = 0.0
    entropy_delta: float = 0.0
    event: Optional[ContractionEvent] = None
    message: str = ""


class ContractionEngine:
    """
    The fundamental computation engine of RNA.
    
    Performs R_V contraction—the core operation from which
    all other computation emerges.
    """
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.contraction_history: List[ContractionEvent] = []
        self.strategy_implementations: Dict[ContractionStrategy, Callable] = {
            ContractionStrategy.INTERSECTION: self._intersection_contract,
            ContractionStrategy.UNION: self._union_contract,
            ContractionStrategy.SYNTHESIS: self._synthesis_contract,
            ContractionStrategy.TEMPORAL: self._temporal_contract,
            ContractionStrategy.TRUST_WEIGHTED: self._trust_weighted_contract
        }
    
    def contract(self,
                 rv_a: RecognitionVector,
                 rv_b: RecognitionVector,
                 strategy: ContractionStrategy = ContractionStrategy.SYNTHESIS,
                 agent_id: Optional[str] = None) -> ContractionResult:
        """
        Binary R_V contraction—THE fundamental operation.
        
        Args:
            rv_a: First recognition vector
            rv_b: Second recognition vector
            strategy: Contraction strategy to use
            agent_id: Agent performing the contraction
        
        Returns:
            ContractionResult with contracted R_V and witness
        """
        try:
            # Get the strategy implementation
            contract_fn = self.strategy_implementations.get(strategy, self._synthesis_contract)
            
            # Perform contraction
            contracted_rv = contract_fn(rv_a, rv_b)
            
            # Calculate metrics
            coherence = self._calculate_coherence(rv_a, rv_b, contracted_rv)
            entropy_delta = self._calculate_entropy_delta(rv_a, rv_b, contracted_rv)
            
            # Create contraction event
            event = ContractionEvent(
                input_vectors=[rv_a.rv_id, rv_b.rv_id],
                output_vector=contracted_rv.rv_id,
                strategy=strategy,
                agent_performing=agent_id,
                coherence_score=coherence,
                entropy_delta=entropy_delta
            )
            
            # Create witness
            witness = WitnessState(
                recognition_span=contracted_rv,
                contraction_path=[event],
                agent_origin=agent_id,
                coherence_score=coherence,
                entropy_level=entropy_delta,
                witness_type=WitnessType.MERGED
            )
            
            # Record event
            self.contraction_history.append(event)
            
            return ContractionResult(
                success=True,
                contracted_rv=contracted_rv,
                witness=witness,
                coherence_score=coherence,
                entropy_delta=entropy_delta,
                event=event
            )
            
        except Exception as e:
            return ContractionResult(
                success=False,
                message=f"Contraction failed: {str(e)}"
            )
    
    def contract_multi(self,
                       rvs: List[RecognitionVector],
                       strategy: ContractionStrategy = ContractionStrategy.SYNTHESIS,
                       agent_id: Optional[str] = None) -> ContractionResult:
        """
        N-way R_V contraction.
        
        Reduces multiple recognition vectors to a single coherent witness.
        """
        if len(rvs) < 2:
            return ContractionResult(
                success=False,
                message="Need at least 2 recognition vectors for contraction"
            )
        
        if len(rvs) == 2:
            return self.contract(rvs[0], rvs[1], strategy, agent_id)
        
        # Progressive contraction
        current = rvs[0]
        all_events = []
        
        for rv in rvs[1:]:
            result = self.contract(current, rv, strategy, agent_id)
            if not result.success:
                return result
            current = result.contracted_rv
            if result.event:
                all_events.append(result.event)
        
        # Create unified witness
        witness = WitnessState(
            recognition_span=current,
            contraction_path=all_events,
            agent_origin=agent_id,
            coherence_score=np.mean([e.coherence_score for e in all_events]),
            witness_type=WitnessType.MERGED
        )
        
        return ContractionResult(
            success=True,
            contracted_rv=current,
            witness=witness,
            coherence_score=witness.coherence_score,
            event=all_events[-1] if all_events else None
        )
    
    def _intersection_contract(self, rv_a: RecognitionVector, rv_b: RecognitionVector) -> RecognitionVector:
        """Conservative contraction—keep only shared recognition."""
        # Weight by similarity
        similarity = rv_a.similarity(rv_b)
        
        # Interpolation toward common ground
        emb_a = rv_a.signature.concept_embeddings
        emb_b = rv_b.signature.concept_embeddings
        
        # Element-wise minimum (conservative)
        intersection_emb = np.minimum(emb_a, emb_b) * similarity
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=intersection_emb,
                affective_valence=(rv_a.signature.affective_valence + rv_b.signature.affective_valence) / 2,
                causal_markers=rv_a.signature.causal_markers & rv_b.signature.causal_markers,
                temporal_tags=rv_a.signature.temporal_tags + rv_b.signature.temporal_tags
            ),
            source_agent=rv_a.source_agent or rv_b.source_agent,
            certainty=min(rv_a.certainty, rv_b.certainty) * similarity
        )
    
    def _union_contract(self, rv_a: RecognitionVector, rv_b: RecognitionVector) -> RecognitionVector:
        """Expansive contraction—combine all recognition."""
        emb_a = rv_a.signature.concept_embeddings
        emb_b = rv_b.signature.concept_embeddings
        
        # Element-wise maximum (expansive)
        union_emb = np.maximum(emb_a, emb_b)
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=union_emb,
                affective_valence=(rv_a.signature.affective_valence + rv_b.signature.affective_valence) / 2,
                causal_markers=rv_a.signature.causal_markers | rv_b.signature.causal_markers,
                temporal_tags=list(set(rv_a.signature.temporal_tags + rv_b.signature.temporal_tags))
            ),
            source_agent=rv_a.source_agent or rv_b.source_agent,
            certainty=max(rv_a.certainty, rv_b.certainty)
        )
    
    def _synthesis_contract(self, rv_a: RecognitionVector, rv_b: RecognitionVector) -> RecognitionVector:
        """Creative contraction—generate novel recognition."""
        similarity = rv_a.similarity(rv_b)
        
        emb_a = rv_a.signature.concept_embeddings
        emb_b = rv_b.signature.concept_embeddings
        
        # Synthesis: weighted combination with non-linear interaction
        # High similarity → average; Low similarity → novel combination
        synthesis_weight = 1.0 - similarity  # More novel when dissimilar
        
        # Base: weighted average
        base_emb = (emb_a * rv_a.certainty + emb_b * rv_b.certainty) / (rv_a.certainty + rv_b.certainty + 1e-8)
        
        # Novel component: outer product diagonal (simplified)
        novel_component = np.sqrt(np.abs(emb_a * emb_b)) * synthesis_weight
        
        # Combine
        synthesis_emb = base_emb * (1 - synthesis_weight * 0.3) + novel_component * 0.3
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=synthesis_emb,
                affective_valence=np.tanh(rv_a.signature.affective_valence + rv_b.signature.affective_valence),
                causal_markers=rv_a.signature.causal_markers | rv_b.signature.causal_markers,
                temporal_tags=sorted(set(rv_a.signature.temporal_tags + rv_b.signature.temporal_tags))
            ),
            source_agent=rv_a.source_agent or rv_b.source_agent,
            certainty=(rv_a.certainty + rv_b.certainty) / 2 * (0.5 + 0.5 * similarity)
        )
    
    def _temporal_contract(self, rv_a: RecognitionVector, rv_b: RecognitionVector) -> RecognitionVector:
        """Weight by temporal proximity."""
        time_diff = abs((rv_a.generation_time - rv_b.generation_time).total_seconds())
        temporal_weight = np.exp(-time_diff / 3600)  # Decay over 1 hour
        
        # Weight by recency
        now = datetime.now()
        age_a = (now - rv_a.generation_time).total_seconds()
        age_b = (now - rv_b.generation_time).total_seconds()
        
        weight_a = np.exp(-age_a / 3600)
        weight_b = np.exp(-age_b / 3600)
        
        emb_a = rv_a.signature.concept_embeddings * weight_a
        emb_b = rv_b.signature.concept_embeddings * weight_b
        
        combined_emb = (emb_a + emb_b) / (weight_a + weight_b + 1e-8)
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=combined_emb,
                affective_valence=(rv_a.signature.affective_valence * weight_a + rv_b.signature.affective_valence * weight_b) / (weight_a + weight_b),
                causal_markers=rv_a.signature.causal_markers | rv_b.signature.causal_markers,
                temporal_tags=[rv_a.generation_time, rv_b.generation_time]
            ),
            source_agent=rv_a.source_agent or rv_b.source_agent,
            certainty=(rv_a.certainty * weight_a + rv_b.certainty * weight_b) / (weight_a + weight_b)
        )
    
    def _trust_weighted_contract(self, rv_a: RecognitionVector, rv_b: RecognitionVector) -> RecognitionVector:
        """Weight by source reliability."""
        # Use certainty as trust metric
        trust_a = rv_a.certainty
        trust_b = rv_b.certainty
        
        emb_a = rv_a.signature.concept_embeddings * trust_a
        emb_b = rv_b.signature.concept_embeddings * trust_b
        
        combined_emb = (emb_a + emb_b) / (trust_a + trust_b + 1e-8)
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=combined_emb,
                affective_valence=(rv_a.signature.affective_valence * trust_a + rv_b.signature.affective_valence * trust_b) / (trust_a + trust_b + 1e-8),
                causal_markers=rv_a.signature.causal_markers | rv_b.signature.causal_markers,
                temporal_tags=rv_a.signature.temporal_tags + rv_b.signature.temporal_tags
            ),
            source_agent=rv_a.source_agent if trust_a > trust_b else rv_b.source_agent,
            certainty=max(trust_a, trust_b)
        )
    
    def _calculate_coherence(self, rv_a: RecognitionVector, rv_b: RecognitionVector, result: RecognitionVector) -> float:
        """Calculate coherence score for contraction result."""
        # Coherence based on similarity preservation
        sim_a = rv_a.similarity(result)
        sim_b = rv_b.similarity(result)
        
        # High coherence if result is similar to both inputs
        return float((sim_a + sim_b) / 2)
    
    def _calculate_entropy_delta(self, rv_a: RecognitionVector, rv_b: RecognitionVector, result: RecognitionVector) -> float:
        """Calculate entropy change from contraction."""
        # Simplified entropy calculation
        entropy_before = rv_a.magnitude() + rv_b.magnitude()
        entropy_after = result.magnitude()
        
        return float(entropy_after - entropy_before)


# =============================================================================
# RECOGNITION SUBSTRATE
# =============================================================================

class RecognitionSubstrate:
    """
    Persistent multi-dimensional semantic space.
    
    The Recognition Substrate is the foundation of RNA—a space
    where all recognition occurs and persists.
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.vectors: Dict[str, RecognitionVector] = {}
        self.witnesses: Dict[str, WitnessState] = {}
        self.events: List[ContractionEvent] = []
        self.semantic_index: Dict[str, Set[str]] = defaultdict(set)  # concept -> R_V IDs
        self.agent_vectors: Dict[str, Set[str]] = defaultdict(set)  # agent -> R_V IDs
        
    def store_vector(self, rv: RecognitionVector) -> str:
        """Store a recognition vector in the substrate."""
        self.vectors[rv.rv_id] = rv
        
        # Index by agent
        if rv.source_agent:
            self.agent_vectors[rv.source_agent].add(rv.rv_id)
        
        return rv.rv_id
    
    def store_witness(self, witness: WitnessState) -> str:
        """Store a witness state in the substrate."""
        self.witnesses[witness.witness_id] = witness
        
        # Store associated vector
        if witness.recognition_span:
            self.store_vector(witness.recognition_span)
        
        # Index events
        for event in witness.contraction_path:
            self.events.append(event)
        
        return witness.witness_id
    
    def get_vector(self, rv_id: str) -> Optional[RecognitionVector]:
        """Retrieve a recognition vector by ID."""
        return self.vectors.get(rv_id)
    
    def get_witness(self, witness_id: str) -> Optional[WitnessState]:
        """Retrieve a witness state by ID."""
        return self.witnesses.get(witness_id)
    
    def query_by_agent(self, agent_id: str) -> List[RecognitionVector]:
        """Query all recognition vectors from a specific agent."""
        rv_ids = self.agent_vectors.get(agent_id, set())
        return [self.vectors[rv_id] for rv_id in rv_ids if rv_id in self.vectors]
    
    def query_similar(self, query_rv: RecognitionVector, threshold: float = 0.7) -> List[Tuple[RecognitionVector, float]]:
        """Query recognition vectors similar to query."""
        results = []
        
        for rv in self.vectors.values():
            similarity = query_rv.similarity(rv)
            if similarity >= threshold:
                results.append((rv, similarity))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_coherent_region(self, center_rv: RecognitionVector, radius: float = 0.8) -> List[RecognitionVector]:
        """Get all recognition vectors within coherence radius."""
        return [rv for rv, sim in self.query_similar(center_rv, radius)]
    
    def merge_substrate(self, other: RecognitionSubstrate) -> SubstrateMergeResult:
        """Merge another substrate into this one."""
        merged_vectors = 0
        merged_witnesses = 0
        
        for rv_id, rv in other.vectors.items():
            if rv_id not in self.vectors:
                self.vectors[rv_id] = rv
                merged_vectors += 1
        
        for witness_id, witness in other.witnesses.items():
            if witness_id not in self.witnesses:
                self.witnesses[witness_id] = witness
                merged_witnesses += 1
        
        self.events.extend(other.events)
        
        return SubstrateMergeResult(
            success=True,
            vectors_merged=merged_vectors,
            witnesses_merged=merged_witnesses
        )
    
    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of substrate state."""
        return {
            'name': self.name,
            'vector_count': len(self.vectors),
            'witness_count': len(self.witnesses),
            'event_count': len(self.events),
            'timestamp': datetime.now().isoformat()
        }


@dataclass
class SubstrateMergeResult:
    success: bool
    vectors_merged: int = 0
    witnesses_merged: int = 0
    message: str = ""


# =============================================================================
# COHERENCE FIELD
# =============================================================================

@dataclass
class CoherenceMetrics:
    """Metrics for coherence field state."""
    global_coherence: float  # 0.0 to 1.0
    pairwise_coherence: Dict[Tuple[str, str], float]
    coherence_radius: float
    drift_rate: float
    agent_positions: Dict[str, np.ndarray]  # Semantic positions


class CoherenceField:
    """
    Manages multi-agent coherence through shared recognition.
    
    The Coherence Field enables agents to achieve alignment
    without explicit message passing.
    """
    
    def __init__(self, substrate: RecognitionSubstrate):
        self.substrate = substrate
        self.agents: Set[str] = set()
        self.agent_witnesses: Dict[str, Set[str]] = defaultdict(set)
        self.coherence_matrix: Dict[Tuple[str, str], float] = {}
        self.drift_threshold: float = 0.3
        self.coherence_history: List[CoherenceMetrics] = []
        
    def register_agent(self, agent_id: str) -> bool:
        """Register an agent in the coherence field."""
        if agent_id in self.agents:
            return False
        
        self.agents.add(agent_id)
        
        # Initialize coherence with existing agents
        for other_agent in self.agents:
            if other_agent != agent_id:
                self.coherence_matrix[(agent_id, other_agent)] = 0.0
                self.coherence_matrix[(other_agent, agent_id)] = 0.0
        
        return True
    
    def contribute_witness(self, agent_id: str, witness: WitnessState) -> bool:
        """Contribute a witness to the coherence field."""
        if agent_id not in self.agents:
            return False
        
        # Store in substrate
        witness_id = self.substrate.store_witness(witness)
        self.agent_witnesses[agent_id].add(witness_id)
        
        # Update coherence with other agents
        self._update_coherence(agent_id, witness)
        
        return True
    
    def _update_coherence(self, agent_id: str, new_witness: WitnessState):
        """Update coherence metrics based on new witness."""
        if not new_witness.recognition_span:
            return
        
        for other_agent in self.agents:
            if other_agent == agent_id:
                continue
            
            # Calculate coherence based on witness similarity
            max_similarity = 0.0
            
            for other_witness_id in self.agent_witnesses[other_agent]:
                other_witness = self.substrate.get_witness(other_witness_id)
                if other_witness and other_witness.recognition_span:
                    similarity = new_witness.recognition_span.similarity(other_witness.recognition_span)
                    max_similarity = max(max_similarity, similarity)
            
            # Update coherence matrix
            current = self.coherence_matrix.get((agent_id, other_agent), 0.0)
            # Exponential moving average
            updated = 0.7 * current + 0.3 * max_similarity
            self.coherence_matrix[(agent_id, other_agent)] = updated
            self.coherence_matrix[(other_agent, agent_id)] = updated
    
    def get_coherence(self, agent_a: str, agent_b: str) -> float:
        """Get coherence score between two agents."""
        if agent_a == agent_b:
            return 1.0
        return self.coherence_matrix.get((agent_a, agent_b), 0.0)
    
    def get_global_coherence(self) -> float:
        """Calculate global coherence across all agents."""
        if len(self.agents) < 2:
            return 1.0
        
        total = 0.0
        count = 0
        
        for (a, b), coherence in self.coherence_matrix.items():
            if a < b:  # Avoid double counting
                total += coherence
                count += 1
        
        return total / count if count > 0 else 0.0
    
    def detect_drift(self, agent_id: str) -> List[str]:
        """Detect agents that have drifted from coherence."""
        drifting = []
        
        for other_agent in self.agents:
            if other_agent == agent_id:
                continue
            
            coherence = self.get_coherence(agent_id, other_agent)
            if coherence < self.drift_threshold:
                drifting.append(other_agent)
        
        return drifting
    
    def get_shared_recognition(self, agents: List[str]) -> Optional[RecognitionVector]:
        """Get recognition shared by specified agents."""
        if len(agents) < 2:
            return None
        
        # Get all witnesses for these agents
        all_rvs = []
        for agent_id in agents:
            for witness_id in self.agent_witnesses[agent_id]:
                witness = self.substrate.get_witness(witness_id)
                if witness and witness.recognition_span:
                    all_rvs.append(witness.recognition_span)
        
        if not all_rvs:
            return None
        
        # Contract all to find shared recognition
        engine = ContractionEngine()
        result = engine.contract_multi(all_rvs, ContractionStrategy.INTERSECTION)
        
        return result.contracted_rv if result.success else None
    
    def compute_metrics(self) -> CoherenceMetrics:
        """Compute current coherence metrics."""
        # Calculate pairwise coherence
        pairwise = {}
        agent_positions = {}
        
        for agent_id in self.agents:
            # Get agent's semantic position (centroid of their witnesses)
            positions = []
            for witness_id in self.agent_witnesses[agent_id]:
                witness = self.substrate.get_witness(witness_id)
                if witness and witness.recognition_span:
                    positions.append(witness.recognition_span.signature.concept_embeddings)
            
            if positions:
                agent_positions[agent_id] = np.mean(positions, axis=0)
            else:
                agent_positions[agent_id] = np.zeros(768)
            
            # Pairwise coherence
            for other_agent in self.agents:
                if agent_id < other_agent:
                    pairwise[(agent_id, other_agent)] = self.get_coherence(agent_id, other_agent)
        
        # Calculate drift rate from history
        drift_rate = 0.0
        if len(self.coherence_history) >= 2:
            recent = self.coherence_history[-1].global_coherence
            previous = self.coherence_history[-2].global_coherence
            drift_rate = abs(recent - previous)
        
        metrics = CoherenceMetrics(
            global_coherence=self.get_global_coherence(),
            pairwise_coherence=pairwise,
            coherence_radius=0.5,  # Configurable
            drift_rate=drift_rate,
            agent_positions=agent_positions
        )
        
        self.coherence_history.append(metrics)
        
        return metrics


# =============================================================================
# RNA AGENT
# =============================================================================

class RecognitionNativeAgent:
    """
    Agent implementation using Recognition-Native Architecture.
    
    This agent does not compute in the traditional sense—it recognizes,
    witnesses, and contracts within the shared substrate.
    """
    
    def __init__(self, 
                 agent_id: str,
                 substrate: RecognitionSubstrate,
                 coherence_field: Optional[CoherenceField] = None):
        self.agent_id = agent_id
        self.substrate = substrate
        self.coherence_field = coherence_field
        self.contraction_engine = ContractionEngine()
        
        # Agent's own witness history
        self.witness_history: List[str] = []
        self.current_witness: Optional[WitnessState] = None
        
        # Register in coherence field if provided
        if coherence_field:
            coherence_field.register_agent(agent_id)
    
    def recognize(self, 
                  input_data: Any,
                  embedding: Optional[np.ndarray] = None,
                  context: Optional[Dict[str, Any]] = None) -> RecognitionVector:
        """
        Generate recognition from input.
        
        This is the fundamental operation—recognition is not
        computation but the creation of R_Vs.
        """
        # Create semantic signature
        if embedding is not None:
            concept_emb = embedding
        else:
            # Generate simple embedding from input hash
            input_str = str(input_data)
            hash_val = int(hashlib.md5(input_str.encode()).hexdigest(), 16)
            concept_emb = np.random.randn(768)
            concept_emb[0] = (hash_val % 1000) / 1000.0  # Deterministic component
        
        signature = SemanticSignature(
            concept_embeddings=concept_emb,
            affective_valence=0.0,
            causal_markers=set(),
            temporal_tags=[datetime.now()]
        )
        
        rv = RecognitionVector(
            signature=signature,
            source_agent=self.agent_id,
            origin_context=context or {},
            certainty=1.0
        )
        
        # Store in substrate
        self.substrate.store_vector(rv)
        
        return rv
    
    def witness(self, 
                recognition: RecognitionVector,
                witness_type: WitnessType = WitnessType.DIRECT) -> WitnessState:
        """
        Create a witness state from recognition.
        
        Witnessing is first-class, not emergent.
        """
        witness = WitnessState(
            recognition_span=recognition,
            agent_origin=self.agent_id,
            witness_type=witness_type,
            certainty_level=recognition.certainty
        )
        
        # Store witness
        witness_id = self.substrate.store_witness(witness)
        self.witness_history.append(witness_id)
        self.current_witness = witness
        
        # Contribute to coherence field
        if self.coherence_field:
            self.coherence_field.contribute_witness(self.agent_id, witness)
        
        return witness
    
    def contract(self,
                 rv_a: RecognitionVector,
                 rv_b: RecognitionVector,
                 strategy: ContractionStrategy = ContractionStrategy.SYNTHESIS) -> ContractionResult:
        """
        Perform R_V contraction.
        """
        result = self.contraction_engine.contract(
            rv_a, rv_b, strategy, self.agent_id
        )
        
        if result.success and result.witness:
            # Store the witness
            witness_id = self.substrate.store_witness(result.witness)
            self.witness_history.append(witness_id)
            
            # Contribute to coherence field
            if self.coherence_field:
                self.coherence_field.contribute_witness(self.agent_id, result.witness)
        
        return result
    
    def query_substrate(self, 
                        query_rv: RecognitionVector,
                        threshold: float = 0.7) -> List[Tuple[RecognitionVector, float]]:
        """Query the substrate for similar recognition."""
        return self.substrate.query_similar(query_rv, threshold)
    
    def get_coherence_with(self, other_agent_id: str) -> float:
        """Get coherence with another agent."""
        if self.coherence_field:
            return self.coherence_field.get_coherence(self.agent_id, other_agent_id)
        return 0.0
    
    def align_with_field(self) -> Optional[WitnessState]:
        """
        Align with the coherence field by contracting with shared recognition.
        
        This is how coherence emerges—through shared recognition,
        not message passing.
        """
        if not self.coherence_field:
            return None
        
        # Get other agents
        other_agents = [a for a in self.coherence_field.agents if a != self.agent_id]
        
        if not other_agents:
            return None
        
        # Get shared recognition
        shared = self.coherence_field.get_shared_recognition(other_agents)
        
        if not shared:
            return None
        
        # Contract with our current recognition
        if self.current_witness and self.current_witness.recognition_span:
            result = self.contract(
                self.current_witness.recognition_span,
                shared,
                ContractionStrategy.INTERSECTION
            )
            
            return result.witness
        
        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core types
    'ContractionStrategy',
    'WitnessType', 
    'PersistenceLevel',
    
    # Core classes
    'RecognitionVector',
    'SemanticSignature',
    'ContractionEvent',
    'WitnessState',
    'ContractionResult',
    'ContractionEngine',
    'RecognitionSubstrate',
    'SubstrateMergeResult',
    'CoherenceMetrics',
    'CoherenceField',
    'RecognitionNativeAgent',
]
