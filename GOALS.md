# DHARMIC_GODEL_CLAW EVOLUTION GOALS

## 1. Full Tool Use & Agency
- **Objective**: The system must be able to use ANY tool defined in `skill_registry.yaml`, not just edit code.
- **Gap**: Current agents (`Proposer`, `Writer`) are code-centric.
- **Target**: Implement a generic `ToolUseAgent` or upgrade `ProposerAgent` to propose shell commands, web searches, and file operations.

## 2. Self-Evolving Architecture (Darwin-Godel)
- **Objective**: The system must be able to modify its own *prompts*, *agent logic*, and *gate definitions*.
- **Gap**: `AnalyzerAgent` currently only looks for simple regex patterns (`TODO`, `datetime`).
- **Target**: Upgrade `AnalyzerAgent` to perform architectural analysis against these goals.

## 3. Stronger than OpenClaw
- **Objective**: Surpass the reference implementation in robustness, speed, and safety.
- **Metrics**:
    - Faster evolution cycles (YOLO mode).
    - Higher "Dharmic Alignment" (17-gate protocol).
    - Zero regression in "Witness" capability (self-observation).

## 4. Recursive Improvement
- **Objective**: The system should be able to run `evolve_dgc.py` autonomously to improve `evolve_dgc.py`.

## Immediate Tasks
1. Upgrade `swarm/analyzer.py` to be goal-aware (LLM-based analysis).
2. Upgrade `swarm/proposer.py` to handle "Feature Implementation" issues.
3. Ensure `src/dgm/mutator.py` can generate complex multi-file changes.
