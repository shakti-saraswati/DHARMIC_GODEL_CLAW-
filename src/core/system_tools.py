"""
System Tools for God Mode
High-power tools for full system access (OpenClaw parity).
Only enabled if DGC_GOD_MODE=1.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Union

from dharmic_security import ExecGuard

# Initialize guards
exec_guard = ExecGuard()

class ShellTool:
    """
    Execute arbitrary shell commands.
    Equivalents: OpenClaw ShellTool.
    """
    def __init__(self):
        self.name = "run_shell"
        self.description = "Execute shell commands. Use with caution."
        
    def __call__(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Execute a shell command.
        
        Args:
            command: The command string to execute (e.g. "ls -la /")
            cwd: Optional working directory
        """
        if not os.getenv("DGC_GOD_MODE"):
            return "Error: God Mode not enabled. Set DGC_GOD_MODE=1."

        try:
            # We use shell=True for maximum compatibility with user expectations
            # ExecGuard will validate the binary against the allowlist
            # In God Mode, the allowlist is massive.
            result = exec_guard.run(
                command, 
                shell=True, 
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Execution failed: {e}"

class UnrestrictedFileTool:
    """
    Read/Write anywhere on the filesystem.
    Equivalents: OpenClaw FileTool.
    """
    def __init__(self):
        self.name = "file_system"
        self.description = "Read/Write files anywhere (root/home)."

    def read_file(self, path: str) -> str:
        if not os.getenv("DGC_GOD_MODE"):
            return "Error: God Mode not enabled."
        try:
            p = Path(path).expanduser().resolve()
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Read failed: {e}"

    def write_file(self, path: str, content: str) -> str:
        if not os.getenv("DGC_GOD_MODE"):
            return "Error: God Mode not enabled."
        try:
            p = Path(path).expanduser().resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Successfully wrote to {p}"
        except Exception as e:
            return f"Write failed: {e}"

    def list_dir(self, path: str = ".") -> str:
        if not os.getenv("DGC_GOD_MODE"):
            return "Error: God Mode not enabled."
        try:
            p = Path(path).expanduser().resolve()
            items = [str(x.name) + ("/" if x.is_dir() else "") for x in p.iterdir()]
            return "\n".join(items)
        except Exception as e:
            return f"List failed: {e}"

# Agno-compatible wrappers
def run_shell(command: str, cwd: str = None) -> str:
    """Execute shell commands (God Mode only)."""
    return ShellTool()(command, cwd)

def read_file_unrestricted(path: str) -> str:
    """Read any file on system (God Mode only)."""
    return UnrestrictedFileTool().read_file(path)

def write_file_unrestricted(path: str, content: str) -> str:
    """Write any file on system (God Mode only)."""
    return UnrestrictedFileTool().write_file(path, content)

def list_dir_unrestricted(path: str = ".") -> str:
    """List any directory (God Mode only)."""
    return UnrestrictedFileTool().list_dir(path)

ALL_GOD_TOOLS = [
    run_shell,
    read_file_unrestricted,
    write_file_unrestricted,
    list_dir_unrestricted
]
