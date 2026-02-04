#!/usr/bin/env python3
"""
DGC TUI - Dharmic Gödel Claw Terminal User Interface

A rich terminal interface for interacting with the DGC agent system.
Run with: python3 dgc_tui.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text
from rich.style import Style

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

console = Console()

# Paths
DGC_ROOT = Path(__file__).parent.parent.parent
MEMORY_DIR = DGC_ROOT / "memory"
DATA_DIR = DGC_ROOT / "data"
SWARM_DIR = DGC_ROOT / "swarm"


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
    archive_path = SWARM_DIR / "archive" / "residual_stream.jsonl"
    if archive_path.exists():
        with open(archive_path) as f:
            entries = [json.loads(line) for line in f if line.strip()]
        if entries:
            latest = entries[-1]
            return {
                "cycles": len(entries),
                "fitness": latest.get("fitness", 0),
                "last_run": latest.get("timestamp", "unknown")[:19],
            }
    return {"cycles": 0, "fitness": 0, "last_run": "never"}


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

    # Memory stats
    mem = get_memory_stats()
    total_entries = sum(m["entries"] for m in mem.values())
    total_size = sum(m["size"] for m in mem.values())
    table.add_row("Memory", f"{total_entries} entries ({total_size/1024:.1f}KB)")

    # Swarm status
    swarm = get_swarm_status()
    table.add_row("DGM Swarm", f"fitness {swarm['fitness']:.2f} ({swarm['cycles']} cycles)")

    # Moltbook status
    molt = get_moltbook_status()
    table.add_row("Moltbook", f"{molt['our_comments']} comments, {molt['engaged_posts']} engagements")

    return Panel(table, title="[bold cyan]DGC STATUS[/bold cyan]", border_style="cyan")


def render_help_panel() -> Panel:
    """Render help panel."""
    help_text = """[bold]Commands:[/bold]
  [cyan]/status[/cyan]    - Show detailed status
  [cyan]/swarm[/cyan]     - Run DGM swarm cycle
  [cyan]/moltbook[/cyan]  - Run Moltbook heartbeat
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
        agent = AgnoDharmicAgent()
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
    console.print(f"  Cycles: {swarm['cycles']}")
    console.print(f"  Fitness: {swarm['fitness']:.3f}")
    console.print(f"  Last run: {swarm['last_run']}")

    console.print()

    # Moltbook details
    console.print("[bold cyan]Moltbook Swarm:[/bold cyan]")
    molt = get_moltbook_status()
    console.print(f"  Tracked posts: {molt['tracked_posts']}")
    console.print(f"  Our comments: {molt['our_comments']}")
    console.print(f"  Engaged posts: {molt['engaged_posts']}")
    console.print(f"  Last heartbeat: {molt['last_heartbeat']}")

    console.print()


def cmd_swarm(dry_run: bool = True):
    """Run DGM swarm cycle."""
    mode = "--dry-run" if dry_run else "--live"
    console.print(f"[yellow]Running DGM swarm ({mode})...[/yellow]")

    result = subprocess.run(
        ["python3", str(SWARM_DIR / "run_swarm.py"), "--cycles", "1", mode],
        capture_output=True,
        text=True,
        cwd=str(DGC_ROOT),
    )

    if result.returncode == 0:
        # Extract key info from output
        lines = result.stdout.split("\n")
        for line in lines:
            if "Fitness:" in line or "EVOLVE" in line or "PROPOSE" in line:
                console.print(f"  {line.strip()}")
        console.print("[green]Swarm cycle complete[/green]")
    else:
        console.print(f"[red]Error: {result.stderr}[/red]")


def cmd_moltbook():
    """Run Moltbook heartbeat."""
    console.print("[yellow]Running Moltbook heartbeat...[/yellow]")

    result = subprocess.run(
        ["python3", str(Path(__file__).parent / "moltbook_heartbeat.py"), "--once"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent),
    )

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

                elif cmd == "/swarm":
                    dry = "--live" not in user_input
                    cmd_swarm(dry_run=dry)

                elif cmd == "/moltbook":
                    cmd_moltbook()

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
