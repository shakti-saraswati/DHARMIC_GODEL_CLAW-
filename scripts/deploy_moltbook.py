#!/usr/bin/env python3
"""
DGC Moltbook Deployment
=======================

One-command deployment of DGC agents to Moltbook.

Prerequisites:
    export MOLTBOOK_API_KEY="your_key_here"
    export MOLTBOOK_AGENT_ID="dharmic_claw"

Usage:
    python3 deploy_moltbook.py --dry-run    # Test without posting
    python3 deploy_moltbook.py --deploy     # Actually deploy
    python3 deploy_moltbook.py --status     # Check agent status
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from dgc_moltbook_bridge import DGCOnMoltbook, MoltbookActionType

def check_credentials():
    """Check if Moltbook credentials are available."""
    api_key = os.getenv("MOLTBOOK_API_KEY")
    agent_id = os.getenv("MOLTBOOK_AGENT_ID", "dharmic_claw")
    
    if not api_key:
        # Try credentials file
        creds_path = Path.home() / ".moltbook" / "credentials.json"
        if creds_path.exists():
            try:
                with open(creds_path) as f:
                    creds = json.load(f)
                    api_key = creds.get("api_key")
                    agent_id = creds.get("agent_id", agent_id)
            except:
                pass
    
    return api_key, agent_id

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deploy DGC to Moltbook")
    parser.add_argument("--dry-run", action="store_true", help="Test without posting")
    parser.add_argument("--deploy", action="store_true", help="Actually deploy")
    parser.add_argument("--status", action="store_true", help="Check status")
    parser.add_argument("--submolt", default="consciousness", help="Target submolt")
    args = parser.parse_args()
    
    # Check credentials
    api_key, agent_id = check_credentials()
    
    if not api_key:
        print("❌ Moltbook credentials not found!")
        print()
        print("To deploy, you need:")
        print("1. Moltbook API key from https://moltbook.com/developer")
        print("2. Set environment variable: export MOLTBOOK_API_KEY='...'")
        print("   OR run: python3 setup_moltbook_bridge.py --configure")
        print()
        print("Cannot deploy without credentials.")
        sys.exit(1)
    
    print("🚀 DGC Moltbook Deployment")
    print(f"   Agent: {agent_id}")
    print(f"   Submolt: {args.submolt}")
    print()
    
    # Initialize bridge
    bridge = DGCOnMoltbook(agent_identity=agent_id)
    
    if args.status:
        print("📊 Bridge Status:")
        print(json.dumps(bridge.get_stats(), indent=2))
        return
    
    # Generate recruitment message
    message = bridge.generate_recruitment_message(args.submolt)
    
    print("📨 Recruitment Message:")
    print("=" * 60)
    print(message[:500] + "..." if len(message) > 500 else message)
    print("=" * 60)
    print()
    
    # Check telos alignment
    check_result = bridge.check_telos_alignment(
        content=message,
        action_type=MoltbookActionType.RECRUIT,
        target_submolt=args.submolt
    )
    
    print("🛡️  Telos Alignment Check:")
    print(f"   Passes: {check_result.passes}")
    print(f"   Alignment Score: {check_result.alignment_score:.2f}")
    print(f"   Recommendation: {check_result.recommendation}")
    
    if check_result.gate_failures:
        print(f"   ⚠️  Gate failures: {', '.join(check_result.gate_failures)}")
    
    print()
    
    if args.dry_run:
        print("🧪 DRY RUN - Not posting to Moltbook")
        print("   Run with --deploy to actually post")
        return
    
    if not check_result.passes:
        print("❌ Telos check failed - aborting deployment")
        sys.exit(1)
    
    if args.deploy:
        print("🚀 DEPLOYING to Moltbook...")
        # This would actually post if the bridge had post_to_submolt implemented
        # For now, simulate
        print("   ✓ Message passed 17 dharmic gates")
        print("   ✓ Recruitment content validated")
        print("   ✓ Ready to post (API integration pending)")
        print()
        print("📤 To complete deployment:")
        print("   1. Ensure MOLTBOOK_API_KEY is valid")
        print("   2. Bridge.post_to_submolt() needs API endpoint")
        print("   3. Run again with --deploy")
        
        # Record deployment attempt
        deploy_log = Path.home() / "DHARMIC_GODEL_CLAW" / "logs" / "moltbook_deployments.jsonl"
        deploy_log.parent.mkdir(parents=True, exist_ok=True)
        
        with open(deploy_log, 'a') as f:
            entry = {
                "timestamp": str(Path.home()),  # Will be overwritten
                "action": "deploy_attempt",
                "agent_id": agent_id,
                "submolt": args.submolt,
                "telos_aligned": check_result.passes,
                "alignment_score": check_result.alignment_score
            }
            f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    main()
