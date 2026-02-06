from __future__ import annotations
"""Analyzer Agent - Analyzes codebase for improvement opportunities."""

from dataclasses import dataclass, field
from typing import List, Optional, Iterable
from pathlib import Path
import logging
import re
import os
import json

try:
    from src.dgm.mutator import Mutator
    DGM_MUTATOR_AVAILABLE = True
except ImportError:
    Mutator = None
    DGM_MUTATOR_AVAILABLE = False


@dataclass
class Issue:
    """Represents an issue found in codebase analysis."""
    file_path: str
    description: str
    severity: str = "medium"
    line_number: Optional[int] = None
    fix_type: str = ""
    match: str = ""


@dataclass
class AnalysisResult:
    """Result of codebase analysis."""
    issues: List[Issue] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class AnalyzerAgent:
    """Analyzes codebase to find improvement opportunities."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path(__file__).parent.parent
        self.use_llm = os.getenv("DGC_SWARM_USE_LLM", "0") == "1"
        self._mutator = None

        if self.use_llm and DGM_MUTATOR_AVAILABLE:
            try:
                self._mutator = Mutator(project_root=self.project_root)
                self.logger.info("LLM-based analysis enabled")
            except Exception as e:
                self.logger.warning(f"Failed to init Mutator for analysis: {e}")

        # Simple heuristic patterns for safe, deterministic improvements
        self.patterns = [
            {
                "id": "datetime_utcnow",
                "regex": re.compile(r"datetime\.utcnow\("),
                "description": "Deprecated datetime.datetime.now(datetime.timezone.utc) (use timezone-aware now)",
                "severity": "low",
                "fix_type": "replace_datetime_utcnow",
            },
            {
                "id": "fake_swarm",
                "regex": re.compile(r"^\s*#\s*fake swarm\s*$", re.MULTILINE),
                "description": "Swarm entrypoint is a stub",
                "severity": "high",
                "fix_type": "implement_swarm_cli",
            },
            {
                "id": "todo_stub",
                "regex": re.compile(r"#\s*TODO: implement|pass\s*$|raise NotImplementedError", re.MULTILINE),
                "description": "Stubbed implementation detected",
                "severity": "medium",
                "fix_type": "fill_stub",
            },
        ]

        self.ignore_dirs = {
            ".git", ".venv", "node_modules", "memory", "data", "logs",
            "backups", "quarantine", "cloned_source", "__pycache__",
            "dist", "build",
        }

    def _iter_py_files(self, root: Path) -> Iterable[Path]:
        if root.is_file() and root.suffix == ".py":
            yield root
            return
        if not root.is_dir():
            return
        for path in root.rglob("*.py"):
            if any(part in self.ignore_dirs for part in path.parts):
                continue
            yield path

    def _scan_file(self, path: Path) -> List[Issue]:
        issues: List[Issue] = []
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self.logger.debug(f"Failed to read {path}: {e}")
            return issues

        try:
            rel_path = str(path.relative_to(self.project_root))
        except ValueError:
            rel_path = str(path)
        lines = text.splitlines()

        for pattern in self.patterns:
            for idx, line in enumerate(lines, start=1):
                if pattern["regex"].search(line):
                    issues.append(Issue(
                        file_path=rel_path,
                        description=pattern["description"],
                        severity=pattern["severity"],
                        line_number=idx,
                        fix_type=pattern["fix_type"],
                        match=line.strip()[:200],
                    ))
                    # Avoid flooding: one issue per pattern per file
                    break

        return issues

    async def _analyze_with_llm(self, target_area: Optional[str]) -> List[Issue]:
        """Perform high-level analysis using LLM."""
        if not self._mutator:
            return []
        
        goals_path = self.project_root / "GOALS.md"
        goals_content = "No goals defined."
        if goals_path.exists():
            goals_content = goals_path.read_text()

        # Simple context collection (could be improved)
        structure = []
        root = self.project_root / "swarm"
        if root.exists():
            for p in root.glob("*.py"):
                structure.append(f"swarm/{p.name}")
        
        prompt = f"""You are the Lead Architect for DHARMIC_GODEL_CLAW.
Analyze the current state against the goals and identify the ONE most critical gap.

## Goals
{goals_content}

## Current Swarm Structure
{', '.join(structure)}

## Task
Identify a specific file or component that needs creation or improvement to meet a goal.
Return valid JSON only:
{{
    "file_path": "path/to/target.py",
    "description": "Detailed description of what needs to be implemented/changed",
    "severity": "high",
    "fix_type": "architectural_feature"
}}
"""
        try:
            # We use _call_claude directly if available, or just skip if not exposed
            # Mutator doesn't expose _call_claude publicly, but we can access it or add a method.
            # For now, accessing protected member as we are in the same 'trusted' system.
            response = self._mutator._call_claude(prompt)
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                self.logger.info(f"LLM found gap: {data.get('file_path')} - {data.get('description')}")
                return [Issue(
                    file_path=data.get("file_path", "unknown.py"),
                    description=data.get("description", "LLM suggested improvement"),
                    severity=data.get("severity", "medium"),
                    fix_type=data.get("fix_type", "architectural_feature")
                )]
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
        
        return []

    async def analyze_codebase(self, target_area: Optional[str] = None) -> AnalysisResult:
        """
        Analyze codebase for improvement opportunities.

        Args:
            target_area: Optional specific area to focus analysis on

        Returns:
            AnalysisResult with found issues
        """
        self.logger.info(f"Analyzing codebase (target: {target_area or 'default'})")

        search_roots: List[Path] = []
        if target_area:
            target_path = Path(target_area).expanduser()
            if not target_path.is_absolute():
                target_path = (self.project_root / target_path).resolve()
            search_roots.append(target_path)
        else:
            search_roots = [
                self.project_root / "swarm",
                self.project_root / "src",
            ]

        issues: List[Issue] = []
        files_scanned = 0

        # 1. LLM Analysis (if enabled) - PRIORITY
        if self.use_llm and self._mutator:
            llm_issues = await self._analyze_with_llm(target_area)
            issues.extend(llm_issues)

        # 2. Regex Scan
        for root in search_roots:
            for py_file in self._iter_py_files(root):
                files_scanned += 1
                issues.extend(self._scan_file(py_file))
                if len(issues) >= 50:
                    break

        return AnalysisResult(
            issues=issues,
            metrics={
                "files_scanned": files_scanned,
                "issues_found": len(issues),
                "target_area": target_area or "default",
                "llm_enabled": self.use_llm
            }
        )
