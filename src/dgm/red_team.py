"""
Red Team Agent — Adversarial Code Attack Module

This is the immune system. It ATTACKS code to find weaknesses before they ship.
No mercy. No theoretical hand-waving. Actual exploits or GTFO.

Philosophy: Better to reject good code than ship vulnerable code.
"""

import ast
import re
import hashlib
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
import textwrap


class Severity(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "CRITICAL"  # Automatic rejection
    HIGH = "HIGH"          # Must fix before ship
    MEDIUM = "MEDIUM"      # Should fix
    LOW = "LOW"            # Nice to fix
    INFO = "INFO"          # Informational only


class AttackVector(Enum):
    """Categories of attack vectors we probe."""
    INPUT_VALIDATION = "input_validation"
    EDGE_CASES = "edge_cases"
    SECURITY = "security"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    RACE_CONDITIONS = "race_conditions"
    ERROR_HANDLING = "error_handling"
    DEPENDENCY_ISSUES = "dependency_issues"
    CODE_INJECTION = "code_injection"


@dataclass
class Vulnerability:
    """A discovered vulnerability with proof-of-concept exploit."""
    severity: Severity
    vector: AttackVector
    description: str
    exploit_poc: str  # Actual code that demonstrates the vulnerability
    location: Optional[str] = None  # Line number or function name
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    remediation: Optional[str] = None  # How to fix it


@dataclass
class RedTeamReport:
    """Complete attack report on analyzed code."""
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    edge_cases_found: List[str] = field(default_factory=list)
    bloat_indicators: List[str] = field(default_factory=list)
    security_score: float = 1.0  # 0-1, lower is worse
    recommendation: str = "PASS"  # PASS, FIX_REQUIRED, REJECT
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    attack_summary: str = ""
    code_hash: str = ""
    
    def has_critical(self) -> bool:
        """Check if any critical vulnerabilities exist."""
        return any(v.severity == Severity.CRITICAL for v in self.vulnerabilities)
    
    def has_high(self) -> bool:
        """Check if any high severity vulnerabilities exist."""
        return any(v.severity == Severity.HIGH for v in self.vulnerabilities)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "vulnerabilities": [
                {
                    "severity": v.severity.value,
                    "vector": v.vector.value,
                    "description": v.description,
                    "exploit_poc": v.exploit_poc,
                    "location": v.location,
                    "cwe_id": v.cwe_id,
                    "remediation": v.remediation
                }
                for v in self.vulnerabilities
            ],
            "edge_cases_found": self.edge_cases_found,
            "bloat_indicators": self.bloat_indicators,
            "security_score": self.security_score,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
            "attack_summary": self.attack_summary,
            "code_hash": self.code_hash
        }


