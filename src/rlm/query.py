"""
Unified Query Interface for RLM

Provides simple entry points for the DGM orchestrator to:
1. Query large contexts (documents, codebases)
2. Query the PSMV vault for consciousness research
3. Process documents with recursive analysis

Usage:
    from rlm import query, query_vault, query_codebase
    
    # General query on any context
    result = query("What are the key themes?", context=large_document)
    
    # Query PSMV vault (consciousness research)
    result = query_vault("What does the research say about R_V metric?")
    
    # Query a codebase
    result = query_codebase("How does the DGM orchestrator work?", path="~/DHARMIC_GODEL_CLAW")
"""

import os
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from .rlm_adapter import RLMAdapter, RLMConfig, RLMResult, AsyncRLMAdapter
from .psmv_rlm import PSMVQueryEngine, quick_search as psmv_quick_search


class RLMQueryType(Enum):
    """Types of RLM queries."""
    GENERAL = auto()      # General context query
    VAULT = auto()        # PSMV vault query  
    CODEBASE = auto()     # Codebase query
    DOCUMENT = auto()     # Single document processing


# Default configuration - uses proxy backend (claude-max-api-proxy)
DEFAULT_CONFIG = RLMConfig(
    backend="proxy",
    model="claude-opus-4",
    max_depth=3,
    max_iterations=30,
)


# Singleton adapter for reuse
_adapter: Optional[RLMAdapter] = None


def _get_adapter(config: Optional[RLMConfig] = None) -> RLMAdapter:
    """Get or create the singleton RLM adapter."""
    global _adapter
    
    if config is not None:
        # Custom config - create new adapter
        return RLMAdapter(config=config)
    
    if _adapter is None:
        _adapter = RLMAdapter(config=DEFAULT_CONFIG)
    
    return _adapter


# =============================================================================
# Main Query Functions
# =============================================================================

def query(
    question: str,
    context: Union[str, Dict, List],
    *,
    config: Optional[RLMConfig] = None,
    max_depth: Optional[int] = None,
    max_iterations: Optional[int] = None,
    verbose: bool = False,
) -> RLMResult:
    """
    Query a large context using RLM.
    
    This is the main entry point for general-purpose RLM queries. The context
    is stored as a Python variable and examined programmatically by the LLM.
    
    Args:
        question: The question to answer about the context
        context: The context to analyze (string, dict, or list)
        config: Optional custom RLMConfig
        max_depth: Max recursion depth (default 3)
        max_iterations: Max REPL iterations (default 30)
        verbose: Print debug info
        
    Returns:
        RLMResult with answer, stats, and trace
        
    Example:
        >>> result = query("What is the main topic?", context=long_document)
        >>> print(result.answer)
        "The document discusses consciousness..."
        >>> print(f"Took {result.iterations} iterations")
    """
    if config is None and verbose:
        config = RLMConfig(
            backend=DEFAULT_CONFIG.backend,
            model=DEFAULT_CONFIG.model,
            verbose=True,
        )
    
    adapter = _get_adapter(config)
    
    return adapter.recursive_complete(
        query=question,
        context=context,
        max_depth=max_depth,
        max_iterations=max_iterations,
    )


def query_vault(
    question: str,
    *,
    vault_path: Optional[str] = None,
    prioritize_crown_jewels: bool = True,
    use_psmv_engine: bool = True,
    config: Optional[RLMConfig] = None,
    verbose: bool = False,
) -> Union[RLMResult, str]:
    """
    Query the PSMV vault (Persistent Semantic Memory Vault).
    
    This uses RLM to intelligently search and analyze the 8000+ files
    in the consciousness research vault.
    
    Args:
        question: The question to answer
        vault_path: Path to vault (default ~/Persistent-Semantic-Memory-Vault)
        prioritize_crown_jewels: Hint LLM to check crown jewels first
        use_psmv_engine: Use the specialized PSMVQueryEngine (default True)
        config: Optional custom RLMConfig
        verbose: Print debug info
        
    Returns:
        RLMResult (if use_psmv_engine=False) or str answer (if True)
        
    Example:
        >>> answer = query_vault("What are the key findings about R_V metric?")
        >>> print(answer)
        "The R_V metric shows correlations of 0.91 with..."
    """
    vault_path = vault_path or os.path.expanduser("~/Persistent-Semantic-Memory-Vault")
    
    if use_psmv_engine:
        # Use the specialized PSMV engine with vault-specific REPL functions
        try:
            engine = PSMVQueryEngine(
                vault_path=vault_path,
                max_iterations=config.max_iterations if config else 30,
                max_depth=config.max_depth if config else 3,
            )
            return engine.query(
                question,
                prioritize_crown_jewels=prioritize_crown_jewels,
            )
        except ImportError as e:
            # litellm not available, fall back to adapter
            if verbose:
                print(f"PSMVQueryEngine unavailable ({e}), using RLMAdapter")
    
    # Fall back to general adapter with vault files as context
    adapter = _get_adapter(config)
    return adapter.query_vault(
        query=question,
        vault_path=vault_path,
    )


