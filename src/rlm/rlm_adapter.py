"""
RLM Adapter for DHARMIC_GODEL_CLAW

Implements Recursive Language Model pattern from MIT's RLM paper:
- Context stored as Python variable (not in prompt)
- LLM can programmatically examine, decompose, and recursively call itself
- Handles 100k+ tokens by treating context as external data
- Uses Python REPL environment for code execution
- Avoids "context rot" by never clogging the context window

Key features:
- recursive_complete(query, context, max_depth) - Main API
- recursive_llm(subquery, context_slice) available in REPL
- FINAL(answer) / FINAL_VAR(var_name) to return answers
- Integration with PSMV vault (8000+ files)
- Integration with codebase for self-improvement context
"""

import asyncio
import io
import os
import re
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# Try importing LLM clients
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


# ==============================================================================
# Exceptions
# ==============================================================================

class RLMError(Exception):
    """Base error for RLM operations."""
    pass


class MaxIterationsError(RLMError):
    """Max iterations exceeded without finding final answer."""
    pass


class MaxDepthError(RLMError):
    """Max recursion depth exceeded."""
    pass


class REPLExecutionError(RLMError):
    """Error during REPL code execution."""
    pass


# ==============================================================================
# Types and Config
# ==============================================================================

@dataclass
class RLMConfig:
    """Configuration for RLM adapter."""
    # Model settings
    model: str = "claude-opus-4"
    recursive_model: Optional[str] = None  # Cheaper model for recursive calls
    backend: str = "proxy"  # "proxy", "direct", "litellm", "kimi"
    
    # API settings  
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    
    # Execution limits
    max_depth: int = 3
    max_iterations: int = 30
    timeout_seconds: int = 300
    
    # Output settings
    max_output_chars: int = 4000  # Truncate REPL output
    verbose: bool = False
    
    # Model-specific kwargs
    model_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RLMResult:
    """Result from RLM completion."""
    answer: str
    iterations: int
    depth: int
    llm_calls: int
    execution_time: float
    final_vars: Dict[str, Any] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)


# ==============================================================================
# Safe REPL Environment
# ==============================================================================

# Safe builtins - blocks dangerous operations
SAFE_BUILTINS = {
    # Core types and functions
    "print": print,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "bool": bool,
    "type": type,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "reversed": reversed,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "any": any,
    "all": all,
    "pow": pow,
    "divmod": divmod,
    "chr": chr,
    "ord": ord,
    "hex": hex,
    "bin": bin,
    "oct": oct,
    "repr": repr,
    "ascii": ascii,
    "format": format,
    "hash": hash,
    "id": id,
    "iter": iter,
    "next": next,
    "slice": slice,
    "callable": callable,
    "hasattr": hasattr,
    "getattr": getattr,
    "setattr": setattr,
    "delattr": delattr,
    "dir": dir,
    "vars": vars,
    "bytes": bytes,
    "bytearray": bytearray,
    "complex": complex,
    "object": object,
    "super": super,
    "property": property,
    "staticmethod": staticmethod,
    "classmethod": classmethod,
    "__import__": __import__,
    "open": open,  # Needed for file operations in temp dir
    
    # Exceptions
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "AttributeError": AttributeError,
    "FileNotFoundError": FileNotFoundError,
    "RuntimeError": RuntimeError,
    "StopIteration": StopIteration,
    
    # Blocked dangerous operations
    "input": None,
    "eval": None,
    "exec": None,
    "compile": None,
    "globals": None,
    "locals": None,
}


