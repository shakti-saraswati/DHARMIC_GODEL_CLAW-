"""
DHARMIC GODEL CLAW - Writer Agent
Implements approved proposals as working code.
"""

from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent, AgentResponse
from ..config import WRITER_CONFIG, SwarmConfig

class WriterAgent(BaseAgent):
    """Agent that implements approved proposals as code."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(WRITER_CONFIG, swarm_config)

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Implement approved proposal as code."""

        proposal = context.get("proposal")
        if not proposal:
            return AgentResponse(
                success=False,
                data={"files": []},
                error="No proposal provided"
            )

        # Step 1: Get implementation plan (what files to create/modify)
        plan_prompt = f"""
## Proposal to Implement

ID: {proposal.get('id')}
Description: {proposal.get('description')}
Implementation Sketch: {proposal.get('implementation_sketch', 'No sketch provided')}

## Project Structure
```
DHARMIC_GODEL_CLAW/
├── swarm/
│   ├── agents/ (base_agent.py, proposer.py, writer.py, tester.py, refiner.py, evolver.py, dharmic_gate.py)
│   ├── config.py
│   ├── residual_stream.py
│   ├── orchestrator.py
│   └── run_swarm.py
├── src/
└── analysis/
```

## Task

Plan the implementation. What files need to be created or modified?

Output ONLY a JSON object (no explanation):
{{
    "files": [
        {{"path": "swarm/utils/example.py", "action": "create", "description": "Brief description"}},
        {{"path": "swarm/config.py", "action": "modify", "description": "What to change"}}
    ],
    "tests_needed": ["test description"],
    "dependencies_added": []
}}
"""

        try:
            # Get plan
            plan_response = self._call_claude([
                {"role": "user", "content": plan_prompt}
            ])
            plan = self._parse_json_response(plan_response)
            planned_files = plan.get("files", [])

            if not planned_files:
                return AgentResponse(
                    success=False,
                    data={"files": []},
                    error="No files planned"
                )

            # Step 2: Generate code for each file
            files_with_content = []
            for file_spec in planned_files[:3]:  # Limit to 3 files per cycle
                code_prompt = f"""
Write the complete Python code for: {file_spec.get('path')}

Purpose: {file_spec.get('description', 'Implementation')}
Action: {file_spec.get('action', 'create')}

Context: This is part of the DHARMIC GODEL CLAW self-improving agent swarm.

Requirements:
- Type hints on all functions
- Brief docstrings
- Error handling
- No placeholders or TODOs
- Keep it minimal and focused

Output ONLY the Python code, no JSON wrapper, no markdown fence.
"""

                code_response = self._call_claude([
                    {"role": "user", "content": code_prompt}
                ])

                # Clean up the code response
                code = code_response.strip()
                if code.startswith("```python"):
                    code = code[9:]
                if code.startswith("```"):
                    code = code[3:]
                if code.endswith("```"):
                    code = code[:-3]
                code = code.strip()

                files_with_content.append({
                    "path": file_spec.get("path"),
                    "action": file_spec.get("action", "create"),
                    "content": code
                })

            return AgentResponse(
                success=True,
                data={
                    "files": files_with_content,
                    "tests_needed": plan.get("tests_needed", []),
                    "dependencies_added": plan.get("dependencies_added", [])
                }
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={"files": []},
                error=str(e)
            )

    def apply_changes(self, files: list, base_path: Path, dry_run: bool = True) -> Dict[str, Any]:
        """Apply file changes to disk."""
        results = {"applied": [], "skipped": [], "errors": []}

        for file_spec in files:
            path = base_path / file_spec["path"]
            action = file_spec["action"]
            content = file_spec.get("content", "")

            try:
                if dry_run:
                    results["skipped"].append({
                        "path": str(path),
                        "action": action,
                        "reason": "dry_run"
                    })
                    continue

                if action == "create":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                    results["applied"].append({"path": str(path), "action": "created"})

                elif action == "modify":
                    if path.exists():
                        path.write_text(content)
                        results["applied"].append({"path": str(path), "action": "modified"})
                    else:
                        results["errors"].append({
                            "path": str(path),
                            "error": "File does not exist for modification"
                        })

                elif action == "delete":
                    if path.exists():
                        path.unlink()
                        results["applied"].append({"path": str(path), "action": "deleted"})
                    else:
                        results["skipped"].append({
                            "path": str(path),
                            "reason": "File already deleted"
                        })

            except Exception as e:
                results["errors"].append({"path": str(path), "error": str(e)})

        return results
