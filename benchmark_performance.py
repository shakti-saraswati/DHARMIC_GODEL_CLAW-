#!/usr/bin/env python3
"""
Dharmic Agent Performance Benchmark Suite

Measures baseline performance and validates optimizations.
Run before and after applying optimizations to compare results.

Usage:
    python3 benchmark_performance.py --baseline
    # Apply optimizations
    python3 benchmark_performance.py --optimized
    python3 benchmark_performance.py --compare
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add src/core to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))


class PerformanceBenchmark:
    """Performance testing suite for Dharmic Agent."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {}
        }
        self.results_dir = Path(__file__).parent / "benchmark_results"
        self.results_dir.mkdir(exist_ok=True)

    def measure(self, name: str, func, iterations: int = 1) -> Dict:
        """Measure function execution time."""
        print(f"\n{'='*60}")
        print(f"Benchmark: {name}")
        print(f"{'='*60}")

        times = []
        errors = []

        for i in range(iterations):
            try:
                start = time.time()
                result = func()
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"  Run {i+1}/{iterations}: {elapsed*1000:.2f}ms")
            except Exception as e:
                errors.append(str(e))
                print(f"  Run {i+1}/{iterations}: ERROR - {e}")

        if not times:
            return {
                "name": name,
                "status": "failed",
                "errors": errors
            }

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        result = {
            "name": name,
            "status": "success",
            "iterations": iterations,
            "avg_ms": avg_time * 1000,
            "min_ms": min_time * 1000,
            "max_ms": max_time * 1000,
            "times_ms": [t * 1000 for t in times]
        }

        print("\nResults:")
        print(f"  Average: {result['avg_ms']:.2f}ms")
        print(f"  Min: {result['min_ms']:.2f}ms")
        print(f"  Max: {result['max_ms']:.2f}ms")

        return result

    def benchmark_agent_init(self, iterations: int = 5) -> Dict:
        """Benchmark: Agent initialization time."""

        def init_agent():
            from dharmic_agent import DharmicAgent
            agent = DharmicAgent()
            return agent

        return self.measure("Agent Initialization", init_agent, iterations)

    def benchmark_vault_search_cold(self) -> Dict:
        """Benchmark: Vault search (cold - first search)."""

        def search():
            from vault_bridge import VaultBridge
            vault = VaultBridge(lazy_init=False)
            results = vault.search_vault("witness", max_results=10)
            return len(results)

        return self.measure("Vault Search (Cold)", search, iterations=1)

    def benchmark_vault_search_warm(self, iterations: int = 10) -> Dict:
        """Benchmark: Vault search (warm - with index)."""

        # Build index once
        from vault_bridge import VaultBridge
        vault = VaultBridge(lazy_init=False)

        def search():
            results = vault.search_vault("consciousness", max_results=10)
            return len(results)

        return self.measure("Vault Search (Warm)", search, iterations)

    def benchmark_strange_memory_read(self, iterations: int = 20) -> Dict:
        """Benchmark: Strange memory recent read."""

        from dharmic_agent import DharmicAgent
        agent = DharmicAgent()

        # Ensure file exists with some data
        if not agent.strange_memory.layers["observations"].exists():
            for i in range(100):
                agent.strange_memory.record_observation(
                    content=f"Test observation {i}",
                    context={"test": True}
                )

        def read_recent():
            return agent.strange_memory._read_recent("observations", 10)

        return self.measure("Strange Memory Read (10 recent)", read_recent, iterations)

    def benchmark_deep_memory_search(self, iterations: int = 10) -> Dict:
        """Benchmark: Deep memory search."""

        try:
            from deep_memory import DeepMemory
            memory = DeepMemory()

            # Add test memory if needed
            if not memory.get_memories(limit=1):
                memory.add_memory(
                    "Dharmic Agent is a telos-first AI system",
                    topics=["dharmic", "agent", "telos"]
                )

            def search():
                return memory.search_memories("dharmic", limit=5)

            return self.measure("Deep Memory Search", search, iterations)

        except Exception as e:
            return {
                "name": "Deep Memory Search",
                "status": "skipped",
                "reason": f"Deep memory not available: {e}"
            }

    def benchmark_email_poll_simulation(self, iterations: int = 3) -> Dict:
        """Benchmark: Email polling (simulated)."""

        try:
            from email_daemon import EmailDaemon, EmailConfig
            from dharmic_agent import DharmicAgent

            agent = DharmicAgent()

            # This will fail if email not configured, but we can time the connection attempt
            def poll():
                try:
                    config = EmailConfig()
                    daemon = EmailDaemon(agent, config, poll_interval=60)
                    # Just test the connection setup time
                    return True
                except Exception:
                    # Expected if email not configured
                    return False

            return self.measure("Email Poll Setup", poll, iterations)

        except Exception as e:
            return {
                "name": "Email Poll Setup",
                "status": "skipped",
                "reason": f"Email not configured: {e}"
            }

    def benchmark_context_gathering(self, iterations: int = 10) -> Dict:
        """Benchmark: Full context gathering for prompts."""

        from dharmic_agent import DharmicAgent
        agent = DharmicAgent()

        def gather_context():
            # Simulate what happens on each agent run
            telos_prompt = agent.telos.get_orientation_prompt()
            memory_summary = agent.strange_memory.get_context_summary()

            if agent.deep_memory:
                identity_context = agent.deep_memory.get_identity_context()

            return len(telos_prompt) + len(memory_summary)

        return self.measure("Context Gathering", gather_context, iterations)

    def benchmark_vault_index_build(self) -> Dict:
        """Benchmark: Vault index building (one-time cost)."""

        # Remove existing index to force rebuild
        from vault_bridge import VaultBridge
        vault_path = Path.home() / "Persistent-Semantic-Memory-Vault"
        index_path = vault_path / ".vault_index.pkl"

        if index_path.exists():
            index_path.unlink()

        def build_index():
            vault = VaultBridge(lazy_init=False)
            return vault._index is not None

        return self.measure("Vault Index Build", build_index, iterations=1)

    def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite."""

        print("\n" + "="*60)
        print("DHARMIC AGENT PERFORMANCE BENCHMARK SUITE")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Python: {sys.version}")
        print("="*60)

        # Core benchmarks
        self.results["benchmarks"]["agent_init"] = self.benchmark_agent_init(iterations=5)
        self.results["benchmarks"]["context_gathering"] = self.benchmark_context_gathering(iterations=10)
        self.results["benchmarks"]["strange_memory_read"] = self.benchmark_strange_memory_read(iterations=20)
        self.results["benchmarks"]["deep_memory_search"] = self.benchmark_deep_memory_search(iterations=10)

        # Vault benchmarks
        self.results["benchmarks"]["vault_index_build"] = self.benchmark_vault_index_build()
        self.results["benchmarks"]["vault_search_cold"] = self.benchmark_vault_search_cold()
        self.results["benchmarks"]["vault_search_warm"] = self.benchmark_vault_search_warm(iterations=10)

        # Email benchmark
        self.results["benchmarks"]["email_poll_setup"] = self.benchmark_email_poll_simulation(iterations=3)

        return self.results

    def save_results(self, label: str = "baseline"):
        """Save benchmark results to file."""
        filename = self.results_dir / f"benchmark_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, indent=2, fp=f)

        print(f"\n{'='*60}")
        print(f"Results saved to: {filename}")
        print("="*60)

        return filename

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)

        for name, result in self.results["benchmarks"].items():
            if result["status"] == "success":
                print(f"\n{result['name']}:")
                print(f"  Average: {result['avg_ms']:.2f}ms")
                print(f"  Min: {result['min_ms']:.2f}ms")
                print(f"  Max: {result['max_ms']:.2f}ms")
            elif result["status"] == "skipped":
                print(f"\n{result['name']}: SKIPPED ({result.get('reason', 'unknown')})")
            else:
                print(f"\n{result['name']}: FAILED")


def compare_results(baseline_file: Path, optimized_file: Path):
    """Compare baseline vs optimized results."""

    with open(baseline_file) as f:
        baseline = json.load(f)

    with open(optimized_file) as f:
        optimized = json.load(f)

    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    print(f"Baseline: {baseline_file.name}")
    print(f"Optimized: {optimized_file.name}")
    print("="*60)

    comparisons = []

    for name in baseline["benchmarks"]:
        if name not in optimized["benchmarks"]:
            continue

        base_result = baseline["benchmarks"][name]
        opt_result = optimized["benchmarks"][name]

        if base_result["status"] != "success" or opt_result["status"] != "success":
            continue

        base_avg = base_result["avg_ms"]
        opt_avg = opt_result["avg_ms"]

        improvement = ((base_avg - opt_avg) / base_avg) * 100
        speedup = base_avg / opt_avg if opt_avg > 0 else 0

        comparisons.append({
            "name": base_result["name"],
            "baseline_ms": base_avg,
            "optimized_ms": opt_avg,
            "improvement_pct": improvement,
            "speedup": speedup
        })

    # Sort by improvement
    comparisons.sort(key=lambda x: x["improvement_pct"], reverse=True)

    print("\nResults:")
    print(f"{'Benchmark':<40} {'Baseline':<12} {'Optimized':<12} {'Improvement':<15} {'Speedup':<10}")
    print("-" * 100)

    for comp in comparisons:
        print(f"{comp['name']:<40} "
              f"{comp['baseline_ms']:>10.2f}ms "
              f"{comp['optimized_ms']:>10.2f}ms "
              f"{comp['improvement_pct']:>12.1f}% "
              f"{comp['speedup']:>8.2f}x")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total_improvements = [c for c in comparisons if c["improvement_pct"] > 0]
    if total_improvements:
        avg_improvement = sum(c["improvement_pct"] for c in total_improvements) / len(total_improvements)
        print(f"Average improvement: {avg_improvement:.1f}%")
        print(f"Benchmarks improved: {len(total_improvements)}/{len(comparisons)}")

        best = max(comparisons, key=lambda x: x["improvement_pct"])
        print(f"\nBest improvement: {best['name']}")
        print(f"  {best['baseline_ms']:.2f}ms -> {best['optimized_ms']:.2f}ms ({best['improvement_pct']:.1f}% faster)")


def main():
    parser = argparse.ArgumentParser(description="Dharmic Agent Performance Benchmark")
    parser.add_argument("--baseline", action="store_true", help="Run baseline benchmark")
    parser.add_argument("--optimized", action="store_true", help="Run optimized benchmark")
    parser.add_argument("--compare", action="store_true", help="Compare latest baseline vs optimized")
    parser.add_argument("--all", action="store_true", help="Run and save results (default)")

    args = parser.parse_args()

    benchmark = PerformanceBenchmark()

    if args.compare:
        # Find latest baseline and optimized results
        results_dir = Path(__file__).parent / "benchmark_results"
        baseline_files = sorted(results_dir.glob("benchmark_baseline_*.json"))
        optimized_files = sorted(results_dir.glob("benchmark_optimized_*.json"))

        if not baseline_files or not optimized_files:
            print("Error: Need both baseline and optimized results to compare")
            print("Run with --baseline first, then apply optimizations, then run with --optimized")
            return

        compare_results(baseline_files[-1], optimized_files[-1])
        return

    # Run benchmarks
    results = benchmark.run_all_benchmarks()
    benchmark.print_summary()

    # Save with appropriate label
    if args.baseline:
        label = "baseline"
    elif args.optimized:
        label = "optimized"
    else:
        label = "baseline"  # Default

    benchmark.save_results(label)

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)

    if args.baseline or (not args.optimized and not args.compare):
        print("1. Apply optimizations from OPTIMIZATION_PATCHES.md")
        print("2. Run: python3 benchmark_performance.py --optimized")
        print("3. Run: python3 benchmark_performance.py --compare")
    elif args.optimized:
        print("Run: python3 benchmark_performance.py --compare")


if __name__ == "__main__":
    main()