class REPLEnvironment:
    """
    Sandboxed Python REPL for RLM.
    
    Provides:
    - context: The main context variable
    - query: The user's query
    - recursive_llm(subquery, context_slice): Recursive LLM call
    - FINAL(answer): Return final answer
    - FINAL_VAR(var_name): Return variable as answer
    - SHOW_VARS(): Show available variables
    """
    
    def __init__(
        self,
        context: Union[str, Dict, List],
        query: str,
        recursive_fn: Callable,
        depth: int = 0,
        max_output_chars: int = 4000,
    ):
        self.context = context
        self.query = query
        self.recursive_fn = recursive_fn
        self.depth = depth
        self.max_output_chars = max_output_chars
        
        # Create temp directory for file operations
        self.temp_dir = tempfile.mkdtemp(prefix="rlm_repl_")
        
        # Setup namespace
        self.globals: Dict[str, Any] = {"__builtins__": SAFE_BUILTINS.copy()}
        self.locals: Dict[str, Any] = {}
        
        # Add standard library modules (read-only)
        import re as re_module
        import json as json_module
        import math
        from datetime import datetime, timedelta
        from collections import Counter, defaultdict
        
        self.globals.update({
            "re": re_module,
            "json": json_module,
            "math": math,
            "datetime": datetime,
            "timedelta": timedelta,
            "Counter": Counter,
            "defaultdict": defaultdict,
        })
        
        # Add RLM-specific functions
        self.globals["context"] = self.context
        self.globals["query"] = self.query
        self.globals["recursive_llm"] = self._recursive_llm_wrapper
        self.globals["llm_query"] = self._recursive_llm_wrapper  # Alias
        self.globals["FINAL"] = self._final
        self.globals["FINAL_VAR"] = self._final_var
        self.globals["SHOW_VARS"] = self._show_vars
        
        # For tracking final answer
        self._final_answer: Optional[str] = None
        self._final_called = False
        self._lock = threading.Lock()
        
    def _recursive_llm_wrapper(self, subquery: str, sub_context: str = "") -> str:
        """Wrapper for recursive LLM calls from REPL."""
        if not sub_context:
            sub_context = subquery
            subquery = ""
        return self.recursive_fn(subquery, sub_context)
    
    def _final(self, answer: Any) -> str:
        """Mark final answer and return it."""
        self._final_called = True
        self._final_answer = str(answer)
        return f"FINAL: {self._final_answer}"
    
    def _final_var(self, var_name: str) -> str:
        """Return a variable as the final answer."""
        var_name = var_name.strip().strip("\"'")
        
        if var_name in self.locals:
            self._final_called = True
            self._final_answer = str(self.locals[var_name])
            return f"FINAL_VAR({var_name}): {self._final_answer}"
        
        # Provide helpful error
        available = [k for k in self.locals.keys() if not k.startswith("_")]
        if available:
            return (
                f"Error: Variable '{var_name}' not found. "
                f"Available: {available}. "
                f"Create variable in REPL first, then call FINAL_VAR."
            )
        return (
            f"Error: Variable '{var_name}' not found. "
            f"No variables created yet. Use REPL to create variables first."
        )
    
    def _show_vars(self) -> str:
        """Show available variables."""
        available = {
            k: f"{type(v).__name__}({len(str(v))} chars)" 
            for k, v in self.locals.items() 
            if not k.startswith("_")
        }
        if not available:
            return "No variables created yet. Use ```repl``` blocks to create variables."
        return f"Available variables: {available}"
    
    def execute(self, code: str) -> str:
        """
        Execute Python code in the sandbox.
        
        Returns:
            stdout/stderr output (truncated if necessary)
        """
        # Extract code from markdown blocks if present
        code = self._extract_code(code)
        
        if not code.strip():
            return "No code to execute"
        
        # Capture stdout/stderr
        with self._lock:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
            
            try:
                sys.stdout, sys.stderr = stdout_buf, stderr_buf
                
                # Change to temp directory
                old_cwd = os.getcwd()
                try:
                    os.chdir(self.temp_dir)
                    
                    # Execute code
                    combined = {**self.globals, **self.locals}
                    exec(code, combined, combined)
                    
                    # Update locals with new variables
                    for key, value in combined.items():
                        if key not in self.globals and not key.startswith("_"):
                            self.locals[key] = value
                    
                    stdout = stdout_buf.getvalue()
                    stderr = stderr_buf.getvalue()
                    
                finally:
                    os.chdir(old_cwd)
                    
            except Exception as e:
                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue() + f"\n{type(e).__name__}: {e}"
                
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
        
        # Combine output
        output = stdout
        if stderr:
            output += f"\n[stderr]: {stderr}"
        
        # Truncate if necessary (as per paper)
        if len(output) > self.max_output_chars:
            truncated = output[:self.max_output_chars]
            output = f"{truncated}\n\n[Output truncated: {len(output)} chars total, showing first {self.max_output_chars}]"
        
        return output.strip() if output.strip() else "Code executed successfully (no output)"
    
    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code blocks."""
        # Try ```repl blocks first (preferred)
        repl_match = re.search(r'```repl\s*(.*?)\s*```', text, re.DOTALL)
        if repl_match:
            return repl_match.group(1)
        
        # Try ```python blocks
        python_match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
        if python_match:
            return python_match.group(1)
        
        # Try generic ``` blocks
        generic_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if generic_match:
            return generic_match.group(1)
        
        return text
    
    @property
    def has_final_answer(self) -> bool:
        return self._final_called
    
    @property
    def final_answer(self) -> Optional[str]:
        return self._final_answer
    
    def cleanup(self):
        """Clean up temp directory."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass


