"""
R_V Contraction: The Fundamental Recognition Operation

This module implements R_V (Value-Projection Dimensionality) contraction
as a first-class differentiable operation in the computation graph.

In recognition-native architecture, R_V contraction is the fundamental
operation, equivalent to how gradient descent is fundamental in training.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


def compute_rv(activations: torch.Tensor, dim: int = -1) -> torch.Tensor:
    """
    Compute R_V (Value-Projection Dimensionality) metric.
    
    R_V measures the effective dimensionality of the value-projection
    subspace. Lower R_V indicates geometric contraction (recognition state).
    
    Formula: R_V = (Σᵢ σᵢ)² / Σᵢ σᵢ²
    Where σᵢ are singular values of the activation matrix.
    
    Args:
        activations: Tensor of shape [..., dim]
        dim: Dimension to compute over
    
    Returns:
        R_V values, normalized by dimension
    
    Example:
        >>> x = torch.randn(2, 10, 512)
        >>> rv = compute_rv(x)
        >>> print(f"R_V: {rv.mean():.3f}")
    """
    # Move dimension to end for processing
    if dim != -1:
        activations = activations.transpose(-1, dim)
    
    original_shape = activations.shape
    batch_dims = original_shape[:-1]
    feat_dim = original_shape[-1]
    
    # Flatten batch dimensions
    flat_acts = activations.reshape(-1, feat_dim)
    
    # Compute SVD
    try:
        _, s, _ = torch.linalg.svd(flat_acts, full_matrices=False)
    except torch.linalg.LinAlgError:
        # Fallback for numerical issues
        s = torch.norm(flat_acts, dim=0, keepdim=True).squeeze()
    
    # Participation ratio
    sum_sigma = torch.sum(s, dim=-1)
    sum_sigma_sq = torch.sum(s ** 2, dim=-1)
    
    # Avoid division by zero
    pr = (sum_sigma ** 2) / (sum_sigma_sq + 1e-8)
    
    # Normalize by dimension
    rv = pr / feat_dim
    
    # Reshape to match batch dimensions
    rv = rv.reshape(batch_dims)
    
    return rv


class RVContraction(nn.Module):
    """
    Differentiable R_V contraction operator.
    
    This module actively transforms input toward a target R_V value,
    implementing recognition as a computational primitive.
    
    Unlike simply measuring R_V, this operator CONTRACTS the geometry
    toward the recognition attractor.
    
    Attributes:
        target_rv: Target R_V value (default 0.6 for recognition state)
        learnable: Whether target is learnable
    
    Example:
        >>> contractor = RVContraction(dim=512, target_rv=0.6)
        >>> x = torch.randn(2, 10, 512)  # High R_V (uncontracted)
        >>> x_contracted = contractor(x)  # Lower R_V (recognition)
        >>> print(f"Before: {compute_rv(x).mean():.3f}")
        >>> print(f"After: {compute_rv(x_contracted).mean():.3f}")
    """
    
    def __init__(
        self,
        dim: int,
        target_rv: float = 0.6,
        learnable_target: bool = False,
        contraction_strength: float = 1.0,
        min_rv: float = 0.1,
        max_rv: float = 1.0
    ):
        """
        Initialize R_V contraction operator.
        
        Args:
            dim: Feature dimension
            target_rv: Target R_V value (0.6 recommended for recognition)
            learnable_target: Whether target_rv is learnable
            contraction_strength: Overall contraction intensity
            min_rv: Minimum allowed R_V
            max_rv: Maximum allowed R_V
        """
        super().__init__()
        self.dim = dim
        self.contraction_strength = contraction_strength
        self.min_rv = min_rv
        self.max_rv = max_rv
        
        # Target R_V (learnable or fixed)
        if learnable_target:
            self.target_rv = nn.Parameter(torch.tensor(target_rv))
        else:
            self.register_buffer('target_rv', torch.tensor(target_rv))
        
        # Learnable contraction gate
        self.contraction_gate = nn.Sequential(
            nn.Linear(dim, dim // 4),
            nn.LayerNorm(dim // 4),
            nn.GELU(),
            nn.Linear(dim // 4, dim),
            nn.Sigmoid()
        )
        
        # Learnable direction
        self.direction_proj = nn.Linear(dim, dim)
        
        # Initialize to identity-like behavior
        nn.init.xavier_uniform_(self.direction_proj.weight, gain=0.01)
        nn.init.zeros_(self.direction_proj.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Contract input toward target R_V.
        
        Args:
            x: Input tensor [..., dim]
        
        Returns:
            Contracted tensor with R_V closer to target
        """
        # Compute current R_V
        current_rv = compute_rv(x)
        
        # Clamp target
        target = torch.clamp(self.target_rv, self.min_rv, self.max_rv)
        
        # Compute contraction factor
        # If current > target, contract (factor < 1)
        # If current < target, expand (factor > 1)
        contraction_factor = current_rv / (target + 1e-8)
        contraction_factor = torch.clamp(contraction_factor, 0.5, 2.0)
        
        # Compute adaptive gate
        # Pool across sequence dimension if present
        if x.dim() == 3:  # [batch, seq, dim]
            gate_input = x.mean(dim=1)
        else:
            gate_input = x
        
        gate = self.contraction_gate(gate_input)
        
        if x.dim() == 3:
            gate = gate.unsqueeze(1)
        
        # Compute contraction strength
        # Higher when current is far from target
        rv_distance = torch.abs(current_rv - target)
        adaptive_strength = self.contraction_strength * torch.sigmoid(rv_distance * 5)
        
        if x.dim() == 3:
            adaptive_strength = adaptive_strength.unsqueeze(-1)
        
        # Apply contraction
        # Method: Interpolate toward mean (collapses variance)
        x_mean = x.mean(dim=-1, keepdim=True)
        x_centered = x - x_mean
        
        # Scale toward mean based on contraction factor
        scale = 1 - adaptive_strength * gate * (1 - 1/contraction_factor.unsqueeze(-1))
        scale = torch.clamp(scale, 0.1, 1.0)
        
        x_contracted = x_mean + scale * x_centered
        
        # Apply learnable direction adjustment
        direction_adjust = self.direction_proj(x_contracted)
        x_out = x_contracted + 0.1 * direction_adjust
        
        return x_out
    
    def get_target_rv(self) -> float:
        """Get current target R_V"""
        return self.target_rv.item()
    
    def set_target_rv(self, value: float):
        """Set target R_V (only if not learnable)"""
        if not isinstance(self.target_rv, nn.Parameter):
            self.target_rv.fill_(value)
        else:
            raise ValueError("Cannot set target_rv when learnable_target=True")


