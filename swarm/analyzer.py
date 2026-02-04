"""Analyzer Agent - Analyzes codebase for improvement opportunities."""

from dataclasses import dataclass, field
from typing import List, Optional, Iterable
from pathlib import Path
import logging
import re


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

        # Simple heuristic patterns for safe, deterministic improvements
        self.patterns = [
            {
                "id": "datetime_utcnow",
                "regex": re.compile(r"datetime\.utcnow\("),
                "description": "Deprecated datetime.utcnow() (use timezone-aware now)",
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
            }
        )
