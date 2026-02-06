"""Status utilities for Cosmic Krishna Coder integration."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

DGC_ROOT = Path(__file__).resolve().parent.parent.parent.parent

QUALITY_RUBRIC = DGC_ROOT / "docs" / "QUALITY_RUBRIC.md"
TOP50_REFS = DGC_ROOT / "docs" / "TOP_50_QUALITY_REFERENCES.md"
GATE_ALIAS = DGC_ROOT / "swarm" / "CosmicChrisnaCoder_Gate_Runner.py"
GATES_YAML = DGC_ROOT / "swarm" / "gates.yaml"


def _ml_overlay_enabled() -> bool:
    if not GATES_YAML.exists() or not yaml:
        return False
    try:
        data = yaml.safe_load(GATES_YAML.read_text()) or {}
        overlay = data.get("ml_overlay", {})
        return bool(overlay.get("enabled"))
    except Exception:
        return False


def get_status() -> Dict[str, Any]:
    """Return a snapshot of Cosmic Krishna Coder integration status."""
    return {
        "quality_rubric": QUALITY_RUBRIC.exists(),
        "top50_references": TOP50_REFS.exists(),
        "gate_alias": GATE_ALIAS.exists(),
        "ml_overlay": _ml_overlay_enabled(),
        "paths": {
            "quality_rubric": str(QUALITY_RUBRIC),
            "top50_references": str(TOP50_REFS),
            "gate_alias": str(GATE_ALIAS),
        },
    }


def status_summary() -> str:
    """Human-readable one-line summary."""
    st = get_status()
    parts = []
    parts.append("rubric" if st["quality_rubric"] else "rubric:missing")
    parts.append("top50" if st["top50_references"] else "top50:missing")
    parts.append("gate" if st["gate_alias"] else "gate:missing")
    parts.append("ml" if st["ml_overlay"] else "ml:off")
    return ", ".join(parts)
