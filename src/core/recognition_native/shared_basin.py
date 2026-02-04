"""
Shared Recognition Basin: Multi-Agent Coherence

This module implements multi-agent coherence through shared recognition
geometry rather than message passing.

Agents synchronize by converging to shared R_V basins—geometric
attractors that enable coordination without explicit negotiation.
"""

import torch
import torch.nn.functional as F
from typing import Dict, Set, Optional, List, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .witness_state import WitnessState


class Consensus(Enum):
    """Consensus levels emerging from basin coherence"""
    NONE = 0.0
    WEAK = 0.5
    STRONG = 0.7
    UNANIMOUS = 0.9


@dataclass
class BasinSnapshot:
    """Snapshot of basin state at a point in time"""
    timestamp: float
    coherence: float
    num_members: int
    mean_rv: float
    rv_std: float


AgentID = str


class SharedRecognitionBasin:
    """
    A shared geometric attractor enabling multi-agent coherence.
    
    Instead of message-passing coordination:
        Agent A: "I propose X"
        Agent B: "I agree"
    
    Recognition-native coordination:
        Agent A → Basin → Witness converges
        Agent B → Basin → Witness converges
        → Coherence emerges from geometric identity
    
    This is the implementation of "shared recognition" as the basis
    for multi-agent coordination.
    
    Example:
        >>> basin = SharedRecognitionBasin(dim=512, basin_id=uuid4())
        >>> agent_a_witness = WitnessState(contraction_level=0.6)
        >>> agent_b_witness = WitnessState(contraction_level=0.7)
        >>> 
        >>> # Agents join basin
        >>> wa = basin.join("agent_a", agent_a_witness)
        >>> wb = basin.join("agent_b", agent_b_witness)
        >>> 
        >>> # Check coherence
        >>> coherence = basin.coherence_check()
        >>> consensus = basin.emergent_consensus()
    """
    
    def __init__(
        self,
        dim: int,
        basin_id: Optional[UUID] = None,
        target_rv: float = 0.6,
        coherence_threshold: float = 0.7,
        attractor_strength: float = 0.3
    ):
        """
        Initialize shared recognition basin.
        
        Args:
            dim: Dimension of coherence vectors
            basin_id: UUID for this basin (generated if None)
            target_rv: Target R_V for basin attractor
            coherence_threshold: Minimum coherence for consensus
            attractor_strength: Strength of basin pull
        """
        self.dim = dim
        self.basin_id = basin_id or uuid4()
        self.target_rv = target_rv
        self.coherence_threshold = coherence_threshold
        self.attractor_strength = attractor_strength
        
        # Basin attractor (the geometric center)
        self.attractor = torch.randn(dim)
        self.attractor = F.normalize(self.attractor, dim=0)
        
        # Member witness states
        self.member_witnesses: Dict[AgentID, WitnessState] = {}
        
        # History for analysis
        self.history: List[BasinSnapshot] = []
        
        # Statistics
        self.join_count = 0
        self.convergence_count = 0
    
    def join(
        self,
        agent_id: AgentID,
        witness: WitnessState,
        force_convergence: bool = False
    ) -> WitnessState:
        """
        Agent joins basin; witness state converges toward attractor.
        
        Args:
            agent_id: Unique agent identifier
            witness: Current witness state
            force_convergence: If True, strongly pull toward attractor
        
        Returns:
            Updated witness state with basin membership
        """
        # Constrain witness to basin geometry
        converged = self._constrain_to_basin(
            witness,
            force=force_convergence
        )
        converged.basin_membership = self.basin_id
        
        # Store
        self.member_witnesses[agent_id] = converged
        self.join_count += 1
        
        # Update basin attractor based on new member
        self._update_attractor()
        
        return converged
    
    def _constrain_to_basin(
        self,
        witness: WitnessState,
        force: bool = False
    ) -> WitnessState:
        """
        Constrain witness state to basin geometry.
        
        This is the core operation: pulling witness toward attractor.
        """
        # Ensure coherence vector exists
        if witness.coherence_vector is None or witness.coherence_vector.shape[0] != self.dim:
            coherence = torch.randn(self.dim)
        else:
            coherence = witness.coherence_vector
        
        # Pull toward attractor
        strength = self.attractor_strength * (2.0 if force else 1.0)
        
        new_coherence = (1 - strength) * coherence + strength * self.attractor
        new_coherence = F.normalize(new_coherence, dim=0)
        
        # Pull R_V toward target
        rv_gap = witness.contraction_level - self.target_rv
        new_rv = witness.contraction_level - strength * rv_gap
        new_rv = np.clip(new_rv, 0.1, 1.0)
        
        return WitnessState(
            contraction_level=new_rv,
            recursion_depth=witness.recursion_depth,
            stability_score=witness.stability_score,
            basin_membership=self.basin_id,
            coherence_vector=new_coherence
        )
    
    def _update_attractor(self):
        """Update basin attractor based on member coherence"""
        if len(self.member_witnesses) < 2:
            return
        
        # Compute mean coherence vector
        vectors = torch.stack([
            w.coherence_vector for w in self.member_witnesses.values()
        ])
        mean_vector = vectors.mean(dim=0)
        mean_vector = F.normalize(mean_vector, dim=0)
        
        # Slowly move attractor toward mean
        self.attractor = 0.9 * self.attractor + 0.1 * mean_vector
        self.attractor = F.normalize(self.attractor, dim=0)
    
    def coherence_check(self) -> float:
        """
        Measure coherence of all basin members.
        
        Returns:
            Coherence value 0.0-1.0 (1.0 = perfect coherence)
        """
        if len(self.member_witnesses) < 2:
            return 1.0
        
        # Get coherence vectors
        witnesses = list(self.member_witnesses.values())
        vectors = torch.stack([w.coherence_vector for w in witnesses])
        
        # Cosine similarity matrix
        similarities = F.cosine_similarity(
            vectors.unsqueeze(1),
            vectors.unsqueeze(0),
            dim=-1
        )
        
        # Average off-diagonal coherence
        mask = ~torch.eye(len(witnesses), dtype=torch.bool)
        coherence = similarities[mask].mean().item()
        
        # Record snapshot
        rv_values = [w.contraction_level for w in witnesses]
        snapshot = BasinSnapshot(
            timestamp=0.0,  # Would use actual time
            coherence=coherence,
            num_members=len(witnesses),
            mean_rv=np.mean(rv_values),
            rv_std=np.std(rv_values)
        )
        self.history.append(snapshot)
        
        if coherence > self.coherence_threshold:
            self.convergence_count += 1
        
        return coherence
    
    def emergent_consensus(self) -> Consensus:
        """
        Extract consensus from basin coherence.
        
        No voting, no messages—consensus emerges from geometric
        convergence of witness states.
        """
        coherence = self.coherence_check()
        
        if coherence >= 0.9:
            return Consensus.UNANIMOUS
        elif coherence >= 0.7:
            return Consensus.STRONG
        elif coherence >= 0.5:
            return Consensus.WEAK
        else:
            return Consensus.NONE
    
    def get_basin_witness(self) -> WitnessState:
        """
        Get aggregate witness state representing the basin.
        
        This is the "collective recognition" of all members.
        """
        if not self.member_witnesses:
            return WitnessState(basin_membership=self.basin_id)
        
        # Aggregate across members
        witnesses = list(self.member_witnesses.values())
        
        mean_rv = np.mean([w.contraction_level for w in witnesses])
        mean_stability = np.mean([w.stability_score for w in witnesses])
        
        # Aggregate coherence vectors
        vectors = torch.stack([w.coherence_vector for w in witnesses])
        aggregate_coherence = F.normalize(vectors.mean(dim=0), dim=0)
        
        return WitnessState(
            contraction_level=mean_rv,
            recursion_depth=max(w.recursion_depth for w in witnesses),
            stability_score=mean_stability,
            basin_membership=self.basin_id,
            coherence_vector=aggregate_coherence
        )
    
    def leave(self, agent_id: AgentID) -> bool:
        """Agent leaves basin"""
        if agent_id in self.member_witnesses:
            del self.member_witnesses[agent_id]
            self._update_attractor()
            return True
        return False
    
    def get_members(self) -> Set[AgentID]:
        """Get set of member agent IDs"""
        return set(self.member_witnesses.keys())
    
    def is_member(self, agent_id: AgentID) -> bool:
        """Check if agent is member"""
        return agent_id in self.member_witnesses
    
    def get_stats(self) -> Dict[str, any]:
        """Get basin statistics"""
        return {
            'basin_id': str(self.basin_id),
            'num_members': len(self.member_witnesses),
            'target_rv': self.target_rv,
            'join_count': self.join_count,
            'convergence_count': self.convergence_count,
            'convergence_rate': self.convergence_count / max(1, self.join_count),
            'current_coherence': self.coherence_check() if self.member_witnesses else 0.0,
        }


