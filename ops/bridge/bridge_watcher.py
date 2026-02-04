#!/usr/bin/env python3
"""
Bridge Watcher Daemon

Monitors inbox for pending tasks and executes them via bridge_exec.
Runs as a long-lived daemon with graceful shutdown support.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bridge_queue import list_pending, init_dirs, BASE_DIR

# Configuration
DEFAULT_POLL_INTERVAL = 30  # seconds
DEFAULT_EXEC_TIMEOUT = 300  # seconds
LOG_FILE = BASE_DIR / "bridge_watcher.log"
PID_FILE = BASE_DIR / "bridge_watcher.pid"

# Global shutdown flag
_shutdown_requested = False


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging to file and optionally stdout."""
    logger = logging.getLogger("bridge_watcher")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # File handler (always)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Stdout handler (if verbose or not daemonized)
    if verbose or sys.stdout.isatty():
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        stdout_handler.setFormatter(stdout_formatter)
        logger.addHandler(stdout_handler)
    
    return logger


def _signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logging.getLogger("bridge_watcher").info(f"Received {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True


def install_signal_handlers() -> None:
    """Install handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)


def write_pid() -> None:
    """Write current PID to file for process management."""
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid() -> None:
    """Remove PID file on shutdown."""
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)


def run_bridge_exec(
    task_id: str,
    dry_run: bool = False,
    timeout: int = DEFAULT_EXEC_TIMEOUT,
    logger: Optional[logging.Logger] = None,
) -> tuple[bool, str]:
    """
    Execute bridge_exec.py for a specific task.
    
    Returns:
        (success: bool, message: str)
    """
    logger = logger or logging.getLogger("bridge_watcher")
    
    exec_script = BASE_DIR / "bridge_exec.py"
    if not exec_script.exists():
        return False, f"bridge_exec.py not found at {exec_script}"
    
    cmd = [
        sys.executable,
        str(exec_script),
        "--id", task_id,
        "--by", "bridge_watcher",
        "--timeout", str(timeout),
    ]
    
    if dry_run:
        cmd.append("--dry-run")
    
    logger.debug(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30,  # Extra buffer beyond exec's internal timeout
            cwd=str(BASE_DIR),
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip() or "Task completed successfully"
        else:
            return False, result.stderr.strip() or f"Exit code: {result.returncode}"
            
    except subprocess.TimeoutExpired:
        return False, f"Subprocess timed out after {timeout + 30}s"
    except Exception as exc:
        return False, f"Subprocess error: {exc}"


def process_pending_tasks(
    dry_run: bool = False,
    timeout: int = DEFAULT_EXEC_TIMEOUT,
    logger: Optional[logging.Logger] = None,
) -> int:
    """
    Process all pending tasks in inbox.
    
    Returns:
        Number of tasks processed
    """
    global _shutdown_requested
    logger = logger or logging.getLogger("bridge_watcher")
    
    pending = list_pending()
    if not pending:
        logger.debug("No pending tasks")
        return 0
    
    processed = 0
    for task in pending:
        if _shutdown_requested:
            logger.info("Shutdown requested, stopping task processing")
            break
        
        task_id = task.get("id", "unknown")
        task_desc = task.get("task", "")[:50]
        
        if task.get("error"):
            logger.warning(f"Skipping unreadable task: {task_id}")
            continue
        
        logger.info(f"Processing task {task_id}: {task_desc}...")
        
        success, message = run_bridge_exec(
            task_id=task_id,
            dry_run=dry_run,
            timeout=timeout,
            logger=logger,
        )
        
        if success:
            logger.info(f"✓ Task {task_id} completed: {message[:100]}")
        else:
            logger.error(f"✗ Task {task_id} failed: {message[:200]}")
        
        processed += 1
    
    return processed


def daemon_loop(
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    dry_run: bool = False,
    timeout: int = DEFAULT_EXEC_TIMEOUT,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Main daemon loop.
    
    Args:
        poll_interval: Seconds between inbox checks
        dry_run: If True, don't actually run Codex
        timeout: Timeout for each task execution
        max_iterations: If set, exit after N iterations (for testing)
    """
    global _shutdown_requested
    
    logger = logging.getLogger("bridge_watcher")
    logger.info("=" * 50)
    logger.info(f"Bridge Watcher starting (PID: {os.getpid()})")
    logger.info(f"  Poll interval: {poll_interval}s")
    logger.info(f"  Exec timeout: {timeout}s")
    logger.info(f"  Dry run: {dry_run}")
    logger.info(f"  Inbox: {BASE_DIR / 'inbox'}")
    logger.info("=" * 50)
    
    init_dirs()
    write_pid()
    
    iteration = 0
    try:
        while not _shutdown_requested:
            iteration += 1
            
            # Check iteration limit (for testing)
            if max_iterations and iteration > max_iterations:
                logger.info(f"Reached max iterations ({max_iterations}), exiting")
                break
            
            # Process pending tasks
            try:
                processed = process_pending_tasks(
                    dry_run=dry_run,
                    timeout=timeout,
                    logger=logger,
                )
                if processed > 0:
                    logger.info(f"Processed {processed} task(s) in iteration {iteration}")
            except Exception as exc:
                logger.exception(f"Error processing tasks: {exc}")
            
            # Sleep with interrupt check
            if not _shutdown_requested:
                logger.debug(f"Sleeping {poll_interval}s...")
                # Sleep in small increments to respond to signals quickly
                sleep_elapsed = 0
                while sleep_elapsed < poll_interval and not _shutdown_requested:
                    time.sleep(min(1, poll_interval - sleep_elapsed))
                    sleep_elapsed += 1
    
    finally:
        cleanup_pid()
        logger.info("Bridge Watcher shutdown complete")


def status() -> dict:
    """Check watcher status."""
    result = {
        "running": False,
        "pid": None,
        "log_file": str(LOG_FILE),
        "pid_file": str(PID_FILE),
    }
    
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is running
            os.kill(pid, 0)
            result["running"] = True
            result["pid"] = pid
        except (ValueError, ProcessLookupError, PermissionError):
            result["stale_pid"] = True
    
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bridge Watcher Daemon - monitors inbox and executes tasks"
    )
    
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between inbox checks (default: {DEFAULT_POLL_INTERVAL})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_EXEC_TIMEOUT,
        help=f"Timeout for each task in seconds (default: {DEFAULT_EXEC_TIMEOUT})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process tasks but don't actually run Codex"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process pending tasks once and exit (no daemon loop)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check if watcher is running"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Exit after N iterations (for testing)"
    )
    
    args = parser.parse_args()
    
    # Status check
    if args.status:
        import json
        print(json.dumps(status(), indent=2))
        return 0
    
    # Setup
    logger = setup_logging(verbose=args.verbose)
    install_signal_handlers()
    
    # Single-shot mode
    if args.once:
        logger.info("Running in single-shot mode")
        processed = process_pending_tasks(
            dry_run=args.dry_run,
            timeout=args.timeout,
            logger=logger,
        )
        logger.info(f"Processed {processed} task(s)")
        return 0
    
    # Daemon mode
    daemon_loop(
        poll_interval=args.poll_interval,
        dry_run=args.dry_run,
        timeout=args.timeout,
        max_iterations=args.max_iterations,
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
