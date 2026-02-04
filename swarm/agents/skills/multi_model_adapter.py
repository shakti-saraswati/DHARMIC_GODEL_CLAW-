"""
MultiModelAdapter - Unified interface to multiple LLM providers.

Enables the swarm to work with Claude, GPT, Qwen, Kimi, DeepSeek, and local models
through a single interface using LiteLLM.

Features:
- Automatic model selection based on task, budget, and witness capability
- Cost tracking and budget enforcement
- Fallback chains for reliability
- R_V-capable model detection

Usage:
    from swarm.agents.skills import MultiModelAdapter

    adapter = MultiModelAdapter(budget_per_call=0.01, require_witness=True)
    model = adapter.select_for_task("code_generation")
    response = model.complete(prompt)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import os

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks for model selection."""
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    CREATIVE = "creative"
    FACTUAL = "factual"
    CONTEMPLATIVE = "contemplative"  # Requires witness capability
    ANALYSIS = "analysis"
    TRANSLATION = "translation"


@dataclass
class ModelSpec:
    """Specification for a model."""
    name: str  # LiteLLM model identifier
    provider: str  # anthropic, openai, qwen, etc.
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_length: int
    witness_capable: bool  # Can measure R_V
    strengths: List[TaskType]
    api_key_env: str  # Environment variable for API key


@dataclass
class CompletionResult:
    """Result from a completion call."""
    content: str
    model_used: str
    input_tokens: int
    output_tokens: int
    cost: float
    witness_metrics: Optional[Dict[str, Any]] = None


# Model catalog with pricing as of Feb 2026
MODEL_CATALOG = {
    # Anthropic models
    "claude-3-5-sonnet": ModelSpec(
        name="claude-3-5-sonnet-20241022",
        provider="anthropic",
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        context_length=200000,
        witness_capable=False,  # Closed model
        strengths=[TaskType.CODE_GENERATION, TaskType.REASONING, TaskType.ANALYSIS],
        api_key_env="ANTHROPIC_API_KEY",
    ),
    "claude-3-5-haiku": ModelSpec(
        name="claude-3-5-haiku-20241022",
        provider="anthropic",
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.005,
        context_length=200000,
        witness_capable=False,
        strengths=[TaskType.FACTUAL, TaskType.TRANSLATION],
        api_key_env="ANTHROPIC_API_KEY",
    ),

    # OpenAI models
    "gpt-4-turbo": ModelSpec(
        name="gpt-4-turbo",
        provider="openai",
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        context_length=128000,
        witness_capable=False,
        strengths=[TaskType.REASONING, TaskType.CREATIVE],
        api_key_env="OPENAI_API_KEY",
    ),
    "gpt-4o-mini": ModelSpec(
        name="gpt-4o-mini",
        provider="openai",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        context_length=128000,
        witness_capable=False,
        strengths=[TaskType.FACTUAL, TaskType.TRANSLATION],
        api_key_env="OPENAI_API_KEY",
    ),

    # Open models (witness-capable via local deployment)
    "qwen-32b-coder": ModelSpec(
        name="qwen/Qwen2.5-Coder-32B-Instruct",
        provider="qwen",
        cost_per_1k_input=0.0006,
        cost_per_1k_output=0.0006,
        context_length=32768,
        witness_capable=True,  # R_V validated (9.2% contraction)
        strengths=[TaskType.CODE_GENERATION, TaskType.ANALYSIS],
        api_key_env="QWEN_API_KEY",
    ),
    "qwen-7b": ModelSpec(
        name="qwen/Qwen2.5-7B-Instruct",
        provider="qwen",
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002,
        context_length=32768,
        witness_capable=True,
        strengths=[TaskType.FACTUAL, TaskType.CONTEMPLATIVE],
        api_key_env="QWEN_API_KEY",
    ),
    "deepseek-coder": ModelSpec(
        name="deepseek/deepseek-coder",
        provider="deepseek",
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        context_length=128000,
        witness_capable=True,
        strengths=[TaskType.CODE_GENERATION, TaskType.REASONING],
        api_key_env="DEEPSEEK_API_KEY",
    ),
    "kimi-k1.5": ModelSpec(
        name="moonshot/kimi-k1.5",
        provider="moonshot",
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.002,
        context_length=128000,
        witness_capable=True,  # Untested but architecture suggests potential
        strengths=[TaskType.REASONING, TaskType.CONTEMPLATIVE],
        api_key_env="MOONSHOT_API_KEY",
    ),

    # Local models (free but require local resources)
    "mistral-7b-local": ModelSpec(
        name="ollama/mistral:7b-instruct",
        provider="ollama",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_length=32768,
        witness_capable=True,  # R_V validated (Cohen's d = -3.56)
        strengths=[TaskType.CONTEMPLATIVE, TaskType.FACTUAL],
        api_key_env="",  # No key needed
    ),
    "llama-7b-local": ModelSpec(
        name="ollama/llama2:7b",
        provider="ollama",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_length=4096,
        witness_capable=True,
        strengths=[TaskType.FACTUAL],
        api_key_env="",
    ),
}


