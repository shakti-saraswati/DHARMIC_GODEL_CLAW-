#!/usr/bin/env python3
"""
INTEGRATION TEST - Make the whole system sing
=============================================

Tests all inter-vault coordination points:
1. DGC Core Agent status
2. Skill Bridge → Registry sync
3. Delegation Router → Backend availability
4. Memory systems (Strange Loop + Mem0)
5. PSMV/Residual Stream connectivity
6. Clawdbot Gateway status

Run: python3 integration_test.py
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def check(name: str, success: bool, detail: str = ""):
    status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
    print(f"  {status} {name}" + (f" - {detail}" if detail else ""))
    return success

def section(name: str):
    print(f"\n{YELLOW}=== {name} ==={RESET}")

def run_integration_tests():
    """Run all integration tests."""
    results = []
    
    # === 1. DGC Core Agent ===
    section("1. DGC CORE AGENT")
    try:
        # Run dharmic_agent.py status command
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "dharmic_agent.py"), "status"],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout + result.stderr
        results.append(check("DGC agent responds", "cycle" in output.lower() or "fitness" in output.lower() or "STATUS" in output, output[:100]))
    except Exception as e:
        results.append(check("DGC agent responds", False, str(e)[:50]))
    
    # === 2. Skill Bridge ===
    section("2. SKILL BRIDGE")
    try:
        from skill_bridge import SkillBridge
        bridge = SkillBridge()
        reg = bridge.sync_registry()
        results.append(check("Skill registry sync", reg["discovered"] > 0, f"{reg['discovered']} skills"))
        
        # Check for key skills
        skill_names = reg.get("skills", [])
        results.append(check("agentic-ai skill exists", any("agentic" in s.lower() for s in skill_names)))
        results.append(check("dgc skill exists", any("dgc" in s.lower() for s in skill_names)))
    except Exception as e:
        results.append(check("Skill bridge", False, str(e)[:50]))
    
    # === 3. Delegation Router ===
    section("3. DELEGATION ROUTER")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
        from delegation_router import DelegationRouter
        router = DelegationRouter()
        backends = router.get_available_backends()
        results.append(check("Router initialized", True, f"{len(backends)} backends"))
        
        # Check each backend
        backend_names = [b.value for b in backends]
        results.append(check("Kimi backend", "kimi" in backend_names))
        results.append(check("Claude CLI backend", "claude-cli" in backend_names))
        results.append(check("Clawdbot backend", "clawdbot" in backend_names))
    except Exception as e:
        results.append(check("Delegation router", False, str(e)[:50]))
    
    # === 4. Memory Systems ===
    section("4. MEMORY SYSTEMS")
    try:
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(Path(__file__).parent.parent / "memory")
        status = memory.get_status()
        results.append(check("Strange loop memory", True, f"obs={status.get('observation_count', 0)}"))
    except Exception as e:
        results.append(check("Strange loop memory", False, str(e)[:50]))
    
    try:
        from mem0_memory import Mem0Memory
        mem0 = Mem0Memory()
        results.append(check("Mem0 memory layer", True))
    except Exception as e:
        results.append(check("Mem0 memory layer", False, str(e)[:50]))
    
    # === 5. PSMV / Residual Stream ===
    section("5. PSMV / RESIDUAL STREAM")
    psmv_path = Path.home() / "Persistent-Semantic-Memory-Vault"
    results.append(check("PSMV exists", psmv_path.exists()))
    
    residual_stream = psmv_path / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"
    if residual_stream.exists():
        files = list(residual_stream.glob("*.md"))
        recent = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        results.append(check("Residual stream active", len(files) > 0, f"{len(files)} files"))
        if recent:
            latest = recent[0].name
            results.append(check("Recent contribution", True, latest[:40]))
    else:
        results.append(check("Residual stream exists", False))
    
    # === 6. Clawdbot Gateway ===
    section("6. CLAWDBOT GATEWAY")
    try:
        # Try multiple paths for clawdbot
        clawdbot_paths = [
            "clawdbot",
            str(Path.home() / ".npm-global" / "bin" / "clawdbot"),
            "/usr/local/bin/clawdbot",
        ]
        for cb_path in clawdbot_paths:
            try:
                result = subprocess.run([cb_path, "status"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 or "Gateway" in result.stdout:
                    results.append(check("Clawdbot gateway", True, "running"))
                    break
            except FileNotFoundError:
                continue
        else:
            # Also try via node
            result = subprocess.run(["node", str(Path.home() / ".npm-global" / "lib" / "node_modules" / "clawdbot" / "bin" / "cli.mjs"), "status"], 
                                  capture_output=True, text=True, timeout=10)
            results.append(check("Clawdbot gateway", "Gateway" in result.stdout or result.returncode == 0, result.stdout[:50]))
    except Exception as e:
        results.append(check("Clawdbot gateway", False, str(e)[:50]))
    
    # === 7. Codex Bridge ===
    section("7. CODEX BRIDGE")
    bridge_queue = Path.home() / "DHARMIC_GODEL_CLAW" / "ops" / "bridge" / "bridge_queue.py"
    results.append(check("Bridge queue exists", bridge_queue.exists()))
    
    bridge_outbox = Path.home() / "DHARMIC_GODEL_CLAW" / "ops" / "bridge" / "outbox"
    if bridge_outbox.exists():
        completed = list(bridge_outbox.glob("*.json"))
        results.append(check("Bridge has completed tasks", len(completed) > 0, f"{len(completed)} tasks"))
    else:
        results.append(check("Bridge outbox exists", False))
    
    # === 8. Unified Daemon ===
    section("8. UNIFIED DAEMON")
    heartbeat_log = Path(__file__).parent.parent / "logs" / "unified_daemon" / f"heartbeat_{datetime.now().strftime('%Y%m%d')}.jsonl"
    if heartbeat_log.exists():
        lines = heartbeat_log.read_text().strip().split('\n')
        if lines:
            last = json.loads(lines[-1])
            hb_num = last.get("heartbeat_number", 0)
            results.append(check("Unified daemon heartbeats", True, f"#{hb_num}"))
    else:
        results.append(check("Unified daemon heartbeats", False, "no log today"))
    
    # === SUMMARY ===
    section("SUMMARY")
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n  {passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n  {GREEN}🎯 ALL SYSTEMS SINGING!{RESET}")
    elif passed > total * 0.7:
        print(f"\n  {YELLOW}⚠️  MOSTLY OPERATIONAL - some gaps{RESET}")
    else:
        print(f"\n  {RED}❌ CRITICAL GAPS - needs attention{RESET}")
    
    return passed == total

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
