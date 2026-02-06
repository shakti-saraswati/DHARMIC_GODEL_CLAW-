#!/usr/bin/env python3
"""
DGC + OpenClaw Unified Monitoring Dashboard
Built using the Krishna Coding System (17-Gate Protocol)

A comprehensive monitoring and development tool for:
- OpenClaw gateway, agents, sessions, and model usage
- DHARMIC_GODEL_CLAW orchestrator, gates, fitness trends, evolution archive
- RLM synthesis capabilities for research corpus queries

Usage:
    python -m tools.monitor.dashboard [command]
    dgc-monitor [command]

Commands:
    status      - Show unified status overview (default)
    openclaw    - OpenClaw detailed status
    dgc         - DGC detailed status
    gates       - Run gate checks
    fitness     - Show fitness trends
    rlm         - RLM synthesis interface
    watch       - Live dashboard mode
    help        - Show this help

Author: Dhyana + Warp Agent
Co-Authored-By: Warp <agent@warp.dev>
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Rich for TUI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not installed. Run: pip install rich")

# =============================================================================
# PATHS
# =============================================================================

OPENCLAW_DIR = Path.home() / ".openclaw"
DGC_DIR = Path.home() / "DHARMIC_GODEL_CLAW"
VAULT_DIR = Path.home() / "Persistent-Semantic-Memory-Vault"
MECH_INTERP_DIR = Path.home() / "mech-interp-latent-lab-phase1"
CLAWD_DIR = Path.home() / "clawd"

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OpenClawStatus:
    """OpenClaw gateway status."""
    gateway_running: bool
    gateway_pid: Optional[int]
    config_valid: bool
    primary_model: str
    fallback_models: list[str]
    skills_count: int
    last_heartbeat: Optional[str]
    log_errors: int
    sessions_active: int


@dataclass
class DGCStatus:
    """DGC orchestrator status."""
    daemon_running: bool
    daemon_pid: Optional[int]
    archive_entries: int
    fitness_trend: str
    average_fitness: float
    gates_config_valid: bool
    last_evolution_id: Optional[str]
    logs_today: int
    enforcement_status: dict


# =============================================================================
# OPENCLAW MONITOR
# =============================================================================

class OpenClawMonitor:
    """Monitor OpenClaw gateway and agents."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
    def get_status(self) -> OpenClawStatus:
        """Get comprehensive OpenClaw status."""
        # Check gateway process
        gateway_running = False
        gateway_pid = None
        try:
            result = subprocess.run(
                ["pgrep", "-f", "openclaw.*gateway"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                gateway_pid = int(result.stdout.strip().split()[0])
                gateway_running = True
        except Exception:
            pass
        
        # Load config
        config_valid = False
        primary_model = "unknown"
        fallback_models = []
        try:
            config_path = OPENCLAW_DIR / "openclaw.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                config_valid = True
                
                # Extract model info from models.providers.openrouter.models
                providers = config.get("models", {}).get("providers", {})
                openrouter = providers.get("openrouter", {})
                models_list = openrouter.get("models", [])
                
                if models_list:
                    primary_model = models_list[0].get("id", "unknown")
                    fallback_models = [m.get("id", "") for m in models_list[1:5]]
        except Exception:
            pass
        
        # Count skills
        skills_count = 0
        skills_dir = OPENCLAW_DIR / "skills"
        if skills_dir.exists():
            skills_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
        
        # Get last heartbeat
        last_heartbeat = None
        heartbeat_log = OPENCLAW_DIR / "workspace" / "memory" / "heartbeat.log"
        if heartbeat_log.exists():
            try:
                lines = heartbeat_log.read_text().strip().split("\n")
                if lines:
                    last_heartbeat = lines[-1].split(" | ")[0] if " | " in lines[-1] else lines[-1][:25]
            except Exception:
                pass
        
        # Count log errors
        log_errors = 0
        err_log = OPENCLAW_DIR / "logs" / "gateway.err.log"
        if err_log.exists():
            try:
                content = err_log.read_text()
                log_errors = content.lower().count("error")
            except Exception:
                pass
        
        # Active sessions (from memory or completions)
        sessions_active = 0
        completions_dir = OPENCLAW_DIR / "completions"
        if completions_dir.exists():
            # Count recent completion files (last hour)
            now = time.time()
            for f in completions_dir.iterdir():
                if f.is_file() and (now - f.stat().st_mtime) < 3600:
                    sessions_active += 1
        
        return OpenClawStatus(
            gateway_running=gateway_running,
            gateway_pid=gateway_pid,
            config_valid=config_valid,
            primary_model=primary_model,
            fallback_models=fallback_models,
            skills_count=skills_count,
            last_heartbeat=last_heartbeat,
            log_errors=log_errors,
            sessions_active=sessions_active
        )
    
    def display_status(self, status: OpenClawStatus) -> None:
        """Display OpenClaw status with rich formatting."""
        if not RICH_AVAILABLE:
            print(f"OpenClaw Gateway: {'✓ Running' if status.gateway_running else '✗ Stopped'}")
            print(f"  PID: {status.gateway_pid}")
            print(f"  Model: {status.primary_model}")
            return
        
        # Create status table
        table = Table(title="🦞 OpenClaw Status", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        # Gateway
        gw_status = "[green]● Running[/]" if status.gateway_running else "[red]○ Stopped[/]"
        table.add_row("Gateway", gw_status, f"PID: {status.gateway_pid or 'N/A'}")
        
        # Config
        cfg_status = "[green]● Valid[/]" if status.config_valid else "[red]○ Invalid[/]"
        table.add_row("Config", cfg_status, str(OPENCLAW_DIR / "openclaw.json"))
        
        # Primary Model
        table.add_row("Primary Model", "[cyan]●[/]", status.primary_model)
        
        # Fallbacks
        fallback_str = ", ".join(status.fallback_models[:3]) if status.fallback_models else "None"
        table.add_row("Fallbacks", f"[yellow]{len(status.fallback_models)}[/]", fallback_str)
        
        # Skills
        table.add_row("Skills", f"[magenta]{status.skills_count}[/]", "Active integrations")
        
        # Heartbeat
        hb_status = "[green]●[/]" if status.last_heartbeat else "[yellow]○[/]"
        table.add_row("Last Heartbeat", hb_status, status.last_heartbeat or "Unknown")
        
        # Errors
        err_color = "green" if status.log_errors == 0 else "red" if status.log_errors > 10 else "yellow"
        table.add_row("Log Errors", f"[{err_color}]{status.log_errors}[/]", "In gateway.err.log")
        
        # Sessions
        table.add_row("Recent Sessions", f"[blue]{status.sessions_active}[/]", "Last hour")
        
        self.console.print(table)
    
    def tail_logs(self, lines: int = 20) -> None:
        """Tail OpenClaw gateway logs."""
        log_path = OPENCLAW_DIR / "logs" / "gateway.log"
        if not log_path.exists():
            print("No gateway log found")
            return
        
        try:
            content = log_path.read_text()
            log_lines = content.strip().split("\n")[-lines:]
            
            if RICH_AVAILABLE:
                self.console.print(Panel("\n".join(log_lines), title="Gateway Logs (last 20)", border_style="blue"))
            else:
                print("\n".join(log_lines))
        except Exception as e:
            print(f"Error reading logs: {e}")


# =============================================================================
# DGC MONITOR
# =============================================================================

class DGCMonitor:
    """Monitor DHARMIC_GODEL_CLAW orchestrator and gates."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
    def get_status(self) -> DGCStatus:
        """Get comprehensive DGC status."""
        # Check daemon process
        daemon_running = False
        daemon_pid = None
        try:
            result = subprocess.run(
                ["pgrep", "-f", "dgc.*daemon|dharmic.*daemon"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                daemon_pid = int(result.stdout.strip().split()[0])
                daemon_running = True
        except Exception:
            pass
        
        # Check daemon status file
        daemon_status = DGC_DIR / "logs" / "daemon_status.json"
        if daemon_status.exists():
            try:
                data = json.load(open(daemon_status))
                if data.get("status") == "running":
                    daemon_running = True
                    daemon_pid = data.get("pid")
            except Exception:
                pass
        
        # Load archive entries
        archive_entries = 0
        fitness_trend = "unknown"
        average_fitness = 0.0
        last_evolution_id = None
        
        archive_path = DGC_DIR / "src" / "dgm" / "archive.json"
        if archive_path.exists():
            try:
                data = json.load(open(archive_path))
                entries = data.get("entries", [])
                archive_entries = len(entries)
                
                if entries:
                    last_evolution_id = entries[-1].get("id")
                    # Calculate fitness trend
                    fitness_scores = []
                    for e in entries[-20:]:
                        f = e.get("fitness", {})
                        if isinstance(f, dict):
                            total = sum(f.values()) / len(f) if f else 0
                            fitness_scores.append(total)
                    
                    if len(fitness_scores) >= 2:
                        first_half = sum(fitness_scores[:len(fitness_scores)//2]) / (len(fitness_scores)//2)
                        second_half = sum(fitness_scores[len(fitness_scores)//2:]) / (len(fitness_scores) - len(fitness_scores)//2)
                        delta = second_half - first_half
                        if delta > 0.05:
                            fitness_trend = "improving"
                        elif delta < -0.05:
                            fitness_trend = "declining"
                        else:
                            fitness_trend = "stable"
                        average_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
            except Exception:
                pass
        
        # Check gates config
        gates_config_valid = False
        gates_path = DGC_DIR / "swarm" / "gates.yaml"
        if gates_path.exists():
            try:
                import yaml
                yaml.safe_load(gates_path.read_text())
                gates_config_valid = True
            except Exception:
                pass
        
        # Count today's logs
        logs_today = 0
        logs_dir = DGC_DIR / "logs"
        if logs_dir.exists():
            today = datetime.now().strftime("%Y%m%d")
            for f in logs_dir.iterdir():
                if today in f.name:
                    logs_today += 1
        
        # Enforcement status
        enforcement_status = {"proposals_today": 0, "budget_remaining": 20.0}
        enforcement_path = DGC_DIR / "swarm" / "enforcement_state.json"
        if enforcement_path.exists():
            try:
                enforcement_status = json.load(open(enforcement_path))
            except Exception:
                pass
        
        return DGCStatus(
            daemon_running=daemon_running,
            daemon_pid=daemon_pid,
            archive_entries=archive_entries,
            fitness_trend=fitness_trend,
            average_fitness=average_fitness,
            gates_config_valid=gates_config_valid,
            last_evolution_id=last_evolution_id,
            logs_today=logs_today,
            enforcement_status=enforcement_status
        )
    
    def display_status(self, status: DGCStatus) -> None:
        """Display DGC status with rich formatting."""
        if not RICH_AVAILABLE:
            print(f"DGC Daemon: {'✓ Running' if status.daemon_running else '✗ Stopped'}")
            print(f"  Archive: {status.archive_entries} entries")
            print(f"  Fitness Trend: {status.fitness_trend}")
            return
        
        # Create status table
        table = Table(title="🕉️ DHARMIC_GODEL_CLAW Status", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        # Daemon
        dm_status = "[green]● Running[/]" if status.daemon_running else "[yellow]○ Stopped[/]"
        table.add_row("Daemon", dm_status, f"PID: {status.daemon_pid or 'N/A'}")
        
        # Gates Config
        gc_status = "[green]● Valid[/]" if status.gates_config_valid else "[red]○ Invalid[/]"
        table.add_row("Gates Config", gc_status, "17-gate protocol")
        
        # Archive
        table.add_row("Evolution Archive", f"[magenta]{status.archive_entries}[/]", 
                     f"Latest: {(status.last_evolution_id or 'None')[:20]}...")
        
        # Fitness Trend
        trend_color = "green" if status.fitness_trend == "improving" else "red" if status.fitness_trend == "declining" else "yellow"
        table.add_row("Fitness Trend", f"[{trend_color}]{status.fitness_trend.upper()}[/]", 
                     f"Avg: {status.average_fitness:.3f}")
        
        # Enforcement
        proposals = status.enforcement_status.get("proposals_today", 0)
        budget = status.enforcement_status.get("budget_remaining", 20.0)
        table.add_row("Enforcement", f"[blue]{proposals}/20[/]", f"Budget: ${budget:.2f}")
        
        # Today's Logs
        table.add_row("Logs Today", f"[cyan]{status.logs_today}[/]", "Log files generated")
        
        self.console.print(table)
    
    def run_gates_dry(self, proposal_id: str = "MONITOR-CHECK") -> dict:
        """Run gates in dry-run mode and return results."""
        try:
            sys.path.insert(0, str(DGC_DIR))
            from swarm.run_gates import GateRunner
            
            runner = GateRunner()
            result = runner.run_all_gates(proposal_id=proposal_id, dry_run=True)
            return {
                "overall": result.overall_result,
                "passed": result.gates_passed,
                "failed": result.gates_failed,
                "warned": result.gates_warned,
                "skipped": result.gates_skipped,
                "duration": result.total_duration_seconds
            }
        except Exception as e:
            return {"error": str(e)}
    
    def display_gates_tree(self) -> None:
        """Display the 17-gate architecture as a tree."""
        if not RICH_AVAILABLE:
            print("Gates: 8 Technical, 7 Dharmic, 2 Supply-Chain")
            return
        
        tree = Tree("🔥 [bold cyan]17-Gate Protocol[/]")
        
        # Technical Gates
        tech = tree.add("[yellow]Technical Gates (1-8)[/]")
        tech.add("[1] LINT_FORMAT - ruff")
        tech.add("[2] TYPE_CHECK - pyright --strict")
        tech.add("[3] SECURITY_SCAN - bandit + detect-secrets")
        tech.add("[4] DEPENDENCY_SAFETY - pip-audit")
        tech.add("[5] TEST_COVERAGE - pytest --cov (≥80%)")
        tech.add("[6] PROPERTY_TESTING - hypothesis")
        tech.add("[7] CONTRACT_INTEGRATION - pytest integration/")
        tech.add("[8] PERFORMANCE_REGRESSION - benchmarks")
        
        # Dharmic Gates
        dharmic = tree.add("[magenta]Dharmic Gates (9-15)[/]")
        dharmic.add("[9] AHIMSA - Non-harm (HAZARDS.md)")
        dharmic.add("[10] SATYA - Truth (claims backed by tests)")
        dharmic.add("[11] CONSENT - Human approval if risk ≥ medium")
        dharmic.add("[12] VYAVASTHIT - Telos alignment")
        dharmic.add("[13] REVERSIBILITY - ROLLBACK.md exists")
        dharmic.add("[14] SVABHAAVA - Change fits system nature")
        dharmic.add("[15] WITNESS - Audit trail + evidence hash")
        
        # Supply-Chain Gates
        supply = tree.add("[blue]Supply-Chain Gates (16-17)[/]")
        supply.add("[16] SBOM_PROVENANCE - cyclonedx + SLSA")
        supply.add("[17] LICENSE_COMPLIANCE - pip-licenses")
        
        self.console.print(tree)


# =============================================================================
# RLM SYNTHESIS INTERFACE
# =============================================================================

class RLMInterface:
    """Interface to RLM synthesis for research queries."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if RLM is available."""
        try:
            import rlm
            self.available = True
        except ImportError:
            self.available = False
    
    def synthesize(self, question: str, model: str = "deepseek/deepseek-chat") -> Optional[str]:
        """Run RLM synthesis over the research corpus."""
        if not self.available:
            return "RLM not installed. Run: pip install git+https://github.com/alexzhang13/rlm.git"
        
        try:
            import rlm
            
            # Build corpus from CLAUDE.md files and research docs
            corpus_parts = []
            
            # CLAUDE.md files
            for claude_file in [
                VAULT_DIR / "CLAUDE.md",
                MECH_INTERP_DIR / "CLAUDE.md", 
                DGC_DIR / "CLAUDE.md",
                CLAWD_DIR / "CLAUDE.md"
            ]:
                if claude_file.exists():
                    corpus_parts.append(f"=== {claude_file.name} from {claude_file.parent.name} ===\n{claude_file.read_text()[:50000]}")
            
            # Key research files
            research_files = list(VAULT_DIR.glob("*.md"))[:30]
            for rf in research_files:
                try:
                    corpus_parts.append(f"=== {rf.name} ===\n{rf.read_text()[:20000]}")
                except Exception:
                    pass
            
            corpus = "\n\n".join(corpus_parts)
            
            # RLM completion
            result = rlm.completion(
                prompt=corpus,
                root_prompt=question,
                model=model
            )
            
            return result.get("response", "No response generated")
            
        except Exception as e:
            return f"RLM synthesis error: {e}"
    
    def interactive_mode(self):
        """Run interactive RLM query mode."""
        if not RICH_AVAILABLE:
            print("Rich library required for interactive mode")
            return
        
        self.console.print(Panel(
            "RLM Synthesis Interface\n"
            "Ask questions about your research corpus.\n"
            "Type 'quit' to exit.",
            title="🧠 RLM Mode",
            border_style="cyan"
        ))
        
        while True:
            try:
                question = self.console.input("[cyan]Query:[/] ")
                if question.lower() in ["quit", "exit", "q"]:
                    break
                
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    task = progress.add_task("Synthesizing...", total=None)
                    result = self.synthesize(question)
                    progress.remove_task(task)
                
                self.console.print(Panel(result, title="Synthesis Result", border_style="green"))
                
            except KeyboardInterrupt:
                break


# =============================================================================
# UNIFIED DASHBOARD
# =============================================================================

class UnifiedDashboard:
    """Unified monitoring dashboard for OpenClaw + DGC."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.openclaw = OpenClawMonitor()
        self.dgc = DGCMonitor()
        self.rlm = RLMInterface()
    
    def show_overview(self) -> None:
        """Show unified status overview."""
        if not RICH_AVAILABLE:
            print("=" * 60)
            print("DGC + OpenClaw Monitoring Dashboard")
            print("=" * 60)
            oc_status = self.openclaw.get_status()
            self.openclaw.display_status(oc_status)
            print()
            dgc_status = self.dgc.get_status()
            self.dgc.display_status(dgc_status)
            return
        
        # Header
        self.console.print()
        self.console.print(Panel(
            "[bold cyan]DGC + OpenClaw Unified Monitoring Dashboard[/]\n"
            "[dim]Krishna Coding System • 17-Gate Protocol[/]",
            border_style="cyan"
        ))
        
        # OpenClaw Status
        oc_status = self.openclaw.get_status()
        self.openclaw.display_status(oc_status)
        
        self.console.print()
        
        # DGC Status
        dgc_status = self.dgc.get_status()
        self.dgc.display_status(dgc_status)
        
        self.console.print()
        
        # Quick Actions
        actions = Table(title="Quick Commands", box=box.SIMPLE)
        actions.add_column("Command", style="cyan")
        actions.add_column("Description", style="white")
        actions.add_row("dgc-monitor openclaw", "Detailed OpenClaw status")
        actions.add_row("dgc-monitor dgc", "Detailed DGC status")
        actions.add_row("dgc-monitor gates", "Run gate checks (dry-run)")
        actions.add_row("dgc-monitor fitness", "Show fitness trends")
        actions.add_row("dgc-monitor rlm", "RLM synthesis interface")
        actions.add_row("dgc-monitor watch", "Live dashboard mode")
        
        self.console.print(actions)
    
    def show_fitness_trends(self) -> None:
        """Show fitness evolution trends."""
        dgc_status = self.dgc.get_status()
        
        if not RICH_AVAILABLE:
            print(f"Fitness Trend: {dgc_status.fitness_trend}")
            print(f"Average Fitness: {dgc_status.average_fitness:.3f}")
            print(f"Archive Entries: {dgc_status.archive_entries}")
            return
        
        # Load archive for detailed analysis
        archive_path = DGC_DIR / "src" / "dgm" / "archive.json"
        entries = []
        if archive_path.exists():
            try:
                data = json.load(open(archive_path))
                entries = data.get("entries", [])[-20:]
            except Exception:
                pass
        
        self.console.print(Panel(
            f"[bold]Fitness Trend: [{self._trend_color(dgc_status.fitness_trend)}]{dgc_status.fitness_trend.upper()}[/][/]\n"
            f"Average Fitness: {dgc_status.average_fitness:.3f}\n"
            f"Archive Entries: {dgc_status.archive_entries}",
            title="📈 Fitness Analysis",
            border_style="magenta"
        ))
        
        if entries:
            table = Table(title="Recent Evolution Entries", box=box.ROUNDED)
            table.add_column("ID", style="cyan", max_width=12)
            table.add_column("Component", style="yellow")
            table.add_column("Type", style="magenta")
            table.add_column("Fitness", style="green")
            table.add_column("Status", style="white")
            
            for entry in entries[-10:]:
                entry_id = str(entry.get("id", ""))[:10] + "..."
                component = entry.get("component", "unknown")[:15]
                change_type = entry.get("change_type", "unknown")
                
                fitness = entry.get("fitness", {})
                if isinstance(fitness, dict):
                    f_total = sum(fitness.values()) / len(fitness) if fitness else 0
                else:
                    f_total = 0
                
                status = entry.get("status", "unknown")
                status_style = "green" if status == "applied" else "yellow" if status == "proposed" else "red"
                
                table.add_row(
                    entry_id,
                    component,
                    change_type,
                    f"{f_total:.3f}",
                    f"[{status_style}]{status}[/]"
                )
            
            self.console.print(table)
    
    def _trend_color(self, trend: str) -> str:
        """Get color for fitness trend."""
        return "green" if trend == "improving" else "red" if trend == "declining" else "yellow"
    
    def watch_mode(self, interval: int = 5) -> None:
        """Run live dashboard mode with auto-refresh."""
        if not RICH_AVAILABLE:
            print("Rich library required for watch mode")
            return
        
        def generate_dashboard():
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=3)
            )
            
            # Header
            layout["header"].update(Panel(
                f"[bold cyan]DGC + OpenClaw Live Dashboard[/] | Updated: {datetime.now().strftime('%H:%M:%S')}",
                border_style="cyan"
            ))
            
            # Main content
            oc_status = self.openclaw.get_status()
            dgc_status = self.dgc.get_status()
            
            main_content = Table(box=None, show_header=False, expand=True)
            main_content.add_column()
            main_content.add_column()
            
            # OpenClaw mini status
            oc_text = Text()
            oc_text.append("🦞 OpenClaw\n", style="bold cyan")
            oc_text.append(f"Gateway: {'● Running' if oc_status.gateway_running else '○ Stopped'}\n", 
                          style="green" if oc_status.gateway_running else "red")
            oc_text.append(f"Model: {oc_status.primary_model[:30]}\n", style="white")
            oc_text.append(f"Skills: {oc_status.skills_count}\n", style="magenta")
            
            # DGC mini status
            dgc_text = Text()
            dgc_text.append("🕉️ DGC\n", style="bold magenta")
            dgc_text.append(f"Daemon: {'● Running' if dgc_status.daemon_running else '○ Stopped'}\n",
                          style="green" if dgc_status.daemon_running else "yellow")
            dgc_text.append(f"Trend: {dgc_status.fitness_trend.upper()}\n",
                          style=self._trend_color(dgc_status.fitness_trend))
            dgc_text.append(f"Archive: {dgc_status.archive_entries} entries\n", style="white")
            
            main_content.add_row(oc_text, dgc_text)
            layout["main"].update(Panel(main_content, border_style="blue"))
            
            # Footer
            layout["footer"].update(Panel(
                "[dim]Press Ctrl+C to exit | Refreshing every 5s[/]",
                border_style="dim"
            ))
            
            return layout
        
        try:
            with Live(generate_dashboard(), refresh_per_second=0.2, screen=False) as live:
                while True:
                    time.sleep(interval)
                    live.update(generate_dashboard())
        except KeyboardInterrupt:
            self.console.print("\n[dim]Dashboard stopped[/]")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="DGC + OpenClaw Unified Monitoring Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    status      Show unified status overview (default)
    openclaw    Detailed OpenClaw status
    dgc         Detailed DGC status
    gates       Show gate architecture & run dry check
    fitness     Show fitness trends and evolution history
    rlm         Enter RLM synthesis interface
    watch       Live dashboard with auto-refresh
    
Examples:
    dgc-monitor                 # Show overview
    dgc-monitor gates           # View 17-gate architecture
    dgc-monitor rlm             # Enter RLM synthesis mode
    dgc-monitor watch           # Live monitoring
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=["status", "openclaw", "dgc", "gates", "fitness", "rlm", "watch", "help"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=5,
        help="Refresh interval for watch mode (seconds)"
    )
    
    args = parser.parse_args()
    
    dashboard = UnifiedDashboard()
    
    if args.command == "status" or args.command == "help":
        dashboard.show_overview()
    
    elif args.command == "openclaw":
        status = dashboard.openclaw.get_status()
        dashboard.openclaw.display_status(status)
        print()
        dashboard.openclaw.tail_logs()
    
    elif args.command == "dgc":
        status = dashboard.dgc.get_status()
        dashboard.dgc.display_status(status)
        print()
        dashboard.dgc.display_gates_tree()
    
    elif args.command == "gates":
        dashboard.dgc.display_gates_tree()
        print()
        if RICH_AVAILABLE:
            console = Console()
            console.print("\n[dim]Running dry-run gate check...[/]")
        result = dashboard.dgc.run_gates_dry()
        if "error" in result:
            print(f"Gate check error: {result['error']}")
        else:
            if RICH_AVAILABLE:
                console = Console()
                overall_color = "green" if result["overall"] == "PASS" else "red" if result["overall"] == "FAIL" else "yellow"
                console.print(Panel(
                    f"[{overall_color}]Overall: {result['overall']}[/]\n"
                    f"Passed: {result['passed']} | Failed: {result['failed']} | Warned: {result['warned']} | Skipped: {result['skipped']}\n"
                    f"Duration: {result['duration']:.2f}s",
                    title="Gate Check Results",
                    border_style=overall_color
                ))
            else:
                print(f"Overall: {result['overall']}")
                print(f"Passed: {result['passed']}, Failed: {result['failed']}")
    
    elif args.command == "fitness":
        dashboard.show_fitness_trends()
    
    elif args.command == "rlm":
        dashboard.rlm.interactive_mode()
    
    elif args.command == "watch":
        dashboard.watch_mode(interval=args.interval)


if __name__ == "__main__":
    main()
