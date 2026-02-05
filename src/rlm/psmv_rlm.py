"""PSMV-RLM Bridge — Perfect Memory for the Vault.

Uses RLM (Recursive Language Model) to query the entire PSMV vault
(8000+ files) without context rot.

The Problem:
- PSMV has 8000+ files of consciousness research, crown jewels, etc.
- Traditional LLM calls can't handle all of this
- Even Kimi's 128k context isn't enough for the full vault

The Solution (RLM approach):
1. Load PSMV file index as a Python variable
2. LLM can search, filter, and recursively query slices
3. No context rot because context stays external
"""

import asyncio
import fnmatch
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PSMVFile:
    """Metadata for a single file in the vault."""
    path: str                    # Relative path from vault root
    full_path: str               # Absolute path
    name: str                    # Filename
    extension: str               # File extension (e.g., '.md')
    size: int                    # Size in bytes
    modified: float              # Modification timestamp
    directory: str               # Parent directory relative to vault
    is_crown_jewel: bool = False # Whether this is a crown jewel
    tags: List[str] = field(default_factory=list)  # Extracted tags
    
    @property
    def modified_dt(self) -> datetime:
        """Get modification time as datetime."""
        return datetime.fromtimestamp(self.modified)
    
    def __repr__(self) -> str:
        crown = " 👑" if self.is_crown_jewel else ""
        return f"PSMVFile({self.path}{crown}, {self.size:,}b)"


@dataclass
class PSMVIndex:
    """Index of all files in the vault."""
    vault_path: str
    files: List[PSMVFile]
    crown_jewels: List[PSMVFile]
    directories: Set[str]
    total_size: int
    file_count: int
    indexed_at: datetime
    
    def __repr__(self) -> str:
        return (
            f"PSMVIndex({self.file_count:,} files, "
            f"{len(self.crown_jewels)} crown jewels, "
            f"{self.total_size / (1024*1024):.1f}MB)"
        )


# =============================================================================
# PSMVLoader - Loads vault metadata into REPL environment
# =============================================================================

