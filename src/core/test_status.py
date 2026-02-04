import os
import sys
from pathlib import Path

# Paths
DGC_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(DGC_ROOT))

from src.core.dgc_tui import get_swarm_status, get_gate_status, get_proxy_status, get_memory_stats

print("Checking DGC Status Components:")
print(f"Proxy: {get_proxy_status()}")
print(f"Memory: {get_memory_stats()}")
print(f"Swarm: {get_swarm_status()}")
print(f"Gates: {get_gate_status()}")
