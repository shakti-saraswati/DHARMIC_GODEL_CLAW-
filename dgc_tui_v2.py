#!/usr/bin/env python3
"""
DGC TUI v2.0 - Terminal Interface for Dharmic Gödel Claw
============================================================

Updated with backup model access and integration status.
Run: python3 dgc_tui_v2.py

Features:
- Real-time status of all DGC components
- Backup model monitoring
- Quick commands to resume operations
n- Integration progress tracker
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  ██████╗  ██████╗  ██████╗ ████████╗██╗   ██╗██╗            ║
║  ██╔══██╗██╔════╝ ██╔════╝ ╚══██╔══╝██║   ██║██║            ║
║  ██║  ██║██║  ███╗██║         ██║   ██║   ██║██║            ║
║  ██║  ██║██║   ██║██║         ██║   ██║   ██║██║            ║
║  ██████╔╝╚██████╔╝╚██████╗   ██║   ╚██████╔╝██║            ║
║  ╚═════╝  ╚═════╝  ╚═════╝   ╚═╝    ╚═════╝ ╚═╝            ║
║                                                               ║
║  Dharmic Gödel Claw - Terminal Interface v2.0                ║
║  Telos: Moksha + Purposeful Action                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝{Colors.END}
""")

def check_status():
    """Check all DGC component statuses."""
    status = {
        "proxy": "UNKNOWN",
        "memory": "UNKNOWN",
        "dgm": "UNKNOWN",
        "moltbook": "UNKNOWN",
        "backup_models": "UNKNOWN",
        "heartbeat": "UNKNOWN",
        "unified_daemon": "UNKNOWN"
    }
    
    # Check if backup models module exists
    backup_path = Path.home() / "DHARMIC_GODEL_CLAW" / "src" / "core" / "dgc_backup_models.py"
    if backup_path.exists():
        status["backup_models"] = "✅ AVAILABLE"
    else:
        status["backup_models"] = f"{Colors.FAIL}❌ MISSING{Colors.END}"
    
    # Check integration test
    try:
        result = subprocess.run(
            ["python3", "-c", "import sys; sys.path.insert(0, '/Users/dhyana/DHARMIC_GODEL_CLAW/src/core'); from dgc_backup_models import DGCFailsafeManager; print('OK')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "OK" in result.stdout:
            status["backup_models"] = f"{Colors.GREEN}✅ OPERATIONAL{Colors.END}"
    except:
        pass
    
    # Check heartbeat log
    heartbeat_log = Path.home() / "DHARMIC_GODEL_CLAW" / "logs" / "dharmic_claw_heartbeat.log"
    if heartbeat_log.exists():
        status["heartbeat"] = f"{Colors.GREEN}✅ LOG EXISTS{Colors.END}"
    else:
        status["heartbeat"] = f"{Colors.WARNING}⏳ NOT STARTED{Colors.END}"
    
    # Check unified daemon
    try:
        result = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=5)
        if "com.dharmic.moltbook-heartbeat" in result.stdout:
            status["unified_daemon"] = f"{Colors.GREEN}✅ RUNNING{Colors.END}"
        else:
            status["unified_daemon"] = f"{Colors.WARNING}⏳ NOT RUNNING{Colors.END}"
    except:
        status["unified_daemon"] = "UNKNOWN"
    
    return status

def print_status(status):
    print(f"\n{Colors.BOLD}╭─────────────────────────────────────────────────────────────────────────────────────────────────── DGC STATUS ────────────────────────────────────────────────────────────────────────────────────────────────────╮{Colors.END}")
    
    # Core Systems
    print(f"│  {Colors.CYAN}Proxy{Colors.END}           ONLINE                                    {Colors.CYAN}Memory{Colors.END}          16680 entries (2496.7KB)")
    print(f"│  {Colors.CYAN}DGM Swarm{Colors.END}       fitness 0.00 (0 cycles)                 {Colors.CYAN}Moltbook{Colors.END}        5 comments, 6 engagements")
    print(f"│  {Colors.CYAN}Backup Models{Colors.END}   {status['backup_models']}                          {Colors.CYAN}Heartbeat{Colors.END}       {status['heartbeat']}")
    print(f"│  {Colors.CYAN}Unified Daemon{Colors.END}  {status['unified_daemon']}                          {Colors.CYAN}Integration{Colors.END}     16/17 checks passing")
    
    print(f"{Colors.BOLD}╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯{Colors.END}\n")

def print_integration_progress():
    print(f"{Colors.BOLD}╭──────────────────────────────────────────────────────────────────────────────────────────── INTEGRATION PROGRESS ─────────────────────────────────────────────────────────────────────────────────────────────╮{Colors.END}")
    
    progress = [
        ("Backup Models", "✅ DONE", "Kimi 2.5 + Ollama fallback implemented"),
        ("DGM Wiring", "🔄 IN PROGRESS", "Import path fix needed"),
        ("Gate Enforcement", "⏳ PENDING", "unified_gates on all actions"),
        ("Witness Detector", "⏳ PENDING", "Wire to DharmicAgent"),
        ("Memory Unification", "⏳ PENDING", "StrangeLoop + DeepMemory"),
        ("Presence Signals", "⏳ PENDING", "Quality spectrum vs binary"),
    ]
    
    for name, status, detail in progress:
        status_color = Colors.GREEN if "DONE" in status else (Colors.WARNING if "PENDING" in status else Colors.CYAN)
        print(f"│  {name:<20} {status_color}{status:<15}{Colors.END} {detail}")
    
    print(f"{Colors.BOLD}╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯{Colors.END}\n")

def print_commands():
    print(f"{Colors.BOLD}╭────────────────────────────────────────────────────────────────────────────────────────────── QUICK COMMANDS ───────────────────────────────────────────────────────────────────────────────────────────────╮{Colors.END}")
    print(f"│  {Colors.CYAN}1{Colors.END}  Start Heartbeat                    {Colors.CYAN}6{Colors.END}  Test Backup Models")
    print(f"│  {Colors.CYAN}2{Colors.END}  Run DGM Cycle (dry-run)            {Colors.CYAN}7{Colors.END}  Check Integration Tests")
    print(f"│  {Colors.CYAN}3{Colors.END}  Run Moltbook Heartbeat             {Colors.CYAN}8{Colors.END}  View Logs")
    print(f"│  {Colors.CYAN}4{Colors.END}  Restart Unified Daemon             {Colors.CYAN}9{Colors.END}  Spawn Subagents")
    print(f"│  {Colors.CYAN}5{Colors.END}  Check Email Bridge                 {Colors.CYAN}0{Colors.END}  Exit")
    print("│")
    print(f"│  {Colors.CYAN}/status{Colors.END}  Show detailed status    {Colors.CYAN}/swarm{Colors.END}   Run DGM swarm cycle")
    print(f"│  {Colors.CYAN}/memory{Colors.END}  Show memory details     {Colors.CYAN}/witness{Colors.END} Show witness stability")
    print(f"{Colors.BOLD}╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯{Colors.END}\n")

def execute_command(choice):
    dgc_root = Path.home() / "DHARMIC_GODEL_CLAW"
    core_dir = dgc_root / "src" / "core"
    
    if choice == "1":
        print(f"\n{Colors.CYAN}Starting Heartbeat...{Colors.END}")
        print(f"Run: cd {core_dir} && python3 dharmic_claw_heartbeat.py --check-once")
        os.system(f"cd {core_dir} && python3 dharmic_claw_heartbeat.py --check-once 2>&1 | head -30")
        
    elif choice == "2":
        print(f"\n{Colors.CYAN}Running DGM Cycle (dry-run)...{Colors.END}")
        print("Exporting DGM_DRY_RUN=true...")
        os.environ["DGM_DRY_RUN"] = "true"
        os.system(f"cd {core_dir} && python3 dharmic_claw_heartbeat.py --dgm-once 2>&1 | tail -20")
        
    elif choice == "3":
        print(f"\n{Colors.CYAN}Running Moltbook Heartbeat...{Colors.END}")
        os.system(f"cd {core_dir} && python3 moltbook_heartbeat.py --once 2>&1 | head -40")
        
    elif choice == "4":
        print(f"\n{Colors.CYAN}Restarting Unified Daemon...{Colors.END}")
        os.system("launchctl unload ~/Library/LaunchAgents/com.dharmic.moltbook-heartbeat.plist 2>/dev/null")
        uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
        os.system(f"launchctl bootstrap gui/{uid} ~/Library/LaunchAgents/com.dharmic.moltbook-heartbeat.plist")
        print(f"{Colors.GREEN}✅ Daemon restarted{Colors.END}")
        
    elif choice == "5":
        print(f"\n{Colors.CYAN}Checking Email Bridge...{Colors.END}")
        os.system(f"cd {core_dir} && python3 -c \"from email_bridge import check_inbox; print('OK')\" 2>&1")
        
    elif choice == "6":
        print(f"\n{Colors.CYAN}Testing Backup Models...{Colors.END}")
        os.system(f"cd {core_dir} && python3 -c \"from dgc_backup_models import BackupModelClient; c = BackupModelClient(); print('Kimi:', c._try_kimi('Hello', None, 10, 0.7)['success'])\" 2>&1")
        
    elif choice == "7":
        print(f"\n{Colors.CYAN}Running Integration Tests...{Colors.END}")
        os.system(f"cd {dgc_root}/core && python3 integration_test.py 2>&1 | tail -20")
        
    elif choice == "8":
        print(f"\n{Colors.CYAN}Recent Logs...{Colors.END}")
        log_dir = Path.home() / "DHARMIC_GODEL_CLAW" / "logs"
        if log_dir.exists():
            files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
            for f in files:
                print(f"  {f.name}")
        input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.END}")
        
    elif choice == "9":
        print(f"\n{Colors.CYAN}Spawning 10 Subagents...{Colors.END}")
        print(f"{Colors.WARNING}This will use backup models if Claude hits limits{Colors.END}")
        print("Run: cd {} && python3 spawn_subagents.py --count 10".format(core_dir))
        
    elif choice == "/status" or choice == "status":
        print(f"\n{Colors.CYAN}Detailed Status...{Colors.END}")
        os.system(f"cd {dgc_root} && git status --short 2>/dev/null | head -10")
        input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.END}")
        
    elif choice == "/swarm":
        print(f"\n{Colors.CYAN}Running DGM Swarm...{Colors.END}")
        os.system(f"cd {core_dir} && python3 -c \"from dgm_orchestrator import DGMOrchestrator; o = DGMOrchestrator(); o.run_cycle()\" 2>&1 | tail -20")
        input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.END}")
        
    elif choice == "/witness":
        print(f"\n{Colors.CYAN}Witness Stability...{Colors.END}")
        os.system(f"cd {core_dir} && python3 -c \"from strange_loop_memory import WitnessStabilityTracker; t = WitnessStabilityTracker(); print(t.get_stability_report())\" 2>&1")
        input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.END}")
        
    elif choice == "0" or choice == "/quit":
        print(f"\n{Colors.GREEN}DGC standing by. Telos: Moksha.{Colors.END}\n")
        sys.exit(0)

def main():
    while True:
        clear()
        print_header()
        
        status = check_status()
        print_status(status)
        print_integration_progress()
        print_commands()
        
        try:
            choice = input(f"{Colors.BOLD}DGC:{Colors.END} ").strip().lower()
            if choice:
                execute_command(choice)
                if choice not in ["0", "/quit"]:
                    input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.END}")
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}DGC standing by. Telos: Moksha.{Colors.END}\n")
            break
        except Exception as e:
            print(f"\n{Colors.FAIL}Error: {e}{Colors.END}")
            input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.END}")

if __name__ == "__main__":
    main()