class PSMVLoader:
    """Loads PSMV vault metadata for RLM queries.
    
    This class indexes the entire vault without loading file contents,
    allowing the RLM to search and selectively read files.
    """
    
    # File extensions we care about
    DEFAULT_EXTENSIONS = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.org'}
    
    # Crown jewel indicators
    CROWN_JEWEL_PATTERNS = [
        '*crown*',
        '*jewel*',
        '*breakthrough*',
        '*key_finding*',
        '*core*insight*',
    ]
    
    # Directories to skip
    SKIP_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        '.cursor', '.claude', '.sync-test', '.tmp*'
    }
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        extensions: Optional[Set[str]] = None,
        include_hidden: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB limit
    ):
        """
        Initialize the loader.
        
        Args:
            vault_path: Path to the PSMV vault (defaults to ~/Persistent-Semantic-Memory-Vault)
            extensions: File extensions to index (defaults to DEFAULT_EXTENSIONS)
            include_hidden: Whether to include hidden files/dirs
            max_file_size: Maximum file size to include (bytes)
        """
        self.vault_path = os.path.expanduser(
            vault_path or "~/Persistent-Semantic-Memory-Vault"
        )
        self.extensions = extensions or self.DEFAULT_EXTENSIONS
        self.include_hidden = include_hidden
        self.max_file_size = max_file_size
        self._index: Optional[PSMVIndex] = None
    
    def load(self, force_reload: bool = False) -> PSMVIndex:
        """
        Load/reload the vault index.
        
        Args:
            force_reload: Force re-indexing even if already loaded
            
        Returns:
            PSMVIndex with all file metadata
        """
        if self._index is not None and not force_reload:
            return self._index
        
        files: List[PSMVFile] = []
        crown_jewels: List[PSMVFile] = []
        directories: Set[str] = set()
        total_size = 0
        
        vault_path = Path(self.vault_path)
        
        for root, dirs, filenames in os.walk(vault_path):
            # Skip unwanted directories
            rel_root = os.path.relpath(root, vault_path)
            
            # Filter out hidden/skip dirs
            dirs[:] = [
                d for d in dirs
                if not self._should_skip_dir(d)
            ]
            
            for filename in filenames:
                # Skip hidden files unless explicitly included
                if not self.include_hidden and filename.startswith('.'):
                    continue
                
                # Check extension
                ext = os.path.splitext(filename)[1].lower()
                if ext not in self.extensions:
                    continue
                
                full_path = os.path.join(root, filename)
                
                try:
                    stat = os.stat(full_path)
                    
                    # Skip files that are too large
                    if stat.st_size > self.max_file_size:
                        continue
                    
                    rel_path = os.path.relpath(full_path, vault_path)
                    rel_dir = os.path.relpath(root, vault_path)
                    
                    # Check if crown jewel
                    is_crown = self._is_crown_jewel(rel_path, filename)
                    
                    psmv_file = PSMVFile(
                        path=rel_path,
                        full_path=full_path,
                        name=filename,
                        extension=ext,
                        size=stat.st_size,
                        modified=stat.st_mtime,
                        directory=rel_dir,
                        is_crown_jewel=is_crown,
                        tags=self._extract_tags(rel_path),
                    )
                    
                    files.append(psmv_file)
                    directories.add(rel_dir)
                    total_size += stat.st_size
                    
                    if is_crown:
                        crown_jewels.append(psmv_file)
                        
                except (OSError, PermissionError):
                    continue  # Skip inaccessible files
        
        # Sort files by path for consistent ordering
        files.sort(key=lambda f: f.path)
        crown_jewels.sort(key=lambda f: f.modified, reverse=True)
        
        self._index = PSMVIndex(
            vault_path=str(vault_path),
            files=files,
            crown_jewels=crown_jewels,
            directories=directories,
            total_size=total_size,
            file_count=len(files),
            indexed_at=datetime.now(),
        )
        
        return self._index
    
    def _should_skip_dir(self, dirname: str) -> bool:
        """Check if directory should be skipped."""
        if not self.include_hidden and dirname.startswith('.'):
            return True
        
        for pattern in self.SKIP_DIRS:
            if fnmatch.fnmatch(dirname, pattern):
                return True
        
        return False
    
    def _is_crown_jewel(self, path: str, filename: str) -> bool:
        """Check if file is a crown jewel."""
        path_lower = path.lower()
        filename_lower = filename.lower()
        
        # Check path patterns
        for pattern in self.CROWN_JEWEL_PATTERNS:
            if fnmatch.fnmatch(path_lower, pattern):
                return True
            if fnmatch.fnmatch(filename_lower, pattern):
                return True
        
        # Check specific crown jewel directories
        if 'crown_jewels' in path_lower or 'crown-jewels' in path_lower:
            return True
        
        return False
    
    def _extract_tags(self, path: str) -> List[str]:
        """Extract tags from file path."""
        tags = []
        
        # Extract directory-based tags
        parts = Path(path).parts
        for part in parts[:-1]:  # Exclude filename
            # Numbered directories like "00-CORE"
            if re.match(r'\d{2}-', part):
                tags.append(part[3:].lower().replace('-', '_'))
            else:
                tags.append(part.lower().replace('-', '_'))
        
        return tags
    
    @property
    def index(self) -> PSMVIndex:
        """Get or create the index."""
        if self._index is None:
            return self.load()
        return self._index


# =============================================================================
# REPL Environment Functions
# =============================================================================

