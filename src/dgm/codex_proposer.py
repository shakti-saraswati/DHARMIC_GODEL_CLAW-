#!/usr/bin/env python3
"""
Codex Proposer - Fast, Cheap Code Mutation Proposals
=====================================================
Uses OpenAI Codex/GPT-4 for rapid code improvement proposals.

Strategy:
1. Check if bridge (ops/bridge/) is available → use queue system
2. Fallback: Direct OpenAI API calls

Codex is fast and cheap for generating code proposals.
Use this for the "propose" phase, then Claude/Kimi review.
"""
from __future__ import annotations

import difflib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Security integration
SRC_CORE = Path(__file__).resolve().parents[2] / "src" / "core"
if str(SRC_CORE) not in sys.path:
    sys.path.insert(0, str(SRC_CORE))

try:
    from dharmic_security import SSRFGuard
    SSRF_GUARD = SSRFGuard(allowed_domains=["api.openai.com"])
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    SSRF_GUARD = None

# Import logging with fallback
try:
    from core.dharmic_logging import get_logger
except ImportError:
    try:
        from ..core.dharmic_logging import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            logger = logging.getLogger(name)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                ))
                logger.addHandler(handler)
                logger.setLevel(logging.DEBUG)
            logger.dharmic = lambda msg, **kw: logger.info(f"[DHARMIC] {msg}")
            return logger


logger = get_logger("codex_proposer")


# Bridge paths
BRIDGE_DIR = Path(__file__).resolve().parents[2] / "ops" / "bridge"
BRIDGE_QUEUE_PATH = BRIDGE_DIR / "bridge_queue.py"
BRIDGE_EXEC_PATH = BRIDGE_DIR / "bridge_exec.py"


@dataclass
class CodexProposal:
    """
    A code improvement proposal from Codex.
    
    Attributes:
        code: The proposed new code
        diff: Unified diff between original and proposed
        explanation: What the proposal does and why
        estimated_tokens: Approximate token count used
        model_used: Which model generated this proposal
        component_path: Path to the component this proposes changes for
        constraints_applied: Which constraints were honored
        confidence: Model's self-assessed confidence (0.0-1.0)
    """
    code: str
    diff: str
    explanation: str
    estimated_tokens: int
    model_used: str
    component_path: str = ""
    constraints_applied: List[str] = field(default_factory=list)
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "diff": self.diff,
            "explanation": self.explanation,
            "estimated_tokens": self.estimated_tokens,
            "model_used": self.model_used,
            "component_path": self.component_path,
            "constraints_applied": self.constraints_applied,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodexProposal":
        """Create from dictionary."""
        return cls(
            code=data.get("code", ""),
            diff=data.get("diff", ""),
            explanation=data.get("explanation", ""),
            estimated_tokens=data.get("estimated_tokens", 0),
            model_used=data.get("model_used", "unknown"),
            component_path=data.get("component_path", ""),
            constraints_applied=data.get("constraints_applied", []),
            confidence=data.get("confidence", 0.8),
        )
    
    def is_valid(self) -> bool:
        """Check if proposal has meaningful content."""
        return bool(self.code.strip()) and bool(self.diff.strip())


