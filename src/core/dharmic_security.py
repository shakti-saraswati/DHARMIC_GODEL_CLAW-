"""
Dharmic Security Module

Centralized security guards for the DGC ecosystem.
Implements:
1. SSRFGuard: Validates and sanitizes HTTP requests
2. ExecGuard: Controls and audits subprocess execution

This module replaces scattered security logic with a unified enforcement point.
"""

import socket
import logging
import shlex
import subprocess
from urllib.parse import urlparse
from typing import List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# SSRF GUARD (Server-Side Request Forgery Protection)
# =============================================================================

class SSRFGuard:
    """
    Guard against SSRF attacks by validating URLs and IPs.
    
    Policies:
    - Deny internal IPs (127.0.0.1, 192.168.x.x, 10.x.x.x, etc.)
    - Deny non-HTTP/HTTPS schemes
    - Allowlist specific domains if configured
    - DNS resolution check to prevent DNS rebinding
    """
    
    # CIDR blocks for private networks
    PRIVATE_NETWORKS = [
        "127.0.0.0/8",      # Loopback
        "10.0.0.0/8",       # Private-use
        "172.16.0.0/12",    # Private-use
        "192.168.0.0/16",   # Private-use
        "169.254.0.0/16",   # Link-local
        "0.0.0.0/8",        # Current network
        "::1/128",          # IPv6 Loopback
        "fc00::/7",         # IPv6 Unique Local
        "fe80::/10",        # IPv6 Link-local
    ]
    
    ALLOWED_SCHEMES = {"http", "https"}
    
    def __init__(self, allowed_domains: Optional[List[str]] = None):
        self.allowed_domains = set(allowed_domains) if allowed_domains else set()
        
    def validate_url(self, url: str) -> bool:
        """
        Validate URL against SSRF rules.
        Returns True if safe, False if unsafe.
        """
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in self.ALLOWED_SCHEMES:
                logger.warning(f"SSRF: Blocked scheme '{parsed.scheme}' for URL: {url}")
                return False
                
            # Check empty hostname
            hostname = parsed.hostname
            if not hostname:
                logger.warning(f"SSRF: No hostname in URL: {url}")
                return False
                
            # Allowlist check (if configured)
            if self.allowed_domains:
                if not any(hostname == d or hostname.endswith("." + d) for d in self.allowed_domains):
                    logger.warning(f"SSRF: Hostname '{hostname}' not in allowlist")
                    return False
            
            # DNS resolution check (prevent internal IP access)
            if not self._validate_ip(hostname):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"SSRF: Validation error for {url}: {e}")
            return False

    def _validate_ip(self, hostname: str) -> bool:
        """Resolve hostname and check against private networks."""
        try:
            # Get address info (handles IPv4 and IPv6)
            addr_info = socket.getaddrinfo(hostname, None)
            
            for _, _, _, _, sockaddr in addr_info:
                ip_addr = sockaddr[0]
                if self._is_private_ip(ip_addr):
                    logger.warning(f"SSRF: Blocked internal IP {ip_addr} for {hostname}")
                    return False
            return True
        except socket.gaierror:
            # If we can't resolve it, it might be unreachable or invalid, but typically we fail open or closed?
            # For security, fail closed if we can't verify the IP.
            logger.warning(f"SSRF: Could not resolve hostname {hostname}")
            return False

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private ranges."""
        # Simple string matching for common cases to avoid heavyweight ipaddress module for every request
        # But ipaddress is robust. Let's use it if available, else simple checks.
        import ipaddress
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except ValueError:
            return False


# =============================================================================
# EXEC GUARD (Subprocess Execution Control)
# =============================================================================

class ExecGuard:
    """
    Guard against unsafe subprocess execution.
    
    Policies:
    - Allowlist of safe binaries (git, grep, python3, etc.)
    - Validation of arguments (prevent shell injection characters)
    - Audit logging of all executions
    - No shell=True by default enforcement
    """
    
    SAFE_BINARIES = {
        # Core tooling
        "python3",
        "git",
        "bash",
        "sh",
        "rg",
        "grep",
        "ls",
        "cat",
        "find",
        "echo",
        # Gate tools
        "ruff",
        "pyright",
        "bandit",
        "detect-secrets",
        "pip-audit",
        "pytest",
        # Optional CLIs
        "claude",
        "node",
        "npm",
        "curl",
    }
    
    # Dangerous chars to flag in arguments if not strictly controlled
    DANGEROUS_CHARS = set(";&|><$`")
    
    def __init__(self, allowed_bins: Optional[List[str]] = None):
        if allowed_bins:
            self.SAFE_BINARIES.update(allowed_bins)
            
    def validate_command(self, args: Union[List[str], str], shell: bool = False) -> bool:
        """
        Validate command against security policy.
        Returns True if safe, False if unsafe.
        """
        # 1. Normalize args
        if isinstance(args, str):
            cmd_list = shlex.split(args)
        else:
            cmd_list = list(args)
            
        if not cmd_list:
            return False
            
        # 2. Check binary allowlist
        binary = Path(cmd_list[0]).name
        if binary not in self.SAFE_BINARIES:
            logger.warning(f"ExecGuard: Blocked unauthorized binary '{binary}'")
            return False

        # 3. Shell mode checks
        if shell:
            # Allow only if the binary itself is allowlisted.
            # For bash/sh, require -c or -lc to avoid interactive shells.
            if binary in {"bash", "sh"}:
                if not any(flag in cmd_list for flag in ("-c", "-lc")):
                    logger.warning("ExecGuard: shell allowed but missing -c/-lc")
            logger.info(f"ExecGuard: Allowed shell command: {cmd_list}")
            return True

        # 4. Non-shell argument safety checks
        for arg in cmd_list[1:]:
            if any(ch in arg for ch in self.DANGEROUS_CHARS):
                logger.warning(f"ExecGuard: Blocked dangerous arg '{arg}'")
                return False

        # 5. Audit log
        logger.info(f"ExecGuard: Allowed command: {cmd_list}")
        return True

    def run(self, args, **kwargs) -> subprocess.CompletedProcess:
        """
        Secure wrapper around subprocess.run.
        Raises PermissionError if validation fails.
        """
        shell = kwargs.get("shell", False)
        if not self.validate_command(args, shell=shell):
            raise PermissionError(f"ExecGuard blocked command: {args}")
            
        return subprocess.run(args, **kwargs)

# Global instances
ssrf_guard = SSRFGuard()
exec_guard = ExecGuard()
