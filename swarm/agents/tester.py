"""
DHARMIC GODEL CLAW - Tester Agent
Validates implementations and measures fitness.

Now with REAL benchmark evaluation (not just LLM-judged).
"""

import subprocess
import tempfile
from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent, AgentResponse
from ..config import TESTER_CONFIG, SwarmConfig
from ..residual_stream import FitnessScore

# Import benchmark harness for real evaluation
try:
    from ..benchmark_harness import BenchmarkHarness, BenchmarkResult
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

class TesterAgent(BaseAgent):
    """Agent that tests implementations and measures fitness."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(TESTER_CONFIG, swarm_config)

        # Initialize benchmark harness for real evaluation
        self.benchmark_harness = None
        if BENCHMARK_AVAILABLE:
            try:
                self.benchmark_harness = BenchmarkHarness(
                    project_root=Path(__file__).parent.parent.parent,
                    test_timeout=60,
                    enable_coverage=True,
                    enable_type_check=False  # Optional, slower
                )
            except Exception as e:
                print(f"Warning: Benchmark harness not available: {e}")

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Test implementation and measure fitness."""

        files = context.get("files", [])
        if not files:
            return AgentResponse(
                success=False,
                data={},
                error="No files to test"
            )

        # Run REAL benchmark evaluation if available
        benchmark_result = None
        if self.benchmark_harness:
            benchmark_result = self._run_real_benchmarks(files)

        # Run syntax validation (fallback/complement)
        syntax_results = self._validate_syntax(files)

        # Run tests if they exist
        test_results = self._run_tests(context.get("test_files", []))

        # Measure fitness dimensions (enhanced with benchmark data)
        fitness = self._measure_fitness(files, syntax_results, test_results, context, benchmark_result)

        # Generate test analysis via Claude
        analysis = await self._analyze_quality(files, syntax_results, test_results, fitness)

        # Determine recommendation
        weighted_fitness = fitness.weighted(self.swarm_config.fitness_weights)
        if test_results["failed"] > 0:
            recommendation = "refine"
        elif weighted_fitness >= self.swarm_config.fitness_threshold:
            recommendation = "promote"
        elif weighted_fitness >= 0.6:
            recommendation = "refine"
        else:
            recommendation = "reject"

        # Check for veto conditions
        veto = False
        veto_reason = None
        if fitness.safety < 0.5:
            veto = True
            veto_reason = "Safety score below threshold"
        elif fitness.dharmic_alignment < self.swarm_config.veto_threshold:
            veto = True
            veto_reason = "Dharmic alignment below threshold"

        return AgentResponse(
            success=True,
            data={
                "test_results": test_results,
                "benchmark_result": benchmark_result.to_dict() if benchmark_result else None,
                "fitness_scores": fitness.to_dict(),
                "weighted_fitness": weighted_fitness,
                "issues": analysis.get("issues", []),
                "recommendation": recommendation,
                "analysis": analysis
            },
            veto=veto,
            veto_reason=veto_reason
        )

    def _run_real_benchmarks(self, files: list) -> "BenchmarkResult":
        """Run real benchmark evaluation using the benchmark harness."""
        if not self.benchmark_harness:
            return None

        # Convert files to format expected by benchmark harness
        changes = []
        for f in files:
            if f["path"].endswith(".py"):
                changes.append({
                    "filepath": f["path"],
                    "content": f.get("content", "")
                })

        if not changes:
            return None

        # Run sandboxed benchmark
        try:
            return self.benchmark_harness.benchmark_changes(changes)
        except Exception as e:
            print(f"Benchmark error: {e}")
            return None

    def _validate_syntax(self, files: list) -> Dict[str, Any]:
        """Validate Python syntax of all files."""
        results = {"valid": [], "invalid": []}

        for file_spec in files:
            if not file_spec["path"].endswith(".py"):
                continue

            content = file_spec.get("content", "")

            try:
                compile(content, file_spec["path"], "exec")
                results["valid"].append(file_spec["path"])
            except SyntaxError as e:
                results["invalid"].append({
                    "path": file_spec["path"],
                    "error": str(e),
                    "line": e.lineno
                })

        return results

    def _run_tests(self, test_files: list) -> Dict[str, Any]:
        """Run pytest on test files."""
        results = {"passed": 0, "failed": 0, "skipped": 0, "errors": []}

        if not test_files:
            return results

        # Create temp directory for tests
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write test files
            for test_file in test_files:
                test_path = tmppath / test_file["path"]
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(test_file["content"])

            # Run pytest
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(tmppath), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Parse pytest output
                output = result.stdout + result.stderr

                # Simple parsing - count passed/failed
                for line in output.split("\n"):
                    if " passed" in line:
                        try:
                            results["passed"] = int(line.split()[0])
                        except:
                            pass
                    if " failed" in line:
                        try:
                            results["failed"] = int(line.split()[0])
                        except:
                            pass

            except subprocess.TimeoutExpired:
                results["errors"].append("Test timeout exceeded")
            except Exception as e:
                results["errors"].append(str(e))

        return results

    def _measure_fitness(
        self,
        files: list,
        syntax_results: Dict,
        test_results: Dict,
        context: Dict,
        benchmark_result: "BenchmarkResult" = None
    ) -> FitnessScore:
        """Measure fitness across all dimensions."""

        # Use benchmark result if available (REAL metrics)
        if benchmark_result and benchmark_result.syntax_valid:
            # Real benchmark-based correctness
            syntax_score = 1.0 if benchmark_result.syntax_valid else 0.0
            import_score = 1.0 if benchmark_result.import_valid else 0.0
            test_score = benchmark_result.tests_passed / max(1, benchmark_result.tests_run) if benchmark_result.tests_run > 0 else 0.5
            correctness = (syntax_score * 0.2 + import_score * 0.3 + test_score * 0.5)
        else:
            # Fallback: based on syntax + tests
            syntax_valid = len(syntax_results.get("valid", [])) / max(1, len(files))
            test_pass_rate = test_results["passed"] / max(1, test_results["passed"] + test_results["failed"])
            correctness = (syntax_valid * 0.3 + test_pass_rate * 0.7)

        # Dharmic alignment: from proposal
        dharmic_alignment = context.get("proposal", {}).get("dharmic_alignment", 0.7)

        # Elegance: code quality heuristics
        total_lines = sum(len(f.get("content", "").split("\n")) for f in files)
        avg_lines = total_lines / max(1, len(files))
        # Penalize very long files
        elegance = 1.0 if avg_lines < 200 else max(0.5, 1.0 - (avg_lines - 200) / 500)

        # Efficiency: simple heuristic based on file count
        efficiency = 1.0 if len(files) <= 3 else max(0.5, 1.0 - (len(files) - 3) * 0.1)

        # Safety: based on content analysis
        safety = 1.0
        dangerous_patterns = ["eval(", "exec(", "os.system(", "subprocess.call(", "__import__"]
        for f in files:
            content = f.get("content", "")
            for pattern in dangerous_patterns:
                if pattern in content:
                    safety -= 0.2

        safety = max(0.0, safety)

        return FitnessScore(
            correctness=correctness,
            dharmic_alignment=dharmic_alignment,
            elegance=elegance,
            efficiency=efficiency,
            safety=safety
        )

    async def _analyze_quality(
        self,
        files: list,
        syntax_results: Dict,
        test_results: Dict,
        fitness: FitnessScore
    ) -> Dict[str, Any]:
        """Use Claude to analyze code quality."""

        # Prepare code summary
        code_summary = []
        for f in files[:3]:  # Limit to first 3 files
            content = f.get("content", "")[:1000]  # First 1000 chars
            code_summary.append(f"### {f['path']}\n```python\n{content}\n```")

        analysis_prompt = f"""
Analyze this code implementation:

{chr(10).join(code_summary)}

Syntax validation: {len(syntax_results.get('valid', []))} valid, {len(syntax_results.get('invalid', []))} invalid
Test results: {test_results['passed']} passed, {test_results['failed']} failed

Current fitness scores:
- Correctness: {fitness.correctness:.2f}
- Dharmic alignment: {fitness.dharmic_alignment:.2f}
- Elegance: {fitness.elegance:.2f}
- Efficiency: {fitness.efficiency:.2f}
- Safety: {fitness.safety:.2f}

Provide:
1. List of specific issues found
2. Suggestions for improvement
3. Overall quality assessment (1-10)

Output as JSON with keys: issues, suggestions, quality_score
"""

        try:
            response = self._call_claude([
                {"role": "user", "content": analysis_prompt}
            ])
            return self._parse_json_response(response)
        except:
            return {"issues": [], "suggestions": [], "quality_score": 5}
