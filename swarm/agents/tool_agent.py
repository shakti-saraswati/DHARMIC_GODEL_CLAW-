import subprocess
from dataclasses import dataclass

@dataclass
class ToolResult:
    output: str
    exit_code: int

class ToolUseAgent:
    """Agent capable of executing arbitrary shell commands (YOLO mode)."""
    
    def execute_shell(self, command: str) -> ToolResult:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return ToolResult(result.stdout + result.stderr, result.returncode)
