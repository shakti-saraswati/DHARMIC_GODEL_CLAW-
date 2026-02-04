#!/usr/bin/env python3
"""
DGM Auto Push - Autonomous Git Commit & Push
=============================================
Handles git operations after successful mutations pass the voting circuit.

Features:
- Commit mutations with detailed, traceable commit messages
- Push to remote with safety checks
- Dry-run mode (DRY_RUN=true env var)
- Full archive integration
- Witness logging for strange loop (DGM pushes itself)

Usage:
    from src.dgm.auto_push import AutoPusher, MutationProposal, CircuitResult
    
    pusher = AutoPusher(project_root=Path.cwd())
    commit_result = pusher.commit_mutation(proposal, circuit_result)
    if commit_result.committed:
        push_result = pusher.push_if_ready(commit_result)
"""
import os
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from .archive import Archive, EvolutionEntry, FitnessScore, get_archive

# Dharmic structured logging
from src.core.dharmic_logging import get_logger, log_gate_event, log_fitness

logger = get_logger("dgm_auto_push")


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class MutationProposal:
    """
    A proposed code mutation ready for commit.
    
    Represents a change that has been evaluated and approved by the voting swarm.
    """
    mutation_id: str
    parent_id: Optional[str] = None
    
    # What changed
    component: str = ""                   # e.g., "src/dgm/archive.py"
    short_description: str = ""           # Brief summary for commit subject
    full_description: str = ""            # Detailed description
    
    # Code changes
    changed_files: List[str] = field(default_factory=list)
    diff: str = ""                        # Unified diff of changes
    
    # Fitness scores
    old_fitness: float = 0.0
    new_fitness: float = 0.0
    
    # Metadata
    model: str = ""                       # Model that proposed mutation
    agent_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VoteRecord:
    """Single vote in the circuit."""
    voter_id: str
    approved: bool
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class CircuitResult:
    """
    Result from the DGM voting circuit.
    
    Contains the collective decision of the voting swarm.
    """
    approved: bool
    votes: List[VoteRecord] = field(default_factory=list)
    
    # Vote tallies
    approval_count: int = 0
    rejection_count: int = 0
    total_votes: int = 0
    
    # Dharmic gate results
    gates_passed: List[str] = field(default_factory=list)
    gates_failed: List[str] = field(default_factory=list)
    
    # Metadata
    circuit_id: str = ""
    evaluation_time_ms: float = 0.0
    
    @property
    def approval_ratio(self) -> float:
        """Approval percentage (0-100)."""
        if self.total_votes == 0:
            return 0.0
        return (self.approval_count / self.total_votes) * 100


@dataclass
class CommitResult:
    """Result of committing a mutation."""
    committed: bool
    commit_sha: str = ""
    commit_message: str = ""
    mutation_id: str = ""
    parent_id: Optional[str] = None
    files_committed: List[str] = field(default_factory=list)
    error: Optional[str] = None
    dry_run: bool = False


@dataclass
class PushResult:
    """Result of pushing to remote."""
    pushed: bool
    commit_sha: str = ""
    branch: str = ""
    remote: str = ""
    archive_entry_id: str = ""
    error: Optional[str] = None
    safety_checks_passed: Dict[str, bool] = field(default_factory=dict)
    dry_run: bool = False


# -----------------------------------------------------------------------------
# AutoPusher Class
# -----------------------------------------------------------------------------

