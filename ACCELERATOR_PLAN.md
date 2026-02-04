# Accelerator Plan (CUDA / HPC)

This plan defines how accelerator code is designed, validated, and evolved.

## Goals
- Keep CPU fallback correct and fast.
- Make GPU acceleration predictable, testable, and benchmarked.
- Avoid silent performance regressions or device-specific bugs.

## Scope
- CUDA kernels, CUDA-aware Python, HIP/ROCm parity where possible.
- Build and runtime compatibility notes in `CUDA_COMPAT.md`.

## Required Artifacts
- `ACCELERATOR_PLAN.md` (this file)
- `HARDWARE_TARGETS.md`
- `CUDA_COMPAT.md`
- `benchmarks/cuda_baseline.json`

## Development Rules
1. Always provide a CPU fallback path.
2. Performance claims must be benchmarked.
3. Kernel changes require a reproducible benchmark case.
4. Unsafe optimizations require an explicit hazard entry in `HAZARDS.md`.

## Benchmark Strategy
- Use `pytest tests/benchmarks/ --benchmark-json=benchmark.json`.
- For GPU, include a dedicated benchmark file and record results in
  `benchmarks/cuda_baseline.json`.
- Track regression thresholds in `swarm/gates.yaml`.

## Rollback Strategy
- Each accelerator change must include a rollback note in `ROLLBACK.md`.
- If a regression is detected, revert to the last known baseline.

## Ownership
- Owner: dhyana
- Reviewers: CODE_GUARDIAN + human approver

