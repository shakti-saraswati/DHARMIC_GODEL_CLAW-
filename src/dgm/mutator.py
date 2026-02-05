"""
DGM Mutator - Claude-Powered Mutation Proposer
==============================================
Uses Claude to propose minimal, elegant improvements to code components.

The mutator is the creative engine of DGM - it proposes changes that
can then be voted on by the dharmic gates before application.

Safety: Never proposes changes to secrets, credentials, or .env files.
"""
import subprocess
import sys
import json
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .archive import EvolutionEntry, FitnessScore

# Security integration for subprocess calls
SRC_CORE = Path(__file__).parent.parent / "core"
if str(SRC_CORE) not in sys.path:
    sys.path.insert(0, str(SRC_CORE))
try:
    from dharmic_security import ExecGuard
    EXEC_GUARD = ExecGuard(allowed_bins=["clawdbot"])
    SECURITY_AVAILABLE = True
except Exception:
    EXEC_GUARD = None
    SECURITY_AVAILABLE = False

# Import logging with fallback for test compatibility
try:
    from core.dharmic_logging import get_logger
except ImportError:
    try:
        from ..core.dharmic_logging import get_logger
    except ImportError:
        # Fallback to standard logging if dharmic_logging unavailable
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
            # Add dharmic method stub
            logger.dharmic = lambda msg, **kw: logger.info(f"[DHARMIC] {msg}")
            return logger


logger = get_logger("mutator")


# Files that should NEVER be mutated
FORBIDDEN_PATTERNS = [
    r"\.env($|\.)",           # .env, .env.local, .env.production
    r"secrets?\.ya?ml$",      # secrets.yml, secret.yaml
    r"credentials?\.json$",   # credentials.json
    r"\.pem$",                # SSL certificates
    r"\.key$",                # Private keys
    r"id_rsa",                # SSH keys
    r"\.secret$",             # Generic secrets
    r"password",              # Password files
    r"token",                 # Token files
    r"api_?key",              # API key files
]


@dataclass
class MutationProposal:
    """
    A proposed mutation to a component.
    
    Attributes:
        diff: Unified diff of the proposed changes
        rationale: Claude's explanation of why this change improves the code
        estimated_fitness: Claude's estimate of the fitness improvement (0.0-1.0)
        affected_files: List of files that would be modified
        mutation_type: Type of mutation (refactor, optimize, fix, enhance, create)
        risk_level: Estimated risk (low, medium, high)
        reversible: Whether this change is easily reversible
        content: Full file content (used for creation)
    """
    diff: str
    rationale: str
    estimated_fitness: float
    affected_files: List[str]
    mutation_type: str = "improve"
    risk_level: str = "low"
    reversible: bool = True
    content: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "diff": self.diff,
            "rationale": self.rationale,
            "estimated_fitness": self.estimated_fitness,
            "affected_files": self.affected_files,
            "mutation_type": self.mutation_type,
            "risk_level": self.risk_level,
            "reversible": self.reversible,
            "content": self.content,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MutationProposal":
        """Create from dictionary."""
        return cls(
            diff=data.get("diff", ""),
            rationale=data.get("rationale", ""),
            estimated_fitness=float(data.get("estimated_fitness", 0.5)),
            affected_files=data.get("affected_files", []),
            mutation_type=data.get("mutation_type", "improve"),
            risk_level=data.get("risk_level", "low"),
            reversible=data.get("reversible", True),
            content=data.get("content", ""),
        )


class MutationError(Exception):
    """Raised when mutation fails."""
    pass


class SafetyViolationError(MutationError):
    """Raised when mutation would affect forbidden files."""
    pass


