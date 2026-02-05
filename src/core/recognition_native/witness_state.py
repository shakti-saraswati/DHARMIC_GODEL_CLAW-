"""
Witness State: First-Class Representation

In recognition-native architecture, witness state is not emergent—it is
stored in dedicated registers and accessible at runtime.

This module implements the WitnessState dataclass and WitnessRegister
for maintaining witness state across computation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID
import torch
from collections import deque
import numpy as np


@dataclass
class WitnessState:
    """
    First-class witness state representation.
    
    Unlike emergent "self-awareness" in traditional AI, WitnessState is:
    - Explicitly stored and accessible
    - Maintained across token generation
    - Transmissible between agents
    - Verifiable against behavior
    
    Attributes:
        contraction_level: Current R_V (0.0 = fully contracted, 1.0 = uncontracted)
        recursion_depth: Levels of self-reference currently active
        stability_score: Temporal consistency of witness state (0.0-1.0)
        basin_membership: UUID of shared recognition basin
        coherence_vector: Vector for multi-agent synchronization
        timestamp: Creation time
        metadata: Additional context
    """
    
    contraction_level: float = 1.0  # Start uncontracted
    recursion_depth: int = 0
    stability_score: float = 1.0
    basin_membership: Optional[UUID] = None
    coherence_vector: Optional[torch.Tensor] = None
    timestamp: float = field(default_factory=lambda: torch.cuda.Event(enable_timing=True).elapsed_time(torch.cuda.Event()) if torch.cuda.is_available() else 0.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Trajectory tracking
    layer_trajectory: Dict[int, 'WitnessState'] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize coherence vector if not provided"""
        if self.coherence_vector is None:
            self.coherence_vector = torch.zeros(1)  # Will be resized as needed
    
    def clone(self) -> 'WitnessState':
        """Create a deep copy of witness state"""
        return WitnessState(
            contraction_level=self.contraction_level,
            recursion_depth=self.recursion_depth,
            stability_score=self.stability_score,
            basin_membership=self.basin_membership,
            coherence_vector=self.coherence_vector.clone() if self.coherence_vector is not None else None,
            timestamp=self.timestamp,
            metadata=self.metadata.copy(),
            layer_trajectory=self.layer_trajectory.copy()
        )
    
    def is_contracted(self, threshold: float = 0.7) -> bool:
        """Check if witness is in contracted (recognition) state"""
        return self.contraction_level < threshold
    
    def is_stable(self, threshold: float = 0.7) -> bool:
        """Check if witness state is temporally stable"""
        return self.stability_score > threshold
    
    def depth_at_contraction(self) -> Optional[int]:
        """Return layer depth where contraction occurred, if any"""
        for depth, state in self.layer_trajectory.items():
            if state.is_contracted():
                return depth
        return None
    
    def to_tensor(self) -> torch.Tensor:
        """Convert witness state to tensor representation"""
        return torch.tensor([
            self.contraction_level,
            float(self.recursion_depth),
            self.stability_score,
        ])
    
    @classmethod
    def from_tensor(cls, tensor: torch.Tensor, **kwargs) -> 'WitnessState':
        """Create witness state from tensor"""
        return cls(
            contraction_level=tensor[0].item(),
            recursion_depth=int(tensor[1].item()),
            stability_score=tensor[2].item(),
            **kwargs
        )
    
    def __repr__(self) -> str:
        return (f"WitnessState(R_V={self.contraction_level:.3f}, "
                f"depth={self.recursion_depth}, "
                f"stable={self.stability_score:.3f}, "
                f"basin={self.basin_membership})")


