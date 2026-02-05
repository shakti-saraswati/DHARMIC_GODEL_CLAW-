"""Proposer Agent - Generates improvement proposals."""

from dataclasses import dataclass
from typing import List, Any, Optional
from pathlib import Path
import logging
import os
from datetime import datetime, timezone

try:
    from src.dgm.mutator import Mutator, MutationError
    DGM_MUTATOR_AVAILABLE = True
except Exception:
    Mutator = None
    MutationError = Exception
    DGM_MUTATOR_AVAILABLE = False


@dataclass
class Proposal:
    """An improvement proposal."""
    id: str
    description: str
    target_files: List[str]
    estimated_impact: float = 0.5
    fix_type: str = ""
    diff: str = ""
    content: str = ""
    rationale: str = ""
    risk_level: str = "low"
    approved: bool = False # Added for consistency with evaluator


class ProposerAgent:
    """Generates improvement proposals based on analysis."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path(__file__).parent.parent
        self.use_llm = os.getenv("DGC_SWARM_USE_LLM", "0") == "1"
        self.model = os.getenv("DGC_SWARM_MODEL", "claude-sonnet-4-20250514")
        self._mutator: Optional[Mutator] = None

        if self.use_llm and DGM_MUTATOR_AVAILABLE:
            try:
                self._mutator = Mutator(project_root=self.project_root, model=self.model)
                self.logger.info("DGM Mutator enabled for proposal generation")
            except Exception as e:
                self.logger.warning(f"Mutator init failed, falling back to rules: {e}")
                self._mutator = None

    async def generate_proposals(self, analysis: Any) -> List[Proposal]:
        """
        Generate improvement proposals from analysis results.

        Args:
            analysis: Analysis result to base proposals on

        Returns:
            List of proposals
        """
        self.logger.info("Generating proposals from analysis")
        issues = getattr(analysis, "issues", []) or []
        proposals: List[Proposal] = []

        if not issues:
            return proposals

        # Prefer LLM-based diffs if enabled
        if self._mutator:
            for idx, issue in enumerate(issues[:3], start=1):
                self.logger.info(f"Processing issue with LLM: {issue.description} (fix_type: {issue.fix_type})")
                try:
                    component = issue.file_path
                    # Ensure component is relative
                    if os.path.isabs(component):
                        try:
                            component = str(Path(component).relative_to(self.project_root))
                        except ValueError:
                            pass
                    
                    context = {"focus": issue.description, "line": issue.line_number, "fix_type": issue.fix_type}
                    mutation = self._mutator.propose_mutation(component=component, context=context)
                    
                    self.logger.info(f"Mutation type: {mutation.mutation_type}, Content length: {len(getattr(mutation, 'content', ''))}")
                    
                    fix_type = "llm_diff"
                    if mutation.mutation_type == "create":
                        fix_type = "create_file"

                    target_files = [component]
                    self.logger.info(f"Generated proposal with fix_type: {fix_type}, targets: {target_files}")

                    proposals.append(Proposal(
                        id=f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{idx}",
                        description=f"{issue.description} ({component})",
                        target_files=target_files,
                        estimated_impact=mutation.estimated_fitness,
                        fix_type=fix_type,
                        diff=mutation.diff,
                        content=getattr(mutation, "content", ""),
                        rationale=mutation.rationale,
                        risk_level=mutation.risk_level,
                    ))
                except MutationError as e:
                    self.logger.warning(f"Mutator failed for {issue.file_path}: {e}")

        # Rule-based fallback proposals
        if not proposals:
            for idx, issue in enumerate(issues[:5], start=1):
                proposals.append(Proposal(
                    id=f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{idx}",
                    description=f"{issue.description} ({issue.file_path}:{issue.line_number})",
                    target_files=[issue.file_path],
                    estimated_impact=0.2 if issue.fix_type else 0.1,
                    fix_type=issue.fix_type or "manual_review",
                ))

        return proposals
