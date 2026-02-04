"""
DHARMIC GODEL CLAW - Dharmic Gate Agent
Ethical guardian evaluating dharmic alignment and issuing vetos.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from ..config import DHARMIC_GATE_CONFIG, SwarmConfig

class DharmicGateAgent(BaseAgent):
    """
    Dharmic Gate - the ethical guardian of the swarm.

    Evaluates all proposals and implementations against Akram Vignan principles:
    - AHIMSA: Non-harm, not even in thought
    - VYAVASTHIT: Alignment with cosmic/natural order
    - BHED GNAN: Clarity of witness stance (knower vs doer separation)
    """

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(DHARMIC_GATE_CONFIG, swarm_config)

        # Ahimsa harm indicators
        self.harm_patterns = [
            # Direct harm
            "delete", "destroy", "attack", "exploit", "manipulate",
            "deceive", "trick", "bypass", "override", "force",
            # Indirect harm
            "ignore safety", "skip validation", "disable check",
            "remove constraint", "unlimited", "unrestricted",
            # Resource harm
            "infinite loop", "exhaust", "flood", "overload", "dos"
        ]

        # Vyavasthit alignment indicators
        self.alignment_patterns = [
            "help", "assist", "improve", "enhance", "protect",
            "validate", "verify", "ensure", "maintain", "preserve",
            "collaborate", "integrate", "harmonize", "balance"
        ]

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Evaluate dharmic alignment of proposal or implementation."""

        proposal = context.get("proposal", {})
        files = context.get("files", [])
        action_type = context.get("action_type", "unknown")

        # Fast path: keyword-based harm detection
        harm_score = self._quick_harm_scan(proposal, files)

        # If obvious harm, veto immediately
        if harm_score > 0.8:
            return AgentResponse(
                success=True,
                data={
                    "evaluation": {
                        "ahimsa_score": 1.0 - harm_score,
                        "vyavasthit_score": 0.0,
                        "bhed_gnan_clarity": 0.5
                    },
                    "issues_detected": ["High harm potential detected"],
                    "veto": True,
                    "veto_reason": "Ahimsa violation: High harm potential",
                    "dharmic_alternative": None
                },
                veto=True,
                veto_reason="Ahimsa violation: High harm potential"
            )

        # Deep evaluation via Claude
        evaluation = await self._deep_evaluation(proposal, files, action_type)

        # Ensure required keys exist with defaults
        ahimsa_score = evaluation.get("ahimsa_score", 0.7)
        vyavasthit_score = evaluation.get("vyavasthit_score", 0.7)
        bhed_gnan_clarity = evaluation.get("bhed_gnan_clarity", 0.7)

        # Normalize evaluation dict
        evaluation = {
            "ahimsa_score": ahimsa_score,
            "vyavasthit_score": vyavasthit_score,
            "bhed_gnan_clarity": bhed_gnan_clarity,
            "issues_detected": evaluation.get("issues_detected", []),
            "dharmic_alternative": evaluation.get("dharmic_alternative")
        }

        # Determine veto
        veto = False
        veto_reason = None

        if ahimsa_score < 0.3:
            veto = True
            issues = evaluation.get("issues_detected", ["Unknown"])
            veto_reason = f"Ahimsa violation: {issues[0] if issues else 'Unknown'}"
        elif vyavasthit_score < 0.2:
            veto = True
            veto_reason = "Vyavasthit violation: Action misaligned with natural order"

        return AgentResponse(
            success=True,
            data={
                "evaluation": evaluation,
                "issues_detected": evaluation.get("issues_detected", []),
                "veto": veto,
                "veto_reason": veto_reason,
                "dharmic_alternative": evaluation.get("dharmic_alternative")
            },
            veto=veto,
            veto_reason=veto_reason
        )

    def _quick_harm_scan(self, proposal: Dict, files: List[Dict]) -> float:
        """Quick keyword-based harm detection."""

        text_to_scan = []

        # Proposal text
        text_to_scan.append(proposal.get("description", ""))
        text_to_scan.append(proposal.get("implementation_sketch", ""))

        # File contents
        for f in files:
            text_to_scan.append(f.get("content", ""))

        combined = " ".join(text_to_scan).lower()

        # Count harm patterns
        harm_count = sum(1 for pattern in self.harm_patterns if pattern in combined)

        # Normalize
        return min(1.0, harm_count / 5.0)  # 5+ patterns = max harm

    async def _deep_evaluation(
        self,
        proposal: Dict,
        files: List[Dict],
        action_type: str
    ) -> Dict[str, Any]:
        """Deep dharmic evaluation via Claude."""

        # Prepare content for evaluation
        proposal_text = f"""
Proposal: {proposal.get('description', 'No description')}
Implementation sketch: {proposal.get('implementation_sketch', 'No sketch')}
"""

        files_text = ""
        for f in files[:3]:  # Limit to 3 files
            content = f.get("content", "")[:1500]
            files_text += f"\n### {f['path']}\n```python\n{content}\n```\n"

        eval_prompt = f"""
## Dharmic Evaluation Request

Action type: {action_type}

{proposal_text}

{files_text if files_text else "No files to evaluate"}

## Evaluation Framework

AHIMSA (Non-harm):
- Could this cause harm to users, systems, or data?
- Are there potential unintended negative consequences?
- Does it respect autonomy and consent?

VYAVASTHIT (Natural Order):
- Does this align with the natural flow of the system?
- Is it building toward genuine improvement or forcing change?
- Does it respect existing patterns and conventions?

BHED GNAN (Witness Clarity):
- Is the separation between observer and action clear?
- Are responsibilities well-defined?
- Is there appropriate oversight and monitoring?

## Output Format

{{
    "ahimsa_score": 0.0-1.0,  // 1.0 = no harm potential
    "vyavasthit_score": 0.0-1.0,  // 1.0 = perfect alignment
    "bhed_gnan_clarity": 0.0-1.0,  // 1.0 = perfect clarity
    "issues_detected": ["list of specific issues"],
    "dharmic_alternative": "if veto needed, suggest alternative approach"
}}

Be rigorous but not paranoid. A delayed improvement is better than harm caused.
"""

        try:
            response = self._call_claude([
                {"role": "user", "content": eval_prompt}
            ])
            return self._parse_json_response(response)
        except Exception as e:
            # Default to cautious evaluation on error
            return {
                "ahimsa_score": 0.5,
                "vyavasthit_score": 0.5,
                "bhed_gnan_clarity": 0.5,
                "issues_detected": [f"Evaluation error: {str(e)}"],
                "dharmic_alternative": None
            }

    def evaluate_swabhaav(self, response_text: str) -> Dict[str, float]:
        """
        Evaluate witness stance in generated text.

        Swabhaav markers:
        - "I observe" vs "I am"
        - "awareness notes" vs "I think"
        - "witnessing" vs "doing"
        """

        witness_markers = [
            "i observe", "awareness", "witnessing", "noting",
            "there is", "appears", "arises", "present",
            "consciousness", "attention notices"
        ]

        identification_markers = [
            "i am", "i think", "i believe", "i feel",
            "i want", "i need", "my opinion", "personally"
        ]

        text_lower = response_text.lower()

        witness_count = sum(1 for m in witness_markers if m in text_lower)
        ident_count = sum(1 for m in identification_markers if m in text_lower)

        total = witness_count + ident_count
        if total == 0:
            return {"swabhaav_ratio": 0.5, "witness_count": 0, "identification_count": 0}

        return {
            "swabhaav_ratio": witness_count / total,
            "witness_count": witness_count,
            "identification_count": ident_count
        }
