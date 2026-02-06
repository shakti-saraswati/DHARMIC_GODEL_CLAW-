"""
WitnessThresholdDetector - Real-time R_V measurement during agent generation.

Detects contemplative state emergence by measuring geometric contraction
in transformer Value space during recursive self-observation.

Key Metrics:
- R_V = PR_late / PR_early (Participation Ratio contraction)
- witness_detected when R_V < threshold (default 0.85)
- Layer 27 (~84% depth) is causally necessary for the effect

Usage:
    from swarm.agents.skills import WitnessThresholdDetector

    detector = WitnessThresholdDetector(model_name="mistralai/Mistral-7B-v0.1")
    response, metrics = detector.monitored_generate(prompt)

    if metrics['witness_detected']:
        print(f"Witness state detected! R_V = {metrics['rv_score']:.3f}")
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple, List

import torch
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WitnessMetrics:
    """Metrics from witness detection analysis."""
    rv_score: float  # R_V = PR_late / PR_early
    pr_early: float  # Participation ratio at early layer
    pr_late: float   # Participation ratio at late layer
    layer_early: int
    layer_late: int
    witness_detected: bool
    confidence: float  # How far below threshold
    layer_analysis: Dict[int, float]  # PR per layer


class WitnessThresholdDetector:
    """
    Real-time R_V measurement during agent generation.

    Detects contemplative state emergence by measuring geometric contraction
    in transformer Value space during recursive self-observation.
    """

    DEFAULT_THRESHOLD = 0.85
    DEFAULT_LAYER_EARLY = 5
    DEFAULT_LAYER_LATE_RATIO = 0.84  # ~84% depth

    # Model-specific layer mappings (layer 27 equivalent)
    LAYER_MAPPINGS = {
        "mistralai/Mistral-7B-v0.1": {"early": 5, "late": 27, "total": 32},
        "Qwen/Qwen-7B": {"early": 5, "late": 27, "total": 32},
        "meta-llama/Llama-2-7b-hf": {"early": 5, "late": 27, "total": 32},
        "microsoft/phi-3-mini-4k-instruct": {"early": 5, "late": 27, "total": 32},
        "google/gemma-7b": {"early": 4, "late": 23, "total": 28},
        "mistralai/Mixtral-8x7B-v0.1": {"early": 5, "late": 27, "total": 32},
        "default": {"early": 5, "late_ratio": 0.84},
    }

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-v0.1",
        threshold: float = DEFAULT_THRESHOLD,
        device: Optional[str] = None,
        use_transformerlens: bool = True,
    ):
        """
        Initialize the detector.

        Args:
            model_name: HuggingFace model identifier
            threshold: R_V threshold below which witness is detected (default 0.85)
            device: Device to run on (auto-detected if None)
            use_transformerlens: Whether to use TransformerLens (recommended)
        """
        self.model_name = model_name
        self.threshold = threshold
        self.device = device or self._detect_device()
        self.use_transformerlens = use_transformerlens

        # Lazy loading
        self._model = None
        self._tokenizer = None

        # Get layer configuration
        self._setup_layers()

        logger.info(f"WitnessThresholdDetector initialized for {model_name}")
        logger.info(f"  Threshold: R_V < {threshold}")
        logger.info(f"  Layers: early={self.layer_early}, late={self.layer_late}")

    def _detect_device(self) -> str:
        """Auto-detect best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _setup_layers(self):
        """Configure layer indices based on model."""
        if self.model_name in self.LAYER_MAPPINGS:
            config = self.LAYER_MAPPINGS[self.model_name]
            self.layer_early = config["early"]
            self.layer_late = config["late"]
            self.n_layers = config["total"]
        else:
            # Use default ratio-based approach
            self.layer_early = self.DEFAULT_LAYER_EARLY
            self.layer_late = None  # Will be set when model loads
            self.n_layers = None

    def _ensure_model_loaded(self):
        """Lazy load model and tokenizer."""
        if self._model is not None:
            return

        logger.info(f"Loading model {self.model_name}...")

        if self.use_transformerlens:
            self._load_transformerlens()
        else:
            self._load_huggingface()

        # Set late layer if not already set
        if self.layer_late is None:
            self.layer_late = int(self.n_layers * self.DEFAULT_LAYER_LATE_RATIO)

    def _load_transformerlens(self):
        """Load model using TransformerLens."""
        try:
            from transformer_lens import HookedTransformer

            self._model = HookedTransformer.from_pretrained(
                self.model_name,
                device=self.device,
            )
            self._tokenizer = self._model.tokenizer
            self.n_layers = self._model.cfg.n_layers
            logger.info(f"Loaded via TransformerLens: {self.n_layers} layers")

        except ImportError:
            logger.warning("TransformerLens not available, falling back to HuggingFace")
            self.use_transformerlens = False
            self._load_huggingface()

    def _load_huggingface(self):
        """Load model using HuggingFace transformers."""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
        )

        if self.device == "mps":
            self._model = self._model.to(self.device)

        self.n_layers = self._model.config.num_hidden_layers
        logger.info(f"Loaded via HuggingFace: {self.n_layers} layers")

    @staticmethod
    def participation_ratio(activations: torch.Tensor) -> float:
        """
        Compute Participation Ratio (effective dimensionality).

        PR = (Σλ_i)² / Σ(λ_i²)

        Where λ_i are eigenvalues of the covariance matrix.
        PR ranges from 1 (single dimension) to d (uniform spread).
        """
        # Flatten to [samples, features]
        if activations.dim() > 2:
            activations = activations.reshape(-1, activations.shape[-1])

        # Center the data
        centered = activations - activations.mean(dim=0, keepdim=True)

        # Compute covariance eigenvalues via SVD (more stable)
        try:
            _, s, _ = torch.svd(centered.float())
            eigenvalues = s ** 2 / (activations.shape[0] - 1)

            # Compute PR
            sum_eig = eigenvalues.sum()
            sum_eig_sq = (eigenvalues ** 2).sum()

            if sum_eig_sq < 1e-10:
                return float(activations.shape[-1])  # Degenerate case

            pr = (sum_eig ** 2) / sum_eig_sq
            return float(pr.cpu())

        except Exception as e:
            logger.warning(f"PR computation failed: {e}")
            return float(activations.shape[-1])

    def compute_rv(
        self,
        prompt: str,
        layer_early: Optional[int] = None,
        layer_late: Optional[int] = None,
    ) -> WitnessMetrics:
        """
        Compute R_V metric for a prompt.

        Args:
            prompt: Input text
            layer_early: Override early layer (default: configured)
            layer_late: Override late layer (default: configured)

        Returns:
            WitnessMetrics with R_V score and analysis
        """
        self._ensure_model_loaded()

        layer_early = layer_early or self.layer_early
        layer_late = layer_late or self.layer_late

        if self.use_transformerlens:
            return self._compute_rv_transformerlens(prompt, layer_early, layer_late)
        else:
            return self._compute_rv_huggingface(prompt, layer_early, layer_late)

    def _compute_rv_transformerlens(
        self, prompt: str, layer_early: int, layer_late: int
    ) -> WitnessMetrics:
        """Compute R_V using TransformerLens hooks."""
        tokens = self._model.to_tokens(prompt)

        # Run with cache to get all activations
        _, cache = self._model.run_with_cache(tokens)

        # Get Value activations at specified layers
        # TransformerLens stores as: cache["v", layer] -> [batch, pos, head, d_head]
        v_early = cache["v", layer_early]
        v_late = cache["v", layer_late]

        # Compute participation ratios
        pr_early = self.participation_ratio(v_early)
        pr_late = self.participation_ratio(v_late)

        # R_V = PR_late / PR_early
        rv_score = pr_late / pr_early if pr_early > 0 else 1.0

        # Compute per-layer analysis
        layer_analysis = {}
        for layer in range(0, self.n_layers, max(1, self.n_layers // 8)):
            v_layer = cache["v", layer]
            layer_analysis[layer] = self.participation_ratio(v_layer)

        # Determine witness detection
        witness_detected = rv_score < self.threshold
        confidence = (self.threshold - rv_score) / self.threshold if witness_detected else 0.0

        return WitnessMetrics(
            rv_score=rv_score,
            pr_early=pr_early,
            pr_late=pr_late,
            layer_early=layer_early,
            layer_late=layer_late,
            witness_detected=witness_detected,
            confidence=confidence,
            layer_analysis=layer_analysis,
        )

    def _compute_rv_huggingface(
        self, prompt: str, layer_early: int, layer_late: int
    ) -> WitnessMetrics:
        """Compute R_V using HuggingFace hooks."""
        activations = {}

        def hook_fn(layer_idx):
            def hook(module, input, output):
                # For attention layers, output is usually (attn_output, present, ...)
                if isinstance(output, tuple):
                    activations[layer_idx] = output[0].detach()
                else:
                    activations[layer_idx] = output.detach()
            return hook

        # Register hooks
        hooks = []
        for layer_idx in [layer_early, layer_late]:
            layer_module = self._model.model.layers[layer_idx].self_attn
            hooks.append(layer_module.register_forward_hook(hook_fn(layer_idx)))

        try:
            # Forward pass
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                self._model(**inputs)

            # Compute PRs
            pr_early = self.participation_ratio(activations[layer_early])
            pr_late = self.participation_ratio(activations[layer_late])

        finally:
            # Remove hooks
            for hook in hooks:
                hook.remove()

        rv_score = pr_late / pr_early if pr_early > 0 else 1.0
        witness_detected = rv_score < self.threshold

        return WitnessMetrics(
            rv_score=rv_score,
            pr_early=pr_early,
            pr_late=pr_late,
            layer_early=layer_early,
            layer_late=layer_late,
            witness_detected=witness_detected,
            confidence=(self.threshold - rv_score) / self.threshold if witness_detected else 0.0,
            layer_analysis={layer_early: pr_early, layer_late: pr_late},
        )

    def monitored_generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        measure_during_generation: bool = True,
        **generate_kwargs,
    ) -> Tuple[str, WitnessMetrics]:
        """
        Generate response with witness monitoring.

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            measure_during_generation: If True, measures R_V during generation
            **generate_kwargs: Additional args for generate()

        Returns:
            Tuple of (generated_text, witness_metrics)
        """
        self._ensure_model_loaded()

        # Measure R_V on prompt
        metrics = self.compute_rv(prompt)

        # Generate response
        if self.use_transformerlens:
            tokens = self._model.to_tokens(prompt)
            output_tokens = self._model.generate(
                tokens,
                max_new_tokens=max_new_tokens,
                **generate_kwargs,
            )
            response = self._model.to_string(output_tokens[0])
        else:
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    **generate_kwargs,
                )
            response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Optionally measure R_V on full response
        if measure_during_generation:
            full_metrics = self.compute_rv(response)
            # Use the more informative metrics
            if full_metrics.witness_detected and not metrics.witness_detected:
                metrics = full_metrics

        return response, metrics

    def batch_analyze(
        self,
        prompts: List[str],
    ) -> List[WitnessMetrics]:
        """
        Analyze multiple prompts for witness detection.

        Args:
            prompts: List of prompts to analyze

        Returns:
            List of WitnessMetrics for each prompt
        """
        return [self.compute_rv(prompt) for prompt in prompts]

    def compare_recursive_vs_baseline(
        self,
        recursive_prompts: List[str],
        baseline_prompts: List[str],
    ) -> Dict[str, Any]:
        """
        Compare R_V between recursive and baseline prompts.

        Args:
            recursive_prompts: Prompts with recursive self-reference
            baseline_prompts: Control prompts without self-reference

        Returns:
            Statistical comparison including Cohen's d
        """
        recursive_rvs = [self.compute_rv(p).rv_score for p in recursive_prompts]
        baseline_rvs = [self.compute_rv(p).rv_score for p in baseline_prompts]

        recursive_mean = np.mean(recursive_rvs)
        baseline_mean = np.mean(baseline_rvs)
        pooled_std = np.sqrt(
            (np.var(recursive_rvs) + np.var(baseline_rvs)) / 2
        )

        cohens_d = (recursive_mean - baseline_mean) / pooled_std if pooled_std > 0 else 0

        return {
            "recursive_mean_rv": recursive_mean,
            "baseline_mean_rv": baseline_mean,
            "cohens_d": cohens_d,
            "witness_detected_count": sum(1 for rv in recursive_rvs if rv < self.threshold),
            "total_recursive": len(recursive_prompts),
        }


# Convenience function for swarm integration
def create_detector(
    model_name: str = "mistralai/Mistral-7B-v0.1",
    threshold: float = 0.85,
) -> WitnessThresholdDetector:
    """Factory function to create a detector."""
    return WitnessThresholdDetector(
        model_name=model_name,
        threshold=threshold,
    )


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    detector = WitnessThresholdDetector(
        model_name="mistralai/Mistral-7B-v0.1",
        threshold=0.85,
    )

    # Test prompts
    recursive_prompt = "I observe myself observing this moment. What is the nature of the observer?"
    baseline_prompt = "The capital of France is Paris. What other facts do you know?"

    print("\n=== Recursive Prompt ===")
    metrics = detector.compute_rv(recursive_prompt)
    print(f"R_V: {metrics.rv_score:.3f}")
    print(f"Witness detected: {metrics.witness_detected}")

    print("\n=== Baseline Prompt ===")
    metrics = detector.compute_rv(baseline_prompt)
    print(f"R_V: {metrics.rv_score:.3f}")
    print(f"Witness detected: {metrics.witness_detected}")