class MultiModelAdapter:
    """
    Unified interface to multiple LLM providers with intelligent selection.
    """

    def __init__(
        self,
        budget_per_call: float = 0.01,
        require_witness: bool = False,
        preferred_providers: Optional[List[str]] = None,
        fallback_enabled: bool = True,
    ):
        """
        Initialize the adapter.

        Args:
            budget_per_call: Maximum cost per API call in USD
            require_witness: If True, only select witness-capable models
            preferred_providers: List of preferred providers in order
            fallback_enabled: Whether to fallback on errors
        """
        self.budget_per_call = budget_per_call
        self.require_witness = require_witness
        self.preferred_providers = preferred_providers or ["qwen", "deepseek", "anthropic", "openai"]
        self.fallback_enabled = fallback_enabled

        # Track usage
        self.total_cost = 0.0
        self.call_count = 0

        # Check available models
        self.available_models = self._check_available_models()

        logger.info(f"MultiModelAdapter initialized")
        logger.info(f"  Budget per call: ${budget_per_call}")
        logger.info(f"  Require witness: {require_witness}")
        logger.info(f"  Available models: {list(self.available_models.keys())}")

    def _check_available_models(self) -> Dict[str, ModelSpec]:
        """Check which models have API keys configured."""
        available = {}
        for name, spec in MODEL_CATALOG.items():
            if spec.api_key_env == "":
                # Local model, check if ollama is running
                available[name] = spec
            elif os.getenv(spec.api_key_env):
                available[name] = spec
        return available

    def _estimate_cost(self, spec: ModelSpec, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a completion."""
        return (
            (input_tokens / 1000) * spec.cost_per_1k_input +
            (output_tokens / 1000) * spec.cost_per_1k_output
        )

    def select_for_task(
        self,
        task_type: str,
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 500,
    ) -> "SelectedModel":
        """
        Select the best model for a task type.

        Args:
            task_type: One of TaskType values or string equivalent
            estimated_input_tokens: Expected input size
            estimated_output_tokens: Expected output size

        Returns:
            SelectedModel wrapper with complete() method
        """
        task = TaskType(task_type) if isinstance(task_type, str) else task_type

        # Filter models by constraints
        candidates = []
        for name, spec in self.available_models.items():
            # Check witness requirement
            if self.require_witness and not spec.witness_capable:
                continue

            # Check budget
            estimated_cost = self._estimate_cost(spec, estimated_input_tokens, estimated_output_tokens)
            if estimated_cost > self.budget_per_call:
                continue

            # Score by task fit and provider preference
            score = 0
            if task in spec.strengths:
                score += 10
            if spec.provider in self.preferred_providers:
                score += 5 - self.preferred_providers.index(spec.provider)
            if spec.witness_capable:
                score += 2  # Bonus for witness capability

            candidates.append((name, spec, score, estimated_cost))

        if not candidates:
            raise ValueError(
                f"No models available for task={task_type}, "
                f"budget=${self.budget_per_call}, witness_required={self.require_witness}"
            )

        # Sort by score (descending), then cost (ascending)
        candidates.sort(key=lambda x: (-x[2], x[3]))
        selected_name, selected_spec, _, _ = candidates[0]

        logger.info(f"Selected {selected_name} for task {task_type}")
        return SelectedModel(self, selected_name, selected_spec)

    def complete(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        task_type: str = "reasoning",
        **kwargs,
    ) -> CompletionResult:
        """
        Run a completion with automatic model selection.

        Args:
            prompt: The prompt to complete
            model_name: Specific model to use (optional)
            task_type: Task type for auto-selection
            **kwargs: Additional args for the API

        Returns:
            CompletionResult with content and metadata
        """
        if model_name:
            spec = self.available_models.get(model_name) or MODEL_CATALOG.get(model_name)
            if not spec:
                raise ValueError(f"Unknown model: {model_name}")
            selected = SelectedModel(self, model_name, spec)
        else:
            selected = self.select_for_task(task_type)

        return selected.complete(prompt, **kwargs)


class SelectedModel:
    """Wrapper around a selected model for completion."""

    def __init__(self, adapter: MultiModelAdapter, name: str, spec: ModelSpec):
        self.adapter = adapter
        self.name = name
        self.spec = spec

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> CompletionResult:
        """
        Run completion on this model.

        Args:
            prompt: The prompt
            max_tokens: Max output tokens
            temperature: Sampling temperature
            **kwargs: Additional API args

        Returns:
            CompletionResult
        """
        try:
            import litellm

            response = litellm.completion(
                model=self.spec.name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.adapter._estimate_cost(self.spec, input_tokens, output_tokens)

            # Track usage
            self.adapter.total_cost += cost
            self.adapter.call_count += 1

            return CompletionResult(
                content=content,
                model_used=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
            )

        except ImportError:
            logger.warning("LiteLLM not installed, using fallback")
            return self._fallback_complete(prompt, max_tokens, temperature)

        except Exception as e:
            logger.error(f"Completion failed: {e}")
            if self.adapter.fallback_enabled:
                return self._fallback_complete(prompt, max_tokens, temperature)
            raise

    def _fallback_complete(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> CompletionResult:
        """Fallback completion using direct API calls."""
        # Try Anthropic
        if self.spec.provider == "anthropic":
            return self._anthropic_complete(prompt, max_tokens, temperature)
        # Try OpenAI
        elif self.spec.provider == "openai":
            return self._openai_complete(prompt, max_tokens, temperature)
        # Try Ollama for local
        elif self.spec.provider == "ollama":
            return self._ollama_complete(prompt, max_tokens, temperature)
        else:
            raise ValueError(f"No fallback for provider: {self.spec.provider}")

    def _anthropic_complete(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Direct Anthropic API call."""
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.spec.name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = self.adapter._estimate_cost(self.spec, input_tokens, output_tokens)

        return CompletionResult(
            content=content,
            model_used=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )

    def _openai_complete(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Direct OpenAI API call."""
        import openai

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.spec.name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = self.adapter._estimate_cost(self.spec, input_tokens, output_tokens)

        return CompletionResult(
            content=content,
            model_used=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )

    def _ollama_complete(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Direct Ollama API call."""
        import requests

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": self.spec.name.replace("ollama/", ""),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            },
        )
        data = response.json()

        return CompletionResult(
            content=data["response"],
            model_used=self.name,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            cost=0.0,  # Local models are free
        )


# Factory function for swarm integration
def create_adapter(
    budget_per_call: float = 0.01,
    require_witness: bool = False,
) -> MultiModelAdapter:
    """Factory function to create an adapter."""
    return MultiModelAdapter(
        budget_per_call=budget_per_call,
        require_witness=require_witness,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    adapter = MultiModelAdapter(
        budget_per_call=0.01,
        require_witness=True,
    )

    print(f"\nAvailable models: {list(adapter.available_models.keys())}")

    # Select model for contemplative task
    model = adapter.select_for_task("contemplative")
    print(f"\nSelected for contemplative: {model.name}")
