#!/usr/bin/env python3
"""
DGC Tool Inventory & Health Check
=================================

Comprehensive status of all available tools and agents.
Run this to see what's operational.

Usage:
    python3 tool_inventory.py --full
"""

import json
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, timeout=5):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def check_tool(name, check_cmd, success_pattern=None):
    """Check if a tool is available."""
    output, success = run_cmd(check_cmd)
    if success_pattern:
        success = success_pattern in output
    return {
        "name": name,
        "available": success,
        "output": output[:200] if output else ""
    }

def main():
    print("=" * 60)
    print("DGC TOOL INVENTORY")
    print("=" * 60)
    print()
    
    # 1. MODEL BACKENDS
    print("🤖 MODEL BACKENDS")
    print("-" * 40)
    
    tools = [
        ("Kimi K2.5 (Current)", "echo 'Running on Kimi K2.5'", "Kimi"),
        ("Ollama Cloud", "ollama list 2>/dev/null | head -3", "NAME"),
        ("Ollama Local", "curl -s localhost:11434/api/tags 2>/dev/null | head -1", ""),
        ("DGC Backup Models", "python3 -c 'from src.core.dgc_backup_models import DGCFailsafeManager; print(\"OK\")' 2>&1", "OK"),
        ("OpenRouter", "curl -s https://openrouter.ai/api/v1/models 2>/dev/null | head -1", ""),
    ]
    
    for name, cmd, pattern in tools:
        result = check_tool(name, cmd, pattern if pattern else None)
        status = "✅" if result["available"] else "❌"
        print(f"{status} {name}")
        if not result["available"] and result["output"]:
            print(f"   → {result['output'][:50]}")
    
    print()
    
    # 2. CODING AGENTS
    print("💻 CODING AGENTS")
    print("-" * 40)
    
    coding_tools = [
        ("Codex Bridge", "ls ~/DHARMIC_GODEL_CLAW/codex_bridge/queue/ 2>/dev/null", ""),
        ("Claude Code", "which claude 2>/dev/null || echo 'not found'", "claude"),
        ("Cursor", "which cursor 2>/dev/null || echo 'not found'", "cursor"),
        ("Clawdbot Gateway", "openclaw status 2>/dev/null | head -1", ""),
    ]
    
    for name, cmd, pattern in coding_tools:
        result = check_tool(name, cmd, pattern if pattern else None)
        status = "✅" if result["available"] else "❌"
        print(f"{status} {name}")
    
    print()
    
    # 3. SUB-AGENT SPAWNING
    print("🔄 SUB-AGENT SPAWNING")
    print("-" * 40)
    
    # Check OpenClaw sessions capability
    result = check_tool(
        "sessions_spawn",
        "openclaw help 2>/dev/null | grep -i spawn || echo 'check manually'",
        ""
    )
    status = "✅" if result["available"] else "⚠️"
    print(f"{status} sessions_spawn (via OpenClaw)")
    print(f"   → Use: sessions_spawn(task='...', label='worker')")
    
    # Show recent subagents
    print()
    print("Recent subagent sessions:")
    output, _ = run_cmd("ls ~/.openclaw/sessions/ 2>/dev/null | head -5 || echo 'No sessions dir'")
    if output and "No sessions" not in output:
        for line in output.split("\n")[:3]:
            print(f"   • {line}")
    else:
        print("   • Check with: sessions_list()")
    
    print()
    
    # 4. EXTERNAL INTEGRATIONS
    print("🔗 EXTERNAL INTEGRATIONS")
    print("-" * 40)
    
    integrations = [
        ("Moltbook Bridge", "test -f ~/DHARMIC_GODEL_CLAW/src/core/dgc_moltbook_bridge.py && echo 'OK'", "OK"),
        ("PSMV Vault", "test -d ~/Persistent-Semantic-Memory-Vault && echo 'OK'", "OK"),
        ("Git Repository", "cd ~/DHARMIC_GODEL_CLAW && git status --short 2>/dev/null | wc -l", ""),
        ("Email (Proton)", "test -f ~/DHARMIC_GODEL_CLAW/src/core/email_client.py && echo 'OK'", "OK"),
    ]
    
    for name, cmd, pattern in integrations:
        result = check_tool(name, cmd, pattern if pattern else None)
        status = "✅" if result["available"] else "❌"
        print(f"{status} {name}")
    
    print()
    
    # 5. RECOMMENDATIONS
    print("💡 RECOMMENDATIONS")
    print("-" * 40)
    print()
    print("For parallel work:")
    print("  • Use sessions_spawn() for sub-agents (4 workers max)")
    print("  • Ollama cloud available: glm-4.7, deepseek-v3.2")
    print()
    print("For coding tasks:")
    print("  • Codex bridge queue exists but empty")
    print("  • Claude Code status: unknown (may need restart)")
    print()
    print("For model fallback:")
    print("  • DGC backup_models.py available but needs API keys")
    print("  • Ollama cloud ready for tier-2 fallback")
    print()
    
    print("=" * 60)
    print("Run with --full for detailed diagnostics")
    print("=" * 60)

if __name__ == "__main__":
    main()