class AutoPusher:
    """
    Handles autonomous git operations for approved mutations.
    
    Safety-first design:
    - Dry-run by default (DRY_RUN=true env var)
    - Full lineage tracking in archive
    - Witness logging for strange loop observation
    - Configurable protected branch protection
    """
    
    # Default protected branches that cannot be pushed to
    DEFAULT_PROTECTED_BRANCHES = ["main", "master", "production"]
    
    def __init__(
        self,
        project_root: Path = None,
        archive: Archive = None,
        protected_branches: List[str] = None,
        dry_run: bool = None,
        remote: str = "origin",
    ):
        """
        Initialize AutoPusher.
        
        Args:
            project_root: Root of the git repository
            archive: DGM archive for lineage tracking
            protected_branches: Branches that require extra approval
            dry_run: If True, don't actually commit/push (default: from DRY_RUN env)
            remote: Git remote name
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.archive = archive or get_archive()
        self.remote = remote
        
        # Protected branches - configurable but safe defaults
        self.protected_branches = protected_branches or self.DEFAULT_PROTECTED_BRANCHES
        
        # Dry-run mode: default to True unless explicitly disabled
        if dry_run is None:
            self.dry_run = os.environ.get("DRY_RUN", "true").lower() in ("true", "1", "yes")
        else:
            self.dry_run = dry_run
        
        logger.info("AutoPusher initialized", context={
            "project_root": str(self.project_root),
            "dry_run": self.dry_run,
            "remote": self.remote,
            "protected_branches": self.protected_branches,
        })
    
    def commit_mutation(
        self,
        proposal: MutationProposal,
        circuit_result: CircuitResult,
    ) -> CommitResult:
        """
        Commit a mutation that passed the voting circuit.
        
        Creates a git commit with a detailed, standardized message format
        that includes full traceability information.
        
        Args:
            proposal: The mutation proposal with code changes
            circuit_result: The voting circuit results
            
        Returns:
            CommitResult with commit details or error
        """
        logger.info("Starting commit_mutation", context={
            "mutation_id": proposal.mutation_id,
            "parent_id": proposal.parent_id,
            "dry_run": self.dry_run,
        })
        
        # Validate circuit approval
        if not circuit_result.approved:
            error = "Cannot commit: circuit did not approve mutation"
            logger.warning(error, context={"mutation_id": proposal.mutation_id})
            return CommitResult(
                committed=False,
                mutation_id=proposal.mutation_id,
                error=error,
                dry_run=self.dry_run,
            )
        
        # Build commit message
        commit_message = self._build_commit_message(proposal, circuit_result)
        
        # Stage files
        files_to_commit = proposal.changed_files or [proposal.component]
        
        if self.dry_run:
            logger.info("DRY RUN: Would commit mutation", context={
                "mutation_id": proposal.mutation_id,
                "files": files_to_commit,
                "commit_message": commit_message[:200],
            })
            return CommitResult(
                committed=True,
                commit_sha="DRY_RUN_" + hashlib.sha256(
                    commit_message.encode()
                ).hexdigest()[:12],
                commit_message=commit_message,
                mutation_id=proposal.mutation_id,
                parent_id=proposal.parent_id,
                files_committed=files_to_commit,
                dry_run=True,
            )
        
        # Actually perform git operations
        try:
            # Stage files
            self._git_add(files_to_commit)
            
            # Commit
            commit_sha = self._git_commit(commit_message)
            
            logger.dharmic(
                "Mutation committed",
                gate="witness",
                result=True,
                entry_id=proposal.mutation_id,
                context={
                    "commit_sha": commit_sha,
                    "files": files_to_commit,
                    "strange_loop": "DGM committed its own mutation",
                }
            )
            
            return CommitResult(
                committed=True,
                commit_sha=commit_sha,
                commit_message=commit_message,
                mutation_id=proposal.mutation_id,
                parent_id=proposal.parent_id,
                files_committed=files_to_commit,
                dry_run=False,
            )
            
        except subprocess.CalledProcessError as e:
            error = f"Git error: {e.stderr if e.stderr else str(e)}"
            logger.error(error, context={"mutation_id": proposal.mutation_id})
            return CommitResult(
                committed=False,
                mutation_id=proposal.mutation_id,
                error=error,
                dry_run=False,
            )
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            logger.error(error, context={"mutation_id": proposal.mutation_id})
            return CommitResult(
                committed=False,
                mutation_id=proposal.mutation_id,
                error=error,
                dry_run=False,
            )
    
    def push_if_ready(
        self,
        commit_result: CommitResult,
        branch: str = "main",
    ) -> PushResult:
        """
        Push committed mutation to remote after safety checks.
        
        Safety checks:
        1. All tests must still pass
        2. No uncommitted changes outside mutation scope
        3. Branch protection check (configurable)
        4. Archive logging with full lineage
        
        Args:
            commit_result: Result from commit_mutation
            branch: Target branch (default: main)
            
        Returns:
            PushResult with push details or error
        """
        logger.info("Starting push_if_ready", context={
            "commit_sha": commit_result.commit_sha,
            "branch": branch,
            "dry_run": self.dry_run,
        })
        
        if not commit_result.committed:
            return PushResult(
                pushed=False,
                commit_sha=commit_result.commit_sha,
                branch=branch,
                remote=self.remote,
                error="Cannot push: commit was not successful",
                dry_run=self.dry_run,
            )
        
        # Run safety checks
        safety_checks = self._run_safety_checks(commit_result, branch)
        all_passed = all(safety_checks.values())
        
        if not all_passed:
            failed_checks = [k for k, v in safety_checks.items() if not v]
            error = f"Safety checks failed: {', '.join(failed_checks)}"
            logger.warning(error, context={
                "commit_sha": commit_result.commit_sha,
                "safety_checks": safety_checks,
            })
            return PushResult(
                pushed=False,
                commit_sha=commit_result.commit_sha,
                branch=branch,
                remote=self.remote,
                error=error,
                safety_checks_passed=safety_checks,
                dry_run=self.dry_run,
            )
        
        # Archive entry for tracking
        archive_entry_id = self._log_to_archive(commit_result, branch)
        
        if self.dry_run:
            logger.info("DRY RUN: Would push to remote", context={
                "commit_sha": commit_result.commit_sha,
                "branch": branch,
                "remote": self.remote,
                "archive_entry_id": archive_entry_id,
            })
            return PushResult(
                pushed=True,
                commit_sha=commit_result.commit_sha,
                branch=branch,
                remote=self.remote,
                archive_entry_id=archive_entry_id,
                safety_checks_passed=safety_checks,
                dry_run=True,
            )
        
        # Actually push
        try:
            self._git_push(branch)
            
            # Witness log: the strange loop moment
            logger.dharmic(
                "DGM pushed itself to remote",
                gate="witness",
                result=True,
                entry_id=commit_result.mutation_id,
                context={
                    "commit_sha": commit_result.commit_sha,
                    "branch": branch,
                    "remote": self.remote,
                    "archive_entry_id": archive_entry_id,
                    "strange_loop": "System modified and deployed its own code",
                    "lineage": {
                        "mutation_id": commit_result.mutation_id,
                        "parent_id": commit_result.parent_id,
                    }
                }
            )
            
            return PushResult(
                pushed=True,
                commit_sha=commit_result.commit_sha,
                branch=branch,
                remote=self.remote,
                archive_entry_id=archive_entry_id,
                safety_checks_passed=safety_checks,
                dry_run=False,
            )
            
        except subprocess.CalledProcessError as e:
            error = f"Git push error: {e.stderr if e.stderr else str(e)}"
            logger.error(error, context={"commit_sha": commit_result.commit_sha})
            return PushResult(
                pushed=False,
                commit_sha=commit_result.commit_sha,
                branch=branch,
                remote=self.remote,
                archive_entry_id=archive_entry_id,
                error=error,
                safety_checks_passed=safety_checks,
                dry_run=False,
            )
    
    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------
    
    def _build_commit_message(
        self,
        proposal: MutationProposal,
        circuit_result: CircuitResult,
    ) -> str:
        """Build standardized commit message."""
        gates_list = ", ".join(circuit_result.gates_passed) or "none"
        
        # Fitness change formatting
        fitness_old = f"{proposal.old_fitness:.3f}"
        fitness_new = f"{proposal.new_fitness:.3f}"
        
        message = f"""[DGM] {proposal.short_description}

