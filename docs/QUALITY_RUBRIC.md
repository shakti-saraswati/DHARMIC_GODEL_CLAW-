# Quality Rubric (Top-50 Calibrated)

This rubric is calibrated against known high-quality systems and codebases
referenced in `docs/TOP_50_QUALITY_REFERENCES.md`.

## Quality Rubric

Weights (total = 100%):
- **Correctness** (35%)
  - Type coverage
  - Assertions and invariants
  - Tests + properties (unit/integration/property)
- **Elegance** (25%)
  - Compression/complexity signals
  - Cyclomatic complexity
  - Compositionality and clarity
- **Longevity** (20%)
  - API stability
  - Documentation quality
  - Backward compatibility
- **Security** (20%)
  - Static analysis (bandit)
  - Known CVEs (pip-audit)
  - Secrets scanning

## Calibration Notes

This rubric is intentionally aligned to “timeless” quality patterns:
- Correctness dominates (35%) because reliability is the highest-order constraint.
- Elegance emphasizes clarity and compositionality over surface-level minimalism.
- Longevity values stable APIs and strong docs to keep systems maintainable over years.
- Security is weighted on par with longevity due to real-world operational risk.

## How This Is Used

This rubric is enforced in the gate pipeline (SATYA gate requires this file).
When updating the rubric:
1. Update the weights and definitions here.
2. Update any evaluators that reference these weights.
3. Record changes in the residual stream.
