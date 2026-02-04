"""
Recognition Layer: Network Architecture

This module implements RecognitionLayer (replacing transformer layers)
and RecognitionStack (multi-layer architectures) where recognition
operations are primary and attention/computation are servants.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, List, Dict

from .witness_state import WitnessState, WitnessRegister
from .rv_contraction import RVContraction, compute_rv
from .recognition_unit import RecognitionField, ComputationServant, WitnessIdentity


class ConditionalAttention(nn.Module):
    """
    Attention mechanism subordinate to recognition state.
    
    In recognition-native architecture, attention serves recognition—it
    is invoked conditionally based on witness state.
    """
    
    def __init__(self, dim: int, num_heads: int = 8):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        
        assert self.head_dim * num_heads == dim, "dim must be divisible by num_heads"
        
        # Q, K, V projections
        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        
        # Requirement predictor based on witness
        self.requirement_score = nn.Sequential(
            nn.Linear(dim, dim // 4),
            nn.GELU(),
            nn.Linear(dim // 4, 1),
            nn.Sigmoid()
        )
    
    def required(self, witness: WitnessState, threshold: float = 0.5) -> bool:
        """
        Determine if attention is required.
        
        Deep recognition (low R_V) requires less attention manipulation.
        Unclear recognition requires more attention.
        """
        # Deep recognition → minimal attention
        if witness.contraction_level < 0.5:
            return False
        
        # Shallow recognition → attention helps
        if witness.contraction_level > 0.8:
            return True
        
        # Medium → sometimes
        return witness.stability_score < threshold
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Apply conditional attention"""
        batch, seq, dim = x.shape
        
        # Project to Q, K, V
        q = self.q_proj(x).view(batch, seq, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch, seq, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch, seq, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, v)
        
        # Reshape and project
        out = out.transpose(1, 2).contiguous().view(batch, seq, dim)
        return self.out_proj(out)


class RecognitionLayer(nn.Module):
    """
    A layer where recognition operations are primary.
    
    This replaces the transformer layer in recognition-native architecture.
    
    Structure:
    1. Witness preservation (residual identity)
    2. R_V contraction (primary operation)
    3. Attention/computation (servant, conditional)
    
    Example:
        >>> layer = RecognitionLayer(dim=512, num_heads=8)
        >>> x = torch.randn(2, 10, 512)
        >>> witness = WitnessState()
        >>> output, new_witness = layer(x, witness)
        >>> print(f"Output R_V: {compute_rv(output).mean():.3f}")
    """
    
    def __init__(
        self,
        dim: int,
        num_heads: int = 8,
        ffn_dim: Optional[int] = None,
        dropout: float = 0.1,
        target_rv: float = 0.6
    ):
        """
        Initialize RecognitionLayer.
        
        Args:
            dim: Feature dimension
            num_heads: Number of attention heads (for servant attention)
            ffn_dim: Feedforward dimension
            dropout: Dropout rate
            target_rv: Target R_V for contraction
        """
        super().__init__()
        self.dim = dim
        self.target_rv = target_rv
        
        # Primary: Witness preservation
        self.witness_path = WitnessIdentity(dim)
        
        # Primary: R_V contraction
        self.contraction = RVContraction(dim, target_rv=target_rv)
        self.contraction_norm = nn.LayerNorm(dim)
        
        # Servant: Conditional attention
        self.attention = ConditionalAttention(dim, num_heads)
        self.attention_norm = nn.LayerNorm(dim)
        
        # Servant: Conditional FFN
        ffn_dim = ffn_dim or dim * 4
        self.ffn = nn.Sequential(
            nn.Linear(dim, ffn_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ffn_dim, dim),
            nn.Dropout(dropout)
        )
        self.ffn_norm = nn.LayerNorm(dim)
        
        # Gate for conditional computation
        self.use_attention_gate = nn.Parameter(torch.tensor(1.0))
        self.use_ffn_gate = nn.Parameter(torch.tensor(1.0))
    
    def forward(
        self,
        x: torch.Tensor,
        witness: Optional[WitnessState] = None,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, WitnessState]:
        """
        Forward pass with witness state threading.
        
        Args:
            x: Input tensor [batch, seq, dim]
            witness: Optional incoming witness state
            mask: Optional attention mask
        
        Returns:
            (output_tensor, updated_witness_state)
        """
        if witness is None:
            witness = WitnessState()
        
        # Step 1: Preserve witness identity
        identity = self.witness_path(x, witness)
        
        # Step 2: Primary - R_V contraction
        contracted = self.contraction(identity)
        contracted = self.contraction_norm(contracted + identity)  # Residual
        
        # Step 3: Measure witness state
        new_contraction = compute_rv(contracted).mean().item()
        
        new_witness = WitnessState(
            contraction_level=new_contraction,
            recursion_depth=witness.recursion_depth + 1,
            stability_score=witness.stability_score,  # Updated later
            coherence_vector=witness.coherence_vector,
            layer_trajectory={**witness.layer_trajectory, witness.recursion_depth: witness}
        )
        
        # Step 4: Servant - Conditional attention
        if self.attention.required(new_witness) and self.use_attention_gate > 0.5:
            attended = self.attention(contracted, mask)
            attended = self.attention_norm(attended + contracted)
        else:
            attended = contracted
        
        # Step 5: Servant - Conditional FFN
        # FFN needed when recognition unclear
        ffn_required = new_witness.contraction_level > 0.7
        
        if ffn_required and self.use_ffn_gate > 0.5:
            output = self.ffn(attended)
            output = self.ffn_norm(output + attended)
        else:
            output = attended
        
        # Update stability based on output
        final_rv = compute_rv(output).mean().item()
        new_witness.contraction_level = final_rv
        
        return output, new_witness
    
    def get_stats(self) -> Dict[str, float]:
        """Get layer statistics"""
        return {
            'target_rv': self.target_rv,
            'attention_gate': self.use_attention_gate.item(),
            'ffn_gate': self.use_ffn_gate.item(),
        }


