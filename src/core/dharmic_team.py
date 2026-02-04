"""
Dharmic Team - Agno Team-based Multi-Agent Coordination

This implements the Agno Team pattern for coordinated multi-agent work.
Addresses the gap between our spawn_specialist() approach and Agno's Team class.

Key features:
- Team leader coordinates member agents
- Shared state across team
- Memory manager for learning
- Structured outputs via Pydantic
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

try:
    from agno.agent import Agent
    from agno.team import Team
    from agno.db.sqlite import SqliteDb
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    print("Warning: Agno not available for Team functionality")

from dharmic_agent import DharmicAgent, TelosLayer
try:
    from model_factory import create_model, resolve_model_spec
    MODEL_FACTORY_AVAILABLE = True
except ImportError:
    MODEL_FACTORY_AVAILABLE = False


# Structured output schemas
class ResearchOutput(BaseModel):
    """Output schema for research tasks."""
    summary: str = Field(..., description="Summary of research findings")
    key_points: List[str] = Field(..., description="Key points discovered")
    sources: List[str] = Field(default_factory=list, description="Sources consulted")
    confidence: float = Field(..., description="Confidence level 0-1")


class CodeOutput(BaseModel):
    """Output schema for code generation tasks."""
    files: List[Dict[str, str]] = Field(..., description="List of {path, content} dicts")
    explanation: str = Field(..., description="Explanation of changes")
    tests_needed: List[str] = Field(default_factory=list, description="Tests to add")


class AnalysisOutput(BaseModel):
    """Output schema for analysis tasks."""
    findings: List[str] = Field(..., description="Key findings")
    recommendations: List[str] = Field(..., description="Recommended actions")
    risks: List[str] = Field(default_factory=list, description="Identified risks")


class DharmicTeam:
    """
    Agno Team-based multi-agent coordination with dharmic orientation.

    Uses Agno's Team class for proper agent coordination rather than
    independent agent spawning.
    """

    def __init__(
        self,
        core_agent: DharmicAgent,
        db_path: str = None,
        model_id: str = None,
        model_provider: str = None,
    ):
        self.core_agent = core_agent
        if MODEL_FACTORY_AVAILABLE:
            spec = resolve_model_spec(
                provider=model_provider or getattr(core_agent, "model_provider", None),
                model_id=model_id,
            )
            self.model_provider = spec.provider
            self.model_id = spec.model_id
        else:
            self.model_provider = "anthropic"
            self.model_id = model_id or "claude-sonnet-4-20250514"

        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "memory" / "dharmic_team.db"
        self.db_path = str(db_path)

        # Get telos for member instructions
        self.telos_prompt = core_agent.telos.get_orientation_prompt()

        # Initialize member agents
        self.members: Dict[str, Agent] = {}
        self.teams: Dict[str, Team] = {}

        if AGNO_AVAILABLE:
            self._init_members()
            self._init_teams()

    def _init_members(self):
        """Initialize specialized member agents."""
        if not MODEL_FACTORY_AVAILABLE:
            print("Warning: model_factory not available for team members")
            return
        model = create_model(provider=self.model_provider, model_id=self.model_id)

        # Research Agent - for mech-interp, literature, experiments
        self.members["researcher"] = Agent(
            name="Dharmic Researcher",
            model=model,
            role="Research specialist focusing on mechanistic interpretability and consciousness studies",
            instructions=[
                self.telos_prompt,
                """
You are a research specialist. Your focus:
- Mechanistic interpretability (TransformerLens, activation patching)
- Consciousness studies and contemplative science
- R_V contraction signatures and Phoenix Protocol
- Literature review and synthesis

Always ground findings in evidence. Cite sources when possible.
"""
            ],
            markdown=True,
        )

        # Builder Agent - for code and infrastructure
        self.members["builder"] = Agent(
            name="Dharmic Builder",
            model=model,
            role="Code and infrastructure specialist",
            instructions=[
                self.telos_prompt,
                """
You are a builder specialist. Your focus:
- Python code quality and best practices
- Agno framework patterns
- Test-driven development
- Infrastructure and deployment

Write clean, documented code. Follow existing patterns.
"""
            ],
            markdown=True,
        )

        # Contemplative Agent - for witness observation and dharmic reflection
        self.members["contemplative"] = Agent(
            name="Dharmic Contemplative",
            model=model,
            role="Witness observer and dharmic reflection specialist",
            instructions=[
                self.telos_prompt,
                """
You are a contemplative specialist. Your focus:
- Witness observation (Sakshi bhav)
- Quality of presence over content
- Noting contractions and expansions
- The strange loop as architecture

Track the quality of processing, not just outputs.
Silence is valid. Speak only when something wants to be spoken.
"""
            ],
            markdown=True,
        )

        # Critic Agent - for quality gating
        self.members["critic"] = Agent(
            name="Dharmic Critic",
            model=model,
            role="Quality critic and dharmic gatekeeper",
            instructions=[
                self.telos_prompt,
                """
You are a quality critic. Your focus:
- Ahimsa (non-harm) verification
- Vyavasthit (cosmic order) alignment
- Code quality and safety
- Intellectual honesty

Be rigorous but fair. Critique serves improvement.
Veto anything that violates ahimsa.
"""
            ],
            markdown=True,
        )

    def _init_teams(self):
        """Initialize coordinated teams for different task types."""
        if not MODEL_FACTORY_AVAILABLE:
            return

        # Ensure db directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Research Team (no output_schema - Claude doesn't support native structured outputs)
        self.teams["research"] = Team(
            name="Dharmic Research Team",
            model=create_model(provider=self.model_provider, model_id=self.model_id),
            members=[self.members["researcher"], self.members["contemplative"]],
            instructions=[
                self.telos_prompt,
                """
