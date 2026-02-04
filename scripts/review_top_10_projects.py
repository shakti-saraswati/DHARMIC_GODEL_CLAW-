#!/usr/bin/env python3
"""
Review TOP 10 Projects Script
Runs every 4 hours to review project status and suggest next actions.
"""

import yaml
from pathlib import Path
from datetime import datetime

def review_projects():
    """Review TOP 10 projects and generate report."""
    config_path = Path.home() / "DHARMIC_GODEL_CLAW/config/top_10_projects.yaml"
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    projects = config.get('projects', [])
    
    print("="*70)
    print(f"TOP 10 PROJECTS REVIEW - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    for p in projects:
        status_emoji = "🟢" if "active" in p['status'].lower() else "🟡" if "pending" in p['status'].lower() else "🔴"
        print(f"\n{status_emoji} {p['id']}: {p['name']}")
        print(f"   Status: {p['status']}")
        print(f"   Next: {p['next_action']}")
        print(f"   Location: {p['location']}")
    
    print("\n" + "="*70)
    print("RECOMMENDATION: Focus on projects with 🔴 status first")
    print("="*70)

if __name__ == "__main__":
    review_projects()
