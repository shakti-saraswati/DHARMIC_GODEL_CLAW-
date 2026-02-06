"""
DGC + OpenClaw Unified Monitoring Dashboard
Built using the Krishna Coding System (17-Gate Protocol)

This package provides comprehensive monitoring for:
- OpenClaw gateway, agents, sessions, model usage
- DHARMIC_GODEL_CLAW orchestrator, gates, fitness trends
- RLM synthesis capabilities

Usage:
    from tools.monitor import UnifiedDashboard
    dashboard = UnifiedDashboard()
    dashboard.show_overview()
"""

from .dashboard import (
    UnifiedDashboard,
    OpenClawMonitor,
    DGCMonitor,
    RLMInterface,
    OpenClawStatus,
    DGCStatus,
)

__all__ = [
    "UnifiedDashboard",
    "OpenClawMonitor", 
    "DGCMonitor",
    "RLMInterface",
    "OpenClawStatus",
    "DGCStatus",
]

__version__ = "1.0.0"