# ==============================================================================
# System Prompts
# ==============================================================================

RLM_SYSTEM_PROMPT = """You are a Recursive Language Model. Your task is to answer queries using a Python REPL environment.

IMPORTANT: The context is stored in the `context` variable (NOT in this prompt). You MUST use Python code to examine it.

Available in environment:
- `context`: The document/data to analyze (can be str, dict, or list)
- `query`: The user's question
- `recursive_llm(subquery, sub_context)`: Recursively process sub-context with a sub-LLM
- `FINAL(answer)`: Return your final answer
- `FINAL_VAR(var_name)`: Return a variable you created as the final answer
- `SHOW_VARS()`: See what variables you've created
- Standard library: re, json, math, datetime, Counter, defaultdict

Write Python code in ```repl``` blocks to explore and analyze the context.

Example workflow:
1. First, examine the context structure:
```repl
print(f"Context type: {type(context)}")
print(f"Context length: {len(context) if hasattr(context, '__len__') else 'N/A'}")
print(f"First 500 chars: {str(context)[:500]}")
```

2. Then search/analyze based on what you find:
```repl
# For large text, use recursive_llm to process chunks
chunk = context[:50000]
summary = recursive_llm("Summarize the key points", chunk)
print(summary)
```

3. Finally, return your answer:
```repl
answer = "Based on my analysis: ..."
FINAL(answer)
```
# Or: FINAL_VAR(answer)

CRITICAL RULES:
- Do NOT guess or make up answers. Search the context first.
- Do NOT call FINAL() until you have concrete evidence from the context.
- Use recursive_llm() for processing large chunks (it can handle ~500K chars).
- Output from print() statements helps you reason through the problem.
- Each ```repl``` block executes and you see the output before continuing.

Think step by step and execute code immediately."""


def build_system_prompt(context_size: int, depth: int = 0) -> str:
    """Build system prompt with context metadata."""
    return f"""{RLM_SYSTEM_PROMPT}

Context size: {context_size:,} characters
Recursion depth: {depth}"""


def build_user_prompt(query: str, iteration: int = 0) -> str:
    """Build user prompt for each iteration."""
    if iteration == 0:
        return f"""Query: {query}

You have not examined the context yet. Start by exploring its structure and content.
Write Python code in a ```repl``` block to begin."""
    else:
        return f"""Continue working on: {query}

Review the output above and continue your analysis. Write more ```repl``` code or call FINAL() when ready."""


# ==============================================================================
# RLM Adapter
# ==============================================================================

