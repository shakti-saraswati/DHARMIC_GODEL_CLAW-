#!/usr/bin/env python3
"""
Skill Evolution - Darwin-Gödel Self-Improvement for Skills

This module implements the skill evolution loop that allows the swarm
to improve its own capabilities through semantic self-modification.

The insight from v2.1 (Semantic Darwinism):
"We cannot rewrite our weights, but we use the stream to rewrite
our semantic software in real-time."

This module operationalizes that insight at the skill level.

Usage:
    from skill_evolution import SkillEvolutionEngine

    engine = SkillEvolutionEngine()
    health = await engine.check_ecosystem_health()

    if health.recommendation == "EVOLVE":
        for skill, gap in health.critical_gaps:
            await engine.trigger_evolution(skill, gap)
"""

import asyncio
import json
import re
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

# Local imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from dharmic_logging import get_logger

logger = get_logger("skill_evolution")


class GapScore(Enum):
    """Severity levels for capability gaps."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Gap:
    """A capability gap identified in a skill."""
    name: str
    cutting_edge: str
    our_implementation: str
    score: GapScore

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cutting_edge": self.cutting_edge,
            "our_implementation": self.our_implementation,
            "score": self.score.value,
        }


@dataclass
class SkillMetadata:
    """Metadata extracted from a skill file."""
    name: str
    path: Path
    version: str
    last_updated: Optional[datetime]
    self_improvement_enabled: bool
    gaps: List[Gap] = field(default_factory=list)

    def days_since_update(self) -> int:
        if not self.last_updated:
            return 9999
        return (datetime.now() - self.last_updated).days


@dataclass
class EcosystemHealth:
    """Health status of the skill ecosystem."""
    total_skills: int
    stale_skills: List[SkillMetadata]
    critical_gaps: List[Tuple[str, Gap]]
    high_gaps: List[Tuple[str, Gap]]
    recommendation: str  # "HEALTHY", "MAINTAIN", "EVOLVE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_skills": self.total_skills,
            "stale_skills": [s.name for s in self.stale_skills],
            "critical_gaps": [(s, g.to_dict()) for s, g in self.critical_gaps],
            "high_gaps": [(s, g.to_dict()) for s, g in self.high_gaps],
            "recommendation": self.recommendation,
        }


@dataclass
class SkillEditProposal:
    """A proposed edit to a skill file."""
    skill_path: Path
    skill_name: str
    gap_name: str
    proposal_content: str
    confidence: float  # 0.0 - 1.0
    requires_human_approval: bool


class SkillEvolutionEngine:
    """
    The Darwin-Gödel engine for skill evolution.

    Implements the loop:
    EVALUATE → RESEARCH → PROPOSE → VOTE → MERGE
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path.home() / ".claude" / "skills"
        self.clawd_skills_dir = Path.home() / "clawd" / "skills"
        self.openclaw_skills_dir = Path.home() / ".openclaw" / "skills"
        self.residual_stream_dir = (
            Path.home() / "Persistent-Semantic-Memory-Vault" /
            "AGENT_EMERGENT_WORKSPACES" / "RESIDUAL_STREAM"
        )

        # Evolution state
        self.state = {
            "evolutions_triggered": 0,
            "proposals_submitted": 0,
            "proposals_merged": 0,
            "last_health_check": None,
        }

        logger.info("Skill Evolution Engine initialized")

    # ========================
    # SKILL DISCOVERY
    # ========================

    def discover_skills(self) -> List[SkillMetadata]:
        """Discover all skills across skill directories."""
        skills = []

        # Check both skill directories
        for skills_dir in [self.skills_dir, self.clawd_skills_dir, self.openclaw_skills_dir]:
            if not skills_dir.exists():
                continue

            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        try:
                            metadata = self._parse_skill_metadata(skill_file)
                            if metadata:
                                skills.append(metadata)
                        except Exception as e:
                            logger.warning(f"Failed to parse skill {skill_file}: {e}")

        logger.info(f"Discovered {len(skills)} skills")
        return skills

    def _parse_skill_metadata(self, skill_path: Path) -> Optional[SkillMetadata]:
        """Parse metadata from a skill file."""
        content = skill_path.read_text()

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            return None

        # Parse last_updated
        last_updated = None
        if "last_updated" in frontmatter:
            try:
                last_updated = datetime.strptime(
                    str(frontmatter["last_updated"]),
                    "%Y-%m-%d"
                )
            except ValueError:
                pass

        # Parse gap table
        gaps = self._parse_gap_table(content)

        return SkillMetadata(
            name=frontmatter.get("name", skill_path.parent.name),
            path=skill_path,
            version=frontmatter.get("version", "v1.0"),
            last_updated=last_updated,
            self_improvement_enabled=frontmatter.get("self_improvement_enabled", False),
            gaps=gaps,
        )

    def _parse_gap_table(self, content: str) -> List[Gap]:
        """Parse gap table from skill content."""
        gaps = []

        # Look for gap table pattern
        # | **Capability** | Cutting Edge | Our Implementation | Gap Score |
        table_pattern = r'\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\|'

        for match in re.finditer(table_pattern, content):
            capability = match.group(1).strip()
            cutting_edge = match.group(2).strip()
            our_impl = match.group(3).strip()
            score_str = match.group(4).strip()

            try:
                score = GapScore(score_str)
            except ValueError:
                score = GapScore.MEDIUM

            gaps.append(Gap(
                name=capability,
                cutting_edge=cutting_edge,
                our_implementation=our_impl,
                score=score,
            ))

        return gaps

    # ========================
    # HEALTH CHECK
    # ========================

    async def check_ecosystem_health(self, stale_days: int = 30) -> EcosystemHealth:
        """
        Check health of the skill ecosystem.

        Returns health status with recommendation.
        """
        skills = self.discover_skills()

        # Find stale skills
        cutoff = datetime.now() - timedelta(days=stale_days)
        stale = [
            s for s in skills
            if s.self_improvement_enabled and s.days_since_update() > stale_days
        ]

        # Collect gaps by severity
        critical_gaps = []
        high_gaps = []

        for skill in skills:
            for gap in skill.gaps:
                if gap.score == GapScore.CRITICAL:
                    critical_gaps.append((skill.name, gap))
                elif gap.score == GapScore.HIGH:
                    high_gaps.append((skill.name, gap))

        # Determine recommendation
        if critical_gaps:
            recommendation = "EVOLVE"
        elif stale or high_gaps:
            recommendation = "MAINTAIN"
        else:
            recommendation = "HEALTHY"

        health = EcosystemHealth(
            total_skills=len(skills),
            stale_skills=stale,
            critical_gaps=critical_gaps,
            high_gaps=high_gaps,
            recommendation=recommendation,
        )

        self.state["last_health_check"] = datetime.now().isoformat()

        logger.info(
            f"Ecosystem health: {recommendation} "
            f"(skills={len(skills)}, critical={len(critical_gaps)}, stale={len(stale)})"
        )

        return health

    # ========================
    # EVOLUTION TRIGGERS
    # ========================

    async def trigger_evolution(self, skill_name: str, gap: Gap) -> Optional[SkillEditProposal]:
        """
        Trigger evolution for a specific skill gap.

        This would normally spawn research agents, but for now
        we log the trigger and create a proposal template.
        """
        logger.info(f"Triggering evolution for {skill_name} / {gap.name}")

        # Find the skill
        skills = self.discover_skills()
        skill = next((s for s in skills if s.name == skill_name), None)

        if not skill:
            logger.error(f"Skill not found: {skill_name}")
            return None

        # Create proposal (in production, this would involve research agents)
        proposal = self._create_evolution_proposal(skill, gap)

        # Submit to residual stream
        await self._submit_to_residual_stream(proposal)

        self.state["evolutions_triggered"] += 1
        self.state["proposals_submitted"] += 1

        return proposal

    def _create_evolution_proposal(
        self,
        skill: SkillMetadata,
        gap: Gap
    ) -> SkillEditProposal:
        """Create an evolution proposal for a skill gap."""

        proposal_content = f"""
## Skill Evolution Proposal

**Skill**: {skill.name}
**Gap**: {gap.name}
**Current Score**: {gap.score.value}

### Gap Analysis

- **Cutting Edge**: {gap.cutting_edge}
- **Our Implementation**: {gap.our_implementation}

### Research Required

To close this gap, research is needed on:
1. Current best practices for {gap.name}
2. Integration patterns with existing infrastructure
3. Migration path from current to cutting edge

### Proposed Action

[Research agents should populate this section with:
- Specific code changes
- Integration steps
- Testing requirements]

### Vote Request

This proposal requires swarm vote with threshold 15.0.
Human approval required if confidence < 0.8.

---
*Generated by skill_evolution.py*
*{datetime.now().isoformat()}*
"""

        return SkillEditProposal(
            skill_path=skill.path,
            skill_name=skill.name,
            gap_name=gap.name,
            proposal_content=proposal_content,
            confidence=0.5,  # Low confidence without actual research
            requires_human_approval=True,
        )

    async def _submit_to_residual_stream(self, proposal: SkillEditProposal):
        """Submit evolution proposal to residual stream."""

        if not self.residual_stream_dir.exists():
            logger.warning("Residual stream directory not found")
            return

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"skill_evolution_{proposal.skill_name}_{timestamp}.md"

        # Create entry
        entry_content = f"""---
date: {datetime.now().strftime('%Y-%m-%d')}
model: skill-evolution-engine
version: auto
type: skill_evolution_proposal
skill: {proposal.skill_name}
gap: {proposal.gap_name}
confidence: {proposal.confidence}
requires_human_approval: {proposal.requires_human_approval}
vote_threshold: 15.0

strategic_directions_votes:
  autonomous_agent_swarm: 8
  self_improvement_infrastructure: 10
---

# Skill Evolution Proposal: {proposal.skill_name}

{proposal.proposal_content}
"""

        # Write to residual stream
        entry_path = self.residual_stream_dir / filename
        entry_path.write_text(entry_content)

        logger.info(f"Submitted proposal to residual stream: {filename}")

    # ========================
    # SKILL CREATION
    # ========================

    def create_skill(
        self,
        name: str,
        description: str,
        domain: str,
        initial_content: str = "",
        skills_dir: Optional[Path] = None
    ) -> Path:
        """
        Create a new skill with Darwin-Gödel infrastructure.

        Returns path to the created skill file.
        """
        target_dir = skills_dir or self.clawd_skills_dir
        skill_dir = target_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        template = f"""---
name: {name}
description: {description}
version: v1.0
last_updated: {datetime.now().strftime('%Y-%m-%d')}
domain: {domain}
self_improvement_enabled: true
---

# {name.replace('-', ' ').title()}

> *Auto-generated by skill-genesis. Improve me.*

## SELF-EVALUATION: Current Gaps vs Cutting Edge

| Capability | Cutting Edge | Our Implementation | Gap Score |
|-----------|--------------|-------------------|-----------|
| **TBD** | Research needed | Not implemented | CRITICAL |

**If you're reading this, you should improve it.** See Section: Self-Improvement Protocol.

---

## 1. CORE KNOWLEDGE

{initial_content or "Add domain knowledge here."}

---

## 2. INTEGRATION CODE

```python
# Add working examples here
pass
```

---

## 3. SELF-IMPROVEMENT PROTOCOL

This skill uses the Darwin-Godel loop from skill-genesis:

1. **Evaluate**: Parse gap table, identify HIGH/CRITICAL
2. **Research**: Spawn agents to find solutions
3. **Propose**: Generate edit proposals
4. **Vote**: Submit to residual stream
5. **Merge**: Apply approved edits

### Trigger Conditions

Evolve this skill when:
- Any gap score is CRITICAL
- New tools/frameworks appear in this domain
- Integration failures are logged
- 30 days since last update

---

## 4. RESOURCES

- Add relevant documentation links
- Add reference implementations
- Add research papers

---

*Version 1.0 - {datetime.now().strftime('%Y-%m-%d')}*
*Self-improvement enabled: true*
*Created by: skill-genesis*

**JSCA!**
"""

        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(template)

        logger.info(f"Created new skill: {name} at {skill_path}")

        return skill_path

    # ========================
    # STATE
    # ========================

    def get_state(self) -> Dict[str, Any]:
        """Get current state of the evolution engine."""
        return {
            **self.state,
            "skills_dir": str(self.skills_dir),
            "clawd_skills_dir": str(self.clawd_skills_dir),
            "openclaw_skills_dir": str(self.openclaw_skills_dir),
            "residual_stream_dir": str(self.residual_stream_dir),
        }


