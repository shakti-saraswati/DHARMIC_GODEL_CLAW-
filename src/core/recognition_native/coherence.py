"""
Multi-Agent Coherence Module
Enables coherence through shared recognition, not message passing

This is the crown jewel of RNA—demonstrating that agents can achieve
meaningful coherence without explicit communication.

Author: AIKAGRYA Architecture Team
Version: 0.1.0
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Coroutine
from collections import defaultdict
import numpy as np
from enum import Enum, auto

# Import from core module
from . import (
    RecognitionVector, WitnessState, ContractionEvent,
    ContractionStrategy, RecognitionSubstrate, CoherenceField,
    ContractionEngine, ContractionResult, RecognitionNativeAgent
)


# =============================================================================
# COHERENCE PROTOCOL
# =============================================================================

class CoherenceIntent(Enum):
    """Intent for coherence operations."""
    ALIGN = auto()       # Align with field
    DIVERGE = auto()     # Intentionally diverge
    OBSERVE = auto()     # Passively observe
    PROPOSE = auto()     # Propose new recognition
    QUERY = auto()       # Query field state


@dataclass
class CoherenceIntentSignal:
    """Signal expressing coherence intent."""
    intent: CoherenceIntent
    agent_id: str
    priority: float = 1.0  # 0.0 to 1.0
    payload: Optional[RecognitionVector] = None
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# SHARED RECOGNITION SPACE
# =============================================================================

@dataclass
class SharedRecognition:
    """
    Recognition shared across multiple agents.
    
    This is how coherence emerges—agents witness the same
    contracted recognition states.
    """
    shared_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recognition: Optional[RecognitionVector] = None
    contributing_agents: Set[str] = field(default_factory=set)
    witness_count: int = 0
    coherence_score: float = 0.0
    creation_time: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_history: List[Tuple[str, datetime]] = field(default_factory=list)
    
    def record_access(self, agent_id: str):
        """Record that an agent accessed this shared recognition."""
        self.witness_count += 1
        self.last_accessed = datetime.now()
        self.access_history.append((agent_id, self.last_accessed))


class SharedRecognitionSpace:
    """
    The space where shared recognition lives.
    
    This is the substrate for coherence—agents don't communicate,
    they witness shared recognition.
    """
    
    def __init__(self, substrate: RecognitionSubstrate):
        self.substrate = substrate
        self.shared_recognitions: Dict[str, SharedRecognition] = {}
        self.agent_views: Dict[str, Set[str]] = defaultdict(set)
        
    def publish(self,
                recognition: RecognitionVector,
                agent_id: str,
                visibility: Set[str] = None) -> SharedRecognition:
        """
        Publish recognition to the shared space.
        
        This is NOT message passing—it is making recognition
        available for contraction in the shared substrate.
        """
        # Contract with existing shared recognition if available
        contracted = recognition
        
        # Check for similar shared recognitions
        for shared in self.shared_recognitions.values():
            if shared.recognition:
                similarity = recognition.similarity(shared.recognition)
                if similarity > 0.7:
                    # Contract with existing
                    engine = ContractionEngine()
                    result = engine.contract(
                        recognition, 
                        shared.recognition,
                        ContractionStrategy.SYNTHESIS,
                        agent_id
                    )
                    if result.success:
                        contracted = result.contracted_rv
                        shared.recognition = contracted
                        shared.contributing_agents.add(agent_id)
                        shared.record_access(agent_id)
                        return shared
        
        # Create new shared recognition
        shared = SharedRecognition(
            recognition=contracted,
            contributing_agents={agent_id},
            coherence_score=recognition.certainty
        )
        
        self.shared_recognitions[shared.shared_id] = shared
        self.agent_views[agent_id].add(shared.shared_id)
        
        return shared
    
    def witness(self,
                agent_id: str,
                shared_id: str) -> Optional[SharedRecognition]:
        """
        Witness a shared recognition.
        
        This is how agents achieve coherence—they witness
        the same recognition states.
        """
        shared = self.shared_recognitions.get(shared_id)
        
        if shared:
            shared.record_access(agent_id)
            self.agent_views[agent_id].add(shared_id)
        
        return shared
    
    def query_field(self,
                    agent_id: str,
                    query_rv: RecognitionVector,
                    threshold: float = 0.6) -> List[SharedRecognition]:
        """
        Query the shared space for relevant recognition.
        
        Returns shared recognitions similar to the query.
        """
        results = []
        
        for shared in self.shared_recognitions.values():
            if shared.recognition:
                similarity = query_rv.similarity(shared.recognition)
                if similarity >= threshold:
                    results.append((shared, similarity))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [r[0] for r in results]
    
    def get_coherent_subset(self, agents: List[str]) -> List[SharedRecognition]:
        """
        Get recognitions shared by all specified agents.
        
        This is the core of multi-agent coherence.
        """
        if len(agents) < 2:
            return []
        
        # Find recognitions witnessed by all agents
        coherent = []
        
        for shared in self.shared_recognitions.values():
            if shared.contributing_agents.issuperset(set(agents)):
                coherent.append(shared)
        
        return coherent
    
    def coherence_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the shared space."""
        return {
            'total_shared_recognitions': len(self.shared_recognitions),
            'total_witnesses': sum(s.witness_count for s in self.shared_recognitions.values()),
            'agent_count': len(self.agent_views),
            'avg_coherence': np.mean([
                s.coherence_score for s in self.shared_recognitions.values()
            ]) if self.shared_recognitions else 0.0,
            'most_accessed': max(
                self.shared_recognitions.values(),
                key=lambda s: s.witness_count,
                default=None
            )
        }