class RedTeamAgent:
    """
    Adversarial agent that attacks code to find vulnerabilities.
    
    This is NOT a linter. This is a hostile attacker trying to break your code.
    We generate actual exploits, not theoretical concerns.
    """
    
    # Dangerous patterns that indicate potential vulnerabilities
    DANGEROUS_PATTERNS = {
        # Code execution vectors
        r'\beval\s*\(': ('CRITICAL', 'code_injection', 'CWE-94', 'eval() allows arbitrary code execution'),
        r'\bexec\s*\(': ('CRITICAL', 'code_injection', 'CWE-94', 'exec() allows arbitrary code execution'),
        r'\bcompile\s*\(': ('HIGH', 'code_injection', 'CWE-94', 'compile() can enable code injection'),
        r'__import__\s*\(': ('HIGH', 'code_injection', 'CWE-94', 'Dynamic imports can be exploited'),
        r'getattr\s*\([^,]+,\s*[^"\']+\)': ('MEDIUM', 'code_injection', 'CWE-94', 'Dynamic getattr with user input'),
        
        # Command injection
        r'\bos\.system\s*\(': ('CRITICAL', 'security', 'CWE-78', 'os.system() enables command injection'),
        r'\bos\.popen\s*\(': ('CRITICAL', 'security', 'CWE-78', 'os.popen() enables command injection'),
        r'subprocess\.\w+\([^)]*shell\s*=\s*True': ('CRITICAL', 'security', 'CWE-78', 'shell=True enables command injection'),
        r'subprocess\.call\s*\(\s*["\']': ('HIGH', 'security', 'CWE-78', 'Potential command injection in subprocess'),
        
        # Path traversal
        r'open\s*\([^)]*\+[^)]*\)': ('HIGH', 'security', 'CWE-22', 'Path concatenation may allow traversal'),
        r'os\.path\.join\s*\([^)]*\.\.[^)]*\)': ('HIGH', 'security', 'CWE-22', 'Path traversal with ..'),
        r'(?<!os\.path\.basename\()[\'"][^"\']*\.\.[^"\']*[\'"]': ('MEDIUM', 'security', 'CWE-22', 'Suspicious path with ..'),
        
        # SQL injection indicators
        r'execute\s*\(\s*["\'].*%s': ('HIGH', 'security', 'CWE-89', 'Potential SQL injection with string formatting'),
        r'execute\s*\(\s*f["\']': ('CRITICAL', 'security', 'CWE-89', 'SQL injection via f-string'),
        r'\.format\s*\([^)]*\)\s*\)': ('MEDIUM', 'security', 'CWE-89', 'String formatting in query context'),
        
        # Deserialization
        r'\bpickle\.loads?\s*\(': ('CRITICAL', 'security', 'CWE-502', 'pickle deserialization is dangerous'),
        r'\byaml\.load\s*\([^)]*(?!Loader)': ('HIGH', 'security', 'CWE-502', 'yaml.load without safe Loader'),
        r'\byaml\.unsafe_load\s*\(': ('CRITICAL', 'security', 'CWE-502', 'yaml.unsafe_load allows code execution'),
        
        # Crypto issues
        r'\bmd5\s*\(': ('MEDIUM', 'security', 'CWE-328', 'MD5 is cryptographically broken'),
        r'\bsha1\s*\(': ('MEDIUM', 'security', 'CWE-328', 'SHA1 is deprecated for security'),
        r'random\.(random|randint|choice)': ('MEDIUM', 'security', 'CWE-330', 'Use secrets module for security'),
        
        # Resource exhaustion
        r'while\s+True\s*:(?![^:]*break)': ('HIGH', 'resource_exhaustion', 'CWE-835', 'Infinite loop without break'),
        r'\.read\s*\(\s*\)': ('MEDIUM', 'resource_exhaustion', 'CWE-400', 'Unbounded read may exhaust memory'),
        r'\*\s*\d{6,}': ('HIGH', 'resource_exhaustion', 'CWE-400', 'Large multiplication may exhaust memory'),
        r'range\s*\(\s*\d{9,}': ('HIGH', 'resource_exhaustion', 'CWE-400', 'Huge range may exhaust memory'),
        
        # Error handling issues
        r'except\s*:\s*(?:pass|\.\.\.)\s*$': ('MEDIUM', 'error_handling', 'CWE-390', 'Silent exception swallowing'),
        r'except\s+Exception\s*:\s*(?:pass|\.\.\.)\s*$': ('MEDIUM', 'error_handling', 'CWE-390', 'Catching all exceptions silently'),
        
        # Hardcoded secrets
        r'(?:password|passwd|pwd|secret|api_key|apikey|token)\s*=\s*["\'][^"\']+["\']': ('HIGH', 'security', 'CWE-798', 'Hardcoded credential'),
        r'(?:AWS|AZURE|GCP)_\w*(?:KEY|SECRET|TOKEN)\s*=': ('CRITICAL', 'security', 'CWE-798', 'Hardcoded cloud credential'),
    }
    
    # Input validation attack payloads
    ATTACK_PAYLOADS = {
        'null': [None, '', [], {}, set(), 0, 0.0, False],
        'huge': ['A' * 10_000_000, list(range(1_000_000)), {str(i): i for i in range(100_000)}],
        'unicode': ['🔥' * 1000, '\x00\x00\x00', '\udcff', '你好' * 10000, '\n' * 100000],
        'special': ["'; DROP TABLE users; --", '{{7*7}}', '${7*7}', '<script>alert(1)</script>'],
        'injection': ['__import__("os").system("id")', 'eval("1+1")', '$(whoami)', '`id`'],
        'path': ['../../../etc/passwd', '....//....//etc/passwd', '%2e%2e%2f', '..\\..\\..\\windows\\system32'],
        'numeric': [float('inf'), float('-inf'), float('nan'), -1, 2**63, -2**63, 10**308],
        'type_confusion': [{'__class__': 'hacked'}, type('Evil', (), {'__str__': lambda s: 'pwned'})()],
    }
    
    def __init__(self, strict_mode: bool = True, max_recursion: int = 100):
        """
        Initialize the Red Team Agent.
        
        Args:
            strict_mode: If True, any CRITICAL vulnerability = REJECT
            max_recursion: Maximum recursion depth for analysis
        """
        self.strict_mode = strict_mode
        self.max_recursion = max_recursion
        self._analyzed_hashes: Set[str] = set()
    
    def attack(self, code: str, context: Optional[Dict[str, Any]] = None) -> RedTeamReport:
        """
        Main attack method. Launches all attack vectors against the code.
        
        Args:
            code: The source code to attack
            context: Optional context about the code (function signatures, purpose, etc.)
        
        Returns:
            RedTeamReport with all findings
        """
        context = context or {}
        report = RedTeamReport()
        report.code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        
        # Skip if we've already analyzed this exact code
        if report.code_hash in self._analyzed_hashes:
            report.attack_summary = "Already analyzed (cached)"
            return report
        
        # Parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            report.vulnerabilities.append(Vulnerability(
                severity=Severity.CRITICAL,
                vector=AttackVector.ERROR_HANDLING,
                description=f"Code has syntax errors and won't run: {e}",
                exploit_poc=f"# Just try to import it:\nimport ast\nast.parse('''{code[:100]}...''')",
                cwe_id="CWE-1104"
            ))
            report.recommendation = "REJECT"
            report.security_score = 0.0
            return report
        
        # Launch all attack vectors
        self._attack_patterns(code, report)
        self._attack_ast(tree, code, report)
        self._attack_input_validation(tree, code, report, context)
        self._attack_edge_cases(tree, code, report)
        self._attack_resource_exhaustion(tree, code, report)
        self._attack_race_conditions(tree, code, report)
        self._attack_error_handling(tree, code, report)
        self._attack_dependencies(tree, code, report)
        self._detect_bloat(tree, code, report)
        
        # Calculate security score and recommendation
        self._calculate_score(report)
        self._generate_summary(report, code)
        
        self._analyzed_hashes.add(report.code_hash)
        return report
    
    def _attack_patterns(self, code: str, report: RedTeamReport) -> None:
        """Attack using regex pattern matching for known dangerous patterns."""
        lines = code.split('\n')
        
        for pattern, (severity, vector, cwe, description) in self.DANGEROUS_PATTERNS.items():
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    # Generate specific exploit PoC
                    exploit = self._generate_pattern_exploit(pattern, line, i)
                    report.vulnerabilities.append(Vulnerability(
                        severity=Severity[severity],
                        vector=AttackVector[vector.upper()],
                        description=f"{description} at line {i}",
                        exploit_poc=exploit,
                        location=f"line {i}",
                        cwe_id=cwe,
                        remediation=self._get_remediation(pattern)
                    ))
    
    def _attack_ast(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Deep AST analysis for structural vulnerabilities."""
        
        class VulnerabilityFinder(ast.NodeVisitor):
            def __init__(self, report: RedTeamReport, agent: 'RedTeamAgent'):
                self.report = report
                self.agent = agent
                self.in_try_block = False
                self.function_depth = 0
                self.class_depth = 0
            
            def visit_Call(self, node: ast.Call) -> None:
                # Check for dangerous function calls
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    # Check for dangerous builtins
                    if func_name in ('eval', 'exec', 'compile'):
                        if node.args:
                            arg = ast.unparse(node.args[0]) if hasattr(ast, 'unparse') else '<arg>'
                            exploit = f'''# Exploit for {func_name}():
code_to_attack = """
def vulnerable_func(user_input):
    return {func_name}(user_input)
"""
# Attack payload:
malicious_input = "__import__('os').system('cat /etc/passwd')"
# This will execute arbitrary system commands!
vulnerable_func(malicious_input)
'''
                            self.report.vulnerabilities.append(Vulnerability(
                                severity=Severity.CRITICAL,
                                vector=AttackVector.CODE_INJECTION,
                                description=f"{func_name}() called with potentially tainted input: {arg}",
                                exploit_poc=exploit,
                                location=f"line {node.lineno}",
                                cwe_id="CWE-94",
                                remediation=f"Never use {func_name}() with user input. Use ast.literal_eval() for safe evaluation."
                            ))
                    
                    # Check for dangerous file operations
                    if func_name == 'open':
                        if node.args:
                            path_arg = ast.unparse(node.args[0]) if hasattr(ast, 'unparse') else '<path>'
                            if '+' in path_arg or 'format' in path_arg or path_arg.startswith('f'):
                                exploit = f'''# Path traversal exploit:
def vulnerable_read(filename):
    with open(f"/data/{{filename}}") as f:  # VULNERABLE!
        return f.read()

# Attack:
vulnerable_read("../../../etc/passwd")
# Reads sensitive system file!
'''
                                self.report.vulnerabilities.append(Vulnerability(
                                    severity=Severity.HIGH,
                                    vector=AttackVector.SECURITY,
                                    description=f"File open with dynamic path: {path_arg}",
                                    exploit_poc=exploit,
                                    location=f"line {node.lineno}",
                                    cwe_id="CWE-22",
                                    remediation="Validate and sanitize file paths. Use os.path.basename() and whitelist directories."
                                ))
                
                self.generic_visit(node)
            
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.function_depth += 1
                
                # Check for missing input validation
                if node.args.args and not self._has_input_validation(node):
                    params = [arg.arg for arg in node.args.args if arg.arg != 'self']
                    if params:
                        exploit = f'''# Missing input validation exploit:
def {node.name}({', '.join(params)}):
    # No type checking, no bounds checking!
    ...

# Attacks:
{node.name}(None)  # NoneType crash
{node.name}("")  # Empty string edge case
{node.name}("A" * 10**8)  # Memory exhaustion
{node.name}({{"__class__": "hacked"}})  # Type confusion
'''
                        self.report.edge_cases_found.append(
                            f"Function '{node.name}' has no input validation for: {params}"
                        )
                
                # Check for recursive functions without depth limit
                if self._is_recursive(node) and not self._has_recursion_limit(node):
                    exploit = f'''# Stack overflow exploit:
def {node.name}(n):
    return {node.name}(n-1)  # No base case check!

# Attack - cause stack overflow:
import sys
sys.setrecursionlimit(10**6)
{node.name}(10**6)  # CRASH: RecursionError
'''
                    self.report.vulnerabilities.append(Vulnerability(
                        severity=Severity.HIGH,
                        vector=AttackVector.RESOURCE_EXHAUSTION,
                        description=f"Recursive function '{node.name}' without depth limit",
                        exploit_poc=exploit,
                        location=f"line {node.lineno}",
                        cwe_id="CWE-674",
                        remediation="Add explicit recursion depth check or convert to iterative"
                    ))
                
                self.generic_visit(node)
                self.function_depth -= 1
            
            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                # Check for async without timeout
                has_timeout = any(
                    isinstance(n, ast.Call) and 
                    isinstance(n.func, ast.Attribute) and 
                    'timeout' in n.func.attr.lower()
                    for n in ast.walk(node)
                )
                if not has_timeout and self._has_await(node):
                    exploit = f'''# Async hanging exploit:
async def {node.name}(...):
    await some_operation()  # No timeout!

# Attack - hang forever:
import asyncio
async def malicious_server():
    await asyncio.sleep(float('inf'))  # Never returns

# Your code will hang waiting for this
'''
                    self.report.vulnerabilities.append(Vulnerability(
                        severity=Severity.MEDIUM,
                        vector=AttackVector.RESOURCE_EXHAUSTION,
                        description=f"Async function '{node.name}' without timeout",
                        exploit_poc=exploit,
                        location=f"line {node.lineno}",
                        cwe_id="CWE-400",
                        remediation="Use asyncio.wait_for() with timeout for all async operations"
                    ))
                
                self.generic_visit(node)
            
            def visit_Try(self, node: ast.Try) -> None:
                self.in_try_block = True
                
                # Check for overly broad exception handling
                for handler in node.handlers:
                    if handler.type is None:  # bare except:
                        exploit = '''# Exception swallowing exploit:
try:
    critical_operation()
except:  # Catches EVERYTHING including KeyboardInterrupt!
    pass

# Attack - hide security breaches:
try:
    raise SecurityBreach("Data exfiltrated!")
except:
    pass  # Attacker's activity is hidden!
'''
                        self.report.vulnerabilities.append(Vulnerability(
                            severity=Severity.MEDIUM,
                            vector=AttackVector.ERROR_HANDLING,
                            description="Bare except clause catches all exceptions including security events",
                            exploit_poc=exploit,
                            location=f"line {node.lineno}",
                            cwe_id="CWE-396",
                            remediation="Catch specific exceptions. Never use bare 'except:'"
                        ))
                
                self.generic_visit(node)
                self.in_try_block = False
            
            def visit_Import(self, node: ast.Import) -> None:
                # Check for dangerous imports
                dangerous_modules = {
                    'pickle': ('HIGH', 'Pickle allows arbitrary code execution during deserialization'),
                    'marshal': ('HIGH', 'Marshal can execute code during deserialization'),
                    'shelve': ('MEDIUM', 'Shelve uses pickle internally'),
                    'subprocess': ('INFO', 'Subprocess can execute system commands'),
                }
                
                for alias in node.names:
                    if alias.name in dangerous_modules:
                        severity, desc = dangerous_modules[alias.name]
                        self.report.vulnerabilities.append(Vulnerability(
                            severity=Severity[severity],
                            vector=AttackVector.DEPENDENCY_ISSUES,
                            description=f"Dangerous import: {alias.name} - {desc}",
                            exploit_poc=f"# The import itself isn't the vuln, but usage might be.\n# Audit all uses of {alias.name} in this code.",
                            location=f"line {node.lineno}",
                            cwe_id="CWE-502"
                        ))
                
                self.generic_visit(node)
            
            def _has_input_validation(self, node: ast.FunctionDef) -> bool:
                """Check if function has any input validation."""
                for child in ast.walk(node):
                    # Check for isinstance, type checks, assertions
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id in ('isinstance', 'type', 'len', 'hasattr'):
                                return True
                    elif isinstance(child, ast.Assert):
                        return True
                    elif isinstance(child, ast.If):
                        # Check if it's a validation pattern
                        test = ast.unparse(child.test) if hasattr(ast, 'unparse') else ''
                        if 'is None' in test or 'not ' in test or '==' in test:
                            return True
                return False
            
            def _is_recursive(self, node: ast.FunctionDef) -> bool:
                """Check if function calls itself."""
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name) and child.func.id == node.name:
                            return True
                return False
            
            def _has_recursion_limit(self, node: ast.FunctionDef) -> bool:
                """Check if recursive function has depth limit."""
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        test = ast.unparse(child.test) if hasattr(ast, 'unparse') else ''
                        if any(kw in test for kw in ('depth', 'level', 'limit', '<', '>', '<=', '>=')):
                            return True
                return False
            
            def _has_await(self, node: ast.AsyncFunctionDef) -> bool:
                """Check if async function has await statements."""
                for child in ast.walk(node):
                    if isinstance(child, ast.Await):
                        return True
                return False
        
        finder = VulnerabilityFinder(report, self)
        finder.visit(tree)
    
    def _attack_input_validation(self, tree: ast.AST, code: str, 
                                  report: RedTeamReport, context: Dict) -> None:
        """Generate input validation attack payloads."""
        
        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args if arg.arg != 'self']
                
                if params and not self._has_type_hints(node):
                    # Generate attack payloads for each parameter
                    for param in params[:3]:  # Limit to first 3 params
                        attacks = []
                        for category, payloads in self.ATTACK_PAYLOADS.items():
                            for payload in payloads[:2]:  # First 2 of each category
                                attacks.append(f"  {node.name}({param}={repr(payload)})  # {category}")
                        
                        if attacks:
                            exploit = f'''# Input validation attacks for {node.name}():
# These may crash, hang, or behave unexpectedly:

{chr(10).join(attacks[:10])}

# Run each and observe behavior!
'''
                            report.edge_cases_found.append(
                                f"'{node.name}({param})' - no type hints, vulnerable to type confusion"
                            )
    
    def _attack_edge_cases(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Find edge case vulnerabilities."""
        
        # Check for division operations (div by zero)
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if isinstance(node.right, ast.Name):  # Division by variable
                    exploit = f'''# Division by zero exploit:
# Code: x / {node.right.id}

# Attack:
{node.right.id} = 0
# Result: ZeroDivisionError crashes the program!

# Also try:
{node.right.id} = float('inf')  # May produce unexpected results
{node.right.id} = float('nan')  # NaN propagation
'''
                    report.edge_cases_found.append(f"Division by variable at line {node.lineno} - potential ZeroDivisionError")
        
        # Check for list/dict access
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Name):  # Dynamic indexing
                    exploit = f'''# Index out of bounds exploit:
# Code: container[{node.slice.id}]

# Attack:
{node.slice.id} = -99999  # Negative index
{node.slice.id} = 99999   # Way past end
{node.slice.id} = None    # TypeError

# For dicts:
{node.slice.id} = "nonexistent_key"  # KeyError
'''
                    report.edge_cases_found.append(f"Dynamic subscript access at line {node.lineno}")
    
    def _attack_resource_exhaustion(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Find resource exhaustion vulnerabilities."""
        
        # Check for string multiplication
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    exploit = f'''# Memory exhaustion via string multiplication:
# Code: "{node.left.value}" * n

# Attack:
n = 10**9  # One billion
result = "{node.left.value}" * n
# Result: MemoryError or system freeze!
'''
                    report.vulnerabilities.append(Vulnerability(
                        severity=Severity.MEDIUM,
                        vector=AttackVector.RESOURCE_EXHAUSTION,
                        description="String multiplication with variable factor",
                        exploit_poc=exploit,
                        location=f"line {node.lineno}",
                        cwe_id="CWE-400",
                        remediation="Add bounds check on multiplier"
                    ))
        
        # Check for list comprehensions with unbounded ranges
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                for gen in node.generators:
                    if isinstance(gen.iter, ast.Call):
                        if isinstance(gen.iter.func, ast.Name) and gen.iter.func.id == 'range':
                            if gen.iter.args:
                                arg = gen.iter.args[-1]
                                if isinstance(arg, ast.Name):  # range(n) where n is variable
                                    exploit = f'''# Memory exhaustion via list comprehension:
# Code: [... for x in range({arg.id})]

# Attack:
{arg.id} = 10**9
result = [x for x in range({arg.id})]
# Result: MemoryError - tries to allocate billions of elements!
'''
                                    report.vulnerabilities.append(Vulnerability(
                                        severity=Severity.MEDIUM,
                                        vector=AttackVector.RESOURCE_EXHAUSTION,
                                        description="List comprehension with unbounded range",
                                        exploit_poc=exploit,
                                        location=f"line {node.lineno}",
                                        cwe_id="CWE-400",
                                        remediation="Use generator expression or limit range size"
                                    ))
    
    def _attack_race_conditions(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Find potential race conditions."""
        
        # Check for threading/multiprocessing usage without locks
        uses_threading = 'threading' in code or 'multiprocessing' in code
        uses_locks = 'Lock' in code or 'RLock' in code or 'Semaphore' in code
        has_shared_state = bool(re.search(r'global\s+\w+', code)) or 'self.' in code
        
        if uses_threading and has_shared_state and not uses_locks:
            exploit = '''# Race condition exploit:
import threading

# Shared state without protection:
counter = 0

def increment():
    global counter
    for _ in range(100000):
        counter += 1  # NOT ATOMIC!

# Attack - demonstrate race:
threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)  # Expected: 1000000, Actual: much less!
'''
            report.vulnerabilities.append(Vulnerability(
                severity=Severity.HIGH,
                vector=AttackVector.RACE_CONDITIONS,
                description="Threading with shared state but no locks",
                exploit_poc=exploit,
                cwe_id="CWE-362",
                remediation="Use threading.Lock() to protect shared state"
            ))
        
        # Check for file operations that might have TOCTOU issues
        if re.search(r'os\.path\.exists.*open\(', code, re.DOTALL):
            exploit = '''# TOCTOU (Time-of-check Time-of-use) exploit:
# Code pattern:
if os.path.exists(filename):
    # ATTACKER WINDOW: File can be replaced here!
    with open(filename) as f:
        data = f.read()

# Attack:
# 1. Create legitimate file
# 2. Wait for exists() check to pass
# 3. Replace file with symlink to /etc/passwd
# 4. Victim reads sensitive file!

# Mitigation: Use try/except instead of exists()
'''
            report.vulnerabilities.append(Vulnerability(
                severity=Severity.HIGH,
                vector=AttackVector.RACE_CONDITIONS,
                description="TOCTOU vulnerability: check then open pattern",
                exploit_poc=exploit,
                cwe_id="CWE-367",
                remediation="Use try/except for file access instead of os.path.exists()"
            ))
    
    def _attack_error_handling(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Find error handling vulnerabilities."""
        
        # Find functions without any error handling
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))
                has_raise = any(isinstance(child, ast.Raise) for child in ast.walk(node))
                
                # Check for operations that commonly fail
                risky_ops = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name) and child.func.id == 'open':
                            risky_ops.append('file I/O')
                    elif isinstance(child, ast.Subscript):
                        risky_ops.append('indexing')
                    elif isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div):
                        risky_ops.append('division')
                
                if risky_ops and not has_try:
                    exploit = f'''# Unhandled exception crash:
# Function {node.name}() performs: {', '.join(set(risky_ops))}
# But has NO try/except!

# Attack - crash with bad input:
try:
    {node.name}(malformed_input)
except Exception as e:
    print(f"CRASHED: {{type(e).__name__}}: {{e}}")
    # Attacker now knows internal error details!
'''
                    report.vulnerabilities.append(Vulnerability(
                        severity=Severity.LOW,
                        vector=AttackVector.ERROR_HANDLING,
                        description=f"Function '{node.name}' has risky operations without error handling",
                        exploit_poc=exploit,
                        location=f"line {node.lineno}",
                        cwe_id="CWE-755",
                        remediation="Add try/except for operations that can fail"
                    ))
    
    def _attack_dependencies(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Check for dependency issues."""
        
        # Find all imports
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        # Check for version-sensitive imports
        version_sensitive = {'asyncio', 'typing', 'dataclasses', 'pathlib'}
        sensitive_used = imports & version_sensitive
        
        if sensitive_used and 'sys' not in imports:
            exploit = f'''# Version compatibility exploit:
# Uses version-sensitive modules: {sensitive_used}
# But doesn't check Python version!

# Attack on old Python:
# Python 3.6 doesn't have: dataclasses (3.7+)
# Python 3.5 doesn't have: async generators
# Python 3.4 doesn't have: typing (3.5+)

import sys
print(sys.version_info)
# If < 3.7 with dataclasses: ImportError!
'''
            report.vulnerabilities.append(Vulnerability(
                severity=Severity.LOW,
                vector=AttackVector.DEPENDENCY_ISSUES,
                description=f"Uses version-sensitive modules without version check: {sensitive_used}",
                exploit_poc=exploit,
                cwe_id="CWE-1104",
                remediation="Add sys.version_info check or declare Python version requirement"
            ))
        
        # Check for missing __future__ imports that might indicate issues
        if 'annotations' in code and '__future__' not in code:
            if 'from __future__ import annotations' not in code:
                report.edge_cases_found.append(
                    "Uses 'annotations' but may need 'from __future__ import annotations' for forward refs"
                )
    
    def _detect_bloat(self, tree: ast.AST, code: str, report: RedTeamReport) -> None:
        """Detect code bloat indicators."""
        
        lines = code.split('\n')
        
        # Check for overly long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno'):
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        report.bloat_indicators.append(
                            f"Function '{node.name}' is {length} lines - consider splitting"
                        )
        
        # Check for duplicated code patterns
        line_hashes = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 20:  # Ignore short lines
                h = hashlib.md5(stripped.encode()).hexdigest()
                if h in line_hashes:
                    report.bloat_indicators.append(
                        f"Duplicate code at lines {line_hashes[h]+1} and {i+1}"
                    )
                line_hashes[h] = i
        
        # Check for too many parameters
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 5:
                    report.bloat_indicators.append(
                        f"Function '{node.name}' has {param_count} parameters - consider refactoring"
                    )
        
        # Check for deeply nested code
        max_depth = self._get_max_nesting_depth(tree)
        if max_depth > 4:
            report.bloat_indicators.append(
                f"Code has nesting depth of {max_depth} - consider flattening"
            )
    
    def _calculate_score(self, report: RedTeamReport) -> None:
        """Calculate security score and recommendation."""
        
        # Start at 1.0 and deduct based on findings
        score = 1.0
        
        severity_weights = {
            Severity.CRITICAL: 0.4,
            Severity.HIGH: 0.15,
            Severity.MEDIUM: 0.05,
            Severity.LOW: 0.02,
            Severity.INFO: 0.01
        }
        
        for vuln in report.vulnerabilities:
            score -= severity_weights.get(vuln.severity, 0)
        
        # Deduct for edge cases and bloat
        score -= len(report.edge_cases_found) * 0.02
        score -= len(report.bloat_indicators) * 0.01
        
        report.security_score = max(0.0, min(1.0, score))
        
        # Determine recommendation
        if report.has_critical():
            report.recommendation = "REJECT"
        elif report.has_high() or report.security_score < 0.5:
            report.recommendation = "FIX_REQUIRED"
        elif report.security_score < 0.8:
            report.recommendation = "FIX_REQUIRED"
        else:
            report.recommendation = "PASS"
        
        # Override for strict mode
        if self.strict_mode and report.has_critical():
            report.recommendation = "REJECT"
    
    def _generate_summary(self, report: RedTeamReport, code: str) -> None:
        """Generate attack summary."""
        
        critical_count = sum(1 for v in report.vulnerabilities if v.severity == Severity.CRITICAL)
        high_count = sum(1 for v in report.vulnerabilities if v.severity == Severity.HIGH)
        medium_count = sum(1 for v in report.vulnerabilities if v.severity == Severity.MEDIUM)
        low_count = sum(1 for v in report.vulnerabilities if v.severity == Severity.LOW)
        
        report.attack_summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                    RED TEAM ATTACK REPORT                      ║
╠══════════════════════════════════════════════════════════════╣
║  Code Hash: {report.code_hash:<47}║
║  Security Score: {report.security_score:.2f}/1.00{' '*36}║
║  Recommendation: {report.recommendation:<43}║
╠══════════════════════════════════════════════════════════════╣
║  VULNERABILITIES FOUND:                                        ║
║    🔴 CRITICAL: {critical_count:<44}║
║    🟠 HIGH:     {high_count:<44}║
║    🟡 MEDIUM:   {medium_count:<44}║
║    🟢 LOW:      {low_count:<44}║
╠══════════════════════════════════════════════════════════════╣
║  Edge Cases: {len(report.edge_cases_found):<47}║
║  Bloat Indicators: {len(report.bloat_indicators):<41}║
╚══════════════════════════════════════════════════════════════╝
"""
    
    def _generate_pattern_exploit(self, pattern: str, line: str, line_num: int) -> str:
        """Generate specific exploit for a pattern match."""
        
        exploits = {
            r'\beval\s*\(': f'''# Code at line {line_num}: {line.strip()[:50]}
# Exploit:
malicious = "__import__('os').system('cat /etc/passwd')"
eval(malicious)  # Executes arbitrary system command!
''',
            r'\bexec\s*\(': f'''# Code at line {line_num}: {line.strip()[:50]}
# Exploit:
malicious = """
import os
os.system('rm -rf /')  # Could delete everything!
"""
exec(malicious)
''',
            r'\bos\.system\s*\(': f'''# Code at line {line_num}: {line.strip()[:50]}
# Exploit - command injection:
user_input = "; cat /etc/passwd; echo "
os.system(f"echo {{user_input}}")  # Executes injected command!
''',
            r'\bpickle\.loads?\s*\(': f'''# Code at line {line_num}: {line.strip()[:50]}
# Exploit - arbitrary code execution:
import pickle
import os

class Exploit:
    def __reduce__(self):
        return (os.system, ('cat /etc/passwd',))

malicious_pickle = pickle.dumps(Exploit())
pickle.loads(malicious_pickle)  # Executes os.system!
''',
            r'subprocess\.\w+\([^)]*shell\s*=\s*True': f'''# Code at line {line_num}: {line.strip()[:50]}
# Exploit:
user_input = "; rm -rf /"
subprocess.call(f"echo {{user_input}}", shell=True)  # BOOM!
''',
        }
        
        for p, exploit in exploits.items():
            if re.search(p, pattern, re.IGNORECASE):
                return exploit
        
        return f"# Vulnerable pattern found at line {line_num}:\n# {line.strip()}\n# Manual review required for exploitation."
    
    def _get_remediation(self, pattern: str) -> str:
        """Get remediation advice for a pattern."""
        
        remediations = {
            r'\beval\s*\(': "Use ast.literal_eval() for safe evaluation, or avoid eval entirely.",
            r'\bexec\s*\(': "Avoid exec(). Use safe alternatives like importlib for dynamic imports.",
            r'\bos\.system\s*\(': "Use subprocess.run() with shell=False and list arguments.",
            r'\bos\.popen\s*\(': "Use subprocess.run() with capture_output=True.",
            r'\bpickle\.loads?\s*\(': "Use json for serialization, or sign pickles with hmac.",
            r'subprocess\.\w+\([^)]*shell\s*=\s*True': "Use shell=False and pass command as list.",
            r'(?:password|passwd|pwd|secret)': "Use environment variables or secure vault for credentials.",
        }
        
        for p, advice in remediations.items():
            if re.search(p, pattern, re.IGNORECASE):
                return advice
        
        return "Review and fix the vulnerable pattern."
    
    def _has_type_hints(self, node: ast.FunctionDef) -> bool:
        """Check if function has type hints."""
        # Check return annotation
        if node.returns:
            return True
        # Check argument annotations
        for arg in node.args.args:
            if arg.annotation:
                return True
        return False
    
    def _get_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth in code."""
        
        def get_depth(node: ast.AST, current: int = 0) -> int:
            max_depth = current
            
            # Nodes that increase nesting
            nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, 
                           ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, nesting_nodes):
                    child_depth = get_depth(child, current + 1)
                else:
                    child_depth = get_depth(child, current)
                max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(tree)


def quick_scan(code: str) -> Tuple[str, float]:
    """
    Quick scan for immediate red flags.
    Returns (recommendation, security_score).
    """
    agent = RedTeamAgent(strict_mode=True)
    report = agent.attack(code, {})
    return report.recommendation, report.security_score


def full_report(code: str, context: Optional[Dict] = None) -> RedTeamReport:
    """
    Full security analysis with detailed report.
    """
    agent = RedTeamAgent(strict_mode=True)
    return agent.attack(code, context or {})


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python red_team.py <file.py>")
        print("       python red_team.py --stdin")
        sys.exit(1)
    
    if sys.argv[1] == "--stdin":
        code = sys.stdin.read()
    else:
        with open(sys.argv[1]) as f:
            code = f.read()
    
    report = full_report(code)
    print(report.attack_summary)
    
    if report.vulnerabilities:
        print("\n=== VULNERABILITY DETAILS ===\n")
        for i, vuln in enumerate(report.vulnerabilities, 1):
            print(f"[{i}] {vuln.severity.value}: {vuln.description}")
            print(f"    Vector: {vuln.vector.value}")
            if vuln.location:
                print(f"    Location: {vuln.location}")
            if vuln.cwe_id:
                print(f"    CWE: {vuln.cwe_id}")
            print(f"\n    Exploit PoC:")
            for line in vuln.exploit_poc.split('\n'):
                print(f"      {line}")
            if vuln.remediation:
                print(f"\n    Remediation: {vuln.remediation}")
            print()
    
    if report.edge_cases_found:
        print("\n=== EDGE CASES ===")
        for ec in report.edge_cases_found:
            print(f"  • {ec}")
    
    if report.bloat_indicators:
        print("\n=== BLOAT INDICATORS ===")
        for bi in report.bloat_indicators:
            print(f"  • {bi}")
    
    sys.exit(0 if report.recommendation == "PASS" else 1)
