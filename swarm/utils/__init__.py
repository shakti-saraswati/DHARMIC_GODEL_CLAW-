"""
Utilities package for the DHARMIC GODEL CLAW self-improving agent swarm.

This package provides common utilities and helper functions used across
the swarm system.
"""

from typing import Any, Dict, List, Optional, Union

__version__ = "0.1.0"
__all__ = []

# Package-level constants
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3

def __getattr__(name: str) -> Any:
    """
    Handle dynamic attribute access for lazy loading of submodules.
    
    Args:
        name: The attribute name being accessed
        
    Returns:
        The requested attribute
        
    Raises:
        AttributeError: If the attribute doesn't exist
    """
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")