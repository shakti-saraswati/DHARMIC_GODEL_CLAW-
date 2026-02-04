# Hardware Targets

This document defines the minimum and preferred accelerator targets.

## Primary Targets
- NVIDIA CUDA (compute capability >= 7.5)
- CPU fallback (x86_64, macOS/Apple Silicon)

## Preferred GPUs
- NVIDIA A100 (80GB)
- NVIDIA H100 (80GB)
- NVIDIA RTX 4090 (24GB)
- NVIDIA L4 / L40S

## Minimum Requirements
- CUDA runtime >= 11.8
- Driver compatible with selected runtime
- 16GB GPU memory for baseline tests

## Build Matrix
- Linux x86_64 (primary)
- macOS (CPU-only fallback)
- Optional: Windows (CPU-only fallback)

## Notes
- If a GPU target is not available in CI, the CPU path must still pass.
- All GPU-specific code must be guarded by capability checks.

