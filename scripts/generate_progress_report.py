#!/usr/bin/env python3
"""
Generate Daily Progress Report
Runs at 6 AM to summarize what was built overnight.
"""

from pathlib import Path
from datetime import datetime, timedelta

def generate_report():
    """Generate overnight progress report."""
    residual_stream = Path.home() / "Persistent-Semantic-Memory-Vault/AGENT_EMERGENT_WORKSPACES/residual_stream"
    
    # Get files from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    recent_files = []
    
    for f in residual_stream.glob("*.md"):
        if f.stat().st_mtime > yesterday.timestamp():
            recent_files.append(f)
    
    # Sort by modification time
    recent_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("="*70)
    print(f"OVERNIGHT PROGRESS REPORT - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*70)
    print(f"\nFiles created/modified: {len(recent_files)}")
    
    for f in recent_files[:10]:  # Top 10 most recent
        content = f.read_text()
        # Extract title or first line
        title = content.split('\n')[0] if content else "No title"
        print(f"\n📄 {f.name}")
        print(f"   {title[:80]}...")
    
    print("\n" + "="*70)
    print("The swarm worked through the night.")
    print("="*70)

if __name__ == "__main__":
    generate_report()