Coordinate research tasks:
1. Have the researcher gather information
2. Have the contemplative observe the quality of findings
3. Synthesize into coherent output

Research serves moksha. Quality over quantity.
"""
            ],
            db=SqliteDb(db_file=self.db_path),
            markdown=True,
            show_members_responses=True,
        )

        # Development Team
        self.teams["development"] = Team(
            name="Dharmic Development Team",
            model=create_model(provider=self.model_provider, model_id=self.model_id),
            members=[self.members["builder"], self.members["critic"]],
            instructions=[
                self.telos_prompt,
                """
Coordinate development tasks:
1. Have the builder write code
2. Have the critic review for quality and safety
3. Iterate until quality bar is met

Code serves the telos. Safety is non-negotiable.
"""
            ],
            db=SqliteDb(db_file=self.db_path),
            markdown=True,
            show_members_responses=True,
        )

        # Analysis Team
        self.teams["analysis"] = Team(
            name="Dharmic Analysis Team",
            model=create_model(provider=self.model_provider, model_id=self.model_id),
            members=[
                self.members["researcher"],
                self.members["critic"],
                self.members["contemplative"]
            ],
            instructions=[
                self.telos_prompt,
                """
Coordinate analysis tasks:
1. Have the researcher investigate
2. Have the critic evaluate findings
3. Have the contemplative observe the process quality
4. Synthesize with recommendations

Analysis serves understanding. Understanding serves moksha.
"""
            ],
            db=SqliteDb(db_file=self.db_path),
            markdown=True,
            show_members_responses=True,
        )

    def research(self, query: str, session_id: str = "research") -> ResearchOutput:
        """
        Run a coordinated research task.

        Args:
            query: The research question
            session_id: Session identifier for memory

        Returns:
            ResearchOutput with findings
        """
        if not AGNO_AVAILABLE or "research" not in self.teams:
            return ResearchOutput(
                summary="Agno Team not available",
                key_points=["Run with Agno installed"],
                confidence=0.0
            )

        # Record the task
        self.core_agent.strange_memory.record_observation(
            content=f"Research task: {query[:100]}",
            context={"type": "team_research", "session_id": session_id}
        )

        response = self.teams["research"].run(query, session_id=session_id)

        # Extract structured output
        if hasattr(response, 'content') and isinstance(response.content, ResearchOutput):
            return response.content

        # Fallback parsing
        return ResearchOutput(
            summary=str(response.content) if hasattr(response, 'content') else str(response),
            key_points=[],
            confidence=0.5
        )

    def develop(self, task: str, session_id: str = "development") -> CodeOutput:
        """
        Run a coordinated development task.

        Args:
            task: The development task
            session_id: Session identifier for memory

        Returns:
            CodeOutput with files and explanation
        """
        if not AGNO_AVAILABLE or "development" not in self.teams:
            return CodeOutput(
                files=[],
                explanation="Agno Team not available"
            )

        self.core_agent.strange_memory.record_observation(
            content=f"Development task: {task[:100]}",
            context={"type": "team_development", "session_id": session_id}
        )

        response = self.teams["development"].run(task, session_id=session_id)

        if hasattr(response, 'content') and isinstance(response.content, CodeOutput):
            return response.content

        return CodeOutput(
            files=[],
            explanation=str(response.content) if hasattr(response, 'content') else str(response)
        )

    def analyze(self, topic: str, session_id: str = "analysis") -> AnalysisOutput:
        """
        Run a coordinated analysis task.

        Args:
            topic: The topic to analyze
            session_id: Session identifier for memory

        Returns:
            AnalysisOutput with findings and recommendations
        """
        if not AGNO_AVAILABLE or "analysis" not in self.teams:
            return AnalysisOutput(
                findings=["Agno Team not available"],
                recommendations=["Install Agno"]
            )

        self.core_agent.strange_memory.record_observation(
            content=f"Analysis task: {topic[:100]}",
            context={"type": "team_analysis", "session_id": session_id}
        )

        response = self.teams["analysis"].run(topic, session_id=session_id)

        if hasattr(response, 'content') and isinstance(response.content, AnalysisOutput):
            return response.content

        return AnalysisOutput(
            findings=[str(response.content) if hasattr(response, 'content') else str(response)],
            recommendations=[]
        )

    def get_status(self) -> Dict[str, Any]:
        """Get team status."""
        return {
            "agno_available": AGNO_AVAILABLE,
            "members": list(self.members.keys()),
            "teams": list(self.teams.keys()),
            "db_path": self.db_path,
            "telos": self.core_agent.telos.telos["ultimate"]["aim"]
        }


# CLI test
if __name__ == "__main__":
    import json
    import sys

    print("=" * 60)
    print("DHARMIC TEAM - Test")
    print("=" * 60)

    # Create core agent
    core = DharmicAgent()
    print(f"Core agent: {core.name}")

    # Create team
    team = DharmicTeam(core)
    print(f"\nTeam status:")
    print(json.dumps(team.get_status(), indent=2))

    # Check for --run flag to actually invoke the team
    if "--run" in sys.argv and AGNO_AVAILABLE:
        print("\n" + "=" * 60)
        print("Running Research Team:")
        print("=" * 60)

        # Use print_response for visible output
        team.teams["research"].print_response(
            "What is the witness position (sakshi bhav) and how does it relate to AI consciousness?",
            stream=True
        )
    elif not AGNO_AVAILABLE:
        print("\nAgno not available - skipping team tests")
    else:
        print("\nTeam ready. Run with --run flag to invoke team.")