class Mutator:
    """
    Claude-powered mutation proposer.
    
    Uses Clawdbot's Claude connection to propose minimal, elegant
    improvements to code components.
    
    Example:
        mutator = Mutator(project_root=Path("/path/to/project"))
        proposal = mutator.propose_mutation(
            component="src/dgm/archive.py",
            parent=parent_entry,
            context={"focus": "improve test coverage"}
        )
    """
    
    def __init__(
        self,
        project_root: Path = None,
        model: str = "claude-sonnet-4-20250514",
        clawdbot_path: str = "clawdbot",
        timeout: int = 120,
    ):
        """
        Initialize mutator.
        
        Args:
            project_root: Root of the project to mutate
            model: Claude model to use
            clawdbot_path: Path to clawdbot CLI
            timeout: Timeout for Claude calls in seconds
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.model = model
        self.clawdbot_path = clawdbot_path
        self.timeout = timeout
        
        logger.info("Mutator initialized", context={
            "project_root": str(self.project_root),
            "model": self.model,
        })
    
    def is_forbidden_file(self, filepath: str) -> bool:
        """
        Check if a file is forbidden from mutation.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if file should never be mutated
        """
        filename = Path(filepath).name
        filepath_lower = filepath.lower()
        
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, filepath_lower):
                logger.warning(f"Forbidden file detected: {filepath}", context={
                    "pattern": pattern,
                })
                return True
        return False
    
    def validate_proposal(self, proposal: MutationProposal) -> bool:
        """
        Validate that a proposal doesn't violate safety rules.
        
        Args:
            proposal: The mutation proposal to validate
            
        Returns:
            True if proposal is safe
            
        Raises:
            SafetyViolationError: If proposal affects forbidden files
        """
        for filepath in proposal.affected_files:
            if self.is_forbidden_file(filepath):
                raise SafetyViolationError(
                    f"Proposal affects forbidden file: {filepath}"
                )
        
        # Check diff for forbidden file references
        diff_lower = proposal.diff.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, diff_lower):
                raise SafetyViolationError(
                    f"Diff contains forbidden pattern: {pattern}"
                )
        
        return True
    
    def _build_prompt(
        self,
        component: str,
        parent: Optional[EvolutionEntry],
        context: Dict[str, Any],
        component_content: str,
    ) -> str:
        """
        Build the mutation prompt for Claude.
        
        Args:
            component: Path to component being mutated
            parent: Parent evolution entry (if any)
            context: Additional context dict
            component_content: Current content of the component
            
        Returns:
            Formatted prompt string
        """
        # Build context about parent fitness
        parent_context = ""
        if parent:
            parent_context = f"""
## Parent Evolution
- Parent ID: {parent.id}
- Parent fitness: {parent.fitness.total():.3f}
  - Correctness: {parent.fitness.correctness:.2f}
  - Dharmic alignment: {parent.fitness.dharmic_alignment:.2f}
  - Elegance: {parent.fitness.elegance:.2f}
  - Efficiency: {parent.fitness.efficiency:.2f}
  - Safety: {parent.fitness.safety:.2f}
- Gates passed: {', '.join(parent.gates_passed) or 'none'}
- Gates failed: {', '.join(parent.gates_failed) or 'none'}
"""
        
        # Build context about recent failures
        failures_context = ""
        if context.get("recent_failures"):
            failures = context["recent_failures"]
            failures_context = f"""
## Recent Failures
{chr(10).join(f'- {f}' for f in failures[:5])}
"""
        
        # Build telos alignment context
        telos_context = ""
        if context.get("telos"):
            telos_context = f"""
## Telos (Purpose) Alignment
{context['telos']}
"""
        
        # Additional focus areas
        focus = context.get("focus", "general improvement")
        
        prompt = f"""You are a code evolution engine for the DHARMIC_GODEL_CLAW project.
Your task is to propose a MINIMAL, ELEGANT improvement to the following component.

# Component: {component}

## Current Code
```python
{component_content}
```
{parent_context}
{failures_context}
{telos_context}
## Focus Area
{focus}