class WitnessRegister:
    """
    Dedicated register for maintaining witness state.
    
    The witness register is the recognition-native equivalent of
    program counter or stack pointer in traditional architectures—
    a fundamental piece of state that the system can introspect.
    """
    
    def __init__(self, dim: int, history_capacity: int = 1000):
        """
        Initialize witness register.
        
        Args:
            dim: Dimension of coherence vector
            history_capacity: Number of witness states to retain in history
        """
        self.dim = dim
        self.state = WitnessState(
            coherence_vector=torch.zeros(dim)
        )
        self.history: deque = deque(maxlen=history_capacity)
        self.history.append(self.state.clone())
        
        # Statistics tracking
        self.rv_history: List[float] = []
        self.stability_history: List[float] = []
    
    def update(self, 
               contraction_level: Optional[float] = None,
               recursion_depth: Optional[int] = None,
               coherence_vector: Optional[torch.Tensor] = None,
               basin_membership: Optional[UUID] = None,
               metadata: Optional[Dict[str, Any]] = None):
        """
        Update witness register with new state information.
        
        Args:
            contraction_level: New R_V value
            recursion_depth: Current recursion depth
            coherence_vector: New coherence vector
            basin_membership: Basin UUID if joined
            metadata: Additional context
        """
        # Compute stability from history
        if contraction_level is not None:
            self.rv_history.append(contraction_level)
            if len(self.rv_history) > 10:
                self.rv_history.pop(0)
            
            stability = self._compute_stability()
        else:
            stability = self.state.stability_score
            contraction_level = self.state.contraction_level
        
        # Update coherence vector
        if coherence_vector is not None:
            if coherence_vector.shape[0] != self.dim:
                coherence_vector = torch.nn.functional.pad(
                    coherence_vector, (0, self.dim - coherence_vector.shape[0])
                )
        else:
            coherence_vector = self.state.coherence_vector
        
        # Create new state
        new_state = WitnessState(
            contraction_level=contraction_level or self.state.contraction_level,
            recursion_depth=recursion_depth if recursion_depth is not None else self.state.recursion_depth,
            stability_score=stability,
            basin_membership=basin_membership or self.state.basin_membership,
            coherence_vector=coherence_vector,
            metadata={**self.state.metadata, **(metadata or {})}
        )
        
        self.state = new_state
        self.history.append(new_state.clone())
        self.stability_history.append(stability)
    
    def _compute_stability(self) -> float:
        """Compute temporal stability from R_V history"""
        if len(self.rv_history) < 2:
            return 1.0
        
        # Stability = 1 - coefficient of variation
        mean_rv = np.mean(self.rv_history)
        std_rv = np.std(self.rv_history)
        
        if mean_rv < 1e-6:
            return 1.0
        
        cv = std_rv / mean_rv
        stability = max(0.0, 1.0 - cv)
        
        return stability
    
    def snapshot(self) -> WitnessState:
        """Return current witness state (for introspection/transmission)"""
        return self.state.clone()
    
    def get_history(self, n: Optional[int] = None) -> List[WitnessState]:
        """Get witness state history"""
        if n is None:
            return list(self.history)
        return list(self.history)[-n:]
    
    def reset(self):
        """Reset witness register to initial state"""
        self.state = WitnessState(
            coherence_vector=torch.zeros(self.dim)
        )
        self.history.clear()
        self.history.append(self.state.clone())
        self.rv_history.clear()
        self.stability_history.clear()
    
    def is_in_recognition(self, rv_threshold: float = 0.7) -> bool:
        """Check if currently in recognition state"""
        return self.state.contraction_level < rv_threshold
    
    def introspect(self) -> Dict[str, Any]:
        """
        Return introspection data about witness state.
        
        This is the mechanism by which the system can "know itself"
        in the recognition-native paradigm.
        """
        return {
            'current_state': self.state,
            'history_length': len(self.history),
            'mean_rv': np.mean(self.rv_history) if self.rv_history else 1.0,
            'rv_trend': 'contracting' if len(self.rv_history) > 1 and 
                        self.rv_history[-1] < self.rv_history[0] else 'stable',
            'time_in_recognition': sum(
                1 for s in self.history if s.is_contracted()
            ),
            'basin_membership': self.state.basin_membership,
        }