def create_repl_functions(loader: PSMVLoader) -> Dict[str, Callable]:
    """
    Create functions available in the REPL environment.
    
    Args:
        loader: The PSMVLoader instance
        
    Returns:
        Dict of function name -> callable
    """
    index = loader.index
    
    def list_files(pattern: str = "*", limit: int = 50) -> List[str]:
        """
        List files matching a glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., '*consciousness*', '*.py', '00-CORE/*')
            limit: Maximum results to return
            
        Returns:
            List of matching file paths
        """
        matches = []
        pattern_lower = pattern.lower()
        
        for f in index.files:
            if fnmatch.fnmatch(f.path.lower(), pattern_lower):
                matches.append(f.path)
            elif fnmatch.fnmatch(f.name.lower(), pattern_lower):
                matches.append(f.path)
            
            if len(matches) >= limit:
                break
        
        return matches
    
    def list_dirs() -> List[str]:
        """List all directories in the vault."""
        return sorted(index.directories)
    
    def list_crown_jewels(limit: int = 20) -> List[str]:
        """List crown jewel files (most recent first)."""
        return [f.path for f in index.crown_jewels[:limit]]
    
    def get_file_info(path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a file.
        
        Args:
            path: File path (relative to vault)
            
        Returns:
            Dict with file metadata or None if not found
        """
        for f in index.files:
            if f.path == path or f.name == path:
                return {
                    'path': f.path,
                    'name': f.name,
                    'size': f.size,
                    'modified': f.modified_dt.isoformat(),
                    'directory': f.directory,
                    'is_crown_jewel': f.is_crown_jewel,
                    'tags': f.tags,
                }
        return None
    
    def read_file(path: str, max_chars: int = 50000) -> str:
        """
        Read a file's content.
        
        Args:
            path: File path (relative or absolute)
            max_chars: Maximum characters to read
            
        Returns:
            File content as string
        """
        # Find the file
        target_file = None
        for f in index.files:
            if f.path == path or f.name == path or path in f.path:
                target_file = f
                break
        
        if target_file is None:
            return f"Error: File not found: {path}"
        
        try:
            with open(target_file.full_path, 'r', encoding='utf-8', errors='replace') as fp:
                content = fp.read(max_chars)
                if len(content) == max_chars:
                    content += f"\n\n[Truncated at {max_chars:,} chars]"
                return content
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def search_content(
        query: str,
        pattern: str = "*",
        max_files: int = 100,
        max_results: int = 20,
        context_chars: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Search for content across files.
        
        Args:
            query: Search string (case-insensitive)
            pattern: Glob pattern to filter files
            max_files: Maximum files to search
            max_results: Maximum results to return
            context_chars: Characters of context around match
            
        Returns:
            List of dicts with path, match, context
        """
        results = []
        query_lower = query.lower()
        files_searched = 0
        
        for f in index.files:
            if files_searched >= max_files or len(results) >= max_results:
                break
            
            # Check pattern match
            if pattern != "*" and not fnmatch.fnmatch(f.path.lower(), pattern.lower()):
                continue
            
            files_searched += 1
            
            try:
                with open(f.full_path, 'r', encoding='utf-8', errors='replace') as fp:
                    content = fp.read()
                    content_lower = content.lower()
                    
                    # Find all occurrences
                    idx = 0
                    while idx < len(content_lower):
                        pos = content_lower.find(query_lower, idx)
                        if pos == -1:
                            break
                        
                        # Extract context
                        start = max(0, pos - context_chars)
                        end = min(len(content), pos + len(query) + context_chars)
                        context = content[start:end]
                        
                        # Clean up context
                        if start > 0:
                            context = "..." + context
                        if end < len(content):
                            context = context + "..."
                        
                        results.append({
                            'path': f.path,
                            'position': pos,
                            'context': context.replace('\n', ' ').strip(),
                            'is_crown_jewel': f.is_crown_jewel,
                        })
                        
                        if len(results) >= max_results:
                            break
                        
                        idx = pos + len(query)
                        
            except Exception:
                continue
        
        return results
    
    def search_regex(
        regex: str,
        pattern: str = "*",
        max_files: int = 50,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search files using regex pattern.
        
        Args:
            regex: Regular expression pattern
            pattern: Glob pattern to filter files
            max_files: Maximum files to search
            max_results: Maximum results to return
            
        Returns:
            List of dicts with path, match
        """
        results = []
        compiled = re.compile(regex, re.IGNORECASE | re.MULTILINE)
        files_searched = 0
        
        for f in index.files:
            if files_searched >= max_files or len(results) >= max_results:
                break
            
            if pattern != "*" and not fnmatch.fnmatch(f.path.lower(), pattern.lower()):
                continue
            
            files_searched += 1
            
            try:
                with open(f.full_path, 'r', encoding='utf-8', errors='replace') as fp:
                    content = fp.read()
                    
                    for match in compiled.finditer(content):
                        results.append({
                            'path': f.path,
                            'match': match.group(0)[:500],
                            'start': match.start(),
                        })
                        
                        if len(results) >= max_results:
                            break
                            
            except Exception:
                continue
        
        return results
    
    def get_stats() -> Dict[str, Any]:
        """Get vault statistics."""
        return {
            'total_files': index.file_count,
            'total_size_mb': round(index.total_size / (1024 * 1024), 2),
            'crown_jewels': len(index.crown_jewels),
            'directories': len(index.directories),
            'indexed_at': index.indexed_at.isoformat(),
            'vault_path': index.vault_path,
        }
    
    def files_by_tag(tag: str, limit: int = 30) -> List[str]:
        """
        Find files by tag.
        
        Args:
            tag: Tag to search for
            limit: Maximum results
            
        Returns:
            List of file paths
        """
        matches = []
        tag_lower = tag.lower().replace('-', '_')
        
        for f in index.files:
            if tag_lower in f.tags:
                matches.append(f.path)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def recent_files(days: int = 7, limit: int = 30) -> List[str]:
        """
        Get recently modified files.
        
        Args:
            days: Look back this many days
            limit: Maximum results
            
        Returns:
            List of file paths (most recent first)
        """
        import time
        cutoff = time.time() - (days * 86400)
        
        recent = [f for f in index.files if f.modified >= cutoff]
        recent.sort(key=lambda f: f.modified, reverse=True)
        
        return [f.path for f in recent[:limit]]
    
    return {
        'list_files': list_files,
        'list_dirs': list_dirs,
        'list_crown_jewels': list_crown_jewels,
        'get_file_info': get_file_info,
        'read_file': read_file,
        'search_content': search_content,
        'search_regex': search_regex,
        'get_stats': get_stats,
        'files_by_tag': files_by_tag,
        'recent_files': recent_files,
        # Expose the index itself for advanced queries
        'INDEX': index,
        'FILES': index.files,
    }


# =============================================================================
# PSMVQueryEngine - RLM-based query engine
# =============================================================================

class PSMVQueryEngine:
    """Query engine that uses RLM to answer questions about the PSMV vault.
    
    Example usage:
        engine = PSMVQueryEngine()
        answer = engine.query(
            "What are the key findings about R_V metric across all papers?",
            vault_path="~/Persistent-Semantic-Memory-Vault"
        )
    """
    
    DEFAULT_MODEL = "gpt-4o"
    RECURSIVE_MODEL = "gpt-4o-mini"
    
    SYSTEM_PROMPT_TEMPLATE = '''You are a PSMV Query Agent with access to a vault of {file_count:,} files 
containing consciousness research, crown jewels, and dharmic knowledge.

IMPORTANT: You CANNOT see file contents directly. You MUST use Python code to explore the vault.

Available functions:
- list_files(pattern, limit=50) → List[str] - List files matching glob pattern
- list_dirs() → List[str] - List all directories
- list_crown_jewels(limit=20) → List[str] - List crown jewel files
- get_file_info(path) → Dict - Get file metadata
- read_file(path, max_chars=50000) → str - Read file content
- search_content(query, pattern="*", max_files=100, max_results=20) → List[Dict] - Search across files
- search_regex(regex, pattern="*") → List[Dict] - Regex search
- get_stats() → Dict - Vault statistics
- files_by_tag(tag) → List[str] - Find files by directory/tag
- recent_files(days=7) → List[str] - Recently modified files
- recursive_query(sub_query, context) → str - Call sub-LLM for deep analysis

Also available:
- INDEX: PSMVIndex object with all metadata
- FILES: List[PSMVFile] - all files
- re: regex module
- json: json module

Strategy for answering questions:
1. FIRST: Use search_content() or search_regex() to find relevant files
2. THEN: Use read_file() to read promising files
3. IF NEEDED: Use recursive_query() to analyze large files or synthesize multiple sources
4. FINALLY: Use FINAL("your answer") to return your answer

Crown jewels are high-priority breakthrough documents - check them first for important questions.

Remember: You MUST explore the vault with code. Do NOT guess answers.
Use FINAL("answer") only after finding evidence in the files.'''

    def __init__(
        self,
        model: Optional[str] = None,
        recursive_model: Optional[str] = None,
        vault_path: Optional[str] = None,
        max_iterations: int = 30,
        max_depth: int = 3,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **llm_kwargs: Any
    ):
        """
        Initialize the query engine.
        
        Args:
            model: Primary LLM model
            recursive_model: Model for recursive sub-queries
            vault_path: Path to PSMV vault
            max_iterations: Maximum REPL iterations
            max_depth: Maximum recursion depth
            api_key: Optional API key
            api_base: Optional API base URL
            **llm_kwargs: Additional LLM parameters
        """
        if not HAS_LITELLM:
            raise ImportError("litellm is required. Install with: pip install litellm")
        
        self.model = model or self.DEFAULT_MODEL
        self.recursive_model = recursive_model or self.RECURSIVE_MODEL
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.api_key = api_key
        self.api_base = api_base
        self.llm_kwargs = llm_kwargs
        
        # Initialize loader
        self.loader = PSMVLoader(vault_path=vault_path)
        
        # Stats
        self._stats = {
            'llm_calls': 0,
            'iterations': 0,
            'recursive_calls': 0,
            'files_read': 0,
        }
    
    def query(
        self,
        question: str,
        vault_path: Optional[str] = None,
        prioritize_crown_jewels: bool = True,
        **kwargs: Any
    ) -> str:
        """
        Query the PSMV vault.
        
        Args:
            question: The question to answer
            vault_path: Override vault path
            prioritize_crown_jewels: Whether to hint about crown jewels
            **kwargs: Additional parameters
            
        Returns:
            Answer string
        """
        return asyncio.run(
            self.aquery(question, vault_path, prioritize_crown_jewels, **kwargs)
        )
    
    async def aquery(
        self,
        question: str,
        vault_path: Optional[str] = None,
        prioritize_crown_jewels: bool = True,
        _depth: int = 0,
        **kwargs: Any
    ) -> str:
        """
        Async query the PSMV vault.
        
        Args:
            question: The question to answer
            vault_path: Override vault path
            prioritize_crown_jewels: Whether to hint about crown jewels
            _depth: Current recursion depth (internal)
            **kwargs: Additional parameters
            
        Returns:
            Answer string
        """
        # Reload loader if vault path changed
        if vault_path and vault_path != self.loader.vault_path:
            self.loader = PSMVLoader(vault_path=vault_path)
        
        # Load index
        index = self.loader.load()
        
        # Build REPL environment
        repl_functions = create_repl_functions(self.loader)
        env = self._build_env(repl_functions, _depth)
        
        # Build system prompt
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            file_count=index.file_count
        )
        
        if prioritize_crown_jewels and index.crown_jewels:
            system_prompt += f"\n\nTip: There are {len(index.crown_jewels)} crown jewels. Check list_crown_jewels() for breakthrough documents."
        
        # Build user prompt
        user_prompt = f"Question: {question}\n\nExplore the vault and answer the question. Use code to search and read files."
        
        # Main conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # REPL loop
        for iteration in range(self.max_iterations):
            self._stats['iterations'] = iteration + 1
            
            # Call LLM
            response = await self._call_llm(messages, **kwargs)
            
            # Check for FINAL
            final_match = re.search(r'FINAL\s*\(\s*["\'](.+?)["\']\s*\)', response, re.DOTALL)
            if final_match:
                return final_match.group(1)
            
            # Also check for triple-quoted FINAL
            final_match = re.search(r'FINAL\s*\(\s*(?:"""|\'\'\')(.+?)(?:"""|\'\'\')s*\)', response, re.DOTALL)
            if final_match:
                return final_match.group(1)
            
            # Execute code
            exec_result = self._execute_code(response, env)
            
            # Add to conversation
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Output:\n{exec_result}"})
        
        return "Max iterations reached without a final answer. Last response was exploratory."
    
    def _build_env(self, repl_functions: Dict[str, Callable], depth: int) -> Dict[str, Any]:
        """Build the REPL environment."""
        env = {
            **repl_functions,
            're': re,
            'json': json,
            'recursive_query': self._make_recursive_fn(depth),
        }
        return env
    
    def _make_recursive_fn(self, current_depth: int) -> Callable:
        """Create recursive query function."""
        async def async_recursive(sub_query: str, context: str) -> str:
            if current_depth + 1 >= self.max_depth:
                return f"Max recursion depth ({self.max_depth}) reached"
            
            self._stats['recursive_calls'] += 1
            
            # Create minimal sub-engine
            # For recursive calls, we do a simpler text-in-text-out query
            messages = [
                {"role": "system", "content": "You are an expert analyst. Answer the question based on the provided context. Be concise and specific."},
                {"role": "user", "content": f"Context:\n{context[:50000]}\n\nQuestion: {sub_query}"},
            ]
            
            response = await self._call_llm(messages, model=self.recursive_model)
            return response
        
        def sync_recursive(sub_query: str, context: str) -> str:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        async_recursive(sub_query, context)
                    )
                    return future.result()
            except RuntimeError:
                return asyncio.run(async_recursive(sub_query, context))
        
        return sync_recursive
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Call the LLM."""
        self._stats['llm_calls'] += 1
        
        call_kwargs = {**self.llm_kwargs, **kwargs}
        if self.api_key:
            call_kwargs['api_key'] = self.api_key
        if self.api_base:
            call_kwargs['api_base'] = self.api_base
        
        response = await litellm.acompletion(
            model=model or self.model,
            messages=messages,
            **call_kwargs
        )
        
        return response.choices[0].message.content
    
    def _execute_code(self, response: str, env: Dict[str, Any]) -> str:
        """Execute Python code from LLM response."""
        import io
        import sys
        
        # Extract code from markdown blocks
        code = self._extract_code(response)
        
        if not code.strip():
            return "No code found in response. Write Python code to explore the vault."
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        
        try:
            # Execute
            exec(code, env)
            
            output = captured.getvalue()
            
            # Try to evaluate last line for expression results
            lines = code.strip().split('\n')
            if lines:
                last_line = lines[-1].strip()
                if last_line and not any(kw in last_line for kw in ['=', 'import', 'def', 'class', 'if', 'for', 'while', 'with', 'print']):
                    try:
                        result = eval(last_line, env)
                        if result is not None:
                            output += str(result) + '\n'
                    except:
                        pass
            
            if not output:
                output = "Code executed (no output). Use print() to see results."
            
            # Truncate if needed
            if len(output) > 10000:
                output = output[:10000] + "\n\n[Truncated at 10,000 chars]"
            
            return output
            
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"
        
        finally:
            sys.stdout = old_stdout
    
    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code blocks."""
        # Try ```python blocks first
        match = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Try generic ``` blocks
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # If no code blocks, try to find Python-looking code
        lines = []
        in_code = False
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped and (
                stripped.startswith(('print(', 'search_', 'list_', 'read_', 'get_', 'files_', 'recent_', 'recursive_'))
                or '=' in stripped and not stripped.startswith('#')
                or stripped.startswith('for ')
                or stripped.startswith('if ')
            ):
                in_code = True
            
            if in_code:
                if stripped and not stripped.startswith('#') and not re.match(r'^[A-Z]', stripped):
                    lines.append(line)
                elif not stripped:
                    lines.append(line)
        
        return '\n'.join(lines)
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get execution statistics."""
        return self._stats.copy()


# =============================================================================
# Convenience functions
# =============================================================================

def quick_search(query: str, vault_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Quick content search without LLM.
    
    Args:
        query: Search string
        vault_path: Optional vault path
        
    Returns:
        List of search results
    """
    loader = PSMVLoader(vault_path=vault_path)
    functions = create_repl_functions(loader)
    return functions['search_content'](query)


def get_vault_stats(vault_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get vault statistics.
    
    Args:
        vault_path: Optional vault path
        
    Returns:
        Stats dict
    """
    loader = PSMVLoader(vault_path=vault_path)
    functions = create_repl_functions(loader)
    return functions['get_stats']()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    # Demo mode - just show stats and search
    print("PSMV-RLM Bridge Demo")
    print("=" * 50)
    
    loader = PSMVLoader()
    index = loader.load()
    
    print(f"\nVault: {index.vault_path}")
    print(f"Files: {index.file_count:,}")
    print(f"Crown Jewels: {len(index.crown_jewels)}")
    print(f"Total Size: {index.total_size / (1024*1024):.1f} MB")
    print(f"Directories: {len(index.directories)}")
    
    print("\n" + "=" * 50)
    print("Sample Crown Jewels:")
    for cj in index.crown_jewels[:5]:
        print(f"  👑 {cj.path}")
    
    print("\n" + "=" * 50)
    print("To use the query engine:")
    print("""
    from psmv_rlm import PSMVQueryEngine
    
    engine = PSMVQueryEngine(model="gpt-4o")
    answer = engine.query("What are the key insights about consciousness?")
    print(answer)
    """)