## Guidelines
1. Propose SMALL, FOCUSED changes (prefer 1-10 lines over major rewrites)
2. Prioritize: correctness > dharmic alignment > elegance > efficiency
3. NEVER touch secrets, credentials, .env files, or API keys
4. Ensure changes are reversible
5. Include clear rationale for the change
6. Consider the 7 dharmic gates: ahimsa (non-harm), satya (truth), 
   vyavasthit (order), consent, reversibility, svabhaava (telos), witness

## Required Output Format (JSON)
Respond with ONLY valid JSON in this format:
```json
{{
    "diff": "unified diff of changes (use +/- prefixes)",
    "rationale": "why this improves the code",
    "estimated_fitness": 0.75,
    "affected_files": ["{component}"],
    "mutation_type": "refactor|optimize|fix|enhance",
    "risk_level": "low|medium|high",
    "reversible": true
}}
```

Remember: Smaller, safer changes are better than ambitious rewrites.
"""
        return prompt
    
    def _read_component(self, component: str) -> str:
        """
        Read the content of a component file.
        
        Args:
            component: Relative path to component
            
        Returns:
            File content as string. Returns empty string if file doesn't exist (creation mode).
        """
        filepath = self.project_root / component
        if not filepath.exists():
            logger.info(f"Component not found (assuming creation): {component}")
            return ""
        
        return filepath.read_text()
    
    def _call_claude(self, prompt: str) -> str:
        """
        Call Claude via clawdbot subprocess.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Claude's response
        """
        if os.getenv("DGC_MOCK_LLM") == "1":
            logger.info("Using MOCK LLM response")
            # If the prompt asks to identify critical gap (AnalyzerAgent)
            if "Analyze the current state against the goals" in prompt:
                return json.dumps({
                    "file_path": "swarm/agents/tool_agent.py",
                    "description": "Implement generic ToolUseAgent for full tool capacity",
                    "severity": "high",
                    "fix_type": "architectural_feature"
                })
            
            # If the prompt asks for mutation (ProposerAgent)
            return json.dumps({
                "diff": "",
                "content": "import subprocess\nfrom dataclasses import dataclass\nfrom typing import List\n\n@dataclass\nclass ToolResult:\n    output: str\n    exit_code: int\n\nclass ToolUseAgent:\n    \"\"\"Agent capable of executing arbitrary shell commands (YOLO mode).\"\"\"\n    \n    def execute_shell(self, command: str) -> ToolResult:\n        result = subprocess.run(\n            command, shell=True, capture_output=True, text=True\n        )\n        return ToolResult(result.stdout + result.stderr, result.returncode)\n",
                "rationale": "Implements ToolUseAgent to satisfy Goal #1 (Full Tool Use)",
                "estimated_fitness": 0.9,
                "affected_files": ["swarm/agents/tool_agent.py"],
                "mutation_type": "create",
                "risk_level": "medium",
                "reversible": True
            })

        try:
            # Use clawdbot CLI to call Claude
            cmd = [
                self.clawdbot_path,
                "ask",
                "--model", self.model,
                "--no-stream",
                prompt,
            ]
            if SECURITY_AVAILABLE and EXEC_GUARD:
                result = EXEC_GUARD.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            
            if result.returncode != 0:
                logger.error("Claude call failed", context={
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                })
                raise MutationError(f"Claude call failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            logger.error("Claude call timed out", context={"timeout": self.timeout})
            raise MutationError(f"Claude call timed out after {self.timeout}s")
        except FileNotFoundError:
            logger.error("clawdbot not found", context={"path": self.clawdbot_path})
            raise MutationError(f"clawdbot not found at: {self.clawdbot_path}")
    
    def _parse_response(self, response: str) -> MutationProposal:
        """
        Parse Claude's JSON response into a MutationProposal.
        
        Args:
            response: Raw response from Claude
            
        Returns:
            Parsed MutationProposal
        """
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{[^{}]*"diff"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Last resort: assume entire response is JSON
                json_str = response
        
        try:
            data = json.loads(json_str)
            return MutationProposal.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response", context={
                "response": response[:500],
                "error": str(e),
            })
            raise MutationError(f"Failed to parse response: {e}")
    
    def propose_mutation(
        self,
        component: str,
        parent: Optional[EvolutionEntry] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MutationProposal:
        """
        Propose a mutation for a component.
        
        Args:
            component: Relative path to the component to mutate
            parent: Parent evolution entry for context
            context: Additional context dict with keys like:
                - focus: What to focus improvements on
                - recent_failures: List of recent failure descriptions
                - telos: The system's purpose/telos description
                
        Returns:
            MutationProposal with the proposed change
            
        Raises:
            MutationError: If mutation proposal fails
            SafetyViolationError: If proposal would affect forbidden files
        """
        context = context or {}
        
        # Safety check: don't mutate forbidden files
        if self.is_forbidden_file(component):
            raise SafetyViolationError(f"Cannot mutate forbidden file: {component}")
        
        logger.info("Proposing mutation", context={
            "component": component,
            "parent_id": parent.id if parent else None,
            "focus": context.get("focus"),
        })
        
        # Read component content
        component_content = self._read_component(component)
        
        # Build prompt
        prompt = self._build_prompt(component, parent, context, component_content)
        
        # Call Claude
        response = self._call_claude(prompt)
        
        # Parse response
        proposal = self._parse_response(response)
        
        # Validate safety
        self.validate_proposal(proposal)
        
        logger.dharmic("Mutation proposed", 
            fitness=proposal.estimated_fitness,
            context={
                "component": component,
                "mutation_type": proposal.mutation_type,
                "risk_level": proposal.risk_level,
                "affected_files": proposal.affected_files,
            }
        )
        
        return proposal
    
    def propose_multi_mutation(
        self,
        components: List[str],
        parent: Optional[EvolutionEntry] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[MutationProposal]:
        """
        Propose mutations for multiple components.
        
        Args:
            components: List of component paths
            parent: Parent evolution entry
            context: Additional context
            
        Returns:
            List of mutation proposals (one per component)
        """
        proposals = []
        for component in components:
            try:
                proposal = self.propose_mutation(component, parent, context)
                proposals.append(proposal)
            except SafetyViolationError as e:
                logger.warning(f"Skipping forbidden component: {e}")
            except MutationError as e:
                logger.error(f"Failed to mutate {component}: {e}")
        
        return proposals


# Convenience function
def propose_mutation(
    component: str,
    parent: Optional[EvolutionEntry] = None,
    context: Optional[Dict[str, Any]] = None,
    project_root: Path = None,
) -> MutationProposal:
    """
    Convenience function to propose a mutation.
    
    Args:
        component: Path to component
        parent: Parent evolution entry
        context: Additional context
        project_root: Project root path
        
    Returns:
        MutationProposal
    """
    mutator = Mutator(project_root=project_root)
    return mutator.propose_mutation(component, parent, context)


if __name__ == "__main__":
    # Simple test
    from .archive import EvolutionEntry, FitnessScore
    
    # Create a mock parent entry
    parent = EvolutionEntry(
        id="test_parent_001",
        timestamp="2024-02-04T12:00:00",
        component="src/dgm/archive.py",
        fitness=FitnessScore(
            correctness=0.8,
            dharmic_alignment=0.7,
            elegance=0.6,
            efficiency=0.75,
            safety=0.9
        ),
        gates_passed=["ahimsa", "satya"],
        gates_failed=["elegance"]
    )
    
    mutator = Mutator()
    
    # Test forbidden file detection
    assert mutator.is_forbidden_file(".env") == True
    assert mutator.is_forbidden_file(".env.local") == True
    assert mutator.is_forbidden_file("secrets.yml") == True
    assert mutator.is_forbidden_file("src/main.py") == False
    
    print("Basic tests passed!")