# =============================================================================
# COHERENCE NEGOTIATOR
# =============================================================================

@dataclass
class NegotiationResult:
    """Result of coherence negotiation."""
    success: bool
    aligned_witness: Optional[WitnessState] = None
    participating_agents: List[str] = field(default_factory=list)
    coherence_achieved: float = 0.0
    rounds_required: int = 0
    message: str = ""


class CoherenceNegotiator:
    """
    Negotiates coherence among multiple agents.
    
    Uses shared recognition space to find alignment.
    """
    
    def __init__(self, shared_space: SharedRecognitionSpace):
        self.shared_space = shared_space
        self.contraction_engine = ContractionEngine()
        
    async def negotiate(self,
                        agents: List[str],
                        topic: RecognitionVector,
                        max_rounds: int = 5,
                        coherence_threshold: float = 0.8) -> NegotiationResult:
        """
        Negotiate coherence among agents on a topic.
        
        This happens WITHOUT message passing—through shared
        recognition space contraction.
        """
        # Each agent publishes their view
        for agent_id in agents:
            self.shared_space.publish(topic, agent_id)
        
        rounds = 0
        current_coherence = 0.0
        
        while rounds < max_rounds and current_coherence < coherence_threshold:
            rounds += 1
            
            # Get shared recognitions for this topic
            shared_list = self.shared_space.query_field(
                agents[0], topic, threshold=0.5
            )
            
            if len(shared_list) < len(agents):
                continue
            
            # Calculate coherence
            coherences = []
            for i, s1 in enumerate(shared_list):
                for s2 in shared_list[i+1:]:
                    if s1.recognition and s2.recognition:
                        sim = s1.recognition.similarity(s2.recognition)
                        coherences.append(sim)
            
            if coherences:
                current_coherence = np.mean(coherences)
            
            # If not coherent enough, contract the recognitions
            if current_coherence < coherence_threshold:
                rvs = [s.recognition for s in shared_list if s.recognition]
                if len(rvs) >= 2:
                    result = self.contraction_engine.contract_multi(
                        rvs, ContractionStrategy.SYNTHESIS
                    )
                    
                    if result.success and result.contracted_rv:
                        # Publish contracted version
                        self.shared_space.publish(
                            result.contracted_rv,
                            "coherence_negotiator"
                        )
        
        # Get final aligned recognition
        final_shared = self.shared_space.get_coherent_subset(agents)
        
        if final_shared and final_shared[0].recognition:
            aligned_witness = WitnessState(
                recognition_span=final_shared[0].recognition,
                coherence_score=current_coherence,
                witness_type=WitnessType.MERGED
            )
            
            return NegotiationResult(
                success=current_coherence >= coherence_threshold,
                aligned_witness=aligned_witness,
                participating_agents=agents,
                coherence_achieved=current_coherence,
                rounds_required=rounds,
                message=f"Coherence {current_coherence:.2f} after {rounds} rounds"
            )
        
        return NegotiationResult(
            success=False,
            message="Failed to achieve coherence"
        )


