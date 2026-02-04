#!/usr/bin/env python3
"""
DHARMIC_CLAW Autonomous Coding Protocol v3 - Gate Runner

This is the non-bypassable gate execution engine.
CI is the ultimate authority - no merge without this passing.

Usage:
    python -m swarm.run_gates [--proposal-id ID] [--dry-run] [--emergency --reason REASON --approver NAME]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

GATES_CONFIG = Path(__file__).parent / "gates.yaml"
EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"
EMERGENCY_LOG = Path(__file__).parent.parent / "logs" / "emergency_bypass.jsonl"

class GateResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
    ERROR = "error"

class GateTier(Enum):
    ABSOLUTE = "absolute"      # Dharmic tier A - never bypass
    REQUIRED = "required"      # Must pass
    STRONG = "strong"          # Dharmic tier B
    ADVISORY = "advisory"      # Dharmic tier C - warn only

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GateEvidence:
    """Evidence artifact from a gate run."""
    gate_id: int
    gate_name: str
    result: str
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = field(default_factory=list)
    error_message: str = ""

@dataclass
class GateRunResult:
    """Complete result of running all gates."""
    proposal_id: str
    timestamp: str
    overall_result: str
    gates_passed: int
    gates_failed: int
    gates_warned: int
    gates_skipped: int
    total_duration_seconds: float
    gate_results: list[dict]
    evidence_bundle_hash: str
    emergency_bypass: bool = False
    emergency_reason: str = ""
    emergency_approver: str = ""

# =============================================================================
# GATE RUNNER
# =============================================================================

class GateRunner:
    """
    Executes gates in order and collects evidence.
    
    This class is the sole authority on gate execution.
    CODE_GUARDIAN uses this; CODING_AGENT cannot modify it.
    """
    
    def __init__(self, config_path: Path = GATES_CONFIG):
        self.config_path = config_path
        self.config = self._load_config()
        self.evidence: list[GateEvidence] = []
        self.proposal_id: str = ""
        self.dry_run: bool = False
        
    def _load_config(self) -> dict:
        """Load and validate gates configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Gates config not found: {self.config_path}")
        
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required = ["version", "gates", "enforcement"]
        for section in required:
            if section not in config:
                raise ValueError(f"Missing required config section: {section}")
        
        return config
    
    def run_all_gates(
        self,
        proposal_id: str,
        dry_run: bool = False,
        emergency: bool = False,
        emergency_reason: str = "",
        emergency_approver: str = ""
    ) -> GateRunResult:
        """
        Execute all gates in sequence.
        
        Args:
            proposal_id: Unique identifier for this proposal
            dry_run: If True, simulate but don't execute
            emergency: If True, run in emergency bypass mode
            emergency_reason: Required if emergency=True
            emergency_approver: Required if emergency=True
        
        Returns:
            GateRunResult with complete evidence bundle
        """
        self.proposal_id = proposal_id
        self.dry_run = dry_run
        
        # Emergency bypass validation
        if emergency:
            if not emergency_reason or not emergency_approver:
                raise ValueError("Emergency bypass requires --reason and --approver")
            self._log_emergency(emergency_reason, emergency_approver)
        
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        passed = 0
        failed = 0
        warned = 0
        skipped = 0
        
        print(f"\n{'='*60}")
        print(f"DHARMIC_CLAW Gate Runner v3")
        print(f"Proposal: {proposal_id}")
        print(f"Timestamp: {timestamp}")
        print(f"Mode: {'DRY-RUN' if dry_run else 'EMERGENCY' if emergency else 'STANDARD'}")
        print(f"{'='*60}\n")
        
        for gate in self.config["gates"]:
            gate_id = gate["id"]
            gate_name = gate["name"]
            gate_tier = gate.get("tier", "required")
            
            # Check if gate can be skipped in emergency
            if emergency and gate_tier not in ["absolute", "required"]:
                print(f"[{gate_id:02d}] {gate_name}: SKIPPED (emergency bypass)")
                skipped += 1
                self.evidence.append(GateEvidence(
                    gate_id=gate_id,
                    gate_name=gate_name,
                    result=GateResult.SKIP.value,
                    duration_seconds=0,
                    error_message="Skipped due to emergency bypass"
                ))
                continue
            
            # Run the gate
            evidence = self._run_single_gate(gate)
            self.evidence.append(evidence)
            
            # Count results
            if evidence.result == GateResult.PASS.value:
                passed += 1
                status = "✓ PASS"
            elif evidence.result == GateResult.FAIL.value:
                failed += 1
                status = "✗ FAIL"
            elif evidence.result == GateResult.WARN.value:
                warned += 1
                status = "⚠ WARN"
            else:
                skipped += 1
                status = "○ SKIP"
            
            print(f"[{gate_id:02d}] {gate_name}: {status} ({evidence.duration_seconds:.2f}s)")
        
        # Check ML overlay
        if self._should_apply_ml_overlay():
            print("\n--- ML Overlay Gates ---")
            ml_results = self._run_ml_overlay()
            for ev in ml_results:
                self.evidence.append(ev)
                if ev.result == GateResult.PASS.value:
                    passed += 1
                elif ev.result == GateResult.FAIL.value:
                    failed += 1
        
        total_duration = time.time() - start_time
        
        # Determine overall result
        if failed > 0:
            overall = "FAIL"
        elif warned > 0:
            overall = "WARN"
        else:
            overall = "PASS"
        
        # Create evidence bundle
        evidence_hash = self._create_evidence_bundle()
        
        result = GateRunResult(
            proposal_id=proposal_id,
            timestamp=timestamp,
            overall_result=overall,
            gates_passed=passed,
            gates_failed=failed,
            gates_warned=warned,
            gates_skipped=skipped,
            total_duration_seconds=total_duration,
            gate_results=[asdict(e) for e in self.evidence],
            evidence_bundle_hash=evidence_hash,
            emergency_bypass=emergency,
            emergency_reason=emergency_reason,
            emergency_approver=emergency_approver
        )
        
        # Save results
        self._save_results(result)
        
        print(f"\n{'='*60}")
        print(f"OVERALL: {overall}")
        print(f"Passed: {passed} | Failed: {failed} | Warned: {warned} | Skipped: {skipped}")
        print(f"Duration: {total_duration:.2f}s")
        print(f"Evidence Hash: {evidence_hash[:16]}...")
        print(f"{'='*60}\n")
        
        return result
    
    def _run_single_gate(self, gate: dict) -> GateEvidence:
        """Execute a single gate and collect evidence."""
        gate_id = gate["id"]
        gate_name = gate["name"]
        timeout = gate.get("timeout_seconds", 60)
        on_failure = gate.get("on_failure", "block")
        
        start_time = time.time()
        
        if self.dry_run:
            return GateEvidence(
                gate_id=gate_id,
                gate_name=gate_name,
                result=GateResult.SKIP.value,
                duration_seconds=0,
                error_message="Dry run - gate not executed"
            )
        
        # Get command(s) to run
        commands = gate.get("commands", [])
        if not commands and "command" in gate:
            commands = [gate["command"]]
        
        if not commands:
            # This is a dharmic gate - use evaluator
            return self._run_dharmic_gate(gate)
        
        # Execute technical gate
        all_stdout = []
        all_stderr = []
        artifacts = []
        
        try:
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=Path(__file__).parent.parent
                )
                all_stdout.append(result.stdout)
                all_stderr.append(result.stderr)
                
                if result.returncode != 0:
                    duration = time.time() - start_time
                    gate_result = GateResult.WARN if on_failure == "warn" else GateResult.FAIL
                    return GateEvidence(
                        gate_id=gate_id,
                        gate_name=gate_name,
                        result=gate_result.value,
                        duration_seconds=duration,
                        stdout="\n".join(all_stdout),
                        stderr="\n".join(all_stderr),
                        artifacts=artifacts,
                        error_message=f"Command failed with exit code {result.returncode}"
                    )
            
            # Collect evidence artifacts
            for artifact in gate.get("evidence", []):
                artifact_path = Path(__file__).parent.parent / artifact
                if artifact_path.exists():
                    artifacts.append(str(artifact_path))
            
            duration = time.time() - start_time
            return GateEvidence(
                gate_id=gate_id,
                gate_name=gate_name,
                result=GateResult.PASS.value,
                duration_seconds=duration,
                stdout="\n".join(all_stdout),
                stderr="\n".join(all_stderr),
                artifacts=artifacts
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return GateEvidence(
                gate_id=gate_id,
                gate_name=gate_name,
                result=GateResult.FAIL.value,
                duration_seconds=duration,
                error_message=f"Gate timed out after {timeout}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            return GateEvidence(
                gate_id=gate_id,
                gate_name=gate_name,
                result=GateResult.ERROR.value,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _run_dharmic_gate(self, gate: dict) -> GateEvidence:
        """Execute a dharmic gate (non-technical evaluation)."""
        gate_id = gate["id"]
        gate_name = gate["name"]
        check_type = gate.get("check_type", "manual")
        on_failure = gate.get("on_failure", "block")
        
        start_time = time.time()
        
        # Check for required files
        required_files = gate.get("required_files", [])
        missing_files = []
        
        for req_file in required_files:
            # Handle spec.yaml:field syntax
            if ":" in req_file:
                file_part, field_part = req_file.split(":", 1)
                file_path = Path(__file__).parent.parent / file_part
                if file_path.exists():
                    try:
                        with open(file_path) as f:
                            data = yaml.safe_load(f)
                        if field_part not in data:
                            missing_files.append(f"{file_part} (missing field: {field_part})")
                    except Exception:
                        missing_files.append(f"{file_part} (invalid yaml)")
                else:
                    missing_files.append(file_part)
            else:
                file_path = Path(__file__).parent.parent / req_file
                if not file_path.exists():
                    missing_files.append(req_file)
        
        duration = time.time() - start_time
        
        if missing_files:
            gate_result = GateResult.WARN if on_failure == "warn" else GateResult.FAIL
            return GateEvidence(
                gate_id=gate_id,
                gate_name=gate_name,
                result=gate_result.value,
                duration_seconds=duration,
                error_message=f"Missing required files: {', '.join(missing_files)}"
            )
        
        # For CONSENT gate, check for approval record
        if gate_name == "CONSENT" and gate.get("requires_human", False):
            approval_file = Path(__file__).parent.parent / "evidence" / self.proposal_id / "consent_record.json"
            if not approval_file.exists():
                return GateEvidence(
                    gate_id=gate_id,
                    gate_name=gate_name,
                    result=GateResult.FAIL.value,
                    duration_seconds=duration,
                    error_message="Human approval required but not found"
                )
        
        return GateEvidence(
            gate_id=gate_id,
            gate_name=gate_name,
            result=GateResult.PASS.value,
            duration_seconds=duration
        )
    
    def _should_apply_ml_overlay(self) -> bool:
        """Check if ML overlay gates should be applied."""
        ml_config = self.config.get("ml_overlay", {})
        if not ml_config.get("enabled", False):
            return False
        
        # Check triggers
        triggers = ml_config.get("triggers", [])
        # For now, return False - implement file scanning later
        return False
    
    def _run_ml_overlay(self) -> list[GateEvidence]:
        """Run ML-specific gates."""
        return []  # Implement when ML code is present
    
    def _create_evidence_bundle(self) -> str:
        """Create and hash the evidence bundle."""
        evidence_dir = EVIDENCE_DIR / self.proposal_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Serialize all evidence
        bundle = {
            "proposal_id": self.proposal_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "evidence": [asdict(e) for e in self.evidence]
        }
        
        # Save bundle
        bundle_path = evidence_dir / "evidence_bundle.json"
        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2)
        
        # Compute hash
        bundle_json = json.dumps(bundle, sort_keys=True)
        bundle_hash = hashlib.sha256(bundle_json.encode()).hexdigest()
        
        # Save hash
        hash_path = evidence_dir / "evidence_hash.sha256"
        with open(hash_path, "w") as f:
            f.write(bundle_hash)
        
        return bundle_hash
    
    def _save_results(self, result: GateRunResult) -> None:
        """Save gate results to file."""
        evidence_dir = EVIDENCE_DIR / self.proposal_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        results_path = evidence_dir / "gate_results.json"
        with open(results_path, "w") as f:
            json.dump(asdict(result), f, indent=2)
    
    def _log_emergency(self, reason: str, approver: str) -> None:
        """Log emergency bypass to separate audit trail."""
        EMERGENCY_LOG.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proposal_id": self.proposal_id,
            "reason": reason,
            "approver": approver,
            "action": "emergency_bypass_invoked"
        }
        
        with open(EMERGENCY_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        print(f"\n⚠️  EMERGENCY BYPASS LOGGED")
        print(f"   Reason: {reason}")
        print(f"   Approver: {approver}")
        print(f"   POST-MORTEM REQUIRED\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="DHARMIC_CLAW Gate Runner v3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Standard run
    python -m swarm.run_gates --proposal-id PROP-001
    
    # Dry run
    python -m swarm.run_gates --proposal-id PROP-001 --dry-run
    
    # Emergency bypass (break-glass)
    python -m swarm.run_gates --proposal-id PROP-001 --emergency \\
        --reason "Production down" --approver dhyana
        """
    )
    
    parser.add_argument(
        "--proposal-id",
        required=True,
        help="Unique proposal identifier"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without executing gates"
    )
    parser.add_argument(
        "--emergency",
        action="store_true",
        help="Emergency bypass mode (skips non-critical gates)"
    )
    parser.add_argument(
        "--reason",
        help="Reason for emergency bypass (required with --emergency)"
    )
    parser.add_argument(
        "--approver",
        help="Human approver name (required with --emergency)"
    )
    
    args = parser.parse_args()
    
    # Validate emergency args
    if args.emergency and (not args.reason or not args.approver):
        parser.error("--emergency requires both --reason and --approver")
    
    # Run gates
    runner = GateRunner()
    result = runner.run_all_gates(
        proposal_id=args.proposal_id,
        dry_run=args.dry_run,
        emergency=args.emergency,
        emergency_reason=args.reason or "",
        emergency_approver=args.approver or ""
    )
    
    # Exit with appropriate code
    if result.overall_result == "FAIL":
        sys.exit(1)
    elif result.overall_result == "WARN":
        sys.exit(0)  # Warnings don't block
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
