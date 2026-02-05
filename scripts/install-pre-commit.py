#!/usr/bin/env python3
"""
Install the dharmic pre-commit hook.

Usage:
    python scripts/install-pre-commit.py
    
Or manually:
    cp scripts/pre-commit-gates .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""

import shutil
import stat
from pathlib import Path


def main():
    repo_root = Path(__file__).parent.parent
    source = repo_root / "scripts" / "pre-commit-gates"
    target = repo_root / ".git" / "hooks" / "pre-commit"
    
    if not source.exists():
        print(f"❌ Source not found: {source}")
        return 1
    
    # Ensure hooks directory exists
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing hook if present
    if target.exists():
        backup = target.with_suffix(".backup")
        shutil.copy(target, backup)
        print(f"📦 Backed up existing hook to: {backup}")
    
    # Copy hook
    shutil.copy(source, target)
    
    # Make executable
    target.chmod(target.stat().st_mode | stat.S_IEXEC)
    
    print(f"✅ Pre-commit hook installed: {target}")
    print("\n🔒 Security gates will now run before every commit:")
    print("   • AHIMSA (bandit security scan)")
    print("   • SECRETS (hardcoded key detection)")
    print("   • VULNERABILITY (dependency audit)")
    print("\n💡 To bypass (NOT RECOMMENDED): git commit --no-verify")
    
    return 0


if __name__ == "__main__":
    exit(main())
