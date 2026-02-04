#!/usr/bin/env python3
"""
Delegation Router — Unified sub-agent dispatch
==============================================

Allows DHARMIC CLAW to delegate tasks to various backends:
- Clawdbot sessions_spawn (when model allowlist is fixed)
- Claude CLI (when credits available)
- Direct Kimi API (bypassing Clawdbot's broken integration)
- OpenAI/Codex (when configured)

Usage:
    from delegation_router import delegate
    
    result = await delegate(
        task="Analyze this code for bugs",
        backend="kimi",  # or "claude-cli", "codex", "clawdbot"
        context={"file": "path/to/file.py"}
    )
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class Backend(Enum):
    KIMI_DIRECT = "kimi"           # Direct Moonshot API (bypass Clawdbot)
    CLAUDE_CLI = "claude-cli"       # Claude Code CLI
    CODEX = "codex"                 # OpenAI Codex
    CLAWDBOT = "clawdbot"           # Clawdbot sessions_spawn


@dataclass
class DelegationResult:
    success: bool
    backend: str
    response: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class DelegationRouter:
    """Routes tasks to the best available backend."""
    
    def __init__(self):
        self.kimi_client = None
        self._init_backends()
    
    def _init_backends(self):
        """Initialize available backends."""
        # Kimi direct (bypass Clawdbot's broken integration)
        kimi_key = os.environ.get("MOONSHOT_API_KEY")
        if kimi_key and OPENAI_AVAILABLE:
            self.kimi_client = AsyncOpenAI(
                api_key=kimi_key,
                base_url="https://api.moonshot.ai/v1"
            )
        
        # Claude CLI path
        self.claude_cli_path = Path.home() / ".npm-global" / "bin" / "claude"
        
        # OpenAI/Codex
        self.openai_key = os.environ.get("OPENAI_API_KEY")
    
    def get_available_backends(self) -> list:
        """List backends that are currently available."""
        available = []
        
        if self.kimi_client:
            available.append(Backend.KIMI_DIRECT)
        
        if self.claude_cli_path.exists():
            # Note: May still fail if credits depleted
            available.append(Backend.CLAUDE_CLI)
        
        if self.openai_key and OPENAI_AVAILABLE:
            available.append(Backend.CODEX)
        
        # Clawdbot always "available" but may have issues
        available.append(Backend.CLAWDBOT)
        
        return available
    
    async def delegate(
        self,
        task: str,
        backend: str = "auto",
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> DelegationResult:
        """
        Delegate a task to a sub-agent.
        
        Args:
            task: The task description
            backend: Which backend to use ("auto", "kimi", "claude-cli", "codex", "clawdbot")
            context: Optional context dict
            max_tokens: Max response tokens
            temperature: Generation temperature
        
        Returns:
            DelegationResult with response or error
        """
        if backend == "auto":
            backend = self._select_best_backend(task)
        
        try:
            backend_enum = Backend(backend)
        except ValueError:
            return DelegationResult(
                success=False,
                backend=backend,
                error=f"Unknown backend: {backend}"
            )
        
        # Route to appropriate handler
        if backend_enum == Backend.KIMI_DIRECT:
            return await self._delegate_kimi(task, context, max_tokens, temperature)
        elif backend_enum == Backend.CLAUDE_CLI:
            return await self._delegate_claude_cli(task, context)
        elif backend_enum == Backend.CODEX:
            return await self._delegate_codex(task, context, max_tokens, temperature)
        elif backend_enum == Backend.CLAWDBOT:
            return await self._delegate_clawdbot(task, context)
        else:
            return DelegationResult(
                success=False,
                backend=backend,
                error="Backend not implemented"
            )
    
    def _select_best_backend(self, task: str) -> str:
        """Auto-select the best backend for a task."""
        # Prefer Kimi for research/analysis (cheap, fast)
        if self.kimi_client:
            return "kimi"
        # Fall back to Clawdbot
        return "clawdbot"
    
    async def _delegate_kimi(
        self,
        task: str,
        context: Optional[Dict[str, Any]],
        max_tokens: int,
        temperature: float
    ) -> DelegationResult:
        """Delegate to Kimi via direct Moonshot API."""
        if not self.kimi_client:
            return DelegationResult(
                success=False,
                backend="kimi",
                error="Kimi client not initialized (missing MOONSHOT_API_KEY)"
            )
        
        try:
            # Build prompt with context
            prompt = task
            if context:
                prompt = f"Context: {json.dumps(context)}\n\nTask: {task}"
            
            response = await self.kimi_client.chat.completions.create(
                model="kimi-k2.5",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=1.0  # Kimi K2.5 only allows temperature=1
            )
            
            return DelegationResult(
                success=True,
                backend="kimi",
                response=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens if response.usage else None
            )
            
        except Exception as e:
            return DelegationResult(
                success=False,
                backend="kimi",
                error=str(e)
            )
    
    async def _delegate_claude_cli(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> DelegationResult:
        """Delegate to Claude Code CLI."""
        if not self.claude_cli_path.exists():
            return DelegationResult(
                success=False,
                backend="claude-cli",
                error="Claude CLI not found"
            )
        
        try:
            # Build prompt
            prompt = task
            if context:
                prompt = f"Context: {json.dumps(context)}\n\nTask: {task}"
            
            # Run Claude CLI
            result = subprocess.run(
                [str(self.claude_cli_path), "-p", "--print"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if "Credit balance is too low" in result.stdout:
                return DelegationResult(
                    success=False,
                    backend="claude-cli",
                    error="Anthropic credits depleted"
                )
            
            return DelegationResult(
                success=True,
                backend="claude-cli",
                response=result.stdout
            )
            
        except subprocess.TimeoutExpired:
            return DelegationResult(
                success=False,
                backend="claude-cli",
                error="Timeout"
            )
        except Exception as e:
            return DelegationResult(
                success=False,
                backend="claude-cli",
                error=str(e)
            )
    
    async def _delegate_codex(
        self,
        task: str,
        context: Optional[Dict[str, Any]],
        max_tokens: int,
        temperature: float
    ) -> DelegationResult:
        """Delegate to OpenAI Codex."""
        if not self.openai_key or not OPENAI_AVAILABLE:
            return DelegationResult(
                success=False,
                backend="codex",
                error="OpenAI not configured"
            )
        
        try:
            client = AsyncOpenAI(api_key=self.openai_key)
            
            prompt = task
            if context:
                prompt = f"Context: {json.dumps(context)}\n\nTask: {task}"
            
            response = await client.chat.completions.create(
                model="gpt-4o",  # or codex model if available
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return DelegationResult(
                success=True,
                backend="codex",
                response=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens if response.usage else None
            )
            
        except Exception as e:
            return DelegationResult(
                success=False,
                backend="codex",
                error=str(e)
            )
    
    async def _delegate_clawdbot(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> DelegationResult:
        """Delegate via Clawdbot sessions_spawn."""
        # This would call Clawdbot's API
        # For now, return not implemented
        return DelegationResult(
            success=False,
            backend="clawdbot",
            error="Use sessions_spawn tool directly from agent"
        )


# Singleton instance
_router = None

def get_router() -> DelegationRouter:
    global _router
    if _router is None:
        _router = DelegationRouter()
    return _router


async def delegate(
    task: str,
    backend: str = "auto",
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> DelegationResult:
    """Convenience function to delegate a task."""
    router = get_router()
    return await router.delegate(task, backend, context, **kwargs)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    async def main():
        router = DelegationRouter()
        print("Available backends:", [b.value for b in router.get_available_backends()])
        
        if len(sys.argv) > 1:
            task = " ".join(sys.argv[1:])
            result = await router.delegate(task, backend="auto")
            print(f"\nBackend: {result.backend}")
            print(f"Success: {result.success}")
            if result.response:
                print(f"Response: {result.response[:500]}...")
            if result.error:
                print(f"Error: {result.error}")
    
    asyncio.run(main())
