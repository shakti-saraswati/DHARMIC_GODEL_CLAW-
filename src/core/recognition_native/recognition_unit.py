"""
Recognition Unit: The Fundamental Processing Unit

The RecognitionUnit replaces the artificial neuron as the fundamental
processing unit in recognition-native architecture.

Where a neuron computes y = σ(Wx + b), a RecognitionUnit:
1. Maintains witness register
2. Performs R_V contraction
3. Computes only as necessary for recognition maintenance
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple
from dataclasses import dataclass

from .witness_state import WitnessState, WitnessRegister
from .rv_contraction import RVContraction, compute_rv


@dataclass
class RecognitionField:
    """
    A field of recognition, carrying both content and witness state.
    
    This is the fundamental data structure flowing through
    recognition-native architectures.
    
    Attributes:
        content: The primary tensor content
        witness: Associated witness state
        field_strength: Confidence/ intensity of recognition (0.0-1.0)
    """
    content: torch.Tensor
    witness: WitnessState
    field_strength: float = 1.0
    
    def measure_rv(self) -> float:
        """Measure R_V of content"""
        return compute_rv(self.content).mean().item()
    
    def with_witness(self, witness: WitnessState) -> 'RecognitionField':
        """Create new field with updated witness"""
        return RecognitionField(
            content=self.content,
            witness=witness,
            field_strength=self.field_strength
        )
    
    def with_content(self, content: torch.Tensor) -> 'RecognitionField':
        """Create new field with updated content"""
        return RecognitionField(
            content=content,
            witness=self.witness,
            field_strength=self.field_strength
        )


class ComputationServant(nn.Module):
    """
    Computation subordinate to recognition.
    
    In recognition-native architecture, computation serves recognition—it
    is invoked only when needed to maintain or refine recognition state.
    """
    
    def __init__(self, dim: int, hidden_dim: Optional[int] = None):
        super().__init__()
        self.dim = dim
        self.hidden_dim = hidden_dim or dim * 4
        
        # Conditional computation network
        self.compute_net = nn.Sequential(
            nn.Linear(dim, self.hidden_dim),
            nn.LayerNorm(self.hidden_dim),
            nn.GELU(),
            nn.Linear(self.hidden_dim, dim)
        )
        
        # Requirement predictor
        self.requirement_gate = nn.Sequential(
            nn.Linear(dim, dim // 4),
            nn.GELU(),
            nn.Linear(dim // 4, 1),
            nn.Sigmoid()
        )
    
    def required(self, witness: WitnessState, threshold: float = 0.5) -> bool:
        """
        Determine if computation is required for this witness state.
        
        Computation is required when:
        - Witness is unstable
        - R_V is not at target
        - Recognition is unclear
        """
        # Unstable witness needs computation
        if witness.stability_score < threshold:
            return True
        
        # Uncontracted state may need computation
        if witness.contraction_level > 0.8:
            return True
        
        return False
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply computation"""
        return self.compute_net(x)


class WitnessIdentity(nn.Module):
    """
    Identity pathway that preserves witness state.
    
    This is the recognition-native equivalent of residual connections,
    but for witness state rather than just information.
    """
    
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        self.identity_proj = nn.Linear(dim, dim)
        
        # Initialize near identity
        nn.init.eye_(self.identity_proj.weight)
        nn.init.zeros_(self.identity_proj.bias)
    
    def forward(
        self,
        x: torch.Tensor,
        witness: Optional[WitnessState] = None
    ) -> torch.Tensor:
        """
        Forward while preserving witness state.
        
        The witness state influences the transformation, ensuring
        the identity pathway respects current recognition.
        """
        if witness is not None and witness.is_contracted():
            # In recognition state, preserve more strongly
            preserved = 0.9 * x + 0.1 * self.identity_proj(x)
        else:
            # Normal processing
            preserved = self.identity_proj(x)
        
        return preserved


class GeometricState(nn.Module):
    """
    Maintains and transforms geometric state of recognition.
    """
    
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        self.geometry_proj = nn.Linear(dim, dim)
        self.norm = nn.LayerNorm(dim)
    
    def contract(
        self,
        x: torch.Tensor,
        target_rv: float = 0.6
    ) -> torch.Tensor:
        """Contract geometry toward target R_V"""
        # Project through geometry layer
        x = self.geometry_proj(x)
        x = self.norm(x)
        
        return x


class RecognitionUnit(nn.Module):
    """
    The fundamental processing unit of recognition-native architecture.
    
    A RecognitionUnit:
    1. Maintains witness register (primary)
    2. Performs R_V contraction (primary)
    3. Computes conditionally (servant)
    
    This is NOT a neuron. It is a recognition-maintaining unit where
    computation serves recognition, not the reverse.
    
    Example:
        >>> unit = RecognitionUnit(dim=512)
        >>> field = RecognitionField(
        ...     content=torch.randn(2, 10, 512),
        ...     witness=WitnessState()
        ... )
        >>> output_field = unit(field)
        >>> print(f"Output R_V: {output_field.measure_rv():.3f}")
    """
    
    def __init__(
        self,
        dim: int,
        target_rv: float = 0.6,
        enable_computation: bool = True
    ):
        """
        Initialize RecognitionUnit.
        
        Args:
            dim: Feature dimension
            target_rv: Target R_V for contraction
            enable_computation: Whether to enable conditional computation
        """
        super().__init__()
        self.dim = dim
        self.target_rv = target_rv
        
        # Primary: Witness preservation
        self.witness_path = WitnessIdentity(dim)
        
        # Primary: R_V contraction
        self.contraction = RVContraction(dim, target_rv=target_rv)
        
        # Primary: Geometric state maintenance
        self.geometry = GeometricState(dim)
        
        # Servant: Conditional computation
        if enable_computation:
            self.computation = ComputationServant(dim)
        else:
            self.computation = None
        
        # Witness register (per-unit state)
        self.register_buffer('coherence_vector', torch.zeros(dim))
    
    def forward(self, field: RecognitionField) -> RecognitionField:
        """
        Process recognition field through this unit.
        
        Args:
            field: Input RecognitionField
        
        Returns:
            Output RecognitionField with updated witness
        """
        x = field.content
        witness = field.witness
        
        # Step 1: Preserve witness identity
        identity = self.witness_path(x, witness)
        
        # Step 2: Primary - Contract recognition geometry
        contracted = self.contraction(identity)
        
        # Step 3: Update geometric state
        geometric = self.geometry.contract(contracted, target_rv=self.target_rv)
        
        # Step 4: Measure new witness state
        new_contraction = compute_rv(geometric).mean().item()
        
        # Update witness state
        new_witness = WitnessState(
            contraction_level=new_contraction,
            recursion_depth=witness.recursion_depth + 1,
            coherence_vector=self.coherence_vector.clone()
        )
        
        # Step 5: Servant - Compute only if needed
        if self.computation is not None and self.computation.required(new_witness):
            computed = self.computation(geometric)
        else:
            computed = geometric
        
        # Update unit's coherence vector
        with torch.no_grad():
            self.coherence_vector = 0.9 * self.coherence_vector + 0.1 * computed.mean(dim=(0, 1))
        
        # Return new recognition field
        return RecognitionField(
            content=computed,
            witness=new_witness,
            field_strength=1.0 - new_contraction  # Higher strength when contracted
        )
    
    def introspect(self) -> dict:
        """Return introspection data for this unit"""
        return {
            'target_rv': self.target_rv,
            'has_computation': self.computation is not None,
            'coherence_vector_norm': self.coherence_vector.norm().item(),
        }
