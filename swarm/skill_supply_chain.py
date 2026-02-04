#!/usr/bin/env python3
"""
Skill supply-chain scanner.

Scans registered skill files for suspicious installer patterns such as
curl|bash, base64 decode piped to shell, and raw IP downloads.
Produces a JSON report and exits nonzero if policy thresholds are met.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

REGISTRY_PATH = Path(__file__).parent / "skill_registry.yaml"
POLICY_PATH = Path(__file__).parent / "policy" / "skill_supply_chain.yaml"
EVIDENCE_PATH = Path(__file__).parent.parent / "skill_supply_chain_report.json"


@dataclass
class PatternRule:
    rule_id: str
    regex: str
    severity: str
    description: str = ""


@dataclass
class Finding:
    rule_id: str
    severity: str
    description: str
    match: str


@dataclass
class FileScan:
    path: str
    sha256: str
    findings: List[Finding] = field(default_factory=list)


@dataclass
class SkillScanResult:
    skill_id: str
    path: str
    exists: bool
    sha256: str = ""
    findings: List[Finding] = field(default_factory=list)
    files: List[FileScan] = field(default_factory=list)
    missing_reason: str = ""


def _load_policy() -> dict:
    if POLICY_PATH.exists():
        return yaml.safe_load(POLICY_PATH.read_text()) or {}
    return {}


def _load_registry(registry_path: Path) -> dict:
    if registry_path.exists():
        return yaml.safe_load(registry_path.read_text()) or {}
    return {}


def _expand_path(path_str: str) -> Path:
    return Path(os.path.expanduser(path_str)).resolve()


def _is_binary(content: bytes) -> bool:
    return b"\x00" in content


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _compile_rules(policy: dict) -> List[PatternRule]:
    rules = []
    for entry in policy.get("patterns", []) or []:
        rules.append(PatternRule(
            rule_id=str(entry.get("id", "rule")),
            regex=str(entry.get("regex", "")),
            severity=str(entry.get("severity", "medium")),
            description=str(entry.get("description", "")),
        ))
    return rules


def _iter_target_files(path: Path, include_siblings: bool, extensions: List[str]) -> Iterable[Path]:
    if path.is_file():
        yield path
        if include_siblings:
            sibling_dir = path.parent / "scripts"
            if sibling_dir.exists() and sibling_dir.is_dir():
                for ext in extensions:
                    yield from sibling_dir.rglob(f"*{ext}")
        return
    if path.is_dir():
        for ext in extensions:
            yield from path.rglob(f"*{ext}")


def _scan_text(text: str, compiled: List[Tuple[PatternRule, re.Pattern]]) -> List[Finding]:
    findings: List[Finding] = []
    for rule, regex in compiled:
        for match in regex.finditer(text):
            snippet = match.group(0)
            snippet = snippet.replace("\n", " ")
            if len(snippet) > 180:
                snippet = snippet[:177] + "..."
            findings.append(Finding(
                rule_id=rule.rule_id,
                severity=rule.severity,
                description=rule.description,
                match=snippet,
            ))
            break
    return findings


def scan_skills(
    registry_path: Path = REGISTRY_PATH,
    policy_path: Path = POLICY_PATH,
    extra_paths: Optional[List[Path]] = None,
    quarantine_dir: Optional[Path] = None,
    quarantine_on_fail: bool = False,
) -> dict:
    policy = _load_policy()
    registry = _load_registry(registry_path)

    include_siblings = bool(policy.get("scan", {}).get("include_sibling_scripts", True))
    extensions = policy.get("scan", {}).get("extensions", [".md", ".sh", ".py", ".txt"])
    fail_on = set(policy.get("fail_on", ["high"]))

    rules = _compile_rules(policy)
    compiled_rules: List[Tuple[PatternRule, re.Pattern]] = []
    for rule in rules:
        if not rule.regex:
            continue
        compiled_rules.append((rule, re.compile(rule.regex, re.IGNORECASE | re.MULTILINE)))

    results: List[SkillScanResult] = []
    missing = 0
    severity_counts = {"high": 0, "medium": 0, "low": 0}

    entries = list(registry.get("skills", []) or [])
    for path in extra_paths or []:
        entries.append({"id": f"extra:{path.name}", "path": str(path)})

    for skill in entries:
        skill_id = str(skill.get("id", "unknown"))
        raw_path = skill.get("path", "")
        if not raw_path:
            results.append(SkillScanResult(skill_id=skill_id, path="", exists=False, missing_reason="no path"))
            missing += 1
            continue
        path = _expand_path(raw_path)
        if not path.exists():
            results.append(SkillScanResult(skill_id=skill_id, path=str(path), exists=False, missing_reason="missing"))
            missing += 1
            continue

        skill_findings: List[Finding] = []
        file_scans: List[FileScan] = []
        file_hashes: List[str] = []
        for target in _iter_target_files(path, include_siblings, extensions):
            try:
                content = target.read_bytes()
            except Exception:
                continue
            file_hashes.append(_sha256_bytes(content))
            if _is_binary(content):
                continue
            text = content.decode("utf-8", errors="ignore")
            findings = _scan_text(text, compiled_rules)
            if findings:
                file_scans.append(FileScan(
                    path=str(target),
                    sha256=_sha256_bytes(content),
                    findings=findings,
                ))
                skill_findings.extend(findings)

        sha256 = file_hashes[0] if file_hashes else ""
        for finding in skill_findings:
            if finding.severity in severity_counts:
                severity_counts[finding.severity] += 1
        results.append(SkillScanResult(
            skill_id=skill_id,
            path=str(path),
            exists=True,
            sha256=sha256,
            findings=skill_findings,
            files=file_scans,
        ))

    report = {
        "scanned_at": time.time(),
        "registry_path": str(registry_path),
        "policy_path": str(policy_path),
        "skills_scanned": len(results),
        "skills_missing": missing,
        "severity_counts": severity_counts,
        "results": [
            {
                **asdict(r),
                "findings": [asdict(f) for f in (r.findings or [])],
                "files": [
                    {
                        **asdict(f),
                        "findings": [asdict(fd) for fd in (f.findings or [])],
                    }
                    for f in (r.files or [])
                ],
            }
            for r in results
        ],
    }

    EVIDENCE_PATH.write_text(json.dumps(report, indent=2))

    should_fail = False
    for result in results:
        for finding in result.findings or []:
            if finding.severity in fail_on:
                should_fail = True
                break
        if should_fail:
            break

    quarantined: List[Dict[str, Any]] = []
    if quarantine_dir and (quarantine_on_fail and should_fail):
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            for file_scan in result.files or []:
                if not any(f.severity in fail_on for f in (file_scan.findings or [])):
                    continue
                src = Path(file_scan.path)
                if not src.exists():
                    continue
                dest_name = f\"{result.skill_id.replace(':', '_')}__{src.name}__{file_scan.sha256[:12]}\"\n                dest = quarantine_dir / dest_name\n                try:\n                    shutil.copy2(src, dest)\n                    quarantined.append({\n                        \"skill_id\": result.skill_id,\n                        \"source\": str(src),\n                        \"dest\": str(dest),\n                        \"sha256\": file_scan.sha256,\n                    })\n                except Exception:\n                    continue\n+\n+    report[\"quarantine\"] = {\n+        \"enabled\": bool(quarantine_dir),\n+        \"dir\": str(quarantine_dir) if quarantine_dir else \"\",\n+        \"quarantined_files\": quarantined,\n+    }\n+\n+    return {\"report\": report, \"should_fail\": should_fail, \"quarantined\": quarantined}


def main() -> None:
    parser = argparse.ArgumentParser(description="Skill supply-chain scanner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Scan skills for supply-chain red flags")
    scan.add_argument("--registry", default=str(REGISTRY_PATH), help="Path to skill registry YAML")
    scan.add_argument("--policy", default=str(POLICY_PATH), help="Path to supply-chain policy YAML")
    scan.add_argument("--paths", nargs="*", default=[], help="Extra files or folders to scan")
    scan.add_argument("--quarantine-dir", default="", help="Directory to copy flagged files into")
    scan.add_argument("--quarantine-on-fail", action="store_true", help="Quarantine when a failing severity is detected")

    args = parser.parse_args()

    if args.cmd == "scan":
        extra = [Path(p).expanduser().resolve() for p in args.paths]
        quarantine_dir = Path(args.quarantine_dir).expanduser().resolve() if args.quarantine_dir else None
        out = scan_skills(
            Path(args.registry),
            Path(args.policy),
            extra_paths=extra,
            quarantine_dir=quarantine_dir,
            quarantine_on_fail=args.quarantine_on_fail,
        )
        if out["should_fail"]:
            raise SystemExit(1)
        return


if __name__ == "__main__":
    main()
