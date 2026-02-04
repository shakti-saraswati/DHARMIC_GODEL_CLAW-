"""
Dharmic Agent Healthcheck Runner

Wraps scripts/devops/health_check.sh so the core agent (and web dashboard)
can run a unified health check and return structured output.
"""

from pathlib import Path
from typing import Dict, Any
import subprocess


def run_healthcheck(timeout: int = 60) -> Dict[str, Any]:
    """Run the project health check script and return structured output."""
    script_path = Path(__file__).parent.parent.parent / "scripts" / "devops" / "health_check.sh"
    if not script_path.exists():
        return {
            "ok": False,
            "code": 127,
            "error": f"Missing health check script at {script_path}",
        }

    try:
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "code": 124,
            "error": f"Health check timed out after {timeout}s",
        }
    except Exception as exc:
        return {
            "ok": False,
            "code": 1,
            "error": f"Health check failed: {exc}",
        }

    return {
        "ok": result.returncode == 0,
        "code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