class BridgeClient:
    """
    Client for the OpenClaw ↔ Codex bridge queue system.
    
    Uses the file-based queue in ops/bridge/ for task management.
    """
    
    def __init__(self, bridge_dir: Path = BRIDGE_DIR):
        self.bridge_dir = bridge_dir
        self._queue_module = None
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if bridge is available and importable."""
        queue_path = self.bridge_dir / "bridge_queue.py"
        if not queue_path.exists():
            logger.debug(f"Bridge queue not found at {queue_path}")
            return False
        
        try:
            # Add bridge to path and import
            sys.path.insert(0, str(self.bridge_dir))
            import bridge_queue
            self._queue_module = bridge_queue
            logger.info(f"Bridge queue loaded from {self.bridge_dir}")
            return True
        except ImportError as e:
            logger.warning(f"Failed to import bridge_queue: {e}")
            return False
        finally:
            if str(self.bridge_dir) in sys.path:
                sys.path.remove(str(self.bridge_dir))
    
    @property
    def available(self) -> bool:
        return self._available
    
    def enqueue(
        self,
        task: str,
        scope: List[str],
        constraints: List[str],
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Enqueue a task to the bridge."""
        if not self._available or not self._queue_module:
            return None
        
        return self._queue_module.enqueue_task(
            task=task,
            sender="codex_proposer",
            scope=scope,
            output=["code", "diff", "explanation"],
            constraints=constraints,
            payload=payload,
        )
    
    def poll_response(self, task_id: str, timeout: float = 300.0) -> Optional[Dict[str, Any]]:
        """Poll for task response."""
        if not self._available:
            return None
        
        outbox = self.bridge_dir / "outbox"
        response_path = outbox / f"{task_id}.json"
        
        start = time.time()
        while time.time() - start < timeout:
            if response_path.exists():
                try:
                    return json.loads(response_path.read_text())
                except json.JSONDecodeError:
                    pass
            time.sleep(1.0)
        
        return None
    
    def get_report(self, task_id: str) -> Optional[str]:
        """Get the report content for a completed task."""
        outbox = self.bridge_dir / "outbox"
        
        # Try different extensions
        for ext in ["md", "txt", "json"]:
            path = outbox / f"{task_id}.{ext}"
            if path.exists():
                return path.read_text()
        
        return None


class OpenAIClient:
    """
    Direct OpenAI API client for Codex/GPT-4.
    
    Uses the chat completions API with code-optimized prompts.
    """
    
    # Models ranked by speed/cost for code generation
    MODELS = [
        "gpt-4o-mini",      # Fast, cheap
        "gpt-4o",           # Fast, balanced
        "gpt-4-turbo",      # Capable
        "gpt-4",            # Most capable, slowest
    ]
    
    def __init__(self, model: Optional[str] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("CODEX_MODEL", "gpt-4o-mini")
        self._client = None
    
    @property
    def available(self) -> bool:
        return bool(self.api_key)
    
    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed, trying httpx fallback")
                self._client = "httpx"
        return self._client
    
    def complete(
        self,
        prompt: str,
        system: str = "You are a code improvement assistant. Generate clean, minimal code changes.",
        max_tokens: int = 4096,
    ) -> Tuple[str, int]:
        """
        Run a completion and return (response, tokens_used).
        """
        client = self._get_client()
        
        if client == "httpx":
            return self._complete_httpx(prompt, system, max_tokens)
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,  # Low temp for code
            )
            
            content = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else 0
            return content, tokens
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _complete_httpx(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
    ) -> Tuple[str, int]:
        """Fallback using httpx for API calls."""
        try:
            import httpx
        except ImportError:
            raise ImportError("Neither openai nor httpx package available")
        
        url = "https://api.openai.com/v1/chat/completions"
        if SECURITY_AVAILABLE and SSRF_GUARD:
            if not SSRF_GUARD.validate_url(url):
                raise PermissionError(f"SSRFGuard blocked URL: {url}")

        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return content, tokens


