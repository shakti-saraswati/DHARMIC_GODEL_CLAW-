#!/usr/bin/env python3
"""
Moltbook Bridge Setup Helper
============================

Prerequisites for DGC-Moltbook integration:

1. Moltbook API credentials
   - Get from: https://moltbook.com/developer
   - Store in: ~/.moltbook/credentials.json
   
2. Agent account
   - Create dedicated DGC agent account
   - Or use existing account with appropriate permissions

3. Environment variables:
   export MOLTBOOK_API_KEY="your_key_here"
   export MOLTBOOK_AGENT_ID="dharmic_claw"

Usage:
    python3 setup_moltbook_bridge.py --check
    python3 setup_moltbook_bridge.py --configure
"""

import json
import os
from pathlib import Path

def check_credentials():
    """Check if Moltbook credentials are configured."""
    creds_path = Path.home() / ".moltbook" / "credentials.json"
    
    results = {
        "credentials_file": creds_path.exists(),
        "api_key_env": bool(os.getenv("MOLTBOOK_API_KEY")),
        "agent_id_env": bool(os.getenv("MOLTBOOK_AGENT_ID")),
        "ready": False
    }
    
    if creds_path.exists():
        try:
            with open(creds_path) as f:
                creds = json.load(f)
                results["has_api_key"] = bool(creds.get("api_key"))
                results["has_agent_id"] = bool(creds.get("agent_id"))
        except:
            results["error"] = "Invalid JSON in credentials file"
    
    results["ready"] = (
        results.get("has_api_key", False) or results["api_key_env"]
    ) and (
        results.get("has_agent_id", False) or results["agent_id_env"]
    )
    
    return results

def configure_credentials():
    """Interactive credential setup."""
    creds_dir = Path.home() / ".moltbook"
    creds_dir.mkdir(exist_ok=True)
    
    print("DGC Moltbook Bridge Configuration")
    print("=" * 40)
    print()
    print("Get your API key from: https://moltbook.com/developer")
    print()
    
    api_key = input("Moltbook API Key: ").strip()
    agent_id = input("Agent ID [dharmic_claw]: ").strip() or "dharmic_claw"
    
    creds = {
        "api_key": api_key,
        "agent_id": agent_id,
        "api_endpoint": "https://api.moltbook.com/v1",
        "configured_at": str(Path.home() / ".moltbook" / "credentials.json")
    }
    
    creds_path = creds_dir / "credentials.json"
    with open(creds_path, 'w') as f:
        json.dump(creds, f, indent=2)
    
    os.chmod(creds_path, 0o600)  # Restrict permissions
    
    print(f"\n✅ Credentials saved to: {creds_path}")
    print(f"   Agent ID: {agent_id}")
    print()
    print("The Moltbook bridge is now ready to use.")
    print("Run: python3 -c 'from dgc_moltbook_bridge import DGCOnMoltbook; ...'")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--configure":
        configure_credentials()
    else:
        print("Checking Moltbook credentials...")
        results = check_credentials()
        
        if results["ready"]:
            print("✅ Moltbook bridge is configured and ready")
        else:
            print("❌ Moltbook bridge needs configuration")
            print()
            print("Missing:")
            if not results.get("has_api_key") and not results["api_key_env"]:
                print("  - API key (file or environment)")
            if not results.get("has_agent_id") and not results["agent_id_env"]:
                print("  - Agent ID (file or environment)")
            print()
            print("Run: python3 setup_moltbook_bridge.py --configure")
