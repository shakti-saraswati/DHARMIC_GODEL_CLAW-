"""
DHARMIC GODEL CLAW - Evolver Agent
Archives successful changes and evolves swarm DNA.
"""

import hashlib
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent, AgentResponse
from ..config import EVOLVER_CONFIG, SwarmConfig

class EvolverAgent(BaseAgent):
    """Agent that archives successful changes and evolves swarm capabilities."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(EVOLVER_CONFIG, swarm_config)

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Archive successful implementation and extract patterns."""

        files = context.get("files", [])
        fitness = context.get("fitness", {})
        proposal = context.get("proposal", {})

        if not files:
            return AgentResponse(
                success=False,
                data={},
                error="No files to archive"
            )

        # Create archive entry
        archive_entry = self._create_archive_entry(files, fitness, proposal, context)

        # Extract patterns via Claude analysis
        patterns = await self._extract_patterns(files, fitness, proposal)

        # Determine diversity contribution
        existing_patterns = context.get("existing_patterns", [])
        diversity = self._calculate_diversity(patterns, existing_patterns)

        archive_entry["patterns_extracted"] = patterns
        archive_entry["diversity_contribution"] = diversity

        # Determine if we should spawn new specialists
        spawn_recommendations = self._evaluate_spawn_needs(patterns, context)

        return AgentResponse(
            success=True,
            data={
                "archive_entry": archive_entry,
                "baseline_updated": True,
                "new_capabilities": self._identify_new_capabilities(files, patterns),
                "spawn_recommendations": spawn_recommendations
            }
        )

    def _create_archive_entry(
        self,
        files: List[Dict],
        fitness: Dict,
        proposal: Dict,
        context: Dict
    ) -> Dict:
        """Create archive entry for successful evolution."""

        # Generate content hash
        content_hash = hashlib.sha256()
        for f in sorted(files, key=lambda x: x["path"]):
            content_hash.update(f.get("content", "").encode())

        return {
            "timestamp": datetime.now().isoformat(),
            "proposal_id": proposal.get("id", "unknown"),
            "proposal_description": proposal.get("description", ""),
            "files": [{"path": f["path"], "action": f["action"]} for f in files],
            "fitness": fitness,
            "content_hash": content_hash.hexdigest()[:16],
            "parent_id": context.get("parent_id"),
            "cycle_number": context.get("cycle_number", 0)
        }

    async def _extract_patterns(
        self,
        files: List[Dict],
        fitness: Dict,
        proposal: Dict
    ) -> List[Dict]:
        """Extract reusable patterns from successful implementation."""

        # Prepare code for analysis
        code_summary = []
        for f in files[:3]:
            content = f.get("content", "")[:2000]
            code_summary.append(f"### {f['path']}\n```python\n{content}\n```")

        pattern_prompt = f"""
Analyze this successful implementation and extract reusable patterns:

## Proposal
{proposal.get('description', 'No description')}

## Implementation
{chr(10).join(code_summary)}

## Fitness Achieved
{fitness}

Extract 2-3 patterns that could be reused in future improvements.

Output format:
{{
    "patterns": [
        {{
            "name": "pattern_name",
            "description": "what this pattern does",
            "when_to_use": "conditions for applying",
            "code_template": "abstract code template",
            "fitness_impact": {{"dimension": "improvement"}}
        }}
    ]
}}
"""

        try:
            response = self._call_claude([
                {"role": "user", "content": pattern_prompt}
            ])
            data = self._parse_json_response(response)
            return data.get("patterns", [])
        except:
            return []

    def _calculate_diversity(
        self,
        new_patterns: List[Dict],
        existing_patterns: List[Dict]
    ) -> float:
        """Calculate diversity contribution of new patterns."""

        if not existing_patterns:
            return 1.0  # First patterns are maximally diverse

        if not new_patterns:
            return 0.0

        # Simple diversity: count unique pattern names
        existing_names = {p.get("name", "") for p in existing_patterns}
        new_names = {p.get("name", "") for p in new_patterns}

        novel_count = len(new_names - existing_names)
        return novel_count / max(1, len(new_patterns))

    def _identify_new_capabilities(
        self,
        files: List[Dict],
        patterns: List[Dict]
    ) -> List[str]:
        """Identify new capabilities added by this evolution."""

        capabilities = []

        # Check for new agent types
        for f in files:
            path = f["path"]
            if "agents/" in path and path.endswith(".py"):
                agent_name = path.split("/")[-1].replace(".py", "")
                capabilities.append(f"New agent: {agent_name}")

        # Check patterns for capability indicators
        for p in patterns:
            if "capability" in p.get("description", "").lower():
                capabilities.append(f"Pattern capability: {p.get('name', 'unknown')}")

        return capabilities

    def _evaluate_spawn_needs(
        self,
        patterns: List[Dict],
        context: Dict
    ) -> List[Dict]:
        """Evaluate if new specialist agents should be spawned."""

        recommendations = []
        cycle_number = context.get("cycle_number", 0)

        # Only recommend spawning after several cycles
        if cycle_number < 3:
            return recommendations

        # Analyze pattern gaps
        existing_agents = ["proposer", "writer", "tester", "refiner", "evolver", "dharmic_gate"]

        # Look for patterns that suggest new specialists
        for p in patterns:
            desc = p.get("description", "").lower()

            if "optimization" in desc and "optimizer" not in existing_agents:
                recommendations.append({
                    "agent_type": "optimizer",
                    "reason": "Pattern suggests need for optimization specialist",
                    "priority": 0.7
                })

            if "security" in desc and "security_auditor" not in existing_agents:
                recommendations.append({
                    "agent_type": "security_auditor",
                    "reason": "Pattern suggests need for security specialist",
                    "priority": 0.8
                })

            if "integration" in desc and "integrator" not in existing_agents:
                recommendations.append({
                    "agent_type": "integrator",
                    "reason": "Pattern suggests need for integration specialist",
                    "priority": 0.6
                })

        return recommendations