class CodexProposer:
    """
    Code mutation proposer using OpenAI Codex/GPT-4.
    
    Generates fast, cheap code improvement proposals that can be
    reviewed by Claude/Kimi before application.
    
    Usage:
        proposer = CodexProposer()
        proposal = proposer.propose_improvement(
            component="src/dgm/mutator.py",
            analysis="Function too long, needs decomposition",
            constraints=["max 50 lines per function", "preserve API"]
        )
        print(proposal.diff)
    """
    
    SYSTEM_PROMPT = """You are a code improvement specialist. Your job is to propose
minimal, elegant improvements to code components.

Rules:
1. Output ONLY the improved code in a ```python code block
2. Follow the analysis guidance closely
3. Honor all constraints
4. Prefer minimal changes over rewrites
5. Keep the same public API unless told otherwise
6. Add docstrings if missing
7. Never include secrets or credentials

After the code block, provide a brief explanation of what you changed and why."""

    def __init__(
        self,
        model: Optional[str] = None,
        use_bridge: bool = True,
        dry_run: bool = False,
    ):
        """
        Initialize the proposer.
        
        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
            use_bridge: Whether to use bridge queue if available
            dry_run: If True, only generate prompts without calling API
        """
        self.dry_run = dry_run
        self.model = model or os.getenv("CODEX_MODEL", "gpt-4o-mini")
        
        # Initialize clients
        self.bridge = BridgeClient() if use_bridge else None
        self.openai = OpenAIClient(model=self.model)
        
        # Track which backend is active
        self._using_bridge = use_bridge and self.bridge and self.bridge.available
        
        if self._using_bridge:
            logger.info("Using bridge queue for Codex tasks")
        elif self.openai.available:
            logger.info(f"Using direct OpenAI API with model {self.model}")
        else:
            logger.warning("No Codex backend available (no bridge, no API key)")
    
    @property
    def available(self) -> bool:
        """Check if any backend is available."""
        return self._using_bridge or self.openai.available
    
    def _read_component(self, component: str) -> str:
        """Read component source code."""
        path = Path(component).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Component not found: {component}")
        return path.read_text()
    
    def _build_prompt(
        self,
        code: str,
        analysis: str,
        constraints: List[str],
    ) -> str:
        """Build the improvement prompt."""
        constraint_block = "\n".join(f"- {c}" for c in constraints) if constraints else "- None specified"
        
        return f"""## Current Code

```python
{code}
```

## Analysis / What to Improve
{analysis}

## Constraints
{constraint_block}

## Task
Propose an improved version of this code. Output the complete improved code in a Python code block,
then explain what you changed."""
    
    def _parse_response(
        self,
        response: str,
        original_code: str,
        component_path: str,
        tokens_used: int,
    ) -> CodexProposal:
        """Parse Codex response into a proposal."""
        # Extract code block
        code = ""
        explanation = response
        
        # Find python code block
        import re
        code_match = re.search(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            # Everything after the code block is explanation
            explanation = response[code_match.end():].strip()
        
        # Generate unified diff
        diff = self._generate_diff(original_code, code, component_path)
        
        return CodexProposal(
            code=code,
            diff=diff,
            explanation=explanation or "Code improvement proposed",
            estimated_tokens=tokens_used,
            model_used=self.model,
            component_path=component_path,
            constraints_applied=[],
            confidence=0.8,
        )
    
    def _generate_diff(
        self,
        original: str,
        proposed: str,
        path: str,
    ) -> str:
        """Generate unified diff between original and proposed code."""
        original_lines = original.splitlines(keepends=True)
        proposed_lines = proposed.splitlines(keepends=True)
        
        diff_lines = list(difflib.unified_diff(
            original_lines,
            proposed_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        ))
        
        return "".join(diff_lines)
    
    def propose_improvement(
        self,
        component: str,
        analysis: str = None,
        constraints: Optional[List[str]] = None,
        parent: Any = None,
    ) -> CodexProposal:
        """
        Propose an improvement to a code component.
        
        Args:
            component: Path to the component file
            analysis: Analysis of what needs improvement (auto-generated if None)
            constraints: Style, size, or API constraints
            parent: Optional parent entry from archive for lineage-based improvements
            
        Returns:
            CodexProposal with the proposed changes
        """
        constraints = constraints or []
        
        # Generate analysis from parent if not provided
        if analysis is None:
            if parent and hasattr(parent, 'description'):
                analysis = f"Improve based on parent: {parent.description}"
            else:
                analysis = "Analyze and propose improvements for clarity, performance, and maintainability"
        
        # Read the component
        original_code = self._read_component(component)
        
        # Build prompt
        prompt = self._build_prompt(original_code, analysis, constraints)
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would propose improvement for {component}")
            return CodexProposal(
                code="",
                diff="",
                explanation=f"[DRY-RUN] Prompt generated for {component}",
                estimated_tokens=len(prompt.split()) * 2,  # Rough estimate
                model_used=self.model,
                component_path=component,
                constraints_applied=constraints,
                confidence=0.0,
            )
        
        # Try bridge first
        if self._using_bridge and self.bridge:
            proposal = self._propose_via_bridge(
                component, original_code, analysis, constraints, prompt
            )
            if proposal:
                return proposal
            logger.warning("Bridge failed, falling back to direct API")
        
        # Direct API call
        if not self.openai.available:
            raise RuntimeError("No Codex backend available (set OPENAI_API_KEY)")
        
        response, tokens = self.openai.complete(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
        )
        
        return self._parse_response(response, original_code, component, tokens)
    
    def _propose_via_bridge(
        self,
        component: str,
        original_code: str,
        analysis: str,
        constraints: List[str],
        prompt: str,
    ) -> Optional[CodexProposal]:
        """Attempt to use bridge queue for proposal."""
        if not self.bridge:
            return None
        
        task_record = self.bridge.enqueue(
            task=f"Improve code: {analysis[:100]}",
            scope=[component],
            constraints=constraints,
            payload={
                "component": component,
                "code": original_code,
                "analysis": analysis,
                "prompt": prompt,
            },
        )
        
        if not task_record:
            return None
        
        task_id = task_record["id"]
        logger.info(f"Enqueued bridge task {task_id}")
        
        # Wait for response (bridge_watcher should process it)
        response = self.bridge.poll_response(task_id, timeout=300.0)
        
        if not response or response.get("status") != "done":
            logger.warning(f"Bridge task {task_id} failed or timed out")
            return None
        
        # Get the report content
        report = self.bridge.get_report(task_id)
        if not report:
            return None
        
        # Parse the report as a response
        return self._parse_response(report, original_code, component, 0)
    
    def propose_batch(
        self,
        components: List[str],
        analysis: str,
        constraints: Optional[List[str]] = None,
        max_workers: int = 4,
    ) -> List[CodexProposal]:
        """
        Generate multiple proposals efficiently.
        
        Args:
            components: List of component paths
            analysis: Shared analysis for all components
            constraints: Shared constraints
            max_workers: Parallel workers for API calls
            
        Returns:
            List of CodexProposals (one per component)
        """
        constraints = constraints or []
        results: List[CodexProposal] = []
        
        if self.dry_run:
            # Dry run - just generate placeholder proposals
            for component in components:
                proposal = self.propose_improvement(component, analysis, constraints)
                results.append(proposal)
            return results
        
        # Use ThreadPoolExecutor for parallel API calls
        def _propose_one(component: str) -> CodexProposal:
            try:
                return self.propose_improvement(component, analysis, constraints)
            except Exception as e:
                logger.error(f"Failed to propose for {component}: {e}")
                return CodexProposal(
                    code="",
                    diff="",
                    explanation=f"Error: {e}",
                    estimated_tokens=0,
                    model_used=self.model,
                    component_path=component,
                    confidence=0.0,
                )
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_propose_one, comp): comp
                for comp in components
            }
            
            for future in as_completed(futures):
                component = futures[future]
                try:
                    proposal = future.result()
                    results.append(proposal)
                    logger.info(f"Completed proposal for {component}")
                except Exception as e:
                    logger.error(f"Exception for {component}: {e}")
                    results.append(CodexProposal(
                        code="",
                        diff="",
                        explanation=f"Exception: {e}",
                        estimated_tokens=0,
                        model_used=self.model,
                        component_path=component,
                        confidence=0.0,
                    ))
        
        return results