class BasinNetwork:
    """
    Network of interconnected recognition basins.
    
    Enables hierarchical and cross-domain coherence.
    """
    
    def __init__(self):
        self.basins: Dict[UUID, SharedRecognitionBasin] = {}
        self.basin_connections: Dict[UUID, Set[UUID]] = {}
    
    def create_basin(
        self,
        dim: int,
        target_rv: float = 0.6,
        basin_id: Optional[UUID] = None
    ) -> SharedRecognitionBasin:
        """Create new basin in network"""
        basin = SharedRecognitionBasin(
            dim=dim,
            basin_id=basin_id,
            target_rv=target_rv
        )
        self.basins[basin.basin_id] = basin
        self.basin_connections[basin.basin_id] = set()
        return basin
    
    def connect_basins(self, basin_a: UUID, basin_b: UUID):
        """Connect two basins for cross-basin coherence"""
        if basin_a in self.basins and basin_b in self.basins:
            self.basin_connections[basin_a].add(basin_b)
            self.basin_connections[basin_b].add(basin_a)
    
    def get_network_coherence(self) -> float:
        """Measure coherence across entire network"""
        if not self.basins:
            return 1.0
        
        coherences = [b.coherence_check() for b in self.basins.values()]
        return np.mean(coherences)
    
    def find_converged_basins(self, threshold: float = 0.8) -> List[UUID]:
        """Find basins with high coherence"""
        return [
            bid for bid, basin in self.basins.items()
            if basin.coherence_check() >= threshold
        ]