def query_codebase(
    question: str,
    path: Optional[str] = None,
    *,
    file_pattern: str = "**/*.py",
    exclude_patterns: Optional[List[str]] = None,
    max_files: int = 200,
    config: Optional[RLMConfig] = None,
    verbose: bool = False,
) -> RLMResult:
    """
    Query a codebase using RLM.
    
    Loads source files and uses RLM to analyze code structure,
    find patterns, understand architecture, etc.
    
    Args:
        question: The question about the codebase
        path: Path to codebase (default ~/DHARMIC_GODEL_CLAW)
        file_pattern: Glob pattern for files (default "**/*.py")
        exclude_patterns: Patterns to exclude (default: __pycache__, .git, etc.)
        max_files: Maximum files to load
        config: Optional custom RLMConfig
        verbose: Print debug info
        
    Returns:
        RLMResult with answer
        
    Example:
        >>> result = query_codebase("How does the DGM orchestrator work?")
        >>> print(result.answer)
        "The DGM orchestrator coordinates..."
    """
    path = path or os.path.expanduser("~/DHARMIC_GODEL_CLAW")
    
    if config is None and verbose:
        config = RLMConfig(
            backend=DEFAULT_CONFIG.backend,
            model=DEFAULT_CONFIG.model,
            verbose=True,
        )
    
    adapter = _get_adapter(config)
    
    return adapter.query_codebase(
        query=question,
        codebase_path=path,
        file_pattern=file_pattern,
        exclude_patterns=exclude_patterns,
        max_files=max_files,
    )


# =============================================================================
# Quick Utilities
# =============================================================================

def search_vault(
    query: str,
    vault_path: Optional[str] = None,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Quick search of PSMV vault without LLM.
    
    Performs a fast content search across vault files.
    Useful for finding relevant files before a full RLM query.
    
    Args:
        query: Search string
        vault_path: Optional vault path
        max_results: Maximum results to return
        
    Returns:
        List of dicts with path, position, context, is_crown_jewel
        
    Example:
        >>> results = search_vault("R_V metric")
        >>> for r in results[:5]:
        ...     print(f"{r['path']}: {r['context'][:50]}...")
    """
    return psmv_quick_search(query, vault_path)[:max_results]


def get_vault_info(vault_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get vault statistics.
    
    Returns:
        Dict with total_files, total_size_mb, crown_jewels, directories, etc.
    """
    from .psmv_rlm import get_vault_stats
    return get_vault_stats(vault_path)


# =============================================================================
# Async Variants
# =============================================================================

async def aquery(
    question: str,
    context: Union[str, Dict, List],
    *,
    config: Optional[RLMConfig] = None,
    max_depth: Optional[int] = None,
    max_iterations: Optional[int] = None,
) -> RLMResult:
    """
    Async version of query().
    
    See query() for full documentation.
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    adapter = AsyncRLMAdapter(config=config)
    return await adapter.async_recursive_complete(
        query=question,
        context=context,
        max_depth=max_depth,
        max_iterations=max_iterations,
    )


async def aquery_vault(
    question: str,
    *,
    vault_path: Optional[str] = None,
    prioritize_crown_jewels: bool = True,
) -> str:
    """
    Async version of query_vault().
    
    Uses PSMVQueryEngine.aquery() for async vault queries.
    """
    vault_path = vault_path or os.path.expanduser("~/Persistent-Semantic-Memory-Vault")
    
    try:
        engine = PSMVQueryEngine(vault_path=vault_path)
        return await engine.aquery(
            question,
            prioritize_crown_jewels=prioritize_crown_jewels,
        )
    except ImportError:
        # Fall back to sync in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: query_vault(question, vault_path=vault_path)
        )


# =============================================================================
# DGM Integration Helpers
# =============================================================================

def create_context_from_files(
    paths: List[str],
    max_chars_per_file: int = 50000,
    separator: str = "\n\n" + "="*60 + "\n\n",
) -> str:
    """
    Create a context string from multiple files.
    
    Useful for preparing context for query().
    
    Args:
        paths: List of file paths
        max_chars_per_file: Truncate files larger than this
        separator: String to separate files
        
    Returns:
        Combined context string
    """
    parts = []
    
    for path in paths:
        try:
            path = os.path.expanduser(path)
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_chars_per_file)
                if len(content) == max_chars_per_file:
                    content += "\n[truncated]"
                parts.append(f"=== {path} ===\n{content}")
        except Exception as e:
            parts.append(f"=== {path} ===\n[Error reading: {e}]")
    
    return separator.join(parts)


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimation.
    
    Uses ~4 chars per token heuristic.
    """
    return len(text) // 4


# =============================================================================
# CLI / Testing
# =============================================================================

if __name__ == "__main__":
    print("RLM Unified Query Interface")
    print("=" * 50)
    
    # Show vault stats if available
    vault_path = os.path.expanduser("~/Persistent-Semantic-Memory-Vault")
    if os.path.exists(vault_path):
        stats = get_vault_info(vault_path)
        print("\nPSMV Vault Stats:")
        print(f"  Files: {stats['total_files']:,}")
        print(f"  Crown Jewels: {stats['crown_jewels']}")
        print(f"  Size: {stats['total_size_mb']:.1f} MB")
    
    # Show usage
    print("\nUsage:")
    print("""
    from rlm import query, query_vault, query_codebase
    
    # Query any context
    result = query("What is the main idea?", context=document)
    
    # Query PSMV vault
    answer = query_vault("What are the R_V metric findings?")
    
    # Query codebase
    result = query_codebase("How does error handling work?")
    """)
