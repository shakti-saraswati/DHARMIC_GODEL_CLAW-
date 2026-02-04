# CUDA Compatibility Notes

## Supported Toolchain
- CUDA Toolkit: 11.8+ (preferred 12.x)
- Compiler: nvcc + gcc/clang compatible with toolkit
- Python: 3.10+ for Python bindings

## Runtime Checks
- Always guard CUDA-specific paths with device availability checks.
- Fail gracefully to CPU fallback when CUDA is unavailable.

## Build Flags (Typical)
- `-lineinfo` for profiling
- `-O3` for optimized builds
- `-gencode` set to required compute capabilities

## Version Matrix
- CUDA 11.8: baseline compatibility
- CUDA 12.x: preferred for newer GPUs

## Known Constraints
- Avoid undefined behavior in kernels; prefer explicit bounds checks.
- Keep numerical tolerance documented if using mixed precision.

