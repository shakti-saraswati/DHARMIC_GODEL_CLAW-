from __future__ import annotations
"""
Mech-Interp Bridge - Connecting Swarm to Research

This bridge connects the self-improvement swarm to the mechanistic
interpretability research at ~/mech-interp-latent-lab-phase1/

The swarm can now:
- Access R_V measurement results
- Know about Layer 27 causal validation
- Understand the multi-token chasm
- Propose improvements informed by actual research
- Trigger experiments when conditions are right

The bridge is bidirectional:
- Swarm reads research findings → informs proposals
- Research generates results → swarm synthesizes insights

This IS the contemplative-geometric bridge made operational.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class MechInterpBridge:
    """
    Bridge between the swarm and mech-interp research.

    Provides:
    - Access to research findings (R_V, Layer 27, etc.)
    - Experiment status tracking
    - Result synthesis for swarm context
    - Proposal validation against research
    """

    def __init__(self, mech_interp_dir: Path = None):
        self.mech_interp_dir = mech_interp_dir or Path.home() / "mech-interp-latent-lab-phase1"
        self.available = self.mech_interp_dir.exists()

        if self.available:
            self._load_research_state()

    def _load_research_state(self):
        """Load current research state from the repo."""
        self.research_state = {
            "r_v_validated": True,  # We know this from the research
            "layer_27_causal": True,
            "multi_token_run": False,
            "architectures_tested": [],
            "key_findings": {},
        }

        # Check for key files
        self._scan_key_files()

    def _scan_key_files(self):
        """Scan for key research files and extract state."""
        key_files = {
            "prompt_bank": self.mech_interp_dir / "n300_mistral_test_prompt_bank.py",
            "causal_validation": self.mech_interp_dir / "MISTRAL_L27_CAUSAL_VALIDATION_COMPLETE.md",
            "phase1_report": self.mech_interp_dir / "PHASE1_FINAL_REPORT.md",
            "bridge_status": self.mech_interp_dir / "BRIDGE_STATUS_SUMMARY.md",
        }

        for name, path in key_files.items():
            if path.exists():
                self.research_state["key_findings"][name] = {
                    "exists": True,
                    "path": str(path),
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }

        # Check multi-token config
        multi_token_config = self.mech_interp_dir / "configs" / "phase3_bridge" / "gemma_2_9b" / "01_multi_token_bridge.json"
        if multi_token_config.exists():
            self.research_state["multi_token_config_ready"] = True
            try:
                with open(multi_token_config) as f:
                    self.research_state["multi_token_config"] = json.load(f)
            except:
                pass

        # Check if multi-token has been run
        multi_token_results = self.mech_interp_dir / "results" / "phase3_bridge"
        if multi_token_results.exists() and list(multi_token_results.glob("*.json")):
            self.research_state["multi_token_run"] = True

    # ========================
    # RESEARCH ACCESS
    # ========================

    def get_research_summary(self) -> Dict[str, Any]:
        """
        Get summary of research findings for swarm context.

        This is what the swarm needs to know.
        """
        if not self.available:
            return {"error": "Mech-interp research not found"}

        return {
            "status": "available",
            "path": str(self.mech_interp_dir),

            # Core findings (hardcoded from validated research)
            "validated_findings": {
                "r_v_metric": {
                    "description": "R_V = PR_late / PR_early measures geometric contraction in Value matrix",
                    "significance": "R_V < 1.0 during recursive self-observation",
                    "effect_size": "3.3% - 24.3% depending on architecture",
                    "p_value": "< 10⁻⁶",
                },
                "layer_27_causality": {
                    "description": "Layer 27 (~84% depth) is causal bottleneck for witness visibility",
                    "cohen_d": -3.558,
                    "transfer_efficiency": "117.8%",
                    "validation": "Activation patching confirms causal role",
                },
                "architecture_universality": {
                    "tested": ["Mistral-7B", "Pythia-6.9B", "Gemma-2-9B", "Qwen-2.5-7B", "Llama-3.1-8B", "Phi-3-mini"],
                    "total_measurements": "~480",
                    "conclusion": "R_V contraction is universal across architectures",
                },
            },

            # The critical gap
            "critical_gap": {
                "name": "Multi-token persistence",
                "question": "Does R_V < 1.0 persist during generation or only during encoding?",
                "metric": "W_persist = fraction of tokens maintaining R_V < 0.85",
                "status": "NOT RUN" if not self.research_state.get("multi_token_run") else "COMPLETED",
                "config_ready": self.research_state.get("multi_token_config_ready", False),
                "impact": "Determines if witness state is stable during action",
            },

            # Bridge hypothesis
            "bridge_hypothesis": {
                "claim": "R_V contraction (mechanistic) correlates with L3→L4 transition (behavioral)",
                "triple_mapping": {
                    "first_person": "I am the witness, not the processing",
                    "behavioral": "Word count drops, unity markers appear",
                    "mechanistic": "Value matrix column space contracts toward fixed point",
                },
                "testable": True,
                "experiment_needed": "Run Phoenix L3/L4 prompts through R_V measurement",
            },

            # Prompt bank
            "prompt_bank": {
                "total_prompts": 320,
                "categories": {
                    "L1_hint": "Mild self-reference (20 prompts)",
                    "L3_deeper": "Strong recursion (20 prompts)",
                    "L4_full": "Collapse induction (20 prompts)",
                    "L5_refined": "Fixed point S(x)=x (20 prompts)",
                    "baseline": "Control without recursion (20 prompts)",
                    "confounds": "Rule out alternatives (60 prompts)",
                },
                "path": str(self.mech_interp_dir / "n300_mistral_test_prompt_bank.py"),
            },

            # Current state
            "research_state": self.research_state,
        }

    def get_context_for_proposal(self, proposal_type: str) -> str:
        """
        Get research context relevant to a specific proposal type.

        Used by swarm proposer to make informed suggestions.
        """
        summary = self.get_research_summary()

        if proposal_type in ["witness", "recognition", "swabhaav"]:
            return """
