# Benchmarks

## CPU Baseline
1. Run benchmarks:
   `pytest tests/benchmarks/ --benchmark-json=benchmark.json`
2. Update baseline:
   `python -m swarm.performance_baseline --update`

## CUDA Baseline
- Create a GPU benchmark suite in `tests/benchmarks/`.
- Record baseline in `benchmarks/cuda_baseline.json`.

Notes:
- CI may not have a GPU. CUDA baselines are required for accelerator changes.
- Performance regressions > 10% fail the performance gate.

