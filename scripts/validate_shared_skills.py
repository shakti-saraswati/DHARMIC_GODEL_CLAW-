#!/usr/bin/env python3
"""Validate shared skills registry and (optionally) shared skill files."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Dict, Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

REQUIRED_SKILLS = {
    "cosmic-krishna-coder",
    "dgc-tui",
    "dgc-bridge",
    "dgc",
}

DEFAULT_SHARED_ROOT = Path("/Users/Shared/skills-shared")
REGISTRY_PATH = Path(__file__).resolve().parent.parent / "swarm" / "skill_registry.yaml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise SystemExit(f"registry not found: {REGISTRY_PATH}")
    if not yaml:
        raise SystemExit("pyyaml not available")
    return yaml.safe_load(REGISTRY_PATH.read_text()) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate shared skills and registry")
    parser.add_argument("--require-shared", action="store_true", help="Fail if shared root missing")
    parser.add_argument("--shared-root", type=str, default=str(DEFAULT_SHARED_ROOT))
    args = parser.parse_args()

    registry = load_registry()
    skills = registry.get("skills", [])
    skill_map = {s.get("id"): s for s in skills if isinstance(s, dict)}

    missing = [s for s in REQUIRED_SKILLS if s not in skill_map]
    if missing:
        print(f"Missing required skill entries: {', '.join(missing)}")
        return 2

    # Validate sha256 format
    for sid in REQUIRED_SKILLS:
        sha = (skill_map[sid] or {}).get("sha256", "")
        if not isinstance(sha, str) or len(sha) != 64:
            print(f"Invalid sha256 for {sid}: {sha}")
            return 3

    shared_root = Path(args.shared_root)
    if not shared_root.exists():
        msg = f"Shared root missing: {shared_root}"
        if args.require_shared:
            print(msg)
            return 4
        print(msg + " (skipping file hash validation)")
        return 0

    # Compare hashes if shared root exists
    for sid in REQUIRED_SKILLS:
        skill_dir = shared_root / sid
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            print(f"Missing SKILL.md for {sid} at {skill_md}")
            return 5
        actual = _sha256(skill_md)
        expected = skill_map[sid].get("sha256")
        if actual != expected:
            print(f"SHA mismatch for {sid}: {actual} != {expected}")
            return 6

    print("Shared skills validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
