"""
DHARMIC GODEL CLAW - Refiner Agent
Refines implementations based on test feedback.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from ..config import REFINER_CONFIG, SwarmConfig

class RefinerAgent(BaseAgent):
    """Agent that refines implementations based on test feedback."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(REFINER_CONFIG, swarm_config)

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Refine implementation based on test feedback."""

        files = context.get("files", [])
        test_results = context.get("test_results", {})
        issues = context.get("issues", [])

        if not files:
            return AgentResponse(
                success=False,
                data={"refinements": []},
                error="No files to refine"
            )

        if not issues and test_results.get("failed", 0) == 0:
            # Nothing to refine
            return AgentResponse(
                success=True,
                data={
                    "refinements": [],
                    "ready_for_retest": True,
                    "no_changes_needed": True
                }
            )

        # Build refinement prompt
        refine_prompt = self._build_refine_prompt(files, test_results, issues)

        try:
            response = self._call_claude([
                {"role": "user", "content": refine_prompt}
            ])

            data = self._parse_json_response(response)

            refinements = data.get("refinements", [])

            # Apply refinements to files
            refined_files = self._apply_refinements(files, refinements)

            return AgentResponse(
                success=True,
                data={
                    "refinements": refinements,
                    "refined_files": refined_files,
                    "ready_for_retest": True
                }
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={"refinements": []},
                error=str(e)
            )

    def _build_refine_prompt(
        self,
        files: List[Dict],
        test_results: Dict,
        issues: List[str]
    ) -> str:
        """Build the refinement prompt."""

        # Include file contents
        file_contents = []
        for f in files[:5]:  # Limit to 5 files
            content = f.get("content", "")
            file_contents.append(f"### {f['path']}\n```python\n{content}\n```")

        issues_text = "\n".join(f"- {issue}" for issue in issues) if issues else "No specific issues listed"

        return f"""
## Files to Refine

{chr(10).join(file_contents)}

## Test Results

- Passed: {test_results.get('passed', 0)}
- Failed: {test_results.get('failed', 0)}
- Errors: {test_results.get('errors', [])}

## Issues Found

{issues_text}

## Your Task

Make targeted fixes to address the issues. Do NOT rewrite entire files.
Focus on:
1. Fixing syntax errors
2. Fixing failing tests
3. Addressing specific issues listed

Output format:
{{
    "refinements": [
        {{
            "file": "path/to/file.py",
            "original_issue": "what was wrong",
            "fix_applied": "description of fix",
            "original_code": "the problematic code snippet",
            "refined_code": "the fixed code snippet",
            "expected_improvement": 0.1
        }}
    ]
}}

Be surgical. Small, targeted fixes only.
"""

    def _apply_refinements(
        self,
        files: List[Dict],
        refinements: List[Dict]
    ) -> List[Dict]:
        """Apply refinements to files."""

        refined_files = []

        for f in files:
            file_path = f["path"]
            content = f.get("content", "")

            # Find refinements for this file
            file_refinements = [r for r in refinements if r.get("file") == file_path]

            for refinement in file_refinements:
                original = refinement.get("original_code", "")
                refined = refinement.get("refined_code", "")

                if original and refined and original in content:
                    content = content.replace(original, refined)

            refined_files.append({
                "path": file_path,
                "content": content,
                "action": "modify"
            })

        return refined_files