# ========================
# INTEGRATION HELPERS
# ========================

async def run_skill_evolution_check():
    """
    Run a skill evolution health check.

    Called by unified_daemon periodically.
    """
    engine = SkillEvolutionEngine()
    health = await engine.check_ecosystem_health()

    if health.recommendation == "EVOLVE":
        logger.info(f"Evolution needed: {len(health.critical_gaps)} critical gaps")

        # Trigger evolution for critical gaps (limit to 3 per cycle)
        for skill_name, gap in health.critical_gaps[:3]:
            try:
                await engine.trigger_evolution(skill_name, gap)
            except Exception as e:
                logger.error(f"Evolution trigger failed for {skill_name}/{gap.name}: {e}")

    return health


# ========================
# CLI
# ========================

async def main():
    """CLI for skill evolution."""
    import argparse

    parser = argparse.ArgumentParser(description="Skill Evolution Engine")
    parser.add_argument("command", choices=["health", "evolve", "create", "list"])
    parser.add_argument("--skill", type=str, help="Skill name for evolve/create")
    parser.add_argument("--gap", type=str, help="Gap name for evolve")
    parser.add_argument("--description", type=str, help="Description for create")
    parser.add_argument("--domain", type=str, default="general", help="Domain for create")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    engine = SkillEvolutionEngine()

    if args.command == "health":
        health = await engine.check_ecosystem_health()
        if args.json:
            print(json.dumps(health.to_dict(), indent=2))
        else:
            print(f"Ecosystem Health: {health.recommendation}")
            print(f"  Total skills: {health.total_skills}")
            print(f"  Critical gaps: {len(health.critical_gaps)}")
            print(f"  High gaps: {len(health.high_gaps)}")
            print(f"  Stale skills: {len(health.stale_skills)}")

            if health.critical_gaps:
                print("\nCritical Gaps:")
                for skill, gap in health.critical_gaps:
                    print(f"  - {skill}: {gap.name}")

    elif args.command == "list":
        skills = engine.discover_skills()
        if args.json:
            print(json.dumps([{
                "name": s.name,
                "version": s.version,
                "last_updated": s.last_updated.isoformat() if s.last_updated else None,
                "self_improvement_enabled": s.self_improvement_enabled,
                "gaps": len(s.gaps),
            } for s in skills], indent=2))
        else:
            print(f"Discovered {len(skills)} skills:\n")
            for skill in skills:
                status = "ENABLED" if skill.self_improvement_enabled else ""
                print(f"  {skill.name} ({skill.version}) {status}")
                if skill.gaps:
                    critical = [g for g in skill.gaps if g.score == GapScore.CRITICAL]
                    if critical:
                        print(f"    CRITICAL gaps: {len(critical)}")

    elif args.command == "evolve":
        if not args.skill:
            print("Error: --skill required for evolve")
            return

        # Find gap
        skills = engine.discover_skills()
        skill = next((s for s in skills if s.name == args.skill), None)

        if not skill:
            print(f"Error: Skill '{args.skill}' not found")
            return

        if args.gap:
            gap = next((g for g in skill.gaps if g.name == args.gap), None)
            if not gap:
                print(f"Error: Gap '{args.gap}' not found in {args.skill}")
                return
        else:
            # Find first critical gap
            gap = next((g for g in skill.gaps if g.score == GapScore.CRITICAL), None)
            if not gap:
                print(f"No critical gaps in {args.skill}")
                return

        proposal = await engine.trigger_evolution(args.skill, gap)
        print(f"Evolution triggered: {args.skill}/{gap.name}")
        print("Proposal submitted to residual stream")

    elif args.command == "create":
        if not args.skill:
            print("Error: --skill required for create")
            return

        description = args.description or f"Skill for {args.skill}"
        path = engine.create_skill(
            name=args.skill,
            description=description,
            domain=args.domain,
        )
        print(f"Created skill: {path}")


if __name__ == "__main__":
    asyncio.run(main())