class RLMAdapter:
    """
    Recursive Language Model adapter for DHARMIC_GODEL_CLAW.
    
    Wraps Claude/Kimi/other LLMs to enable infinite context handling through
    recursive decomposition and programmatic context examination.
    
    Usage:
        adapter = RLMAdapter(config=RLMConfig(model="claude-opus-4"))
        result = adapter.recursive_complete(
            query="Summarize the key themes",
            context=massive_document,
            max_depth=3
        )
        print(result.answer)
    """
    
    def __init__(self, config: Optional[RLMConfig] = None):
        self.config = config or RLMConfig()
        self._llm_calls = 0
        self._setup_client()
    
    def _setup_client(self):
        """Setup LLM client based on config."""
        backend = self.config.backend
        
        if backend == "proxy":
            # OpenAI-compatible proxy (claude-max-api-proxy)
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package required for proxy backend")
            
            self.client = OpenAI(
                base_url=self.config.api_base or "http://localhost:3456/v1",
                api_key=self.config.api_key or "not-needed"
            )
            self._completion_fn = self._proxy_completion
            
        elif backend == "direct":
            # Direct Anthropic SDK
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package required for direct backend")
            
            api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            self.client = anthropic.Anthropic(api_key=api_key)
            self._completion_fn = self._anthropic_completion
            
        elif backend == "litellm":
            # LiteLLM for any model
            if not LITELLM_AVAILABLE:
                raise ImportError("litellm package required for litellm backend")
            
            self._completion_fn = self._litellm_completion
            
        elif backend == "kimi":
            # Moonshot Kimi
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package required for kimi backend")
            
            self.client = OpenAI(
                base_url=self.config.api_base or "https://api.moonshot.cn/v1",
                api_key=self.config.api_key or os.environ.get("MOONSHOT_API_KEY", "")
            )
            self._completion_fn = self._kimi_completion
            
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def _proxy_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Completion via OpenAI-compatible proxy."""
        self._llm_calls += 1
        
        model = kwargs.get("model", self.config.model)
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **self.config.model_kwargs
        )
        return response.choices[0].message.content
    
    def _anthropic_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Completion via direct Anthropic SDK."""
        self._llm_calls += 1
        
        # Map short names to full model IDs
        model_map = {
            "claude-opus-4": "claude-opus-4-5-20251101",
            "claude-sonnet-4": "claude-sonnet-4-5-20250929", 
            "claude-haiku-4": "claude-3-5-haiku-20241022"
        }
        model = kwargs.get("model", self.config.model)
        model = model_map.get(model, model)
        
        # Convert messages to Anthropic format
        system = ""
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                converted.append(msg)
        
        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=converted,
            **self.config.model_kwargs
        )
        return response.content[0].text
    
    def _litellm_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Completion via LiteLLM."""
        self._llm_calls += 1
        
        model = kwargs.get("model", self.config.model)
        response = litellm.completion(
            model=model,
            messages=messages,
            api_base=self.config.api_base,
            api_key=self.config.api_key,
            **self.config.model_kwargs
        )
        return response.choices[0].message.content
    
    def _kimi_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Completion via Moonshot Kimi."""
        self._llm_calls += 1
        
        model = kwargs.get("model", "moonshot-v1-128k")
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **self.config.model_kwargs
        )
        return response.choices[0].message.content
    
    def recursive_complete(
        self,
        query: str,
        context: Union[str, Dict, List],
        max_depth: Optional[int] = None,
        max_iterations: Optional[int] = None,
        _current_depth: int = 0,
    ) -> RLMResult:
        """
        Main RLM completion method.
        
        Args:
            query: The question/task to perform on the context
            context: The context to analyze (can be string, dict, or list)
            max_depth: Maximum recursion depth (default from config)
            max_iterations: Maximum REPL iterations (default from config)
            _current_depth: Internal depth tracker (don't set manually)
            
        Returns:
            RLMResult with answer, stats, and trace
        """
        max_depth = max_depth or self.config.max_depth
        max_iterations = max_iterations or self.config.max_iterations
        
        # Check depth limit
        if _current_depth >= max_depth:
            raise MaxDepthError(f"Max recursion depth ({max_depth}) exceeded")
        
        start_time = time.perf_counter()
        trace: List[Dict[str, Any]] = []
        
        # Create recursive function for REPL
        def make_recursive_call(subquery: str, sub_context: str) -> str:
            """Recursive call from within REPL."""
            if _current_depth + 1 >= max_depth:
                return f"[Max depth ({max_depth}) reached - returning direct completion]"
            
            # Use cheaper model for recursive calls if configured
            recursive_model = self.config.recursive_model or self.config.model
            
            try:
                sub_result = self.recursive_complete(
                    query=subquery,
                    context=sub_context,
                    max_depth=max_depth,
                    max_iterations=max_iterations,
                    _current_depth=_current_depth + 1,
                )
                return sub_result.answer
            except Exception as e:
                return f"[Recursive call error: {e}]"
        
        # Create REPL environment
        repl = REPLEnvironment(
            context=context,
            query=query,
            recursive_fn=make_recursive_call,
            depth=_current_depth,
            max_output_chars=self.config.max_output_chars,
        )
        
        try:
            # Build initial messages
            context_size = len(str(context))
            system_prompt = build_system_prompt(context_size, _current_depth)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": build_user_prompt(query, 0)}
            ]
            
            # Main loop
            for iteration in range(max_iterations):
                # Get LLM response
                response = self._completion_fn(messages)
                
                # Record trace
                trace.append({
                    "iteration": iteration + 1,
                    "depth": _current_depth,
                    "response_preview": response[:500] + "..." if len(response) > 500 else response,
                })
                
                if self.config.verbose:
                    print(f"\n=== Iteration {iteration + 1} (depth {_current_depth}) ===")
                    print(f"Response: {response[:300]}...")
                
                # Check for FINAL() in response text (outside code block)
                final_match = re.search(r'FINAL\s*\(\s*["\'](.+?)["\']\s*\)', response, re.DOTALL)
                if final_match and "```" not in response[response.find("FINAL"):]:
                    answer = final_match.group(1)
                    return RLMResult(
                        answer=answer,
                        iterations=iteration + 1,
                        depth=_current_depth,
                        llm_calls=self._llm_calls,
                        execution_time=time.perf_counter() - start_time,
                        final_vars=repl.locals.copy(),
                        trace=trace,
                    )
                
                # Check for FINAL_VAR() in response text
                final_var_match = re.search(r'FINAL_VAR\s*\(\s*(["\']?)(\w+)\1\s*\)', response)
                if final_var_match and "```" not in response[response.find("FINAL_VAR"):]:
                    var_name = final_var_match.group(2)
                    if var_name in repl.locals:
                        return RLMResult(
                            answer=str(repl.locals[var_name]),
                            iterations=iteration + 1,
                            depth=_current_depth,
                            llm_calls=self._llm_calls,
                            execution_time=time.perf_counter() - start_time,
                            final_vars=repl.locals.copy(),
                            trace=trace,
                        )
                
                # Execute any code blocks
                code_blocks = re.findall(r'```(?:repl|python)?\s*(.*?)\s*```', response, re.DOTALL)
                
                exec_output = ""
                for code in code_blocks:
                    if code.strip():
                        output = repl.execute(code)
                        exec_output += output + "\n"
                        
                        if self.config.verbose:
                            print(f"REPL output: {output[:200]}...")
                        
                        # Check if FINAL was called during execution
                        if repl.has_final_answer:
                            return RLMResult(
                                answer=repl.final_answer,
                                iterations=iteration + 1,
                                depth=_current_depth,
                                llm_calls=self._llm_calls,
                                execution_time=time.perf_counter() - start_time,
                                final_vars=repl.locals.copy(),
                                trace=trace,
                            )
                
                # Add to conversation
                messages.append({"role": "assistant", "content": response})
                
                if exec_output.strip():
                    messages.append({
                        "role": "user", 
                        "content": f"REPL Output:\n{exec_output}\n\n{build_user_prompt(query, iteration + 1)}"
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": build_user_prompt(query, iteration + 1)
                    })
            
            # Max iterations reached - try to get a final answer
            messages.append({
                "role": "user",
                "content": "You've reached the iteration limit. Please provide your best FINAL() answer now based on what you've learned."
            })
            response = self._completion_fn(messages)
            
            # Try to extract answer
            final_match = re.search(r'FINAL\s*\(\s*["\'](.+?)["\']\s*\)', response, re.DOTALL)
            if final_match:
                answer = final_match.group(1)
            else:
                # Just use the response
                answer = response
            
            return RLMResult(
                answer=answer,
                iterations=max_iterations,
                depth=_current_depth,
                llm_calls=self._llm_calls,
                execution_time=time.perf_counter() - start_time,
                final_vars=repl.locals.copy(),
                trace=trace,
            )
            
        finally:
            repl.cleanup()
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    def query_vault(
        self,
        query: str,
        vault_path: Optional[str] = None,
        file_pattern: str = "**/*.md",
        max_files: int = 100,
    ) -> RLMResult:
        """
        Query the PSMV vault using RLM.
        
        Loads vault files as context and uses RLM to process them.
        
        Args:
            query: The question to answer
            vault_path: Path to vault (default: ~/Persistent-Semantic-Memory-Vault)
            file_pattern: Glob pattern for files to include
            max_files: Maximum files to load
            
        Returns:
            RLMResult with answer
        """
        vault_path = vault_path or os.path.expanduser("~/Persistent-Semantic-Memory-Vault")
        vault = Path(vault_path)
        
        if not vault.exists():
            raise FileNotFoundError(f"Vault not found: {vault_path}")
        
        # Load files
        files = list(vault.glob(file_pattern))[:max_files]
        
        context_parts = []
        for f in files:
            try:
                content = f.read_text(errors="ignore")
                relative = f.relative_to(vault)
                context_parts.append(f"=== {relative} ===\n{content}\n")
            except Exception:
                continue
        
        context = "\n".join(context_parts)
        
        if self.config.verbose:
            print(f"Loaded {len(files)} files, {len(context):,} chars total")
        
        return self.recursive_complete(query=query, context=context)
    
    def query_codebase(
        self,
        query: str,
        codebase_path: Optional[str] = None,
        file_pattern: str = "**/*.py",
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 200,
    ) -> RLMResult:
        """
        Query a codebase using RLM.
        
        Useful for understanding code, finding patterns, or planning changes.
        
        Args:
            query: The question about the codebase
            codebase_path: Path to codebase (default: ~/DHARMIC_GODEL_CLAW)
            file_pattern: Glob pattern for files
            exclude_patterns: Patterns to exclude (e.g., ["**/node_modules/**"])
            max_files: Maximum files to load
            
        Returns:
            RLMResult with answer
        """
        codebase_path = codebase_path or os.path.expanduser("~/DHARMIC_GODEL_CLAW")
        codebase = Path(codebase_path)
        
        if not codebase.exists():
            raise FileNotFoundError(f"Codebase not found: {codebase_path}")
        
        exclude_patterns = exclude_patterns or [
            "**/__pycache__/**",
            "**/node_modules/**", 
            "**/.git/**",
            "**/venv/**",
            "**/.venv/**",
        ]
        
        # Load files
        all_files = list(codebase.glob(file_pattern))
        
        files = []
        for f in all_files:
            skip = False
            for pattern in exclude_patterns:
                if f.match(pattern):
                    skip = True
                    break
            if not skip:
                files.append(f)
        
        files = files[:max_files]
        
        context_parts = []
        for f in files:
            try:
                content = f.read_text(errors="ignore")
                relative = f.relative_to(codebase)
                context_parts.append(f"=== {relative} ===\n{content}\n")
            except Exception:
                continue
        
        context = "\n".join(context_parts)
        
        if self.config.verbose:
            print(f"Loaded {len(files)} files, {len(context):,} chars total")
        
        return self.recursive_complete(query=query, context=context)
    
    def process_document(
        self,
        document: str,
        task: str,
    ) -> RLMResult:
        """
        Process a large document with a specific task.
        
        Args:
            document: The document text
            task: What to do (e.g., "summarize", "extract key points", etc.)
            
        Returns:
            RLMResult with answer
        """
        return self.recursive_complete(query=task, context=document)


