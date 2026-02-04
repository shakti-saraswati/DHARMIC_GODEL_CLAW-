#!/usr/bin/env python3
"""
DHARMIC_CLAW Protocol v3 - Multi-Agent File Locking

Prevents race conditions when multiple agents modify files.
Uses file-based locks with TTL to prevent deadlocks.

Usage:
    from swarm.file_lock import FileLock
    
    with FileLock("path/to/file.py", agent_id="CODING_AGENT") as lock:
        # Modify file safely
        pass
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import fcntl
import hashlib

# =============================================================================
# CONSTANTS
# =============================================================================

LOCK_DIR = Path(__file__).parent.parent / ".locks"
DEFAULT_TTL_SECONDS = 300  # 5 minutes
LOCK_POLL_INTERVAL = 0.1  # 100ms

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LockInfo:
    """Information about an active lock."""
    file_path: str
    agent_id: str
    acquired_at: str
    expires_at: str
    ttl_seconds: int
    lock_id: str

# =============================================================================
# FILE LOCK
# =============================================================================

class FileLockError(Exception):
    """Raised when a file lock cannot be acquired."""
    pass

class FileLockTimeout(FileLockError):
    """Raised when lock acquisition times out."""
    pass

class FileLockBusy(FileLockError):
    """Raised when file is locked by another agent."""
    def __init__(self, message: str, holder: Optional[LockInfo] = None):
        super().__init__(message)
        self.holder = holder

class FileLock:
    """
    File-based locking with TTL for multi-agent safety.
    
    Features:
    - Atomic lock acquisition using flock
    - TTL prevents deadlocks from crashed agents
    - Lock info stored as JSON for debugging
    - Context manager support
    
    Example:
        with FileLock("src/module.py", agent_id="CODING_AGENT", ttl=60) as lock:
            # File is locked for 60 seconds
            with open("src/module.py", "w") as f:
                f.write(new_content)
    """
    
    def __init__(
        self,
        file_path: str | Path,
        agent_id: str,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        timeout_seconds: int = 30,
        force: bool = False
    ):
        """
        Initialize file lock.
        
        Args:
            file_path: Path to the file to lock
            agent_id: Identifier for the locking agent
            ttl_seconds: Time-to-live for the lock (prevents deadlocks)
            timeout_seconds: How long to wait for lock acquisition
            force: If True, break expired locks automatically
        """
        self.file_path = Path(file_path).resolve()
        self.agent_id = agent_id
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self.force = force
        
        # Generate lock paths
        file_hash = hashlib.md5(str(self.file_path).encode()).hexdigest()[:12]
        self.lock_file = LOCK_DIR / f"{file_hash}.lock"
        self.info_file = LOCK_DIR / f"{file_hash}.info.json"
        
        self._lock_fd: Optional[int] = None
        self._lock_info: Optional[LockInfo] = None
    
    def acquire(self) -> "FileLock":
        """
        Acquire the file lock.
        
        Raises:
            FileLockTimeout: If lock cannot be acquired within timeout
            FileLockBusy: If file is locked by another agent (and not expired)
        """
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        while True:
            # Check for existing lock
            existing = self._read_lock_info()
            
            if existing:
                # Check if expired
                expires_at = datetime.fromisoformat(existing.expires_at)
                if datetime.now(timezone.utc) > expires_at:
                    if self.force:
                        self._break_lock(existing)
                    else:
                        # Lock expired but not forcing - warn and break
                        print(f"⚠️  Breaking expired lock held by {existing.agent_id}")
                        self._break_lock(existing)
                elif existing.agent_id == self.agent_id:
                    # Same agent - refresh lock
                    pass
                else:
                    # Another agent holds the lock
                    if time.time() - start_time > self.timeout_seconds:
                        raise FileLockTimeout(
                            f"Timeout waiting for lock on {self.file_path}"
                        )
                    time.sleep(LOCK_POLL_INTERVAL)
                    continue
            
            # Try to acquire lock
            try:
                self._lock_fd = os.open(
                    str(self.lock_file),
                    os.O_CREAT | os.O_RDWR
                )
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # Write lock info
                self._write_lock_info()
                return self
                
            except (IOError, OSError) as e:
                if self._lock_fd is not None:
                    os.close(self._lock_fd)
                    self._lock_fd = None
                
                if time.time() - start_time > self.timeout_seconds:
                    raise FileLockTimeout(
                        f"Timeout waiting for lock on {self.file_path}"
                    )
                
                time.sleep(LOCK_POLL_INTERVAL)
    
    def release(self) -> None:
        """Release the file lock."""
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            except (IOError, OSError):
                pass
            finally:
                self._lock_fd = None
        
        # Remove lock files
        try:
            self.lock_file.unlink(missing_ok=True)
            self.info_file.unlink(missing_ok=True)
        except (IOError, OSError):
            pass
    
    def refresh(self) -> None:
        """Refresh the lock TTL."""
        if self._lock_fd is None:
            raise FileLockError("Cannot refresh - lock not held")
        
        self._write_lock_info()
    
    def _read_lock_info(self) -> Optional[LockInfo]:
        """Read existing lock info if present."""
        if not self.info_file.exists():
            return None
        
        try:
            with open(self.info_file) as f:
                data = json.load(f)
            return LockInfo(**data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
    
    def _write_lock_info(self) -> None:
        """Write lock info to disk."""
        now = datetime.now(timezone.utc)
        expires = now.timestamp() + self.ttl_seconds
        
        self._lock_info = LockInfo(
            file_path=str(self.file_path),
            agent_id=self.agent_id,
            acquired_at=now.isoformat(),
            expires_at=datetime.fromtimestamp(expires, timezone.utc).isoformat(),
            ttl_seconds=self.ttl_seconds,
            lock_id=hashlib.md5(f"{self.file_path}{now.isoformat()}".encode()).hexdigest()[:8]
        )
        
        with open(self.info_file, "w") as f:
            json.dump(asdict(self._lock_info), f, indent=2)
    
    def _break_lock(self, existing: LockInfo) -> None:
        """Break an existing lock (for expired locks)."""
        print(f"🔓 Breaking lock: {existing.lock_id} (held by {existing.agent_id})")
        
        try:
            self.lock_file.unlink(missing_ok=True)
            self.info_file.unlink(missing_ok=True)
        except (IOError, OSError):
            pass
    
    def __enter__(self) -> "FileLock":
        return self.acquire()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
    
    @property
    def is_held(self) -> bool:
        """Check if this instance holds the lock."""
        return self._lock_fd is not None
    
    @property
    def info(self) -> Optional[LockInfo]:
        """Get lock info if held."""
        return self._lock_info


# =============================================================================
# LOCK MANAGER
# =============================================================================

class LockManager:
    """
    Manages multiple file locks for batch operations.
    
    Example:
        manager = LockManager(agent_id="CODING_AGENT")
        with manager.lock_files(["a.py", "b.py"]) as locks:
            # Both files locked
            pass
    """
    
    def __init__(self, agent_id: str, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.agent_id = agent_id
        self.ttl_seconds = ttl_seconds
        self._locks: list[FileLock] = []
    
    def lock_files(self, file_paths: list[str | Path]) -> "LockManager":
        """
        Acquire locks on multiple files.
        
        Files are locked in sorted order to prevent deadlocks.
        """
        # Sort paths to prevent deadlock
        sorted_paths = sorted(str(p) for p in file_paths)
        
        try:
            for path in sorted_paths:
                lock = FileLock(path, self.agent_id, self.ttl_seconds)
                lock.acquire()
                self._locks.append(lock)
            return self
        except FileLockError:
            # Release any acquired locks on failure
            self.release_all()
            raise
    
    def release_all(self) -> None:
        """Release all held locks."""
        for lock in self._locks:
            try:
                lock.release()
            except Exception:
                pass
        self._locks = []
    
    def __enter__(self) -> "LockManager":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release_all()


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for testing file locks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="File lock utility")
    parser.add_argument("action", choices=["lock", "unlock", "status"])
    parser.add_argument("file", help="File to lock")
    parser.add_argument("--agent", default="CLI", help="Agent ID")
    parser.add_argument("--ttl", type=int, default=60, help="TTL in seconds")
    
    args = parser.parse_args()
    
    if args.action == "lock":
        lock = FileLock(args.file, args.agent, args.ttl)
        lock.acquire()
        print(f"✓ Locked {args.file} for {args.ttl}s")
        print(f"  Lock ID: {lock.info.lock_id}")
        print(f"  Expires: {lock.info.expires_at}")
        # Note: lock released on exit
        
    elif args.action == "status":
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        locks = list(LOCK_DIR.glob("*.info.json"))
        if not locks:
            print("No active locks")
        else:
            print(f"Active locks: {len(locks)}")
            for info_file in locks:
                with open(info_file) as f:
                    info = json.load(f)
                expires = datetime.fromisoformat(info["expires_at"])
                expired = "EXPIRED" if datetime.now(timezone.utc) > expires else "active"
                print(f"  {info['file_path']}: {info['agent_id']} ({expired})")


if __name__ == "__main__":
    main()