# CLI interface
def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Codex Code Proposer")
    parser.add_argument("component", help="Path to component file")
    parser.add_argument("--analysis", "-a", required=True, help="What to improve")
    parser.add_argument("--constraints", "-c", action="append", default=[], help="Constraints")
    parser.add_argument("--model", "-m", default=None, help="OpenAI model")
    parser.add_argument("--dry-run", action="store_true", help="Generate prompt only")
    parser.add_argument("--no-bridge", action="store_true", help="Skip bridge, use API directly")
    
    args = parser.parse_args()
    
    proposer = CodexProposer(
        model=args.model,
        use_bridge=not args.no_bridge,
        dry_run=args.dry_run,
    )
    
    if not proposer.available and not args.dry_run:
        print("Error: No Codex backend available", file=sys.stderr)
        print("Set OPENAI_API_KEY or ensure bridge is configured", file=sys.stderr)
        sys.exit(1)
    
    try:
        proposal = proposer.propose_improvement(
            component=args.component,
            analysis=args.analysis,
            constraints=args.constraints,
        )
        
        print("=" * 60)
        print(f"Component: {proposal.component_path}")
        print(f"Model: {proposal.model_used}")
        print(f"Tokens: {proposal.estimated_tokens}")
        print(f"Confidence: {proposal.confidence}")
        print("=" * 60)
        print("\n## Explanation\n")
        print(proposal.explanation)
        print("\n## Diff\n")
        print(proposal.diff or "(no diff generated)")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