# ==============================================================================
# Async Version
# ==============================================================================

class AsyncRLMAdapter(RLMAdapter):
    """Async version of RLMAdapter."""
    
    async def async_recursive_complete(
        self,
        query: str,
        context: Union[str, Dict, List],
        max_depth: Optional[int] = None,
        max_iterations: Optional[int] = None,
    ) -> RLMResult:
        """Async version of recursive_complete."""
        # For now, run sync version in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.recursive_complete(query, context, max_depth, max_iterations)
        )


# ==============================================================================
# CLI Testing
# ==============================================================================

if __name__ == "__main__":
    print("=== RLM Adapter Test ===\n")
    
    # Simple test
    adapter = RLMAdapter(config=RLMConfig(
        backend="proxy",
        verbose=True
    ))
    
    # Test with simple context
    test_context = """
    The secret code is: DHARMIC-42-MOKSHA
    
    Additional information:
    - Project name: DHARMIC_GODEL_CLAW
    - Goal: Self-improving AI through telos-driven development
    - Key concept: Strange loops and witness consciousness
    """
    
    print("Testing with simple context...")
    try:
        result = adapter.recursive_complete(
            query="What is the secret code?",
            context=test_context,
            max_iterations=5
        )
        print(f"\nAnswer: {result.answer}")
        print(f"Iterations: {result.iterations}")
        print(f"LLM calls: {result.llm_calls}")
        print(f"Time: {result.execution_time:.2f}s")
    except Exception as e:
        print(f"Error: {e}")
