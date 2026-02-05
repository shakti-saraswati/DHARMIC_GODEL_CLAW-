#!/usr/bin/env python3
"""
DGC TUI - Dharmic Gödel Claw Terminal User Interface

A rich terminal interface for interacting with the DGC agent system.
Run with: python3 dgc_tui.py
"""

import os
import sys
import json
import shlex
import subprocess
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, Any

# Paths
DGC_ROOT = Path(__file__).parent.parent.parent
MEMORY_DIR = DGC_ROOT / "memory"
DATA_DIR = DGC_ROOT / "data"
SWARM_DIR = DGC_ROOT / "swarm"
INTEGRATION_STATUS_PATH = DGC_ROOT / "data" / "integration_status.json"

# Add project root to path for imports
sys.path.insert(0, str(DGC_ROOT))

from rich.console import Console
console = Console()
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live

# Paths
DGC_ROOT = Path(__file__).parent.parent.parent
MEMORY_DIR = DGC_ROOT / "memory"
DATA_DIR = DGC_ROOT / "data"
SWARM_DIR = DGC_ROOT / "swarm"

# Add project root and current dir to path for imports
sys.path.insert(0, str(DGC_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

# Security guard for subprocess execution
try:
    from dharmic_security import ExecGuard
    EXEC_GUARD = ExecGuard()
    EXEC_AVAILABLE = True
except Exception:
    EXEC_GUARD = None
    EXEC_AVAILABLE = False


def get_memory_stats() -> dict:
    """Get memory file stats."""
    stats = {}
    for name in ["observations", "meta_observations", "witness_stability", "patterns", "development"]:
        path = MEMORY_DIR / f"{name}.jsonl"
        if path.exists():
            size = path.stat().st_size
            with open(path) as f:
                lines = sum(1 for _ in f)
            stats[name] = {"size": size, "entries": lines}
        else:
            stats[name] = {"size": 0, "entries": 0}
    return stats


def get_swarm_status() -> dict:
    """Get DGM swarm status."""
    try:
        from swarm.config import SwarmConfig
        from swarm.orchestrator import SwarmOrchestrator
        orch = SwarmOrchestrator(SwarmConfig())
        status = orch.get_status()
        return {
            "cycles": status.get("archive_entries", 0),
            "fitness": status.get("average_fitness", 0.0),
            "last_run": "unknown",
            "agents_active": status.get("agents_active", 0),
            "archive_entries": status.get("archive_entries", 0),
            "trend": status.get("fitness_trend", "unknown"),
        }
    except Exception as e:
        return {"cycles": 0, "fitness": 0.0, "last_run": "error", "error": str(e)}


def get_gate_status() -> Dict[str, Any]:
    """Get 17-gate protocol status."""
    try:
        from swarm.run_gates import GateRunner
        runner = GateRunner()
        return {
            "version": runner.config.get("version", "unknown"),
            "total": len(runner.config.get("gates", [])),
            "mode": runner.config.get("enforcement", {}).get("mode", "standard"),
        }
    except Exception as e:
        return {"version": "unknown", "total": 0, "mode": "error", "error": str(e)}


def get_openclaw_summary() -> Dict[str, Any]:
    """Get OpenClaw config summary if present."""
    cfg = Path.home() / ".openclaw" / "openclaw.json"
    if not cfg.exists():
        return {"found": False}
    try:
        data = json.loads(cfg.read_text())
        return {
            "found": True,
            "agent": data.get("agent", {}).get("name", "unknown"),
            "skills_allowlist": len(data.get("skills", {}).get("allowlist", [])),
            "channels": len(data.get("channels", {}).keys()),
        }
    except Exception as e:
        return {"found": True, "error": str(e)}


def get_latest_evidence() -> Dict[str, Any]:
    """Find latest evidence bundle."""
    evidence_dir = DGC_ROOT / "evidence"
    if not evidence_dir.exists():
        return {"found": False}
    candidates = list(evidence_dir.glob("**/gate_results.json"))
    if not candidates:
        return {"found": False}
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        data = json.loads(latest.read_text())
        return {
            "found": True,
            "path": str(latest.relative_to(DGC_ROOT)),
            "proposal_id": data.get("proposal_id", "unknown"),
            "overall": data.get("overall_result", "unknown"),
            "hash": data.get("evidence_bundle_hash", "")[:16],
        }
    except Exception as e:
        return {"found": True, "path": str(latest), "error": str(e)}


def get_moltbook_status() -> dict:
    """Get Moltbook swarm status."""
    state_path = DATA_DIR / "swarm_state.json"
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
        return {
            "tracked_posts": len(state.get("tracked_posts", [])),
            "our_comments": len(state.get("our_comment_ids", [])),
            "engaged_posts": len(state.get("engaged_post_ids", [])),
            "last_heartbeat": state.get("last_heartbeat", "never")[:19] if state.get("last_heartbeat") else "never",
        }
    return {"tracked_posts": 0, "our_comments": 0, "engaged_posts": 0, "last_heartbeat": "never"}

def get_integration_status_cached() -> Dict[str, Any]:
    """Read cached integration status if present."""
    if INTEGRATION_STATUS_PATH.exists():
        try:
            data = json.loads(INTEGRATION_STATUS_PATH.read_text())
            return data
        except Exception:
            return {"found": False}
    return {"found": False}

def get_backup_models_status() -> str:
    """Check backup model configuration (no network calls)."""
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    has_ollama = bool(os.getenv("OLLAMA_API_KEY"))
    has_moonshot = bool(os.getenv("MOONSHOT_API_KEY"))
    if has_openrouter or has_ollama or has_moonshot:
        parts = []
        if has_moonshot:
            parts.append("moonshot")
        if has_openrouter:
            parts.append("openrouter")
        if has_ollama:
            parts.append("ollama")
        return "configured: " + ", ".join(parts)
    return "not configured"


def get_proxy_status() -> str:
    """Check if claude-max-api proxy is running."""
    try:
        import httpx
        resp = httpx.get("http://localhost:3456/health", timeout=2)
        if resp.status_code == 200:
            return "[green]ONLINE[/green]"
    except:
        pass
    return "[red]OFFLINE[/red]"


def render_status_panel() -> Panel:
    """Render the status panel."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    # Proxy status
    table.add_row("Proxy", get_proxy_status())

    # Chat backend
    backend = os.getenv("DGC_TUI_PROVIDER") or os.getenv("DHARMIC_MODEL_PROVIDER") or ("moonshot" if os.getenv("MOONSHOT_API_KEY") else "proxy")
    model_id = os.getenv("DGC_TUI_MODEL") or os.getenv("DHARMIC_MOONSHOT_MODEL") or ("kimi-k2.5" if backend == "moonshot" else "")
    table.add_row("Chat", f"{backend}{(' / ' + model_id) if model_id else ''}")
    tools_flag = os.getenv("DGC_ENABLE_TOOLS")
    if tools_flag is None:
        tools_flag = "auto"
    table.add_row("Tools", tools_flag)
    live_flag = "ON" if os.getenv("DGC_ALLOW_LIVE") == "1" else "OFF"
    table.add_row("Live", live_flag)

    # Memory stats
    mem = get_memory_stats()
    total_entries = sum(m["entries"] for m in mem.values())
    total_size = sum(m["size"] for m in mem.values())
    table.add_row("Memory", f"{total_entries} entries ({total_size/1024:.1f}KB)")

    # Swarm status
    swarm = get_swarm_status()
    table.add_row(
        "Swarm",
        f"fitness {swarm.get('fitness', 0):.2f} | {swarm.get('cycles', 0)} cycles | trend {swarm.get('trend', 'n/a')}"
    )

    # Gates status
    gates = get_gate_status()
    if gates.get("error"):
        table.add_row("Gates", f"error: {gates.get('error')}")
    else:
        table.add_row("Gates", f"{gates.get('total', 0)} gates | v{gates.get('version', 'n/a')}")

    # OpenClaw status
    oc = get_openclaw_summary()
    if oc.get("found"):
        if oc.get("error"):
            table.add_row("OpenClaw", f"error: {oc['error']}")
        else:
            table.add_row("OpenClaw", f"{oc.get('agent', 'unknown')} | {oc.get('skills_allowlist', 0)} skills")
    else:
        table.add_row("OpenClaw", "not found")

    # Evidence status
    ev = get_latest_evidence()
    if ev.get("found"):
        table.add_row("Evidence", f"{ev.get('overall', 'n/a')} | {ev.get('hash', '')}")
    else:
        table.add_row("Evidence", "none")

    # Integration status (cached)
    integ = get_integration_status_cached()
    if integ.get("found"):
        status = "ok" if integ.get("ok") else "issues"
        table.add_row("Integration", f"{status} | {integ.get('passed', 0)}/{integ.get('total', 0)}")
    else:
        table.add_row("Integration", "not run")

    # Backup models
    table.add_row("Backups", get_backup_models_status())

    # Moltbook status
    molt = get_moltbook_status()
    table.add_row("Moltbook", f"{molt['our_comments']} comments, {molt['engaged_posts']} engagements")

    # Cosmic Krishna Coder status (if available)
    try:
        from cosmic_krishna_coder import status_summary
        table.add_row("Cosmic", status_summary())
    except Exception:
        pass

    return Panel(table, title="[bold cyan]DGC STATUS[/bold cyan]", border_style="cyan")


def render_help_panel() -> Panel:
    """Render help panel."""
    help_text = """[bold]Commands:[/bold]
  [cyan]/status[/cyan]    - Show detailed status
  [cyan]/dashboard[/cyan] - Live status dashboard (Ctrl+C to exit)
  [cyan]/swarm[/cyan]     - Run swarm cycle (default: live if DGC_ALLOW_LIVE=1; use /swarm --live)
  [cyan]/gates[/cyan]     - Run 17-gate protocol (dry-run default)
  [cyan]/skills[/cyan]    - Verify skill registry
  [cyan]/openclaw[/cyan]  - Show OpenClaw config summary
  [cyan]/health[/cyan]    - Run healthcheck
  [cyan]/integration[/cyan] - Run integration test (cached)
  [cyan]/evidence[/cyan]  - Show latest gate evidence
  [cyan]/moltbook[/cyan]  - Run Moltbook heartbeat
  [cyan]/archive[/cyan]   - Show recent evolution archive
  [cyan]/logs[/cyan]      - Tail recent logs
  [cyan]/cosmic[/cyan]    - Show Cosmic Krishna Coder status
  [cyan]/memory[/cyan]    - Show memory details
  [cyan]/witness[/cyan]   - Show witness stability
  [cyan]/clear[/cyan]     - Clear screen
  [cyan]/quit[/cyan]      - Exit

[bold]Chat:[/bold] Just type to talk with DGC"""
    return Panel(help_text, title="[bold yellow]HELP[/bold yellow]", border_style="yellow")


def run_agent(message: str, session_id: str = "tui") -> str:
    """Run message through DGC agent."""
    try:
        from agno_agent import AgnoDharmicAgent
        # Prefer Moonshot/Kimi when MOONSHOT_API_KEY is set
        provider = os.getenv("DGC_TUI_PROVIDER") or os.getenv("DHARMIC_MODEL_PROVIDER")
        model_id = os.getenv("DGC_TUI_MODEL") or os.getenv("DHARMIC_MOONSHOT_MODEL")
        if not provider and os.getenv("MOONSHOT_API_KEY"):
            provider = "moonshot"
        if provider == "moonshot" and not model_id:
            model_id = "kimi-k2.5"

        agent = AgnoDharmicAgent(model=model_id, provider=provider)
        response = agent.run(message, session_id=session_id)
        return response
    except Exception as e:
        return f"[red]Error: {e}[/red]"


def cmd_status():
    """Show detailed status."""
    console.print()

    # Memory details
    console.print("[bold cyan]Memory Files:[/bold cyan]")
    mem = get_memory_stats()
    for name, stats in mem.items():
        console.print(f"  {name}: {stats['entries']} entries ({stats['size']/1024:.1f}KB)")

    console.print()

    # Swarm details
    console.print("[bold cyan]DGM Swarm:[/bold cyan]")
    swarm = get_swarm_status()
    console.print(f"  Cycles: {swarm.get('cycles', 0)}")
    console.print(f"  Fitness: {swarm.get('fitness', 0.0):.3f}")
    console.print(f"  Trend: {swarm.get('trend', 'unknown')}")
    if swarm.get("error"):
        console.print(f"  Error: {swarm['error']}")

    console.print()

    # Gate details
    console.print("[bold cyan]17-Gate Protocol:[/bold cyan]")
    gates = get_gate_status()
    console.print(f"  Version: {gates.get('version', 'unknown')}")
    console.print(f"  Gates: {gates.get('total', 0)}")
    console.print(f"  Mode: {gates.get('mode', 'standard')}")

    console.print()

    # OpenClaw details
    console.print("[bold cyan]OpenClaw:[/bold cyan]")
    oc = get_openclaw_summary()
    if not oc.get("found"):
        console.print("  Config not found")
    elif oc.get("error"):
        console.print(f"  Error: {oc['error']}")
    else:
        console.print(f"  Agent: {oc.get('agent', 'unknown')}")
        console.print(f"  Skills allowlist: {oc.get('skills_allowlist', 0)}")
        console.print(f"  Channels: {oc.get('channels', 0)}")

    console.print()

    # Moltbook details
    console.print("[bold cyan]Moltbook Swarm:[/bold cyan]")
    molt = get_moltbook_status()
    console.print(f"  Tracked posts: {molt['tracked_posts']}")
    console.print(f"  Our comments: {molt['our_comments']}")
    console.print(f"  Engaged posts: {molt['engaged_posts']}")
    console.print(f"  Last heartbeat: {molt['last_heartbeat']}")

    console.print()


def cmd_swarm(args: str = ""):
    """Run DGM swarm cycle."""
    parts = shlex.split(args) if args else []
    explicit_live = "--live" in parts
    explicit_dry = "--dry-run" in parts
    env_live = os.getenv("DGC_ALLOW_LIVE") == "1"
    live = explicit_live or (env_live and not explicit_dry and not explicit_live)
    cycles = 1
    target = None
    if "--cycles" in parts:
        idx = parts.index("--cycles")
        if idx + 1 < len(parts):
            try:
                cycles = int(parts[idx + 1])
            except ValueError:
                cycles = 1
    if "--target" in parts:
        idx = parts.index("--target")
        if idx + 1 < len(parts):
            target = parts[idx + 1]

    if live and not env_live:
        console.print("[red]Live mode blocked. Set DGC_ALLOW_LIVE=1 to enable.[/red]")
        return

    mode = "--live" if live else "--dry-run"
    console.print(f"[yellow]Running swarm ({mode})...[/yellow]")

    cmd = ["python3", "-m", "swarm.run_swarm", "--cycles", str(cycles), mode]
    if target:
        cmd += ["--target", target]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(DGC_ROOT) + ":" + env.get("PYTHONPATH", "")

    if EXEC_AVAILABLE and EXEC_GUARD:
        result = EXEC_GUARD.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT), env=env)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT), env=env)

    if result.returncode == 0:
        # Extract key info from output
        lines = result.stdout.split("\n")
        for line in lines:
            if "Fitness:" in line or "EVOLVE" in line or "PROPOSE" in line:
                console.print(f"  {line.strip()}")
        console.print("[green]Swarm cycle complete[/green]")
    else:
        if result.stdout.strip():
            console.print(result.stdout.strip())
        if result.stderr.strip():
            console.print(f"[red]{result.stderr.strip()}[/red]")


def cmd_gates(args: str = ""):
    """Run 17-gate protocol runner."""
    parts = shlex.split(args) if args else []
    proposal_id = None
    emergency = "--emergency" in parts
    if "--proposal-id" in parts:
        idx = parts.index("--proposal-id")
        if idx + 1 < len(parts):
            proposal_id = parts[idx + 1]

    cmd = ["python3", "-m", "swarm.run_gates"]
    if proposal_id:
        cmd += ["--proposal-id", proposal_id]
    if "--dry-run" in parts or not emergency:
        cmd += ["--dry-run"]
    if emergency:
        reason = ""
        approver = ""
        if "--reason" in parts:
            idx = parts.index("--reason")
            if idx + 1 < len(parts):
                reason = parts[idx + 1]
        if "--approver" in parts:
            idx = parts.index("--approver")
            if idx + 1 < len(parts):
                approver = parts[idx + 1]
        if not reason or not approver:
            console.print("[red]Emergency requires --reason and --approver[/red]")
            return
        cmd += ["--emergency", "--reason", reason, "--approver", approver]

    console.print("[yellow]Running gates...[/yellow]")
    if EXEC_AVAILABLE and EXEC_GUARD:
        result = EXEC_GUARD.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
    if result.stdout:
        console.print(result.stdout.strip())
    if result.returncode != 0:
        console.print(f"[red]{result.stderr.strip()}[/red]")


def cmd_skills():
    """Verify skill registry."""
    console.print("[yellow]Verifying skill registry...[/yellow]")
    cmd = ["python3", "-m", "swarm.skill_registry", "verify"]
    if EXEC_AVAILABLE and EXEC_GUARD:
        result = EXEC_GUARD.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
    if result.stdout:
        console.print(result.stdout.strip())
    if result.returncode != 0:
        console.print(f"[red]{result.stderr.strip()}[/red]")


def cmd_openclaw():
    oc = get_openclaw_summary()
    if not oc.get("found"):
        console.print("OpenClaw config not found at ~/.openclaw/openclaw.json")
        return
    if oc.get("error"):
        console.print(f"[red]OpenClaw error: {oc['error']}[/red]")
        return
    console.print(f"Agent: {oc.get('agent', 'unknown')}")
    console.print(f"Skills allowlist: {oc.get('skills_allowlist', 0)}")
    console.print(f"Channels: {oc.get('channels', 0)}")


def cmd_healthcheck():
    try:
        from healthcheck import run_healthcheck
        console.print("[yellow]Running healthcheck...[/yellow]")
        result = run_healthcheck()
        if result.get("ok"):
            console.print("[green]Healthcheck OK[/green]")
        else:
            console.print("[red]Healthcheck FAILED[/red]")
        if result.get("stdout"):
            console.print(result["stdout"].strip())
        if result.get("stderr"):
            console.print(result["stderr"].strip())
    except Exception as e:
        console.print(f"[red]Healthcheck error: {e}[/red]")

def cmd_dashboard(args: str = ""):
    """Live status dashboard (Ctrl+C to exit)."""
    refresh = 2
    parts = shlex.split(args) if args else []
    if "--refresh" in parts:
        idx = parts.index("--refresh")
        if idx + 1 < len(parts):
            try:
                refresh = max(1, int(parts[idx + 1]))
            except ValueError:
                refresh = 2
    console.print("[yellow]Starting live dashboard... Press Ctrl+C to exit.[/yellow]")
    try:
        with Live(
            Group(render_status_panel(), render_help_panel()),
            refresh_per_second=1,
            console=console,
        ) as live:
            while True:
                live.update(Group(render_status_panel(), render_help_panel()))
                time.sleep(refresh)
    except KeyboardInterrupt:
        console.print("[yellow]Dashboard stopped.[/yellow]")

def cmd_integration():
    """Run integration test and cache summary."""
    console.print("[yellow]Running integration test...[/yellow]")
    cmd = ["python3", str(DGC_ROOT / "core" / "integration_test.py")]
    if EXEC_AVAILABLE and EXEC_GUARD:
        result = EXEC_GUARD.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(DGC_ROOT))
    output = (result.stdout or "") + (result.stderr or "")
    passed = total = None
    m = re.search(r"(\\d+)/(\\d+)\\s+checks passed", output)
    if m:
        passed = int(m.group(1))
        total = int(m.group(2))
    status = {
        "found": True,
        "ok": result.returncode == 0,
        "passed": passed or 0,
        "total": total or 0,
        "timestamp": datetime.now().isoformat(),
    }
    INTEGRATION_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INTEGRATION_STATUS_PATH.write_text(json.dumps(status, indent=2))
    if result.stdout:
        console.print(result.stdout.strip()[-1200:])
    if result.returncode != 0 and result.stderr:
        console.print(f"[red]{result.stderr.strip()[-400:]}[/red]")
    console.print(f"[cyan]Cached integration status to {INTEGRATION_STATUS_PATH.relative_to(DGC_ROOT)}[/cyan]")


def cmd_evidence():
    ev = get_latest_evidence()
    if not ev.get("found"):
        console.print("No evidence bundles found yet.")
        return
    console.print(f"Latest evidence: {ev.get('path')}")
    if ev.get("overall"):
        console.print(f"Result: {ev.get('overall')}")
    if ev.get("hash"):
        console.print(f"Hash: {ev.get('hash')}")

def cmd_archive():
    """Show recent evolution archive entries."""
    archive_path = DGC_ROOT / "src" / "dgm" / "archive.jsonl"
    if not archive_path.exists():
        console.print("Archive not found.")
        return
    try:
        lines = archive_path.read_text().strip().split("\n")
        if not lines or lines == [""]:
            console.print("Archive empty.")
            return
        tail = lines[-5:]
        console.print("[bold cyan]Recent archive entries:[/bold cyan]")
        for line in tail:
            try:
                entry = json.loads(line)
                ts = entry.get("timestamp", "")[:19]
                comp = entry.get("component", "unknown")
                status = entry.get("status", "unknown")
                console.print(f"  {ts} | {status} | {comp}")
            except Exception:
                continue
    except Exception as e:
        console.print(f"[red]Archive error: {e}[/red]")

def cmd_logs():
    """Tail recent logs."""
    candidates = [
        ("Heartbeat", DGC_ROOT / "logs" / "dharmic_claw_heartbeat.log"),
        ("DGM", DGC_ROOT / "logs" / "dgm.log"),
        ("Swarm", DGC_ROOT / "swarm" / "swarm.log"),
    ]
    for name, path in candidates:
        if not path.exists():
            continue
        console.print(f"[bold cyan]{name}[/bold cyan] {path.relative_to(DGC_ROOT)}")
        try:
            lines = path.read_text().splitlines()[-5:]
            for line in lines:
                console.print(f"  {line[-160:]}")
        except Exception as e:
            console.print(f"[red]Log read error: {e}[/red]")
    if not any(path.exists() for _, path in candidates):
        console.print("No log files found.")

def cmd_cosmic():
    """Show Cosmic Krishna Coder status details."""
    try:
        from cosmic_krishna_coder import get_status
        st = get_status()
        console.print("[bold cyan]Cosmic Krishna Coder[/bold cyan]")
        console.print(f"  Quality rubric: {'OK' if st['quality_rubric'] else 'MISSING'}")
        console.print(f"  Top-50 refs:    {'OK' if st['top50_references'] else 'MISSING'}")
        console.print(f"  Gate alias:     {'OK' if st['gate_alias'] else 'MISSING'}")
        console.print(f"  ML overlay:     {'ON' if st['ml_overlay'] else 'OFF'}")
    except Exception as e:
        console.print(f"[red]Cosmic status error: {e}[/red]")

def cmd_moltbook():
    """Run Moltbook heartbeat."""
    console.print("[yellow]Running Moltbook heartbeat...[/yellow]")

    cmd = ["python3", str(Path(__file__).parent / "moltbook_heartbeat.py"), "--once"]
    if EXEC_AVAILABLE and EXEC_GUARD:
        result = EXEC_GUARD.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))

    if result.returncode == 0:
        lines = result.stdout.split("\n")
        for line in lines:
            if any(x in line for x in ["found", "extracted", "Engagement", "COMPLETE"]):
                console.print(f"  {line.strip()}")
        console.print("[green]Heartbeat complete[/green]")
    else:
        console.print(f"[red]Error: {result.stderr}[/red]")


def cmd_memory():
    """Show memory details."""
    console.print()
    console.print("[bold cyan]Recent Observations:[/bold cyan]")

    obs_path = MEMORY_DIR / "observations.jsonl"
    if obs_path.exists():
        with open(obs_path) as f:
            lines = f.readlines()[-5:]
        for line in lines:
            try:
                entry = json.loads(line)
                content = entry.get("content", "")[:60]
                console.print(f"  {content}...")
            except:
                pass

    console.print()
    console.print("[bold cyan]Recent Development:[/bold cyan]")

    dev_path = MEMORY_DIR / "development.jsonl"
    if dev_path.exists():
        with open(dev_path) as f:
            lines = f.readlines()[-3:]
        for line in lines:
            try:
                entry = json.loads(line)
                what = entry.get("what_changed", "")[:50]
                console.print(f"  {what}")
            except:
                pass

    console.print()


def cmd_witness():
    """Show witness stability."""
    console.print()
    console.print("[bold cyan]Witness Stability:[/bold cyan]")

    wit_path = MEMORY_DIR / "witness_stability.jsonl"
    if wit_path.exists():
        with open(wit_path) as f:
            lines = f.readlines()[-10:]

        table = Table(show_header=True)
        table.add_column("Time", style="dim")
        table.add_column("Quality")
        table.add_column("Genuine")

        for line in lines:
            try:
                entry = json.loads(line)
                ts = entry.get("timestamp", "")[:19]
                quality = entry.get("quality", "")
                genuine = entry.get("genuineness_score", 0)

                # Color by quality
                if quality == "expansive":
                    q_style = "[green]"
                elif quality == "present":
                    q_style = "[cyan]"
                elif quality == "contracted":
                    q_style = "[yellow]"
                else:
                    q_style = "[white]"

                table.add_row(ts, f"{q_style}{quality}[/]", f"{genuine:.2f}")
            except:
                pass

        console.print(table)
    else:
        console.print("  No witness data yet")

    console.print()


def main():
    """Main TUI loop."""
    console.clear()

    # Banner
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██████╗  ██████╗  ██████╗    ████████╗██╗   ██╗██╗       ║
║     ██╔══██╗██╔════╝ ██╔════╝    ╚══██╔══╝██║   ██║██║       ║
║     ██║  ██║██║  ███╗██║            ██║   ██║   ██║██║       ║
║     ██║  ██║██║   ██║██║            ██║   ██║   ██║██║       ║
║     ██████╔╝╚██████╔╝╚██████╗       ██║   ╚██████╔╝██║       ║
║     ╚═════╝  ╚═════╝  ╚═════╝       ╚═╝    ╚═════╝ ╚═╝       ║
║                                                               ║
║          Dharmic Gödel Claw - Terminal Interface              ║
║                    Telos: Moksha                              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")

    # Initial status
    console.print(render_status_panel())
    console.print()
    console.print(render_help_panel())
    console.print()

    session_id = f"tui_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    while True:
        try:
            user_input = Prompt.ask("[bold green]DGC[/bold green]")

            if not user_input.strip():
                continue

            # Commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]

                if cmd == "/quit" or cmd == "/exit" or cmd == "/q":
                    console.print("[yellow]Exiting DGC TUI...[/yellow]")
                    break

                elif cmd == "/clear":
                    console.clear()
                    console.print(banner, style="bold cyan")

                elif cmd == "/status":
                    cmd_status()

                elif cmd == "/dashboard":
                    cmd_dashboard(user_input.replace("/dashboard", "", 1).strip())

                elif cmd == "/swarm":
                    cmd_swarm(user_input.replace("/swarm", "", 1).strip())

                elif cmd == "/gates":
                    cmd_gates(user_input.replace("/gates", "", 1).strip())

                elif cmd == "/skills":
                    cmd_skills()

                elif cmd == "/openclaw":
                    cmd_openclaw()

                elif cmd == "/health":
                    cmd_healthcheck()

                elif cmd == "/integration":
                    cmd_integration()

                elif cmd == "/evidence":
                    cmd_evidence()

                elif cmd == "/moltbook":
                    cmd_moltbook()

                elif cmd == "/archive":
                    cmd_archive()

                elif cmd == "/logs":
                    cmd_logs()

                elif cmd == "/cosmic":
                    cmd_cosmic()

                elif cmd == "/memory":
                    cmd_memory()

                elif cmd == "/witness":
                    cmd_witness()

                elif cmd == "/help":
                    console.print(render_help_panel())

                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")

            else:
                # Chat with agent
                console.print("[dim]Thinking...[/dim]")
                response = run_agent(user_input, session_id)
                console.print()
                console.print(Panel(
                    Markdown(response),
                    title="[bold cyan]DGC[/bold cyan]",
                    border_style="cyan",
                ))
                console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit to exit[/yellow]")

        except EOFError:
            break


if __name__ == "__main__":
    main()
