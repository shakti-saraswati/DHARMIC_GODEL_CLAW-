from __future__ import annotations
"""Writer Agent - Implements approved proposals."""

from dataclasses import dataclass, field
from typing import List, Any
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
import sys

# Add src/core to path for security module
SRC_CORE = Path(__file__).parent.parent / "src" / "core"
if SRC_CORE.exists():
    sys.path.insert(0, str(SRC_CORE))

try:
    from dharmic_security import ExecGuard
    EXEC_GUARD = ExecGuard(allowed_bins=["git", "apply"])
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    EXEC_GUARD = None


@dataclass
class ImplementationResult:
    """Result of implementing proposals."""
    files_changed: List[str] = field(default_factory=list)
    success: bool = True
    error_message: str = ""


class WriterAgent:
    """Implements approved proposals as code changes."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path(__file__).parent.parent

    async def implement_proposals(self, proposals: List[Any]) -> ImplementationResult:
        """
        Implement approved proposals.

        Args:
            proposals: List of approved proposals to implement

        Returns:
            ImplementationResult with changed files
        """
        self.logger.info(f"Implementing {len(proposals)} proposals")
        files_changed: List[str] = []
        errors: List[str] = []

        live_allowed = os.getenv("DGC_ALLOW_LIVE") == "1"

        for proposal in proposals:
            try:
                diff = getattr(proposal, "diff", "") or ""
                fix_type = getattr(proposal, "fix_type", "") or ""
                target_files = getattr(proposal, "target_files", []) or []

                if diff:
                    applied = self._apply_diff(diff, live_allowed)
                    if applied:
                        files_changed.extend(target_files)
                    continue

                # Rule-based fixers
                if fix_type == "replace_datetime_utcnow":
                    for file_path in target_files:
                        if self._replace_datetime_utcnow(file_path, live_allowed):
                            files_changed.append(file_path)
                elif fix_type == "create_file":
                    content = getattr(proposal, "content", "")
                    if target_files:
                        self.logger.info(f"Triggering create_file for {target_files[0]}")
                        if self._create_file(target_files[0], content, live_allowed):
                            files_changed.append(target_files[0])
                else:
                    self.logger.info(f"No writer action for fix_type={fix_type}")

            except Exception as e:
                errors.append(str(e))

        success = len(errors) == 0
        return ImplementationResult(
            files_changed=sorted(set(files_changed)),
            success=success,
            error_message="; ".join(errors) if errors else ""
        )

    def _apply_diff(self, diff: str, live_allowed: bool) -> bool:
        """Apply a unified diff using git apply."""
        if not diff.strip():
            return False
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp.write(diff)
            tmp_path = tmp.name

        try:
            if not live_allowed:
                # Dry-run check
                cmd = ["git", "apply", "--check", tmp_path]
                if SECURITY_AVAILABLE and EXEC_GUARD:
                    result = EXEC_GUARD.run(
                        cmd,
                        cwd=str(self.project_root),
                        capture_output=True,
                        text=True,
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        cwd=str(self.project_root),
                        capture_output=True,
                        text=True,
                    )
                
                if result.returncode != 0:
                    self.logger.warning(f"Diff check failed: {result.stderr.strip()}")
                    return False
                self.logger.info("Diff validated (dry-run), not applied")
                return False

            cmd = ["git", "apply", "--whitespace=nowarn", tmp_path]
            if SECURITY_AVAILABLE and EXEC_GUARD:
                result = EXEC_GUARD.run(
                    cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                )
            else:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                )
                
            if result.returncode != 0:
                self.logger.warning(f"Diff apply failed: {result.stderr.strip()}")
                return False
            return True
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _replace_datetime_utcnow(self, file_path: str, live_allowed: bool) -> bool:
        """Replace datetime.utcnow() with timezone-aware usage."""
        path = (self.project_root / file_path).resolve()
        if not path.exists():
            return False

        text = path.read_text(encoding="utf-8", errors="ignore")
        if "datetime.utcnow(" not in text:
            return False

        # Update import
        updated_text = text
        if re.search(r"from datetime import .*datetime", text):
            if "timezone" not in text:
                updated_text = re.sub(
                    r"from datetime import ([^\n]+)",
                    lambda m: m.group(0).replace("datetime", "datetime, timezone")
                    if "timezone" not in m.group(0) else m.group(0),
                    updated_text,
                    count=1
                )
            updated_text = updated_text.replace(
                "datetime.utcnow()", "datetime.now(timezone.utc)"
            )
        else:
            # Fallback for `import datetime`
            updated_text = updated_text.replace(
                "datetime.utcnow()", "datetime.datetime.now(datetime.timezone.utc)"
            )

        if updated_text == text:
            return False

        if not live_allowed:
            self.logger.info(f"Dry-run: would update {file_path}")
            return False

        path.write_text(updated_text, encoding="utf-8")
        return True

    def _create_file(self, file_path: str, content: str, live_allowed: bool) -> bool:
        """Create a new file with content."""
        path = (self.project_root / file_path).resolve()
        
        if not live_allowed:
            self.logger.info(f"Dry-run: would create {file_path}")
            return True # Pretend success for dry-run validation

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            self.logger.info(f"Created file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create file {file_path}: {e}")
            return False