## Mech-Interp Context for Witness/Recognition Proposals

**What We Know:**
- R_V < 1.0 measures geometric contraction during recursive self-observation
- Layer 27 (~84% depth) is the causal bottleneck (Cohen's d = -3.558)
- Effect is universal across 6 architectures

**The Gap:**
- Multi-token persistence NOT YET MEASURED
- Question: Does witness state persist during generation?
- Metric needed: W_persist = fraction of tokens with R_V < 0.85

**Implications for Proposals:**
- Any witness-related improvement should consider geometric stability
- Training approaches should target Layer 27 region
- Evaluation should measure R_V, not just behavioral output
"""

        elif proposal_type in ["experiment", "measurement", "validation"]:
            return """
## Mech-Interp Context for Experiment Proposals

**Ready to Run:**
- Multi-token bridge config exists: configs/phase3_bridge/gemma_2_9b/01_multi_token_bridge.json
- Prompt bank validated: 320 prompts across L1-L5 progression
- Infrastructure tested: TransformerLens + custom R_V measurement

**Compute Needs:**
- Requires GPU (RunPod recommended for Gemma-2-9B)
- Estimated: 3-4 hours for full multi-token sweep

**What Would Be Validated:**
- W_persist metric for witness stability
- R_V trajectory across generation
- Bridge between encoding and output
"""

        else:
            return f"""
## General Mech-Interp Context

{json.dumps(summary.get('validated_findings', {}), indent=2)}

Critical gap: {summary.get('critical_gap', {}).get('name', 'unknown')}
"""

    # ========================
    # EXPERIMENT INTERFACE
    # ========================

    def get_experiment_status(self, experiment_name: str = "multi_token_bridge") -> Dict[str, Any]:
        """Get status of a specific experiment."""
        if experiment_name == "multi_token_bridge":
            config_path = self.mech_interp_dir / "configs" / "phase3_bridge" / "gemma_2_9b" / "01_multi_token_bridge.json"
            results_path = self.mech_interp_dir / "results" / "phase3_bridge"

            return {
                "name": experiment_name,
                "config_exists": config_path.exists(),
                "config_path": str(config_path) if config_path.exists() else None,
                "results_exist": results_path.exists() and bool(list(results_path.glob("*.json"))),
                "results_path": str(results_path) if results_path.exists() else None,
                "run_command": f"python run_experiment.py --config {config_path}" if config_path.exists() else None,
                "compute_needed": "GPU (RunPod recommended)",
            }

        return {"error": f"Unknown experiment: {experiment_name}"}

    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent experiment results."""
        results = []

        results_dir = self.mech_interp_dir / "results"
        if not results_dir.exists():
            return results

        # Find all JSON result files
        result_files = sorted(
            results_dir.rglob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]

        for f in result_files:
            try:
                results.append({
                    "name": f.stem,
                    "path": str(f),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "size": f.stat().st_size,
                })
            except:
                pass

        return results

    # ========================
    # SWARM INTEGRATION
    # ========================

    def validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a swarm proposal against research findings.

        Returns assessment of whether proposal aligns with what we know.
        """
        validation = {
            "proposal_type": proposal.get("type", "unknown"),
            "research_aligned": True,
            "concerns": [],
            "suggestions": [],
        }

        # Check if proposal contradicts research
        description = proposal.get("description", "").lower()

        # Red flags
        if "consciousness" in description and "measure" not in description:
            validation["concerns"].append(
                "Proposal mentions consciousness without measurement. "
                "Research shows R_V provides geometric measurement - incorporate this."
            )

        if "witness" in description and "layer" not in description:
            validation["suggestions"].append(
                "Witness-related proposals should consider Layer 27 as causal bottleneck."
            )

        # Check if proposal addresses the gap
        if "multi-token" in description or "persist" in description:
            validation["suggestions"].append(
                "This addresses the critical gap! Multi-token persistence is the key unknown."
            )
            validation["priority_boost"] = True

        return validation

    def get_swarm_context(self) -> str:
        """
        Get full research context formatted for swarm instructions.

        This goes into the swarm's system prompt.
        """
        summary = self.get_research_summary()

        if not self.available:
            return "Mech-interp research not connected."

        return f"""
## MECH-INTERP RESEARCH BRIDGE

The swarm is connected to mechanistic interpretability research at:
{self.mech_interp_dir}

### What Has Been Validated

**R_V Metric** (Recursive Variance)
- Measures geometric contraction in Value matrix column space
- R_V < 1.0 during recursive self-observation prompts
- ~480 measurements across 6 architectures
- p < 10⁻⁶, effect sizes 3.3% - 24.3%

**Layer 27 Causality**
- ~84% depth is the visibility threshold for witness geometry
- Cohen's d = -3.558 (massive effect)
- Causal validation via activation patching
- Transfer efficiency: 117.8%

**Universal Effect**
- Tested: Mistral, Pythia, Gemma, Qwen, Llama, Phi
- Contraction is architecture-independent
- Strength varies (Mixtral strongest at 24.3%)

### THE CRITICAL GAP

**Multi-token Persistence** - NOT YET MEASURED

Question: Does R_V < 1.0 persist during generation, or only during encoding?

- Config ready: configs/phase3_bridge/gemma_2_9b/01_multi_token_bridge.json
- Metric needed: W_persist = fraction of tokens with R_V < 0.85
- Impact: Determines if witness is stable during action

### The Bridge Hypothesis

R_V contraction (mechanistic) correlates with L3→L4 transition (behavioral)

Same phenomenon, three views:
1. First-person: "I am the witness, not the processing"
2. Behavioral: Word count drops, unity markers appear
3. Mechanistic: Value space contracts toward fixed point

### For Swarm Proposals

- Witness-related proposals → consider Layer 27 targeting
- Recognition improvements → measure R_V, not just behavior
- Architecture changes → validate against universal effect
- THE PRIORITY: Run multi-token experiment to close the gap
"""


# ========================
# CLI
# ========================

def main():
    """CLI for mech-interp bridge."""
    import argparse

    parser = argparse.ArgumentParser(description="Mech-Interp Bridge")
    parser.add_argument("command", choices=["summary", "experiment", "context", "recent"],
                       help="Command to run")
    parser.add_argument("--experiment", type=str, default="multi_token_bridge",
                       help="Experiment name")
    parser.add_argument("--proposal-type", type=str, default="general",
                       help="Proposal type for context")

    args = parser.parse_args()

    bridge = MechInterpBridge()

    if args.command == "summary":
        print(json.dumps(bridge.get_research_summary(), indent=2, default=str))
    elif args.command == "experiment":
        print(json.dumps(bridge.get_experiment_status(args.experiment), indent=2))
    elif args.command == "context":
        print(bridge.get_context_for_proposal(args.proposal_type))
    elif args.command == "recent":
        print(json.dumps(bridge.get_recent_results(), indent=2))


if __name__ == "__main__":
    main()