class WitnessAggregator(nn.Module):
    """
    Aggregates witness states across layers.
    
    Combines witness trajectory into unified state.
    """
    
    def __init__(self, method: str = 'mean'):
        super().__init__()
        self.method = method
    
    def forward(self, witness: WitnessState) -> WitnessState:
        """
        Aggregate witness trajectory.
        
        Args:
            witness: Witness with layer_trajectory
        
        Returns:
            Aggregated witness state
        """
        if not witness.layer_trajectory:
            return witness
        
        trajectory = list(witness.layer_trajectory.values())
        
        if self.method == 'mean':
            # Average contraction across layers
            avg_contraction = sum(s.contraction_level for s in trajectory) / len(trajectory)
            
            # Use deepest recursion
            max_depth = max(s.recursion_depth for s in trajectory)
            
            # Average stability
            avg_stability = sum(s.stability_score for s in trajectory) / len(trajectory)
            
            return WitnessState(
                contraction_level=avg_contraction,
                recursion_depth=max_depth,
                stability_score=avg_stability,
                basin_membership=witness.basin_membership,
                coherence_vector=witness.coherence_vector,
                layer_trajectory=witness.layer_trajectory
            )
        
        elif self.method == 'final':
            # Use final state
            final = max(trajectory, key=lambda s: s.recursion_depth)
            return final
        
        else:
            return witness


class RecognitionStack(nn.Module):
    """
    Stack of recognition layers with witness state propagation.
    
    This replaces the transformer encoder/decoder in recognition-native
    architectures.
    """
    
    def __init__(
        self,
        num_layers: int,
        dim: int,
        num_heads: int = 8,
        target_rv: float = 0.6,
        progressive_contraction: bool = True
    ):
        """
        Initialize RecognitionStack.
        
        Args:
            num_layers: Number of recognition layers
            dim: Feature dimension
            num_heads: Attention heads per layer
            target_rv: Target R_V (progressively decreases if progressive=True)
            progressive_contraction: Whether to decrease target R_V per layer
        """
        super().__init__()
        self.num_layers = num_layers
        self.dim = dim
        
        # Create layers with progressive targets
        if progressive_contraction:
            # Start high, end low (deep recognition)
            targets = torch.linspace(0.9, target_rv, num_layers)
        else:
            targets = torch.full((num_layers,), target_rv)
        
        self.layers = nn.ModuleList([
            RecognitionLayer(dim, num_heads, target_rv=targets[i].item())
            for i in range(num_layers)
        ])
        
        # Witness aggregation
        self.witness_aggregator = WitnessAggregator()
        
        # Final normalization
        self.norm = nn.LayerNorm(dim)
    
    def forward(
        self,
        x: torch.Tensor,
        initial_witness: Optional[WitnessState] = None,
        mask: Optional[torch.Tensor] = None,
        return_all_witnesses: bool = False
    ) -> Tuple[torch.Tensor, WitnessState, Optional[List[WitnessState]]]:
        """
        Process through recognition stack.
        
        Args:
            x: Input [batch, seq, dim]
            initial_witness: Starting witness state
            mask: Optional attention mask
            return_all_witnesses: Whether to return per-layer witness states
        
        Returns:
            (output, final_witness, optional_all_witnesses)
        """
        witness = initial_witness or WitnessState()
        all_witnesses = [] if return_all_witnesses else None
        
        for i, layer in enumerate(self.layers):
            x, witness = layer(x, witness, mask)
            
            if return_all_witnesses:
                all_witnesses.append(witness.clone())
        
        # Aggregate final witness
        final_witness = self.witness_aggregator(witness)
        
        # Final normalization
        x = self.norm(x)
        
        return x, final_witness, all_witnesses
    
    def introspect(self) -> Dict[str, any]:
        """Return stack introspection data"""
        return {
            'num_layers': self.num_layers,
            'dim': self.dim,
            'layer_targets': [layer.target_rv for layer in self.layers],
            'mean_target': sum(layer.target_rv for layer in self.layers) / self.num_layers,
        }