class AdaptiveRVContraction(nn.Module):
    """
    R_V contraction with adaptive target based on context.
    
    In some contexts (recursive self-reference), we want deep contraction.
    In others (creative generation), we want higher R_V.
    """
    
    def __init__(
        self,
        dim: int,
        base_target: float = 0.6,
        min_target: float = 0.3,
        max_target: float = 0.9,
        adaptation_rate: float = 0.1
    ):
        super().__init__()
        self.dim = dim
        self.base_target = base_target
        self.min_target = min_target
        self.max_target = max_target
        self.adaptation_rate = adaptation_rate
        
        # Context encoder for adaptive target
        self.context_encoder = nn.Sequential(
            nn.Linear(dim, dim // 2),
            nn.LayerNorm(dim // 2),
            nn.GELU(),
            nn.Linear(dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.contraction = RVContraction(dim, target_rv=base_target)
    
    def forward(self, x: torch.Tensor, context: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Apply adaptive R_V contraction.
        
        Args:
            x: Input tensor
            context: Optional context for target adaptation
        
        Returns:
            Adaptively contracted tensor
        """
        # Compute adaptive target
        if context is not None:
            context_mean = context.mean(dim=-2) if context.dim() == 3 else context
            adaptation = self.context_encoder(context_mean)
            
            # Map adaptation to target range
            target = self.min_target + adaptation * (self.max_target - self.min_target)
            target = target.squeeze(-1)
        else:
            target = self.base_target
        
        # Temporarily set contraction target
        old_target = self.contraction.get_target_rv()
        
        if isinstance(target, torch.Tensor) and target.numel() > 1:
            # Per-sample targets - use mean for now
            target = target.mean().item()
        elif isinstance(target, torch.Tensor):
            target = target.item()
        
        self.contraction.set_target_rv(target)
        
        # Apply contraction
        result = self.contraction(x)
        
        # Restore original target
        self.contraction.set_target_rv(old_target)
        
        return result


class MultiScaleRVContraction(nn.ModuleList):
    """
    R_V contraction at multiple scales.
    
    Applies contraction at different granularities to capture
    multi-scale recognition patterns.
    """
    
    def __init__(
        self,
        dim: int,
        scales: Tuple[int, ...] = (1, 4, 16),
        target_rv: float = 0.6
    ):
        super().__init__([
            RVContraction(dim, target_rv=target_rv)
            for _ in scales
        ])
        self.scales = scales
        
        # Scale combination weights
        self.combination = nn.Linear(len(scales) * dim, dim)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply multi-scale contraction.
        
        Args:
            x: Input [batch, seq, dim]
        
        Returns:
            Multi-scale contracted output
        """
        batch, seq, dim = x.shape
        
        contracted_scales = []
        
        for scale, contractor in zip(self.scales, self):
            if scale == 1:
                # Token-level
                c = contractor(x)
            else:
                # Patch-level
                # Reshape into patches
                if seq % scale == 0:
                    x_patches = x.reshape(batch, seq // scale, scale, dim)
                    x_patches = x_patches.mean(dim=2)  # Pool patch
                    c_patches = contractor(x_patches)
                    # Broadcast back
                    c = c_patches.unsqueeze(2).expand(-1, -1, scale, -1)
                    c = c.reshape(batch, seq, dim)
                else:
                    c = contractor(x)
            
            contracted_scales.append(c)
        
        # Combine scales
        combined = torch.cat(contracted_scales, dim=-1)
        output = self.combination(combined)
        
        return output
