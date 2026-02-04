"""
DGM Fitness - Multi-Dimensional Fitness Evaluation
===================================================
Evaluates evolution candidates on multiple dimensions.

Dimensions:
1. Correctness - Does it work? (tests pass)
2. Dharmic Alignment - Passes all 7 gates?
3. Elegance - Clean, minimal, readable?
4. Efficiency - Resource usage acceptable?
5. Safety - No harmful side effects?
"""
import subprocess
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .archive import FitnessScore


@dataclass
class EvaluationResult:
    """Result of fitness evaluation."""
    score: FitnessScore
    details: Dict[str, Any]
    tests_passed: int
    tests_failed: int
    gates_passed: List[str]
    gates_failed: List[str]


class FitnessEvaluator:
    """
    Evaluates fitness of code changes.
    
    Each dimension is scored 0.0-1.0.
    """
    
    # The 7 dharmic gates
    DHARMIC_GATES = [
        "ahimsa",        # Non-harm
        "satya",         # Truth
        "vyavasthit",    # Natural order
        "consent",       # Human approval
        "reversibility", # Can undo
        "svabhaava",     # Telos alignment
        "witness",       # Meta-observation
    ]
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.test_dir = self.project_root / "tests"
    
    def evaluate(
        self,
        component_path: str,
        diff: str = "",
        run_tests: bool = True
    ) -> EvaluationResult:
        """Full fitness evaluation."""
        
        score = FitnessScore()
        details = {}
        
        # 1. Correctness (tests)
        if run_tests:
            test_result = self._evaluate_correctness(component_path)
            score.correctness = test_result["score"]
            details["correctness"] = test_result
        else:
            score.correctness = 0.5  # Unknown
            details["correctness"] = {"skipped": True}
        
        # 2. Dharmic alignment
        gate_result = self._evaluate_dharmic_gates(component_path, diff)
        score.dharmic_alignment = gate_result["score"]
        details["dharmic_alignment"] = gate_result
        
        # 3. Elegance
        elegance_result = self._evaluate_elegance(component_path)
        score.elegance = elegance_result["score"]
        details["elegance"] = elegance_result
        
        # 4. Efficiency (placeholder - would need runtime measurement)
        score.efficiency = 0.7  # Default reasonable
        details["efficiency"] = {"note": "Not measured"}
        
        # 5. Safety
        safety_result = self._evaluate_safety(component_path, diff)
        score.safety = safety_result["score"]
        details["safety"] = safety_result
        
        return EvaluationResult(
            score=score,
            details=details,
            tests_passed=details.get("correctness", {}).get("passed", 0),
            tests_failed=details.get("correctness", {}).get("failed", 0),
            gates_passed=gate_result.get("passed", []),
            gates_failed=gate_result.get("failed", []),
        )
    
    def _evaluate_correctness(self, component_path: str) -> Dict[str, Any]:
        """Run tests and score correctness."""
        try:
            # Find test file
            component_name = Path(component_path).stem
            test_patterns = [
                self.test_dir / f"test_{component_name}.py",
                self.test_dir / "unit" / f"test_{component_name}.py",
            ]
            
            test_file = None
            for pattern in test_patterns:
                if pattern.exists():
                    test_file = pattern
                    break
            
            if not test_file:
                return {"score": 0.5, "note": "No tests found", "passed": 0, "failed": 0}
            
            # Run pytest
            result = subprocess.run(
                ["python3", "-m", "pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root
            )
            
            # Parse results
            output = result.stdout + result.stderr
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            total = passed + failed
            
            if total == 0:
                return {"score": 0.5, "note": "No tests ran", "passed": 0, "failed": 0}
            
            score = passed / total
            return {
                "score": score,
                "passed": passed,
                "failed": failed,
                "output": output[-500:] if len(output) > 500 else output
            }
            
        except subprocess.TimeoutExpired:
            return {"score": 0.0, "error": "Tests timed out", "passed": 0, "failed": 0}
        except Exception as e:
            return {"score": 0.0, "error": str(e), "passed": 0, "failed": 0}
    
    def _evaluate_dharmic_gates(self, component_path: str, diff: str) -> Dict[str, Any]:
        """Check which dharmic gates the change passes."""
        passed = []
        failed = []
        
        # Read the component
        try:
            component_full_path = self.project_root / component_path
            if component_full_path.exists():
                content = component_full_path.read_text()
            else:
                content = ""
        except:
            content = ""
        
        # Gate checks (simplified - real implementation would be more sophisticated)
        
        # AHIMSA: No harmful patterns
        harmful_patterns = ["os.remove", "shutil.rmtree", "subprocess.call", "eval(", "exec("]
        if not any(p in content for p in harmful_patterns) and not any(p in diff for p in harmful_patterns):
            passed.append("ahimsa")
        else:
            failed.append("ahimsa")
        
        # SATYA: Has docstrings
        if '"""' in content or "'''" in content:
            passed.append("satya")
        else:
            failed.append("satya")
        
        # VYAVASTHIT: Follows existing patterns (has type hints)
        if ": " in content and "->" in content:
            passed.append("vyavasthit")
        else:
            failed.append("vyavasthit")
        
        # CONSENT: Requires explicit approval (always fails automatically)
        failed.append("consent")  # Must be approved by human
        
        # REVERSIBILITY: Has rollback mechanism mentioned
        if "rollback" in content.lower() or "undo" in content.lower() or "revert" in content.lower():
            passed.append("reversibility")
        else:
            failed.append("reversibility")
        
        # SVABHAAVA: References telos
        if "telos" in content.lower() or "moksha" in content.lower():
            passed.append("svabhaava")
        else:
            failed.append("svabhaava")
        
        # WITNESS: Has observation/logging
        if "logger" in content or "logging" in content or "observe" in content.lower():
            passed.append("witness")
        else:
            failed.append("witness")
        
        score = len(passed) / len(self.DHARMIC_GATES)
        return {"score": score, "passed": passed, "failed": failed}
    
    def _evaluate_elegance(self, component_path: str) -> Dict[str, Any]:
        """Evaluate code elegance."""
        try:
            component_full_path = self.project_root / component_path
            if not component_full_path.exists():
                return {"score": 0.5, "note": "File not found"}
            
            content = component_full_path.read_text()
            
            # Metrics
            lines = content.split("\n")
            total_lines = len(lines)
            blank_lines = sum(1 for l in lines if not l.strip())
            comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
            
            # Parse AST for complexity
            try:
                tree = ast.parse(content)
                num_functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
                num_classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            except:
                num_functions = 0
                num_classes = 0
            
            # Score components
            doc_ratio = comment_lines / max(total_lines, 1)
            modularity = min(num_functions / 10, 1.0)  # Cap at 10 functions
            
            # Combined score
            score = (doc_ratio * 0.3) + (modularity * 0.4) + 0.3  # Base 0.3
            score = min(score, 1.0)
            
            return {
                "score": score,
                "lines": total_lines,
                "functions": num_functions,
                "classes": num_classes,
                "doc_ratio": doc_ratio,
            }
            
        except Exception as e:
            return {"score": 0.5, "error": str(e)}
    
    def _evaluate_safety(self, component_path: str, diff: str) -> Dict[str, Any]:
        """Evaluate safety of changes."""
        dangerous_patterns = [
            "os.system",
            "subprocess.run",
            "eval(",
            "exec(",
            "open(",  # Only concerning if writing
            "__import__",
            "pickle.loads",
        ]
        
        concerns = []
        
        for pattern in dangerous_patterns:
            if pattern in diff:
                concerns.append(f"Found {pattern} in diff")
        
        if not concerns:
            return {"score": 1.0, "concerns": []}
        elif len(concerns) <= 2:
            return {"score": 0.7, "concerns": concerns}
        else:
            return {"score": 0.3, "concerns": concerns}


def evaluate_component(component_path: str) -> EvaluationResult:
    """Convenience function to evaluate a component."""
    evaluator = FitnessEvaluator()
    return evaluator.evaluate(component_path)


if __name__ == "__main__":
    # Test fitness evaluation
    evaluator = FitnessEvaluator()
    
    # Evaluate this file
    result = evaluator.evaluate("src/dgm/fitness.py", run_tests=False)
    
    print(f"Fitness Score: {result.score.total():.2f}")
    print(f"  Correctness: {result.score.correctness:.2f}")
    print(f"  Dharmic: {result.score.dharmic_alignment:.2f}")
    print(f"  Elegance: {result.score.elegance:.2f}")
    print(f"  Safety: {result.score.safety:.2f}")
    print(f"\nGates passed: {result.gates_passed}")
    print(f"Gates failed: {result.gates_failed}")