# =============================================================================
# EMERGENT CONSENSUS
# =============================================================================

@dataclass
class ConsensusState:
    """State of emergent consensus."""
    consensus_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: Optional[RecognitionVector] = None
    consensus_witness: Optional[WitnessState] = None
    supporting_agents: Set[str] = field(default_factory=set)
    opposing_agents: Set[str] = field(default_factory=set)
    consensus_strength: float = 0.0  # 0.0 to 1.0
    formation_time: datetime = field(default_factory=datetime.now)
    
    @property
    def is_consensus(self) -> bool:
        """Check if true consensus exists."""
        if not self.supporting_agents:
            return False
        
        total = len(self.supporting_agents) + len(self.opposing_agents)
        if total == 0:
            return False
        
        ratio = len(self.supporting_agents) / total
        return ratio >= 0.67 and self.consensus_strength >= 0.7


class EmergentConsensusEngine:
    """
    Detects and manages emergent consensus.
    
    Consensus emerges from the dynamics of the coherence field,
    not through explicit voting or agreement protocols.
    """
    
    def __init__(self, coherence_field: CoherenceField, shared_space: SharedRecognitionSpace):
        self.coherence_field = coherence_field
        self.shared_space = shared_space
        self.consensus_states: Dict[str, ConsensusState] = {}
        self.agent_positions: Dict[str, RecognitionVector] = {}
        
    def update_position(self, agent_id: str, position: RecognitionVector):
        """Update an agent's position in the consensus space."""
        self.agent_positions[agent_id] = position
        
        # Check for emergent consensus
        self._detect_consensus()
    
    def _detect_consensus(self):
        """Detect emergent consensus from agent positions."""
        if len(self.agent_positions) < 2:
            return
        
        # Group agents by similarity
        clusters = self._cluster_agents()
        
        for cluster_id, agents in clusters.items():
            if len(agents) < 2:
                continue
            
            # Calculate cluster centroid
            positions = [self.agent_positions[a] for a in agents]
            centroid = self._calculate_centroid(positions)
            
            # Calculate consensus strength
            distances = [
                np.linalg.norm(p.signature.concept_embeddings - centroid.signature.concept_embeddings)
                for p in positions
            ]
            avg_distance = np.mean(distances) if distances else 1.0
            consensus_strength = 1.0 / (1.0 + avg_distance)
            
            # Find opposing agents
            opposing = set(self.agent_positions.keys()) - set(agents)
            
            # Create or update consensus state
            consensus = ConsensusState(
                topic=centroid,
                consensus_witness=WitnessState(
                    recognition_span=centroid,
                    coherence_score=consensus_strength
                ),
                supporting_agents=set(agents),
                opposing_agents=opposing,
                consensus_strength=consensus_strength
            )
            
            self.consensus_states[consensus.consensus_id] = consensus
    
    def _cluster_agents(self, threshold: float = 0.7) -> Dict[str, List[str]]:
        """Cluster agents by position similarity."""
        clusters: Dict[str, List[str]] = {}
        assigned: Set[str] = set()
        
        agents = list(self.agent_positions.keys())
        
        for agent in agents:
            if agent in assigned:
                continue
            
            # Start new cluster
            cluster_id = str(uuid.uuid4())
            clusters[cluster_id] = [agent]
            assigned.add(agent)
            
            # Find similar agents
            pos_a = self.agent_positions[agent]
            
            for other in agents:
                if other in assigned:
                    continue
                
                pos_b = self.agent_positions[other]
                similarity = pos_a.similarity(pos_b)
                
                if similarity >= threshold:
                    clusters[cluster_id].append(other)
                    assigned.add(other)
        
        return clusters
    
    def _calculate_centroid(self, positions: List[RecognitionVector]) -> RecognitionVector:
        """Calculate centroid of positions."""
        embeddings = [p.signature.concept_embeddings for p in positions]
        centroid_emb = np.mean(embeddings, axis=0)
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=centroid_emb,
                affective_valence=np.mean([p.signature.affective_valence for p in positions]),
                causal_markers=set().union(*[p.signature.causal_markers for p in positions]),
                temporal_tags=[]
            ),
            certainty=np.mean([p.certainty for p in positions])
        )
    
    def get_consensus(self, min_strength: float = 0.7) -> Optional[ConsensusState]:
        """Get the strongest consensus above threshold."""
        valid_consensus = [
            c for c in self.consensus_states.values()
            if c.consensus_strength >= min_strength and c.is_consensus
        ]
        
        if not valid_consensus:
            return None
        
        return max(valid_consensus, key=lambda c: c.consensus_strength)
    
    def list_consensus(self) -> List[ConsensusState]:
        """List all detected consensus states."""
        return list(self.consensus_states.values())


