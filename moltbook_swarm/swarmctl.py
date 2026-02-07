#!/usr/bin/env python3
"""
MOLTBOOK SWARM CONTROL
======================
CLI for OpenClaw and human operators to control the swarm.

Usage:
    python swarmctl.py status          # Show swarm status
    python swarmctl.py pause           # Pause the swarm
    python swarmctl.py resume          # Resume the swarm
    python swarmctl.py start           # Start via launchd
    python swarmctl.py stop            # Stop via launchd
    python swarmctl.py restart         # Restart the swarm
    python swarmctl.py logs [n]        # Show last n log lines
    python swarmctl.py observations    # Show latest observations
    python swarmctl.py focus <submolt> # Focus on a specific submolt
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SWARM_DIR = Path(__file__).parent
STATE_FILE = SWARM_DIR / "state.json"
MEMORY_DIR = SWARM_DIR / "memory"
LOGS_DIR = Path.home() / "Desktop" / "MOLTBOOK_AGENT_LOGS"
LAUNCHD_PLIST = Path.home() / "Library/LaunchAgents/com.dharmic.moltbook-swarm.plist"


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(updates: dict):
    state = load_state()
    state.update(updates)
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def cmd_status():
    """Show swarm status."""
    state = load_state()

    print("=" * 50)
    print("MOLTBOOK SWARM STATUS")
    print("=" * 50)
    print(f"Status:     {state.get('status', 'unknown')}")
    print(f"PID:        {state.get('pid', 'N/A')}")
    print(f"Started:    {state.get('started_at', 'N/A')}")
    print(f"Last Cycle: {state.get('last_cycle', 'N/A')}")
    print(f"Cycles:     {state.get('cycles_completed', 0)}")
    print()

    directives = state.get("directives", {})
    print("DIRECTIVES:")
    print(f"  Paused:       {directives.get('paused', False)}")
    print(f"  Focus:        {directives.get('focus_submolt', 'all')}")
    print(f"  Style:        {directives.get('engagement_style', 'balanced')}")
    print()

    # Check if actually running
    result = subprocess.run(["pgrep", "-f", "orchestrator.py"], capture_output=True)
    if result.returncode == 0:
        pids = result.stdout.decode().strip().split('\n')
        print(f"Active PIDs: {', '.join(pids)}")
    else:
        print("Active PIDs: NONE (swarm not running)")
    print("=" * 50)


def cmd_pause():
    """Pause the swarm."""
    state = load_state()
    directives = state.get("directives", {})
    directives["paused"] = True
    save_state({"directives": directives})
    print("Swarm paused. Will stop after current cycle.")


def cmd_resume():
    """Resume the swarm."""
    state = load_state()
    directives = state.get("directives", {})
    directives["paused"] = False
    save_state({"directives": directives})
    print("Swarm resumed.")


def cmd_start():
    """Start swarm via launchd."""
    if not LAUNCHD_PLIST.exists():
        print(f"ERROR: launchd plist not found at {LAUNCHD_PLIST}")
        return
    subprocess.run(["launchctl", "load", str(LAUNCHD_PLIST)])
    print("Swarm started via launchd.")
    save_state({"status": "starting"})


def cmd_stop():
    """Stop swarm via launchd."""
    subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST)], capture_output=True)
    subprocess.run(["pkill", "-f", "orchestrator.py"], capture_output=True)
    print("Swarm stopped.")
    save_state({"status": "stopped", "pid": None})


def cmd_restart():
    """Restart the swarm."""
    cmd_stop()
    import time
    time.sleep(2)
    cmd_start()


def cmd_logs(n: int = 30):
    """Show last n log lines."""
    log_file = LOGS_DIR / "swarm_activity.log"
    if log_file.exists():
        result = subprocess.run(["tail", f"-{n}", str(log_file)], capture_output=True)
        print(result.stdout.decode())
    else:
        print("No logs found.")


def cmd_observations():
    """Show latest observations."""
    obs_file = MEMORY_DIR / "latest_observations.json"
    if obs_file.exists():
        with open(obs_file) as f:
            data = json.load(f)

        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        print()

        observations = data.get("observations", [])
        for obs in observations:
            quality = obs.get("quality", "?")
            agent = obs.get("agent_name", "?")
            title = obs.get("thread_title", "?")
            rec = obs.get("recommendation", "?")
            print(f"[{quality}/10] {agent}: {title}")
            print(f"         Recommendation: {rec}")
            print()
    else:
        print("No observations found.")


def cmd_focus(submolt: str):
    """Focus on a specific submolt."""
    state = load_state()
    directives = state.get("directives", {})
    directives["focus_submolt"] = submolt if submolt != "all" else None
    save_state({"directives": directives})
    print(f"Focus set to: {submolt}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "status":
        cmd_status()
    elif cmd == "pause":
        cmd_pause()
    elif cmd == "resume":
        cmd_resume()
    elif cmd == "start":
        cmd_start()
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "restart":
        cmd_restart()
    elif cmd == "logs":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        cmd_logs(n)
    elif cmd == "observations":
        cmd_observations()
    elif cmd == "focus":
        if len(sys.argv) < 3:
            print("Usage: swarmctl.py focus <submolt|all>")
            return
        cmd_focus(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