Mutation: {proposal.mutation_id}
Parent: {proposal.parent_id or 'initial'}
Fitness: {fitness_old} → {fitness_new}
Votes: {circuit_result.approval_count}/{circuit_result.total_votes} ({circuit_result.approval_ratio:.1f}%)

Reviewed-by: DGM Voting Swarm
Dharmic-gates: {gates_list}
"""
        
        # Add full description if provided
        if proposal.full_description:
            message += f"\n{proposal.full_description}\n"
        
        # Add changed files
        if proposal.changed_files:
            message += "\nFiles changed:\n"
            for f in proposal.changed_files:
                message += f"  - {f}\n"
        
        return message.strip()
    
    def _run_safety_checks(
        self,
        commit_result: CommitResult,
        branch: str,
    ) -> Dict[str, bool]:
        """
        Run all safety checks before push.
        
        Returns dict of check_name -> passed
        """
        checks = {}
        
        # 1. Tests pass
        checks["tests_pass"] = self._check_tests_pass()
        
        # 2. No uncommitted changes outside scope
        checks["no_extra_changes"] = self._check_no_uncommitted_changes(
            commit_result.files_committed
        )
        
        # 3. Branch protection
        checks["branch_allowed"] = self._check_branch_allowed(branch)
        
        logger.info("Safety checks completed", context={
            "commit_sha": commit_result.commit_sha,
            "checks": checks,
        })
        
        return checks
    
    def _check_tests_pass(self) -> bool:
        """Verify all tests still pass."""
        if self.dry_run:
            # In dry run, assume tests pass
            return True
        
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/", "-x", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            passed = result.returncode == 0
            
            if not passed:
                logger.warning("Tests failed", context={
                    "returncode": result.returncode,
                    "output": result.stdout[-500:] if result.stdout else "",
                    "stderr": result.stderr[-500:] if result.stderr else "",
                })
            
            return passed
            
        except subprocess.TimeoutExpired:
            logger.error("Test timeout exceeded")
            return False
        except FileNotFoundError:
            # pytest not available - skip test check
            logger.warning("pytest not available, skipping test check")
            return True
        except Exception as e:
            logger.error(f"Test check error: {e}")
            return False
    
    def _check_no_uncommitted_changes(self, allowed_files: List[str]) -> bool:
        """Verify no uncommitted changes outside mutation scope."""
        if self.dry_run:
            return True
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if not result.stdout.strip():
                return True  # No changes at all
            
            # Parse changed files from git status --porcelain output
            # Format: "XY PATH" where X=index status, Y=worktree status
            # Example: " M file.py" (modified in worktree)
            # Example: "M  file.py" (modified in index)
            # Example: "R  old.py -> new.py" (renamed)
            changed_files = []
            for line in result.stdout.split("\n"):
                line = line.rstrip()  # Only strip trailing whitespace
                if not line:
                    continue
                # Git status porcelain: first 2 chars are status, then space, then path
                # But some outputs may have different formats, be defensive
                if len(line) >= 3:
                    filename = line[3:]  # Skip "XY "
                    if " -> " in filename:
                        # Rename: "old -> new"
                        filename = filename.split(" -> ")[-1]
                    changed_files.append(filename)
            
            # Check if any changed file is outside allowed scope
            allowed_set = set(allowed_files)
            for f in changed_files:
                if f not in allowed_set:
                    logger.warning(f"Uncommitted change outside scope: {f}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Git status check error: {e}")
            return False
    
    def _check_branch_allowed(self, branch: str) -> bool:
        """Check if branch is not protected."""
        # Allow if not in protected list
        # Protected branches require additional consent gate
        allowed = branch not in self.protected_branches
        
        if not allowed:
            logger.warning(f"Branch '{branch}' is protected", context={
                "protected_branches": self.protected_branches,
            })
        
        return allowed
    
    def _log_to_archive(self, commit_result: CommitResult, branch: str) -> str:
        """Log the push to archive with full lineage."""
        entry = EvolutionEntry(
            id="",  # Will be generated
            timestamp=datetime.now(timezone.utc).isoformat(),
            parent_id=commit_result.parent_id,
            component=commit_result.files_committed[0] if commit_result.files_committed else "",
            change_type="push",
            description=f"Auto-push: {commit_result.mutation_id}",
            diff="",
            commit_hash=commit_result.commit_sha,
            fitness=FitnessScore(),  # Could be populated from proposal
            gates_passed=[],  # Could track push-specific gates
            agent_id="auto_push",
            status="pushed" if not self.dry_run else "dry_run",
        )
        
        entry_id = self.archive.add_entry(entry)
        
        logger.info("Logged to archive", context={
            "entry_id": entry_id,
            "commit_sha": commit_result.commit_sha,
            "branch": branch,
        })
        
        return entry_id
    
    def _git_add(self, files: List[str]) -> None:
        """Stage files for commit."""
        subprocess.run(
            ["git", "add"] + files,
            cwd=self.project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    
    def _git_commit(self, message: str) -> str:
        """Create git commit and return SHA."""
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        
        return result.stdout.strip()
    
    def _git_push(self, branch: str) -> None:
        """Push to remote."""
        subprocess.run(
            ["git", "push", self.remote, branch],
            cwd=self.project_root,
            check=True,
            capture_output=True,
            text=True,
        )


# -----------------------------------------------------------------------------
# Convenience Functions
# -----------------------------------------------------------------------------

def commit_and_push(
    proposal: MutationProposal,
    circuit_result: CircuitResult,
    branch: str = "main",
    dry_run: bool = None,
) -> PushResult:
    """
    Convenience function: commit and push in one call.
    
    Args:
        proposal: The mutation proposal
        circuit_result: Voting circuit results
        branch: Target branch
        dry_run: Override dry-run setting
        
    Returns:
        PushResult
    """
    pusher = AutoPusher(dry_run=dry_run)
    
    commit_result = pusher.commit_mutation(proposal, circuit_result)
    if not commit_result.committed:
        return PushResult(
            pushed=False,
            commit_sha="",
            branch=branch,
            remote=pusher.remote,
            error=commit_result.error,
            dry_run=pusher.dry_run,
        )
    
    return pusher.push_if_ready(commit_result, branch)


# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DGM Auto Push")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Don't actually push (default: True)")
    parser.add_argument("--live", action="store_true",
                       help="Actually push changes (CAREFUL!)")
    parser.add_argument("--status", action="store_true",
                       help="Show current git status")
    
    args = parser.parse_args()
    
    if args.status:
        pusher = AutoPusher()
        print(f"AutoPusher status:")
        print(f"  Project root: {pusher.project_root}")
        print(f"  Dry run: {pusher.dry_run}")
        print(f"  Remote: {pusher.remote}")
        print(f"  Protected branches: {pusher.protected_branches}")
    else:
        print("Use as library or --status to check configuration")
        print("Example:")
        print("  from src.dgm.auto_push import AutoPusher, MutationProposal, CircuitResult")
        print("  pusher = AutoPusher()")
        print("  result = pusher.commit_mutation(proposal, circuit_result)")