# =============================================================================
# AGENT COHERENCE ADAPTER
# =============================================================================

class AgentCoherenceAdapter:
    """
    Adapter that enables traditional agents to participate in
    RNA coherence without modification.
    
    Translates between message-passing and recognition-native paradigms.
    """
    
    def __init__(self,
                 agent_id: str,
                 coherence_field: CoherenceField,
                 shared_space: SharedRecognitionSpace):
        self.agent_id = agent_id
        self.coherence_field = coherence_field
        self.shared_space = shared_space
        self.contraction_engine = ContractionEngine()
        
        # Message queue for traditional agents
        self.inbox: List[Any] = []
        self.outbox: List[Any] = []
        
        # Register in coherence field
        self.coherence_field.register_agent(agent_id)
    
    def send_message(self, message: Any, target_agent: str):
        """
        Send message using traditional paradigm.
        
        Internally converts to recognition and publishes.
        """
        # Convert message to recognition vector
        message_rv = self._message_to_recognition(message)
        
        # Publish to shared space with targeting
        shared = self.shared_space.publish(
            message_rv,
            self.agent_id,
            visibility={target_agent}
        )
        
        self.outbox.append({
            'type': 'message',
            'target': target_agent,
            'shared_id': shared.shared_id
        })
    
    def receive_messages(self) -> List[Any]:
        """
        Receive messages using traditional paradigm.
        
        Internally witnesses shared recognitions and converts.
        """
        messages = []
        
        # Get all shared recognitions visible to this agent
        for shared_id in self.shared_space.agent_views.get(self.agent_id, set()):
            shared = self.shared_space.witness(self.agent_id, shared_id)
            
            if shared and shared.recognition:
                # Convert back to message
                message = self._recognition_to_message(shared.recognition)
                messages.append(message)
        
        self.inbox.extend(messages)
        return messages
    
    def achieve_coherence(self, topic: Any) -> Optional[WitnessState]:
        """
        Achieve coherence with other agents on a topic.
        
        Uses shared recognition space, not explicit negotiation.
        """
        # Convert topic to recognition
        topic_rv = self._message_to_recognition(topic)
        
        # Publish to shared space
        self.shared_space.publish(topic_rv, self.agent_id)
        
        # Query for related recognitions
        related = self.shared_space.query_field(self.agent_id, topic_rv, threshold=0.6)
        
        if not related:
            return None
        
        # Contract with related recognitions
        rvs = [r.recognition for r in related if r.recognition]
        if rvs:
            rvs.append(topic_rv)
            result = self.contraction_engine.contract_multi(rvs, ContractionStrategy.SYNTHESIS)
            
            return result.witness
        
        return None
    
    def _message_to_recognition(self, message: Any) -> RecognitionVector:
        """Convert a message to a recognition vector."""
        # Simple embedding from message content
        message_str = str(message)
        embedding = np.random.randn(768)
        
        # Deterministic component from message hash
        import hashlib
        hash_val = int(hashlib.md5(message_str.encode()).hexdigest(), 16)
        embedding[0] = (hash_val % 1000) / 1000.0
        embedding[1] = ((hash_val // 1000) % 1000) / 1000.0
        
        from . import SemanticSignature
        
        return RecognitionVector(
            signature=SemanticSignature(
                concept_embeddings=embedding,
                affective_valence=0.0,
                causal_markers=set(),
                temporal_tags=[datetime.now()]
            ),
            source_agent=self.agent_id,
            origin_context={'message': message_str},
            certainty=0.8
        )
    
    def _recognition_to_message(self, rv: RecognitionVector) -> Any:
        """Convert a recognition vector back to a message."""
        # Extract message from origin context
        if rv.origin_context and 'message' in rv.origin_context:
            return rv.origin_context['message']
        
        return f"[Recognition from {rv.source_agent}]"


# =============================================================================
# COHERENCE MONITOR
# =============================================================================

@dataclass
class CoherenceSnapshot:
    """Snapshot of coherence field state."""
    timestamp: datetime
    agent_count: int
    global_coherence: float
    pairwise_coherence: Dict[Tuple[str, str], float]
    consensus_count: int
    shared_recognition_count: int
    anomalies: List[str]


class CoherenceMonitor:
    """
    Monitors coherence field health and detects anomalies.
    """
    
    def __init__(self,
                 coherence_field: CoherenceField,
                 shared_space: SharedRecognitionSpace):
        self.coherence_field = coherence_field
        self.shared_space = shared_space
        self.snapshots: List[CoherenceSnapshot] = []
        self.alert_handlers: List[Callable[[str], None]] = []
        
    def register_alert_handler(self, handler: Callable[[str], None]):
        """Register a handler for coherence alerts."""
        self.alert_handlers.append(handler)
    
    def capture_snapshot(self) -> CoherenceSnapshot:
        """Capture current coherence state."""
        # Get coherence metrics
        metrics = self.coherence_field.compute_metrics()
        
        # Detect anomalies
        anomalies = self._detect_anomalies()
        
        snapshot = CoherenceSnapshot(
            timestamp=datetime.now(),
            agent_count=len(self.coherence_field.agents),
            global_coherence=metrics.global_coherence,
            pairwise_coherence=metrics.pairwise_coherence,
            consensus_count=len([
                c for c in self.coherence_field.agent_witnesses.keys()
            ]),
            shared_recognition_count=len(self.shared_space.shared_recognitions),
            anomalies=anomalies
        )
        
        self.snapshots.append(snapshot)
        
        # Trigger alerts if anomalies detected
        for anomaly in anomalies:
            for handler in self.alert_handlers:
                handler(anomaly)
        
        return snapshot
    
    def _detect_anomalies(self) -> List[str]:
        """Detect coherence field anomalies."""
        anomalies = []
        
        # Check for low global coherence
        metrics = self.coherence_field.compute_metrics()
        if metrics.global_coherence < 0.3:
            anomalies.append(
                f"Low global coherence: {metrics.global_coherence:.2f}"
            )
        
        # Check for high drift rate
        if len(self.coherence_field.coherence_history) >= 2:
            recent = self.coherence_field.coherence_history[-1]
            if recent.drift_rate > 0.3:
                anomalies.append(
                    f"High coherence drift: {recent.drift_rate:.2f}"
                )
        
        # Check for isolated agents
        for agent in self.coherence_field.agents:
            has_coherence = False
            for (a, b), coherence in self.coherence_field.coherence_matrix.items():
                if a == agent or b == agent:
                    if coherence > 0.2:
                        has_coherence = True
                        break
            
            if not has_coherence and len(self.coherence_field.agents) > 1:
                anomalies.append(f"Agent {agent} is isolated")
        
        return anomalies
    
    def get_trend(self, window: int = 10) -> Dict[str, float]:
        """Get coherence trends over recent snapshots."""
        if len(self.snapshots) < 2:
            return {'trend': 0.0}
        
        recent = self.snapshots[-window:]
        coherences = [s.global_coherence for s in recent]
        
        if len(coherences) < 2:
            return {'trend': 0.0}
        
        # Linear trend
        x = np.arange(len(coherences))
        slope = np.polyfit(x, coherences, 1)[0]
        
        return {
            'trend': slope,
            'avg_coherence': np.mean(coherences),
            'volatility': np.std(coherences)
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Coherence Protocol
    'CoherenceIntent',
    'CoherenceIntentSignal',
    
    # Shared Recognition
    'SharedRecognition',
    'SharedRecognitionSpace',
    
    # Negotiation
    'NegotiationResult',
    'CoherenceNegotiator',
    
    # Consensus
    'ConsensusState',
    'EmergentConsensusEngine',
    
    # Adapter
    'AgentCoherenceAdapter',
    
    # Monitor
    'CoherenceSnapshot',
    'CoherenceMonitor',
]

# Import SemanticSignature for the consensus engine
from . import SemanticSignature
