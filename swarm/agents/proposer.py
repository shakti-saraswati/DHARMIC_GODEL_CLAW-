"""
DHARMIC GODEL CLAW - Proposer Agent
Generates improvement proposals for the swarm.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from ..config import PROPOSER_CONFIG, SwarmConfig

class ProposerAgent(BaseAgent):
    """Agent that proposes improvements to swarm capabilities."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(PROPOSER_CONFIG, swarm_config)

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Generate improvement proposals."""

        # Build the prompt
        context_msg = self._build_context_message(context)

        # Add swarm state analysis
        analysis_prompt = f"""
{context_msg}

## Your Task
Analyze the current swarm state and generate 2-3 concrete improvement proposals.

Focus areas for proposals:
1. Capability gaps - what can't the swarm do that it should?
2. Efficiency improvements - what takes too long or uses too many resources?
3. Dharmic alignment - how can we better align with Akram Vignan principles?
4. Safety enhancements - what could go wrong and how do we prevent it?

Current swarm capabilities:
- Proposer (you) - generates improvement proposals
- Writer - implements approved proposals as code
- Tester - validates implementations
- Refiner - fixes issues found in testing
- Evolver - archives successful changes
- Dharmic Gate - evaluates ethical alignment

Archive patterns available:
{context.get('patterns', ['No patterns yet - this is the first cycle'])}

Generate proposals that build on what exists, not rebuild from scratch.
"""

        try:
            response = self._call_claude([
                {"role": "user", "content": analysis_prompt}
            ])

            data = self._parse_json_response(response)

            # Validate proposals
            proposals = data.get("proposals", [])
            valid_proposals = []

            for prop in proposals:
                if all(k in prop for k in ["id", "description", "expected_benefit", "difficulty", "dharmic_alignment"]):
                    valid_proposals.append(prop)

            if not valid_proposals:
                return AgentResponse(
                    success=False,
                    data={"proposals": []},
                    error="No valid proposals generated"
                )

            return AgentResponse(
                success=True,
                data={"proposals": valid_proposals}
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={"proposals": []},
                error=str(e)
            )

    def rank_proposals(self, proposals: List[Dict]) -> List[Dict]:
        """Rank proposals by expected value (benefit / difficulty)."""
        def score(p):
            benefit = p.get("expected_benefit", 0)
            difficulty = p.get("difficulty", 5)
            dharmic = p.get("dharmic_alignment", 0.5)
            # Expected value weighted by dharmic alignment
            return (benefit / difficulty) * dharmic

        return sorted(proposals, key=score, reverse=True)
